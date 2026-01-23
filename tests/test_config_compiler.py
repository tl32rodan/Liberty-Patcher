import unittest

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
