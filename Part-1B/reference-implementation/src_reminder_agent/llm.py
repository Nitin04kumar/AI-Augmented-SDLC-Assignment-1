"""Model clients. Secrets come from environment variables only - never from files in the repo.

REMINDER_PROVIDER = anthropic | openai | mock   (openai = any OpenAI-compatible endpoint:
OpenAI, Gemini's OpenAI-compat URL, Groq, Ollama, ...)
"""

import json
import os
import re
import time
import urllib.error
import urllib.request


class ModelServiceError(Exception):
    """Network/quota/auth/HTTP failure of the model service (NOT an application failure)."""


def _post(url: str, headers: dict, body: dict, timeout: int = 60, retries: int = 2) -> dict:
    if not url.startswith(("https://", "http://localhost", "http://127.0.0.1")):
        raise ModelServiceError("Refusing non-HTTPS endpoint")
    data = json.dumps(body).encode()
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")  # noqa: S310
        try:
            # URL scheme is allow-listed (https / localhost) at the top of this function.
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            if exc.code not in (429, 500, 502, 503, 529):
                break
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            last = str(exc)
        time.sleep(1.5 * (attempt + 1))
    raise ModelServiceError(last or "unknown model service error")


class AnthropicClient:
    def __init__(self):
        self.key = os.environ.get("ANTHROPIC_API_KEY")
        self.model = os.environ.get("REMINDER_MODEL", "claude-haiku-4-5")
        self.temperature = float(os.environ.get("REMINDER_TEMPERATURE", "0.3"))
        if not self.key:
            raise ModelServiceError("ANTHROPIC_API_KEY is not set")

    def describe(self) -> dict:
        return {"provider": "anthropic", "model": self.model, "temperature": self.temperature}

    def complete(self, system: str, user: str) -> str:
        body = {
            "model": self.model,
            "max_tokens": 500,
            "temperature": self.temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key": self.key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        out = _post("https://api.anthropic.com/v1/messages", headers, body)
        try:
            return "".join(b.get("text", "") for b in out["content"])
        except (KeyError, TypeError) as exc:
            raise ModelServiceError("Unexpected response shape") from exc


class OpenAICompatClient:
    def __init__(self):
        self.key = os.environ.get("OPENAI_API_KEY", "")
        self.base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.environ.get("REMINDER_MODEL", "gpt-4o-mini")
        self.temperature = float(os.environ.get("REMINDER_TEMPERATURE", "0.3"))

    def describe(self) -> dict:
        return {
            "provider": "openai-compatible",
            "base_url": self.base,
            "model": self.model,
            "temperature": self.temperature,
        }

    def complete(self, system: str, user: str) -> str:
        body = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        headers = {"content-type": "application/json"}
        if self.key:
            headers["authorization"] = f"Bearer {self.key}"
        out = _post(f"{self.base}/chat/completions", headers, body)
        try:
            return out["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelServiceError("Unexpected response shape") from exc


class MockClient:
    """Offline stand-in used ONLY to test the harness plumbing. Not valid evidence for Part 1B."""

    def describe(self) -> dict:
        return {"provider": "mock", "model": "regex-heuristic", "temperature": 0}

    def complete(self, system: str, user: str) -> str:  # noqa: ARG002
        from reminder_agent.mock_model import respond

        return respond(user)


def get_client():
    provider = os.environ.get("REMINDER_PROVIDER", "mock").lower()
    if provider == "anthropic":
        return AnthropicClient()
    if provider == "openai":
        return OpenAICompatClient()
    if provider == "mock":
        return MockClient()
    raise ModelServiceError(f"Unknown REMINDER_PROVIDER: {provider}")


def extract_json(text: str):
    """Return the first JSON object found in model text, or None."""
    cleaned = re.sub(r"```(?:json)?", "", text or "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(cleaned[start : end + 1])
    except ValueError:
        return None
