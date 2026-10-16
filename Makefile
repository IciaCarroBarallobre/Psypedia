.PHONY: help setup up down logs ps urls test build-frontend test-integration check

help:
	@echo "make test-integration - Test the Vite-to-Flask proxy (requires running services)"
	@echo "make urls   - Show browser URLs using the effective Compose ports"
	@echo "make setup  - Build images and install dependencies; do not start services"
	@echo "make up     - Start development servers with reload; refresh frontend dependency volume"
	@echo "make down   - Stop and remove project containers and network"
	@echo "make logs   - Follow both services' logs; Ctrl+C stops following"
	@echo "make ps     - Show service status and published ports"
	@echo "make test   - Build backend image and run unit tests in a temporary container"
	@echo "make build-frontend - Build frontend image, run UI tests, check TypeScript, and write frontend/dist/"
	@echo "make check  - Run backend tests and frontend build"

setup: urls
	docker compose -f compose.dev.yaml build

# Start in the foreground; reuse images or build them if missing.
# Local source is mounted: saving updates Vite or reloads Flask, without rebuilding.
# After dependency/Dockerfile changes: stop, make setup, then make up.
# Refresh the node_modules volume from the image to use its installed dependencies.
up:
	docker compose -f compose.dev.yaml up --renew-anon-volumes

down:
	docker compose -f compose.dev.yaml down

logs:
	docker compose -f compose.dev.yaml logs -f

ps:
	docker compose -f compose.dev.yaml ps

test:
	docker compose -f compose.dev.yaml run --rm --no-deps --build backend python -m unittest discover -s tests -v

# Build first, run UI tests and compile the frontend without starting the backend.
# The temporary container is removed; frontend/dist/ remains through the bind mount.
build-frontend:
	docker compose -f compose.dev.yaml run --rm --no-deps --build frontend sh -c "npm test && npm run build"

# Run both verification targets (parallel execution is possible with make -j).
check: test build-frontend

# Read Compose's resolved environment, including .env and shell overrides.
# These are host URLs; server logs may still show internal container ports.
urls:
	@docker compose -f compose.dev.yaml config --quiet
	@docker compose -f compose.dev.yaml config --environment | awk '\
		BEGIN { frontend = "5173"; backend = "5000" } \
		/^FRONTEND_PORT=./ { frontend = substr($$0, 15) } \
		/^BACKEND_PORT=./ { backend = substr($$0, 14) } \
		END { printf "Browser URLs (available once services are ready):\n  Frontend: http://localhost:%s/\n  Backend:  http://localhost:%s/api/health\nContainer logs show internal ports.\n\n", frontend, backend }'

# Run HTTP integration checks against the running stack, using container addresses.
test-integration:
	docker compose -f compose.dev.yaml run --rm --no-deps -v "$(CURDIR)/tests/integration:/integration:ro" backend python -m unittest discover -s /integration -v
