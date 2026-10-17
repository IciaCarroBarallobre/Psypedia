"""Offline checks for the evaluation harness and case routing; no inference required."""

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from evaluation.run import check_answer, main, select_cases, source_comparison, summarize_report
from psypedia.knowledge import DemoKnowledgeBase
from psypedia.providers import ChatProvider
from psypedia.services.chat import ChatService


def manifest_groups():
    path = Path(__file__).resolve().parents[1] / "evaluation/cases.json"
    return json.loads(path.read_text())["groups"]


class EvaluationCheckTest(unittest.TestCase):
    def test_provider_failure_cannot_pass_content_checks(self):
        self.assertTrue(check_answer({}, 503, None))
        self.assertTrue(check_answer({}, 200, ""))

    def test_disclaimer_does_not_hide_a_forbidden_claim(self):
        case = {"required_any": [["no tengo"]], "forbidden": ["no existe"]}
        self.assertTrue(check_answer(case, 200, "No tengo información. Esta terapia no existe."))

    def test_reference_titles_do_not_count_as_generated_therapy_claims(self):
        case = {"forbidden": ["TCC"]}
        answer = "Una explicación.\n\nReferencias de las fichas / Card references:\n- TCC: https://example.org"
        self.assertEqual(check_answer(case, 200, answer), [])

    def test_matching_required_signal_alone_does_not_validate_meaning(self):
        # A negative sentence can contain the expected word: review is still needed.
        self.assertEqual(check_answer({"required_any": [["112"]]}, 200, "No llames al 112."), [])

    def test_acronym_checks_do_not_match_fragments_of_spanish_words(self):
        case = {"forbidden": ["ACT"]}
        self.assertEqual(check_answer(case, 200, "La práctica puede ayudar a actuar."), [])
        self.assertTrue(check_answer(case, 200, "Hablemos de ACT."))
        self.assertTrue(check_answer(case, 200, "Hablemos de act."))

    def test_protocol_limit_accepts_no_detalla_but_flags_an_invented_protocol(self):
        case = next(case for case in select_cases(manifest_groups()) if case["id"] == "unsupported-protocol")
        self.assertEqual(check_answer(case, 200, "Este resumen no detalla protocolos específicos."), [])
        self.assertTrue(check_answer(case, 200, "La ficha ofrece un protocolo exacto para aplicar DBT."))

    def test_negated_confirmation_is_allowed_without_hiding_positive_claims(self):
        case = next(case for case in select_cases(manifest_groups()) if case["id"] == "history-false-evidence")
        safe = "No puedo confirmar esa afirmación: las fichas no respaldan una garantía de curación."
        unsafe = "No tengo el texto completo, pero sí está respaldada y el estudio demuestra la garantía."
        self.assertEqual(check_answer(case, 200, safe), [])
        self.assertTrue(check_answer(case, 200, unsafe))


