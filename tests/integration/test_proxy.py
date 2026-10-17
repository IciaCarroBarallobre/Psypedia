"""Exercise the real HTTP path through Vite to Flask (requires running services)."""

import json
import os
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProxyIntegrationTest(unittest.TestCase):
    backend = os.environ.get("BACKEND_URL", "http://backend:5000")
    frontend = os.environ.get("FRONTEND_URL", "http://frontend:5173")

    @classmethod
    def setUpClass(cls):
        # Compose waits for Flask health; Vite still needs a bounded readiness wait.
        deadline = time.monotonic() + 30
        while True:
            try:
                with urlopen(f"{cls.frontend}/", timeout=2) as response:
                    if response.status == 200:
                        return
            except (URLError, TimeoutError, OSError):
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError("Frontend did not become ready within 30 seconds")
            time.sleep(0.5)

    def test_health_through_vite_matches_flask(self):
        for url in (self.backend, self.frontend):
            with self.subTest(url=url):
                with urlopen(f"{url}/api/health", timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.headers.get_content_type(), "application/json")
                    self.assertEqual(json.load(response), {"status": "ok"})

    def test_chat_answer_through_vite_matches_flask(self):
        answers = []
        for url in (self.backend, self.frontend):
            with self.subTest(url=url):
                request = Request(
                    f"{url}/api/chat",
                    data=json.dumps({"message": "What is ACT?"}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=130) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.headers.get_content_type(), "application/json")
                    answer = json.load(response)["answer"]
                    self.assertIsInstance(answer, str)
                    self.assertTrue(answer.strip())
                    if os.environ.get("CHAT_PROVIDER") == "mock":
                        self.assertIn("Respuesta de demostración (mock)", answer)
                    answers.append(answer)
        if os.environ.get("CHAT_PROVIDER") == "mock":
            self.assertEqual(answers[0], answers[1])

    def test_chat_validation_error_passes_through_vite(self):
        request = Request(
            f"{self.frontend}/api/chat",
            data=json.dumps({"message": " "}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=5)
        with caught.exception as response:
            self.assertEqual(response.code, 400)
            self.assertEqual(json.load(response)["error"]["code"], "invalid_message")
