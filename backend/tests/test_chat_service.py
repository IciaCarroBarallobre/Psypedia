import unittest
from unittest.mock import Mock

from psypedia.providers import ChatProvider
from psypedia.services.chat import ChatService


class ChatServiceTest(unittest.TestCase):
    def test_returns_the_injected_provider_answer_without_flask(self):
        provider = Mock(spec=ChatProvider)
        provider.answer.return_value = "Provider answer"
        self.assertEqual(ChatService(provider).answer("Question"), "Provider answer")
        provider.answer.assert_called_once_with("Question")
