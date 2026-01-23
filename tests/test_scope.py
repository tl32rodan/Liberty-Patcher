import unittest

from liberty_core import Parser
from patch_engine import find_nodes_by_scope


class TestScopePathTraversal(unittest.TestCase):
    def test_find_nodes_by_path(self) -> None:
        text = (
            "library(lib) {\n"
            "  cell(A) {\n"
            "    pin(X) {\n"
            "      timing() {\n"
            '        related_pin : "Y";\n'
            "      }\n"
            "    }\n"
            "  }\n"
            "}\n"
        )
        result = Parser().parse(text)
        scope = {
            "path": [
                {"group": "library", "name": "lib"},
                {"group": "cell", "name": "A"},
                {"group": "pin", "name": "X"},
                {"group": "timing", "attributes": {"related_pin": "Y"}},
            ]
        }
        groups = find_nodes_by_scope(result.root, scope)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].name, "timing")
