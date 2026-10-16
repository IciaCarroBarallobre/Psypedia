"""Exercise the real HTTP path through Vite to Flask (requires running services)."""

import json
import os
import time
import unittest
from urllib.error import URLError
from urllib.request import urlopen


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
