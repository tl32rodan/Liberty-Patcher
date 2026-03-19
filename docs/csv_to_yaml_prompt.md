# Prompt: Generate a Python Script to Convert Margin CSV to Liberty-Patcher YAML

## Instructions for AI

You are tasked with writing a Python script that converts a **CSV file containing margin data** into a **YAML configuration file** for a tool called **Liberty-Patcher**. Read this entire document carefully before you begin — it contains all the background, format specifications, and requirements you need.

---

## 1. Background and Purpose

### What is Liberty-Patcher?

Liberty-Patcher is an internal tool that modifies semiconductor timing library files (`.lib` files in the Liberty format). These library files contain hierarchical data describing cell timing, power, and other electrical characteristics in lookup table (matrix) form.

Liberty-Patcher reads a **YAML configuration file** that specifies:
- **Where** to apply changes (called "scope" — targeting specific cells, pins, and timing groups)
- **What** changes to apply (called "action" — an element-wise add operation on the matrix data)

### What is the margin CSV?

Our team maintains margin data in CSV files. Each row in the CSV represents one modification — it identifies a target (cell, pin, group, etc.) and provides a matrix of numerical adjustments. The matrix is "flattened" into individual columns in the CSV (e.g., a 5×5 matrix = 25 value columns).

### Why only `add` + `matrix` mode?

Liberty-Patcher supports multiple operations (`add`, `multiply`) and modes (`broadcast`, `matrix`). However, **all margin adjustments can be expressed as element-wise matrix addition**. The upstream flow is responsible for computing the correct residual values in the CSV, so the converter only needs to produce `operation: add` with `mode: matrix`. This keeps the script focused and reliable.

### Goal

Write a Python script that:
1. Reads the margin CSV file
2. Extracts scope information and matrix values from each row
3. Outputs a valid YAML file with **only `add` + `matrix` mode** modifications

---

## 2. YAML Target Format (Liberty-Patcher Config)

The output YAML must follow this exact structure:

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

### Structural rules:

1. The root key is `modifications`, which is a list.
2. Each list item has exactly two keys: `scope` and `action`.
3. **`scope.path`** is an ordered list describing the hierarchical path to the target:
   - `library: "*"` — always the first element (wildcard `"*"` matches all libraries)
   - `cell: "<cell_name>"` — the target cell (e.g., `"AND2x2_ASAP7_6t_SL"`)
   - `pin: "<pin_name>"` — the target pin (e.g., `"Y"`, or `"*"` for all)
   - `group: "<group_type>"` — one or more group entries (e.g., `"timing"`, then `"cell_fall"`)
4. **`action`** is always:
   ```yaml
   operation: add
   mode: matrix
   value: <2D list of floats>
   ```

---

## 3. CSV Source Format

### General structure

The CSV contains **multiple rows**, one per modification. Columns fall into two categories:

- **Scope columns** (non-numeric strings): Identify the target. Map to `scope.path` in the YAML.
- **Value columns** (numeric floats): The flattened N×N matrix. Stored as N² consecutive columns.

### Example CSV:

```csv
cell,pin,group,sub_group,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12,v13,v14,v15,v16,v17,v18,v19,v20,v21,v22,v23,v24,v25
AND2x2_ASAP7_6t_SL,Y,timing,cell_fall,0.01,0,0,0,0,0,0.01,0,0,0,0,0,0.01,0,0,0,0,0,0.01,0,0,0,0,0,0.01
AND2x2_ASAP7_6t_SL,Y,timing,cell_rise,0.005,0,0,0,0,0,0.005,0,0,0,0,0,0.005,0,0,0,0,0,0.005,0,0,0,0,0,0.005
```

### Important: Columns may change!

The CSV format is **not yet finalized**. The script must handle these potential changes:

| What may change | Examples | How to handle |
|---|---|---|
| **Scope column names** | `cell` → `cell_name`, `group` → `group_type` | Configurable via `--scope-columns` CLI arg |
| **Number of scope columns** | New columns like `related_pin` might be added | Support arbitrary scope columns via `--scope-columns` |
| **Matrix dimensions** | 5×5 (25 values), 7×7 (49 values), etc. | Auto-detect: count numeric columns, take square root |
| **Value column naming** | `v1,v2,...` or `val_0_0,val_0_1,...` | Identify by numeric content, not by name |

---

## 4. Script Requirements

### 4.1 Naming

**IMPORTANT:** Before writing the script, ask the developer:

> "There are multiple types of margins (e.g., timing margin, power margin, noise margin). What type of margin does this CSV represent? This determines the script name. For example:
> - `timing_margin_csv_to_yaml.py`
> - `power_margin_csv_to_yaml.py`
> - `margin_csv_to_yaml.py` (generic)
>
> Will there be separate scripts per margin type, or one script for all?"

### 4.2 Dependencies

- **Python 3.8+**
- **PyYAML** (`pip install pyyaml`) — for YAML output
- **csv** (standard library) — for CSV parsing
- **argparse** (standard library) — for CLI

### 4.3 CLI Interface

```bash
python <script_name>.py input.csv -o output.yaml [options]
```

| Argument | Required | Description |
|---|---|---|
| `input.csv` | Yes | Path to input CSV file |
| `-o / --output` | Yes | Path to output YAML file |
| `--scope-columns` | No | Comma-separated scope column names, in order. Default: auto-detect non-numeric columns |
| `--library` | No | Library name for the first path entry. Default: `"*"` |

### 4.4 Core Logic

```
1. Parse CLI arguments
2. Read CSV with csv.DictReader
3. Determine scope vs. value columns:
   - If --scope-columns given → use those as scope, rest are value columns
   - Otherwise → auto-detect: try float() on first data row per column
4. For each row:
   a. Extract scope column values (in order)
   b. Extract value column values as floats
   c. N = int(sqrt(num_values)) — error if not perfect square
   d. Reshape into N×N 2D list
   e. Build modification dict:
      scope.path = [{library: <lib>}] + one entry per scope column
      action = {operation: "add", mode: "matrix", value: 2D list}
5. Dump all modifications to YAML
```

### 4.5 Scope Path Construction

Given scope columns in order, each column maps to a YAML path entry:

- Column name contains `cell` → `cell: "<value>"`
- Column name contains `pin` → `pin: "<value>"`
- Everything else → `group: "<value>"`

The path always starts with `library: "*"` (or the `--library` value).

### 4.6 YAML Formatting

Matrix rows must use **flow style**: `- [0.01, 0, 0, 0, 0]`
Everything else uses **block style** (default).

Achieve this with a custom PyYAML representer:

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

Wrap each matrix row with `FlowList(row)` before calling `yaml.dump()`.

---

## 5. Error Handling

| Error case | Action |
|---|---|
| CSV file not found | Print path, exit with code 1 |
| No numeric columns found | Suggest using `--scope-columns` |
| Value count not a perfect square | Print count, suggest checking CSV |
| Empty CSV | Warn, output YAML with empty `modifications: []` |
| `--scope-columns` names not in header | List available column names |

---

## 6. Complete Example

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

## 7. Testing Checklist

- [ ] Script runs on the example CSV above without errors
- [ ] Output YAML is valid (parseable by `yaml.safe_load`)
- [ ] Matrix dimensions correct (5×5 for 25 values, 7×7 for 49)
- [ ] Scope path order matches CSV column order
- [ ] `--scope-columns` override works
- [ ] Clear error messages for bad input
