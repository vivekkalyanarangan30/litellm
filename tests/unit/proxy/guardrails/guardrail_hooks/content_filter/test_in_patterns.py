from typing import Final

import pytest

from litellm.proxy.guardrails.guardrail_hooks.litellm_content_filter.content_filter import (
    ContentFilterGuardrail,
)
from litellm.types.guardrails import ContentFilterAction, ContentFilterPattern


async def _masked(pattern_name: str, text: str) -> str:
    guardrail: Final = ContentFilterGuardrail(
        guardrail_name=f"test-{pattern_name}",
        patterns=[
            ContentFilterPattern(pattern_type="prebuilt", pattern_name=pattern_name, action=ContentFilterAction.MASK)
        ],
    )
    guardrailed_inputs: Final = await guardrail.apply_guardrail(
        inputs={"texts": [text]}, request_data={}, input_type="request"
    )
    return guardrailed_inputs["texts"][0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("pattern_name", "text", "expected"),
    [
        ("in_aadhaar", "aadhaar 2345 6789 0124", "aadhaar [IN_AADHAAR_REDACTED]"),
        ("in_aadhaar", "id 234567890124 on file", "id [IN_AADHAAR_REDACTED] on file"),
        ("in_pan", "PAN ABCPK1234D", "PAN [IN_PAN_REDACTED]"),
        ("in_pan", "pan abcpk1234d", "pan [IN_PAN_REDACTED]"),
        ("in_gstin", "GSTIN 22ABCPK1234D1ZJ", "GSTIN [IN_GSTIN_REDACTED]"),
        ("in_ifsc", "IFSC ABCD0123456", "IFSC [IN_IFSC_REDACTED]"),
        ("in_upi_id", "my upi id is rahul.k@okbank", "my upi id is [IN_UPI_ID_REDACTED]"),
        ("in_upi_id", "VPA: rahul-99@ybank", "VPA: [IN_UPI_ID_REDACTED]"),
        ("in_phone", "call +91 98765 43210 now", "call [IN_PHONE_REDACTED] now"),
        ("in_phone", "call +91-9876543210", "call [IN_PHONE_REDACTED]"),
        ("in_phone_contextual", "mobile number 9876543210", "mobile number [IN_PHONE_CONTEXTUAL_REDACTED]"),
        ("in_driving_licence", "DL MH12 20110012345", "DL [IN_DRIVING_LICENCE_REDACTED]"),
        ("in_vehicle_registration", "car MH 12 AB 1234", "car [IN_VEHICLE_REGISTRATION_REDACTED]"),
        ("in_vehicle_registration", "car 22 BH 1234 AA", "car [IN_VEHICLE_REGISTRATION_REDACTED]"),
    ],
)
async def test_india_pattern_masks_identifier(pattern_name: str, text: str, expected: str):
    assert await _masked(pattern_name, text) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("pattern_name", "text"),
    [
        ("in_aadhaar", "aadhaar 2345 6789 0125"),
        ("in_aadhaar", "aadhaar 1234 5678 9012"),
        ("in_pan", "code ABCXK1234D"),
        ("in_pan", "GSTIN 22ABCPK1234D1ZJ"),
        ("in_gstin", "GSTIN 22ABCPK1234D1ZK"),
        ("in_ifsc", "word abcd0efghij"),
        ("in_upi_id", "ping rahul.k@okbank"),
        ("in_upi_id", "upi id rahul@example.com"),
        ("in_phone", "call 98765 43210"),
        ("in_phone_contextual", "order 9876543210"),
        ("in_phone_contextual", "mobile 5876543210"),
        ("in_driving_licence", "ref ZZ12 20110012345"),
        ("in_vehicle_registration", "as 1 in 1000 cases"),
        ("in_vehicle_registration", "or 2 to 1234 times"),
    ],
)
async def test_india_pattern_leaves_look_alike_untouched(pattern_name: str, text: str):
    assert await _masked(pattern_name, text) == text
