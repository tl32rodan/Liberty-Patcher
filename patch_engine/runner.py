from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, List, Optional
from uuid import uuid4

from liberty_core.cst import AttributeNode, GroupNode, Token, TokenType
from liberty_core.parser import ParseResult
from provenance import ArtifactRecord, BatchOp, ProvenanceDB

from .matrix import add_matrices, multiply_matrix, parse_values_tokens
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
            groups = find_nodes_by_scope(parse_result.root, scope)
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
        for owner, node in _iter_attribute_nodes(group, attribute):
            rows, cols = _resolve_matrix_shape(owner, node.raw_tokens)
            matrix = parse_values_tokens(node.raw_tokens, rows, cols)
            updated = _apply_operation(matrix, action)
            node.raw_tokens = _matrix_to_tokens(updated)


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


def _resolve_matrix_shape(group: GroupNode, values_tokens: Iterable[Token]) -> tuple[int, int]:
    index_1 = _find_index_values(group, "index_1")
    index_2 = _find_index_values(group, "index_2")
    if index_1 and index_2:
        return len(index_1), len(index_2)
    if index_1:
        return 1, len(index_1)
    flat_values = _parse_index_tokens(values_tokens)
    return 1, len(flat_values)


def _find_index_values(group: GroupNode, key: str) -> Optional[List[float]]:
    for child in group.children:
        if isinstance(child, AttributeNode) and child.key == key:
            return _parse_index_tokens(child.raw_tokens)
    return None


def _parse_index_tokens(tokens: Iterable[Token]) -> List[float]:
    values: List[float] = []
    for token in tokens:
        if token.type in {TokenType.COMMENT, TokenType.ESCAPED_NEWLINE}:
            continue
        if token.type in {TokenType.STRING, TokenType.IDENTIFIER}:
            for part in token.value.split(","):
                stripped = part.strip()
                if stripped:
                    values.append(float(stripped))
    return values


def _normalize_matrix(value: object) -> List[List[float]]:
    if not isinstance(value, list):
        raise PatchActionError("Matrix value must be a list.")
    matrix: List[List[float]] = []
    for row in value:
        if not isinstance(row, list):
            raise PatchActionError("Matrix rows must be lists.")
        matrix.append([float(item) for item in row])
    return matrix


def _matrix_to_tokens(matrix: Iterable[Iterable[float]]) -> List[Token]:
    tokens: List[Token] = []
    for row in matrix:
        row_values = ",".join(format(value, "g") for value in row)
        tokens.append(Token(TokenType.STRING, row_values, 0, 0))
    return tokens


def _iter_attribute_nodes(group: GroupNode, key: str) -> Iterable[tuple[GroupNode, AttributeNode]]:
    stack = [group]
    while stack:
        current = stack.pop()
        for child in current.children:
            if isinstance(child, AttributeNode) and child.key == key:
                yield current, child
            elif isinstance(child, GroupNode):
                stack.append(child)
