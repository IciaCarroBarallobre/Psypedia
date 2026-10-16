# PsyPedia

**PsyPedia** is an AI-assisted knowledge platform engineered specifically for
psychologists and mental health practitioners, strictly grounding its
educational answers in public, well-known, and transparent clinical literature.

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
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── app.py                 # Flask CLI entry point
│   ├── psypedia/              # Application factory and API routes
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
