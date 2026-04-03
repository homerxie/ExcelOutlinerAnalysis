from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import shlex
import shutil
from typing import Any

from .output_paths import prepare_output_directory


def export_debug_bundle(
    bundle_path: str | Path,
    gui_settings: dict[str, Any],
    current_results: dict[str, Any],
    log_text: str,
    template_path: str | None = None,
    input_path: str | None = None,
    storage_path: str | None = None,
    golden_path: str | None = None,
    output_path: str | None = None,
    storage_summary: dict[str, Any] | None = None,
    import_history: list[dict[str, Any]] | None = None,
    if_exists: str = "overwrite",
) -> dict[str, Any]:
    bundle_root = prepare_output_directory(bundle_path, if_exists=if_exists)
    files_dir = bundle_root / "files"
    database_dir = bundle_root / "database_snapshot"
    repro_dir = bundle_root / "repro_output"
    files_dir.mkdir(parents=True, exist_ok=True)
    repro_dir.mkdir(parents=True, exist_ok=True)

    copied_files: dict[str, dict[str, Any]] = {}
    copied_files["template"] = _copy_file_if_present(template_path, files_dir / "template")
    copied_files["input"] = _copy_file_if_present(input_path, files_dir / "input")
    copied_files["golden"] = _copy_file_if_present(golden_path, files_dir / "golden")
    copied_files["current_output"] = _copy_file_if_present(output_path, files_dir / "current_output")

    storage_snapshot = _copy_storage_snapshot(storage_path, database_dir)
    if storage_summary is not None:
        _write_json(bundle_root / "storage_summary.json", storage_summary)
    if import_history is not None:
        _write_json(bundle_root / "import_history.json", import_history)

    _write_json(bundle_root / "gui_settings.json", gui_settings)
    _write_json(bundle_root / "current_results.json", current_results)
    (bundle_root / "log.txt").write_text(log_text or "", encoding="utf-8")

    cli_repro = _build_cli_repro(
        gui_settings=gui_settings,
        copied_files=copied_files,
        storage_snapshot=storage_snapshot,
        bundle_root=bundle_root,
    )
    _write_json(bundle_root / "cli_repro.json", cli_repro)
    (bundle_root / "README.txt").write_text(
        _build_readme_text(bundle_root, cli_repro),
        encoding="utf-8",
    )

    manifest = {
        "bundle_format_version": 1,
        "created_at_local": datetime.now().isoformat(timespec="seconds"),
        "bundle_root": str(bundle_root.resolve()),
        "files": copied_files,
        "storage_snapshot": storage_snapshot,
        "cli_command_count": len(cli_repro["commands"]),
    }
    _write_json(bundle_root / "manifest.json", manifest)
    return manifest


def _copy_file_if_present(source_path: str | None, destination_base: Path) -> dict[str, Any]:
    if not source_path:
        return {"status": "not_configured"}
    source = Path(source_path)
    if not source.exists() or not source.is_file():
        return {
            "status": "missing",
            "source": str(source.resolve()) if source.exists() else str(source),
        }
    destination = destination_base.with_suffix(source.suffix)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "status": "copied",
        "source": str(source.resolve()),
        "bundle_path": str(destination),
    }


def _copy_storage_snapshot(source_path: str | None, destination: Path) -> dict[str, Any]:
    if not source_path:
        return {"status": "not_configured"}
    source = Path(source_path)
    if not source.exists() or not source.is_dir():
        return {
            "status": "missing",
            "source": str(source.resolve()) if source.exists() else str(source),
        }

    destination.mkdir(parents=True, exist_ok=True)
    copied_entries: list[str] = []
    for file_name in ("measurements.jsonl", "datasets.jsonl"):
        source_file = source / file_name
        if source_file.exists():
            shutil.copy2(source_file, destination / file_name)
            copied_entries.append(file_name)
    for directory_name in ("golden", "imports"):
        source_directory = source / directory_name
        if source_directory.exists() and source_directory.is_dir():
            shutil.copytree(source_directory, destination / directory_name, dirs_exist_ok=True)
            copied_entries.append(directory_name)
    return {
        "status": "copied",
        "source": str(source.resolve()),
        "bundle_path": str(destination),
        "entries": copied_entries,
    }


