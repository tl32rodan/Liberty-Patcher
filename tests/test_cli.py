import tempfile
import unittest
from pathlib import Path

import cli
import config_compiler


@unittest.skipIf(config_compiler.yaml is None, "PyYAML is required for YAML tests.")
class TestCliConfigLoading(unittest.TestCase):
    def test_load_config_yaml(self) -> None:
        yaml_text = """
modifications:
  - scope:
      path:
        - group: library
          name: lib
        - cell: "AND*"
    action:
      operation: multiply
      mode: broadcast
      value: 1.1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.yaml"
            path.write_text(yaml_text, encoding="utf-8")
            config = cli._load_config(str(path))
        self.assertIn("modifications", config)
        selector = config["modifications"][0]["scope"]["path"][1]
        self.assertEqual(selector["group"], "cell")
        self.assertEqual(selector["name"], "AND*")
