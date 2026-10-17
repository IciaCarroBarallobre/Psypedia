# Changelog

Notable changes to PsyPedia are recorded here. Unreleased changes are grouped below; published releases will use version numbers and release dates.

## Table of Contents

- [Unreleased](#unreleased)
  - [Added](#added)
  - [Changed](#changed)

## [Unreleased]

### Added

- Local Ollama generation in Docker, with configurable models, automatic model preparation, persistent downloads, and controlled service errors.
- Demo knowledge cards for CBT, ACT, DBT, and Precision Psychology, with source links, category-based therapy overviews, and partial answers that explain available information while stating its limits.
- Patient-information warnings and help redirection before inference, combining subject, harm, intention, and context signals without assessing clinical risk.
- Recent conversation history for follow-up questions, without backend persistence.
- Spanish chat interface with a welcome message, animated loading feedback, and automatic scrolling that respects the reader's position.
- Synthetic evaluation cases and reports with a shared [results summary](backend/evaluation/reports/summary.md), automated backend coverage, and documentation of LLM behavior and limitations.

- Connect question submission to `POST /api/chat`, displaying returned answers, pending status, and network/API errors with automated frontend coverage.

- Mock `POST /api/chat` endpoint with JSON validation, documented response/error contracts, and automated backend tests.

- Chat interface with validated question submission, distinct user/assistant messages, and a clear disconnected-assistant notice.
- Tailwind CSS v4, shadcn-vue controls, and automated Vue component tests.

- OpenAPI specification for the implemented health endpoint in `docs/openapi.yaml`.

- Automated HTTP integration test for the Vite-to-Flask API proxy, with a dedicated CI job and `make test-integration`.

- Vue 3 and TypeScript frontend with Vite and an initial project landing page.
- Flask application with a `GET /api/health` endpoint and backend unit tests.
- Vite proxy for `/api` requests to the backend.
- Docker-based development with source mounts, frontend HMR, and Flask automatic reload with its debugger disabled.
- Backend health check and frontend startup dependency in Compose, with ports exposed only on localhost.
- Optional development port configuration through `.env.example`.
- Make commands for development, image builds, backend tests, and frontend verification.
- Shared editor conventions and Git ignore rules.
- Quickstart and contribution guidelines covering development, branches, checks, and release promotion.

### Changed

- Gate generation on available knowledge cards; unknown topics receive an explicit limitation, detected patient information is blocked before inference, and emergencies retain human-help redirection. Ollama is instructed to rewrite selected facts only.

- Limit Docker Ollama to one resident model to reduce memory contention between evaluation and application models.

- Require explicit configuration in a local `.env` created from `.env.example`, without Compose/backend fallback values; mock mode needs no Ollama settings, and CI creates the file before integration checks.

- Separate backend HTTP routes, chat service, and injectable mock provider while preserving the API contract.

- Apply the shared navy/blue design palette through centralized light-only tokens and mobile-first chat components.

- Frontend Docker runtime updated to Node 22.23.3 for UI tooling compatibility.

- Development startup logs show browser URLs using the published host ports instead of container-local URLs.

- Named the development Compose configuration `compose.dev.yaml` to make its purpose explicit.
- Named the frontend compilation command `make build-frontend` to distinguish it from Docker image builds.
