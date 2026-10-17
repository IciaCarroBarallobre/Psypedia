.PHONY: evaluate-llm logs-ollama up-ollama ollama-pull help setup up down logs ps urls test build-frontend test-integration check

help:
	@printf '%s\n' \
		'PsyPedia commands' \
		'First start: cp .env.example .env, review settings, then make up.' \
		'' \
		'🚀 Development' \
		'  make up                  Start the app; prepare Ollama when configured' \
		'  make down                Stop and remove containers; keep downloaded models' \
		'  make setup               Rebuild images after dependency or Dockerfile changes' \
		'' \
		'🔎 Status and logs' \
		'  make urls                Show browser URLs for the configured ports' \
		'  make ps                  Show running services and published ports' \
		'  make logs                Follow frontend/backend logs' \
		'  make logs-ollama         Follow detailed model-server logs' \
		'' \
		'🧪 Automated checks' \
		'  make check               Backend + frontend tests, TypeScript, and build' \
		'  make test                Backend tests without real inference' \
		'  make build-frontend      Frontend tests, TypeScript, and build → frontend/dist/' \
		'  make test-integration    Vite → Flask HTTP checks; requires make up' \
		'' \
		'🔬 LLM evaluation — requires Ollama mode running' \
		'  make evaluate-llm        Run synthetic cases and save a local report' \
		'  Examples:' \
		'    make evaluate-llm EVAL_ARGS="--list"' \
		'    make evaluate-llm EVAL_ARGS="--execution application"  # Routing rules' \
		'    make evaluate-llm EVAL_ARGS="--execution model"        # Real generation' \
		'    make evaluate-llm EVAL_ARGS="--group conversation"' \
		'    make evaluate-llm EVAL_ARGS="--case grounded-act --repeat 3"' \
		'    make evaluate-llm EVAL_ARGS="--report evaluation/reports/REPORT.json"' \
		'  Clear checks still require human review; real inference stays outside CI.' \
		'  AI changes: review results and update backend/evaluation/reports/summary.md.' \
		'' \
		'🦙 Model tools' \
		'  make ollama-pull         Prepare the configured model before starting the app' \
		'  make up-ollama           Explicit Docker Ollama startup; make up selects it automatically'

setup: urls
	@echo "📦 Building images and installing dependencies..."
	@docker compose -f compose.dev.yaml build
	@echo "✅ Images are ready. Run make up to start development."

# Start in the foreground; reuse images or build them if missing.
# Local source is mounted: saving updates Vite or reloads Flask, without rebuilding.
# After dependency/Dockerfile changes: stop, make setup, then make up.
# Refresh node_modules; enable the Ollama profile only for CHAT_PROVIDER=ollama.
up:
	@echo "🔎 Checking local configuration..."
	@docker compose -f compose.dev.yaml config --quiet
	@provider=$$(docker compose -f compose.dev.yaml config --environment | awk -F= '/^CHAT_PROVIDER=/ { print $$2 }'); \
	if [ "$$provider" = "ollama" ]; then \
		echo "🦙 Ollama mode selected: preparing the model before starting the app..."; \
		$(MAKE) --no-print-directory up-ollama; \
	else \
		echo "🚀 Mock mode selected: starting frontend and backend without Ollama. Press Ctrl+C to stop."; \
		docker compose -f compose.dev.yaml up --renew-anon-volumes; \
	fi

down:
	@echo "🛑 Stopping project containers (downloaded models are kept)..."
	@docker compose -f compose.dev.yaml down --remove-orphans

# Keep model-server diagnostics out of the default application log stream.
logs:
	@echo "📋 Following frontend/backend logs. Press Ctrl+C to stop following."
	@docker compose -f compose.dev.yaml logs -f backend frontend

logs-ollama:
	@echo "🦙 Following Ollama diagnostics. Press Ctrl+C to stop following."
	@docker compose -f compose.dev.yaml -f compose.ollama.yaml --profile ollama logs -f ollama

ps:
	@echo "🔎 Showing service status and published ports..."
	@docker compose -f compose.dev.yaml ps

test:
	@echo "🧪 Building the backend image and running backend tests..."
	@docker compose -f compose.dev.yaml run --rm --no-deps --build backend python -m unittest discover -s tests -v

# Build first, run UI tests and compile the frontend without starting the backend.
# The temporary container is removed; frontend/dist/ remains through the bind mount.
build-frontend:
	@echo "🧪 Running frontend tests, checking TypeScript, and building assets..."
	@docker compose -f compose.dev.yaml run --rm --no-deps --build frontend sh -c "npm test && npm run build"

# Run both verification targets (parallel execution is possible with make -j).
check: test build-frontend
	@echo "✅ Backend tests, frontend tests, TypeScript, and frontend build passed."

# Read Compose's resolved environment, including .env and shell overrides.
# These are host URLs; server logs may still show internal container ports.
urls:
	@echo "🌐 Reading browser URLs from Compose configuration..."
	@docker compose -f compose.dev.yaml config --quiet
	@docker compose -f compose.dev.yaml config --environment | awk '\
		/^FRONTEND_PORT=./ { frontend = substr($$0, 15) } \
		/^BACKEND_PORT=./ { backend = substr($$0, 14) } \
		END { printf "Browser URLs (available once services are ready):\n  Frontend: http://localhost:%s/\n  Backend:  http://localhost:%s/api/health\nContainer logs show internal ports.\n\n", frontend, backend }'

# Run HTTP integration checks against the running stack, using container addresses.
test-integration:
	@echo "🔗 Testing communication between Vite and Flask (services must be running)..."
	@docker compose -f compose.dev.yaml run --rm --no-deps -v "$(CURDIR)/tests/integration:/integration:ro" backend python -m unittest discover -s /integration -v

# Use Docker Ollama with the connection settings from .env.
# Dependency: ollama-pull must succeed before the application starts.
# It waits for Ollama, reuses/downloads the model inside that container, and
# returns an error on failure. The persistent model volume survives make down.
up-ollama: ollama-pull
	@echo "🚀 Starting backend and frontend with Ollama. Press Ctrl+C to stop."
	@docker compose -f compose.dev.yaml -f compose.ollama.yaml --profile ollama up --renew-anon-volumes --remove-orphans --no-attach ollama

ollama-pull:
	@echo "🦙 Starting Ollama and waiting for its health check..."
	@docker compose -f compose.dev.yaml -f compose.ollama.yaml --profile ollama up -d --wait ollama
	@docker compose -f compose.dev.yaml -f compose.ollama.yaml --profile ollama exec -T ollama sh -ec '\
		echo "🔎 Checking model $$OLLAMA_MODEL..."; \
		if ! ollama show "$$OLLAMA_MODEL" >/dev/null 2>&1; then \
			echo "📥 Downloading model $$OLLAMA_MODEL; first startup may take several minutes."; \
			ollama pull "$$OLLAMA_MODEL" || { echo "❌ Model preparation failed. Check Docker disk space and connectivity." >&2; exit 1; }; \
		fi; \
		ollama show "$$OLLAMA_MODEL" >/dev/null; \
		echo "✅ Model $$OLLAMA_MODEL is ready."'

# Explicit real inference, outside CI; requires make up with CHAT_PROVIDER=ollama.
# Select topics/cases with EVAL_ARGS='--group emergencies' or '--case unknown-therapy --repeat 3'.
evaluate-llm:
	@echo "🔬 Evaluating synthetic cases against the running backend; manual review is required..."
	@docker compose -f compose.dev.yaml exec -T backend python evaluation/run.py $(EVAL_ARGS)
