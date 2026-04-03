from __future__ import annotations

import unittest

from excel_data_analysis.models import (
    MeasurementRecord,
    OutlierRatioStatConfig,
    ReportConfig,
    RowDimension,
    RowDimensionSource,
    TemplateConfig,
    ThresholdConfig,
)
from excel_data_analysis.reporting import (
    ColumnMeta,
    MetricValue,
    RowData,
    _collect_outlier_summary_artifacts,
    _build_zscore_map,
)


def _build_template(
    node_orders: list[list[str]],
    outlier_ratio_stats: list[OutlierRatioStatConfig] | None = None,
) -> TemplateConfig:
    return TemplateConfig(
        name="test-template",
        row_dimensions=[
            RowDimension(
                name="sample_id",
                display_name="SampleID",
                sources=[RowDimensionSource(column="recordName")],
            ),
            RowDimension(
                name="reliability_node",
                display_name="ReliabilityNode",
                sources=[RowDimensionSource(column="recordName")],
            ),
            RowDimension(
                name="repeat_id",
                display_name="RepeatIndex",
                sources=[RowDimensionSource(column="recordName")],
                optional=True,
                default_value="1",
            ),
        ],
        report=ReportConfig(
            node_orders=node_orders,
            outlier_fail_method="golden_deviation",
            outlier_chain_fail_rule="any_fail",
            outlier_ratio_stats=outlier_ratio_stats or [],
        ),
    )


def _build_rows() -> list[RowData]:
    rows: list[RowData] = []
    for row_number, node in enumerate(["T0", "T1", "T2"], start=1):
        rows.append(
            RowData(
                dataset_id="dataset-1",
                source_file="/tmp/test.xlsx",
                row_number=row_number,
                dimensions={
                    "sample_id": "S1",
                    "reliability_node": node,
                    "repeat_id": "1",
                },
                values={"V_Link4_1A": 0.4},
            )
        )
    return rows


def _build_columns() -> list[ColumnMeta]:
    return [
        ColumnMeta(
            raw_column="V_Link4_1A",
            logical_metric="link4_voltage::V_Link4_1A",
            group_id="link4_voltage",
            chain_name="Link4",
            item_label="V",
            repeat_index=1,
            unit="V",
            display_order=0,
            metric_type="V",
            condition="1A",
        )
    ]


def _build_metric_values(failing_nodes: set[str]) -> dict[tuple[str, int, str], MetricValue]:
    values: dict[tuple[str, int, str], MetricValue] = {}
    for row_number, node in enumerate(["T0", "T1", "T2"], start=1):
        is_fail = node in failing_nodes
        values[("dataset-1", row_number, "V_Link4_1A")] = MetricValue(
            value=0.1 if is_fail else 0.0,
            threshold=0.05,
            golden_value=0.4,
            is_fail=is_fail,
        )
    return values


