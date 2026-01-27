from __future__ import annotations

import argparse
import time

import cli

DEFAULT_INPUT_PATH = "examples/asap7sc6t_SIMPLE_SLVT_TT_nldm_211010.lib"
DEFAULT_CONFIG_PATH = "examples/patch_demo.yaml"
DEFAULT_OUTPUT_PATH = "patched_output.lib"


def main(
    input_path: str = DEFAULT_INPUT_PATH,
    config_path: str = DEFAULT_CONFIG_PATH,
    output_path: str = DEFAULT_OUTPUT_PATH,
    indent_size: int = 2,
) -> int:
    print(f"Reading {input_path}...")
    start = time.time()

    args = argparse.Namespace(
        input=input_path,
        config=config_path,
        output=output_path,
        description="demo patch",
        indent_size=indent_size,
        db="",
        dump_parse=None,
    )

    print("Patching with CLI...")
    exit_code = cli._handle_patch(args)

    print(f"Completed in {time.time() - start:.2f}s")
    print(f"Done! Check {output_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
