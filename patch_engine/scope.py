from __future__ import annotations

from fnmatch import fnmatch
from typing import List

from liberty_core.cst import GroupNode


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
