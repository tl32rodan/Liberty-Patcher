import unittest

from liberty_core import Lexer, LexerError, TokenType


class TestLexer(unittest.TestCase):
    def test_lexes_identifiers_and_numbers(self) -> None:
        tokens = Lexer("area : 5.2;").tokenize()
        types = [token.type for token in tokens]
        self.assertEqual(
            types,
            [TokenType.IDENTIFIER, TokenType.COLON, TokenType.IDENTIFIER, TokenType.SEMI],
        )

    def test_lexes_quoted_strings(self) -> None:
        tokens = Lexer('time_unit : "1ns";').tokenize()
        types = [token.type for token in tokens]
        self.assertEqual(
            types,
            [TokenType.IDENTIFIER, TokenType.COLON, TokenType.STRING, TokenType.SEMI],
        )

    def test_lexes_comments_and_escaped_newline(self) -> None:
        text = 'values : "1,2" \\\n "3,4"; // trailing'
        tokens = Lexer(text).tokenize()
        token_types = [token.type for token in tokens]
        self.assertIn(TokenType.ESCAPED_NEWLINE, token_types)
        self.assertIn(TokenType.COMMENT, token_types)

    def test_lexes_block_comments(self) -> None:
        tokens = Lexer("/* comment */ cell(A) { }").tokenize()
        self.assertEqual(tokens[0].type, TokenType.COMMENT)

    def test_unterminated_string_raises(self) -> None:
        with self.assertRaises(LexerError):
            Lexer('time_unit : "1ns;').tokenize()

    def test_unterminated_comment_raises(self) -> None:
        with self.assertRaises(LexerError):
            Lexer("/* comment").tokenize()
