from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class UnitMismatchError(ValueError):
    pass


@dataclass
class UnitExpectations:
    time_unit: Optional[str] = None
    voltage_unit: Optional[str] = None
    leakage_power_unit: Optional[str] = None

    @classmethod
    def from_config(cls, config: dict) -> "UnitExpectations":
        expected = config.get("expected_units", {})
        return cls(
            time_unit=expected.get("time_unit"),
            voltage_unit=expected.get("voltage_unit"),
            leakage_power_unit=expected.get("leakage_power_unit"),
        )


def validate_units(library_context: dict, expectations: UnitExpectations) -> None:
    for field, expected in expectations.__dict__.items():
        if expected is None:
            continue
        actual = library_context.get(field)
        if actual != expected:
            raise UnitMismatchError(
                f"Library is {actual}, but Patch expects {expected}. "
                "Manual conversion required or Config update needed."
            )
