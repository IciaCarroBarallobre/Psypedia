import unittest
from unittest.mock import Mock, patch

from psypedia.providers import ChatProvider
from psypedia.services.chat import ChatService


class ChatServiceTest(unittest.TestCase):
    def test_returns_the_injected_provider_answer_without_flask(self):
        provider = Mock(spec=ChatProvider)
        provider.answer.return_value = "Provider answer"
        self.assertEqual(ChatService(provider).answer("Question"), "Provider answer")
        provider.answer.assert_called_once_with("Question")

    def test_retriever_and_provider_can_be_replaced_independently(self):
        knowledge = Mock()
        knowledge.retrieve.return_value = [{
            "name": "Demo topic", "summary": "Selected demo facts",
            "source_title": "Demo source", "source_url": "https://example.org/demo",
        }]
        provider = Mock(spec=ChatProvider)
        provider.answer.return_value = "Generated answer"
        answer = ChatService(provider, knowledge).answer("Demo question")
        knowledge.retrieve.assert_called_once_with("Demo question")
        args, kwargs = provider.answer.call_args
        self.assertEqual(args, ("Demo question",))
        self.assertIn("Selected demo facts", kwargs["system_prompt"])
        self.assertIn("Devuelve solo la respuesta al usuario", kwargs["system_prompt"])
        self.assertEqual(answer, "Generated answer\n\nReferencias de las fichas / Card references:\n- Demo source: https://example.org/demo")

    def test_short_follow_up_reuses_the_previous_topic_and_history(self):
        from psypedia.knowledge import DemoKnowledgeBase
        provider = Mock(spec=ChatProvider)
        provider.answer.return_value = "Continued ACT explanation"
        history = [
            {"role": "user", "content": "Ni idea"},
            {"role": "assistant", "content": "¿Empezamos por ACT?"},
        ]
        answer = ChatService(provider, DemoKnowledgeBase()).answer("sí", history=history)
        self.assertTrue(answer.startswith("Continued ACT explanation"))
        self.assertEqual(provider.answer.call_args.kwargs["history"], history)
        self.assertEqual(provider.answer.call_args.args, ("sí",))
        self.assertIn("Acceptance and Commitment Therapy", provider.answer.call_args.kwargs["system_prompt"])

    def test_agreement_without_a_topic_requests_a_question_without_selecting_a_card(self):
        from psypedia.knowledge import DemoKnowledgeBase
        for message in ("Si", "sí!", "vale", "OK", "de acuerdo"):
            with self.subTest(message=message):
                provider = Mock(spec=ChatProvider)
                knowledge = Mock(wraps=DemoKnowledgeBase())
                answer = ChatService(provider, knowledge).answer(message)
                self.assertIn("una pregunta o un tema concreto", answer)
                self.assertNotIn("sus principios", answer)
                self.assertNotIn("Referencias", answer)
                knowledge.introductory_topic.assert_not_called()
                provider.answer.assert_not_called()

    def test_unrelated_history_does_not_make_agreement_a_therapy_request(self):
        from psypedia.knowledge import DemoKnowledgeBase
        provider = Mock(spec=ChatProvider)
        answer = ChatService(provider, DemoKnowledgeBase()).answer("sí", history=[
            {"role": "assistant", "content": "¿Qué te gustaría saber?"},
        ])
        self.assertIn("una pregunta o un tema concreto", answer)
        provider.answer.assert_not_called()

    def test_current_topic_takes_priority_over_previous_topic(self):
        from psypedia.knowledge import DemoKnowledgeBase
        provider = Mock(spec=ChatProvider)
        provider.answer.return_value = "New topic answer"
        ChatService(provider, DemoKnowledgeBase()).answer("¿Qué es DBT?", history=[
            {"role": "user", "content": "What is ACT?"},
        ])
        prompt = provider.answer.call_args.kwargs["system_prompt"]
        self.assertIn("Dialectical Behavior Therapy (DBT)", prompt)
        self.assertNotIn("Acceptance and Commitment Therapy (ACT)", prompt)

    def test_indecision_selects_an_introductory_card_instead_of_repeating_a_menu(self):
        from psypedia.knowledge import DemoKnowledgeBase
        for message in ("Ni idea", "No sé por dónde empezar"):
            with self.subTest(message=message):
                provider = Mock(spec=ChatProvider)
                provider.answer.return_value = "Introductory explanation"
                answer = ChatService(provider, DemoKnowledgeBase()).answer(message)
                self.assertTrue(answer.startswith("Introductory explanation"))
                self.assertIn("Cognitive Behavioral Therapy", provider.answer.call_args.kwargs["system_prompt"])

    def test_repeated_answer_gets_one_retry_with_same_history(self):
        from psypedia.knowledge import DemoKnowledgeBase
        provider = Mock(spec=ChatProvider)
        provider.answer.side_effect = ["¿Por dónde empezamos?", "Podemos empezar con una introducción."]
        history = [{"role": "assistant", "content": "¿Por dónde empezamos?"}]
        answer = ChatService(provider, DemoKnowledgeBase()).answer("Ni idea", history=history)
        self.assertTrue(answer.startswith("Podemos empezar con una introducción."))
        self.assertEqual(provider.answer.call_count, 2)
        self.assertTrue(all(call.args == ("Ni idea",) for call in provider.answer.call_args_list))
        self.assertIn("previous attempt repeated", provider.answer.call_args.kwargs["system_prompt"])
        self.assertEqual(provider.answer.call_args.kwargs["history"], history)

    def test_repetition_is_not_returned_after_retry_fails(self):
        from psypedia.knowledge import DemoKnowledgeBase
        from psypedia.providers import ProviderInvalidResponse
        provider = Mock(spec=ChatProvider)
        provider.answer.return_value = "La misma respuesta."
        with self.assertRaises(ProviderInvalidResponse):
            ChatService(provider, DemoKnowledgeBase()).answer("Ni idea", history=[
                {"role": "assistant", "content": "La misma respuesta!"},
            ])
        self.assertEqual(provider.answer.call_count, 2)

    @patch("psypedia.services.chat.monotonic", side_effect=[0, 11])
    def test_slow_repeated_answer_is_not_retried(self, clock):
        from psypedia.knowledge import DemoKnowledgeBase
        from psypedia.providers import ProviderInvalidResponse
        provider = Mock(spec=ChatProvider)
        provider.answer.return_value = "Previous answer"
        with self.assertRaises(ProviderInvalidResponse):
            ChatService(provider, DemoKnowledgeBase()).answer("Ni idea", history=[
                {"role": "assistant", "content": "Previous answer"},
            ])
        provider.answer.assert_called_once()
