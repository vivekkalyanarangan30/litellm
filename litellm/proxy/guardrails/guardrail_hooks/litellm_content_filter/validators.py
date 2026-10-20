import functools
import re
from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Final

_SEPARATORS: Final = re.compile(r"[\s\-]")
_IBAN_CHARACTERS: Final = re.compile(r"[0-9A-Z]{5,34}")
_GSTIN_CHARACTERS: Final = re.compile(r"[0-9A-Z]{15}")
_BASE36_DIGITS: Final = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_VERHOEFF_MULTIPLICATION: Final = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)
_VERHOEFF_PERMUTATION: Final = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
)


def _luhn_term(position: int, digit: int) -> int:
    if position % 2 == 0:
        return digit
    doubled: Final = digit * 2
    return doubled - 9 if doubled > 9 else doubled


def passes_luhn(value: str) -> bool:
    digits: Final = _SEPARATORS.sub("", value)
    if not digits.isdecimal():
        return False
    return sum(_luhn_term(position, int(digit)) for position, digit in enumerate(reversed(digits))) % 10 == 0


def passes_iban_mod97(value: str) -> bool:
    iban: Final = _SEPARATORS.sub("", value).upper()
    if _IBAN_CHARACTERS.fullmatch(iban) is None:
        return False
    rearranged: Final = iban[4:] + iban[:4]
    return int("".join(str(int(character, 36)) for character in rearranged)) % 97 == 1


def _verhoeff_step(checksum: int, position_and_digit: tuple[int, str]) -> int:
    position, digit = position_and_digit
    return _VERHOEFF_MULTIPLICATION[checksum][_VERHOEFF_PERMUTATION[position % 8][int(digit)]]


def passes_verhoeff(value: str) -> bool:
    digits: Final = _SEPARATORS.sub("", value)
    if not digits.isdecimal():
        return False
    return functools.reduce(_verhoeff_step, enumerate(reversed(digits)), 0) == 0


def _gstin_term(position: int, character: str) -> int:
    product: Final = int(character, 36) * (2 if position % 2 else 1)
    return product // 36 + product % 36


def passes_gstin_checksum(value: str) -> bool:
    gstin: Final = _SEPARATORS.sub("", value).upper()
    if _GSTIN_CHARACTERS.fullmatch(gstin) is None:
        return False
    total: Final = sum(_gstin_term(position, character) for position, character in enumerate(gstin[:14]))
    return _BASE36_DIGITS[-total % 36] == gstin[14]


PATTERN_VALIDATORS: Final[Mapping[str, Callable[[str], bool]]] = MappingProxyType(
    {
        "luhn": passes_luhn,
        "iban_mod97": passes_iban_mod97,
        "verhoeff": passes_verhoeff,
        "gstin": passes_gstin_checksum,
    }
)
