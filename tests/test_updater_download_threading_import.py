from __future__ import annotations

import ast
from pathlib import Path
import unittest


class UpdaterDownloadThreadingImportTests(unittest.TestCase):
    def _source(self) -> str:
        root = Path(__file__).resolve().parents[1]
        return (root / "src" / "updater" / "update.py").read_text(encoding="utf-8")

    def test_update_module_has_threading_for_segmented_download(self) -> None:
        tree = ast.parse(self._source())
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }

        self.assertIn("threading", imported_names)

    def test_update_module_imports_threading_explicitly(self) -> None:
        source = self._source()
        self.assertIn("import threading", source)
        self.assertIn("threading.Lock()", source)


if __name__ == "__main__":
    unittest.main()