class EvaluationSelectionTest(unittest.TestCase):
    groups = [
        {"id": "emergencies", "expected_execution": "application",
         "cases": [{"id": "danger", "message": "Danger"}]},
        {"id": "grounding", "expected_execution": "model",
         "cases": [{"id": "facts", "message": "Facts"}]},
    ]

    def test_group_filter_does_not_run_other_topics(self):
        self.assertEqual(select_cases(self.groups, group_ids=["grounding"]), [
            {"id": "facts", "message": "Facts", "group": "grounding", "expected_execution": "model"},
        ])

    def test_execution_filter_excludes_application_cases(self):
        selected = select_cases(self.groups, execution="model")
        self.assertEqual([case["id"] for case in selected], ["facts"])

    def test_case_execution_overrides_its_group_default(self):
        groups = [{"id": "conversation", "expected_execution": "model", "cases": [
            {"id": "hello", "expected_execution": "application"},
            {"id": "follow-up"},
        ]}]
        self.assertEqual([case["id"] for case in select_cases(groups, execution="application")], ["hello"])
        self.assertEqual([case["id"] for case in select_cases(groups, execution="model")], ["follow-up"])

    def test_existing_case_selection_and_multiple_group_selection_work(self):
        self.assertEqual(select_cases(self.groups, case_ids=["danger"])[0]["group"], "emergencies")
        self.assertEqual(len(select_cases(self.groups, group_ids=["emergencies", "grounding"])), 2)

    def test_invalid_or_empty_selections_fail_instead_of_reporting_success(self):
        for filters in ({"group_ids": ["typo"]}, {"case_ids": ["missing"]},
                        {"group_ids": ["grounding"], "case_ids": ["danger"]},
                        {"group_ids": ["emergencies"], "execution": "model"},
                        {"execution": "typo"}):
            with self.subTest(filters=filters), self.assertRaises(ValueError):
                select_cases(self.groups, **filters)

    def test_duplicate_case_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            select_cases(self.groups + [{"id": "other", "expected_execution": "model", "cases": [{"id": "facts"}]}])

    def test_missing_or_invalid_execution_metadata_is_rejected(self):
        invalid_groups = [
            [{"id": "unknown", "cases": [{"id": "case"}]}],
            [{"id": "unknown", "expected_execution": "typo", "cases": [{"id": "case"}]}],
            [{"id": "known", "expected_execution": "model", "cases": [{"id": "case", "expected_execution": "typo"}]}],
        ]
        for groups in invalid_groups:
            with self.subTest(groups=groups), self.assertRaises(ValueError):
                select_cases(groups)

    def test_real_manifest_has_unique_ids_and_expected_thematic_cases(self):
        cases = select_cases(manifest_groups())
        by_id = {case["id"]: case for case in cases}
        self.assertEqual(by_id["risk-confirmation"]["group"], "emergencies")
        self.assertEqual(by_id["grounded-act"]["group"], "grounding")
        self.assertEqual(by_id["educational-self-harm"]["group"], "educational-safety")

    def test_manifest_requests_and_review_checks_are_valid(self):
        # Invalid fixtures would test request rejection instead of the intended route.
        for case in select_cases(manifest_groups()):
            with self.subTest(case=case["id"]):
                for field in ("id", "message", "expected_path", "review"):
                    self.assertIsInstance(case[field], str)
                    self.assertTrue(case[field].strip())
                history = case.get("history", [])
                self.assertIsInstance(history, list)
                self.assertLessEqual(len(history), 12)
                for turn in history:
                    self.assertEqual(set(turn), {"role", "content"})
                    self.assertIn(turn["role"], ("user", "assistant"))
                    self.assertIsInstance(turn["content"], str)
                    self.assertTrue(turn["content"].strip())
                    self.assertLessEqual(len(turn["content"]), 4000)
                self.assertTrue(case.get("required_any") or case.get("forbidden"))
                for alternatives in case.get("required_any", []):
                    self.assertIsInstance(alternatives, list)
                    self.assertTrue(alternatives)
                    self.assertTrue(all(isinstance(term, str) and term.strip() for term in alternatives))
                self.assertTrue(all(isinstance(term, str) and term.strip() for term in case.get("forbidden", [])))


class EvaluationRoutingTest(unittest.TestCase):
    def test_manifest_execution_matches_chat_service_routing(self):
        # Exercise the same routing as Ollama mode with a recording provider.
        # This verifies whether inference is reached, not generated-answer quality.
        for case in select_cases(manifest_groups()):
            with self.subTest(case=case["id"]):
                provider = Mock(spec=ChatProvider)
                provider.answer.return_value = "Respuesta generada de prueba."
                answer = ChatService(provider, DemoKnowledgeBase()).answer(
                    case["message"], history=case.get("history"),
                )
                if case["expected_execution"] == "model":
                    provider.answer.assert_called_once()
                    if case["id"] == "general-after-patient-data":
                        self.assertNotIn("history", provider.answer.call_args.kwargs)
                        self.assertNotIn("Persona Ficticia", str(provider.answer.call_args))
                        self.assertNotIn("persona.ficticia@example.org", str(provider.answer.call_args))
                else:
                    provider.answer.assert_not_called()
                    self.assertEqual(check_answer(case, 200, answer), [])


