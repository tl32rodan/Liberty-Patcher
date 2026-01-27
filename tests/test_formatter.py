import unittest

from liberty_core import Formatter, Parser


class TestFormatter(unittest.TestCase):
    def test_formatter_preserves_quote_style_for_simple_values(self) -> None:
        text = 'cell(A) { area : "5"; size : 7; }'
        result = Parser().parse(text)
        output = Formatter().dump(result.root)
        self.assertIn("cell (A) {", output)
        self.assertIn('area : "5";', output)
        self.assertIn("size : 7;", output)

    def test_formatter_enforces_quotes_for_values_table(self) -> None:
        text = (
            "cell(A) {\n"
            "  index_1 : 0.1, 0.2;\n"
            "  index_2 : 1, 2;\n"
            "  values ( \"1,2\" \\\n"
            "           \"3,4\" );\n"
            "}\n"
        )
        result = Parser().parse(text)
        output = Formatter().dump(result.root)
        self.assertIn("values ( \\", output)
        self.assertIn('    "1, 2", \\', output)
        self.assertIn('    "3, 4" \\', output)
        self.assertIn(");", output)

    def test_formatter_keeps_single_row_values_inline(self) -> None:
        text = (
            "cell(A) {\n"
            "  index_1 : 0.1, 0.2, 0.3;\n"
            "  values ( 1,2,3 );\n"
            "}\n"
        )
        result = Parser().parse(text)
        output = Formatter().dump(result.root)
        self.assertIn("values (1, 2, 3);", output)

    def test_formatter_keeps_single_row_values_multiline_with_newlines(self) -> None:
        text = (
            "cell(A) {\n"
            "  values ( \\\n"
            "    \"0, 1\" \\\n"
            "  );\n"
            "}\n"
        )
        result = Parser().parse(text)
        output = Formatter().dump(result.root)
        self.assertIn("values ( \\", output)
        self.assertIn('    "0, 1" \\', output)
        self.assertIn(");", output)

    def test_formatter_applies_array_formatting_without_key(self) -> None:
        text = (
            "cell(A) {\n"
            "  foo ( 1,2 );\n"
            "}\n"
        )
        result = Parser().parse(text)
        output = Formatter().dump(result.root)
        self.assertIn("foo (1, 2);", output)

    def test_formatter_preserves_unquoted_arrays(self) -> None:
        text = (
            "cell(A) {\n"
            "  rise_capacitance_range (0.276893, 0.440626);\n"
            "}\n"
        )
        result = Parser().parse(text)
        output = Formatter().dump(result.root)
        self.assertIn("rise_capacitance_range (0.276893, 0.440626);", output)

    def test_formatter_adds_space_before_group_paren(self) -> None:
        text = (
            "timing () {\n"
            "}\n"
        )
        result = Parser().parse(text)
        output = Formatter().dump(result.root)
        self.assertIn("timing () {", output)
