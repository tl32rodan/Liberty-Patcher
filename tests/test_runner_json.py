import json
import tempfile
import unittest
from pathlib import Path

from liberty_core import Parser
from liberty_core.cst import AttributeNode
from patch_engine import PatchRunner, find_nodes_by_scope, parse_array_tokens


class TestPatchRunnerJson(unittest.TestCase):
    def test_runner_applies_compiled_json(self) -> None:
        text = "library(test) { cell(A) { foo (1,2); } }"
        parse_result = Parser().parse(text)
        config = {
            "modifications": [
                {
                    "scope": {"path": [{"group": "library"}, {"group": "cell", "name": "A"}]},
                    "action": {"attribute": "foo", "operation": "add", "mode": "broadcast", "value": 1.0},
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "compiled.json"
            json_path.write_text(json.dumps(config), encoding="utf-8")
            loaded = json.loads(json_path.read_text(encoding="utf-8"))
        runner = PatchRunner()
        runner.run(parse_result, loaded)
        groups = find_nodes_by_scope(
            parse_result.root,
            {"path": [{"group": "library"}, {"group": "cell", "name": "A"}]},
        )
        foo_node = None
        for group in groups:
            for child in group.children:
                if isinstance(child, AttributeNode) and child.key == "foo":
                    foo_node = child
                    break
        self.assertIsNotNone(foo_node)
        values = parse_array_tokens(foo_node.raw_tokens)
        self.assertEqual(values, [[2.0, 3.0]])
