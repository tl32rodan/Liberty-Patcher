import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Iterable, List, Optional

from liberty_core import Formatter, Parser
from liberty_core.cst import AttributeNode, GroupNode, RootNode
from patch_engine import PatchRunner, find_nodes_by_scope, parse_array_tokens
from provenance import ProvenanceDB


class TestPatchRunnerE2E(unittest.TestCase):
    def test_patch_runner_e2e(self) -> None:
        input_path = Path("examples/asap7sc6t_SIMPLE_SLVT_TT_nldm_211010.lib")
        text = input_path.read_text(encoding="utf-8")
        parse_result = Parser().parse(text)

        cell_name = "AND2x2_ASAP7_6t_SL"
        cell_group = _find_cell_group(parse_result.root, cell_name)
        self.assertIsNotNone(cell_group)

        before_matrix = _extract_first_timing_matrix(parse_result.root, cell_name)
        self.assertIsNotNone(before_matrix)

        config = {
            "modifications": [
                {
                    "scope": {
                        "path": [
                            {"group": "library"},
                            {"group": "cell", "name": "AND*"},
                            {"group": "pin", "name": "*"},
                            {"group": "timing"},
                        ]
                    },
                    "action": {"operation": "multiply", "mode": "broadcast", "value": 1.1},
                }
            ]
        }

        with tempfile.NamedTemporaryFile() as tmp:
            db = ProvenanceDB(tmp.name)
            runner = PatchRunner(provenance_db=db)
            runner.run(parse_result, config)
            output_text = Formatter(indent_size=2).dump(parse_result.root)
            runner.log_run(config, "e2e timing scale", text, output_text, "patched.lib")

            after_matrix = _extract_first_timing_matrix(parse_result.root, cell_name)
            self.assertIsNotNone(after_matrix)
            _assert_scaled_matrix(self, before_matrix, after_matrix, 1.1)

            Parser().parse(output_text)

            with sqlite3.connect(tmp.name) as conn:
                batch_count = conn.execute("SELECT COUNT(*) FROM batch_ops").fetchone()[0]
                artifact_count = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
            self.assertEqual(batch_count, 1)
            self.assertEqual(artifact_count, 1)

    def test_internal_power_when_related_pg_pin_patch(self) -> None:
        input_path = Path("examples/asap7sc6t_SIMPLE_SLVT_TT_nldm_211010.lib")
        text = input_path.read_text(encoding="utf-8")
        parse_result = Parser().parse(text)

        before_matrix = _extract_internal_power_fall_matrix(
            parse_result.root,
            cell_name="AND3x1_ASAP7_6t_SL",
            pin_name="A",
            when="(B * !C * !Y)",
            related_pg_pin="VDD",
        )
        self.assertIsNotNone(before_matrix)

        config = {
            "modifications": [
                {
                    "scope": {
                        "path": [
                            {"group": "library"},
                            {"group": "cell", "name": "AND3x1_ASAP7_6t_SL"},
                            {"group": "pin", "name": "A"},
                            {
                                "group": "internal_power",
                                "attributes": {"when": "(B * !C * !Y)", "related_pg_pin": "VDD"},
                            },
                            {"group": "fall_power"},
                        ]
                    },
                    "action": {"operation": "add", "mode": "broadcast", "value": 0.01},
                }
            ]
        }

        runner = PatchRunner()
        runner.run(parse_result, config)

        after_matrix = _extract_internal_power_fall_matrix(
            parse_result.root,
            cell_name="AND3x1_ASAP7_6t_SL",
            pin_name="A",
            when="(B * !C * !Y)",
            related_pg_pin="VDD",
        )
        self.assertIsNotNone(after_matrix)
        _assert_offset_matrix(self, before_matrix, after_matrix, 0.01)


def _find_cell_group(root: RootNode, cell_name: str) -> Optional[GroupNode]:
    for child in root.children:
        if isinstance(child, GroupNode) and child.name == "library":
            for cell in child.children:
                if isinstance(cell, GroupNode) and cell.name == "cell" and cell.args_tokens:
                    if cell.args_tokens[0].value == cell_name:
                        return cell
    return None


def _extract_first_timing_matrix(root: RootNode, cell_name: str) -> Optional[List[List[float]]]:
    timing_groups = find_nodes_by_scope(
        root,
        {
            "path": [
                {"group": "library"},
                {"group": "cell", "name": cell_name},
                {"group": "pin", "name": "*"},
                {"group": "timing"},
            ]
        },
    )
    for group in timing_groups:
        for owner, values_attr in _iter_attribute_nodes(group, "values"):
            return parse_array_tokens(values_attr.raw_tokens)
    return None


def _assert_scaled_matrix(
    test_case: unittest.TestCase,
    before: List[List[float]],
    after: List[List[float]],
    scale: float,
) -> None:
    test_case.assertEqual(len(before), len(after))
    for before_row, after_row in zip(before, after):
        test_case.assertEqual(len(before_row), len(after_row))
        for before_value, after_value in zip(before_row, after_row):
            test_case.assertAlmostEqual(after_value, before_value * scale, places=3)


def _assert_offset_matrix(
    test_case: unittest.TestCase,
    before: List[List[float]],
    after: List[List[float]],
    offset: float,
) -> None:
    test_case.assertEqual(len(before), len(after))
    for before_row, after_row in zip(before, after):
        test_case.assertEqual(len(before_row), len(after_row))
        for before_value, after_value in zip(before_row, after_row):
            test_case.assertAlmostEqual(after_value, before_value + offset, places=3)


def _extract_internal_power_fall_matrix(
    root: RootNode,
    cell_name: str,
    pin_name: str,
    when: str,
    related_pg_pin: str,
) -> Optional[List[List[float]]]:
    fall_groups = find_nodes_by_scope(
        root,
        {
            "path": [
                {"group": "library"},
                {"group": "cell", "name": cell_name},
                {"group": "pin", "name": pin_name},
                {"group": "internal_power", "attributes": {"when": when, "related_pg_pin": related_pg_pin}},
                {"group": "fall_power"},
            ]
        },
    )
    for group in fall_groups:
        for _, values_attr in _iter_attribute_nodes(group, "values"):
            return parse_array_tokens(values_attr.raw_tokens)
    return None


def _iter_attribute_nodes(group: GroupNode, key: str) -> Iterable[tuple[GroupNode, AttributeNode]]:
    stack = [group]
    while stack:
        current = stack.pop()
        for child in current.children:
            if isinstance(child, AttributeNode) and child.key == key:
                yield current, child
            elif isinstance(child, GroupNode):
                stack.append(child)
