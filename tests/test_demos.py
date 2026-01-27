import json
import tempfile
import unittest
from pathlib import Path

import demo_format
import demo_patch


class TestDemos(unittest.TestCase):
    def test_demo_format_uses_cli_handler(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.lib"
            output_path = Path(tmpdir) / "output.lib"
            input_path.write_text('cell(A) { area : 1; }\n', encoding="utf-8")

            exit_code = demo_format.main(
                input_path=str(input_path),
                output_path=str(output_path),
                indent_size=2,
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())
            output_text = output_path.read_text(encoding="utf-8")
            self.assertIn("cell (A) {", output_text)
            self.assertIn("area : 1;", output_text)

    def test_demo_patch_uses_cli_handler(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.lib"
            config_path = Path(tmpdir) / "config.json"
            output_path = Path(tmpdir) / "output.lib"
            input_path.write_text(
                "library(test) { cell(A) { foo (1, 2); } }\n",
                encoding="utf-8",
            )
            config = {
                "modifications": [
                    {
                        "scope": {"path": [{"group": "library"}, {"group": "cell", "name": "A"}]},
                        "action": {"attribute": "foo", "operation": "add", "mode": "broadcast", "value": 0.1},
                    }
                ]
            }
            config_path.write_text(json.dumps(config), encoding="utf-8")

            exit_code = demo_patch.main(
                input_path=str(input_path),
                config_path=str(config_path),
                output_path=str(output_path),
                indent_size=2,
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())
            output_text = output_path.read_text(encoding="utf-8")
            self.assertIn("foo (1.1, 2.1);", output_text)
