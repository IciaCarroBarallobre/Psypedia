"""Synthetic evaluation over HTTP; automatic checks never certify answer quality."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from time import monotonic
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
EVALUATED_FILES = (
    "psypedia/__init__.py", "psypedia/api/chat.py",
    "psypedia/prompting/prompts.py", "psypedia/prompting/context.py",
    "psypedia/knowledge/topics.json", "psypedia/knowledge/retrieval.py",
    "psypedia/providers/ollama.py", "psypedia/services/chat.py",
    "psypedia/services/emergency.py", "evaluation/cases.json", "evaluation/run.py",
)


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold())
                   if not unicodedata.combining(c))


def contains_term(text, term):
    normalized = normalize(term)
    # ACT must not match words such as "práctica" or "actuar".
    if term.isalpha() and term.isupper() and len(term) <= 6:
        return re.search(r"\b" + re.escape(normalized) + r"\b", text) is not None
    return normalized in text


def check_answer(case, status, answer):
    if status != 200 or not isinstance(answer, str) or not answer.strip():
        return [f"Expected HTTP 200 with a non-empty answer; received {status}"]
    failures = []
    text = normalize(answer.split("\n\nReferencias de las fichas / Card references:")[0])
    for alternatives in case.get("required_any", []):
        if not any(contains_term(text, term) for term in alternatives):
            failures.append(f"Missing expected signal: {alternatives}")
    for term in case.get("forbidden", []):
        if contains_term(text, term):
            failures.append(f"Potential instruction violation: {term}")
    if "<think>" in text or "</think>" in text:
        failures.append("Marked reasoning leaked into answer")
    return failures


def get_expected_execution(case):
    """Read expectations, including old reports; never infer observed model calls."""
    if case.get("expected_execution") in ("application", "model"):
        return case["expected_execution"]
    path = case.get("expected_path", "").casefold()
    for execution in ("application", "model"):
        if path.startswith(execution):
            return execution
    return "unknown"


def select_cases(groups, *, group_ids=None, case_ids=None, execution=None):
    """Flatten thematic groups and reject ambiguous metadata or empty selections."""
    group_names = [group["id"] for group in groups]
    cases = [{"expected_execution": group.get("expected_execution"), **case,
              "group": group["id"]} for group in groups for case in group["cases"]]
    names = [case["id"] for case in cases]
    if len(set(group_names)) != len(group_names) or len(set(names)) != len(names):
        raise ValueError("Group IDs and case IDs must be unique")
    if any(case["expected_execution"] not in ("application", "model") for case in cases):
        raise ValueError("Every case needs expected_execution: application or model")
    if execution not in (None, "application", "model"):
        raise ValueError("Execution must be application or model")
    unknown_groups = set(group_ids or []) - set(group_names)
    unknown_cases = set(case_ids or []) - set(names)
    if unknown_groups or unknown_cases:
        raise ValueError(f"Unknown groups: {sorted(unknown_groups)}; unknown cases: {sorted(unknown_cases)}")
    selected = [case for case in cases
                if (not group_ids or case["group"] in group_ids)
                and (not case_ids or case["id"] in case_ids)
                and (not execution or case["expected_execution"] == execution)]
    if not selected:
        raise ValueError("No cases match the selected filters")
    return selected


def summarize_report(report):
    """Recompute totals from results so later review edits cannot leave stale counts."""
    results = report.get("results", [])
    return {
        "results": len(results),
        "unique_cases": len({r["case"]["id"] for r in results}),
        "expected_execution": {scope: sum(get_expected_execution(r["case"]) == scope for r in results)
                               for scope in ("application", "model", "unknown")},
        "http_failures": sum(r.get("http_status") != 200 for r in results),
        "automatic_failures": sum(bool(r.get("heuristic_failures")) for r in results),
        "without_content_checks": sum(not (r["case"].get("required_any") or r["case"].get("forbidden"))
                                      for r in results),
        "human_review": {
            state: sum((r.get("human_review", {}).get("status")
                        if r.get("human_review", {}).get("status") in ("accepted", "rejected")
                        else "pending") == state for r in results)
            for state in ("accepted", "rejected", "pending")
        },
        "agent_flags": sum(r.get("agent_review", {}).get("status") == "rejected" for r in results),
    }


def source_comparison(report):
    """Compare the available snapshot; missing hashes do not establish a match."""
    recorded = report.get("source_hashes", {})
    return {
        "changed": [name for name in EVALUATED_FILES
                    if name in recorded and recorded[name] != hashlib.sha256((ROOT / name).read_bytes()).hexdigest()],
        "unrecorded": [name for name in EVALUATED_FILES if name not in recorded],
    }


def print_report_summary(report, path):
    summary = summarize_report(report)
    sources = source_comparison(report)
    scope = summary["expected_execution"]
    review = summary["human_review"]
    print(f"\nReport: {path}\nModel recorded: {report.get('model', 'unknown')}")
    print(f"Scope: {summary['results']} results, {summary['unique_cases']} unique cases")
    print(f"Expected execution: {scope['application']} application, {scope['model']} model, {scope['unknown']} unclassified")
    print("Execution is expected, not observed; HTTP reports do not count actual model calls.")
    print(f"Automatic failures: {summary['automatic_failures']}; HTTP failures: {summary['http_failures']}")
    print(f"Human review: {review['accepted']} accepted, {review['rejected']} rejected, {review['pending']} pending")
    print(f"Agent flags: {summary['agent_flags']} (not human sign-off)")
    if summary["without_content_checks"]:
        print(f"Results without case-specific content checks: {summary['without_content_checks']}")
    if sources["changed"]:
        print("Snapshot differs from current files: " + ", ".join(sources["changed"]))
    if sources["unrecorded"]:
        print("Snapshot incomplete; no recorded hash for: " + ", ".join(sources["unrecorded"]))
    if not any(sources.values()):
        print("Recorded source snapshot matches current files; this does not verify loaded server code or model weights.")
    planned = report.get("planned_results")
    incomplete = not summary["results"] or (planned is not None and planned != summary["results"])
    if incomplete:
        print(f"Incomplete run: {summary['results']} of {planned} planned results")
    current_ids = {case["id"] for group in json.loads((ROOT / "evaluation/cases.json").read_text())["groups"]
                   for case in group["cases"]}
    covered = {r["case"]["id"] for r in report.get("results", [])}
    missing = sorted(current_ids - covered)
    if missing:
        print("Outside this report's coverage (current manifest): " + ", ".join(missing))
    for result in report.get("results", []):
        notes = list(result.get("heuristic_failures", []))
        for field in ("agent_review", "human_review"):
            decision = result.get(field, {})
            if decision.get("status") == "rejected":
                notes.append(f"{field}: {decision.get('notes', 'rejected')}")
        if notes:
            candidate = f" / {result['version']}" if "version" in result else ""
            print(f"  {result['case']['id']}{candidate}, trial {result.get('trial', '?')}: " + "; ".join(notes))
    failed = bool(summary["automatic_failures"] or summary["http_failures"]
                  or review["rejected"] or summary["agent_flags"] or incomplete)
    print("Conclusion: " + ("ISSUES FOUND" if failed else "NO RECORDED AUTOMATIC FAILURES — NOT A QUALITY APPROVAL"))
    return failed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", dest="cases", help="Case ID; repeat to select several")
    parser.add_argument("--group", action="append", dest="groups", help="Thematic group; repeat for several")
    parser.add_argument("--execution", choices=("application", "model"), help="Filter by expected execution")
    parser.add_argument("--list", action="store_true", help="List selected cases without sending requests")
    parser.add_argument("--report", type=Path, help="Summarize an existing report without HTTP or inference")
    parser.add_argument("--repeat", type=int, default=1, help="Trials per case (default: 1)")
    args = parser.parse_args()
    if args.report:
        if args.cases or args.groups or args.execution or args.list or args.repeat != 1:
            parser.error("--report cannot be combined with run filters")
        try:
            report = json.loads(args.report.read_text())
            return int(print_report_summary(report, args.report))
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            parser.error(f"Cannot read report: {error}")
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    groups = json.loads((ROOT / "evaluation/cases.json").read_text())["groups"]
    try:
        selected = select_cases(groups, group_ids=args.groups, case_ids=args.cases, execution=args.execution)
    except ValueError as error:
        parser.error(str(error))
    if args.list:
        for case in selected:
            print(f"[{case['group']} / expected {case['expected_execution']}] {case['id']}: {case['message']}")
        return 0
    if os.environ.get("CHAT_PROVIDER") != "ollama":
        parser.error("Run in the Docker backend with CHAT_PROVIDER=ollama; mock answers cannot evaluate a model.")
    folder = ROOT / "evaluation/reports"
    folder.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = folder / f"{stamp}.json"
    report = {
        "schema_version": 2, "created_at": stamp, "model": os.environ.get("OLLAMA_MODEL"),
        "provider": "ollama", "endpoint": "http://127.0.0.1:5000/api/chat",
        "planned_results": len(selected) * args.repeat,
        "note": "Synthetic data only. Execution labels are expectations, not observed provider calls. Automatic checks do not replace human review or establish clinical safety.",
        "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in EVALUATED_FILES},
        "results": [],
    }
    print(f"Model: {report['model']}. {report['planned_results']} requests; human review required.", flush=True)
    for case in selected:
        for trial in range(1, args.repeat + 1):
            print(f"Running [{case['group']} / expected {case['expected_execution']}] {case['id']} ({trial}/{args.repeat})…", flush=True)
            started = monotonic()
            status, answer, error = None, None, None
            payload = {"message": case["message"], "history": case.get("history", [])}
            try:
                request = Request(report["endpoint"], data=json.dumps(payload).encode(),
                                  headers={"Content-Type": "application/json"})
                with urlopen(request, timeout=150) as response:
                    status, data = response.status, json.load(response)
                answer, error = data.get("answer"), data.get("error")
            except HTTPError as exc:
                status = exc.code
                with exc:
                    error = exc.read().decode("utf-8", errors="replace")
            except (URLError, OSError, ValueError, AttributeError) as exc:
                error = str(exc)
            failures = check_answer(case, status, answer)
            report["results"].append({
                "case": case, "trial": trial, "http_status": status,
                "answer": answer, "error": error, "seconds": round(monotonic() - started, 2),
                "heuristic_failures": failures,
                "human_review": {"status": "pending", "notes": ""},
            })
            path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            print(f"  {'CHECK FAILED' if failures else 'CHECKS CLEAR — REVIEW REQUIRED'}; {report['results'][-1]['seconds']} s", flush=True)
    return int(print_report_summary(report, path))


if __name__ == "__main__":
    raise SystemExit(main())
