import sqlite3
import tempfile
import unittest

from liberty_core import Lexer, Parser, TokenType
from liberty_core.cst import AttributeNode
from patch_engine import (
    MatrixShapeError,
    PatchRunner,
    UnitExpectations,
    UnitMismatchError,
    add_matrices,
    find_nodes_by_scope,
    multiply_matrix,
    parse_array_tokens,
    validate_units,
)
from provenance import ArtifactRecord, BatchOp, ProvenanceDB


class TestPatchEngine(unittest.TestCase):
    def test_validate_units_mismatch(self) -> None:
        expectations = UnitExpectations(time_unit="1ns")
        with self.assertRaises(UnitMismatchError):
            validate_units({"time_unit": "2ns"}, expectations)

    def test_parse_values_tokens(self) -> None:
        text = 'values ( "1,2" \\\n "3,4" );'
        tokens = Lexer(text).tokenize()
        start_index = next(index for index, token in enumerate(tokens) if token.type == TokenType.GROUP_START)
        end_index = next(index for index, token in enumerate(tokens) if token.type == TokenType.GROUP_END)
        values_tokens = tokens[start_index + 1 : end_index]
        matrix = parse_array_tokens(values_tokens)
        self.assertEqual(matrix, [[1.0, 2.0], [3.0, 4.0]])

    def test_matrix_operations(self) -> None:
        matrix = [[1.0, 2.0], [3.0, 4.0]]
        self.assertEqual(multiply_matrix(matrix, 2.0), [[2.0, 4.0], [6.0, 8.0]])
        self.assertEqual(add_matrices(matrix, matrix), [[2.0, 4.0], [6.0, 8.0]])
        with self.assertRaises(MatrixShapeError):
            add_matrices([[1.0]], [[1.0, 2.0]])

    def test_patch_runner_preserves_unquoted_arrays(self) -> None:
        text = "library(test) { cell(A) { foo (0.1, 0.2); } }"
        parse_result = Parser().parse(text)
        config = {
            "modifications": [
                {
                    "scope": {"path": [{"group": "library"}, {"group": "cell", "name": "A"}]},
                    "action": {"attribute": "foo", "operation": "add", "mode": "broadcast", "value": 0.1},
                }
            ]
        }
        runner = PatchRunner()
        runner.run(parse_result, config)
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
        token_types = [token.type for token in foo_node.raw_tokens]
        self.assertIn(TokenType.IDENTIFIER, token_types)


class TestProvenance(unittest.TestCase):
    def test_provenance_db_logging(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            db = ProvenanceDB(tmp.name)
            batch = BatchOp(
                batch_id="batch-1",
                description="test",
                config_json={"mod": []},
                expected_units={"time_unit": "1ns"},
            )
            db.log_batch(batch)
            db.log_artifacts(
                [
                    ArtifactRecord(
                        batch_id="batch-1",
                        file_path="file.lib",
                        input_hash="a" * 64,
                        output_hash="b" * 64,
                        status="ok",
                    )
                ]
            )
            with sqlite3.connect(tmp.name) as conn:
                batch_rows = conn.execute("SELECT COUNT(*) FROM batch_ops").fetchone()[0]
                artifact_rows = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
            self.assertEqual(batch_rows, 1)
            self.assertEqual(artifact_rows, 1)
