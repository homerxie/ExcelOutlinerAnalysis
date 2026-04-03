from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from excel_data_analysis.models import GoldenMetricRange, GoldenReference, MeasurementRecord
from excel_data_analysis.repository import Repository
from excel_data_analysis.service import save_debug_bundle


class DebugBundleTests(unittest.TestCase):
    def test_save_debug_bundle_exports_settings_results_and_storage_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template_path = root / "template.json"
            input_path = root / "input.xlsx"
            output_path = root / "report.xlsx"
            storage_path = root / "database"
            bundle_path = root / "debug_bundle"

            template_path.write_text('{"name":"demo-template"}', encoding="utf-8")
            input_path.write_text("placeholder input", encoding="utf-8")
            output_path.write_text("placeholder report", encoding="utf-8")

            repository = Repository(storage_path)
            repository.save_import(
                dataset_id="dataset-1",
                source_file=str(input_path),
                template_name="demo-template",
                measurements=[
                    MeasurementRecord(
                        dataset_id="dataset-1",
                        source_file=str(input_path),
                        row_number=1,
                        logical_metric="metric-1",
                        group_id="group-1",
                        group_display_name="Group 1",
                        presentation_group="Link1",
                        raw_column="Value_1",
                        value=1.23,
                        dimensions={"sample_id": "S1", "reliability_node": "T0"},
                    )
                ],
            )
            golden_path = repository.save_golden(
                GoldenReference(
                    name="demo_golden",
                    reference_dimensions=["sample_id"],
                    filters={"reliability_node": "T0"},
                    threshold_mode="relative",
                    relative_limit=0.05,
                    sigma_multiplier=None,
                    center_method="mean",
                    metrics=[
                        GoldenMetricRange(
                            reference_key={"sample_id": "S1"},
                            logical_metric="metric-1",
                            sample_size=1,
                            center=1.23,
                            stdev=0.0,
                            lower_bound=1.17,
                            upper_bound=1.29,
                            threshold_mode="relative",
                        )
                    ],
                ),
                if_exists="overwrite",
            )

            payload = save_debug_bundle(
                bundle_path=str(bundle_path),
                gui_settings={
                    "paths": {
                        "template_path": str(template_path),
                        "input_path": str(input_path),
                        "storage_path": str(storage_path),
                        "golden_path": str(golden_path),
                        "output_path": str(output_path),
                    },
                    "golden": {"golden_source": "built_golden_file"},
                    "analysis": {
                        "analysis_scope": "filtered_database",
                        "outlier_fail_mode": "golden_deviation",
                        "z_threshold": 4.2,
                        "sample_ids_text": "S1",
                        "nodes_text": "T0",
                        "selected_dataset_ids": ["dataset-1"],
                    },
                },
                current_results={
                    "golden_coverage_summary": {"matched_measurement_count": 1},
                    "outlier_summary_rows": [{"sample_id": "S1", "node": "T0"}],
                    "outlier_ratio_rows": [{"id": "ratio-1", "outlier_ratio": 0.5}],
                },
                log_text="debug log",
                template_path=str(template_path),
                input_path=str(input_path),
                storage_path=str(storage_path),
                golden_path=str(golden_path),
                output_path=str(output_path),
                if_exists="overwrite",
            )

            self.assertEqual(payload["cli_command_count"], 3)
            self.assertTrue((bundle_path / "gui_settings.json").exists())
            self.assertTrue((bundle_path / "current_results.json").exists())
            self.assertTrue((bundle_path / "log.txt").exists())
            self.assertTrue((bundle_path / "storage_summary.json").exists())
            self.assertTrue((bundle_path / "import_history.json").exists())
            self.assertTrue((bundle_path / "files" / "template.json").exists())
            self.assertTrue((bundle_path / "files" / "input.xlsx").exists())
            self.assertTrue((bundle_path / "files" / "golden.json").exists())
            self.assertTrue((bundle_path / "files" / "current_output.xlsx").exists())
            self.assertTrue((bundle_path / "database_snapshot" / "measurements.jsonl").exists())
            self.assertTrue((bundle_path / "database_snapshot" / "datasets.jsonl").exists())
            self.assertTrue((bundle_path / "database_snapshot" / "golden" / "demo_golden.json").exists())

            cli_repro = json.loads((bundle_path / "cli_repro.json").read_text(encoding="utf-8"))
            command_ids = [item["id"] for item in cli_repro["commands"]]
            self.assertEqual(command_ids, ["show_storage", "generate_report", "preview_import"])
            self.assertIn("--storage", cli_repro["commands"][1]["argv"])
            self.assertIn("--z-threshold", cli_repro["commands"][1]["argv"])
            self.assertIn("4.2", cli_repro["commands"][1]["argv"])
            self.assertIn("database_snapshot", cli_repro["commands"][1]["command_text"])


if __name__ == "__main__":
    unittest.main()