def _build_cli_repro(
    gui_settings: dict[str, Any],
    copied_files: dict[str, dict[str, Any]],
    storage_snapshot: dict[str, Any],
    bundle_root: Path,
) -> dict[str, Any]:
    paths = gui_settings.get("paths", {})
    analysis = gui_settings.get("analysis", {})
    golden_settings = gui_settings.get("golden", {})
    commands: list[dict[str, Any]] = []

    template_path = _bundle_relative_path(copied_files.get("template"), bundle_root)
    input_path = _bundle_relative_path(copied_files.get("input"), bundle_root)
    golden_path = _bundle_relative_path(copied_files.get("golden"), bundle_root)
    storage_path = _bundle_relative_storage_path(storage_snapshot, bundle_root)
    output_path = str(Path("repro_output") / "reproduced_report.xlsx")

    if template_path and storage_path:
        show_storage_argv = [
            "python",
            "-m",
            "excel_data_analysis.cli",
            "show-storage",
            "--storage",
            storage_path,
            "--template",
            template_path,
        ]
        commands.append(_build_command_entry("show_storage", show_storage_argv))

    report_argv: list[str] | None = None
    if template_path:
        report_argv = [
            "python",
            "-m",
            "excel_data_analysis.cli",
            "generate-report",
            "--template",
            template_path,
        ]
        analysis_scope = str(analysis.get("analysis_scope", "current_input_file"))
        if analysis_scope == "current_input_file" and input_path:
            report_argv.extend(["--input", input_path])
        elif storage_path:
            report_argv.extend(["--storage", storage_path])
            for dataset_id in analysis.get("selected_dataset_ids", []):
                report_argv.extend(["--dataset-id", str(dataset_id)])
            sample_ids = str(analysis.get("sample_ids_text", "")).strip()
            if sample_ids:
                report_argv.extend(["--sample-ids", sample_ids])
            except_sample_ids = str(analysis.get("exclude_sample_ids_text", "")).strip()
            if except_sample_ids:
                report_argv.extend(["--except-sample-ids", except_sample_ids])
            nodes = str(analysis.get("nodes_text", "")).strip()
            if nodes:
                report_argv.extend(["--nodes", nodes])
            except_nodes = str(analysis.get("exclude_nodes_text", "")).strip()
            if except_nodes:
                report_argv.extend(["--except-nodes", except_nodes])
        else:
            report_argv = None

        if report_argv is not None:
            report_argv.extend(["--output", output_path])
            if str(golden_settings.get("golden_source", "")) == "built_golden_file" and golden_path:
                report_argv.extend(["--golden", golden_path])
            outlier_fail_mode = str(analysis.get("outlier_fail_mode", "")).strip()
            if outlier_fail_mode:
                report_argv.extend(["--outlier-fail-mode", outlier_fail_mode])
            z_threshold = analysis.get("z_threshold")
            if z_threshold is not None:
                report_argv.extend(["--z-threshold", str(z_threshold)])
            commands.append(_build_command_entry("generate_report", report_argv))

    if template_path and input_path and storage_path:
        preview_argv = [
            "python",
            "-m",
            "excel_data_analysis.cli",
            "preview-import",
            "--template",
            template_path,
            "--input",
            input_path,
            "--storage",
            storage_path,
        ]
        commands.append(_build_command_entry("preview_import", preview_argv))

    return {
        "notes": [
            "Activate the project environment before running these commands.",
            "Command paths are relative to the debug bundle root.",
            "If you use Windows, you can reuse the argv arrays directly even if shell quoting differs.",
        ],
        "original_paths": paths,
        "commands": commands,
    }


def _build_command_entry(command_id: str, argv: list[str]) -> dict[str, Any]:
    return {
        "id": command_id,
        "argv": argv,
        "command_text": shlex.join(argv),
    }


def _bundle_relative_path(file_info: dict[str, Any] | None, bundle_root: Path) -> str | None:
    if not file_info or file_info.get("status") != "copied":
        return None
    return str(Path(file_info["bundle_path"]).resolve().relative_to(bundle_root.resolve()))


def _bundle_relative_storage_path(storage_snapshot: dict[str, Any], bundle_root: Path) -> str | None:
    if storage_snapshot.get("status") != "copied":
        return None
    return str(
        Path(storage_snapshot["bundle_path"]).resolve().relative_to(bundle_root.resolve())
    )


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_readme_text(bundle_root: Path, cli_repro: dict[str, Any]) -> str:
    lines = [
        "Excel Data Analysis Debug Bundle",
        "",
        f"Bundle Root: {bundle_root.resolve()}",
        "",
        "Key Files:",
        "- manifest.json: overall bundle summary",
        "- gui_settings.json: GUI values when the bundle was saved",
        "- current_results.json: current result payloads shown in the GUI",
        "- storage_summary.json: database summary at save time",
        "- import_history.json: import history at save time",
        "- cli_repro.json: suggested CLI argv and command text",
        "- log.txt: current GUI log pane content",
        "",
        "Suggested Commands:",
    ]
    for command in cli_repro.get("commands", []):
        lines.append(f"- {command.get('id')}: {command.get('command_text')}")
    return "\n".join(lines) + "\n"
