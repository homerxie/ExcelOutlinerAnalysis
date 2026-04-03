from __future__ import annotations

import sys
from pathlib import Path


APP_NAME = "ExcelDataAnalysis"


def package_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass).resolve() / "excel_data_analysis"
        return Path(sys.executable).resolve().parent / "excel_data_analysis"
    return Path(__file__).resolve().parent


def bundled_template_path() -> Path:
    return package_root() / "assets" / "templates" / "chip_reliability_template.json"


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return repo_root()


def repo_root() -> Path:
    return package_root().parent.parent


def repo_examples_dir() -> Path | None:
    if getattr(sys, "frozen", False):
        return None
    path = repo_root() / "examples"
    if path.exists():
        return path
    return None


def default_database_root() -> Path:
    return app_root() / "tempDatabase"


def default_export_dir() -> Path:
    documents = _documents_home()
    return documents / APP_NAME / "exports"


def default_output_path(filename: str = "analysis_output.xlsx") -> Path:
    examples_dir = repo_examples_dir()
    if examples_dir is not None:
        return examples_dir / filename
    return default_export_dir() / filename


def default_dialog_dir() -> Path:
    if getattr(sys, "frozen", False):
        return app_root()
    return repo_root()


def _documents_home() -> Path:
    path = Path.home() / "Documents"
    if path.exists():
        return path
    return Path.home()
