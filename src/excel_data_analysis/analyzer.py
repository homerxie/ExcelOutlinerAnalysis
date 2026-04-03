from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean, median, pstdev

from .models import AnomalyResult, GoldenMetricRange, GoldenReference, MeasurementRecord


def build_golden_reference(
    name: str,
    measurements: list[MeasurementRecord],
    reference_dimensions: list[str],
    filters: dict[str, str] | None = None,
    center_method: str = "mean",
    threshold_mode: str = "relative",
    relative_limit: float | None = 0.2,
    sigma_multiplier: float | None = None,
) -> GoldenReference:
    filters = filters or {}
    if center_method not in {"mean", "median"}:
        raise ValueError(f"Unsupported center_method: {center_method}")
    grouped: dict[tuple[tuple[str, str], str], list[float]] = defaultdict(list)

    for record in measurements:
        if not _match_dimensions(record.dimensions, filters):
            continue
        reference_key = tuple(
            (dimension, record.dimensions.get(dimension, ""))
            for dimension in reference_dimensions
        )
        grouped[(reference_key, record.logical_metric)].append(record.value)

    metrics: list[GoldenMetricRange] = []
    for (reference_key, logical_metric), values in grouped.items():
        center = _resolve_center(values, center_method)
        stdev = pstdev(values, mu=center) if len(values) > 1 else 0.0
        lower_bound, upper_bound = _resolve_bounds(
            center=center,
            stdev=stdev,
            threshold_mode=threshold_mode,
            relative_limit=relative_limit,
            sigma_multiplier=sigma_multiplier,
        )
        metrics.append(
            GoldenMetricRange(
                reference_key=dict(reference_key),
                logical_metric=logical_metric,
                sample_size=len(values),
                center=center,
                stdev=stdev,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                threshold_mode=threshold_mode,
            )
        )

    return GoldenReference(
        name=name,
        reference_dimensions=reference_dimensions,
        filters=filters,
        threshold_mode=threshold_mode,
        relative_limit=relative_limit,
        sigma_multiplier=sigma_multiplier,
        metrics=sorted(
            metrics,
            key=lambda item: (
                tuple(sorted(item.reference_key.items())),
                item.logical_metric,
            ),
        ),
        center_method=center_method,
    )


def detect_against_golden(
    measurements: list[MeasurementRecord],
    reference: GoldenReference,
) -> list[AnomalyResult]:
    evaluations = evaluate_against_golden(measurements, reference)
    return [item for item in evaluations if item.reason]


def evaluate_against_golden(
    measurements: list[MeasurementRecord],
    reference: GoldenReference,
) -> list[AnomalyResult]:
    index = _build_golden_index(reference)

    evaluations: list[AnomalyResult] = []
    for record in measurements:
        reference_key = tuple(
            (dimension, record.dimensions.get(dimension, ""))
            for dimension in reference.reference_dimensions
        )
        metric = index.get((reference_key, record.logical_metric))
        if metric is None:
            continue
        is_outside = not (metric.lower_bound <= record.value <= metric.upper_bound)
        evaluations.append(
            AnomalyResult(
                method="golden_reference",
                dataset_id=record.dataset_id,
                source_file=record.source_file,
                row_number=record.row_number,
                logical_metric=record.logical_metric,
                raw_column=record.raw_column,
                value=record.value,
                dimensions=record.dimensions,
                lower_bound=metric.lower_bound,
                upper_bound=metric.upper_bound,
                center=metric.center,
                reference_key=metric.reference_key,
                reason="Value is outside golden bounds." if is_outside else None,
            )
        )
    return evaluations


def summarize_golden_coverage(
    measurements: list[MeasurementRecord],
    reference: GoldenReference,
) -> dict[str, object]:
    index = _build_golden_index(reference)
    matched_measurement_count = 0
    unmatched_measurement_count = 0
    matched_rows: set[tuple[str, str, int]] = set()
    unmatched_rows: set[tuple[str, str, int]] = set()
    unmatched_examples: list[dict[str, object]] = []

    for record in measurements:
        reference_key = tuple(
            (dimension, record.dimensions.get(dimension, ""))
            for dimension in reference.reference_dimensions
        )
        metric = index.get((reference_key, record.logical_metric))
        row_key = (record.dataset_id, record.source_file, record.row_number)
        if metric is None:
            unmatched_measurement_count += 1
            unmatched_rows.add(row_key)
            if len(unmatched_examples) < 5:
                unmatched_examples.append(
                    {
                        "dataset_id": record.dataset_id,
                        "row_number": record.row_number,
                        "logical_metric": record.logical_metric,
                        "raw_column": record.raw_column,
                        "dimensions": dict(record.dimensions),
                    }
                )
            continue
        matched_measurement_count += 1
        matched_rows.add(row_key)

    total_measurement_count = len(measurements)
    return {
        "total_measurement_count": total_measurement_count,
        "matched_measurement_count": matched_measurement_count,
        "unmatched_measurement_count": unmatched_measurement_count,
        "matched_row_count": len(matched_rows),
        "unmatched_row_count": len(unmatched_rows),
        "unmatched_examples": unmatched_examples,
    }


