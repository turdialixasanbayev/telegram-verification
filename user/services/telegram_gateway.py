import requests

from django.conf import settings


class TelegramGatewayService:
    BASE_URL = "https://gatewayapi.telegram.org"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.TELEGRAM_GATEWAY_TOKEN}",
            "Content-Type": "application/json",
        }

    def _post(self, endpoint, payload):
        response = requests.post(
            f"{self.BASE_URL}/{endpoint}",
            headers=self.headers,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        if not data["ok"]:
            raise RuntimeError(data)

        return data["result"]

    def send_verification_code(self, phone_number):
        return self._post(
            "sendVerificationMessage",
            {
                "phone_number": phone_number,
                "code_length": 6,
                "ttl": 300,
            },
        )

    def check_verification_code(self, request_id, code):
        return self._post(
            "checkVerificationStatus",
            {
                "request_id": request_id,
                "code": code,
            },
        )
