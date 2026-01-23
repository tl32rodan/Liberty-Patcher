from __future__ import annotations

import argparse
import json
from pathlib import Path

import config_compiler
from liberty_core import Formatter, Parser
from patch_engine import PatchRunner
from provenance import ProvenanceDB


def _read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Liberty format and patch CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    format_parser = subparsers.add_parser("format", help="Normalize a Liberty file.")
    format_parser.add_argument("--input", required=True, help="Input Liberty file.")
    format_parser.add_argument("--output", required=True, help="Output Liberty file.")
    format_parser.add_argument("--indent-size", type=int, default=2, help="Formatter indentation size.")

    patch_parser = subparsers.add_parser("patch", help="Apply a patch configuration.")
    patch_parser.add_argument("--input", required=True, help="Input Liberty file.")
    patch_parser.add_argument("--config", required=True, help="Patch config JSON file.")
    patch_parser.add_argument("--output", required=True, help="Output Liberty file.")
    patch_parser.add_argument("--description", default="", help="Patch description.")
    patch_parser.add_argument("--indent-size", type=int, default=2, help="Formatter indentation size.")
    patch_parser.add_argument("--db", default="provenance.db", help="Provenance SQLite DB path.")

    return parser


def _handle_format(args: argparse.Namespace) -> int:
    text = _read_text(args.input)
    parse_result = Parser().parse(text)
    output_text = Formatter(indent_size=args.indent_size).dump(parse_result.root)
    _write_text(args.output, output_text)
    return 0


def _handle_patch(args: argparse.Namespace) -> int:
    text = _read_text(args.input)
    parse_result = Parser().parse(text)
    config = _load_config(args.config)
    provenance_db = ProvenanceDB(args.db) if args.db else None
    runner = PatchRunner(provenance_db=provenance_db)
    runner.run(parse_result, config)
    output_text = Formatter(indent_size=args.indent_size).dump(parse_result.root)
    _write_text(args.output, output_text)
    runner.log_run(config, args.description, text, output_text, args.output)
    return 0


def _load_config(path: str) -> dict:
    config_text = _read_text(path)
    suffix = Path(path).suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return config_compiler.compile_config(config_text)
    return json.loads(config_text)


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if args.command == "format":
        return _handle_format(args)
    if args.command == "patch":
        return _handle_patch(args)
    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
