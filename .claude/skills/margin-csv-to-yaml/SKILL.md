---
name: margin-csv-to-yaml
description: Generate a Python script that converts a margin CSV file into a Liberty-Patcher YAML config. Use when a developer needs to create or update a CSV-to-YAML converter for margin data.
argument-hint: "[margin-type]"
disable-model-invocation: true
---

# Generate a Margin CSV to Liberty-Patcher YAML Converter

Write a Python script that converts a CSV file containing margin data into a YAML configuration file for Liberty-Patcher. The margin type is: **$ARGUMENTS** (if no margin type was specified, ask the developer which type this is — e.g., timing margin, power margin, noise margin — as this determines the script filename like `timing_margin_csv_to_yaml.py`).

---

## Background

### What is Liberty-Patcher?

Liberty-Patcher is a tool that modifies semiconductor timing library files (`.lib`, Liberty format). These files contain hierarchical data — cells, pins, timing groups — with electrical characteristics stored as lookup-table matrices (e.g., 5x5 or 7x7).

Liberty-Patcher reads a **YAML config** that says:
- **Where** to patch — a hierarchical path called "scope" (library → cell → pin → group)
- **What** to patch — an element-wise matrix addition on the target's `values` attribute

### What is the margin CSV?

The team stores margin adjustments in CSV files. Each row = one patch target + a flattened N×N matrix of adjustment values (e.g., 25 columns for a 5×5 matrix). The upstream flow computes the residual values; this script just reformats them into YAML.

### Why only `add` + `matrix`?

All margin adjustments are expressed as element-wise matrix addition. The upstream flow handles all computation, so the converter always produces `operation: add`, `mode: matrix`. No other modes are needed.

---

## YAML Target Format

The output must match this exact structure:

```yaml
modifications:
  - scope:
      path:
        - library: "*"
        - cell: "AND2x2_ASAP7_6t_SL"
        - pin: "Y"
        - group: "timing"
        - group: "cell_fall"
    action:
      operation: add
      mode: matrix
      value:
        - [0.01, 0, 0, 0, 0, 0, 0]
        - [0, 0.01, 0, 0, 0, 0, 0]
        - [0, 0, 0.01, 0, 0, 0, 0]
        - [0, 0, 0, 0.01, 0, 0, 0]
        - [0, 0, 0, 0, 0.01, 0, 0]
        - [0, 0, 0, 0, 0, 0.01, 0]
        - [0, 0, 0, 0, 0, 0, 0.01]
```

### Rules

1. Root key: `modifications` (a list)
2. Each item has `scope` and `action`
3. `scope.path` is an ordered list:
   - `library: "*"` — always first (wildcard)
   - `cell: "<name>"` — target cell
   - `pin: "<name>"` — target pin (or `"*"` for all)
   - `group: "<type>"` — one or more group entries (e.g., `"timing"`, then `"cell_fall"`)
4. `action` is always exactly:
   ```yaml
   operation: add
   mode: matrix
   value: <2D list of floats>
   ```

---

## CSV Source Format

Each row = one modification. Columns are either **scope** (strings) or **values** (floats):

```csv
cell,pin,group,sub_group,v1,v2,v3,...,v25
AND2x2_ASAP7_6t_SL,Y,timing,cell_fall,0.01,0,0,...,0.01
AND2x2_ASAP7_6t_SL,Y,timing,cell_rise,0.005,0,0,...,0.005
```

### Columns may change!

The CSV format is not finalized. Handle these changes:

| What may change | How to handle |
|---|---|
| Scope column names (`cell` → `cell_name`) | Configurable via `--scope-columns` CLI arg |
| Number of scope columns (new `related_pin` column) | Support arbitrary scope columns via `--scope-columns` |
| Matrix dimensions (5×5, 7×7, etc.) | Auto-detect: count numeric columns, take square root |
| Value column naming (`v1` vs `val_0_0`) | Identify by numeric content, not by name |

---

## Script Requirements

### Dependencies

- Python 3.8+
- PyYAML (`pip install pyyaml`)
- csv, argparse (standard library)

### CLI Interface

```bash
python <script_name>.py input.csv -o output.yaml [options]
```