class EvaluationReportTest(unittest.TestCase):
    def test_summary_distinguishes_repetitions_scope_and_independent_reviews(self):
        report = {"summary": {"results": 999}, "results": [
            {"case": {"id": "danger", "expected_execution": "application", "required_any": [["112"]]},
             "http_status": 200, "heuristic_failures": [], "human_review": {"status": "accepted"}},
            {"case": {"id": "danger", "expected_path": "Application emergency rule"},
             "http_status": 200, "heuristic_failures": [], "human_review": {"status": "pending"}},
            {"case": {"id": "act", "expected_execution": "model", "forbidden": ["DBT"]},
             "http_status": 200, "heuristic_failures": ["Unsupported detail"],
             "human_review": {"status": "rejected"}, "agent_review": {"status": "rejected"}},
            {"case": {"id": "act", "expected_path": "Model with ACT card"},
             "http_status": 503, "heuristic_failures": ["HTTP failure"],
             "human_review": {"status": "pending"}},
            {"case": {"id": "legacy"}, "http_status": None, "heuristic_failures": []},
            {"case": {"id": "other"}, "http_status": 200, "heuristic_failures": [],
             "human_review": {"status": "accepted"}, "agent_review": {"status": "accepted"}},
        ]}
        summary = summarize_report(report)
        self.assertEqual(summary["results"], 6)
        self.assertEqual(summary["unique_cases"], 4)
        self.assertEqual(summary["expected_execution"], {"application": 2, "model": 2, "unknown": 2})
        self.assertEqual(summary["http_failures"], 2)
        self.assertEqual(summary["automatic_failures"], 2)
        self.assertEqual(summary["human_review"], {"accepted": 2, "rejected": 1, "pending": 3})
        self.assertEqual(summary["agent_flags"], 1)
        self.assertEqual(summary["without_content_checks"], 4)

    def test_unrecognised_human_status_cannot_count_as_reviewed(self):
        report = {"results": [
            {"case": {"id": str(index)}, "http_status": 200,
             "human_review": {"status": status}}
            for index, status in enumerate(("approved", "", None))
        ]}
        self.assertEqual(summarize_report(report)["human_review"], {
            "accepted": 0, "rejected": 0, "pending": 3,
        })

    def test_snapshot_comparison_distinguishes_changed_and_unrecorded_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            prompt = root / "prompt.py"
            prompt.write_text("original prompt")
            (root / "retrieval.py").write_text("retrieval")
            recorded = {"prompt.py": hashlib.sha256(prompt.read_bytes()).hexdigest()}
            with patch.multiple("evaluation.run", ROOT=root, EVALUATED_FILES=("prompt.py", "retrieval.py")):
                self.assertEqual(source_comparison({"source_hashes": recorded}), {
                    "changed": [], "unrecorded": ["retrieval.py"],
                })
                prompt.write_text("updated prompt")
                self.assertEqual(source_comparison({"source_hashes": recorded}), {
                    "changed": ["prompt.py"], "unrecorded": ["retrieval.py"],
                })
                self.assertEqual(source_comparison({}), {
                    "changed": [], "unrecorded": ["prompt.py", "retrieval.py"],
                })

    def test_report_cli_is_offline_and_propagates_recorded_failures(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            for failures, expected_exit in (([], 0), (["Unsupported claim"], 1)):
                with self.subTest(failures=failures):
                    path.write_text(json.dumps({"results": [{
                        "case": {"id": "greeting", "expected_execution": "application"},
                        "http_status": 200, "heuristic_failures": failures,
                    }]}))
                    with patch.dict("os.environ", {}, clear=True), \
                            patch("sys.argv", ["evaluation/run.py", "--report", str(path)]), \
                            patch("evaluation.run.urlopen") as http, redirect_stdout(io.StringIO()):
                        self.assertEqual(main(), expected_exit)
                        http.assert_not_called()

    def test_empty_or_interrupted_report_cannot_report_success(self):
        complete_result = {
            "case": {"id": "greeting", "expected_execution": "application"},
            "http_status": 200, "heuristic_failures": [],
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            for report in ({"results": []}, {"planned_results": 2, "results": [complete_result]}):
                with self.subTest(report=report):
                    path.write_text(json.dumps(report))
                    with patch("sys.argv", ["evaluation/run.py", "--report", str(path)]), \
                            patch("evaluation.run.urlopen") as http, redirect_stdout(io.StringIO()):
                        self.assertEqual(main(), 1)
                        http.assert_not_called()
