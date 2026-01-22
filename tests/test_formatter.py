import unittest

from liberty_core import Formatter, Parser


class TestFormatter(unittest.TestCase):
    def test_formatter_preserves_quote_style_for_simple_values(self) -> None:
        text = 'cell(A) { area : "5"; size : 7; }'
        result = Parser().parse(text)
        output = Formatter().dump(result.root)
        self.assertIn('area : "5";', output)
        self.assertIn("size : 7;", output)

    def test_formatter_enforces_quotes_for_values_table(self) -> None:
        text = (
            "cell(A) {\n"
            "  index_1 : 0.1, 0.2;\n"
            "  index_2 : 1, 2;\n"
            "  values : 1,2,3,4;\n"
            "}\n"
        )
        result = Parser().parse(text)
        output = Formatter().dump(result.root)
        self.assertIn('values : "1, 2" \\', output)
        self.assertIn('"3, 4";', output)
