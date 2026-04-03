from __future__ import annotations

import json
import sys
from pathlib import Path

from ..gui_state import load_gui_state, save_gui_state
from ..runtime import (
    bundled_template_path,
    default_database_root,
    default_dialog_dir,
    default_output_path,
)
from ..service import (
    analyze_report_outlier_summary_artifacts,
    analyze_report_outlier_summary_artifacts_from_storage,
    build_dimension_filters,
    clear_storage_root,
    create_golden_reference,
    delete_storage_rows,
    discard_storage_workspace_changes,
    describe_storage,
    ensure_storage_workspace,
    generate_report,
    generate_report_from_storage,
    import_dataset,
    list_import_history,
    parse_csv_items,
    parse_filter_text,
    preview_import,
    save_debug_bundle,
    save_storage_workspace,
    save_storage_workspace_as,
    storage_workspace_differs,
    summarize_built_golden_coverage_for_input,
    summarize_built_golden_coverage_for_storage,
)
from ..template import load_template, save_template, summarize_template
from ..workspace import default_database_output_path
from .ui_main_window import Ui_MainWindow

try:
    from PySide6.QtCore import QDateTime, Qt
    from PySide6.QtGui import QCloseEvent
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QInputDialog,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QTableWidgetItem,
    )
except ImportError as exc:
    raise RuntimeError(
        "PySide6 is not installed yet. Activate the project virtual environment and install dependencies first."
    ) from exc


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.current_golden_coverage_summary: dict | None = None
        self.current_outlier_summary_rows: list[dict[str, str]] = []
        self.current_outlier_ratio_rows: list[dict[str, object]] = []
        self.current_storage_headers: list[str] = []
        self.current_workspace_path: str = ""
        self._wire_events()
        self._apply_defaults()
        self._ensure_storage_workspace_for_current_database(silent=True)
        self._prompt_workspace_recovery_if_needed()
        self._update_analysis_mode_state()
        self._refresh_analysis_imports(silent=True)
        self._refresh_storage_overview(silent=True)
        self._refresh_golden_coverage_view(None)
        self._refresh_outlier_summary_view([], [])
        self._load_saved_settings_for_current_database(silent=True)

    def _wire_events(self) -> None:
        self.ui.actionSaveDatabase.triggered.connect(self._save_database)
        self.ui.actionSaveDatabaseAs.triggered.connect(self._save_database_as)
        self.ui.browseTemplateButton.clicked.connect(self._browse_template)
        self.ui.validateTemplateButton.clicked.connect(self._validate_template)
        self.ui.exportTemplateJsonButton.clicked.connect(self._export_template_json)
        self.ui.exportTemplateExcelButton.clicked.connect(self._export_template_excel)
        self.ui.saveDebugBundleButton.clicked.connect(self._save_debug_bundle)
        self.ui.browseInputButton.clicked.connect(self._browse_input)
        self.ui.browseStorageButton.clicked.connect(self._browse_storage)
        self.ui.browseGoldenButton.clicked.connect(self._browse_golden)
        self.ui.browseOutputButton.clicked.connect(self._browse_output)
        self.ui.importButton.clicked.connect(self._import_dataset)
        self.ui.refreshStorageViewButton.clicked.connect(self._refresh_storage_overview)
        self.ui.deleteSelectedRowsButton.clicked.connect(self._delete_selected_storage_rows)
        self.ui.refreshAnalysisImportsButton.clicked.connect(self._refresh_analysis_imports)
        self.ui.buildGoldenButton.clicked.connect(self._build_golden)
        self.ui.runAnalysisButton.clicked.connect(self._run_analysis)
        self.ui.goldenSourceComboBox.currentTextChanged.connect(self._update_analysis_mode_state)
        self.ui.analysisScopeComboBox.currentTextChanged.connect(self._update_analysis_mode_state)
        self.ui.thresholdModeComboBox.currentTextChanged.connect(self._update_golden_threshold_mode_state)

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._should_prompt_save_temp_database_on_close():
            event.accept()
            return
        outcome = self._prompt_save_temp_database_before_exit()
        if outcome == "cancel":
            event.ignore()
            return
        event.accept()

    def _apply_defaults(self) -> None:
        template_path = bundled_template_path()
        self.ui.templatePathEdit.setText(str(template_path.resolve()))
        self.ui.inputPathEdit.setText("")
        self.ui.storagePathEdit.setText(str(default_database_root().resolve()))
        self.ui.goldenNameEdit.setText("sample_t0_golden")
        self.ui.referenceDimsEdit.setText("sample_id")
        self.ui.filtersEdit.setPlainText("reliability_node=T0")
        self.ui.centerMethodComboBox.setCurrentText("mean")
        self.ui.goldenSourceComboBox.setCurrentText("template_direct")
        self.ui.outlierFailModeComboBox.setCurrentText("golden_deviation")
        self.ui.zThresholdSpinBox.setValue(3.5)
        self.ui.analysisScopeComboBox.setCurrentText("current_input_file")
        self._sync_template_backed_settings_from_template(silent=True)
        self._update_golden_threshold_mode_state()
        self._refresh_default_output_path()

    def _browse_template(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template File",
            self.ui.templatePathEdit.text() or str(default_dialog_dir()),
            "Template Files (*.json *.xlsx);;JSON Files (*.json);;Excel Files (*.xlsx)",
        )
        if path:
            self.ui.templatePathEdit.setText(path)
            self._sync_template_backed_settings_from_template(silent=True)
            self._refresh_storage_overview(silent=True)

    def _validate_template(self) -> None:
        try:
            template_path = self._ensure_template_path()
            template = load_template(template_path)
        except Exception as exc:
            self._show_error("Validate template failed", exc)
            return
        payload = {
            "template_path": str(Path(template_path).resolve()),
            "summary": summarize_template(template),
        }
        self._log("Template valid:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
        QMessageBox.information(self, "Template Valid", json.dumps(payload, ensure_ascii=False, indent=2))
        self.statusBar().showMessage("Template validated.", 5000)

    def _export_template_json(self) -> None:
        self._export_template_with_suffix(".json", "JSON Files (*.json)")

    def _export_template_excel(self) -> None:
        self._export_template_with_suffix(".xlsx", "Excel Files (*.xlsx)")

    def _export_template_with_suffix(self, suffix: str, file_filter: str) -> None:
        try:
            template_path = self._ensure_template_path()
            template = load_template(template_path)
            default_path = str(Path(template_path).with_suffix(suffix))
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                f"Save Template As {suffix.upper().lstrip('.')}",
                default_path,
                file_filter,
            )
            if not output_path:
                return
            resolved_path = self._resolve_existing_output_path(
                output_path,
                "Template output file",
            )
            if resolved_path is None:
                self.statusBar().showMessage("Template export cancelled.", 5000)
                return
            resolved = save_template(template, resolved_path, if_exists="overwrite")
        except Exception as exc:
            self._show_error("Template export failed", exc)
            return
        payload = {
            "input": str(Path(template_path).resolve()),
            "output": str(resolved.resolve()),
            "summary": summarize_template(template),
        }
        self._log("Template converted:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
        self.statusBar().showMessage("Template converted.", 5000)

    def _browse_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Input File", self.ui.inputPathEdit.text() or str(default_dialog_dir()), "Table Files (*.csv *.xlsx *.xlsm)")
        if path:
            self.ui.inputPathEdit.setText(path)

    def _browse_storage(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Database Folder", self.ui.storagePathEdit.text() or str(default_dialog_dir()))
        if path:
            self.ui.storagePathEdit.setText(path)
            self._ensure_storage_workspace_for_current_database(silent=True)
            self._prompt_workspace_recovery_if_needed()
            self._refresh_default_output_path()
            self._refresh_storage_overview(silent=True)
            self._load_saved_settings_for_current_database(silent=True)

    def _browse_golden(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Golden Reference File", self.ui.goldenPathEdit.text() or str(default_dialog_dir()), "JSON Files (*.json)")
        if path:
            self.ui.goldenPathEdit.setText(path)

    def _browse_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Report Output File",
            self.ui.outputPathEdit.text() or str(default_output_path()),
            "Excel Files (*.xlsx)",
        )
        if path:
            self.ui.outputPathEdit.setText(path)

    def _save_debug_bundle(self) -> None:
        try:
            parent = QFileDialog.getExistingDirectory(
                self,
                "Select Folder For Debug Bundle",
                self.ui.storagePathEdit.text() or str(default_dialog_dir()),
            )
            if not parent:
                return
            bundle_path = Path(parent) / "excel_data_analysis_debug_bundle"
            resolved_bundle_path = self._resolve_existing_output_directory(
                bundle_path,
                "Debug bundle folder",
            )
            if resolved_bundle_path is None:
                self.statusBar().showMessage("Save debug bundle cancelled.", 5000)
                return
            payload = save_debug_bundle(
                bundle_path=resolved_bundle_path,
                gui_settings=self._collect_gui_settings_snapshot(),
                current_results=self._collect_current_results_snapshot(),
                log_text=self.ui.logPlainTextEdit.toPlainText(),
                template_path=self.ui.templatePathEdit.text().strip() or None,
                input_path=self.ui.inputPathEdit.text().strip() or None,
                storage_path=self._active_storage_path() or None,
                golden_path=self.ui.goldenPathEdit.text().strip() or None,
                output_path=self.ui.outputPathEdit.text().strip() or None,
                if_exists="overwrite",
            )
        except Exception as exc:
            self._show_error("Save debug bundle failed", exc)
            return
        self._log("Saved debug bundle:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
        self.statusBar().showMessage("Debug bundle saved.", 5000)
        QMessageBox.information(
            self,
            "Debug Bundle Saved",
            (
                "Current GUI settings and results were saved to:\n"
                f"{payload['bundle_root']}"
            ),
        )

    def _save_database(self) -> None:
        database_root = self._database_root_path()
        if not database_root:
            self._show_error("Save database failed", ValueError("Database Folder is required."))
            return
        if Path(database_root).resolve() == default_database_root().resolve():
            self._save_database_as()
            return
        try:
            payload = save_storage_workspace(database_root)
            target = save_gui_state(
                database_root,
                self._collect_persistent_gui_settings(),
            )
        except Exception as exc:
            self._show_error("Save database failed", exc)
            return
        self._ensure_storage_workspace_for_current_database(silent=True)
        self._log(
            "Saved database:\n"
            + json.dumps(
                {
                    "workspace_merge": payload,
                    "settings_file": str(target),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        self.statusBar().showMessage("Database saved.", 5000)
        QMessageBox.information(
            self,
            "Database Saved",
            (
                "Current temp workspace has been merged into the database root.\n\n"
                f"Settings file:\n{target}"
            ),
        )

    def _save_database_as(self) -> None:
        database_root = self._database_root_path()
        if not database_root:
            self._show_error("Save database as failed", ValueError("Database Folder is required."))
            return
        try:
            saved_path = self._save_database_copy_as(database_root)
        except Exception as exc:
            self._show_error("Save database as failed", exc)
            return
        if not saved_path:
            self.statusBar().showMessage("Save database as cancelled.", 5000)
            return
        self.ui.storagePathEdit.setText(saved_path)
        self._ensure_storage_workspace_for_current_database(silent=True)
        self._refresh_default_output_path()
        self._refresh_storage_overview(silent=True)
        self._load_saved_settings_for_current_database(silent=True)
        self.statusBar().showMessage("Database saved to a new folder.", 5000)
        QMessageBox.information(
            self,
            "Database Saved",
            f"Current workspace was saved as:\n{saved_path}",
        )

    def _save_database_copy_as(self, storage_path: str) -> str | None:
        source_path = Path(storage_path).resolve()
        default_temp_root = default_database_root().resolve()
        parent = QFileDialog.getExistingDirectory(
            self,
            "Select Parent Folder For Saved Database",
            str(default_dialog_dir()),
        )
        if not parent:
            return None
        default_name = "projectDatabase"
        folder_name, ok = QInputDialog.getText(
            self,
            "Database Folder Name",
            "Enter a folder name for the saved database:",
            text=default_name,
        )
        if not ok:
            return None
        folder_name = folder_name.strip()
        if not folder_name:
            raise ValueError("Database folder name cannot be empty.")
        target_path = Path(parent) / folder_name
        resolved_target_path = self._resolve_existing_output_directory(
            target_path,
            "Saved database folder",
        )
        if resolved_target_path is None:
            return None
        resolved_target_path_obj = Path(resolved_target_path).resolve()
        payload = save_storage_workspace_as(
            storage_root_path=storage_path,
            target_storage_root_path=resolved_target_path_obj,
        )
        save_gui_state(resolved_target_path_obj, self._collect_persistent_gui_settings())
        self._log("Saved database copy:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
        if source_path == default_temp_root and resolved_target_path_obj != default_temp_root:
            try:
                cleanup_payload = clear_storage_root(storage_path)
            except Exception as exc:
                self._log(f"Failed to clear tempDatabase after save: {exc}")
                QMessageBox.warning(
                    self,
                    "Temp Database Cleanup Failed",
                    (
                        "Database copy was saved successfully, but the default tempDatabase "
                        "could not be cleared automatically.\n\n"
                        "Please close any files that may still be using tempDatabase and try again later.\n\n"
                        f"Reason: {exc}"
                    ),
                )
            else:
                self._log(
                    "Cleared default tempDatabase after successful save:\n"
                    + json.dumps(cleanup_payload, ensure_ascii=False, indent=2)
                )
        return str(resolved_target_path_obj)

    def _import_dataset(self) -> None:
        try:
            self._ensure_required_paths(require_input=True)
            preview = preview_import(
                self.ui.templatePathEdit.text().strip(),
                self.ui.inputPathEdit.text().strip(),
                self._active_storage_path(),
            )
            conflict_mode = "error"
            if preview["conflict_row_count"]:
                conflict_mode = self._prompt_import_conflict_mode(preview)
                if conflict_mode is None:
                    self.statusBar().showMessage("Import cancelled.", 5000)
                    return
            payload = import_dataset(
                self.ui.templatePathEdit.text().strip(),
                self.ui.inputPathEdit.text().strip(),
                self._active_storage_path(),
                conflict_mode=conflict_mode,
            )
        except Exception as exc:
            self._show_error("Import failed", exc)
            return
        self._log(f"Imported dataset:\n{json.dumps(payload, ensure_ascii=False, indent=2)}")
        self._refresh_storage_overview(silent=True)
        self.statusBar().showMessage("Dataset imported.", 5000)

    def _delete_selected_storage_rows(self) -> None:
        database_root = self._database_root_path()
        if not database_root:
            self._show_error("Delete rows failed", ValueError("Database Folder is required."))
            return
        selectors = self._selected_storage_row_selectors()
        if not selectors:
            QMessageBox.information(
                self,
                "No Rows Selected",
                "Please select one or more database rows to delete.",
            )
            return
        response = QMessageBox.question(
            self,
            "Delete Selected Database Rows",
            (
                f"Delete {len(selectors)} selected database row(s)?\n\n"
                "Use this for cases like mistaken imports or rows that should be removed from the database."
            ),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if response != QMessageBox.Yes:
            self.statusBar().showMessage("Delete rows cancelled.", 5000)
            return
        try:
            payload = delete_storage_rows(self._active_storage_path(), selectors)
        except Exception as exc:
            self._show_error("Delete rows failed", exc)
            return
        self._log("Deleted database rows:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
        self._refresh_storage_overview(silent=True)
        self.statusBar().showMessage("Selected database rows deleted.", 5000)

    def _build_golden(self) -> None:
        try:
            self._ensure_required_paths(require_input=False)
            template_path = self.ui.templatePathEdit.text().strip()
            template = load_template(template_path)
            if self._maybe_write_back_template_settings(
                template_path,
                template,
                scope="build_golden",
            ) is None:
                self.statusBar().showMessage("Build golden cancelled.", 5000)
                return
            golden_name = self.ui.goldenNameEdit.text().strip() or "golden_reference"
            golden_target_path = (
                Path(self._active_storage_path()) / "golden" / f"{golden_name}.json"
            )
            existing_mode = self._resolve_existing_output_mode(
                golden_target_path,
                "Golden reference file",
            )
            if existing_mode is None:
                self.statusBar().showMessage("Build golden cancelled.", 5000)
                return
            reference, path = create_golden_reference(
                storage_path=self._active_storage_path(),
                name=golden_name,
                reference_dimensions=parse_csv_items(self.ui.referenceDimsEdit.text().strip()),
                filters=parse_filter_text(self.ui.filtersEdit.toPlainText()),
                center_method=self.ui.centerMethodComboBox.currentText(),
                threshold_mode=self.ui.thresholdModeComboBox.currentText(),
                relative_limit=self._resolve_relative_limit(),
                sigma_multiplier=self._resolve_sigma_multiplier(),
                if_exists=existing_mode,
            )
        except Exception as exc:
            self._show_error("Build golden failed", exc)
            return
        self.ui.goldenPathEdit.setText(path)
        self._log(
            "Golden built:\n"
            + json.dumps(
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
        self.statusBar().showMessage("Golden reference created.", 5000)

    def _run_analysis(self) -> None:
        try:
            analysis_scope = self.ui.analysisScopeComboBox.currentText()
            self._ensure_analysis_paths(analysis_scope)
            template_path = self.ui.templatePathEdit.text().strip()
            template = load_template(template_path)
            if self._maybe_write_back_template_settings(
                template_path,
                template,
                scope="analysis",
            ) is None:
                self.statusBar().showMessage("Analysis cancelled.", 5000)
                return
            golden_coverage_summary = None
            outlier_summary_rows: list[dict[str, str]] = []
            outlier_ratio_rows: list[dict[str, object]] = []
            report_outlier_fail_method = None
            built_golden_path = self.ui.goldenPathEdit.text().strip() or None
            if self._should_use_report_mode(template):
                report_outlier_fail_method = self.ui.outlierFailModeComboBox.currentText()

            output_path = self.ui.outputPathEdit.text().strip()
            if not output_path:
                raise ValueError("Report Output File cannot be empty.")
            zscore_threshold_override = self.ui.zThresholdSpinBox.value()
            resolved_output_path = self._resolve_existing_output_path(
                output_path,
                "Report output file",
            )
            if resolved_output_path is None:
                self.statusBar().showMessage("Analysis cancelled.", 5000)
                return

            if analysis_scope == "current_input_file":
                if not self._should_use_report_mode(template):
                    raise ValueError(
                        "Current input file scope is only available for report-style templates. "
                        "Please choose a database scope for storage analysis."
                    )
                if self._is_built_golden_mode() and not built_golden_path:
                    raise ValueError("Golden File is required when Golden Source is built_golden_file.")
                if self._is_built_golden_mode():
                    golden_coverage_summary = self._warn_built_golden_coverage_for_input(built_golden_path)
                payload = generate_report(
                    template_path,
                    self.ui.inputPathEdit.text().strip(),
                    resolved_output_path,
                    built_golden_path=(
                    built_golden_path if self._is_built_golden_mode() else None
                    ),
                    outlier_fail_method_override=report_outlier_fail_method,
                    zscore_threshold_override=zscore_threshold_override,
                    if_exists="overwrite",
                )
                outlier_artifacts = analyze_report_outlier_summary_artifacts(
                    template_path,
                    self.ui.inputPathEdit.text().strip(),
                    built_golden_path=(
                        built_golden_path if self._is_built_golden_mode() else None
                    ),
                    outlier_fail_method_override=report_outlier_fail_method,
                    zscore_threshold_override=zscore_threshold_override,
                )
                outlier_summary_rows = outlier_artifacts["summary_rows"]
                outlier_ratio_rows = outlier_artifacts["ratio_rows"]
            else:
                self._ensure_required_paths(require_input=False)
                dataset_ids, dimension_filters = self._collect_database_analysis_filters(
                    analysis_scope
                )
                if self._is_built_golden_mode():
                    if not built_golden_path:
                        raise ValueError("Golden File is required when Golden Source is built_golden_file.")
                    golden_coverage_summary = self._warn_built_golden_coverage_for_storage(
                        built_golden_path,
                        dataset_ids,
                        dimension_filters,
                    )
                payload = generate_report_from_storage(
                    template_path=template_path,
                    storage_path=self._active_storage_path(),
                    output_path=resolved_output_path,
                    built_golden_path=(
                        built_golden_path if self._is_built_golden_mode() else None
                    ),
                    outlier_fail_method_override=report_outlier_fail_method,
                    zscore_threshold_override=zscore_threshold_override,
                    dataset_ids=dataset_ids,
                    dimension_filters=dimension_filters,
                    if_exists="overwrite",
                )
                outlier_artifacts = analyze_report_outlier_summary_artifacts_from_storage(
                    template_path=template_path,
                    storage_path=self._active_storage_path(),
                    built_golden_path=(
                        built_golden_path if self._is_built_golden_mode() else None
                    ),
                    outlier_fail_method_override=report_outlier_fail_method,
                    zscore_threshold_override=zscore_threshold_override,
                    dataset_ids=dataset_ids,
                    dimension_filters=dimension_filters,
                )
                outlier_summary_rows = outlier_artifacts["summary_rows"]
                outlier_ratio_rows = outlier_artifacts["ratio_rows"]
        except Exception as exc:
            self._show_error("Analysis failed", exc)
            return

        self.current_golden_coverage_summary = golden_coverage_summary
        self.current_outlier_summary_rows = outlier_summary_rows
        self.current_outlier_ratio_rows = outlier_ratio_rows
        self._refresh_golden_coverage_view(golden_coverage_summary)
        self._refresh_outlier_summary_view(outlier_summary_rows, outlier_ratio_rows)
        if outlier_summary_rows or outlier_ratio_rows:
            self.ui.resultTabWidget.setCurrentWidget(self.ui.outlinerSummaryTab)
        elif golden_coverage_summary:
            self.ui.resultTabWidget.setCurrentWidget(self.ui.goldenCoverageTab)
        else:
            self.ui.resultTabWidget.setCurrentWidget(self.ui.logTab)
        self._log("Report exported:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
        self.statusBar().showMessage("Analysis completed.", 5000)

    def _refresh_storage_overview(self, silent: bool = False) -> None:
        database_root = self._database_root_path()
        if not database_root:
            self.current_storage_headers = []
            self.ui.storageSummaryLabel.setText("Database folder is empty.")
            self._populate_table(self.ui.storageTableWidget, ["Current Database Rows"], [])
            return
        template_path = self.ui.templatePathEdit.text().strip() or None
        try:
            payload = describe_storage(self._active_storage_path(), template_path=template_path, limit=500)
        except Exception as exc:
            self.current_storage_headers = []
            self.ui.storageSummaryLabel.setText(f"Current database view unavailable: {exc}")
            if not silent:
                self._show_error("Refresh database view failed", exc)
            return

        dimensions = payload["dimensions"]
        headers = [*dimensions, "measurement_count", "dataset_id", "__row_number__", "__source_file__"]
        rows = [
            [
                *[str(item.get(header, "")) for header in dimensions],
                str(item.get("measurement_count", "")),
                str(item.get("dataset_id", "")),
                str(item.get("row_number", "")),
                str(item.get("source_file", "")),
            ]
            for item in payload["rows"]
        ]
        self.current_storage_headers = headers
        self._populate_table(self.ui.storageTableWidget, headers or ["Current Database Rows"], rows)
        self._set_hidden_table_columns(
            self.ui.storageTableWidget,
            ["__row_number__", "__source_file__"],
        )

        summary = (
            f"Current workspace: {payload['dataset_count']} dataset(s), "
            f"{payload['row_count']} row(s), {payload['measurement_count']} measurement(s), "
            f"{payload['import_history_count']} import record(s)."
        )
        summary += (
            f" Database root: {Path(database_root).resolve()} | "
            f"Workspace: {Path(self._active_storage_path()).resolve()}"
        )
        if payload["truncated"]:
            summary += " Only the first 500 rows are shown."
        self.ui.storageSummaryLabel.setText(summary)
        self._refresh_analysis_imports(silent=True)

    def _refresh_golden_coverage_view(self, summary: dict | None) -> None:
        if not summary:
            self.ui.goldenCoverageSummaryLabel.setText(
                "No built golden coverage checked yet."
            )
            self._populate_table(
                self.ui.goldenCoverageSummaryTableWidget,
                ["scope", "total_measurement_count", "matched_measurement_count", "unmatched_measurement_count", "matched_row_count", "unmatched_row_count"],
                [],
            )
            self._populate_table(
                self.ui.goldenCoverageExamplesTableWidget,
                ["row_number", "dataset_id", "logical_metric", "raw_column", "dimensions"],
                [],
            )
            return

        self.ui.goldenCoverageSummaryLabel.setText(
            (
                f"Built golden coverage for {summary.get('scope', 'analysis')}: "
                f"{summary.get('matched_measurement_count', 0)}/"
                f"{summary.get('total_measurement_count', 0)} measurements matched."
            )
        )
        summary_headers = [
            "scope",
            "total_measurement_count",
            "matched_measurement_count",
            "unmatched_measurement_count",
            "matched_row_count",
            "unmatched_row_count",
        ]
        self._populate_table(
            self.ui.goldenCoverageSummaryTableWidget,
            summary_headers,
            [[str(summary.get(header, "")) for header in summary_headers]],
        )
        example_headers = ["row_number", "dataset_id", "logical_metric", "raw_column", "dimensions"]
        example_rows = [
            [
                str(item.get("row_number", "")),
                str(item.get("dataset_id", "")),
                str(item.get("logical_metric", "")),
                str(item.get("raw_column", "")),
                json.dumps(item.get("dimensions", {}), ensure_ascii=False, sort_keys=True),
            ]
            for item in summary.get("unmatched_examples", [])
        ]
        self._populate_table(
            self.ui.goldenCoverageExamplesTableWidget,
            example_headers,
            example_rows,
        )

    def _refresh_outlier_summary_view(
        self,
        rows: list[dict[str, str]],
        ratio_rows: list[dict[str, object]],
    ) -> None:
        if not rows and not ratio_rows:
            self.ui.outlinerSummaryLabel.setText("No outliner summary available for the current analysis scope.")
            self._populate_table(
                self.ui.outlinerSummaryTableWidget,
                ["sample_id", "node", "chain", "status"],
                [],
            )
            self.ui.outlierRatioSummaryLabel.setText("No outlier ratio statistics configured for the current analysis scope.")
            self._populate_table(
                self.ui.outlierRatioTableWidget,
                [
                    "id",
                    "display_name",
                    "group_by_dimension",
                    "group_value",
                    "numerator",
                    "outlier_sample_count",
                    "total_sample_count",
                    "outlier_ratio",
                    "filter_summary",
                ],
                [],
            )
            return
        self.ui.outlinerSummaryLabel.setText(
            f"Current outliner summary contains {len(rows)} event(s)."
        )
        self._populate_table(
            self.ui.outlinerSummaryTableWidget,
            ["sample_id", "node", "chain", "status"],
            [
                [
                    str(item.get("sample_id", "")),
                    str(item.get("node", "")),
                    str(item.get("chain", "")),
                    str(item.get("status", "")),
                ]
                for item in rows
            ],
        )
        self.ui.outlierRatioSummaryLabel.setText(
            f"Current outlier ratio statistics contain {len(ratio_rows)} row(s)."
        )
        self._populate_table(
            self.ui.outlierRatioTableWidget,
            [
                "id",
                "display_name",
                "group_by_dimension",
                "group_value",
                "numerator",
                "outlier_sample_count",
                "total_sample_count",
                "outlier_ratio",
                "filter_summary",
            ],
            [
                [
                    str(item.get("id", "")),
                    str(item.get("display_name", "")),
                    str(item.get("group_by_dimension", "")),
                    str(item.get("group_value", "")),
                    str(item.get("numerator", "")),
                    str(item.get("outlier_sample_count", "")),
                    str(item.get("total_sample_count", "")),
                    str(item.get("outlier_ratio", "")),
                    str(item.get("filter_summary", "")),
                ]
                for item in ratio_rows
            ],
        )

    def _refresh_analysis_imports(self, silent: bool = False) -> None:
        widget = self.ui.analysisImportsListWidget
        checked_ids = set(self._selected_analysis_dataset_ids())
        widget.clear()
        database_root = self._database_root_path()
        if not database_root:
            return
        try:
            entries = list_import_history(self._active_storage_path())
        except Exception as exc:
            if not silent:
                self._show_error("Refresh import list failed", exc)
            return
        for entry in entries:
            dataset_id = str(entry.get("dataset_id", ""))
            created_at = str(entry.get("created_at_utc", ""))
            source_file = Path(str(entry.get("source_file", "") or "")).name
            measurement_count = entry.get("measurement_count", "")
            label = (
                f"{created_at} | {dataset_id} | {source_file} | "
                f"{measurement_count} measurements"
            )
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, dataset_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if dataset_id in checked_ids else Qt.Unchecked)
            widget.addItem(item)

    def _update_analysis_mode_state(self) -> None:
        built_golden_mode = self._is_built_golden_mode()
        database_scope = self.ui.analysisScopeComboBox.currentText() != "current_input_file"
        filtered_scope = self.ui.analysisScopeComboBox.currentText() in {
            "filtered_database",
            "checked_imports",
        }
        checked_imports_scope = self.ui.analysisScopeComboBox.currentText() == "checked_imports"
        self.ui.goldenSourceComboBox.setEnabled(True)
        self.ui.goldenPathEdit.setEnabled(built_golden_mode)
        self.ui.browseGoldenButton.setEnabled(built_golden_mode)
        self.ui.analysisSampleIdsEdit.setEnabled(filtered_scope)
        self.ui.analysisExcludeSampleIdsEdit.setEnabled(filtered_scope)
        self.ui.analysisNodesEdit.setEnabled(filtered_scope)
        self.ui.analysisExcludeNodesEdit.setEnabled(filtered_scope)
        self.ui.refreshAnalysisImportsButton.setEnabled(database_scope)
        self.ui.analysisImportsListWidget.setEnabled(checked_imports_scope)
        self.ui.outputPathEdit.setEnabled(True)
        self.ui.browseOutputButton.setEnabled(True)
        self._update_golden_threshold_mode_state()

    def _update_golden_threshold_mode_state(self) -> None:
        threshold_mode = self.ui.thresholdModeComboBox.currentText()
        self.ui.relativeLimitSpinBox.setEnabled(threshold_mode in {"relative", "hybrid"})
        self.ui.sigmaMultiplierSpinBox.setEnabled(threshold_mode in {"sigma", "hybrid"})

    def _ensure_required_paths(self, require_input: bool) -> None:
        self._ensure_template_path()
        if require_input and not self.ui.inputPathEdit.text().strip():
            raise ValueError("Input Excel/CSV path is required.")
        if not self._database_root_path():
            raise ValueError("Storage Folder is required.")

    def _ensure_report_paths(self) -> None:
        self._ensure_template_path()
        if not self.ui.inputPathEdit.text().strip():
            raise ValueError("Input Excel/CSV path is required.")

    def _ensure_analysis_paths(self, analysis_scope: str) -> None:
        self._ensure_template_path()
        if analysis_scope == "current_input_file":
            self._ensure_report_paths()
            return
        if not self._database_root_path():
            raise ValueError("Database Folder is required.")

    def _ensure_template_path(self) -> str:
        template_path = self.ui.templatePathEdit.text().strip()
        if not template_path:
            raise ValueError("Template path is required.")
        return template_path

    def _resolve_relative_limit(self) -> float | None:
        if self.ui.thresholdModeComboBox.currentText() in {"relative", "hybrid"}:
            return self.ui.relativeLimitSpinBox.value()
        return None

    def _resolve_sigma_multiplier(self) -> float | None:
        if self.ui.thresholdModeComboBox.currentText() in {"sigma", "hybrid"}:
            return self.ui.sigmaMultiplierSpinBox.value()
        return None

    def _database_root_path(self) -> str:
        return self.ui.storagePathEdit.text().strip()

    def _active_storage_path(self) -> str:
        database_root = self._database_root_path()
        if not database_root:
            return ""
        if self.current_workspace_path:
            return self.current_workspace_path
        self._ensure_storage_workspace_for_current_database(silent=True)
        return self.current_workspace_path

    def _ensure_storage_workspace_for_current_database(self, silent: bool) -> None:
        database_root = self._database_root_path()
        if not database_root:
            self.current_workspace_path = ""
            return
        try:
            payload = ensure_storage_workspace(database_root)
        except Exception as exc:
            self.current_workspace_path = ""
            if not silent:
                self._show_error("Prepare database workspace failed", exc)
            return
        self.current_workspace_path = str(Path(payload["workspace"]).resolve())

    def _refresh_default_output_path(self) -> None:
        database_root = self._database_root_path()
        if not database_root:
            self.ui.outputPathEdit.setText(
                str(default_output_path("sample_chip_data_real_result.xlsx").resolve())
            )
            return
        self.ui.outputPathEdit.setText(
            str(default_database_output_path(database_root).resolve())
        )

    def _prompt_workspace_recovery_if_needed(self) -> None:
        database_root = self._database_root_path()
        if not database_root:
            return
        try:
            payload = storage_workspace_differs(database_root)
        except Exception as exc:
            self._show_error("Check temp workspace failed", exc)
            return
        if not payload.get("differs"):
            return
        response = QMessageBox(self)
        response.setWindowTitle("Unsaved Temp Workspace Found")
        response.setIcon(QMessageBox.Warning)
        response.setText(
            (
                "This database contains a temp workspace that is different from the last saved database.\n\n"
                f"Database root:\n{database_root}\n\n"
                f"Temp workspace:\n{payload.get('workspace', '')}"
            )
        )
        response.setInformativeText(
            "Choose Continue Temp Workspace to keep working from temp/, or Discard Temp And Reload Saved Database to drop those unsaved temp changes."
        )
        continue_button = response.addButton("Continue Temp Workspace", QMessageBox.AcceptRole)
        discard_button = response.addButton("Discard Temp And Reload Saved Database", QMessageBox.DestructiveRole)
        response.setDefaultButton(continue_button)
        response.exec()
        if response.clickedButton() == discard_button:
            try:
                reset_payload = discard_storage_workspace_changes(database_root)
            except Exception as exc:
                self._show_error("Discard temp workspace failed", exc)
                return
            self.current_workspace_path = str(Path(reset_payload["workspace"]).resolve())
            self._log(
                "Discarded temp workspace changes and reloaded saved database:\n"
                + json.dumps(reset_payload, ensure_ascii=False, indent=2)
            )
        else:
            self._log(
                "Continuing with unsaved temp workspace:\n"
                + json.dumps(payload, ensure_ascii=False, indent=2)
            )

    def _show_error(self, title: str, exc: Exception) -> None:
        self._log(f"{title}: {exc}")
        QMessageBox.critical(self, title, str(exc))
        self.statusBar().showMessage(title, 5000)

    def _log(self, message: str) -> None:
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.ui.logPlainTextEdit.appendPlainText(f"[{timestamp}] {message}")

    @staticmethod
    def _should_use_report_mode(template) -> bool:
        return bool(
            template.report.golden_values
            or template.measurement_header_row != template.row_header_row
            or template.unit_row is not None
        )

    def _is_template_golden_mode(self) -> bool:
        return self.ui.goldenSourceComboBox.currentText() == "template_direct"

    def _is_built_golden_mode(self) -> bool:
        return self.ui.goldenSourceComboBox.currentText() == "built_golden_file"

    @staticmethod
    def _format_outlier_method_label(method: str) -> str:
        if method == "golden_deviation":
            return "GoldenDeviation"
        if method == "zscore_and_golden":
            return "Zscore AND GoldenDeviation"
        if method == "zscore_or_golden":
            return "Zscore OR GoldenDeviation"
        return "Zscore"

    def _prompt_import_conflict_mode(self, preview: dict) -> str | None:
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Import Conflict Detected")
        message_box.setIcon(QMessageBox.Warning)
        message_box.setText(
            (
                "Current database already contains rows with the same sample attributes.\n\n"
                f"Incoming conflicting rows: {preview['conflict_row_count']}\n"
                f"Existing rows affected: {preview['existing_conflict_row_count']}"
            )
        )

        preview_lines = []
        for item in preview["conflict_rows_preview"][:5]:
            text = ", ".join(f"{key}={value}" for key, value in item.items() if value != "")
            if text:
                preview_lines.append(text)
        informative_lines = [
            "Replace: remove existing rows with the same sample/node/site... key, then import this file.",
        ]
        if preview["has_repeat_dimension"]:
            informative_lines.append(
                "Append: keep existing rows and shift repeat_id upward for the new file."
            )
        else:
            informative_lines.append(
                "Append is unavailable because conflicting rows do not contain a valid repeat_id."
            )
        if preview_lines:
            informative_lines.append("")
            informative_lines.append("Examples:")
            informative_lines.extend(preview_lines)
        message_box.setInformativeText("\n".join(informative_lines))

        replace_button = message_box.addButton("Replace Existing", QMessageBox.AcceptRole)
        append_button = None
        if preview["has_repeat_dimension"]:
            append_button = message_box.addButton("Append And Shift Repeat", QMessageBox.ActionRole)
        cancel_button = message_box.addButton(QMessageBox.Cancel)
        message_box.setDefaultButton(replace_button)
        message_box.exec()

        clicked = message_box.clickedButton()
        if clicked == replace_button:
            return "replace"
        if append_button is not None and clicked == append_button:
            return "append"
        if clicked == cancel_button:
            return None
        return None

    def _selected_analysis_dataset_ids(self) -> list[str]:
        dataset_ids: list[str] = []
        for index in range(self.ui.analysisImportsListWidget.count()):
            item = self.ui.analysisImportsListWidget.item(index)
            if item.checkState() == Qt.Checked:
                dataset_ids.append(str(item.data(Qt.UserRole)))
        return dataset_ids

    def _collect_database_analysis_filters(
        self,
        analysis_scope: str,
    ) -> tuple[list[str] | None, dict[str, dict[str, list[str]]]]:
        dataset_ids: list[str] | None = None
        if analysis_scope == "checked_imports":
            dataset_ids = self._selected_analysis_dataset_ids()
            if not dataset_ids:
                raise ValueError("Please check at least one import entry to analyze.")
        sample_ids = parse_csv_items(self.ui.analysisSampleIdsEdit.text().strip())
        exclude_sample_ids = parse_csv_items(self.ui.analysisExcludeSampleIdsEdit.text().strip())
        nodes = parse_csv_items(self.ui.analysisNodesEdit.text().strip())
        exclude_nodes = parse_csv_items(self.ui.analysisExcludeNodesEdit.text().strip())
        if analysis_scope not in {"filtered_database", "checked_imports"}:
            sample_ids = []
            exclude_sample_ids = []
            nodes = []
            exclude_nodes = []
        return dataset_ids, build_dimension_filters(
            sample_ids=sample_ids,
            reliability_nodes=nodes,
            exclude_sample_ids=exclude_sample_ids,
            exclude_reliability_nodes=exclude_nodes,
        )

    def _sync_template_backed_settings_from_template(self, silent: bool = False) -> None:
        try:
            template = load_template(self._ensure_template_path())
        except Exception as exc:
            if not silent:
                self._show_error("Load template failed", exc)
            return
        self.ui.outlierFailModeComboBox.setCurrentText(template.report.outlier_fail_method)
        self.ui.zThresholdSpinBox.setValue(template.report.zscore_thresholds.default)
        golden_defaults = template.golden_reference_defaults
        self.ui.referenceDimsEdit.setText(",".join(golden_defaults.reference_dimensions))
        self.ui.filtersEdit.setPlainText(
            "\n".join(f"{key}={value}" for key, value in golden_defaults.filters.items())
        )
        self._set_combo_text_if_present(
            self.ui.centerMethodComboBox,
            golden_defaults.center_method,
        )
        self._set_combo_text_if_present(
            self.ui.thresholdModeComboBox,
            golden_defaults.threshold_mode,
        )
        if golden_defaults.relative_limit is not None:
            self.ui.relativeLimitSpinBox.setValue(float(golden_defaults.relative_limit))
        if golden_defaults.sigma_multiplier is not None:
            self.ui.sigmaMultiplierSpinBox.setValue(float(golden_defaults.sigma_multiplier))

    def _maybe_write_back_template_settings(
        self,
        template_path: str,
        template,
        scope: str,
    ) -> bool | None:
        diffs: list[dict[str, object]] = []
        if scope == "analysis":
            desired_outlier = self.ui.outlierFailModeComboBox.currentText()
            if desired_outlier != template.report.outlier_fail_method:
                diffs.append(
                    {
                        "label": "Outlier Criteria",
                        "gui": self._format_outlier_method_label(desired_outlier),
                        "template": self._format_outlier_method_label(
                            template.report.outlier_fail_method
                        ),
                        "apply": lambda item, desired=desired_outlier: setattr(
                            item.report,
                            "outlier_fail_method",
                            desired,
                        ),
                    }
                )
            desired_z = float(self.ui.zThresholdSpinBox.value())
            template_z = float(template.report.zscore_thresholds.default)
            override_count = len(template.report.zscore_thresholds.overrides)
            if abs(desired_z - template_z) > 1e-12 or override_count:
                template_label = f"{template_z:g}"
                if override_count:
                    template_label = f"{template_label} (+{override_count} override)"
                    if override_count > 1:
                        template_label += "s"
                diffs.append(
                    {
                        "label": "Z Threshold",
                        "gui": f"{desired_z:g}",
                        "template": template_label,
                        "note": (
                            "Writing back will set template default z-threshold "
                            "and clear metric-specific zscore overrides to match the GUI."
                        )
                        if override_count
                        else None,
                        "apply": lambda item, desired=desired_z: setattr(
                            item.report,
                            "zscore_thresholds",
                            item.report.zscore_thresholds.__class__(
                                default=desired,
                                overrides={},
                            ),
                        ),
                    }
                )
        elif scope == "build_golden":
            golden_defaults = template.golden_reference_defaults
            desired_reference_dims = parse_csv_items(self.ui.referenceDimsEdit.text().strip())
            if desired_reference_dims != golden_defaults.reference_dimensions:
                diffs.append(
                    {
                        "label": "Golden Reference Dims",
                        "gui": ",".join(desired_reference_dims) or "(empty)",
                        "template": ",".join(golden_defaults.reference_dimensions) or "(empty)",
                        "apply": lambda item, desired=desired_reference_dims: setattr(
                            item.golden_reference_defaults,
                            "reference_dimensions",
                            list(desired),
                        ),
                    }
                )
            desired_filters = parse_filter_text(self.ui.filtersEdit.toPlainText())
            if desired_filters != golden_defaults.filters:
                diffs.append(
                    {
                        "label": "Golden Filters",
                        "gui": "; ".join(f"{key}={value}" for key, value in desired_filters.items()) or "(empty)",
                        "template": "; ".join(
                            f"{key}={value}" for key, value in golden_defaults.filters.items()
                        )
                        or "(empty)",
                        "apply": lambda item, desired=desired_filters: setattr(
                            item.golden_reference_defaults,
                            "filters",
                            dict(desired),
                        ),
                    }
                )
            desired_center_method = self.ui.centerMethodComboBox.currentText()
            if desired_center_method != golden_defaults.center_method:
                diffs.append(
                    {
                        "label": "Golden Center",
                        "gui": desired_center_method,
                        "template": golden_defaults.center_method,
                        "apply": lambda item, desired=desired_center_method: setattr(
                            item.golden_reference_defaults,
                            "center_method",
                            desired,
                        ),
                    }
                )
            desired_threshold_mode = self.ui.thresholdModeComboBox.currentText()
            if desired_threshold_mode != golden_defaults.threshold_mode:
                diffs.append(
                    {
                        "label": "Golden Threshold Mode",
                        "gui": desired_threshold_mode,
                        "template": golden_defaults.threshold_mode,
                        "apply": lambda item, desired=desired_threshold_mode: setattr(
                            item.golden_reference_defaults,
                            "threshold_mode",
                            desired,
                        ),
                    }
                )
            desired_relative_limit = self._resolve_relative_limit()
            template_relative_limit = (
                golden_defaults.relative_limit
                if desired_threshold_mode in {"relative", "hybrid"}
                else None
            )
            if desired_relative_limit != template_relative_limit:
                diffs.append(
                    {
                        "label": "Golden Relative Limit",
                        "gui": self._format_optional_number(desired_relative_limit),
                        "template": self._format_optional_number(
                            template_relative_limit
                        ),
                        "apply": lambda item, desired=desired_relative_limit: setattr(
                            item.golden_reference_defaults,
                            "relative_limit",
                            desired,
                        ),
                    }
                )
            desired_sigma_multiplier = self._resolve_sigma_multiplier()
            template_sigma_multiplier = (
                golden_defaults.sigma_multiplier
                if desired_threshold_mode in {"sigma", "hybrid"}
                else None
            )
            if desired_sigma_multiplier != template_sigma_multiplier:
                diffs.append(
                    {
                        "label": "Golden Sigma Multiplier",
                        "gui": self._format_optional_number(desired_sigma_multiplier),
                        "template": self._format_optional_number(
                            template_sigma_multiplier
                        ),
                        "apply": lambda item, desired=desired_sigma_multiplier: setattr(
                            item.golden_reference_defaults,
                            "sigma_multiplier",
                            desired,
                        ),
                    }
                )

        if not diffs:
            return True

        lines = ["当前 GUI 设置和 template 中的默认值不一致：", ""]
        for diff in diffs:
            lines.append(
                f"- {diff['label']}: GUI={diff['gui']} | Template={diff['template']}"
            )
            note = diff.get("note")
            if note:
                lines.append(f"  {note}")
        lines.extend(
            [
                "",
                "是否把这些值回写到当前 template？",
                "选择 Yes 会保存到 template；选择 No 只对本次操作生效。",
            ]
        )
        response = QMessageBox.question(
            self,
            "Sync Settings Back To Template",
            "\n".join(lines),
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes,
        )
        if response == QMessageBox.Cancel:
            return None
        if response == QMessageBox.No:
            return True

        updated_template = load_template(template_path)
        for diff in diffs:
            apply_fn = diff["apply"]
            apply_fn(updated_template)
        save_template(updated_template, template_path)
        self._log(
            "Updated template-backed GUI settings in "
            f"{template_path}:\n"
            + json.dumps(
                [
                    {
                        "label": diff["label"],
                        "gui": diff["gui"],
                        "template_previous": diff["template"],
                    }
                    for diff in diffs
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return True

    @staticmethod
    def _format_optional_number(value: float | None) -> str:
        if value is None:
            return "(empty)"
        return f"{value:g}"

    def _warn_built_golden_coverage_for_input(self, golden_path: str) -> dict:
        summary = summarize_built_golden_coverage_for_input(
            self.ui.templatePathEdit.text().strip(),
            self.ui.inputPathEdit.text().strip(),
            golden_path,
        )
        self._show_built_golden_coverage_summary(summary)
        return summary

    def _warn_built_golden_coverage_for_storage(
        self,
        golden_path: str,
        dataset_ids: list[str] | None,
        dimension_filters: dict[str, dict[str, list[str]]],
    ) -> dict:
        summary = summarize_built_golden_coverage_for_storage(
            self._active_storage_path(),
            golden_path,
            dataset_ids=dataset_ids,
            dimension_filters=dimension_filters,
        )
        self._show_built_golden_coverage_summary(summary)
        return summary

    def _show_built_golden_coverage_summary(self, summary: dict) -> None:
        matched = summary["matched_measurement_count"]
        unmatched = summary["unmatched_measurement_count"]
        total = summary["total_measurement_count"]
        self._log(
            "Built golden coverage:\n"
            + json.dumps(summary, ensure_ascii=False, indent=2)
        )
        if total == 0:
            QMessageBox.information(
                self,
                "Built Golden Coverage",
                "Current analysis scope does not contain any measurement data.",
            )
            return
        if unmatched == 0:
            self.statusBar().showMessage(
                f"Built golden coverage: {matched}/{total} measurements matched.",
                5000,
            )
            return

        examples = []
        for item in summary.get("unmatched_examples", [])[:5]:
            dimensions = item.get("dimensions", {})
            dimension_text = ", ".join(
                f"{key}={value}" for key, value in dimensions.items() if value != ""
            )
            examples.append(
                f"- row {item.get('row_number')} | {item.get('raw_column')} | {dimension_text}"
            )
        detail = [
            (
                f"Built golden matched {matched}/{total} measurements, "
                f"but {unmatched} measurements in {summary['unmatched_row_count']} row(s) "
                "did not match any golden key."
            ),
        ]
        if examples:
            detail.append("")
            detail.append("Examples:")
            detail.extend(examples)
        QMessageBox.warning(
            self,
            "Built Golden Coverage Warning",
            "\n".join(detail),
        )

    def _collect_persistent_gui_settings(self) -> dict[str, object]:
        return {
            "version": 1,
            "paths": {
                "template_path": self.ui.templatePathEdit.text().strip(),
                "input_path": self.ui.inputPathEdit.text().strip(),
                "golden_path": self.ui.goldenPathEdit.text().strip(),
                "output_path": self.ui.outputPathEdit.text().strip(),
            },
            "golden": {
                "golden_name": self.ui.goldenNameEdit.text().strip(),
                "reference_dims_text": self.ui.referenceDimsEdit.text().strip(),
                "filters_text": self.ui.filtersEdit.toPlainText(),
                "center_method": self.ui.centerMethodComboBox.currentText(),
                "threshold_mode": self.ui.thresholdModeComboBox.currentText(),
                "relative_limit": self.ui.relativeLimitSpinBox.value(),
                "sigma_multiplier": self.ui.sigmaMultiplierSpinBox.value(),
                "golden_source": self.ui.goldenSourceComboBox.currentText(),
            },
            "analysis": {
                "analysis_scope": self.ui.analysisScopeComboBox.currentText(),
                "outlier_fail_mode": self.ui.outlierFailModeComboBox.currentText(),
                "z_threshold": self.ui.zThresholdSpinBox.value(),
                "sample_ids_text": self.ui.analysisSampleIdsEdit.text().strip(),
                "exclude_sample_ids_text": self.ui.analysisExcludeSampleIdsEdit.text().strip(),
                "nodes_text": self.ui.analysisNodesEdit.text().strip(),
                "exclude_nodes_text": self.ui.analysisExcludeNodesEdit.text().strip(),
                "selected_dataset_ids": self._selected_analysis_dataset_ids(),
            },
            "ui_state": {
                "workbench_tab_index": self.ui.workbenchTabWidget.currentIndex(),
                "result_tab_index": self.ui.resultTabWidget.currentIndex(),
                "splitter_sizes": self.ui.mainSplitter.sizes(),
            },
        }

    def _load_saved_settings_for_current_database(self, silent: bool) -> None:
        database_root = self._database_root_path()
        if not database_root:
            return
        try:
            payload = load_gui_state(database_root)
        except Exception as exc:
            if not silent:
                self._show_error("Load settings failed", exc)
            return
        if payload is None:
            if not silent:
                QMessageBox.information(
                    self,
                    "No Saved Settings",
                    "Current database does not contain any saved GUI settings yet.",
                )
            return
        try:
            self._apply_persistent_gui_settings(payload)
        except Exception as exc:
            if not silent:
                self._show_error("Apply settings failed", exc)
            return
        self._log(f"Loaded database GUI settings from {Path(database_root) / '.excel_data_analysis_gui_state.json'}")
        self.statusBar().showMessage("Saved database settings loaded.", 5000)

    def _should_prompt_save_temp_database_on_close(self) -> bool:
        database_root = self._database_root_path()
        if not database_root:
            return False
        try:
            current = Path(database_root).resolve()
            default_temp = default_database_root().resolve()
        except Exception:
            return False
        if current != default_temp:
            return False
        return self._storage_has_user_content(Path(self._active_storage_path()))

    @staticmethod
    def _storage_has_user_content(storage_path: Path) -> bool:
        measurements_path = storage_path / "measurements.jsonl"
        datasets_path = storage_path / "datasets.jsonl"
        golden_dir = storage_path / "golden"
        imports_dir = storage_path / "imports"
        return (
            (measurements_path.exists() and measurements_path.stat().st_size > 0)
            or (datasets_path.exists() and datasets_path.stat().st_size > 0)
            or (golden_dir.exists() and any(golden_dir.iterdir()))
            or (imports_dir.exists() and any(imports_dir.iterdir()))
        )

    def _prompt_save_temp_database_before_exit(self) -> str:
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Temporary Database In Use")
        message_box.setIcon(QMessageBox.Warning)
        message_box.setText(
            (
                "Current database is still using the default temporary folder:\n"
                f"{default_database_root().resolve()}\n\n"
                "Please save it to a proper project directory before closing."
            )
        )
        message_box.setInformativeText(
            "Choose Save Database to copy the current database to a new folder, Exit Anyway to keep using tempDatabase, or Cancel to stay in the app."
        )
        save_button = message_box.addButton("Save Database", QMessageBox.AcceptRole)
        exit_button = message_box.addButton("Exit Anyway", QMessageBox.DestructiveRole)
        cancel_button = message_box.addButton(QMessageBox.Cancel)
        message_box.setDefaultButton(save_button)
        message_box.exec()
        clicked = message_box.clickedButton()
        if clicked == cancel_button:
            return "cancel"
        if clicked == exit_button:
            return "exit"
        if clicked == save_button:
            try:
                saved_path = self._save_database_copy_as(self._database_root_path())
            except Exception as exc:
                self._show_error("Save database copy failed", exc)
                return "cancel"
            if not saved_path:
                return "cancel"
            self.ui.storagePathEdit.setText(saved_path)
            self._refresh_storage_overview(silent=True)
            self._load_saved_settings_for_current_database(silent=True)
            QMessageBox.information(
                self,
                "Database Saved",
                f"Current database was copied to:\n{saved_path}",
            )
            return "saved"
        return "cancel"

    def _apply_persistent_gui_settings(self, payload: dict[str, object]) -> None:
        paths = payload.get("paths", {})
        if isinstance(paths, dict):
            self.ui.templatePathEdit.setText(self._coerce_saved_text(paths.get("template_path"), self.ui.templatePathEdit.text()))
            self.ui.inputPathEdit.setText(self._coerce_saved_text(paths.get("input_path"), self.ui.inputPathEdit.text()))
            self.ui.goldenPathEdit.setText(self._coerce_saved_text(paths.get("golden_path"), self.ui.goldenPathEdit.text()))
            self.ui.outputPathEdit.setText(self._coerce_saved_text(paths.get("output_path"), self.ui.outputPathEdit.text()))

        golden = payload.get("golden", {})
        if isinstance(golden, dict):
            self.ui.goldenNameEdit.setText(self._coerce_saved_text(golden.get("golden_name"), self.ui.goldenNameEdit.text()))
            self.ui.referenceDimsEdit.setText(self._coerce_saved_text(golden.get("reference_dims_text"), self.ui.referenceDimsEdit.text()))
            self.ui.filtersEdit.setPlainText(self._coerce_saved_text(golden.get("filters_text"), self.ui.filtersEdit.toPlainText()))
            self._set_combo_text_if_present(self.ui.centerMethodComboBox, golden.get("center_method"))
            self._set_combo_text_if_present(self.ui.thresholdModeComboBox, golden.get("threshold_mode"))
            if "relative_limit" in golden:
                self.ui.relativeLimitSpinBox.setValue(float(golden["relative_limit"]))
            if "sigma_multiplier" in golden:
                self.ui.sigmaMultiplierSpinBox.setValue(float(golden["sigma_multiplier"]))
            self._set_combo_text_if_present(self.ui.goldenSourceComboBox, golden.get("golden_source"))

        analysis = payload.get("analysis", {})
        selected_dataset_ids: list[str] = []
        if isinstance(analysis, dict):
            self._set_combo_text_if_present(self.ui.analysisScopeComboBox, analysis.get("analysis_scope"))
            self._set_combo_text_if_present(self.ui.outlierFailModeComboBox, analysis.get("outlier_fail_mode"))
            if "z_threshold" in analysis:
                self.ui.zThresholdSpinBox.setValue(float(analysis["z_threshold"]))
            self.ui.analysisSampleIdsEdit.setText(self._coerce_saved_text(analysis.get("sample_ids_text"), self.ui.analysisSampleIdsEdit.text()))
            self.ui.analysisExcludeSampleIdsEdit.setText(self._coerce_saved_text(analysis.get("exclude_sample_ids_text"), self.ui.analysisExcludeSampleIdsEdit.text()))
            self.ui.analysisNodesEdit.setText(self._coerce_saved_text(analysis.get("nodes_text"), self.ui.analysisNodesEdit.text()))
            self.ui.analysisExcludeNodesEdit.setText(self._coerce_saved_text(analysis.get("exclude_nodes_text"), self.ui.analysisExcludeNodesEdit.text()))
            selected_dataset_ids = [str(item) for item in analysis.get("selected_dataset_ids", [])]

        ui_state = payload.get("ui_state", {})
        splitter_sizes: list[int] | None = None
        if isinstance(ui_state, dict):
            workbench_tab_index = ui_state.get("workbench_tab_index")
            if isinstance(workbench_tab_index, int) and 0 <= workbench_tab_index < self.ui.workbenchTabWidget.count():
                self.ui.workbenchTabWidget.setCurrentIndex(workbench_tab_index)
            result_tab_index = ui_state.get("result_tab_index")
            if isinstance(result_tab_index, int) and 0 <= result_tab_index < self.ui.resultTabWidget.count():
                self.ui.resultTabWidget.setCurrentIndex(result_tab_index)
            if isinstance(ui_state.get("splitter_sizes"), list):
                splitter_sizes = [int(item) for item in ui_state["splitter_sizes"]]

        self._refresh_analysis_imports(silent=True)
        self._set_selected_analysis_dataset_ids(selected_dataset_ids)
        self._update_analysis_mode_state()
        if splitter_sizes:
            self.ui.mainSplitter.setSizes(splitter_sizes)

    @staticmethod
    def _set_combo_text_if_present(combo_box, value: object) -> None:
        if value is None:
            return
        text = str(value)
        if combo_box.findText(text) >= 0:
            combo_box.setCurrentText(text)

    @staticmethod
    def _coerce_saved_text(value: object, fallback: str) -> str:
        if value is None:
            return fallback
        return str(value)

    def _set_selected_analysis_dataset_ids(self, dataset_ids: list[str]) -> None:
        selected_ids = set(dataset_ids)
        for index in range(self.ui.analysisImportsListWidget.count()):
            item = self.ui.analysisImportsListWidget.item(index)
            item.setCheckState(Qt.Checked if str(item.data(Qt.UserRole)) in selected_ids else Qt.Unchecked)

    def _selected_storage_row_selectors(self) -> list[dict[str, object]]:
        headers = self.current_storage_headers
        if not headers:
            return []
        dataset_index = self._header_index(headers, "dataset_id")
        row_number_index = self._header_index(headers, "__row_number__")
        source_file_index = self._header_index(headers, "__source_file__")
        if dataset_index < 0 or row_number_index < 0 or source_file_index < 0:
            return []
        selectors: list[dict[str, object]] = []
        for row_index in sorted({item.row() for item in self.ui.storageTableWidget.selectedItems()}):
            dataset_item = self.ui.storageTableWidget.item(row_index, dataset_index)
            row_number_item = self.ui.storageTableWidget.item(row_index, row_number_index)
            source_file_item = self.ui.storageTableWidget.item(row_index, source_file_index)
            if dataset_item is None or row_number_item is None or source_file_item is None:
                continue
            selectors.append(
                {
                    "dataset_id": dataset_item.text(),
                    "row_number": row_number_item.text(),
                    "source_file": source_file_item.text(),
                }
            )
        return selectors

    @staticmethod
    def _header_index(headers: list[str], name: str) -> int:
        try:
            return headers.index(name)
        except ValueError:
            return -1

    @staticmethod
    def _set_hidden_table_columns(table, hidden_headers: list[str]) -> None:
        actual_headers = [
            table.horizontalHeaderItem(index).text()
            if table.horizontalHeaderItem(index) is not None
            else ""
            for index in range(table.columnCount())
        ]
        for header in hidden_headers:
            if header in actual_headers:
                table.setColumnHidden(actual_headers.index(header), True)

    def _collect_gui_settings_snapshot(self) -> dict[str, object]:
        template_summary = None
        template_error = None
        template_path = self.ui.templatePathEdit.text().strip()
        if template_path:
            try:
                template_summary = summarize_template(load_template(template_path))
            except Exception as exc:
                template_error = str(exc)
        return {
            "paths": {
                "template_path": template_path,
                "input_path": self.ui.inputPathEdit.text().strip(),
                "database_root_path": self._database_root_path(),
                "workspace_storage_path": self._active_storage_path(),
                "storage_path": self._active_storage_path(),
                "golden_path": self.ui.goldenPathEdit.text().strip(),
                "output_path": self.ui.outputPathEdit.text().strip(),
            },
            "template_summary": template_summary,
            "template_summary_error": template_error,
            "golden": {
                "golden_name": self.ui.goldenNameEdit.text().strip(),
                "reference_dims_text": self.ui.referenceDimsEdit.text().strip(),
                "filters_text": self.ui.filtersEdit.toPlainText(),
                "center_method": self.ui.centerMethodComboBox.currentText(),
                "threshold_mode": self.ui.thresholdModeComboBox.currentText(),
                "relative_limit": self.ui.relativeLimitSpinBox.value(),
                "sigma_multiplier": self.ui.sigmaMultiplierSpinBox.value(),
                "golden_source": self.ui.goldenSourceComboBox.currentText(),
            },
            "analysis": {
                "analysis_scope": self.ui.analysisScopeComboBox.currentText(),
                "outlier_fail_mode": self.ui.outlierFailModeComboBox.currentText(),
                "z_threshold": self.ui.zThresholdSpinBox.value(),
                "sample_ids_text": self.ui.analysisSampleIdsEdit.text().strip(),
                "exclude_sample_ids_text": self.ui.analysisExcludeSampleIdsEdit.text().strip(),
                "nodes_text": self.ui.analysisNodesEdit.text().strip(),
                "exclude_nodes_text": self.ui.analysisExcludeNodesEdit.text().strip(),
                "selected_dataset_ids": self._selected_analysis_dataset_ids(),
                "selected_import_entries": self._selected_analysis_import_entries(),
                "workbench_tab": self.ui.workbenchTabWidget.tabText(
                    self.ui.workbenchTabWidget.currentIndex()
                ),
                "result_tab": self.ui.resultTabWidget.tabText(
                    self.ui.resultTabWidget.currentIndex()
                ),
            },
        }

    def _collect_current_results_snapshot(self) -> dict[str, object]:
        return {
            "golden_coverage_summary": self.current_golden_coverage_summary,
            "outlier_summary_rows": self.current_outlier_summary_rows,
            "outlier_ratio_rows": self.current_outlier_ratio_rows,
            "storage_summary_label": self.ui.storageSummaryLabel.text(),
            "golden_coverage_summary_label": self.ui.goldenCoverageSummaryLabel.text(),
            "outlier_summary_label": self.ui.outlinerSummaryLabel.text(),
            "outlier_ratio_summary_label": self.ui.outlierRatioSummaryLabel.text(),
        }

    def _resolve_existing_output_path(
        self,
        output_path: str | Path,
        label: str,
    ) -> str | None:
        mode = self._resolve_existing_output_mode(output_path, label)
        if mode is None:
            return None
        if mode == "timestamp":
            from ..output_paths import resolve_output_path

            return str(resolve_output_path(output_path, if_exists="timestamp"))
        return str(output_path)

    def _resolve_existing_output_directory(
        self,
        output_path: str | Path,
        label: str,
    ) -> str | None:
        mode = self._resolve_existing_output_mode(output_path, label)
        if mode is None:
            return None
        if mode == "timestamp":
            from ..output_paths import prepare_output_directory

            resolved = prepare_output_directory(output_path, if_exists="timestamp")
            return str(resolved)
        return str(output_path)

    def _resolve_existing_output_mode(
        self,
        output_path: str | Path,
        label: str,
    ) -> str | None:
        target = Path(output_path)
        if not target.exists():
            return "overwrite"
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Output Path Already Exists")
        message_box.setIcon(QMessageBox.Warning)
        message_box.setText(
            f"{label} already exists:\n{target}"
        )
        message_box.setInformativeText(
            "Choose Overwrite to replace it, Timestamp Suffix to keep the old file and create a new one, or Cancel to stop this action."
        )
        overwrite_button = message_box.addButton("Overwrite", QMessageBox.AcceptRole)
        timestamp_button = message_box.addButton("Timestamp Suffix", QMessageBox.ActionRole)
        cancel_button = message_box.addButton(QMessageBox.Cancel)
        message_box.setDefaultButton(timestamp_button)
        message_box.exec()
        clicked = message_box.clickedButton()
        if clicked == overwrite_button:
            return "overwrite"
        if clicked == timestamp_button:
            return "timestamp"
        if clicked == cancel_button:
            return None
        return None

    def _selected_analysis_import_entries(self) -> list[dict[str, str]]:
        entries: list[dict[str, str]] = []
        for index in range(self.ui.analysisImportsListWidget.count()):
            item = self.ui.analysisImportsListWidget.item(index)
            if item.checkState() != Qt.Checked:
                continue
            entries.append(
                {
                    "dataset_id": str(item.data(Qt.UserRole)),
                    "label": item.text(),
                }
            )
        return entries

    @staticmethod
    def _populate_table(table, headers: list[str], rows: list[list[str]]) -> None:
        table.setSortingEnabled(False)
        table.clearContents()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for column_index, value in enumerate(values):
                table.setItem(row_index, column_index, QTableWidgetItem(value))
        table.resizeColumnsToContents()
        table.setSortingEnabled(True)


def launch() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    launch()
