from __future__ import annotations

from fnmatch import fnmatch
from typing import Iterable, List, Optional

from liberty_core.cst import AttributeNode, GroupNode, RootNode, Token, TokenType


def find_groups_by_name(root: GroupNode, group_name: str) -> List[GroupNode]:
    matches: List[GroupNode] = []
    nodes = [root]
    while nodes:
        node = nodes.pop()
        if node.name == group_name:
            matches.append(node)
        for child in node.children:
            if isinstance(child, GroupNode):
                nodes.append(child)
    return matches


def filter_cells_by_pattern(library_group: GroupNode, patterns: List[str]) -> List[GroupNode]:
    cells = [child for child in library_group.children if isinstance(child, GroupNode) and child.name == "cell"]
    matched: List[GroupNode] = []
    for cell in cells:
        if not cell.args_tokens:
            continue
        cell_name = cell.args_tokens[0].value
        if any(fnmatch(cell_name, pattern) for pattern in patterns):
            matched.append(cell)
    return matched


def find_nodes_by_scope(root: RootNode, scope: dict) -> List[GroupNode]:
    library_group = _find_library_group(root)
    if library_group is None:
        return []
    cell_patterns = scope.get("cells")
    if cell_patterns:
        cells = filter_cells_by_pattern(library_group, cell_patterns)
    else:
        cells = [
            child
            for child in library_group.children
            if isinstance(child, GroupNode) and child.name == "cell"
        ]
    pin_patterns = scope.get("pins")
    metric = scope.get("metric")
    direction = scope.get("direction")
    attribute_filters = {
        key: value
        for key, value in scope.items()
        if key not in {"cells", "pins", "metric", "direction"} and value is not None
    }
    matched_groups: List[GroupNode] = []
    for cell in cells:
        pins = _find_child_groups(cell, "pin")
        if pin_patterns:
            pins = [pin for pin in pins if _group_args_match(pin, pin_patterns)]
        for pin in pins:
            groups = [child for child in pin.children if isinstance(child, GroupNode)]
            if metric:
                groups = [group for group in groups if group.name == metric]
            for group in groups:
                if direction and not _matches_direction(group, direction):
                    continue
                if attribute_filters and not _matches_attributes(group, attribute_filters):
                    continue
                matched_groups.append(group)
    return matched_groups


def group_has_attribute(group: GroupNode, key: str, value_pattern: str) -> bool:
    for child in group.children:
        if isinstance(child, AttributeNode) and child.key == key:
            value = _tokens_to_value(child.raw_tokens)
            if fnmatch(value, value_pattern):
                return True
    return False


def _find_library_group(root: RootNode) -> Optional[GroupNode]:
    for child in root.children:
        if isinstance(child, GroupNode) and child.name == "library":
            return child
    return None


def _find_child_groups(node: GroupNode, name: str) -> List[GroupNode]:
    return [child for child in node.children if isinstance(child, GroupNode) and child.name == name]


def _group_args_match(node: GroupNode, patterns: Iterable[str]) -> bool:
    if not node.args_tokens:
        return False
    value = node.args_tokens[0].value
    return any(fnmatch(value, pattern) for pattern in patterns)


def _matches_direction(group: GroupNode, direction: str) -> bool:
    pattern = f"*{direction}*"
    return any(
        group_has_attribute(group, key, pattern)
        for key in ("timing_type", "timing_sense", "related_pin")
    )


def _matches_attributes(group: GroupNode, filters: dict) -> bool:
    for key, value in filters.items():
        if isinstance(value, list):
            if not any(group_has_attribute(group, key, pattern) for pattern in value):
                return False
            continue
        if not group_has_attribute(group, key, value):
            return False
    return True


def _tokens_to_value(tokens: Iterable[Token]) -> str:
    pieces: List[str] = []
    for token in tokens:
        if token.type in {TokenType.COMMENT, TokenType.ESCAPED_NEWLINE}:
            continue
        if token.type == TokenType.STRING:
            pieces.append(token.value)
        elif token.type == TokenType.IDENTIFIER:
            pieces.append(token.value)
        elif token.type == TokenType.COMMA:
            pieces.append(",")
    value = ""
    for part in pieces:
        if part == ",":
            value = value.rstrip() + ","
        else:
            value = f"{value} {part}".strip()
    return value
