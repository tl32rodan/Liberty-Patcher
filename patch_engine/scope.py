from __future__ import annotations

from fnmatch import fnmatch
from typing import Iterable, List, Sequence, Union

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


def find_nodes_by_scope(root: RootNode, scope: dict) -> List[GroupNode]:
    path = scope.get("path", [])
    if not path:
        return []
    current: List[Union[RootNode, GroupNode]] = [root]
    for selector in path:
        current = _select_child_groups(current, selector)
        if not current:
            return []
    return [node for node in current if isinstance(node, GroupNode)]


def group_has_attribute(group: GroupNode, key: str, value_pattern: str) -> bool:
    for child in group.children:
        if isinstance(child, AttributeNode) and child.key == key:
            value = _tokens_to_value(child.raw_tokens)
            if fnmatch(value, value_pattern):
                return True
    return False


def _select_child_groups(
    nodes: Sequence[Union[RootNode, GroupNode]],
    selector: dict,
) -> List[GroupNode]:
    matched: List[GroupNode] = []
    for node in nodes:
        children = _iter_child_groups(node)
        for child in children:
            if _matches_selector(child, selector):
                matched.append(child)
    return matched


def _matches_selector(node: GroupNode, selector: dict) -> bool:
    group_pattern = selector.get("group")
    if group_pattern and not fnmatch(node.name, group_pattern):
        return False
    name_pattern = selector.get("name")
    if name_pattern and not _group_name_match(node, name_pattern):
        return False
    args_pattern = selector.get("args")
    if args_pattern and not _group_args_match(node, args_pattern):
        return False
    attributes = selector.get("attributes")
    if attributes and not _matches_attributes(node, attributes):
        return False
    return True


def _group_name_match(node: GroupNode, pattern: str) -> bool:
    if not node.args_tokens:
        return False
    return fnmatch(node.args_tokens[0].value, pattern)


def _group_args_match(node: GroupNode, patterns: Union[str, Iterable[str]]) -> bool:
    if not node.args_tokens:
        return False
    value = _tokens_to_value(node.args_tokens)
    if isinstance(patterns, str):
        patterns = [patterns]
    return any(fnmatch(value, pattern) for pattern in patterns)


def _matches_attributes(group: GroupNode, filters: dict) -> bool:
    for key, value in filters.items():
        if isinstance(value, list):
            if not any(group_has_attribute(group, key, pattern) for pattern in value):
                return False
            continue
        if not group_has_attribute(group, key, value):
            return False
    return True


def _iter_child_groups(node: Union[RootNode, GroupNode]) -> List[GroupNode]:
    if isinstance(node, RootNode):
        return [child for child in node.children if isinstance(child, GroupNode)]
    return [child for child in node.children if isinstance(child, GroupNode)]


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
