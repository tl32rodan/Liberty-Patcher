from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .cst import (
    AttributeNode,
    CommentNode,
    GroupNode,
    LibraryContext,
    QuoteStyle,
    RootNode,
    Token,
    TokenType,
)
from .lexer import Lexer


class ParserError(ValueError):
    pass


@dataclass
class ParseResult:
    root: RootNode
    context: LibraryContext


class Parser:
    def __init__(self) -> None:
        self.tokens: List[Token] = []
        self.index = 0

    def parse(self, text: str) -> ParseResult:
        self.tokens = Lexer(text).tokenize()
        self.index = 0
        root = RootNode()
        while not self._is_at_end():
            node = self._parse_node()
            if node is not None:
                root.add_child(node)
        context = self._extract_context(root)
        return ParseResult(root=root, context=context)

    def _parse_node(self) -> Optional[object]:
        token = self._peek()
        if token is None:
            return None
        if token.type == TokenType.COMMENT:
            self._advance()
            return CommentNode(text=token.value)
        if token.type == TokenType.IDENTIFIER:
            if self._is_group_start():
                return self._parse_group()
            if self._is_attribute_start():
                return self._parse_attribute()
        raise ParserError(f"Unexpected token {token.type} at {token.line}:{token.column}")

    def _parse_group(self) -> GroupNode:
        name_token = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.GROUP_START)
        args_tokens = self._collect_until(TokenType.GROUP_END)
        self._expect(TokenType.GROUP_END)
        self._expect(TokenType.BLOCK_START)
        group = GroupNode(name=name_token.value, args_tokens=args_tokens)
        while not self._check(TokenType.BLOCK_END):
            node = self._parse_node()
            if node is not None:
                group.add_child(node)
        self._expect(TokenType.BLOCK_END)
        return group

    def _parse_attribute(self) -> AttributeNode:
        key_token = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.COLON)
        raw_tokens = self._collect_until(TokenType.SEMI)
        self._expect(TokenType.SEMI)
        quote_style = QuoteStyle.NONE
        for token in raw_tokens:
            if token.type == TokenType.STRING:
                quote_style = QuoteStyle.DOUBLE
                break
            if token.type in {TokenType.IDENTIFIER, TokenType.COMMA}:
                break
        return AttributeNode(key=key_token.value, raw_tokens=raw_tokens, quote_style=quote_style)

    def _collect_until(self, token_type: TokenType) -> List[Token]:
        collected: List[Token] = []
        while not self._check(token_type):
            token = self._peek()
            if token is None:
                raise ParserError(f"Unexpected end of input, expected {token_type}")
            collected.append(token)
            self._advance()
        return collected

    def _extract_context(self, root: RootNode) -> LibraryContext:
        context = LibraryContext()
        library_group = next(
            (child for child in root.children if isinstance(child, GroupNode) and child.name == "library"),
            None,
        )
        if library_group is None:
            return context
        for child in library_group.children:
            if not isinstance(child, AttributeNode):
                continue
            if child.key == "time_unit":
                context.time_unit = self._tokens_to_value(child.raw_tokens)
            if child.key == "voltage_unit":
                context.voltage_unit = self._tokens_to_value(child.raw_tokens)
            if child.key == "leakage_power_unit":
                context.leakage_power_unit = self._tokens_to_value(child.raw_tokens)
        return context

    def _tokens_to_value(self, tokens: List[Token]) -> str:
        parts = []
        for token in tokens:
            if token.type == TokenType.STRING:
                parts.append(token.value)
            elif token.type == TokenType.IDENTIFIER:
                parts.append(token.value)
            elif token.type == TokenType.COMMA:
                parts.append(",")
        value = " ".join(parts).strip()
        return value

    def _is_group_start(self) -> bool:
        return self._peek_type(1) == TokenType.GROUP_START

    def _is_attribute_start(self) -> bool:
        return self._peek_type(1) == TokenType.COLON

    def _expect(self, token_type: TokenType) -> Token:
        token = self._peek()
        if token is None or token.type != token_type:
            location = "end of input" if token is None else f"{token.line}:{token.column}"
            raise ParserError(f"Expected {token_type} at {location}")
        self._advance()
        return token

    def _check(self, token_type: TokenType) -> bool:
        token = self._peek()
        return token is not None and token.type == token_type

    def _peek(self) -> Optional[Token]:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def _peek_type(self, offset: int) -> Optional[TokenType]:
        position = self.index + offset
        if position >= len(self.tokens):
            return None
        return self.tokens[position].type

    def _advance(self) -> None:
        self.index += 1

    def _is_at_end(self) -> bool:
        return self.index >= len(self.tokens)