def detect_by_modified_zscore(
    measurements: list[MeasurementRecord],
    population_dimensions: list[str] | None = None,
    z_threshold: float = 3.5,
) -> list[AnomalyResult]:
    evaluations = evaluate_modified_zscore(
        measurements=measurements,
        population_dimensions=population_dimensions,
    )
    anomalies: list[AnomalyResult] = []
    for item in evaluations:
        if item.score is None or abs(item.score) <= z_threshold:
            continue
        item.reason = f"Absolute modified z-score exceeded threshold {z_threshold}."
        anomalies.append(item)
    return anomalies


def evaluate_modified_zscore(
    measurements: list[MeasurementRecord],
    population_dimensions: list[str] | None = None,
) -> list[AnomalyResult]:
    population_dimensions = population_dimensions or []
    grouped: dict[tuple[tuple[str, str], str], list[MeasurementRecord]] = defaultdict(list)

    for record in measurements:
        population_key = tuple(
            (dimension, record.dimensions.get(dimension, ""))
            for dimension in population_dimensions
        )
        grouped[(population_key, record.logical_metric)].append(record)

    evaluations: list[AnomalyResult] = []
    for (population_key, logical_metric), records in grouped.items():
        values = [record.value for record in records]
        if len(values) < 3:
            for record in records:
                evaluations.append(
                    AnomalyResult(
                        method="modified_z_score",
                        dataset_id=record.dataset_id,
                        source_file=record.source_file,
                        row_number=record.row_number,
                        logical_metric=logical_metric,
                        raw_column=record.raw_column,
                        value=record.value,
                        dimensions=record.dimensions,
                        center=None,
                        score=None,
                        reason=None,
                    )
                )
            continue
        med = median(values)
        deviations = [abs(value - med) for value in values]
        mad = median(deviations)
        if mad == 0:
            for record in records:
                evaluations.append(
                    AnomalyResult(
                        method="modified_z_score",
                        dataset_id=record.dataset_id,
                        source_file=record.source_file,
                        row_number=record.row_number,
                        logical_metric=logical_metric,
                        raw_column=record.raw_column,
                        value=record.value,
                        dimensions=record.dimensions,
                        center=med,
                        score=0.0,
                        reason=None,
                    )
                )
            continue
        for record in records:
            score = 0.6745 * (record.value - med) / mad
            evaluations.append(
                AnomalyResult(
                    method="modified_z_score",
                    dataset_id=record.dataset_id,
                    source_file=record.source_file,
                    row_number=record.row_number,
                    logical_metric=logical_metric,
                    raw_column=record.raw_column,
                    value=record.value,
                    dimensions=record.dimensions,
                    center=med,
                    score=score,
                    reason=None,
                )
            )
    return evaluations


def _match_dimensions(dimensions: dict[str, str], expected: dict[str, str]) -> bool:
    for key, value in expected.items():
        if dimensions.get(key) != value:
            return False
    return True


def _build_golden_index(
    reference: GoldenReference,
) -> dict[tuple[tuple[tuple[str, str], ...], str], GoldenMetricRange]:
    return {
        (
            tuple(
                (dimension, metric.reference_key.get(dimension, ""))
                for dimension in reference.reference_dimensions
            ),
            metric.logical_metric,
        ): metric
        for metric in reference.metrics
    }


def _resolve_bounds(
    center: float,
    stdev: float,
    threshold_mode: str,
    relative_limit: float | None,
    sigma_multiplier: float | None,
) -> tuple[float, float]:
    lower_candidates: list[float] = [-math.inf]
    upper_candidates: list[float] = [math.inf]

    if threshold_mode in {"relative", "hybrid"}:
        if relative_limit is None:
            raise ValueError("relative_limit is required for relative or hybrid mode.")
        delta = abs(center) * relative_limit
        lower_candidates.append(center - delta)
        upper_candidates.append(center + delta)

    if threshold_mode in {"sigma", "hybrid"}:
        if sigma_multiplier is None:
            raise ValueError("sigma_multiplier is required for sigma or hybrid mode.")
        delta = stdev * sigma_multiplier
        lower_candidates.append(center - delta)
        upper_candidates.append(center + delta)

    if threshold_mode not in {"relative", "sigma", "hybrid"}:
        raise ValueError(f"Unsupported threshold mode: {threshold_mode}")

    return max(lower_candidates), min(upper_candidates)


def _resolve_center(values: list[float], center_method: str) -> float:
    if center_method == "median":
        return median(values)
    return mean(values)
