from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, List, Optional
from uuid import uuid4

from liberty_core.cst import AttributeNode, GroupNode, Token, TokenType
from liberty_core.parser import ParseResult
from provenance import ArtifactRecord, BatchOp, ProvenanceDB

from .matrix import ArrayFormat, add_matrices, extract_array_format, multiply_matrix, parse_array_tokens
from .scope import find_nodes_by_scope
from .units import UnitExpectations, validate_units


class PatchActionError(ValueError):
    pass


@dataclass
class PatchSummary:
    batch_id: str
    modified_groups: int


class PatchRunner:
    def __init__(self, provenance_db: Optional[ProvenanceDB] = None, batch_id: Optional[str] = None) -> None:
        self.provenance_db = provenance_db
        self.batch_id = batch_id or f"batch-{uuid4()}"

    def run(self, parse_result: ParseResult, config: dict) -> PatchSummary:
        expectations = UnitExpectations.from_config(config)
        validate_units(parse_result.context.as_dict(), expectations)
        modifications = config.get("modifications", [])
        modified_groups = 0
        for modification in modifications:
            scope = modification.get("scope", {})
            action = modification.get("action", {})
            attribute = action.get("attribute", "values")
            groups = find_nodes_by_scope(parse_result.root, scope, require_match=True)
            for group in groups:
                self._apply_action(group, attribute, action)
                modified_groups += 1
        return PatchSummary(batch_id=self.batch_id, modified_groups=modified_groups)

    def log_run(
        self,
        config: dict,
        description: str,
        input_text: str,
        output_text: str,
        output_path: str,
    ) -> None:
        if self.provenance_db is None:
            return
        batch = BatchOp(
            batch_id=self.batch_id,
            description=description,
            config_json=config,
            expected_units=config.get("expected_units", {}),
        )
        self.provenance_db.log_batch(batch)
        input_hash = hashlib.sha256(input_text.encode("utf-8")).hexdigest()
        output_hash = hashlib.sha256(output_text.encode("utf-8")).hexdigest()
        self.provenance_db.log_artifacts(
            [
                ArtifactRecord(
                    batch_id=self.batch_id,
                    file_path=output_path,
                    input_hash=input_hash,
                    output_hash=output_hash,
                    status="ok",
                )
            ]
        )

    def _apply_action(self, group: GroupNode, attribute: str, action: dict) -> None:
        for _, node in _iter_attribute_nodes(group, attribute):
            array_format = extract_array_format(node.raw_tokens)
            matrix = parse_array_tokens(node.raw_tokens)
            updated = _apply_operation(matrix, action)
            node.raw_tokens = _matrix_to_tokens(updated, _array_uses_quotes(node.raw_tokens), array_format)


def _apply_operation(matrix: List[List[float]], action: dict) -> List[List[float]]:
    operation = action.get("operation")
    mode = action.get("mode", "broadcast")
    value = action.get("value")
    if operation is None:
        raise PatchActionError("Missing operation in action.")
    if value is None:
        raise PatchActionError("Missing value in action.")
    if operation == "multiply":
        if mode != "broadcast":
            raise PatchActionError(f"Unsupported mode for multiply: {mode}")
        return multiply_matrix(matrix, float(value))
    if operation == "add":
        if mode == "broadcast":
            scalar = float(value)
            scalar_matrix = [[scalar for _ in row] for row in matrix]
            return add_matrices(matrix, scalar_matrix)
        if mode == "matrix":
            return add_matrices(matrix, _normalize_matrix(value))
        raise PatchActionError(f"Unsupported mode for add: {mode}")
    raise PatchActionError(f"Unsupported operation: {operation}")


def _normalize_matrix(value: object) -> List[List[float]]:
    if not isinstance(value, list):
        raise PatchActionError("Matrix value must be a list.")
    matrix: List[List[float]] = []
    for row in value:
        if not isinstance(row, list):
            raise PatchActionError("Matrix rows must be lists.")
        matrix.append([float(item) for item in row])
    return matrix


def _matrix_to_tokens(
    matrix: Iterable[Iterable[float]],
    quoted: bool,
    array_format: Optional[ArrayFormat] = None,
) -> List[Token]:
    tokens: List[Token] = []
    matrix_list = [list(row) for row in matrix]
    has_escaped_newline = array_format.has_escaped_newline if array_format else False
    layout = array_format.layout if array_format else None
    for row_index, row in enumerate(matrix_list):
        if quoted:
            row_layout = None
            if layout is not None and row_index < len(layout):
                row_layout = layout[row_index]
            if row_layout and sum(row_layout) == len(row):
                position = 0
                for count in row_layout:
                    segment_values = ",".join(format(value, "g") for value in row[position : position + count])
                    tokens.append(Token(TokenType.STRING, segment_values, 0, 0))
                    position += count
            else:
                row_values = ",".join(format(value, "g") for value in row)
                tokens.append(Token(TokenType.STRING, row_values, 0, 0))
        else:
            last_index = len(row) - 1
            for value_index, value in enumerate(row):
                tokens.append(Token(TokenType.IDENTIFIER, format(value, "g"), 0, 0))
                if value_index < last_index:
                    tokens.append(Token(TokenType.COMMA, ",", 0, 0))
        if row_index < len(matrix_list) - 1 or has_escaped_newline:
            tokens.append(Token(TokenType.ESCAPED_NEWLINE, "\\\n", 0, 0))
    if tokens and tokens[-1].type == TokenType.ESCAPED_NEWLINE and not has_escaped_newline:
        tokens.pop()
    return tokens


def _array_uses_quotes(tokens: Iterable[Token]) -> bool:
    return any(token.type == TokenType.STRING for token in tokens)


def _iter_attribute_nodes(group: GroupNode, key: str) -> Iterable[tuple[GroupNode, AttributeNode]]:
    stack = [group]
    while stack:
        current = stack.pop()
        for child in current.children:
            if isinstance(child, AttributeNode) and child.key == key:
                yield current, child
            elif isinstance(child, GroupNode):
                stack.append(child)
