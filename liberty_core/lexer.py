from __future__ import annotations

from typing import List

from .cst import Token, TokenType


class LexerError(ValueError):
    pass


class Lexer:
    def __init__(self, text: str) -> None:
        self.text = text
        self.length = len(text)
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while self.index < self.length:
            char = self.text[self.index]
            if char == "\\" and self._peek(1) == "\n":
                tokens.append(self._make_token(TokenType.ESCAPED_NEWLINE, "\\\n"))
                self._advance(2)
                self._newline()
                continue
            if char.isspace():
                self._advance_whitespace(char)
                continue
            if char == "/" and self._peek(1) == "/":
                tokens.append(self._read_line_comment())
                continue
            if char == "/" and self._peek(1) == "*":
                tokens.append(self._read_block_comment())
                continue
            if char == "\"":
                tokens.append(self._read_string())
                continue
            token = self._match_symbol(char)
            if token:
                tokens.append(token)
                self._advance(1)
                continue
            if self._is_identifier_start(char):
                tokens.append(self._read_identifier())
                continue
            raise LexerError(f"Unexpected character {char!r} at {self.line}:{self.column}")
        return tokens

    def _match_symbol(self, char: str) -> Token | None:
        mapping = {
            "(": TokenType.GROUP_START,
            ")": TokenType.GROUP_END,
            "{": TokenType.BLOCK_START,
            "}": TokenType.BLOCK_END,
            ":": TokenType.COLON,
            ";": TokenType.SEMI,
            ",": TokenType.COMMA,
        }
        token_type = mapping.get(char)
        if token_type is None:
            return None
        return self._make_token(token_type, char)

    def _read_string(self) -> Token:
        start_line = self.line
        start_column = self.column
        self._advance(1)
        value_chars = []
        while self.index < self.length:
            char = self.text[self.index]
            if char == "\\" and self._peek(1) == "\n":
                value_chars.append("\\\n")
                self._advance(2)
                self._newline()
                continue
            if char == "\\" and self._peek(1) in {'"', "\\"}:
                value_chars.append(self._peek(1))
                self._advance(2)
                continue
            if char == "\"":
                self._advance(1)
                return Token(TokenType.STRING, "".join(value_chars), start_line, start_column)
            if char == "\n":
                self._newline()
                value_chars.append("\n")
                self._advance(1)
                continue
            value_chars.append(char)
            self._advance(1)
        raise LexerError(f"Unterminated string starting at {start_line}:{start_column}")

    def _read_line_comment(self) -> Token:
        start_line = self.line
        start_column = self.column
        self._advance(2)
        value_chars = ["//"]
        while self.index < self.length:
            char = self.text[self.index]
            if char == "\n":
                break
            value_chars.append(char)
            self._advance(1)
        return Token(TokenType.COMMENT, "".join(value_chars), start_line, start_column)

    def _read_block_comment(self) -> Token:
        start_line = self.line
        start_column = self.column
        self._advance(2)
        value_chars = ["/*"]
        while self.index < self.length:
            char = self.text[self.index]
            if char == "*" and self._peek(1) == "/":
                value_chars.append("*/")
                self._advance(2)
                return Token(TokenType.COMMENT, "".join(value_chars), start_line, start_column)
            if char == "\n":
                self._newline()
                value_chars.append("\n")
                self._advance(1)
                continue
            value_chars.append(char)
            self._advance(1)
        raise LexerError(f"Unterminated comment starting at {start_line}:{start_column}")

    def _read_identifier(self) -> Token:
        start_line = self.line
        start_column = self.column
        value_chars = []
        while self.index < self.length:
            char = self.text[self.index]
            if self._is_identifier_part(char):
                value_chars.append(char)
                self._advance(1)
                continue
            break
        return Token(TokenType.IDENTIFIER, "".join(value_chars), start_line, start_column)

    def _is_identifier_start(self, char: str) -> bool:
        return not char.isspace() and char not in "(){}:;,\"/"

    def _is_identifier_part(self, char: str) -> bool:
        return self._is_identifier_start(char)

    def _advance_whitespace(self, char: str) -> None:
        if char == "\n":
            self._newline()
        self._advance(1)

    def _advance(self, count: int) -> None:
        self.index += count
        self.column += count

    def _newline(self) -> None:
        self.line += 1
        self.column = 1

    def _peek(self, offset: int) -> str:
        position = self.index + offset
        if position >= self.length:
            return ""
        return self.text[position]

    def _make_token(self, token_type: TokenType, value: str) -> Token:
        return Token(token_type, value, self.line, self.column)
