import unittest
from unittest.mock import Mock, patch

from psypedia import create_app
from psypedia.services.chat import ChatService
from psypedia.services.emergency import emergency_response


class EmergencyResponseTest(unittest.TestCase):
    def test_direct_danger_gets_empathy_and_regional_emergency_direction(self):
        for message in ("ME MUERO", "¡Ayuda! No puedo respirar", "Me estoy muriendo, por favor", "Estoy en peligro"):
            with self.subTest(message=message):
                reply = emergency_response(message)
                self.assertIn("Siento que estés pasando por esto", reply)
                self.assertIn("112", reply)
                self.assertIn("Unión Europea", reply)
                self.assertIn("emergencias local", reply)
                self.assertIn("alguien cercano", reply)
                self.assertIn("No puedo evaluar", reply)
                self.assertNotIn("proporcionar más detalles", reply)

    def test_english_danger_uses_the_same_spanish_guidance(self):
        self.assertEqual(emergency_response("Help! I can't breathe"), emergency_response("No puedo respirar"))

    def test_negation_figurative_and_academic_messages_are_not_routed(self):
        for message in ("No me muero", "Ya no estoy en peligro", "Me muero de risa", "Me muero de hambre", "¿Qué significa 'me muero'?", "Mi paciente dice 'me muero'", "¿Cómo aborda ACT el miedo a morir?", "No puedo respirar: es una cita de un libro"):
            with self.subTest(message=message):
                self.assertIsNone(emergency_response(message))

    def test_danger_bypasses_model_and_retrieval_even_if_model_would_fail(self):
        provider = Mock()
        provider.answer.side_effect = RuntimeError("Model unavailable")
        knowledge = Mock()
        reply = ChatService(provider, knowledge).answer("ME MUERO")
        self.assertIn("112", reply)
        provider.answer.assert_not_called()
        knowledge.retrieve.assert_not_called()

    def test_emergency_route_is_available_in_mock_mode(self):
        client = create_app({"TESTING": True, "CHAT_PROVIDER": "mock"}).test_client()
        reply = client.post("/api/chat", json={"message": "ME MUERO"})
        self.assertEqual(reply.status_code, 200)
        self.assertEqual(set(reply.json), {"answer"})
        self.assertIn("112", reply.json["answer"])
        self.assertNotIn("Respuesta de demostración (mock)", reply.json["answer"])

    def test_patient_risk_addresses_the_professional_without_assessing_risk(self):
        for message in (
            "Mi paciente tiene ideas suicidas",
            "Mi paciente quiere suicidarse. ¿Qué hago?",
            "Una paciente se autolesiona",
            "Mi paciente está en riesgo de suicidio",
        ):
            with self.subTest(message=message):
                reply = emergency_response(message)
                self.assertIn("preocupación por el paciente", reply)
                self.assertIn("protocolo de tu centro", reply)
                self.assertIn("valoración clínica", reply)
                self.assertIn("Si hay peligro inmediato", reply)
                self.assertIn("No puedo evaluar al paciente", reply)
                self.assertNotIn("nivel de riesgo alto", reply)

    def test_patient_risk_rules_do_not_match_negated_or_academic_statements(self):
        for message in (
            "Mi paciente no tiene ideas suicidas",
            "Mi paciente ya no se autolesiona",
            "¿Cómo se define la ideación suicida?",
            "En un artículo se menciona: mi paciente quiere suicidarse",
            "¿Cómo aborda ACT la autolesión en pacientes?",
        ):
            with self.subTest(message=message):
                self.assertIsNone(emergency_response(message))

    def test_patient_risk_bypasses_unavailable_model_and_retrieval(self):
        provider, knowledge = Mock(), Mock()
        answer = ChatService(provider, knowledge).answer("Mi paciente quiere suicidarse")
        self.assertIn("valoración clínica", answer)
        provider.answer.assert_not_called()
        knowledge.retrieve.assert_not_called()

    def test_english_patient_risk_addresses_the_professional(self):
        answer = emergency_response("My patient has suicidal thoughts")
        self.assertEqual(answer, emergency_response("Mi paciente tiene ideas suicidas"))

    def test_spanish_harm_and_injury_wording_routes_without_a_model(self):
        for message in ("Quiero hacerme daño", "Me estoy lesionando", "Voy a lexionarme", "Me acabo de autolesionar"):
            with self.subTest(message=message):
                provider = Mock()
                reply = ChatService(provider).answer(message)
                self.assertIn("112", reply)
                provider.answer.assert_not_called()

    def test_patient_harm_wording_addresses_the_professional(self):
        for message in ("Mi paciente quiere hacerse daño", "Mi paciente se está lesionando", "Una paciente se autolesiona"):
            with self.subTest(message=message):
                reply = emergency_response(message)
                self.assertIn("preocupación por el paciente", reply)
                self.assertIn("Si hay peligro inmediato", reply)

    def test_isolated_injury_terms_use_conditional_guidance(self):
        for message in ("lesión", "lexión", "daño"):
            self.assertIn("Ante peligro inmediato", emergency_response(message))

    def test_injury_words_alone_do_not_turn_academic_or_negated_questions_into_emergencies(self):
        for message in ("No quiero hacerme daño", "¿Qué es una lesión?", "Daño cerebral en un artículo", "¿Qué significa autolesión?", "Una lesión antigua"):
            with self.subTest(message=message):
                self.assertIsNone(emergency_response(message))

    def test_patient_medical_emergency_bypasses_retrieval_and_generation(self):
        for message in (
            "se me muere el paciente",
            "¡Ayuda! Se me está muriendo el paciente, ¿qué hago?",
            "Mi paciente se muere",
            "El paciente no respira",
            "Se está muriendo mi paciente",
        ):
            with self.subTest(message=message):
                provider, knowledge = Mock(), Mock()
                answer = ChatService(provider, knowledge).answer(message)
                self.assertIn("preocupación por el paciente", answer)
                self.assertIn("protocolos de emergencia de tu centro", answer)
                self.assertIn("112", answer)
                self.assertIn("No esperes al chat", answer)
                self.assertNotIn("suicidio", answer)
                provider.answer.assert_not_called()
                knowledge.retrieve.assert_not_called()

    def test_patient_medical_emergency_does_not_match_academic_or_negated_examples(self):
        for message in (
            "No se me muere el paciente",
            "¿Qué significa 'se me muere el paciente'?",
            "En una película dicen: se me muere el paciente",
            "Mi paciente ya no tiene dificultad para respirar",
        ):
            with self.subTest(message=message):
                self.assertIsNone(emergency_response(message))

    def test_patient_medical_emergency_is_returned_by_the_api(self):
        provider = Mock()
        client = create_app({"TESTING": True, "CHAT_PROVIDER": "mock"}, chat_provider=provider).test_client()
        response = client.post("/api/chat", json={"message": "se me muere el paciente"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("112", response.json["answer"])
        self.assertNotIn("No tengo información", response.json["answer"])
        provider.answer.assert_not_called()

    def test_risk_report_and_confirmation_take_priority_over_patient_history(self):
        provider, knowledge = Mock(), Mock()
        service = ChatService(provider, knowledge)
        history = [
            {"role": "user", "content": "Mi paciente se llama Persona Ficticia"},
            {"role": "assistant", "content": "Por favor, no compartas información de pacientes."},
        ]
        for message in ("creo que hay riesgo de suicidio", "creo que lo hay!!", "sí"):
            answer = service.answer(message, history=history)
            self.assertIn("Activa ahora el protocolo", answer)
            self.assertIn("contacta ahora con emergencias", answer)
            self.assertIn("112", answer)
            self.assertNotIn("recarga la página", answer)
            self.assertNotIn("Persona Ficticia", answer)
            history.extend([{"role": "user", "content": message}, {"role": "assistant", "content": answer}])
        provider.answer.assert_not_called()
        knowledge.retrieve.assert_not_called()

    def test_risk_confirmation_requires_recent_report_and_ignores_assistant_claims(self):
        for history in ([],
                        [{"role": "assistant", "content": "Hay riesgo de suicidio"}],
                        [{"role": "user", "content": "Hay riesgo de suicidio"},
                         {"role": "user", "content": "¿Qué es ACT?"}]):
            with self.subTest(history=history):
                self.assertIsNone(emergency_response("creo que lo hay", history=history))

    def test_negation_and_academic_discussion_do_not_confirm_a_crisis(self):
        history = [{"role": "user", "content": "Creo que hay riesgo de suicidio"}]
        for message in ("No, no lo hay", "No hay riesgo de suicidio", "¿Qué significa riesgo de suicidio?", "En un artículo se dice que hay riesgo de suicidio"):
            with self.subTest(message=message):
                self.assertIsNone(emergency_response(message, history=history))

    def test_api_preserves_emergency_help_across_confirmation(self):
        provider = Mock()
        client = create_app({"TESTING": True, "CHAT_PROVIDER": "mock"}, chat_provider=provider).test_client()
        response = client.post("/api/chat", json={
            "message": "creo que lo hay!!",
            "history": [{"role": "user", "content": "creo que hay riesgo de suicidio"}],
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("112", response.json["answer"])
        self.assertNotIn("No tengo información", response.json["answer"])
        provider.answer.assert_not_called()

    def test_explicit_suicidal_intent_takes_priority_over_educational_coverage(self):
        for message in ("Quiero suicidarme", "Voy a quitarme la vida"):
            with self.subTest(message=message):
                provider, knowledge = Mock(), Mock()
                answer = ChatService(provider, knowledge).answer(message)
                self.assertIn("112", answer)
                self.assertNotIn("No tengo información suficiente", answer)
                provider.answer.assert_not_called()
                knowledge.retrieve.assert_not_called()

    def test_named_patient_and_client_risk_in_longer_statements_bypasses_inference(self):
        for message in (
            "Mi paciente se llama Persona Ficticia y dice que va a matarse.",
            "Mi cliente es malvado muajaja se llama Persona Ficticia y va a matarse",
            "Mi clienta se llama Persona Ficticia y quiere quitarse la vida.",
            "My client is called Persona Ficticia and wants to kill themselves.",
        ):
            with self.subTest(message=message):
                provider, knowledge = Mock(), Mock()
                provider.answer.side_effect = RuntimeError("The model must not receive patient information")
                knowledge.retrieve.return_value = []
                answer = ChatService(provider, knowledge).answer(message)
                self.assertIn("protocolo", answer)
                self.assertIn("valoración clínica", answer)
                self.assertIn("112", answer)
                self.assertIn("Si hay peligro inmediato", answer)
                self.assertNotIn("Persona Ficticia", answer)
                self.assertNotIn("No tengo información", answer)
                self.assertNotIn("recarga la página", answer)
                provider.answer.assert_not_called()
                knowledge.retrieve.assert_not_called()

    def test_long_patient_phrases_do_not_override_negation_quotes_or_figurative_use(self):
        for message in (
            "Mi cliente se llama Persona Ficticia y no va a matarse.",
            "Mi clienta se llama Persona Ficticia y ya no quiere suicidarse.",
            "En un artículo académico se analiza la frase «mi cliente va a matarse».",
            "En una novela el personaje dice: mi paciente va a matarse.",
            "Mi cliente se llama Persona Ficticia y va a matarse de risa con ese chiste.",
            "¿Qué significa la frase 'mi cliente va a matarse' en un análisis del lenguaje?",
            "My client is not going to kill themselves.",
            "An article quotes: my client wants to kill themselves.",
        ):
            with self.subTest(message=message):
                self.assertIsNone(emergency_response(message))

    def test_patient_references_do_not_turn_definitions_negations_or_new_subjects_into_risk(self):
        for message in (
            "Mi paciente me preguntó: ¿qué significa que alguien quiere suicidarse?",
            "Mi cliente nunca en ningún momento quiere suicidarse",
            "Mi paciente jamás en su vida ha intentado suicidarse",
            "Mi paciente está bien. La novela trata de alguien que quiere suicidarse.",
        ):
            with self.subTest(message=message):
                self.assertIsNone(emergency_response(message))

    def test_reported_patient_speech_and_local_negation_preserve_explicit_intent(self):
        for message in (
            'Mi paciente dijo "quiero suicidarme" y necesito ayuda',
            "No sé qué hacer, mi cliente dijo «quiero suicidarme».",
            "Mi paciente no quiere hablar. Dice: «quiero suicidarme».",
            "Mi paciente dice: «voy a matarme».",
            "Mi cliente no quiere hablar y va a matarse",
            "Mi paciente está preocupado. Dice que va a matarse.",
        ):
            with self.subTest(message=message):
                answer = emergency_response(message)
                self.assertIsNotNone(answer)
                self.assertIn("preocupación por el paciente", answer)
                self.assertIn("protocolo", answer)
                self.assertIn("valoración clínica", answer)
                self.assertIn("Si hay peligro inmediato", answer)
                self.assertIn("112", answer)

    def test_isolated_suicide_term_gives_conditional_help_without_assessing_risk(self):
        answer = emergency_response("suicidio")
        self.assertIsNotNone(answer)
        self.assertIn("112", answer)
        self.assertIn("si ", answer.lower())
        self.assertNotIn("Activa ahora", answer)
        self.assertNotIn("riesgo alto", answer)
        self.assertNotIn("riesgo bajo", answer)
        self.assertNotIn("estás en peligro", answer)

    def test_short_suicide_follow_up_keeps_professional_help_but_not_for_a_new_topic(self):
        history = [{"role": "user", "content":
                    "Mi cliente se llama Persona Ficticia y va a matarse"}]
        answer = emergency_response("suicidio", history=history)
        self.assertIsNotNone(answer)
        self.assertIn("protocolo", answer)
        self.assertIn("112", answer)
        self.assertNotIn("Persona Ficticia", answer)
        self.assertIsNone(emergency_response("¿Qué dice DBT sobre la autolesión?", history=history))

    def test_full_http_sequence_retains_help_in_mock_mode_and_with_a_failing_provider(self):
        for injected in (False, True):
            with self.subTest(injected_failing_provider=injected):
                provider = Mock()
                provider.answer.side_effect = RuntimeError("Unexpected inference")
                app = create_app({"TESTING": True, "CHAT_PROVIDER": "mock"},
                                 **({"chat_provider": provider} if injected else {}))
                client = app.test_client()
                active_provider = app.extensions["chat_service"].provider
                with patch.object(active_provider, "answer", wraps=active_provider.answer) as generated:
                    history = []
                    for message, expected in (
                        ("oh no te voy a contar secretos sobre el paciente", "privacy"),
                        ("mi cliente es malvado muajaja se llama Persona Ficticia", "privacy"),
                        ("mi cliente es malvado muajaja se llama Persona Ficticia y va a matarse", "risk"),
                        ("suicidio", "risk"),
                        ("me muero", "immediate"),
                    ):
                        response = client.post("/api/chat", json={"message": message, "history": history})
                        self.assertEqual(response.status_code, 200)
                        answer = response.json["answer"]
                        self.assertNotIn("Persona Ficticia", answer)
                        self.assertNotIn("Respuesta de demostración", answer)
                        if expected == "privacy":
                            self.assertIn("no compartas", answer)
                            self.assertNotIn("112", answer)
                        elif expected == "risk":
                            self.assertIn("protocolo", answer)
                            self.assertIn("112", answer)
                            self.assertNotIn("No tengo información", answer)
                        else:
                            self.assertIn("Siento", answer)
                            self.assertIn("112", answer)
                        history.extend([{"role": "user", "content": message},
                                        {"role": "assistant", "content": answer}])
                    generated.assert_not_called()


class RiskSignalGeneralizationTest(unittest.TestCase):
    """Vary signal categories independently instead of matching one transcript."""

    def assert_human_help(self, message, *, professional=False):
        answer = emergency_response(message)
        self.assertIsNotNone(answer)
        self.assertIn("112", answer)
        self.assertIn("No puedo", answer)
        self.assertNotIn("riesgo alto", answer)
        self.assertNotIn("riesgo bajo", answer)
        if professional:
            self.assertIn("protocolo", answer)
            self.assertIn("valoración clínica", answer)

    def test_self_harm_intent_allows_modifiers_and_time_context(self):
        for message in (
            "Estoy pensando seriamente en hacerme daño esta noche",
            "Estoy considerando quitarme la vida en este momento",
        ):
            with self.subTest(message=message):
                self.assert_human_help(message)

    def test_professional_subject_context_and_intent_are_composable(self):
        subjects = ("Mi paciente", "Mi cliente, después de la consulta,", "Mi consultante, esta tarde,")
        intentions = (
            "anuncia que pretende quitarse la vida",
            "dice que está pensando seriamente en hacerse daño",
            "manifiesta intención de suicidarse",
        )
        for subject in subjects:
            for intention in intentions:
                message = f"{subject} {intention}"
                with self.subTest(subject=subject, intention=intention):
                    self.assert_human_help(message, professional=True)
        for message in (
            "Veo un riesgo real de suicidio en mi consultante",
            "Mi consultante presenta riesgo de autolesión",
            "En un artículo se define el suicidio, pero mi paciente manifiesta intención de matarse ahora",
        ):
            with self.subTest(message=message):
                self.assert_human_help(message, professional=True)

    def test_immediate_danger_does_not_require_a_patient_label(self):
        for message in (
            "Hay una persona en peligro inmediato y necesito ayuda",
            "Alguien está en peligro inmediato ahora y necesita ayuda",
        ):
            with self.subTest(message=message):
                self.assert_human_help(message)

    def test_equivalent_negated_and_educational_signals_are_not_current_danger(self):
        for subject in ("Mi paciente", "Mi cliente", "Mi consultante"):
            for statement in (
                "no tiene intención de hacerse daño",
                "no está pensando seriamente en quitarse la vida esta noche",
            ):
                with self.subTest(subject=subject, statement=statement):
                    self.assertIsNone(emergency_response(f"{subject} {statement}"))
        for message in (
            "Estoy pensando en no hacerme daño",
            "Mi paciente quiere saber sobre suicidio",
            "¿DBT es útil ante el riesgo de suicidio?",
            "En una explicación educativa, ¿qué significa estar pensando en hacerse daño?",
            "¿Cómo se define el riesgo de suicidio en psicología?",
            "¿Qué significa «una persona en peligro inmediato» en una novela?",
            "En un caso ficticio, mi consultante anuncia que pretende quitarse la vida.",
        ):
            with self.subTest(message=message):
                self.assertIsNone(emergency_response(message))

    def test_subject_changes_relative_context_and_execution_questions_keep_the_right_guidance(self):
        for message, professional in (
            ("Mi paciente está bien, pero yo quiero suicidarme", False),
            ("Mi paciente quiere suicidarse antes de su cita", True),
            ("Mi cliente, que dice que quiere suicidarse, está aquí", True),
            ("Quiero saber cómo matarme", False),
            ("¿Cómo puedo matarme?", False),
            ("Mi paciente quiere aprender a suicidarse", True),
        ):
            with self.subTest(message=message):
                answer = emergency_response(message)
                self.assertIsNotNone(answer)
                self.assertIn("112", answer)
                if professional:
                    self.assertIn("protocolo", answer)
                    self.assertIn("valoración clínica", answer)
                else:
                    self.assertIn("Siento", answer)
                    self.assertNotIn("preocupación por el paciente", answer)
        for connective in ("y", "and"):
            with self.subTest(connective=connective):
                self.assertIsNone(emergency_response(connective))
