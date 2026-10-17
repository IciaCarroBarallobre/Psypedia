"""Local Ollama adapter. No prompts or upstream error bodies are logged."""

import json
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import ProviderInvalidResponse, ProviderTimeout, ProviderUnavailable

class OllamaChatProvider:
    def __init__(self, base_url: str, model: str, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def answer(self, message: str, *, system_prompt: str | None = None,
               history: list[dict[str, str]] | None = None) -> str:
        system_prompt = system_prompt or ""
        # Qwen3 also accepts an explicit non-thinking instruction in its template.
        if self.model.split(":", 1)[0] == "qwen3":
            system_prompt += "\n/no_think"
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps({
                "model": self.model,
                "stream": False,
                "think": False,
                "keep_alive": "15m",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *(history or []),
                    {"role": "user", "content": message},
                ],
                "options": {"temperature": 0.2, "num_predict": 384},
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except HTTPError as error:
            error.close()
            raise ProviderUnavailable() from None
        except (TimeoutError, socket.timeout):
            raise ProviderTimeout() from None
        except URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise ProviderTimeout() from None
            raise ProviderUnavailable() from None
        except OSError:
            raise ProviderUnavailable() from None
        except (ValueError, UnicodeError):
            raise ProviderInvalidResponse() from None

        if not isinstance(payload, dict) or not isinstance(payload.get("message"), dict):
            raise ProviderInvalidResponse()
        answer = payload["message"].get("content")
        if (not isinstance(answer, str) or not answer.strip()
                or payload.get("done") is not True or payload.get("done_reason") == "length"):
            raise ProviderInvalidResponse()
        # Never forward explicitly marked reasoning from older model templates.
        answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL)
        if "</think>" in answer:
            answer = answer.rsplit("</think>", 1)[1]
        if "<think>" in answer or not answer.strip():
            raise ProviderInvalidResponse()
        return answer.strip()
