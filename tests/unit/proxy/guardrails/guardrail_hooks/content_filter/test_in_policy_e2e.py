import json
import os
from typing import Final

import pytest

import litellm
from litellm.proxy.guardrails.guardrail_hooks.litellm_content_filter.content_filter import (
    ContentFilterGuardrail,
)
from litellm.types.guardrails import ContentFilterPattern

_PACKAGE_DIR: Final = os.path.dirname(litellm.__file__)
_TEMPLATE_FILES: Final = (
    os.path.join(os.path.dirname(_PACKAGE_DIR), "policy_templates.json"),
    os.path.join(_PACKAGE_DIR, "policy_templates_backup.json"),
)


def _india_template_guardrails(template_file: str) -> tuple[ContentFilterGuardrail, ...]:
    with open(template_file) as f:
        templates: Final = json.load(f)
    template: Final = next(t for t in templates if t["id"] == "india-pii-protection")
    return tuple(
        ContentFilterGuardrail(
            guardrail_name=definition["guardrail_name"],
            patterns=[ContentFilterPattern.model_validate(p) for p in definition["litellm_params"]["patterns"]],
            pattern_redaction_format=definition["litellm_params"]["pattern_redaction_format"],
        )
        for definition in template["guardrailDefinitions"]
    )


async def _apply_all(guardrails: tuple[ContentFilterGuardrail, ...], text: str) -> str:
    if not guardrails:
        return text
    guardrailed_inputs: Final = await guardrails[0].apply_guardrail(
        inputs={"texts": [text]}, request_data={}, input_type="request"
    )
    return await _apply_all(guardrails[1:], guardrailed_inputs["texts"][0])


@pytest.mark.asyncio
@pytest.mark.parametrize("template_file", _TEMPLATE_FILES)
async def test_india_template_masks_every_identifier_in_a_kyc_prompt(template_file: str):
    prompt: Final = (
        "Verify customer. Aadhaar 2345 6789 0124, PAN ABCPK1234D, GSTIN 22ABCPK1234D1ZJ, "
        "IFSC ABCD0123456, upi id rahul.k@okbank, card 4532 0151 1283 0366, "
        "mobile number 9876543210, alt +91 98765 43210, email rahul@example.com, "
        "DL MH12 20110012345, car MH 12 AB 1234"
    )

    masked: Final = await _apply_all(_india_template_guardrails(template_file), prompt)

    assert masked == (
        "Verify customer. Aadhaar [IN_AADHAAR_REDACTED], PAN [IN_PAN_REDACTED], GSTIN [IN_GSTIN_REDACTED], "
        "IFSC [IN_IFSC_REDACTED], upi id [IN_UPI_ID_REDACTED], card [CREDIT_CARD_REDACTED], "
        "mobile number [IN_PHONE_CONTEXTUAL_REDACTED], alt [IN_PHONE_REDACTED], email [EMAIL_REDACTED], "
        "DL [IN_DRIVING_LICENCE_REDACTED], car [IN_VEHICLE_REGISTRATION_REDACTED]"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("template_file", _TEMPLATE_FILES)
async def test_india_template_leaves_clean_prompt_untouched(template_file: str):
    prompt: Final = "Order 2345 6789 0125 shipped as 1 in 1000 parcels, ref ABCXK1234D, total 9876543210 paise"

    assert await _apply_all(_india_template_guardrails(template_file), prompt) == prompt
