from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class QuoteStyle(Enum):
    NONE = 0
    DOUBLE = 1


@dataclass
class CSTNode:
    parent: Optional["CSTNode"] = None
    children: List["CSTNode"] = field(default_factory=list)

    def add_child(self, child: "CSTNode") -> None:
        child.parent = self
        self.children.append(child)


@dataclass
class GroupNode(CSTNode):
    name: str = ""
    args_tokens: List["Token"] = field(default_factory=list)


@dataclass
class AttributeNode(CSTNode):
    key: str = ""
    raw_tokens: List["Token"] = field(default_factory=list)
    quote_style: QuoteStyle = QuoteStyle.NONE
    use_parens: bool = False


@dataclass
class CommentNode(CSTNode):
    text: str = ""


@dataclass
class RootNode(CSTNode):
    pass


@dataclass
class LibraryContext:
    time_unit: Optional[str] = None
    voltage_unit: Optional[str] = None
    leakage_power_unit: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "time_unit": self.time_unit,
            "voltage_unit": self.voltage_unit,
            "leakage_power_unit": self.leakage_power_unit,
        }


class TokenType(Enum):
    GROUP_START = "("
    GROUP_END = ")"
    BLOCK_START = "{"
    BLOCK_END = "}"
    COLON = ":"
    SEMI = ";"
    COMMA = ","
    STRING = "STRING"
    IDENTIFIER = "IDENTIFIER"
    COMMENT = "COMMENT"
    ESCAPED_NEWLINE = "ESCAPED_NEWLINE"


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
