import time
from pathlib import Path

import config_compiler
from liberty_core import Formatter, Parser
from patch_engine import PatchRunner

input_path = "examples/asap7sc6t_SIMPLE_SLVT_TT_nldm_211010.lib"
config_path = "examples/patch_demo.yaml"
output_path = "patched_output.lib"

print(f"Reading {input_path}...")
start = time.time()

text = Path(input_path).read_text(encoding="utf-8")
parse_result = Parser().parse(text)
print(f"Parsed in {time.time() - start:.2f}s")

print(f"Compiling {config_path}...")
config_text = Path(config_path).read_text(encoding="utf-8")
config = config_compiler.compile_config(config_text)

print("Patching...")
runner = PatchRunner()
runner.run(parse_result, config)
output_text = Formatter(indent_size=2).dump(parse_result.root)
Path(output_path).write_text(output_text, encoding="utf-8")

print(f"Done! Check {output_path}")
