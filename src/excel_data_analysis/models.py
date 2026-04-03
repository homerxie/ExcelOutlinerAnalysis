from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RowDimensionSource:
    column: str
    split_delimiters: list[str] = field(default_factory=list)
    split_position: int | None = None
    skip_empty_parts: bool = False


@dataclass(slots=True)
class RowDimension:
    name: str
    sources: list[RowDimensionSource]
    optional: bool = False
    display_name: str | None = None
    default_value: str | None = None


@dataclass(slots=True)
class AnalysisGroup:
    id: str
    display_name: str
    columns: list[str]
    analysis_mode: str
    presentation_group: str | None = None
    unit: str | None = None


@dataclass(slots=True)
class ThresholdConfig:
    default: float
    overrides: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class GoldenReferenceDefaults:
    reference_dimensions: list[str] = field(default_factory=list)
    filters: dict[str, str] = field(default_factory=dict)
    center_method: str = "mean"
    threshold_mode: str = "relative"
    relative_limit: float | None = 0.2
    sigma_multiplier: float | None = 3.0


@dataclass(slots=True)
class OutlierRatioStatConfig:
    id: str
    display_name: str | None = None
    group_by_dimension: str = "reliability_node"
    numerator: str = "new_outlier_samples"
    chains: list[str] = field(default_factory=list)
    raw_columns: list[str] = field(default_factory=list)
    logical_metrics: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ReportConfig:
    golden_values: dict[str, float] = field(default_factory=dict)
    zscore_thresholds: ThresholdConfig = field(
        default_factory=lambda: ThresholdConfig(default=3.5)
    )
    golden_deviation_thresholds: ThresholdConfig = field(
        default_factory=lambda: ThresholdConfig(default=0.05)
    )
    node_order: list[str] = field(default_factory=list)
    node_orders: list[list[str]] = field(default_factory=list)
    outlier_fail_method: str = "modified_z_score"
    outlier_chain_fail_rule: str = "any_fail"
    outlier_ratio_stats: list[OutlierRatioStatConfig] = field(default_factory=list)


@dataclass(slots=True)
class TemplateConfig:
    name: str
    header_row: int = 0
    measurement_header_row: int | None = None
    row_header_row: int | None = None
    unit_row: int | None = None
    data_start_row: int | None = None
    row_dimensions: list[RowDimension] = field(default_factory=list)
    analysis_groups: list[AnalysisGroup] = field(default_factory=list)
    golden_reference_defaults: GoldenReferenceDefaults = field(
        default_factory=GoldenReferenceDefaults
    )
    report: ReportConfig = field(default_factory=ReportConfig)


@dataclass(slots=True)
class LoadedTable:
    headers: list[str]
    rows: list[dict[str, Any]]
    units: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class MeasurementRecord:
    dataset_id: str
    source_file: str
    row_number: int
    logical_metric: str
    group_id: str
    group_display_name: str
    presentation_group: str | None
    raw_column: str
    value: float
    dimensions: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MeasurementRecord":
        return cls(**payload)


@dataclass(slots=True)
class GoldenMetricRange:
    reference_key: dict[str, str]
    logical_metric: str
    sample_size: int
    center: float
    stdev: float
    lower_bound: float
    upper_bound: float
    threshold_mode: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GoldenMetricRange":
        return cls(**payload)


@dataclass(slots=True)
class GoldenReference:
    name: str
    reference_dimensions: list[str]
    filters: dict[str, str]
    threshold_mode: str
    relative_limit: float | None
    sigma_multiplier: float | None
    metrics: list[GoldenMetricRange]
    center_method: str = "mean"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GoldenReference":
        payload = dict(payload)
        payload["metrics"] = [
            GoldenMetricRange.from_dict(item) for item in payload.get("metrics", [])
        ]
        payload.setdefault("center_method", "mean")
        return cls(**payload)


@dataclass(slots=True)
class AnomalyResult:
    method: str
    dataset_id: str
    source_file: str
    row_number: int
    logical_metric: str
    raw_column: str
    value: float
    dimensions: dict[str, str]
    lower_bound: float | None = None
    upper_bound: float | None = None
    center: float | None = None
    score: float | None = None
    reference_key: dict[str, str] | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
