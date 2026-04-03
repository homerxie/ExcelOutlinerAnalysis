from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import shutil
from typing import Any

from .analyzer import (
    build_golden_reference,
    summarize_golden_coverage,
)
from .debug_bundle import export_debug_bundle
from .io import build_measurements, load_table
from .models import AnomalyResult, GoldenReference, MeasurementRecord
from .reporting import (
    collect_outlier_summary_rows_from_measurements,
    collect_outlier_ratio_rows,
    collect_outlier_ratio_rows_from_measurements,
    collect_outlier_summary_artifacts,
    collect_outlier_summary_artifacts_from_measurements,
    collect_outlier_summary_rows,
    collect_report_failures,
    generate_chip_report_from_measurements,
    generate_chip_report,
)
from .repository import Repository
from .template import load_template
from .workspace import (
    clear_database_root,
    database_workspace_differs,
    ensure_database_workspace,
    merge_database_workspace,
    reset_database_workspace,
    save_database_workspace_as,
)

REPEAT_DIMENSION_NAME = "repeat_id"


def import_dataset(
    template_path: str,
    input_path: str,
    storage_path: str,
    conflict_mode: str = "error",
) -> dict:
    if conflict_mode not in {"error", "replace", "append"}:
        raise ValueError(
            f"Unsupported conflict_mode: {conflict_mode}. Expected error, replace, or append."
        )
    template = load_template(template_path)
    table = load_table(input_path, template=template)
    repository = Repository(storage_path)
    dataset_id = repository.new_dataset_id()
    incoming_measurements = build_measurements(
        template=template,
        rows=table.rows,
        dataset_id=dataset_id,
        source_file=str(Path(input_path).resolve()),
    )
    existing_measurements = repository.load_measurements()
    preview = _build_import_preview(existing_measurements, incoming_measurements)

    if preview["conflict_row_count"] and conflict_mode == "error":
        raise ValueError(_format_import_conflict_message(preview))

    final_measurements = incoming_measurements
    removed_measurements = 0
    repeat_shifted_rows = 0

    if conflict_mode == "replace" and preview["conflict_row_count"]:
        filtered_existing = [
            item
            for item in existing_measurements
            if _row_identity_key(item.dimensions) not in preview["conflict_keys"]
        ]
        removed_measurements = len(existing_measurements) - len(filtered_existing)
        repository.replace_measurements([*filtered_existing, *final_measurements])
        repository.save_dataset_entry(
            _build_dataset_payload(
                dataset_id=dataset_id,
                source_file=str(Path(input_path).resolve()),
                template_name=template.name,
                measurement_count=len(final_measurements),
                metadata={
                    "conflict_mode": "replace",
                    "removed_measurements": removed_measurements,
                    "removed_row_count": preview["existing_conflict_row_count"],
                    "imported_row_count": preview["incoming_row_count"],
                    "conflict_row_count": preview["conflict_row_count"],
                },
            )
        )
        repository.reconcile_dataset_entries()
    elif conflict_mode == "append" and preview["conflict_row_count"]:
        final_measurements, repeat_shifted_rows = _append_with_shifted_repeats(
            existing_measurements,
            incoming_measurements,
        )
        repository.save_import(
            dataset_id=dataset_id,
            source_file=str(Path(input_path).resolve()),
            template_name=template.name,
            measurements=final_measurements,
            metadata={
                "conflict_mode": "append",
                "shifted_repeat_row_count": repeat_shifted_rows,
                "imported_row_count": preview["incoming_row_count"],
                "conflict_row_count": preview["conflict_row_count"],
            },
        )
    else:
        repository.save_import(
            dataset_id=dataset_id,
            source_file=str(Path(input_path).resolve()),
            template_name=template.name,
            measurements=final_measurements,
            metadata={
                "conflict_mode": "none" if preview["conflict_row_count"] == 0 else conflict_mode,
                "imported_row_count": preview["incoming_row_count"],
                "conflict_row_count": preview["conflict_row_count"],
            },
        )

    return {
        "dataset_id": dataset_id,
        "template": template.name,
        "imported_measurements": len(final_measurements),
        "imported_rows": preview["incoming_row_count"],
        "conflict_mode": conflict_mode,
        "conflict_rows": preview["conflict_row_count"],
        "existing_conflict_rows": preview["existing_conflict_row_count"],
        "shifted_repeat_rows": repeat_shifted_rows,
        "removed_measurements": removed_measurements,
        "storage": str(Path(storage_path).resolve()),
    }


