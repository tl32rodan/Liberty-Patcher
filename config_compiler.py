from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - handled in tests via explicit error
    yaml = None


class ConfigCompilerError(ValueError):
    pass


def compile_config(yaml_text: str, export_json_path: Optional[str] = None) -> dict:
    data = _load_yaml(yaml_text)
    return compile_config_data(data, export_json_path=export_json_path)


def compile_config_data(data: dict, export_json_path: Optional[str] = None) -> dict:
    if not isinstance(data, dict):
        raise ConfigCompilerError("Config root must be a mapping.")
    modifications = data.get("modifications", [])
    if not isinstance(modifications, list):
        raise ConfigCompilerError("Config modifications must be a list.")
    compiled_mods = []
    for modification in modifications:
        if not isinstance(modification, dict):
            raise ConfigCompilerError("Each modification must be a mapping.")
        compiled = dict(modification)
        scope = modification.get("scope", {})
        compiled["scope"] = _compile_scope(scope)
        compiled_mods.append(compiled)
    compiled_config = dict(data)
    compiled_config["modifications"] = compiled_mods
    if export_json_path:
        _export_compiled_json(compiled_config, export_json_path)
    return compiled_config


def _load_yaml(text: str) -> dict:
    if yaml is None:
        raise ConfigCompilerError("PyYAML is required to load YAML configs.")
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigCompilerError("YAML root must be a mapping.")
    return data


def _compile_scope(scope: Any) -> dict:
    if scope is None:
        return {}
    if isinstance(scope, list):
        return {"path": [_compile_path_selector(item) for item in scope]}
    if not isinstance(scope, dict):
        raise ConfigCompilerError("Scope must be a mapping or a path list.")
    if "path" not in scope:
        raise ConfigCompilerError("Scope must include a path array.")
    path = scope.get("path", [])
    if not isinstance(path, list):
        raise ConfigCompilerError("Scope path must be a list.")
    compiled_path = [_compile_path_selector(item) for item in path]
    compiled_scope = dict(scope)
    compiled_scope["path"] = compiled_path
    return compiled_scope


def _compile_path_selector(selector: Any) -> dict:
    if isinstance(selector, str):
        return {"group": selector}
    if not isinstance(selector, dict):
        raise ConfigCompilerError("Path selector must be a mapping or string.")
    if "group" in selector:
        return _normalize_attributes(dict(selector))
    if len(selector) == 1:
        key, value = next(iter(selector.items()))
        compiled: Dict[str, Any] = {"group": key}
        if isinstance(value, dict):
            compiled.update(value)
        elif value is not None:
            compiled["name"] = value
        return _normalize_attributes(compiled)
    return _normalize_attributes(dict(selector))


def _normalize_attributes(selector: Dict[str, Any]) -> Dict[str, Any]:
    if "attrs" in selector and "attributes" in selector:
        raise ConfigCompilerError("Selector cannot include both attrs and attributes.")
    if "attrs" in selector:
        selector = dict(selector)
        selector["attributes"] = selector.pop("attrs")
    return selector


def _export_compiled_json(config: dict, path: str) -> None:
    output_path = Path(path)
    output_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
