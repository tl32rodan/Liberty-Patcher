# Liberty-Patcher

## Immediate Verification (Format Demo)

Run the following script to verify the Parse & Format behavior on the ASAP7 example.

### 1. Create `demo_format.py`

This repository includes a ready-to-run script at the project root. If you need to recreate it, the content is:

```python
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
```

### 2. Execute

```bash
python demo_format.py
```

This helps confirm backslash alignment and quote normalization.

---

# Implementation Specification: Phase 2 (Application Layer & Glue)

This spec defines how to assemble the existing core pieces into an executable tool and implement JSON Patch business logic.

## Implementation Spec: Phase 2 - Application Layer & CLI

**Version:** 2.1  
**Objective:** Bridge the Core (Parser/Formatter) with the Logic (Patch Engine) via a CLI, enabling end-to-end execution.

---

## 1. New Module: `cli.py` (The Entry Point)

**Requirement:** Create a robust CLI using `argparse` to expose functionalities.

### 1.1 Command Structure

The tool should support a subcommands pattern:

- `libmod format`: Purely clean up a file (Parse -> Dump).
- `libmod patch`: Apply modifications (Parse -> Patch -> Dump -> Log).

### 1.2 Expected Commands (Future State)

Once implemented, users will run:

```bash
# 1. Format Only (Normalization)
python cli.py format \
    --input examples/asap7sc6t_SIMPLE_SLVT_TT_nldm_211010.lib \
    --output normalized.lib

# 2. Apply Patch
python cli.py patch \
    --input normalized.lib \
    --config patch.json \
    --output patched.lib \
    --description "Fix hold time violation for ASAP7"
```

---

## 2. Enhancement: `patch_engine/runner.py` (The Glue Logic)

**Requirement:** Implement the "Interpreter" that orchestrates the modification loop.

### 2.1 Class `PatchRunner`

**Input:** `ParseResult` (CST Root), `ConfigDict` (JSON)

**Workflow:**

1. **Validate Units**: Check `config['expected_units']` against `ParseResult.context`. Raise error if mismatch.
2. **Iterate Modifications**: Loop through each item in `config['modifications']`.
3. **Resolve Scope**:
   - Call `scope.py` functions to find target nodes.
   - Update needed in `scope.py`: Add logic to drill down from cell -> pin -> timing -> values.
4. **Apply Action**:
   - Identify the target attribute (e.g., `values`, `rise_constraint`).
   - Parse the existing matrix (using `matrix.py`).
   - Perform math operation (using `matrix.py`).
   - **Write Back**: Update the CST node's `raw_tokens` with the new calculated values (must convert float back to string tokens).

---

## 3. Enhancement: `patch_engine/scope.py` (Advanced Resolver)

**Current Status:** Only supports `find_groups_by_name` and `filter_cells`.  
**Requirement:** Add "Attribute-aware" filtering to support the spec.

### Function: `find_nodes_by_scope(root, scope_dict) -> List[CSTNode]`

**Logic:**

- **Layer 1**: Filter Cells (`scope['cells']`).
- **Layer 2**: Filter Pins (`scope['pins']`).
- **Layer 3**: Filter Timing/Power Groups (`scope['metric']`, `scope['direction']`).
  - **Challenge**: Need to check attributes inside the group (e.g., `related_pin`, `timing_sense`).
  - **Impl**: Helper function `group_has_attribute(group, key, value_pattern)`.

---

## 4. Integration Test (End-to-End)

**Requirement:** Create `tests/test_e2e.py` using the uploaded ASAP7 example.

### Scenario

1. Load `examples/asap7sc6t_SIMPLE_SLVT_TT_nldm_211010.lib`.
2. Define a Mock Config:

```json
{
  "modifications": [{
    "scope": { "cells": ["AND*"], "metric": "timing" },
    "action": { "operation": "multiply", "mode": "broadcast", "value": 1.1 }
  }]
}
```

3. Run `PatchRunner`.

### Verification

- Check if `AND2x2_ASAP7_75t_SL` cell exists.
- Check if its timing tables are exactly 1.1x larger.
- Check if the output file format is valid (parseable again).
- Check if DB record is created.

---

## Suggested Action Plan for Agent

- Create `patch_engine/runner.py`: Focus on the loop logic first.
- Update `patch_engine/scope.py`: Add the deep attribute filtering capability.
- Create `cli.py`: Wire up the arguments to the Runner.
- Run E2E Test: Use the ASAP7 library as the golden sample.

---

## Testing Policy

Make sure source codes added are covered by behavioral unit tests.