def preview_import(
    template_path: str,
    input_path: str,
    storage_path: str,
) -> dict[str, Any]:
    template = load_template(template_path)
    table = load_table(input_path, template=template)
    repository = Repository(storage_path)
    dataset_id = repository.new_dataset_id()
    incoming_measurements = build_measurements(
        template=template,
        rows=table.rows,
        dataset_id=dataset_id,
        source_file=str(Path(input_path).resolve()),
    )
    return _build_import_preview(repository.load_measurements(), incoming_measurements)


def describe_storage(
    storage_path: str,
    template_path: str | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    repository = Repository(storage_path)
    measurements = repository.load_measurements()
    dataset_entries = repository.load_dataset_entries()
    ordered_dimensions = _resolve_dimension_order(template_path, measurements)
    rows = list(_collect_row_records(measurements).values())
    rows.sort(key=lambda item: tuple(item["dimensions"].get(name, "") for name in ordered_dimensions))
    preview_rows: list[dict[str, Any]] = []
    for item in rows[:limit]:
        payload = {name: item["dimensions"].get(name, "") for name in ordered_dimensions}
        payload["measurement_count"] = item["measurement_count"]
        payload["dataset_id"] = item["dataset_id"]
        payload["source_file"] = item["source_file"]
        payload["row_number"] = item["row_number"]
        preview_rows.append(payload)
    return {
        "storage": str(Path(storage_path).resolve()),
        "dataset_count": len({item.dataset_id for item in measurements}),
        "measurement_count": len(measurements),
        "row_count": len(rows),
        "dimensions": ordered_dimensions,
        "rows": preview_rows,
        "truncated": len(rows) > limit,
        "import_history_count": len(dataset_entries),
    }


def list_import_history(storage_path: str) -> list[dict[str, Any]]:
    repository = Repository(storage_path)
    entries = repository.load_dataset_entries()
    return sorted(
        entries,
        key=lambda item: (
            str(item.get("created_at_utc", "")),
            str(item.get("dataset_id", "")),
        ),
        reverse=True,
    )


def copy_storage(
    source_storage_path: str,
    target_storage_path: str,
    if_exists: str = "overwrite",
) -> dict[str, Any]:
    source = Path(source_storage_path)
    if not source.exists() or not source.is_dir():
        raise ValueError(f"Source database folder does not exist: {source}")
    from .output_paths import prepare_output_directory

    destination = prepare_output_directory(target_storage_path, if_exists=if_exists)
    shutil.copytree(source, destination, dirs_exist_ok=True)
    return {
        "source": str(source.resolve()),
        "destination": str(destination.resolve()),
    }


def ensure_storage_workspace(
    storage_root_path: str,
) -> dict[str, Any]:
    workspace = ensure_database_workspace(storage_root_path)
    return {
        "database_root": str(Path(storage_root_path).resolve()),
        "workspace": str(workspace.resolve()),
    }


def storage_workspace_differs(
    storage_root_path: str,
) -> dict[str, Any]:
    return {
        "database_root": str(Path(storage_root_path).resolve()),
        "workspace": str(ensure_database_workspace(storage_root_path).resolve()),
        "differs": database_workspace_differs(storage_root_path),
    }


def discard_storage_workspace_changes(
    storage_root_path: str,
) -> dict[str, Any]:
    workspace = reset_database_workspace(storage_root_path)
    return {
        "database_root": str(Path(storage_root_path).resolve()),
        "workspace": str(workspace.resolve()),
    }


def save_storage_workspace(
    storage_root_path: str,
) -> dict[str, Any]:
    workspace = merge_database_workspace(storage_root_path)
    return {
        "database_root": str(Path(storage_root_path).resolve()),
        "workspace": str(workspace.resolve()),
    }


def save_storage_workspace_as(
    storage_root_path: str,
    target_storage_root_path: str,
) -> dict[str, Any]:
    target_root, target_workspace = save_database_workspace_as(
        storage_root_path,
        target_storage_root_path,
    )
    return {
        "source_database_root": str(Path(storage_root_path).resolve()),
        "target_database_root": str(target_root.resolve()),
        "target_workspace": str(target_workspace.resolve()),
    }


def clear_storage_root(
    storage_root_path: str,
) -> dict[str, Any]:
    cleared_root = clear_database_root(storage_root_path)
    return {
        "database_root": str(cleared_root.resolve()),
    }


def delete_storage_rows(
    storage_path: str,
    row_selectors: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized_selectors = [
        (
            str(item.get("dataset_id", "")).strip(),
            str(item.get("source_file", "")).strip(),
            int(item.get("row_number")),
        )
        for item in row_selectors
        if str(item.get("dataset_id", "")).strip()
        and str(item.get("source_file", "")).strip()
        and item.get("row_number") is not None
    ]
    repository = Repository(storage_path)
    existing_rows = _collect_row_records(repository.load_measurements())
    existing_row_keys = set(existing_rows.keys())
    matched_row_keys = {
        (dataset_id, source_file, row_number)
        for dataset_id, source_file, row_number in normalized_selectors
        if (dataset_id, source_file, row_number) in existing_row_keys
    }
    deleted_measurement_count = repository.delete_measurements(normalized_selectors)
    return {
        "storage": str(Path(storage_path).resolve()),
        "deleted_row_count": len(matched_row_keys),
        "deleted_measurement_count": deleted_measurement_count,
    }


def save_debug_bundle(
    bundle_path: str,
    gui_settings: dict[str, Any],
    current_results: dict[str, Any],
    log_text: str,
    template_path: str | None = None,
    input_path: str | None = None,
    storage_path: str | None = None,
    golden_path: str | None = None,
    output_path: str | None = None,
    if_exists: str = "overwrite",
) -> dict[str, Any]:
    storage_summary = None
    import_history = None
    resolved_template_path = template_path if template_path and Path(template_path).exists() else None
    if storage_path and Path(storage_path).exists():
        storage_summary = describe_storage(
            storage_path,
            template_path=resolved_template_path,
            limit=500,
        )
        import_history = list_import_history(storage_path)
    return export_debug_bundle(
        bundle_path=bundle_path,
        gui_settings=gui_settings,
        current_results=current_results,
        log_text=log_text,
        template_path=template_path,
        input_path=input_path,
        storage_path=storage_path,
        golden_path=golden_path,
        output_path=output_path,
        storage_summary=storage_summary,
        import_history=import_history,
        if_exists=if_exists,
    )


def generate_report(
    template_path: str,
    input_path: str,
    output_path: str,
    built_golden_path: str | None = None,
    outlier_fail_method_override: str | None = None,
    zscore_threshold_override: float | None = None,
    if_exists: str = "overwrite",
) -> dict:
    return generate_chip_report(
        template_path,
        input_path,
        output_path,
        built_golden_path=built_golden_path,
        outlier_fail_method_override=outlier_fail_method_override,
        zscore_threshold_override=zscore_threshold_override,
        if_exists=if_exists,
    )


def generate_report_from_storage(
    template_path: str,
    storage_path: str,
    output_path: str,
    built_golden_path: str | None = None,
    outlier_fail_method_override: str | None = None,
    zscore_threshold_override: float | None = None,
    dataset_ids: list[str] | None = None,
    dimension_filters: dict[str, dict[str, list[str]]] | None = None,
    if_exists: str = "overwrite",
) -> dict[str, Any]:
    repository = Repository(storage_path)
    measurements = _filter_measurements(
        repository.load_measurements(),
        dataset_ids=dataset_ids,
        dimension_filters=dimension_filters,
    )
    if not measurements:
        raise ValueError("Current database scope does not contain any measurement data.")
    return generate_chip_report_from_measurements(
        template_path=template_path,
        measurements=measurements,
        output_path=output_path,
        built_golden_path=built_golden_path,
        outlier_fail_method_override=outlier_fail_method_override,
        zscore_threshold_override=zscore_threshold_override,
        source_label=str(Path(storage_path).resolve()),
        if_exists=if_exists,
    )


def analyze_report_failures(
    template_path: str,
    input_path: str,
    built_golden_path: str | None = None,
    zscore_threshold_override: float | None = None,
) -> list[AnomalyResult]:
    return collect_report_failures(
        template_path,
        input_path,
        built_golden_path=built_golden_path,
        zscore_threshold_override=zscore_threshold_override,
    )


def analyze_report_outlier_summary(
    template_path: str,
    input_path: str,
    built_golden_path: str | None = None,
    outlier_fail_method_override: str | None = None,
    zscore_threshold_override: float | None = None,
) -> list[dict[str, str]]:
    return collect_outlier_summary_rows(
        template_path,
        input_path,
        built_golden_path=built_golden_path,
        outlier_fail_method_override=outlier_fail_method_override,
        zscore_threshold_override=zscore_threshold_override,
    )


def analyze_report_outlier_summary_artifacts(
    template_path: str,
    input_path: str,
    built_golden_path: str | None = None,
    outlier_fail_method_override: str | None = None,
    zscore_threshold_override: float | None = None,
) -> dict[str, list[dict[str, Any]]]:
    return collect_outlier_summary_artifacts(
        template_path,
        input_path,
        built_golden_path=built_golden_path,
        outlier_fail_method_override=outlier_fail_method_override,
        zscore_threshold_override=zscore_threshold_override,
    )


def analyze_report_outlier_ratios(
    template_path: str,
    input_path: str,
    built_golden_path: str | None = None,
    outlier_fail_method_override: str | None = None,
    zscore_threshold_override: float | None = None,
) -> list[dict[str, Any]]:
    return collect_outlier_ratio_rows(
        template_path,
        input_path,
        built_golden_path=built_golden_path,
        outlier_fail_method_override=outlier_fail_method_override,
        zscore_threshold_override=zscore_threshold_override,
    )


def analyze_report_outlier_summary_from_storage(
    template_path: str,
    storage_path: str,
    built_golden_path: str | None = None,
    outlier_fail_method_override: str | None = None,
    zscore_threshold_override: float | None = None,
    dataset_ids: list[str] | None = None,
    dimension_filters: dict[str, dict[str, list[str]]] | None = None,
) -> list[dict[str, str]]:
    repository = Repository(storage_path)
    measurements = _filter_measurements(
        repository.load_measurements(),
        dataset_ids=dataset_ids,
        dimension_filters=dimension_filters,
    )
    if not measurements:
        return []
    return collect_outlier_summary_rows_from_measurements(
        template_path=template_path,
        measurements=measurements,
        built_golden_path=built_golden_path,
        outlier_fail_method_override=outlier_fail_method_override,
        zscore_threshold_override=zscore_threshold_override,
    )


def analyze_report_outlier_summary_artifacts_from_storage(
    template_path: str,
    storage_path: str,
    built_golden_path: str | None = None,
    outlier_fail_method_override: str | None = None,
    zscore_threshold_override: float | None = None,
    dataset_ids: list[str] | None = None,
    dimension_filters: dict[str, dict[str, list[str]]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    repository = Repository(storage_path)
    measurements = _filter_measurements(
        repository.load_measurements(),
        dataset_ids=dataset_ids,
        dimension_filters=dimension_filters,
    )
    if not measurements:
        return {"summary_rows": [], "ratio_rows": []}
    return collect_outlier_summary_artifacts_from_measurements(
        template_path=template_path,
        measurements=measurements,
        built_golden_path=built_golden_path,
        outlier_fail_method_override=outlier_fail_method_override,
        zscore_threshold_override=zscore_threshold_override,
    )


def analyze_report_outlier_ratios_from_storage(
    template_path: str,
    storage_path: str,
    built_golden_path: str | None = None,
    outlier_fail_method_override: str | None = None,
    zscore_threshold_override: float | None = None,
    dataset_ids: list[str] | None = None,
    dimension_filters: dict[str, dict[str, list[str]]] | None = None,
) -> list[dict[str, Any]]:
    repository = Repository(storage_path)
    measurements = _filter_measurements(
        repository.load_measurements(),
        dataset_ids=dataset_ids,
        dimension_filters=dimension_filters,
    )
    if not measurements:
        return []
    return collect_outlier_ratio_rows_from_measurements(
        template_path=template_path,
        measurements=measurements,
        built_golden_path=built_golden_path,
        outlier_fail_method_override=outlier_fail_method_override,
        zscore_threshold_override=zscore_threshold_override,
    )


def summarize_built_golden_coverage_for_input(
    template_path: str,
    input_path: str,
    golden_path: str,
) -> dict[str, Any]:
    template = load_template(template_path)
    table = load_table(input_path, template=template)
    measurements = build_measurements(
        template=template,
        rows=table.rows,
        dataset_id="coverage-preview",
        source_file=str(Path(input_path).resolve()),
    )
    golden = GoldenReference.from_dict(
        json.loads(Path(golden_path).read_text(encoding="utf-8"))
    )
    payload = summarize_golden_coverage(measurements, golden)
    payload.update(
        {
            "scope": "current_input_file",
            "input": str(Path(input_path).resolve()),
            "golden": str(Path(golden_path).resolve()),
        }
    )
    return payload


def summarize_built_golden_coverage_for_storage(
    storage_path: str,
    golden_path: str,
    dataset_ids: list[str] | None = None,
    dimension_filters: dict[str, dict[str, list[str]]] | None = None,
) -> dict[str, Any]:
    repository = Repository(storage_path)
    measurements = _filter_measurements(
        repository.load_measurements(),
        dataset_ids=dataset_ids,
        dimension_filters=dimension_filters,
    )
    golden = repository.load_golden(golden_path)
    payload = summarize_golden_coverage(measurements, golden)
    payload.update(
        {
            "scope": "database",
            "storage": str(Path(storage_path).resolve()),
            "golden": str(Path(golden_path).resolve()),
        }
    )
    return payload


def create_golden_reference(
    storage_path: str,
    name: str,
    reference_dimensions: list[str],
    filters: dict[str, str],
    center_method: str,
    threshold_mode: str,
    relative_limit: float | None,
    sigma_multiplier: float | None,
    if_exists: str = "overwrite",
) -> tuple[GoldenReference, str]:
    repository = Repository(storage_path)
    measurements = repository.load_measurements()
    reference = build_golden_reference(
        name=name,
        measurements=measurements,
        reference_dimensions=reference_dimensions,
        filters=filters,
        center_method=center_method,
        threshold_mode=threshold_mode,
        relative_limit=relative_limit,
        sigma_multiplier=sigma_multiplier,
    )
    path = repository.save_golden(reference, if_exists=if_exists)
    return reference, str(path.resolve())


def parse_csv_items(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_filters(items: list[str]) -> dict[str, str]:
    filters: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid filter: {item}. Expected key=value")
        key, raw_value = item.split("=", 1)
        filters[key.strip()] = raw_value.strip()
    return filters


def parse_filter_text(value: str) -> dict[str, str]:
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    return parse_filters(lines)


def build_dimension_filters(
    sample_ids: list[str] | None = None,
    reliability_nodes: list[str] | None = None,
    exclude_sample_ids: list[str] | None = None,
    exclude_reliability_nodes: list[str] | None = None,
) -> dict[str, dict[str, list[str]]]:
    filters: dict[str, dict[str, list[str]]] = {}
    if sample_ids:
        filters.setdefault("sample_id", {})["include"] = [item for item in sample_ids if item]
    if exclude_sample_ids:
        filters.setdefault("sample_id", {})["exclude"] = [item for item in exclude_sample_ids if item]
    if reliability_nodes:
        filters.setdefault("reliability_node", {})["include"] = [
            item for item in reliability_nodes if item
        ]
    if exclude_reliability_nodes:
        filters.setdefault("reliability_node", {})["exclude"] = [
            item for item in exclude_reliability_nodes if item
        ]
    return filters


def _build_dataset_payload(
    dataset_id: str,
    source_file: str,
    template_name: str,
    measurement_count: int,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "dataset_id": dataset_id,
        "source_file": source_file,
        "template_name": template_name,
        "measurement_count": measurement_count,
    }
    if metadata:
        payload.update(metadata)
    return payload


def _filter_measurements(
    measurements: list[MeasurementRecord],
    dataset_ids: list[str] | None = None,
    dimension_filters: dict[str, dict[str, list[str]]] | None = None,
) -> list[MeasurementRecord]:
    dataset_id_set = {item for item in (dataset_ids or []) if item}
    normalized_dimension_filters: dict[str, dict[str, set[str]]] = {}
    for key, config in (dimension_filters or {}).items():
        include_values = {value for value in config.get("include", []) if value}
        exclude_values = {value for value in config.get("exclude", []) if value}
        if include_values or exclude_values:
            normalized_dimension_filters[key] = {
                "include": include_values,
                "exclude": exclude_values,
            }
    filtered: list[MeasurementRecord] = []
    for item in measurements:
        if dataset_id_set and item.dataset_id not in dataset_id_set:
            continue
        if normalized_dimension_filters and not _matches_dimension_filters(
            item.dimensions,
            normalized_dimension_filters,
        ):
            continue
        filtered.append(item)
    return filtered


def _matches_dimension_filters(
    dimensions: dict[str, str],
    filters: dict[str, dict[str, set[str]]],
) -> bool:
    for key, filter_config in filters.items():
        value = dimensions.get(key, "")
        include_values = filter_config.get("include", set())
        exclude_values = filter_config.get("exclude", set())
        if include_values and value not in include_values:
            return False
        if exclude_values and value in exclude_values:
            return False
    return True


def _build_import_preview(
    existing_measurements: list[MeasurementRecord],
    incoming_measurements: list[MeasurementRecord],
) -> dict[str, Any]:
    existing_rows = _collect_row_records(existing_measurements)
    incoming_rows = _collect_row_records(incoming_measurements)

    existing_row_groups = list(existing_rows.values())
    incoming_row_groups = list(incoming_rows.values())

    existing_keys = {_row_identity_key(item["dimensions"]) for item in existing_row_groups}
    incoming_keys = {_row_identity_key(item["dimensions"]) for item in incoming_row_groups}
    conflict_keys = existing_keys & incoming_keys

    existing_conflicts = [
        item for item in existing_row_groups if _row_identity_key(item["dimensions"]) in conflict_keys
    ]
    incoming_conflicts = [
        item for item in incoming_row_groups if _row_identity_key(item["dimensions"]) in conflict_keys
    ]

    ordered_dimensions = _resolve_dimension_order(None, [*existing_measurements, *incoming_measurements])

    return {
        "existing_measurement_count": len(existing_measurements),
        "incoming_measurement_count": len(incoming_measurements),
        "existing_row_count": len(existing_row_groups),
        "incoming_row_count": len(incoming_row_groups),
        "existing_conflict_row_count": len(existing_conflicts),
        "conflict_row_count": len(incoming_conflicts),
        "conflict_keys": conflict_keys,
        "conflict_rows_preview": [
            {name: item["dimensions"].get(name, "") for name in ordered_dimensions}
            for item in incoming_conflicts[:20]
        ],
        "has_repeat_dimension": all(
            REPEAT_DIMENSION_NAME in item["dimensions"]
            and str(item["dimensions"].get(REPEAT_DIMENSION_NAME, "")).strip() != ""
            for item in incoming_conflicts
        ),
        "dimensions": ordered_dimensions,
    }


def _format_import_conflict_message(preview: dict[str, Any]) -> str:
    lines = [
        (
            "Detected duplicate sample attributes in current database. "
            "Please choose replace or append."
        ),
        (
            f"Incoming conflicting rows: {preview['conflict_row_count']}, "
            f"existing rows affected: {preview['existing_conflict_row_count']}."
        ),
    ]
    if preview["conflict_rows_preview"]:
        lines.append("Examples:")
        for item in preview["conflict_rows_preview"][:5]:
            text = ", ".join(f"{key}={value}" for key, value in item.items() if value != "")
            lines.append(f"- {text}")
    if not preview["has_repeat_dimension"]:
        lines.append(
            "Append is unavailable because this template does not provide repeat_id."
        )
    return "\n".join(lines)


def _append_with_shifted_repeats(
    existing_measurements: list[MeasurementRecord],
    incoming_measurements: list[MeasurementRecord],
) -> tuple[list[MeasurementRecord], int]:
    existing_rows = _collect_row_records(existing_measurements)
    incoming_rows = _collect_row_records(incoming_measurements)
    existing_repeat_max = _build_repeat_index_map(existing_rows.values())

    grouped_incoming: dict[tuple[tuple[str, str], ...], list[dict[str, Any]]] = defaultdict(list)
    for row in incoming_rows.values():
        grouped_incoming[_row_identity_key(row["dimensions"])].append(row)

    row_repeat_updates: dict[tuple[str, str, int], str] = {}
    shifted_row_count = 0

    for base_key, rows in grouped_incoming.items():
        if base_key not in existing_repeat_max:
            continue
        if any(REPEAT_DIMENSION_NAME not in row["dimensions"] for row in rows):
            raise ValueError(
                "Append mode requires repeat_id for all conflicting rows."
            )
        rows.sort(
            key=lambda item: (
                _parse_repeat_index(item["dimensions"].get(REPEAT_DIMENSION_NAME)) or 0,
                item["row_number"],
            )
        )
        next_repeat = existing_repeat_max[base_key]
        for row in rows:
            next_repeat += 1
            row_repeat_updates[row["row_key"]] = str(next_repeat)
            shifted_row_count += 1

    adjusted_measurements: list[MeasurementRecord] = []
    for item in incoming_measurements:
        row_key = (item.dataset_id, item.source_file, item.row_number)
        if row_key in row_repeat_updates:
            dimensions = dict(item.dimensions)
            dimensions[REPEAT_DIMENSION_NAME] = row_repeat_updates[row_key]
            adjusted_measurements.append(
                MeasurementRecord(
                    dataset_id=item.dataset_id,
                    source_file=item.source_file,
                    row_number=item.row_number,
                    logical_metric=item.logical_metric,
                    group_id=item.group_id,
                    group_display_name=item.group_display_name,
                    presentation_group=item.presentation_group,
                    raw_column=item.raw_column,
                    value=item.value,
                    dimensions=dimensions,
                )
            )
        else:
            adjusted_measurements.append(item)
    return adjusted_measurements, shifted_row_count


def _collect_row_records(measurements: list) -> dict[tuple[str, str, int], dict[str, Any]]:
    rows: dict[tuple[str, str, int], dict[str, Any]] = {}
    for item in measurements:
        row_key = (item.dataset_id, item.source_file, item.row_number)
        entry = rows.setdefault(
            row_key,
            {
                "row_key": row_key,
                "dataset_id": item.dataset_id,
                "source_file": item.source_file,
                "row_number": item.row_number,
                "dimensions": dict(item.dimensions),
                "measurement_count": 0,
            },
        )
        entry["measurement_count"] += 1
    return rows


def _build_repeat_index_map(rows: Any) -> dict[tuple[tuple[str, str], ...], int]:
    repeat_map: dict[tuple[tuple[str, str], ...], int] = {}
    for row in rows:
        repeat_value = row["dimensions"].get(REPEAT_DIMENSION_NAME)
        repeat_index = _parse_repeat_index(repeat_value)
        if repeat_index is None:
            continue
        base_key = _row_identity_key(row["dimensions"])
        repeat_map[base_key] = max(repeat_map.get(base_key, 0), repeat_index)
    return repeat_map


def _parse_repeat_index(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError as exc:
        raise ValueError(
            f"repeat_id must be an integer when append mode is used. Got: {text}"
        ) from exc


def _row_identity_key(dimensions: dict[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (key, value)
            for key, value in dimensions.items()
            if key != REPEAT_DIMENSION_NAME
        )
    )


def _resolve_dimension_order(
    template_path: str | None,
    measurements: list,
) -> list[str]:
    if template_path:
        try:
            template = load_template(template_path)
            ordered = [item.name for item in template.row_dimensions]
            existing = {
                key
                for measurement in measurements
                for key in measurement.dimensions.keys()
            }
            return ordered + sorted(existing - set(ordered))
        except Exception:
            pass
    dimension_names = {
        key
        for measurement in measurements
        for key in measurement.dimensions.keys()
    }
    return sorted(dimension_names)
