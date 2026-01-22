from __future__ import annotations

from typing import Iterable, List

from liberty_core.cst import Token, TokenType


class MatrixShapeError(ValueError):
    pass


def parse_values_tokens(tokens: Iterable[Token], rows: int, cols: int) -> List[List[float]]:
    flat: List[float] = []
    for token in tokens:
        if token.type in {TokenType.ESCAPED_NEWLINE, TokenType.COMMENT}:
            continue
        if token.type in {TokenType.STRING, TokenType.IDENTIFIER}:
            for segment in token.value.split(","):
                stripped = segment.strip()
                if stripped:
                    flat.append(float(stripped))
            continue
        if token.type == TokenType.COMMA:
            continue
    expected = rows * cols
    if expected != len(flat):
        raise MatrixShapeError(f"Expected {expected} values but parsed {len(flat)}")
    return [flat[row * cols : (row + 1) * cols] for row in range(rows)]


def multiply_matrix(matrix: List[List[float]], scalar: float) -> List[List[float]]:
    return [[value * scalar for value in row] for row in matrix]


def add_matrices(left: List[List[float]], right: List[List[float]]) -> List[List[float]]:
    if len(left) != len(right):
        raise MatrixShapeError("Row count mismatch")
    result: List[List[float]] = []
    for left_row, right_row in zip(left, right):
        if len(left_row) != len(right_row):
            raise MatrixShapeError("Column count mismatch")
        result.append([left_value + right_value for left_value, right_value in zip(left_row, right_row)])
    return result
