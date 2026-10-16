# PsyPedia

**PsyPedia** is an AI-assisted knowledge platform engineered specifically for
psychologists and mental health practitioners, intended to provide educational
answers grounded in curated clinical literature.

## Current scope

The responsive, light-mode chat lets you submit questions and displays user and assistant messages separately. It is an interface preview: the frontend calls the Flask chat API, which returns an explicit mock answer without a model or clinical answer generation. Messages are kept in memory and cleared on refresh. Clinical sources have not been selected or integrated yet.

## Getting started

Development, testing, and builds run entirely inside Docker for both
the frontend and backend.

### Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/) with Compose v2
  or [Docker Desktop](https://www.docker.com/products/docker-desktop/) running.
- An active Internet connection (required for the initial build to download base
  images and dependencies).

### Quickstart

1. **[Optional] Configure local development**:

    ```sh
        cp .env.example .env # run this from its root if you need custom ports
    ```

2. **Start containers**:

    ```sh
    make up
    ```

3. **Access the application**: Open [PsyPedia](http://localhost:5173) in your browser.
   If you changed the ports, adjust this URL and the health-check URLs below.

4. Check Flask directly and through the Vite proxy:

    ```sh
    curl --fail http://localhost:5000/api/health
    curl --fail http://localhost:5173/api/health
    ```

    Both should return `{"status":"ok"}`.

5. Other useful commands: `make help`

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, everyday commands,
checks, and our branching and release workflow.

See [CHANGELOG.md](CHANGELOG.md) for notable project changes.

## Repository structure

```text
.
├── README.md                  # Project overview and quickstart
├── CONTRIBUTING.md            # Development setup, branches, releases, and checks
├── CHANGELOG.md               # Notable changes and release history
├── Makefile                   # Docker development shortcuts
├── compose.dev.yaml           # Local development containers, mounts, and reload
├── .env.example               # Optional development port configuration
├── .editorconfig              # Editor conventions
├── .gitignore                 # Files excluded from version control
├── LICENSE                    # Project license
├── backend/
│   ├── README.md              # Backend architecture and tests
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── app.py                 # Flask CLI entry point
│   ├── psypedia/
│   │   ├── __init__.py        # Application factory and provider wiring
│   │   ├── api/               # HTTP routes and request validation
│   │   ├── services/          # Chat orchestration
│   │   └── providers/         # Provider contract and mock implementation
│   └── tests/                 # Backend unit tests
└── frontend/
    ├── Dockerfile
    ├── .dockerignore
    ├── .npmrc
    ├── package.json
    ├── package-lock.json
    ├── tsconfig.json
    ├── vite.config.ts         # Vue integration and development API proxy
    ├── index.html
    └── src/                   # Vue application
```

## API contract

See [docs/openapi.yaml](docs/openapi.yaml) for the OpenAPI specification of the implemented API. For direct Flask access, use your configured `BACKEND_PORT`; the relative `/api` server uses the frontend proxy.

### Mock chat endpoint

`POST /api/chat` accepts a JSON object with a non-empty `message` string and returns an `answer` string explicitly marked as a mock. It does not call a model or store messages. Invalid JSON/messages return `400`; non-JSON requests return `415`, with an `error` object containing `code` and `message`.

```sh
curl --fail http://localhost:5000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What is psychotherapy?"}'
```

Use your configured backend port if different. The frontend sends questions to this endpoint through the Vite proxy and displays returned answers or visible errors.

See [backend/README.md](backend/README.md) for backend architecture and testing.
