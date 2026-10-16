# Changelog

Notable changes to PsyPedia are recorded here. Unreleased changes are grouped below; published releases will use version numbers and release dates.

## [Unreleased]

### Added

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

- Development startup logs show browser URLs using the published host ports instead of container-local URLs.

- Named the development Compose configuration `compose.dev.yaml` to make its purpose explicit.
- Named the frontend compilation command `make build-frontend` to distinguish it from Docker image builds.
