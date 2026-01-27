from __future__ import annotations

import argparse
import time

import cli

DEFAULT_INPUT_PATH = "examples/asap7sc6t_SIMPLE_SLVT_TT_nldm_211010.lib"
DEFAULT_OUTPUT_PATH = "formatted_output.lib"


def main(
    input_path: str = DEFAULT_INPUT_PATH,
    output_path: str = DEFAULT_OUTPUT_PATH,
    indent_size: int = 2,
) -> int:
    print(f"Reading {input_path}...")
    start = time.time()

    args = argparse.Namespace(
        input=input_path,
        output=output_path,
        indent_size=indent_size,
        dump_parse=None,
    )

    print("Formatting with CLI...")
    exit_code = cli._handle_format(args)

    print(f"Completed in {time.time() - start:.2f}s")
    print(f"Done! Check {output_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
