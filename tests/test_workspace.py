from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from excel_data_analysis.models import MeasurementRecord
from excel_data_analysis.repository import Repository
from excel_data_analysis.workspace import (
    TEMP_WORKSPACE_DIRNAME,
    clear_database_root,
    database_workspace_path,
    database_workspace_differs,
    default_database_output_path,
    reset_database_workspace,
    ensure_database_workspace,
    merge_database_workspace,
    save_database_workspace_as,
)


class WorkspaceTests(unittest.TestCase):
    def test_default_database_output_path_points_to_result_folder(self) -> None:
        database_root = Path("/tmp/demo_database")
        self.assertEqual(
            default_database_output_path(database_root),
            database_root / "result" / "sample_chip_data_real_result.xlsx",
        )

    def test_ensure_database_workspace_creates_temp_clone(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_root = Path(temp_dir) / "database"
            repository = Repository(database_root)
            repository.save_import(
                dataset_id="dataset-1",
                source_file=str(Path(temp_dir) / "input.xlsx"),
                template_name="demo-template",
                measurements=[
                    MeasurementRecord(
                        dataset_id="dataset-1",
                        source_file=str(Path(temp_dir) / "input.xlsx"),
                        row_number=1,
                        logical_metric="metric-1",
                        group_id="group-1",
                        group_display_name="Group 1",
                        presentation_group="Link1",
                        raw_column="Value_1",
                        value=1.0,
                        dimensions={"sample_id": "S1", "reliability_node": "T0"},
                    )
                ],
            )

            workspace = ensure_database_workspace(database_root)

            self.assertEqual(workspace, database_workspace_path(database_root))
            self.assertTrue((workspace / "measurements.jsonl").exists())
            self.assertTrue((workspace / "datasets.jsonl").exists())
            self.assertFalse(database_workspace_differs(database_root))

    def test_merge_database_workspace_copies_temp_back_to_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_root = Path(temp_dir) / "database"
            repository = Repository(database_root)
            source_file = str(Path(temp_dir) / "input.xlsx")
            repository.save_import(
                dataset_id="dataset-1",
                source_file=source_file,
                template_name="demo-template",
                measurements=[
                    MeasurementRecord(
                        dataset_id="dataset-1",
                        source_file=source_file,
                        row_number=1,
                        logical_metric="metric-1",
                        group_id="group-1",
                        group_display_name="Group 1",
                        presentation_group="Link1",
                        raw_column="Value_1",
                        value=1.0,
                        dimensions={"sample_id": "S1", "reliability_node": "T0"},
                    )
                ],
            )
            workspace = ensure_database_workspace(database_root)
            workspace_repo = Repository(workspace)
            workspace_repo.save_import(
                dataset_id="dataset-2",
                source_file=source_file,
                template_name="demo-template",
                measurements=[
                    MeasurementRecord(
                        dataset_id="dataset-2",
                        source_file=source_file,
                        row_number=2,
                        logical_metric="metric-2",
                        group_id="group-2",
                        group_display_name="Group 2",
                        presentation_group="Link2",
                        raw_column="Value_2",
                        value=2.0,
                        dimensions={"sample_id": "S2", "reliability_node": "T1"},
                    )
                ],
            )

            merge_database_workspace(database_root)

            root_repo = Repository(database_root)
            root_measurements = root_repo.load_measurements()
            self.assertEqual(len(root_measurements), 2)
            self.assertEqual({item.dataset_id for item in root_measurements}, {"dataset-1", "dataset-2"})
            self.assertFalse(database_workspace_differs(database_root))

    def test_database_workspace_differs_and_reset_restores_saved_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_root = Path(temp_dir) / "database"
            repository = Repository(database_root)
            source_file = str(Path(temp_dir) / "input.xlsx")
            repository.save_import(
                dataset_id="dataset-1",
                source_file=source_file,
                template_name="demo-template",
                measurements=[
                    MeasurementRecord(
                        dataset_id="dataset-1",
                        source_file=source_file,
                        row_number=1,
                        logical_metric="metric-1",
                        group_id="group-1",
                        group_display_name="Group 1",
                        presentation_group="Link1",
                        raw_column="Value_1",
                        value=1.0,
                        dimensions={"sample_id": "S1", "reliability_node": "T0"},
                    )
                ],
            )
            workspace = ensure_database_workspace(database_root)
            Repository(workspace).save_import(
                dataset_id="dataset-2",
                source_file=source_file,
                template_name="demo-template",
                measurements=[
                    MeasurementRecord(
                        dataset_id="dataset-2",
                        source_file=source_file,
                        row_number=2,
                        logical_metric="metric-2",
                        group_id="group-2",
                        group_display_name="Group 2",
                        presentation_group="Link2",
                        raw_column="Value_2",
                        value=2.0,
                        dimensions={"sample_id": "S2", "reliability_node": "T1"},
                    )
                ],
            )

            self.assertTrue(database_workspace_differs(database_root))

            reset_database_workspace(database_root)

            self.assertFalse(database_workspace_differs(database_root))
            workspace_measurements = Repository(database_workspace_path(database_root)).load_measurements()
            self.assertEqual(len(workspace_measurements), 1)
            self.assertEqual(workspace_measurements[0].dataset_id, "dataset-1")

    def test_save_database_workspace_as_creates_new_root_and_new_temp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source_db"
            target_root = Path(temp_dir) / "target_db"
            repository = Repository(source_root)
            source_file = str(Path(temp_dir) / "input.xlsx")
            repository.save_import(
                dataset_id="dataset-1",
                source_file=source_file,
                template_name="demo-template",
                measurements=[
                    MeasurementRecord(
                        dataset_id="dataset-1",
                        source_file=source_file,
                        row_number=1,
                        logical_metric="metric-1",
                        group_id="group-1",
                        group_display_name="Group 1",
                        presentation_group="Link1",
                        raw_column="Value_1",
                        value=1.0,
                        dimensions={"sample_id": "S1", "reliability_node": "T0"},
                    )
                ],
            )
            source_workspace = ensure_database_workspace(source_root)
            result_dir = source_root / "result"
            result_dir.mkdir(parents=True, exist_ok=True)
            (result_dir / "existing_report.xlsx").write_text("report", encoding="utf-8")
            Repository(source_workspace).save_import(
                dataset_id="dataset-2",
                source_file=source_file,
                template_name="demo-template",
                measurements=[
                    MeasurementRecord(
                        dataset_id="dataset-2",
                        source_file=source_file,
                        row_number=2,
                        logical_metric="metric-2",
                        group_id="group-2",
                        group_display_name="Group 2",
                        presentation_group="Link2",
                        raw_column="Value_2",
                        value=2.0,
                        dimensions={"sample_id": "S2", "reliability_node": "T1"},
                    )
                ],
            )

            saved_root, saved_workspace = save_database_workspace_as(source_root, target_root)

            self.assertEqual(saved_root, target_root)
            self.assertEqual(saved_workspace, target_root / TEMP_WORKSPACE_DIRNAME)
            self.assertTrue((target_root / "measurements.jsonl").exists())
            self.assertTrue((saved_workspace / "measurements.jsonl").exists())
            self.assertTrue((target_root / "result" / "existing_report.xlsx").exists())
            target_measurements = Repository(target_root).load_measurements()
            self.assertEqual(len(target_measurements), 2)

    def test_clear_database_root_removes_temp_database_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_root = Path(temp_dir) / "database"
            repository = Repository(database_root)
            source_file = str(Path(temp_dir) / "input.xlsx")
            repository.save_import(
                dataset_id="dataset-1",
                source_file=source_file,
                template_name="demo-template",
                measurements=[
                    MeasurementRecord(
                        dataset_id="dataset-1",
                        source_file=source_file,
                        row_number=1,
                        logical_metric="metric-1",
                        group_id="group-1",
                        group_display_name="Group 1",
                        presentation_group="Link1",
                        raw_column="Value_1",
                        value=1.0,
                        dimensions={"sample_id": "S1", "reliability_node": "T0"},
                    )
                ],
            )
            ensure_database_workspace(database_root)
            result_dir = database_root / "result"
            result_dir.mkdir(parents=True, exist_ok=True)
            (result_dir / "existing_report.xlsx").write_text("report", encoding="utf-8")
            (database_root / ".excel_data_analysis_gui_state.json").write_text(
                "{}",
                encoding="utf-8",
            )

            clear_database_root(database_root)

            self.assertTrue(database_root.exists())
            self.assertFalse((database_root / "measurements.jsonl").exists())
            self.assertFalse((database_root / "datasets.jsonl").exists())
            self.assertFalse((database_root / "golden").exists())
            self.assertFalse((database_root / "imports").exists())
            self.assertFalse((database_root / "temp").exists())
            self.assertFalse((database_root / "result").exists())
            self.assertFalse((database_root / ".excel_data_analysis_gui_state.json").exists())


if __name__ == "__main__":
    unittest.main()
