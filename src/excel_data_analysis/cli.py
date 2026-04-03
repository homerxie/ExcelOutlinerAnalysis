from __future__ import annotations

import argparse
import json
from pathlib import Path

from .service import (
    analyze_report_failures,
    build_dimension_filters,
    create_golden_reference,
    describe_storage,
    generate_report,
    generate_report_from_storage,
    import_dataset,
    list_import_history,
    parse_csv_items,
    parse_filters,
    preview_import,
)
from .template import load_template, save_template, summarize_template, validate_template_file


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="excel-data-analysis",
        description="Template-driven Excel/CSV anomaly analysis",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import-data", help="Import a table into storage")
    import_parser.add_argument("--template", required=True)
    import_parser.add_argument("--input", required=True)
    import_parser.add_argument("--storage", required=True)
    import_parser.add_argument(
        "--conflict-mode",
        choices=["error", "replace", "append"],
        default="error",
    )

    preview_import_parser = subparsers.add_parser(
        "preview-import",
        help="Preview import conflicts before writing data into storage",
    )
    preview_import_parser.add_argument("--template", required=True)
    preview_import_parser.add_argument("--input", required=True)
    preview_import_parser.add_argument("--storage", required=True)

    show_storage_parser = subparsers.add_parser(
        "show-storage",
        help="Show current storage/database content summary",
    )
    show_storage_parser.add_argument("--storage", required=True)
    show_storage_parser.add_argument("--template")
    show_storage_parser.add_argument("--limit", type=int, default=200)

    golden_parser = subparsers.add_parser("build-golden", help="Build a golden reference")
    golden_parser.add_argument("--storage", required=True)
    golden_parser.add_argument("--name", required=True)
    golden_parser.add_argument("--reference-dims", required=True)
    golden_parser.add_argument("--filter", action="append", default=[])
    golden_parser.add_argument(
        "--center-method",
        choices=["mean", "median"],
        default="mean",
    )
    golden_parser.add_argument(
        "--threshold-mode",
        choices=["relative", "sigma", "hybrid"],
        default="relative",
    )
    golden_parser.add_argument("--relative-limit", type=float)
    golden_parser.add_argument("--sigma-multiplier", type=float)
    golden_parser.add_argument(
        "--if-exists",
        choices=["error", "overwrite", "timestamp"],
        default="error",
    )

    show_imports_parser = subparsers.add_parser(
        "show-imports",
        help="Show import history for the current database",
    )
    show_imports_parser.add_argument("--storage", required=True)

    report_parser = subparsers.add_parser(
        "generate-report",
        help="Generate the multi-sheet chip reliability report from an input workbook or a database scope",
    )
    report_parser.add_argument("--template", required=True)
    report_parser.add_argument("--output", required=True)
    report_source = report_parser.add_mutually_exclusive_group(required=True)
    report_source.add_argument("--input")
    report_source.add_argument("--storage")
    report_parser.add_argument("--golden")
    report_parser.add_argument("--dataset-id", action="append", default=[])
    report_parser.add_argument("--sample-ids", default="")
    report_parser.add_argument("--except-sample-ids", default="")
    report_parser.add_argument("--nodes", default="")
    report_parser.add_argument("--except-nodes", default="")
    report_parser.add_argument(
        "--outlier-fail-mode",
        choices=[
            "modified_z_score",
            "golden_deviation",
            "zscore_and_golden",
            "zscore_or_golden",
        ],
    )
    report_parser.add_argument("--z-threshold", type=float)
    report_parser.add_argument(
        "--if-exists",
        choices=["error", "overwrite", "timestamp"],
        default="error",
    )

    report_check_parser = subparsers.add_parser(
        "report-failures",
        help="List all fail items used by the multi-sheet report",
    )
    report_check_parser.add_argument("--template", required=True)
    report_check_parser.add_argument("--input", required=True)
    report_check_parser.add_argument("--golden")
    report_check_parser.add_argument("--z-threshold", type=float)

    validate_template_parser = subparsers.add_parser(
        "validate-template",
        help="Validate a template file in JSON or Excel format",
    )
    validate_template_parser.add_argument("--input", required=True)

    template_to_json_parser = subparsers.add_parser(
        "template-to-json",
        help="Convert a template file to JSON format",
    )
    template_to_json_parser.add_argument("--input", required=True)
    template_to_json_parser.add_argument("--output")
    template_to_json_parser.add_argument(
        "--if-exists",
        choices=["error", "overwrite", "timestamp"],
        default="error",
    )

    template_to_xlsx_parser = subparsers.add_parser(
        "template-to-xlsx",
        help="Convert a template file to Excel format",
    )
    template_to_xlsx_parser.add_argument("--input", required=True)
    template_to_xlsx_parser.add_argument("--output")
    template_to_xlsx_parser.add_argument(
        "--if-exists",
        choices=["error", "overwrite", "timestamp"],
        default="error",
    )

    args = parser.parse_args()

    if args.command == "import-data":
        handle_import(args)
        return
    if args.command == "preview-import":
        handle_preview_import(args)
        return
    if args.command == "show-storage":
        handle_show_storage(args)
        return
    if args.command == "build-golden":
        handle_build_golden(args)
        return
    if args.command == "show-imports":
        handle_show_imports(args)
        return
    if args.command == "generate-report":
        handle_generate_report(args)
        return
    if args.command == "report-failures":
        handle_report_failures(args)
        return
    if args.command == "validate-template":
        handle_validate_template(args)
        return
    if args.command == "template-to-json":
        handle_template_to_json(args)
        return
    if args.command == "template-to-xlsx":
        handle_template_to_xlsx(args)
        return


