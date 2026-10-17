# PsyPedia backend

A small Flask application inspired by ports and adapters: HTTP handling, chat
coordination, knowledge retrieval, prompting, and model transport stay separate.

## Table of Contents

- [Responsibilities](#responsibilities)
- [How a question reaches the model](#how-a-question-reaches-the-model)
- [Demo knowledge and limits](#demo-knowledge-and-limits)
- [Ollama configuration and errors](#ollama-configuration-and-errors)
- [Development and verification](#development-and-verification)
- [Real-model evaluation](#real-model-evaluation)
  - [Evaluation summaries](#evaluation-summaries)

## Responsibilities

| Folder | Responsibility |
| --- | --- |
| `api/` | Validate requests and return JSON responses/errors |
| `services/` | Apply routing rules and coordinate answers |
| `knowledge/` | Store demo cards and retrieve matching aliases |
| `prompting/` | Separate card formatting from centralised model instructions |
| `providers/` | Communicate with Ollama or return a fixed mock answer |

The application factory selects and injects the provider. See the
[API contract](../docs/openapi.yaml) and [LLM decisions](LLM_AND_PROMPTING.md).

## How a question reaches the model

Flask validates the request; the chat service applies emergency/privacy rules,
retrieves cards, and calls Ollama only when reference content is available.
Responses without inference cover recognised greetings and missing information.

See the [linked flow diagram and routing rules](LLM_AND_PROMPTING.md#how-it-works)
and [conversation behavior](LLM_AND_PROMPTING.md#current-behavior).

## Demo knowledge and limits

See [knowledge sources and scope](psypedia/knowledge/README.md) for available
cards. This is lexical demo retrieval, not clinically validated RAG. Use synthetic
data only; [limitations](LLM_AND_PROMPTING.md#limitations) explain the boundaries
of privacy rules, emergency routing, and model output.

## Ollama configuration and errors

Start with the [quickstart](../README.md#quickstart). Choose `CHAT_PROVIDER` and
`OLLAMA_*` values in root `.env` using [`.env.example`](../.env.example).

With `ollama`, `make up` starts the model server, waits for health, and checks or
downloads the selected model before starting Flask and Vite. Use Make: direct
Compose startup bypasses model preparation. Failed preparation stops that startup
sequence; existing services are not automatically stopped. `mock` skips Ollama.

Models persist in a volume. Only one stays loaded at a time; a killed runner can
indicate insufficient Docker memory. Inspect `make logs-ollama` for model errors.
Adapter output controls are explained in [LLM behavior](LLM_AND_PROMPTING.md#current-behavior).

See [OpenAPI](../docs/openapi.yaml) for error codes and request/response formats.
`/api/health` checks Flask, not model readiness.

## Development and verification

See [contribution checks](../CONTRIBUTING.md#pull-requests-and-ci) for commands.
Backend tests simulate upstream HTTP; integration checks exercise real Vite-to-Flask
HTTP. Neither establishes the quality of generated answers.

## Real-model evaluation

With Ollama mode running:

```sh
make evaluate-llm EVAL_ARGS='--list'  # Show groups and case IDs, without inference
make evaluate-llm EVAL_ARGS='--execution application'  # Routing rules
make evaluate-llm EVAL_ARGS='--execution model'        # Real generation
make evaluate-llm EVAL_ARGS='--case grounded-act --repeat 3'
make evaluate-llm EVAL_ARGS='--report evaluation/reports/REPORT.json'  # Read only
```

[Cases](evaluation/cases.json) are grouped by emergencies, privacy, knowledge
limits, conversation, grounding, and educational safety. Run without filters to
execute all; repeat `--group` or `--case` to select several. Combining both filters
selects their intersection. Execution labels are expectations: unit tests verify
provider calls, while HTTP reports do not observe them directly.

The [runner](evaluation/run.py) saves raw responses, latency, source hashes, and
review criteria as ignored JSON reports. `--report` summarises them without new
inference. Repeated cases are not additional coverage; older runs describe their
recorded snapshot, not approval of current code.

### Evaluation summaries

[`evaluation/reports/summary.md`](evaluation/reports/summary.md) summarises the
evaluation results: what was tested, what worked, failures, and pending review.
It is a single report, updated as evaluations are repeated.

For changes to the model, prompts, cards, retrieval, guards, history, provider, or
generation options:

1. Rerun relevant synthetic cases and review answers against their rubrics and cards.
2. Update the summary with the date/model, commands, application/model coverage,
   automatic alerts, agent findings, human review status, and raw report filenames.
3. Include the updated summary in the PR and link it from the template. Repeat after
   further AI changes during review so the summary describes the tested behavior.

Only `summary.md` is tracked in `reports/`; raw JSON remains local. Keep human
reviews pending until a person records a decision. Passing keyword checks or
completing an evaluation is not approval. CI uses mocks and downloads no models.
