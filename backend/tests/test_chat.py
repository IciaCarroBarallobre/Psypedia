import unittest
from unittest.mock import Mock

from psypedia import create_app
from psypedia.providers import ChatProvider


class ChatTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app({"TESTING": True, "CHAT_PROVIDER": "mock"}).test_client()

    def assert_error(self, response, status, code):
        self.assertEqual(response.status_code, status)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(response.json["error"]["code"], code)
        self.assertIsInstance(response.json["error"]["message"], str)

    def test_valid_messages_return_an_explicit_mock_answer(self):
        for message in ("A question", "  A question  ", "¿Qué es la psicoterapia?\nOtra línea"):
            with self.subTest(message=message):
                response = self.client.post("/api/chat", json={"message": message})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "application/json")
                self.assertEqual(set(response.json), {"answer"})
                self.assertIsInstance(response.json["answer"], str)
                self.assertIn("Respuesta de demostración (mock)", response.json["answer"])

    def test_rejects_missing_empty_and_non_string_messages(self):
        for payload in ({}, {"message": ""}, {"message": " \n\t"},
                        {"message": None}, {"message": 42}, {"message": False},
                        {"message": []}, {"message": {}}, [], "question", 42):
            with self.subTest(payload=payload):
                self.assert_error(self.client.post("/api/chat", json=payload), 400, "invalid_message")

    def test_rejects_json_null(self):
        self.assert_error(self.client.post("/api/chat", data="null", content_type="application/json"), 400, "invalid_message")

    def test_rejects_malformed_or_empty_json(self):
        for body in ('{"message":', ''):
            with self.subTest(body=body):
                self.assert_error(self.client.post("/api/chat", data=body, content_type="application/json"), 400, "invalid_json")

    def test_requires_json_content_type(self):
        self.assert_error(self.client.post("/api/chat", data='{"message":"Question"}', content_type="text/plain"), 415, "unsupported_media_type")

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get("/api/chat").status_code, 405)


class ChatProviderIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.provider = Mock(spec=ChatProvider)
        self.provider.answer.return_value = "Test provider answer"
        self.client = create_app({"TESTING": True, "CHAT_PROVIDER": "mock"}, chat_provider=self.provider).test_client()

    def test_route_passes_trimmed_message_to_service_and_returns_answer(self):
        response = self.client.post("/api/chat", json={"message": "  Question  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"answer": "Test provider answer"})
        self.provider.answer.assert_called_once_with("Question")

    def test_invalid_input_never_calls_provider(self):
        for payload in ({}, {"message": " "}, {"message": 1}):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/chat", json=payload).status_code, 400)
        self.provider.answer.assert_not_called()


    def test_provider_is_scoped_to_each_application(self):
        other_client = create_app({"TESTING": True, "CHAT_PROVIDER": "mock"}).test_client()
        response = other_client.post("/api/chat", json={"message": "Question"})
        self.assertIn("Respuesta de demostración (mock)", response.json["answer"])
        self.provider.answer.assert_not_called()
