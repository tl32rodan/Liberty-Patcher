import unittest

from liberty_core import Parser
from patch_engine import ScopeMatchError, find_nodes_by_scope


class TestScopeSelectors(unittest.TestCase):
    def setUp(self) -> None:
        text = """
library (demo) {
  cell (AND3x1_ASAP7_6t_SL) {
    pin (A) {
      internal_power () {
        when : "(B * !C * !Y)";
        related_pg_pin : VDD;
        fall_power () {
          values ("1,2,3");
        }
      }
    }
  }
}
"""
        self.root = Parser().parse(text).root

    def test_scope_supports_regex_lists(self) -> None:
        scope = {
            "path": [
                {"group": "library"},
                {"group": ["cell"], "name": [r"AND3x1_.*", r"OR.*"]},
                {"group": "pin", "args": [r"A"]},
                {
                    "group": "internal_power",
                    "attributes": {"when": [r"\(B \* !C \* !Y\)"], "related_pg_pin": [r"VDD"]},
                },
            ]
        }
        matches = find_nodes_by_scope(self.root, scope)
        self.assertEqual(len(matches), 1)

    def test_scope_raises_on_missing_group(self) -> None:
        scope = {"path": [{"group": "library"}, {"group": "missing"}]}
        with self.assertRaises(ScopeMatchError):
            find_nodes_by_scope(self.root, scope, require_match=True)

    def test_scope_raises_on_missing_attribute(self) -> None:
        scope = {
            "path": [
                {"group": "library"},
                {"group": "cell", "name": "AND3x1_ASAP7_6t_SL"},
                {"group": "pin", "name": "A"},
                {"group": "internal_power", "attributes": {"when": ["NO_MATCH"]}},
            ]
        }
        with self.assertRaises(ScopeMatchError) as context:
            find_nodes_by_scope(self.root, scope, require_match=True)
        self.assertIn("Scope match failed", str(context.exception))
