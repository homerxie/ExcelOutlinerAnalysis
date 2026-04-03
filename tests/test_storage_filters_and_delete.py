from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from excel_data_analysis.models import MeasurementRecord
from excel_data_analysis.repository import Repository
from excel_data_analysis.runtime import default_database_root
from excel_data_analysis.service import build_dimension_filters, copy_storage, delete_storage_rows


class StorageFilterAndDeleteTests(unittest.TestCase):
    def test_default_database_root_uses_temp_database_under_app_directory(self) -> None:
        self.assertEqual(default_database_root().name, "tempDatabase")

    def test_build_dimension_filters_supports_include_and_exclude(self) -> None:
        filters = build_dimension_filters(
            sample_ids=["S001", "S002"],
            reliability_nodes=["T0", "T1"],
            exclude_sample_ids=["S999"],
            exclude_reliability_nodes=["T9"],
        )
        self.assertEqual(
            filters,
            {
                "sample_id": {
                    "include": ["S001", "S002"],
                    "exclude": ["S999"],
                },
                "reliability_node": {
                    "include": ["T0", "T1"],
                    "exclude": ["T9"],
                },
            },
        )

    def test_delete_storage_rows_removes_only_selected_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "database"
            repository = Repository(storage_path)
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
                    ),
                    MeasurementRecord(
                        dataset_id="dataset-1",
                        source_file=source_file,
                        row_number=2,
                        logical_metric="metric-1",
                        group_id="group-1",
                        group_display_name="Group 1",
                        presentation_group="Link1",
                        raw_column="Value_1",
                        value=2.0,
                        dimensions={"sample_id": "S2", "reliability_node": "T0"},
                    ),
                ],
            )

            payload = delete_storage_rows(
                str(storage_path),
                [
                    {
                        "dataset_id": "dataset-1",
                        "source_file": source_file,
                        "row_number": 1,
                    }
                ],
            )

            self.assertEqual(payload["deleted_row_count"], 1)
            self.assertEqual(payload["deleted_measurement_count"], 1)
            remaining_measurements = repository.load_measurements()
            self.assertEqual(len(remaining_measurements), 1)
            self.assertEqual(remaining_measurements[0].row_number, 2)
            remaining_entries = repository.load_dataset_entries()
            self.assertEqual(len(remaining_entries), 1)
            self.assertEqual(remaining_entries[0]["measurement_count"], 1)

    def test_delete_storage_rows_removes_import_history_when_dataset_becomes_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "database"
            repository = Repository(storage_path)
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

            delete_storage_rows(
                str(storage_path),
                [
                    {
                        "dataset_id": "dataset-1",
                        "source_file": source_file,
                        "row_number": 1,
                    }
                ],
            )

            self.assertEqual(repository.load_measurements(), [])
            self.assertEqual(repository.load_dataset_entries(), [])

    def test_replace_measurements_reconciles_import_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "database"
            repository = Repository(storage_path)
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
            repository.save_import(
                dataset_id="dataset-2",
                source_file=source_file,
                template_name="demo-template",
                measurements=[
                    MeasurementRecord(
                        dataset_id="dataset-2",
                        source_file=source_file,
                        row_number=2,
                        logical_metric="metric-1",
                        group_id="group-1",
                        group_display_name="Group 1",
                        presentation_group="Link1",
                        raw_column="Value_1",
                        value=2.0,
                        dimensions={"sample_id": "S2", "reliability_node": "T0"},
                    )
                ],
            )

            repository.replace_measurements(
                [
                    MeasurementRecord(
                        dataset_id="dataset-2",
                        source_file=source_file,
                        row_number=2,
                        logical_metric="metric-1",
                        group_id="group-1",
                        group_display_name="Group 1",
                        presentation_group="Link1",
                        raw_column="Value_1",
                        value=2.0,
                        dimensions={"sample_id": "S2", "reliability_node": "T0"},
                    ),
                    MeasurementRecord(
                        dataset_id="dataset-2",
                        source_file=source_file,
                        row_number=3,
                        logical_metric="metric-1",
                        group_id="group-1",
                        group_display_name="Group 1",
                        presentation_group="Link1",
                        raw_column="Value_1",
                        value=3.0,
                        dimensions={"sample_id": "S3", "reliability_node": "T1"},
                    ),
                ]
            )

            entries = repository.load_dataset_entries()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["dataset_id"], "dataset-2")
            self.assertEqual(entries[0]["measurement_count"], 2)

    def test_copy_storage_copies_database_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_storage = Path(temp_dir) / "source_db"
            target_storage = Path(temp_dir) / "target_db"
            repository = Repository(source_storage)
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

            payload = copy_storage(str(source_storage), str(target_storage))

            self.assertEqual(payload["destination"], str(target_storage.resolve()))
            self.assertTrue((target_storage / "measurements.jsonl").exists())
            self.assertTrue((target_storage / "datasets.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
