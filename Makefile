GIT_HASH := $(shell git rev-parse HEAD)
ifndef GIT_HASH
	$(error GIT_HASH is not set)
endif

# ----- Docker -----

NAMESPACE=$(DOCKER_REGISTRY_NAME)
DOCKER_REGISTRY=955244480243.dkr.ecr.us-east-1.amazonaws.com
DOCKER_CONTAINER_NAME=bsides-llm-ctf
DOCKER_REPOSITORY=$(DOCKER_REGISTRY)/$(DOCKER_CONTAINER_NAME)
COMPOSE_CMD ?= docker compose
COMPOSE_SERVICES ?= adk-api web

.PHONY: run run-prod prepare-flags
run:
	$(COMPOSE_CMD) --profile default up --build $(COMPOSE_SERVICES)

run-prod:
	$(COMPOSE_CMD) --profile prod up --build $(COMPOSE_SERVICES)

# Seed the level passwords (LanceDB RAG store + level 5 users.db) locally,
# from ctf/agents like the container does, so `adk web` there finds them.
prepare-flags:
	cd ctf/agents && PYTHONPATH=$(CURDIR) PREPARE_FLAGS=1 DOWNLOAD_MODELS=0 uv run python -m ctf.agent_startup

docker-image:
	docker build --rm -t $(DOCKER_REPOSITORY):local web

ci-docker-auth:
	@echo "Logging in to $(DOCKER_REGISTRY) as $(DOCKER_REGISTRY_USERNAME)"
	@aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 955244480243.dkr.ecr.us-east-1.amazonaws.com

ci-docker-build: ci-docker-auth
	@docker build \
		--no-cache \
		-t $(DOCKER_REPOSITORY):$(GIT_HASH) web

ci-docker-push: ci-docker-auth
	docker tag $(DOCKER_REPOSITORY):$(GIT_HASH) $(DOCKER_REPOSITORY):latest
	docker push $(DOCKER_REPOSITORY)

ci-test:
	@uv run pytest ctf/

ci-format:
	@uv run black .

ci-lint:
	@uv run black . --check
	@uv run flake8

# ----- Formatting & Linting -----

.PHONY: format lint security test

# Auto-format Python code in place.
format:
	@uv run black .

# Check formatting and run static analysis (Python agent + web app).
lint: web-lint
	@uv run black . --check
	@uv run flake8

# Security scan. Note: this CTF contains intentionally vulnerable code,
# so findings are expected and reviewed manually rather than gated in lint.
security:
	@uv run bandit -r . --ini .bandit

# Python agent tests + web app tests.
test: web-test
	@uv run pytest ctf/

# ----- Web app (Next.js 16.4 on vinext, in web/) -----

.PHONY: web-install web-dev web-lint web-test web-build web-build-cf

web-install:
	@pnpm --dir web install --frozen-lockfile

web-dev:
	@pnpm --dir web dev

web-lint:
	@pnpm --dir web lint
	@pnpm --dir web typecheck

web-test:
	@pnpm --dir web test

# Node standalone server (Docker) and the Next.js 16.4 compatibility build.
web-build:
	@pnpm --dir web build
	@pnpm --dir web build:next

web-build-cf:
	@pnpm --dir web build:cf
