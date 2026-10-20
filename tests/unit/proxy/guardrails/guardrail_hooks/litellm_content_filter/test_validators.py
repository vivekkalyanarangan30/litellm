import pytest

from litellm.proxy.guardrails.guardrail_hooks.litellm_content_filter.validators import (
    passes_gstin_checksum,
    passes_iban_mod97,
    passes_luhn,
    passes_verhoeff,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("4111 1111 1111 1111", True),
        ("4111-1111-1111-1112", False),
        ("٤" + "١" * 15, True),
        ("4111 1111 1111 111x", False),
        ("", False),
    ],
)
def test_passes_luhn(value: str, expected: bool):
    assert passes_luhn(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("GB82 WEST 1234 5698 7654 32", True),
        ("gb82west12345698765432", True),
        ("GB82WEST12345698765433", False),
        ("GB82", False),
        ("GB82WEST1234569876543é", False),
    ],
)
def test_passes_iban_mod97(value: str, expected: bool):
    assert passes_iban_mod97(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2345 6789 0124", True),
        ("9876-5432-1096", True),
        ("234567890125", False),
        ("234567890142", False),
        ("2345 6789 012x", False),
    ],
)
def test_passes_verhoeff(value: str, expected: bool):
    assert passes_verhoeff(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("22ABCPK1234D1ZJ", True),
        ("07aaapz9999q1z5", True),
        ("22ABCPK1234D1ZK", False),
        ("22ABCPK1234D1Z", False),
        ("22ABCPK1234D1Zé", False),
    ],
)
def test_passes_gstin_checksum(value: str, expected: bool):
    assert passes_gstin_checksum(value) is expected
