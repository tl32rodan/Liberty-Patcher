from __future__ import annotations

from typing import Iterable, List, Optional

from .cst import AttributeNode, CommentNode, GroupNode, QuoteStyle, RootNode, Token, TokenType


class Formatter:
    def __init__(self, indent_size: int = 2, float_format: str = "g") -> None:
        self.indent_size = indent_size
        self.float_format = float_format

    def dump(self, root: RootNode) -> str:
        lines: List[str] = []
        for child in root.children:
            lines.extend(self._format_node(child, 0))
        return "\n".join(lines) + "\n"

    def _format_node(self, node: object, indent: int) -> List[str]:
        if isinstance(node, CommentNode):
            return [self._indent(indent) + node.text]
        if isinstance(node, GroupNode):
            return self._format_group(node, indent)
        if isinstance(node, AttributeNode):
            return self._format_attribute(node, indent)
        return []

    def _format_group(self, node: GroupNode, indent: int) -> List[str]:
        lines: List[str] = []
        args = self._tokens_to_value(node.args_tokens)
        lines.append(f"{self._indent(indent)}{node.name}({args}) {{")
        for child in node.children:
            lines.extend(self._format_node(child, indent + 1))
        lines.append(f"{self._indent(indent)}}}")
        return lines

    def _format_attribute(self, node: AttributeNode, indent: int) -> List[str]:
        if node.key == "values":
            return self._format_values_attribute(node, indent)
        value = self._tokens_to_value(node.raw_tokens)
        if node.quote_style == QuoteStyle.DOUBLE:
            value = f"\"{value}\""
        return [f"{self._indent(indent)}{node.key} : {value};"]

    def _format_values_attribute(self, node: AttributeNode, indent: int) -> List[str]:
        group = node.parent if isinstance(node.parent, GroupNode) else None
        index_1 = self._find_index_values(group, "index_1")
        index_2 = self._find_index_values(group, "index_2")
        rows, cols = self._resolve_matrix_shape(index_1, index_2, node.raw_tokens)
        matrix = self._parse_values(node.raw_tokens, rows, cols)
        formatted_rows = self._align_matrix(matrix)
        lines: List[str] = []
        header = f"{self._indent(indent)}{node.key} : {formatted_rows[0]}"
        lines.append(header)
        for row in formatted_rows[1:]:
            lines.append(f"{self._indent(indent)}{' ' * (len(node.key) + 3)}{row}")
        lines[-1] = lines[-1] + ";"
        return lines

    def _parse_values(self, tokens: List[Token], rows: int, cols: int) -> List[List[float]]:
        flat: List[float] = []
        for token in tokens:
            if token.type in {TokenType.COMMENT, TokenType.ESCAPED_NEWLINE}:
                continue
            if token.type in {TokenType.STRING, TokenType.IDENTIFIER}:
                for part in token.value.split(","):
                    stripped = part.strip()
                    if stripped:
                        flat.append(float(stripped))
                continue
            if token.type == TokenType.COMMA:
                continue
        expected = rows * cols
        if expected != len(flat):
            raise ValueError(f"Values count {len(flat)} does not match expected shape {rows}x{cols}")
        return [flat[row * cols : (row + 1) * cols] for row in range(rows)]

    def _align_matrix(self, matrix: List[List[float]]) -> List[str]:
        formatted = [[format(value, self.float_format) for value in row] for row in matrix]
        col_widths = [max(len(row[col]) for row in formatted) for col in range(len(formatted[0]))]
        lines: List[str] = []
        for row_index, row in enumerate(formatted):
            cells = [row[col].rjust(col_widths[col]) for col in range(len(row))]
            line = ", ".join(cells)
            if row_index < len(formatted) - 1:
                lines.append(f"\"{line}\" \\")
            else:
                lines.append(f"\"{line}\"")
        return lines

    def _find_index_values(self, group: Optional[GroupNode], key: str) -> Optional[List[float]]:
        if group is None:
            return None
        for child in group.children:
            if isinstance(child, AttributeNode) and child.key == key:
                return self._parse_index(child.raw_tokens)
        return None

    def _parse_index(self, tokens: List[Token]) -> List[float]:
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

    def _resolve_matrix_shape(
        self,
        index_1: Optional[List[float]],
        index_2: Optional[List[float]],
        tokens: List[Token],
    ) -> tuple[int, int]:
        if index_1 and index_2:
            return len(index_1), len(index_2)
        if index_1:
            return 1, len(index_1)
        flat_count = len(self._parse_index(tokens))
        return 1, flat_count

    def _tokens_to_value(self, tokens: Iterable[Token]) -> str:
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

    def _indent(self, indent: int) -> str:
        return " " * (indent * self.indent_size)
