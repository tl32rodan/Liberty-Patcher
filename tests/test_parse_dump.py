import json
import tempfile
import unittest
from pathlib import Path

from liberty_core import Parser, dump_parse_result, serialize_parse_result


class TestParseDump(unittest.TestCase):
    def test_dump_parse_result_writes_json(self) -> None:
        text = "library(test) { cell(A) { foo (1,2); } }"
        parse_result = Parser().parse(text)
        payload = serialize_parse_result(parse_result)
        self.assertIn("root", payload)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "parse.json"
            dump_parse_result(parse_result, str(output_path))
            stored = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload, stored)
