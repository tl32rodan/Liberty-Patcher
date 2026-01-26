from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

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
        if node.use_parens and self._is_array_tokens(node.raw_tokens):
            return self._format_array_attribute(node, indent)
        value = self._tokens_to_value(node.raw_tokens)
        if node.quote_style == QuoteStyle.DOUBLE:
            value = f"\"{value}\""
        if node.use_parens:
            return [f"{self._indent(indent)}{node.key} ({value});"]
        return [f"{self._indent(indent)}{node.key} : {value};"]

    def _format_array_attribute(self, node: AttributeNode, indent: int) -> List[str]:
        rows = self._parse_array_matrix(node.raw_tokens)
        formatted_rows = self._format_matrix_rows(rows)
        if len(formatted_rows) == 1:
            lines: List[str] = []
            header = f"{self._indent(indent)}{node.key} ( {formatted_rows[0]}"
            lines.append(header + ");")
            return lines

        lines = []
        header = f"{self._indent(indent)}{node.key} ( \\"
        lines.append(header)
        continuation_indent = f"{self._indent(indent + 1)}"
        last_index = len(formatted_rows) - 1
        for index, row in enumerate(formatted_rows):
            comma = "," if index < last_index else ""
            lines.append(f"{continuation_indent}{row}{comma} \\")
        lines.append(f"{self._indent(indent)});")
        return lines

    def _parse_array_matrix(self, tokens: List[Token]) -> List["ArrayRow"]:
        rows: List[ArrayRow] = []
        current_row: List[Token] = []
        for token in tokens:
            if token.type == TokenType.ESCAPED_NEWLINE:
                if current_row:
                    rows.append(self._parse_array_row(current_row))
                    current_row = []
                continue
            if token.type == TokenType.COMMENT:
                continue
            current_row.append(token)
        if current_row:
            rows.append(self._parse_array_row(current_row))
        return rows

    def _parse_array_row(self, tokens: List[Token]) -> "ArrayRow":
        values: List[float] = []
        has_string = False
        for token in tokens:
            if token.type in {TokenType.COMMENT, TokenType.ESCAPED_NEWLINE, TokenType.COMMA}:
                continue
            if token.type in {TokenType.STRING, TokenType.IDENTIFIER}:
                if token.type == TokenType.STRING:
                    has_string = True
                for part in token.value.split(","):
                    stripped = part.strip()
                    if stripped:
                        values.append(float(stripped))
        return ArrayRow(values=values, quoted=has_string)

    def _format_matrix_rows(self, rows: List["ArrayRow"]) -> List[str]:
        formatted = [[format(value, self.float_format) for value in row.values] for row in rows]
        col_widths = [max(len(row[col]) for row in formatted) for col in range(len(formatted[0]))]
        lines: List[str] = []
        for row_index, row in enumerate(formatted):
            cells = [row[col].rjust(col_widths[col]) for col in range(len(row))]
            line = ", ".join(cells)
            if rows[row_index].quoted:
                lines.append(f"\"{line}\"")
            else:
                lines.append(line)
        return lines

    def _is_array_tokens(self, tokens: Iterable[Token]) -> bool:
        has_separator = False
        for token in tokens:
            if token.type in {TokenType.COMMENT, TokenType.ESCAPED_NEWLINE}:
                if token.type == TokenType.ESCAPED_NEWLINE:
                    has_separator = True
                continue
            if token.type == TokenType.COMMA:
                has_separator = True
                continue
            if token.type not in {TokenType.STRING, TokenType.IDENTIFIER}:
                return False
            if not self._token_is_numeric(token.value):
                return False
        return has_separator

    def _token_is_numeric(self, value: str) -> bool:
        has_value = False
        for part in value.split(","):
            stripped = part.strip()
            if not stripped:
                continue
            has_value = True
            try:
                float(stripped)
            except ValueError:
                return False
        return has_value

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


@dataclass(frozen=True)
class ArrayRow:
    values: List[float]
    quoted: bool
