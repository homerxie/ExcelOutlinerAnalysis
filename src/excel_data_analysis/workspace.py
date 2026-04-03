from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


TEMP_WORKSPACE_DIRNAME = "temp"
RESULT_DIRNAME = "result"
DATABASE_ENTRY_NAMES = (
    "measurements.jsonl",
    "datasets.jsonl",
    "golden",
    "imports",
)
DATABASE_ROOT_ENTRY_NAMES = (
    *DATABASE_ENTRY_NAMES,
    TEMP_WORKSPACE_DIRNAME,
    RESULT_DIRNAME,
    ".excel_data_analysis_gui_state.json",
)


def database_workspace_path(database_root: str | Path) -> Path:
    return Path(database_root) / TEMP_WORKSPACE_DIRNAME


def database_result_dir(database_root: str | Path) -> Path:
    return Path(database_root) / RESULT_DIRNAME


def default_database_output_path(
    database_root: str | Path,
    filename: str = "sample_chip_data_real_result.xlsx",
) -> Path:
    return database_result_dir(database_root) / filename


def ensure_database_workspace(database_root: str | Path) -> Path:
    root = Path(database_root)
    root.mkdir(parents=True, exist_ok=True)
    workspace = database_workspace_path(root)
    if workspace.exists():
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace
    workspace.mkdir(parents=True, exist_ok=True)
    _copy_database_entries(root, workspace)
    return workspace


def database_workspace_differs(database_root: str | Path) -> bool:
    root = Path(database_root)
    workspace = database_workspace_path(root)
    if not workspace.exists():
        return False
    return _snapshot_database_entries(root) != _snapshot_database_entries(workspace)


def reset_database_workspace(database_root: str | Path) -> Path:
    root = Path(database_root)
    workspace = database_workspace_path(root)
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    _copy_database_entries(root, workspace)
    return workspace


def merge_database_workspace(database_root: str | Path) -> Path:
    root = Path(database_root)
    workspace = database_workspace_path(root)
    if not workspace.exists():
        return ensure_database_workspace(root)
    try:
        _clear_database_entries(root)
        _copy_database_entries(workspace, root)
    except PermissionError as exc:
        raise PermissionError(
            "Cannot save the database because one or more files are open in another application "
            "(for example Excel). Please close those files and try again."
        ) from exc
    return workspace


def save_database_workspace_as(
    database_root: str | Path,
    target_database_root: str | Path,
) -> tuple[Path, Path]:
    source_root = Path(database_root)
    workspace = ensure_database_workspace(source_root)
    target_root = Path(target_database_root)
    target_root.mkdir(parents=True, exist_ok=True)
    try:
        _clear_database_entries(target_root)
        _copy_database_entries(workspace, target_root)
        _copy_result_entries(source_root, target_root)
    except PermissionError as exc:
        raise PermissionError(
            "Cannot save the database copy because one or more files are open in another application "
            "(for example Excel). Please close those files and try again."
        ) from exc
    target_workspace = database_workspace_path(target_root)
    if target_workspace.exists():
        shutil.rmtree(target_workspace)
    target_workspace.mkdir(parents=True, exist_ok=True)
    _copy_database_entries(target_root, target_workspace)
    return target_root, target_workspace


def clear_database_root(database_root: str | Path) -> Path:
    root = Path(database_root)
    root.mkdir(parents=True, exist_ok=True)
    for name in DATABASE_ROOT_ENTRY_NAMES:
        path = root / name
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    return root


def _clear_database_entries(root: Path) -> None:
    for name in DATABASE_ENTRY_NAMES:
        path = root / name
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def _copy_database_entries(source_root: Path, destination_root: Path) -> None:
    destination_root.mkdir(parents=True, exist_ok=True)
    for name in DATABASE_ENTRY_NAMES:
        source = source_root / name
        if not source.exists():
            continue
        destination = destination_root / name
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def _copy_result_entries(source_root: Path, destination_root: Path) -> None:
    source_result_dir = database_result_dir(source_root)
    if not source_result_dir.exists():
        return
    destination_result_dir = database_result_dir(destination_root)
    shutil.copytree(source_result_dir, destination_result_dir, dirs_exist_ok=True)


def _snapshot_database_entries(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for name in DATABASE_ENTRY_NAMES:
        path = root / name
        if not path.exists():
            continue
        if path.is_file():
            snapshot[name] = _hash_file(path)
            continue
        for child in sorted(path.rglob("*")):
            if child.is_dir():
                continue
            relative = child.relative_to(root).as_posix()
            snapshot[relative] = _hash_file(child)
    return snapshot


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
