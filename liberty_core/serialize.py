from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .cst import AttributeNode, CommentNode, GroupNode, RootNode, Token
from .parser import ParseResult


def serialize_parse_result(parse_result: ParseResult) -> Dict[str, Any]:
    return {
        "context": parse_result.context.as_dict(),
        "root": _serialize_node(parse_result.root),
    }


def dump_parse_result(parse_result: ParseResult, path: str) -> None:
    payload = serialize_parse_result(parse_result)
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _serialize_node(node: object) -> Dict[str, Any]:
    if isinstance(node, RootNode):
        return {"type": "root", "children": [_serialize_node(child) for child in node.children]}
    if isinstance(node, GroupNode):
        return {
            "type": "group",
            "name": node.name,
            "args_tokens": [_serialize_token(token) for token in node.args_tokens],
            "children": [_serialize_node(child) for child in node.children],
        }
    if isinstance(node, AttributeNode):
        return {
            "type": "attribute",
            "key": node.key,
            "raw_tokens": [_serialize_token(token) for token in node.raw_tokens],
            "quote_style": node.quote_style.name,
            "use_parens": node.use_parens,
        }
    if isinstance(node, CommentNode):
        return {"type": "comment", "text": node.text}
    raise TypeError(f"Unsupported node type: {type(node)}")


def _serialize_token(token: Token) -> Dict[str, Any]:
    return {
        "type": token.type.name,
        "value": token.value,
        "line": token.line,
        "column": token.column,
    }
