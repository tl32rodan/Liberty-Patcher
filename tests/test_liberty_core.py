import unittest

from liberty_core import Formatter, Lexer, Parser, QuoteStyle
from liberty_core.cst import TokenType


class TestLibertyCore(unittest.TestCase):
    def test_lexer_emits_escaped_newline(self) -> None:
        text = 'values ( "1,2" \\\n "3,4" );'
        tokens = Lexer(text).tokenize()
        token_types = [token.type for token in tokens]
        self.assertIn(TokenType.ESCAPED_NEWLINE, token_types)

    def test_parser_quote_style(self) -> None:
        text = 'cell(A) { area : "5"; size : 7; }'
        result = Parser().parse(text)
        cell = result.root.children[0]
        area = cell.children[0]
        size = cell.children[1]
        self.assertEqual(area.quote_style, QuoteStyle.DOUBLE)
        self.assertEqual(size.quote_style, QuoteStyle.NONE)

    def test_formatter_values_alignment(self) -> None:
        text = (
            'cell(A) {\n'
            '  index_1 : "0.1, 0.2";\n'
            '  index_2 : "1, 2";\n'
            '  values ( "1,2" \\\n "3,4" );\n'
            '}\n'
        )
        result = Parser().parse(text)
        output = Formatter().dump(result.root)
        self.assertIn('values ( "1, 2" \\', output)
        self.assertIn('"3, 4");', output)
