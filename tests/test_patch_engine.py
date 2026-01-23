import sqlite3
import tempfile
import unittest

from liberty_core import Lexer, TokenType
from patch_engine import (
    MatrixShapeError,
    UnitExpectations,
    UnitMismatchError,
    add_matrices,
    multiply_matrix,
    parse_values_tokens,
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
        matrix = parse_values_tokens(values_tokens, rows=2, cols=2)
        self.assertEqual(matrix, [[1.0, 2.0], [3.0, 4.0]])

    def test_matrix_operations(self) -> None:
        matrix = [[1.0, 2.0], [3.0, 4.0]]
        self.assertEqual(multiply_matrix(matrix, 2.0), [[2.0, 4.0], [6.0, 8.0]])
        self.assertEqual(add_matrices(matrix, matrix), [[2.0, 4.0], [6.0, 8.0]])
        with self.assertRaises(MatrixShapeError):
            add_matrices([[1.0]], [[1.0, 2.0]])


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
