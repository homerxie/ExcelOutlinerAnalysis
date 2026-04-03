from __future__ import annotations

import json
from pathlib import Path
from typing import Any


GUI_STATE_FILENAME = ".excel_data_analysis_gui_state.json"


def gui_state_path(storage_path: str | Path) -> Path:
    return Path(storage_path) / GUI_STATE_FILENAME


def save_gui_state(
    storage_path: str | Path,
    payload: dict[str, Any],
) -> Path:
    target = gui_state_path(storage_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target


def load_gui_state(
    storage_path: str | Path,
) -> dict[str, Any] | None:
    target = gui_state_path(storage_path)
    if not target.exists():
        return None
    return json.loads(target.read_text(encoding="utf-8"))