class OutlierSummarySequenceTests(unittest.TestCase):
    def test_branching_sequences_mark_sibling_failures_as_new(self) -> None:
        template = _build_template([["T0", "T1"], ["T0", "T2"]])
        rows = _build_rows()
        columns = _build_columns()
        golden_values = _build_metric_values({"T1", "T2"})
        artifacts = _collect_outlier_summary_artifacts(
            template=template,
            columns=columns,
            rows=rows,
            zscore_values={},
            golden_values=golden_values,
            sample_node_orders={"S1": ["T0", "T1"]},
        )
        summary_rows = artifacts["summary_rows"]

        self.assertEqual(
            summary_rows,
            [
                {"sample_id": "S1", "node": "T1", "chain": "Link4", "status": "New"},
                {"sample_id": "S1", "node": "T2", "chain": "Link4", "status": "New"},
            ],
        )

    def test_linear_sequence_marks_later_failure_as_existed(self) -> None:
        template = _build_template([["T0", "T1", "T2"]])
        rows = _build_rows()
        columns = _build_columns()
        golden_values = _build_metric_values({"T1", "T2"})
        artifacts = _collect_outlier_summary_artifacts(
            template=template,
            columns=columns,
            rows=rows,
            zscore_values={},
            golden_values=golden_values,
            sample_node_orders={"S1": ["T0", "T1", "T2"]},
        )
        summary_rows = artifacts["summary_rows"]

        self.assertEqual(
            summary_rows,
            [
                {"sample_id": "S1", "node": "T1", "chain": "Link4", "status": "New"},
                {"sample_id": "S1", "node": "T2", "chain": "Link4", "status": "Existed"},
            ],
        )

    def test_ratio_stats_support_new_and_total_outlier_sample_ratios(self) -> None:
        template = _build_template(
            [["T0", "T1"], ["T0", "T2"]],
            outlier_ratio_stats=[
                OutlierRatioStatConfig(
                    id="new_ratio_by_node",
                    display_name="New Ratio By Node",
                    group_by_dimension="reliability_node",
                    numerator="new_outlier_samples",
                ),
                OutlierRatioStatConfig(
                    id="total_ratio_link4",
                    display_name="Total Ratio Link4",
                    group_by_dimension="reliability_node",
                    numerator="outlier_samples",
                    chains=["Link4"],
                ),
            ],
        )
        rows = _build_rows()
        columns = _build_columns()
        golden_values = _build_metric_values({"T1", "T2"})
        artifacts = _collect_outlier_summary_artifacts(
            template=template,
            columns=columns,
            rows=rows,
            zscore_values={},
            golden_values=golden_values,
            sample_node_orders={"S1": ["T0", "T1"]},
        )
        ratio_rows = artifacts["ratio_rows"]

        self.assertEqual(
            ratio_rows,
            [
                {
                    "id": "new_ratio_by_node",
                    "display_name": "New Ratio By Node",
                    "group_by_dimension": "reliability_node",
                    "group_value": "T0",
                    "numerator": "new_outlier_samples",
                    "outlier_sample_count": 0,
                    "total_sample_count": 1,
                    "outlier_ratio": 0.0,
                    "filter_summary": "No filters",
                },
                {
                    "id": "new_ratio_by_node",
                    "display_name": "New Ratio By Node",
                    "group_by_dimension": "reliability_node",
                    "group_value": "T1",
                    "numerator": "new_outlier_samples",
                    "outlier_sample_count": 1,
                    "total_sample_count": 1,
                    "outlier_ratio": 1.0,
                    "filter_summary": "No filters",
                },
                {
                    "id": "new_ratio_by_node",
                    "display_name": "New Ratio By Node",
                    "group_by_dimension": "reliability_node",
                    "group_value": "T2",
                    "numerator": "new_outlier_samples",
                    "outlier_sample_count": 1,
                    "total_sample_count": 1,
                    "outlier_ratio": 1.0,
                    "filter_summary": "No filters",
                },
                {
                    "id": "total_ratio_link4",
                    "display_name": "Total Ratio Link4",
                    "group_by_dimension": "reliability_node",
                    "group_value": "T0",
                    "numerator": "outlier_samples",
                    "outlier_sample_count": 0,
                    "total_sample_count": 1,
                    "outlier_ratio": 0.0,
                    "filter_summary": "chain=Link4",
                },
                {
                    "id": "total_ratio_link4",
                    "display_name": "Total Ratio Link4",
                    "group_by_dimension": "reliability_node",
                    "group_value": "T1",
                    "numerator": "outlier_samples",
                    "outlier_sample_count": 1,
                    "total_sample_count": 1,
                    "outlier_ratio": 1.0,
                    "filter_summary": "chain=Link4",
                },
                {
                    "id": "total_ratio_link4",
                    "display_name": "Total Ratio Link4",
                    "group_by_dimension": "reliability_node",
                    "group_value": "T2",
                    "numerator": "outlier_samples",
                    "outlier_sample_count": 1,
                    "total_sample_count": 1,
                    "outlier_ratio": 1.0,
                    "filter_summary": "chain=Link4",
                },
            ],
        )

    def test_zscore_threshold_override_replaces_template_thresholds(self) -> None:
        measurements = [
            MeasurementRecord(
                dataset_id="dataset-1",
                source_file="/tmp/test.xlsx",
                row_number=index,
                logical_metric="link4_voltage::V_Link4_1A",
                group_id="link4_voltage",
                group_display_name="Link4 Voltage",
                presentation_group="Link4",
                raw_column="V_Link4_1A",
                value=value,
                dimensions={"sample_id": f"S{index}", "reliability_node": "T0"},
            )
            for index, value in enumerate([10.0, 11.0, 100.0], start=1)
        ]
        columns = _build_columns()
        thresholds = ThresholdConfig(default=3.5, overrides={"Link4": 0.5})

        default_values = _build_zscore_map(measurements, thresholds, columns)
        override_values = _build_zscore_map(
            measurements,
            thresholds,
            columns,
            zscore_threshold_override=100.0,
        )

        outlier_key = ("dataset-1", 3, "V_Link4_1A")
        self.assertTrue(default_values[outlier_key].is_fail)
        self.assertEqual(default_values[outlier_key].threshold, 0.5)
        self.assertFalse(override_values[outlier_key].is_fail)
        self.assertEqual(override_values[outlier_key].threshold, 100.0)


if __name__ == "__main__":
    unittest.main()
