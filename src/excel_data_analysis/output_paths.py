from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil


def resolve_output_path(
    path: str | Path,
    if_exists: str = "overwrite",
) -> Path:
    output_path = Path(path)
    if if_exists not in {"overwrite", "timestamp", "error"}:
        raise ValueError(
            f"Unsupported if_exists mode: {if_exists}. Expected overwrite, timestamp, or error."
        )
    if not output_path.exists() or if_exists == "overwrite":
        return output_path
    if if_exists == "error":
        raise FileExistsError(f"Output file already exists: {output_path}")
    return _timestamped_output_path(output_path)


def prepare_output_directory(
    path: str | Path,
    if_exists: str = "overwrite",
) -> Path:
    directory_path = Path(path)
    if if_exists not in {"overwrite", "timestamp", "error"}:
        raise ValueError(
            f"Unsupported if_exists mode: {if_exists}. Expected overwrite, timestamp, or error."
        )
    if directory_path.exists():
        if if_exists == "error":
            raise FileExistsError(f"Output directory already exists: {directory_path}")
        if if_exists == "timestamp":
            directory_path = _timestamped_output_path(directory_path)
        else:
            if directory_path.is_dir():
                shutil.rmtree(directory_path)
            else:
                directory_path.unlink()
    directory_path.mkdir(parents=True, exist_ok=True)
    return directory_path


def _timestamped_output_path(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    candidate = path.with_name(f"{path.stem}_{timestamp}{path.suffix}")
    index = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}_{timestamp}_{index}{path.suffix}")
        index += 1
    return candidate
