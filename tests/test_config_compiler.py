import json
import tempfile
import unittest
from pathlib import Path

import config_compiler


@unittest.skipIf(config_compiler.yaml is None, "PyYAML is required for YAML tests.")
class TestConfigCompiler(unittest.TestCase):
    def test_type1_shorthand(self) -> None:
        yaml_text = """
modifications:
  - scope:
      path:
        - cell: "AND*"
        - timing:
            WHERE:
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
        self.assertEqual(path[1]["where"], {"related_pin": "A"})

    def test_where_keyword(self) -> None:
        yaml_text = """
modifications:
  - scope:
      path:
        - timing:
          WHERE:
            timing_type: "combinational"
    action:
      operation: add
      mode: broadcast
      value: 0.5
"""
        compiled = config_compiler.compile_config(yaml_text)
        selector = compiled["modifications"][0]["scope"]["path"][0]
        self.assertEqual(selector["where"], {"timing_type": "combinational"})

    def test_list_selectors(self) -> None:
        yaml_text = """
modifications:
  - scope:
      path:
        - cell:
          name:
            - "AND.*"
            - "OR.*"
        - timing:
          WHERE:
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
        self.assertEqual(attr_selector["where"]["related_pin"], ["A", "B"])

    def test_type1_with_arg(self) -> None:
        yaml_text = """
modifications:
  - scope:
      path:
        - cell_rise: "delay_template_7x7"
    action:
      operation: add
      mode: broadcast
      value: 0.01
"""
        compiled = config_compiler.compile_config(yaml_text)
        selector = compiled["modifications"][0]["scope"]["path"][0]
        self.assertEqual(selector["group"], "cell_rise")
        self.assertEqual(selector["name"], "delay_template_7x7")

    def test_type2_null_value(self) -> None:
        yaml_text = """
modifications:
  - scope:
      path:
        - timing:
    action:
      operation: add
      mode: broadcast
      value: 0.01
"""
        compiled = config_compiler.compile_config(yaml_text)
        selector = compiled["modifications"][0]["scope"]["path"][0]
        self.assertEqual(selector["group"], "timing")
        self.assertNotIn("name", selector)

    def test_multi_key_with_where(self) -> None:
        yaml_text = """
modifications:
  - scope:
      path:
        - timing:
          WHERE:
            related_pin: "A"
    action:
      operation: add
      mode: broadcast
      value: 0.01
"""
        compiled = config_compiler.compile_config(yaml_text)
        selector = compiled["modifications"][0]["scope"]["path"][0]
        self.assertEqual(selector["group"], "timing")
        self.assertEqual(selector["where"], {"related_pin": "A"})

    def test_type1_with_name_and_where(self) -> None:
        compiled = config_compiler.compile_config_data({
            "modifications": [{
                "scope": {
                    "path": [{"cell_rise": "delay_*", "WHERE": {"index_1": "5"}}]
                },
                "action": {"operation": "add", "mode": "broadcast", "value": 0.01},
            }]
        })
        selector = compiled["modifications"][0]["scope"]["path"][0]
        self.assertEqual(selector["group"], "cell_rise")
        self.assertEqual(selector["name"], "delay_*")
        self.assertEqual(selector["where"], {"index_1": "5"})

    def test_error_multiple_group_type_keys(self) -> None:
        with self.assertRaises(config_compiler.ConfigCompilerError) as ctx:
            config_compiler.compile_config_data({
                "modifications": [{
                    "scope": {
                        "path": [{"cell": "AND*", "timing": None}]
                    },
                    "action": {"operation": "add", "mode": "broadcast", "value": 0.01},
                }]
            })
        self.assertIn("multiple group type keys", str(ctx.exception))

    def test_error_no_group_type_key(self) -> None:
        with self.assertRaises(config_compiler.ConfigCompilerError) as ctx:
            config_compiler.compile_config_data({
                "modifications": [{
                    "scope": {
                        "path": [{"name": "foo", "WHERE": {}}]
                    },
                    "action": {"operation": "add", "mode": "broadcast", "value": 0.01},
                }]
            })
        self.assertIn("group type key", str(ctx.exception))

    def test_compile_config_exports_json(self) -> None:
        yaml_text = """
modifications:
  - scope:
      path:
        - cell: "AND*"
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
