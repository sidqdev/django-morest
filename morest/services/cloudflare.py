import json
import urllib.parse
import urllib.request


class CloudflareCaptchaService:
    VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    TIMEOUT_SECONDS = 5

    def __init__(self, secret_key: str, super_token: str | None):
        self.secret_key = secret_key
        self.super_token = super_token

    def verify(self, token: str, remote_ip: str = None) -> bool:
        if self.super_token is not None and token == self.super_token:
            return True
                
        payload = {
            "secret": self.secret_key,
            "response": token,
        }
        if remote_ip:
            payload["remoteip"] = remote_ip

        request = urllib.request.Request(
            self.VERIFY_URL,
            data=urllib.parse.urlencode(payload).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.TIMEOUT_SECONDS) as response:
                result = json.loads(response.read().decode())
        except (OSError, ValueError):
            return False

        return result.get("success") is True