def handle_import(args: argparse.Namespace) -> None:
    payload = import_dataset(
        args.template,
        args.input,
        args.storage,
        conflict_mode=args.conflict_mode,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def handle_preview_import(args: argparse.Namespace) -> None:
    payload = preview_import(args.template, args.input, args.storage)
    payload = dict(payload)
    payload.pop("conflict_keys", None)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def handle_show_storage(args: argparse.Namespace) -> None:
    payload = describe_storage(args.storage, template_path=args.template, limit=args.limit)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def handle_build_golden(args: argparse.Namespace) -> None:
    reference, path = create_golden_reference(
        storage_path=args.storage,
        name=args.name,
        reference_dimensions=parse_csv_items(args.reference_dims),
        filters=parse_filters(args.filter),
        center_method=args.center_method,
        threshold_mode=args.threshold_mode,
        relative_limit=args.relative_limit,
        sigma_multiplier=args.sigma_multiplier,
        if_exists=args.if_exists,
    )
    print(
        json.dumps(
            {
                "golden_name": reference.name,
                "metric_count": len(reference.metrics),
                "center_method": reference.center_method,
                "saved_to": path,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def handle_show_imports(args: argparse.Namespace) -> None:
    print(json.dumps(list_import_history(args.storage), ensure_ascii=False, indent=2))


def handle_generate_report(args: argparse.Namespace) -> None:
    if args.input:
        payload = generate_report(
            args.template,
            args.input,
            args.output,
            built_golden_path=args.golden,
            outlier_fail_method_override=args.outlier_fail_mode,
            zscore_threshold_override=args.z_threshold,
            if_exists=args.if_exists,
        )
    else:
        payload = generate_report_from_storage(
            template_path=args.template,
            storage_path=args.storage,
            output_path=args.output,
            built_golden_path=args.golden,
            outlier_fail_method_override=args.outlier_fail_mode,
            zscore_threshold_override=args.z_threshold,
            dataset_ids=args.dataset_id,
            dimension_filters=build_dimension_filters(
                sample_ids=parse_csv_items(args.sample_ids),
                reliability_nodes=parse_csv_items(args.nodes),
                exclude_sample_ids=parse_csv_items(args.except_sample_ids),
                exclude_reliability_nodes=parse_csv_items(args.except_nodes),
            ),
            if_exists=args.if_exists,
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def handle_report_failures(args: argparse.Namespace) -> None:
    payload = [
        item.to_dict()
        for item in analyze_report_failures(
            args.template,
            args.input,
            built_golden_path=args.golden,
            zscore_threshold_override=args.z_threshold,
        )
    ]
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def handle_validate_template(args: argparse.Namespace) -> None:
    template = validate_template_file(args.input)
    print(
        json.dumps(
            {
                "input": str(Path(args.input).resolve()),
                "format": Path(args.input).suffix.lower().lstrip("."),
                "valid": True,
                "summary": summarize_template(template),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def handle_template_to_json(args: argparse.Namespace) -> None:
    template = load_template(args.input)
    output = args.output or str(Path(args.input).with_suffix(".json"))
    resolved = save_template(template, output, if_exists=args.if_exists)
    print(
        json.dumps(
            {
                "input": str(Path(args.input).resolve()),
                "output": str(resolved.resolve()),
                "summary": summarize_template(template),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def handle_template_to_xlsx(args: argparse.Namespace) -> None:
    template = load_template(args.input)
    output = args.output or str(Path(args.input).with_suffix(".xlsx"))
    resolved = save_template(template, output, if_exists=args.if_exists)
    print(
        json.dumps(
            {
                "input": str(Path(args.input).resolve()),
                "output": str(resolved.resolve()),
                "summary": summarize_template(template),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
if __name__ == "__main__":
    main()
