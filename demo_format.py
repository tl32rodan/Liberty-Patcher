import time
from liberty_core import Parser, Formatter

input_path = "examples/asap7sc6t_SIMPLE_SLVT_TT_nldm_211010.lib"
output_path = "formatted_output.lib"

print(f"Reading {input_path}...")
start = time.time()

with open(input_path, "r") as f:
    text = f.read()
parse_result = Parser().parse(text)
print(f"Parsed in {time.time() - start:.2f}s")

print("Formatting...")
formatter = Formatter(indent_size=2)
dump_str = formatter.dump(parse_result.root)

with open(output_path, "w") as f:
    f.write(dump_str)

print(f"Done! Check {output_path}")
