# PsyPedia

An educational psychology assistant for mental health professionals.

## Table of Contents

- [Current scope](#current-scope)
- [Getting started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Quickstart](#quickstart)
- [Repository structure](#repository-structure)
- [Further reading](#further-reading)

## Current scope

The Vue chat connects to Flask and a small public-source demo knowledge base.
Ollama generates answers locally in Docker; mock mode works without a model.
This prototype is not clinically validated. Clinical manuals and semantic RAG
are not integrated, and conversations are cleared on refresh. Use synthetic data only.

## Getting started

### Prerequisites

- Docker with Compose v2, running.
- Git and Make.
- Internet access for initial images, dependencies, and model downloads.

### Quickstart

From the repository root:

1. Create the local configuration:

   ```sh
   cp .env.example .env
   ```

   Choose `CHAT_PROVIDER=ollama` or `mock` and adjust ports/model as needed.
   `.env` is required and ignored by Git; `OLLAMA_*` settings are needed only for Ollama.

2. Start the application:

   ```sh
   make up
   ```

   Ollama mode prepares the model before starting the app; the first download
   can take several minutes. Mock mode skips Ollama and model downloads.

3. Open [PsyPedia](http://localhost:5173). Use your configured port if different;
   `make urls` shows the browser addresses. Keep the containers running while editing.

Use `make help` for commands and [CONTRIBUTING](CONTRIBUTING.md#local-development)
for everyday development.

## Repository structure

```text
.
├── README.md                 # Overview and quickstart
├── CONTRIBUTING.md           # Development and review workflow
├── CHANGELOG.md              # Notable changes
├── Makefile                  # Development commands
├── compose.dev.yaml          # Frontend/backend development services
├── compose.ollama.yaml       # Ollama service and inference settings
├── .env.example              # Local configuration template
├── .github/                  # CI and pull request template
├── docs/openapi.yaml         # API contract
├── backend/                  # Flask, knowledge cards, prompting, and providers
│   ├── tests/                # Deterministic backend tests
│   └── evaluation/           # Opt-in real-model evaluation
├── frontend/                 # Vue, TypeScript, and shared UI components
└── tests/integration/        # Vite-to-Flask HTTP checks
```

## Further reading

- [Contributing](CONTRIBUTING.md): commands, checks, branches, and release process.
- [Backend](backend/README.md): architecture, Ollama startup, and evaluation.
- [LLM and prompting](backend/LLM_AND_PROMPTING.md): decision flow and model limitations.
- [LLM evaluation results](backend/evaluation/reports/summary.md): tested scope, findings, and pending review;
  follow the [summary workflow](backend/README.md#evaluation-summaries) when changing AI behavior.
- [Demo knowledge](backend/psypedia/knowledge/README.md): available topics and public sources.
- [OpenAPI](docs/openapi.yaml): request, response, and error contracts.
- [Changelog](CHANGELOG.md): notable changes.