| Argument | Required | Description |
|---|---|---|
| `input.csv` | Yes | Input CSV file path |
| `-o / --output` | Yes | Output YAML file path |
| `--scope-columns` | No | Comma-separated scope column names in order. Default: auto-detect non-numeric columns |
| `--library` | No | Library name for first path entry. Default: `"*"` |

### Core Logic

```
1. Parse CLI arguments
2. Read CSV with csv.DictReader
3. Determine scope vs. value columns:
   - If --scope-columns given → use those; rest are value columns
   - Otherwise → auto-detect: try float() on first data row per column
4. For each row:
   a. Extract scope values (in order)
   b. Extract numeric values as floats
   c. N = int(sqrt(num_values)) — error if not perfect square
   d. Reshape into N×N 2D list
   e. Build modification:
      scope.path = [{library: <lib>}] + one entry per scope column
      action = {operation: "add", mode: "matrix", value: <2D list>}
5. Dump all modifications to YAML
```

### Scope Path Construction

Map each scope column to a YAML path entry:
- Column name contains `cell` → `cell: "<value>"`
- Column name contains `pin` → `pin: "<value>"`
- Everything else → `group: "<value>"`

Path always starts with `library: "*"` (or `--library` value).

### YAML Formatting

Matrix rows must render as flow-style lists: `- [0.01, 0, 0, 0, 0]`

Use a custom PyYAML representer:

```python
import yaml

class FlowList(list):
    pass

def flow_list_representer(dumper, data):
    return dumper.represent_sequence(
        'tag:yaml.org,2002:seq', data, flow_style=True
    )

yaml.add_representer(FlowList, flow_list_representer)
```

Wrap each matrix row with `FlowList(row)` before `yaml.dump()`.

### Error Handling

| Error | Action |
|---|---|
| CSV not found | Print path, exit code 1 |
| No numeric columns | Suggest `--scope-columns` |
| Value count not perfect square | Print count, suggest checking CSV |
| Empty CSV | Warn, output `modifications: []` |
| Bad `--scope-columns` name | List available columns |

---

## Complete Example

### Input (`margin.csv`):

```csv
cell,pin,group,sub_group,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12,v13,v14,v15,v16,v17,v18,v19,v20,v21,v22,v23,v24,v25
AND2x2_ASAP7_6t_SL,Y,timing,cell_fall,0.01,0,0,0,0,0,0.01,0,0,0,0,0,0.01,0,0,0,0,0,0.01,0,0,0,0,0,0.01
AND2x2_ASAP7_6t_SL,Y,timing,cell_rise,0.005,0,0,0,0,0,0.005,0,0,0,0,0,0.005,0,0,0,0,0,0.005,0,0,0,0,0,0.005
```

### Command:

```bash
python margin_csv_to_yaml.py margin.csv -o margin_patch.yaml
```

### Output (`margin_patch.yaml`):

```yaml
modifications:
  - scope:
      path:
        - library: "*"
        - cell: "AND2x2_ASAP7_6t_SL"
        - pin: "Y"
        - group: "timing"
        - group: "cell_fall"
    action:
      operation: add
      mode: matrix
      value:
        - [0.01, 0.0, 0.0, 0.0, 0.0]
        - [0.0, 0.01, 0.0, 0.0, 0.0]
        - [0.0, 0.0, 0.01, 0.0, 0.0]
        - [0.0, 0.0, 0.0, 0.01, 0.0]
        - [0.0, 0.0, 0.0, 0.0, 0.01]
  - scope:
      path:
        - library: "*"
        - cell: "AND2x2_ASAP7_6t_SL"
        - pin: "Y"
        - group: "timing"
        - group: "cell_rise"
    action:
      operation: add
      mode: matrix
      value:
        - [0.005, 0.0, 0.0, 0.0, 0.0]
        - [0.0, 0.005, 0.0, 0.0, 0.0]
        - [0.0, 0.0, 0.005, 0.0, 0.0]
        - [0.0, 0.0, 0.0, 0.005, 0.0]
        - [0.0, 0.0, 0.0, 0.0, 0.005]
```

---

## Testing Checklist

After generating the script, verify:
- [ ] Runs on example CSV without errors
- [ ] Output is valid YAML (`yaml.safe_load` succeeds)
- [ ] Matrix dimensions correct (5×5 for 25 values, 7×7 for 49)
- [ ] Scope path order matches CSV column order
- [ ] `--scope-columns` override works
- [ ] Clear error messages for bad input
