import unittest

from psypedia import create_app


class HealthTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app({"TESTING": True}).test_client()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})
        self.assertEqual(response.mimetype, "application/json")

    def test_health_does_not_accept_post(self):
        self.assertEqual(self.client.post("/api/health").status_code, 405)

    def test_chat_is_not_implemented(self):
        self.assertEqual(self.client.post("/api/chat").status_code, 404)
