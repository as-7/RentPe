from typing import Iterable, Optional

import httpx

from app.core.config import settings


class WhatsAppConfigurationError(RuntimeError):
    pass


class WhatsAppSendError(RuntimeError):
    pass


def is_configured() -> bool:
    return all(
        [
            settings.WHATSAPP_ENABLED,
            settings.WHATSAPP_PHONE_NUMBER_ID,
            settings.WHATSAPP_ACCESS_TOKEN,
            settings.WHATSAPP_TEMPLATE_NAME,
        ]
    )


def normalize_phone_number(raw_number: str) -> str:
    digits = "".join(ch for ch in raw_number if ch.isdigit())
    if not digits:
        raise ValueError("No digits found in mobile number")

    if raw_number.strip().startswith("+"):
        return digits

    if digits.startswith("00"):
        return digits[2:]

    default_country_code = settings.WHATSAPP_DEFAULT_COUNTRY_CODE.strip()
    if len(digits) == 10 and default_country_code:
        return f"{default_country_code}{digits}"

    return digits


async def send_template_message(
    recipient_phone: str,
    body_parameters: Iterable[str],
    template_name: Optional[str] = None,
    template_language: Optional[str] = None,
) -> str:
    if not is_configured():
        raise WhatsAppConfigurationError("WhatsApp settings are incomplete")

    normalized_phone = normalize_phone_number(recipient_phone)
    payload = {
        "messaging_product": "whatsapp",
        "to": normalized_phone,
        "type": "template",
        "template": {
            "name": template_name or settings.WHATSAPP_TEMPLATE_NAME,
            "language": {
                "policy": "deterministic",
                "code": template_language or settings.WHATSAPP_TEMPLATE_LANGUAGE,
            },
        },
    }

    parameters = [
        {
            "type": "text",
            "text": str(value),
        }
        for value in body_parameters
    ]
    if parameters:
        payload["template"]["components"] = [
            {
                "type": "body",
                "parameters": parameters,
            }
        ]

    url = f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code >= 400:
        raise WhatsAppSendError(f"WhatsApp send failed ({response.status_code}): {response.text}")

    data = response.json()
    messages = data.get("messages") or []
    if not messages:
        raise WhatsAppSendError(f"WhatsApp send succeeded without message id: {data}")
    return messages[0]["id"]
