from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from excel_data_analysis.gui_state import GUI_STATE_FILENAME, load_gui_state, save_gui_state


class GuiStateTests(unittest.TestCase):
    def test_save_and_load_gui_state_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "database"
            payload = {
                "version": 1,
                "paths": {"template_path": "/tmp/template.json"},
                "analysis": {"analysis_scope": "filtered_database"},
            }
            saved_path = save_gui_state(storage_path, payload)
            self.assertEqual(saved_path.name, GUI_STATE_FILENAME)
            self.assertEqual(load_gui_state(storage_path), payload)


if __name__ == "__main__":
    unittest.main()
