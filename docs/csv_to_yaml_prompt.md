# Prompt: Generate a Python Script to Convert Margin CSV to Liberty-Patcher YAML

## Instructions for AI

You are tasked with writing a Python script that converts a **CSV file containing margin data** into a **YAML configuration file** for a tool called **Liberty-Patcher**. Read this entire document carefully before you begin — it contains all the background, format specifications, and requirements you need.

---

## 1. Background and Purpose

### What is Liberty-Patcher?

Liberty-Patcher is an internal tool that modifies semiconductor timing library files (`.lib` files in the Liberty format). These library files contain hierarchical data describing cell timing, power, and other electrical characteristics in lookup table (matrix) form.

Liberty-Patcher reads a **YAML configuration file** that specifies:
- **Where** to apply changes (called "scope" — targeting specific cells, pins, and timing groups)
- **What** changes to apply (called "action" — an arithmetic operation on the matrix data)

### What is the margin CSV?

Our team maintains margin data in CSV files. Each row in the CSV represents one modification — it identifies a target (cell, pin, group, etc.) and provides a matrix of numerical adjustments. The matrix is "flattened" into individual columns in the CSV (e.g., a 5×5 matrix = 25 value columns).

### Goal

Write a Python script that:
1. Reads the margin CSV file
2. Extracts scope information and matrix values from each row
3. Outputs a valid YAML file that Liberty-Patcher can consume

---

## 2. YAML Target Format (Liberty-Patcher Config)

The output YAML must follow this exact structure. Here is a complete example:

```yaml
modifications:
  # Example 1: broadcast mode (scalar applied to all elements)
  - scope:
      path:
        - library: "*"
        - cell: "AND2x2_ASAP7_6t_SL"
        - pin: "Y"
        - group: "timing"
    action:
      operation: add
      mode: broadcast
      value: 0.05

  # Example 2: matrix mode (element-wise addition with a full matrix)
  - scope:
      path:
        - library: "*"
        - cell: "AND2x2_ASAP7_6t_SL"
        - pin: "Y"
        - group: "timing"
          attributes:
            related_pin: "A"
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

### Key structural rules:

1. The root key is `modifications`, which is a list.
2. Each list item has two keys: `scope` and `action`.
3. **`scope.path`** is an ordered list that describes the hierarchical path to the target:
   - `library: "*"` — always the first element, typically uses wildcard `"*"`
   - `cell: "<cell_name>"` — the cell name (e.g., `"AND2x2_ASAP7_6t_SL"`)
   - `pin: "<pin_name>"` — the pin name (e.g., `"Y"`, or `"*"` for all pins)
   - `group: "<group_type>"` — a group in the hierarchy (e.g., `"timing"`, `"internal_power"`)
   - A second `group:` entry can specify a sub-group (e.g., `"cell_fall"`, `"cell_rise"`, `"rise_transition"`, `"fall_transition"`, `"rise_power"`, `"fall_power"`)
   - Optionally, a group can have an `attributes` sub-key for filtering (e.g., `related_pin: "A"`)
4. **`action`** has three keys:
   - `operation`: The arithmetic operation. **For this use case, always `"add"`.**
   - `mode`: How the value is applied. **For this use case, always `"matrix"`** (element-wise addition).
   - `value`: A 2D list (list of lists) representing the matrix. Each inner list is one row.

---

## 3. CSV Source Format

### General structure

The CSV file contains **multiple rows**, each representing one modification. The columns fall into two categories:

- **Scope columns** (non-numeric): Identify the target cell/pin/group. These map to the `scope.path` in the YAML.
- **Value columns** (numeric): The flattened matrix values. A N×N matrix is stored as N² consecutive columns.

### Example CSV (this is illustrative — actual column names may differ):

```csv
cell,pin,group,sub_group,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12,v13,v14,v15,v16,v17,v18,v19,v20,v21,v22,v23,v24,v25
AND2x2_ASAP7_6t_SL,Y,timing,cell_fall,0.01,0,0,0,0,0,0.01,0,0,0,0,0,0.01,0,0,0,0,0,0.01,0,0,0,0,0,0.01
```

### Important: Columns may change!

The CSV format is **not yet finalized**. The following things may change in the future:

| What may change | Examples | How the script should handle it |
|---|---|---|
| **Scope column names** | `cell` might become `cell_name`; `group` might split into `group_type` + `sub_group_type` | Use a configurable column mapping (CLI args or config dict) |
| **Number of scope columns** | New scope columns like `related_pin`, `when_condition` might be added | Support arbitrary scope columns via configuration |
| **Matrix dimensions** | Could be 5×5 (25 values), 7×7 (49 values), or other sizes | Auto-detect from the number of value columns (must be a perfect square) |
| **Value column naming** | Could be `v1,v2,...` or `val_0_0,val_0_1,...` or unnamed | Identify value columns by: (a) checking if they are numeric, or (b) using a configurable prefix/pattern |
| **Additional metadata columns** | e.g., `operation`, `mode`, `comment` columns might be added | Ignore unknown non-scope, non-value columns gracefully |

---

## 4. Script Requirements

### 4.1 Naming

**IMPORTANT:** Before writing the script, ask the developer:

> "There are multiple types of margins (e.g., timing margin, power margin, noise margin, etc.). What type of margin does this CSV represent? This will determine the script name. For example:
> - `timing_margin_csv_to_yaml.py` — for timing margin
> - `power_margin_csv_to_yaml.py` — for power margin
> - `margin_csv_to_yaml.py` — for a generic converter
>
> Also, is it possible that one script needs to handle multiple margin types, or will there be separate scripts per type?"

### 4.2 Dependencies

- **Python 3.8+**
- **PyYAML** (`pip install pyyaml`) — for YAML output
- **csv** (standard library) — for CSV parsing
- **argparse** (standard library) — for CLI interface

### 4.3 CLI Interface

```bash
python <script_name>.py input.csv -o output.yaml [options]
```

Required arguments:
- `input.csv` — path to the input CSV file
- `-o / --output` — path to the output YAML file

Optional arguments:
- `--scope-columns` — comma-separated list of CSV column names that form the scope path, **in order**. Default: auto-detect non-numeric columns. Example: `--scope-columns cell,pin,group,sub_group`
- `--library` — the library name/pattern for the first scope path entry. Default: `"*"`
- `--scope-mapping` — JSON string or file path defining how CSV column names map to YAML scope keys. Example: `'{"cell_name": "cell", "pin_name": "pin", "timing_group": "group"}'`

### 4.4 Core Logic (Pseudocode)

```
1. Parse CLI arguments
2. Read the CSV file (use csv.DictReader)
3. Determine scope columns and value columns:
   a. If --scope-columns is provided, use those
   b. Otherwise, auto-detect: try to parse each column's values as float;
      columns that fail are scope columns
