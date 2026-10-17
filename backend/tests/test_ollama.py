import io
import json
import os
import unittest
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from psypedia import create_app
from psypedia.providers.ollama import OllamaChatProvider
from psypedia.providers import ProviderInvalidResponse, ProviderTimeout, ProviderUnavailable


class OllamaProviderTest(unittest.TestCase):
    def setUp(self):
        self.provider = OllamaChatProvider("http://ollama:11434/", "test-model", 12)

    @patch("psypedia.providers.ollama.urlopen")
    def test_posts_configured_model_and_supplied_system_prompt(self, open_url):
        open_url.return_value = io.BytesIO(json.dumps({
            "done": True, "message": {"content": " Generated answer "}
        }).encode())
        self.assertEqual(self.provider.answer("Question", system_prompt="Prepared instructions and selected cards"), "Generated answer")
        request = open_url.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual(request.full_url, "http://ollama:11434/api/chat")
        self.assertEqual(request.method, "POST")
        self.assertEqual(open_url.call_args.kwargs["timeout"], 12)
        self.assertEqual(body["model"], "test-model")
        self.assertFalse(body["stream"])
        self.assertFalse(body["think"])
        self.assertEqual(body["keep_alive"], "15m")
        self.assertEqual(body["messages"], [
            {"role": "system", "content": "Prepared instructions and selected cards"},
            {"role": "user", "content": "Question"},
        ])

    @patch("psypedia.providers.ollama.urlopen")
    def test_adapter_transmits_prompt_without_adding_application_instructions(self, open_url):
        open_url.return_value = io.BytesIO(b'{"done":true,"message":{"content":"Answer"}}')
        self.provider.answer("What is ACT?", system_prompt="Selected ACT card")
        body = json.loads(open_url.call_args.args[0].data)
        self.assertEqual(body["messages"][0]["content"], "Selected ACT card")
        self.assertNotIn("No curated clinical documents", body["messages"][0]["content"])

    @patch("psypedia.providers.ollama.urlopen")
    def test_sends_history_between_system_prompt_and_current_message(self, open_url):
        open_url.return_value = io.BytesIO(b'{"done":true,"message":{"content":"Continued answer"}}')
        history = [
            {"role": "user", "content": "Ni idea"},
            {"role": "assistant", "content": "Shall we start with ACT?"},
        ]
        self.provider.answer("yes", system_prompt="Trusted instructions", history=history)
        body = json.loads(open_url.call_args.args[0].data)
        self.assertEqual(body["messages"], [
            {"role": "system", "content": "Trusted instructions"},
            *history, {"role": "user", "content": "yes"},
        ])


    @patch("psypedia.providers.ollama.urlopen")
    def test_qwen3_disables_thinking_without_changing_user_message(self, open_url):
        open_url.return_value = io.BytesIO(b'{"done":true,"message":{"content":"Hola"}}')
        provider = OllamaChatProvider("http://ollama:11434", "qwen3:4b", 12)
        self.assertEqual(provider.answer("hola"), "Hola")
        body = json.loads(open_url.call_args.args[0].data)
        self.assertTrue(body["messages"][0]["content"].endswith("/no_think"))
        self.assertEqual(body["messages"][1]["content"], "hola")

    @patch("psypedia.providers.ollama.urlopen")
    def test_only_final_content_is_returned(self, open_url):
        for content in ("Hola", "<think>Internal reasoning</think>Hola",
                        "Internal reasoning</think>Hola"):
            with self.subTest(content=content):
                open_url.return_value = io.BytesIO(json.dumps({
                    "done": True,
                    "message": {"content": content, "thinking": "Private reasoning"},
                }).encode())
                self.assertEqual(self.provider.answer("hola"), "Hola")
        for content in ("<think>Unfinished reasoning", "<think>Reasoning only</think>"):
            with self.subTest(content=content):
                open_url.return_value = io.BytesIO(json.dumps({
                    "done": True, "message": {"content": content},
                }).encode())
                with self.assertRaises(ProviderInvalidResponse):
                    self.provider.answer("hola")

    @patch("psypedia.providers.ollama.urlopen")
    def test_connection_and_timeout_errors(self, open_url):
        for failure, expected in [
            (URLError("connection refused"), ProviderUnavailable),
            (TimeoutError(), ProviderTimeout),
            (URLError(TimeoutError()), ProviderTimeout),
            (HTTPError("http://ollama", 404, "missing model", {}, None), ProviderUnavailable),
        ]:
            with self.subTest(failure=failure):
                open_url.side_effect = failure
                with self.assertRaises(expected):
                    self.provider.answer("Question")

    @patch("psypedia.providers.ollama.urlopen")
    def test_rejects_invalid_and_incomplete_answers(self, open_url):
        for body in ('not json', 'null', '{}', '{"message":null}',
                     '{"done":true,"message":{"content":" "}}',
                     '{"done":true,"done_reason":"length","message":{"content":"Cut off answer"}}',
                     '{"done":false,"message":{"content":"partial"}}'):
            with self.subTest(body=body):
                open_url.return_value = io.BytesIO(body.encode())
                with self.assertRaises(ProviderInvalidResponse):
                    self.provider.answer("Question")

    def test_factory_uses_explicit_configuration(self):
        app = create_app({
            "CHAT_PROVIDER": "ollama", "OLLAMA_BASE_URL": "http://ollama:11434",
            "OLLAMA_MODEL": "chosen", "OLLAMA_TIMEOUT": 30,
        })
        provider = app.extensions["chat_service"].provider
        self.assertIsInstance(provider, OllamaChatProvider)
        self.assertEqual(provider.model, "chosen")
        self.assertEqual(provider.timeout, 30)

    @patch("psypedia.providers.ollama.urlopen")
    def test_endpoint_maps_provider_failures_without_exposing_details(self, open_url):
        client = create_app({
            "TESTING": True, "CHAT_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://ollama:11434",
            "OLLAMA_MODEL": "test-model", "OLLAMA_TIMEOUT": 12,
        }).test_client()
        for failure, status, code in [
            (URLError("private internal details"), 503, "provider_unavailable"),
            (TimeoutError(), 504, "provider_timeout"),
        ]:
            with self.subTest(code=code):
                open_url.side_effect = failure
                response = client.post("/api/chat", json={"message": "What is ACT?"})
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json["error"]["code"], code)
                self.assertNotIn("private internal details", response.get_data(as_text=True))
        open_url.side_effect = None
        open_url.return_value = io.BytesIO(b'{}')
        response = client.post("/api/chat", json={"message": "What is ACT?"})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json["error"]["code"], "invalid_provider_response")


class RequiredConfigurationTest(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_provider_must_be_explicit(self):
        with self.assertRaisesRegex(ValueError, "CHAT_PROVIDER"):
            create_app()

    @patch.dict(os.environ, {}, clear=True)
    def test_mock_runs_without_ollama_configuration(self):
        app = create_app({"CHAT_PROVIDER": "mock"})
        self.assertEqual(app.test_client().get("/api/health").status_code, 200)

    @patch.dict(os.environ, {}, clear=True)
    def test_ollama_requires_each_setting(self):
        config = {
            "CHAT_PROVIDER": "ollama", "OLLAMA_BASE_URL": "http://ollama:11434",
            "OLLAMA_MODEL": "test-model", "OLLAMA_TIMEOUT": 12,
        }
        for key in ("OLLAMA_BASE_URL", "OLLAMA_MODEL", "OLLAMA_TIMEOUT"):
            for value in (None, "", " "):
                with self.subTest(key=key, value=value):
                    with self.assertRaisesRegex(ValueError, key):
                        create_app({**config, key: value})
