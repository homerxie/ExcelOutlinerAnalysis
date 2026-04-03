from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from .models import GoldenReference, MeasurementRecord
from .output_paths import resolve_output_path


class Repository:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.import_dir = self.root / "imports"
        self.golden_dir = self.root / "golden"
        self.measurements_path = self.root / "measurements.jsonl"
        self.datasets_path = self.root / "datasets.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)
        self.import_dir.mkdir(parents=True, exist_ok=True)
        self.golden_dir.mkdir(parents=True, exist_ok=True)

    def new_dataset_id(self) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{stamp}-{uuid4().hex[:8]}"

    def save_import(
        self,
        dataset_id: str,
        source_file: str,
        template_name: str,
        measurements: Iterable[MeasurementRecord],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        measurement_list = list(measurements)
        payload = {
            "dataset_id": dataset_id,
            "source_file": source_file,
            "template_name": template_name,
            "measurement_count": len(measurement_list),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        if metadata:
            payload.update(metadata)
        self.save_dataset_entry(payload)
        with self.measurements_path.open("a", encoding="utf-8") as handle:
            for item in measurement_list:
                handle.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
        self.reconcile_dataset_entries()

    def save_dataset_entry(self, payload: dict[str, Any]) -> None:
        if "created_at_utc" not in payload:
            payload = dict(payload)
            payload["created_at_utc"] = datetime.now(timezone.utc).isoformat()
        with self.datasets_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def load_measurements(self) -> list[MeasurementRecord]:
        if not self.measurements_path.exists():
            return []
        measurements: list[MeasurementRecord] = []
        with self.measurements_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                measurements.append(MeasurementRecord.from_dict(json.loads(line)))
        return measurements

    def replace_measurements(self, measurements: Iterable[MeasurementRecord]) -> None:
        measurement_list = list(measurements)
        with self.measurements_path.open("w", encoding="utf-8") as handle:
            for item in measurement_list:
                handle.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
        self.reconcile_dataset_entries()

    def delete_measurements(
        self,
        row_selectors: Iterable[tuple[str, str, int]],
    ) -> int:
        selectors = {
            (str(dataset_id), str(source_file), int(row_number))
            for dataset_id, source_file, row_number in row_selectors
        }
        if not selectors:
            return 0
        measurements = self.load_measurements()
        kept_measurements = [
            item
            for item in measurements
            if (item.dataset_id, item.source_file, item.row_number) not in selectors
        ]
        deleted_count = len(measurements) - len(kept_measurements)
        if deleted_count:
            self.replace_measurements(kept_measurements)
        return deleted_count

    def load_dataset_entries(self) -> list[dict[str, Any]]:
        if not self.datasets_path.exists():
            return []
        entries: list[dict[str, Any]] = []
        with self.datasets_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                entries.append(json.loads(line))
        return entries

    def replace_dataset_entries(self, entries: Iterable[dict[str, Any]]) -> None:
        entry_list = list(entries)
        with self.datasets_path.open("w", encoding="utf-8") as handle:
            for item in entry_list:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    def reconcile_dataset_entries(self) -> None:
        measurements = self.load_measurements()
        measurement_counts: dict[str, int] = {}
        for item in measurements:
            measurement_counts[item.dataset_id] = measurement_counts.get(item.dataset_id, 0) + 1

        entries = self.load_dataset_entries()
        if not entries:
            return

        reconciled_entries: list[dict[str, Any]] = []
        for entry in entries:
            dataset_id = str(entry.get("dataset_id", "")).strip()
            if not dataset_id or dataset_id not in measurement_counts:
                continue
            updated_entry = dict(entry)
            updated_entry["measurement_count"] = measurement_counts[dataset_id]
            reconciled_entries.append(updated_entry)
        self.replace_dataset_entries(reconciled_entries)

    def save_golden(
        self,
        reference: GoldenReference,
        if_exists: str = "overwrite",
    ) -> Path:
        path = resolve_output_path(
            self.golden_dir / f"{reference.name}.json",
            if_exists=if_exists,
        )
        if path.stem != reference.name:
            reference.name = path.stem
        path.write_text(
            json.dumps(reference.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def load_golden(self, path: str | Path) -> GoldenReference:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return GoldenReference.from_dict(payload)
