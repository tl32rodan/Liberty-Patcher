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
