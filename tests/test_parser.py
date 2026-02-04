import unittest

from liberty_core import Parser, ParserError


class TestParser(unittest.TestCase):
    def test_parses_group_and_attribute(self) -> None:
        text = "library(foo) { time_unit : 1ns; }"
        result = Parser().parse(text)
        self.assertEqual(len(result.root.children), 1)
        library = result.root.children[0]
        self.assertEqual(library.name, "library")
        self.assertEqual(result.context.time_unit, "1ns")

    def test_parses_nested_groups(self) -> None:
        text = "library(foo) { cell(A) { area : 5; } }"
        result = Parser().parse(text)
        library = result.root.children[0]
        cell = library.children[0]
        self.assertEqual(cell.name, "cell")

    def test_unexpected_token_raises(self) -> None:
        with self.assertRaises(ParserError):
            Parser().parse(": 1;")

    def test_parses_attribute_without_semicolon(self) -> None:
        text = "library(foo) {\n  default_max_transition : 253.300000\n  cell(A) { area : 5; }\n}"
        result = Parser().parse(text)
        library = result.root.children[0]
        attribute = library.children[0]
        self.assertEqual(attribute.key, "default_max_transition")
        self.assertEqual("253.300000", "".join(token.value for token in attribute.raw_tokens))

    def test_parses_parenthesized_attribute_without_semicolon(self) -> None:
        text = "library(foo) {\n  fanout_length(1,0.0000)\n  cell(A) { area : 5; }\n}"
        result = Parser().parse(text)
        library = result.root.children[0]
        attribute = library.children[0]
        self.assertEqual(attribute.key, "fanout_length")
        self.assertTrue(attribute.use_parens)