4. For each row in the CSV:
   a. Extract scope values from the scope columns
   b. Extract numeric values from the value columns
   c. Calculate matrix dimension: N = sqrt(len(values))
      - If not a perfect square, raise an error with a clear message
   d. Reshape flat values into N×N 2D list
   e. Build the YAML modification entry:
      - scope.path: [library: <library>] + one entry per scope column
      - action: {operation: "add", mode: "matrix", value: <2D list>}
5. Assemble all modifications under the "modifications" key
6. Write to YAML file using PyYAML (use default_flow_style=None so that
   the matrix rows are rendered as flow-style lists like [0.01, 0, 0, ...])
```

### 4.5 Scope Path Construction Rules

Given scope columns in order, build the path as follows:

| Scope column value | YAML path entry |
|---|---|
| First column (typically `cell`) | `cell: "<value>"` |
| Second column (typically `pin`) | `pin: "<value>"` |
| Remaining columns (typically `group`, `sub_group`) | `group: "<value>"` (one entry per column) |

The first entry in the path is always `library: "*"` (or the value from `--library`).

**Special handling:**
- If a scope column name contains `cell`, map it to `cell: <value>`
- If a scope column name contains `pin`, map it to `pin: <value>`
- Otherwise, map it to `group: <value>`
- The `--scope-mapping` argument overrides this auto-detection

### 4.6 YAML Output Formatting

The YAML output must be human-readable. Specifically:
- The matrix `value` should use **flow style** for each row: `- [0.01, 0, 0, 0, 0]`
- The rest of the YAML should use **block style** (default PyYAML behavior)

To achieve this with PyYAML, define a custom representer:

```python
import yaml

class FlowList(list):
    """A list that will be represented in flow style in YAML."""
    pass

def flow_list_representer(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

yaml.add_representer(FlowList, flow_list_representer)
```

Then wrap each matrix row with `FlowList(row)` before dumping.

---

## 5. Error Handling

The script should handle these error cases with clear, actionable error messages:

1. **CSV file not found** — print path and exit
2. **No numeric columns found** — suggest using `--scope-columns` to explicitly specify scope columns
3. **Number of value columns is not a perfect square** — print the count and suggest checking the CSV
4. **Empty CSV file** — warn and produce a YAML with an empty `modifications` list
5. **Missing scope column** — if `--scope-columns` specifies a column not in the CSV header, list available columns

---

## 6. Example End-to-End

### Input CSV (`margin.csv`):

```csv
cell,pin,group,sub_group,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12,v13,v14,v15,v16,v17,v18,v19,v20,v21,v22,v23,v24,v25
AND2x2_ASAP7_6t_SL,Y,timing,cell_fall,0.01,0,0,0,0,0,0.01,0,0,0,0,0,0.01,0,0,0,0,0,0.01,0,0,0,0,0,0.01
AND2x2_ASAP7_6t_SL,Y,timing,cell_rise,0.005,0,0,0,0,0,0.005,0,0,0,0,0,0.005,0,0,0,0,0,0.005,0,0,0,0,0,0.005
```

### Command:

```bash
python margin_csv_to_yaml.py margin.csv -o margin_patch.yaml
```

### Expected Output (`margin_patch.yaml`):

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

After generating the script, verify:

- [ ] Script runs without errors on the example CSV above
- [ ] Output YAML is valid YAML (parseable by `yaml.safe_load`)
- [ ] Matrix dimensions are correct (5×5 for 25 values, 7×7 for 49 values)
- [ ] Scope path order matches the CSV column order
- [ ] `--scope-columns` flag works to override auto-detection
- [ ] Error messages are clear when CSV format is unexpected
- [ ] The script handles edge cases: empty rows, extra whitespace, trailing commas

---

## 8. Future Extensibility Notes

These are known future directions. **Do not implement them now**, but design the code so they can be added easily:

- Supporting `operation: multiply` and `mode: broadcast` (currently hardcoded to `add` + `matrix`)
- Supporting `attributes` filters in the scope (e.g., `related_pin`, `when` conditions)
- Reading multiple CSV files and merging into one YAML
- Supporting non-square matrices (e.g., 7×5) — would require explicit dimension specification
- Adding a `--dry-run` flag to preview the YAML without writing to file
