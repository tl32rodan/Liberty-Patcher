import json
import tempfile
import unittest
from pathlib import Path

import config_compiler


@unittest.skipIf(config_compiler.yaml is None, "PyYAML is required for YAML tests.")
class TestConfigCompiler(unittest.TestCase):
    def test_compile_config_expands_shorthand(self) -> None:
        yaml_text = """
modifications:
  - scope:
      path:
        - cell: "AND*"
        - timing:
            attributes:
              related_pin: "A"
    action:
      operation: multiply
      mode: broadcast
      value: 1.1
"""
        compiled = config_compiler.compile_config(yaml_text)
        path = compiled["modifications"][0]["scope"]["path"]
        self.assertEqual(path[0]["group"], "cell")
        self.assertEqual(path[0]["name"], "AND*")
        self.assertEqual(path[1]["group"], "timing")
        self.assertEqual(path[1]["attributes"], {"related_pin": "A"})

    def test_compile_config_supports_attrs_alias(self) -> None:
        yaml_text = """
modifications:
  - scope:
      path:
        - group: timing
          attrs:
            timing_type: "combinational"
    action:
      operation: add
      mode: broadcast
      value: 0.5
"""
        compiled = config_compiler.compile_config(yaml_text)
        selector = compiled["modifications"][0]["scope"]["path"][0]
        self.assertEqual(selector["attributes"], {"timing_type": "combinational"})

    def test_compile_config_keeps_list_selectors(self) -> None:
        yaml_text = """
modifications:
  - scope:
      path:
        - group: cell
          name:
            - "AND.*"
            - "OR.*"
        - group: timing
          attributes:
            related_pin:
              - "A"
              - "B"
    action:
      operation: add
      mode: broadcast
      value: 0.5
"""
        compiled = config_compiler.compile_config(yaml_text)
        selector = compiled["modifications"][0]["scope"]["path"][0]
        self.assertEqual(selector["name"], ["AND.*", "OR.*"])
        attr_selector = compiled["modifications"][0]["scope"]["path"][1]
        self.assertEqual(attr_selector["attributes"]["related_pin"], ["A", "B"])

    def test_compile_config_exports_json(self) -> None:
        yaml_text = """
modifications:
  - scope:
      path:
        - group: cell
          name: "AND*"
    action:
      operation: add
      mode: broadcast
      value: 0.1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "compiled.json"
            compiled = config_compiler.compile_config(yaml_text, export_json_path=str(output_path))
            exported = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(compiled, exported)
