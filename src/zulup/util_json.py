from __future__ import annotations

import enum


def check_enum(enum_class: type[enum.StrEnum], value: str) -> None:
    valid = [e.value for e in enum_class]
    if value not in valid:
        raise ValueError(
            f"'{enum_class.__name__}: {value}' is invalid. Please use one of {valid}!"
        )
