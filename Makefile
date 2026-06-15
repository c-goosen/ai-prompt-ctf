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
COMPOSE_SERVICES ?= adk-api frontend

.PHONY: run run-prod
run:
	$(COMPOSE_CMD) --profile default up --build $(COMPOSE_SERVICES)

run-prod:
	$(COMPOSE_CMD) --profile prod up --build $(COMPOSE_SERVICES)

docker-image:
	docker build -f Dockerfile.frontend --rm -t $(DOCKER_REPOSITORY):local .

ci-docker-auth:
	@echo "Logging in to $(DOCKER_REGISTRY) as $(DOCKER_REGISTRY_USERNAME)"
	@aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 955244480243.dkr.ecr.us-east-1.amazonaws.com

ci-docker-build: ci-docker-auth
	@docker build -f Dockerfile.frontend \
		--no-cache \
		-t $(DOCKER_REPOSITORY):$(GIT_HASH) .

ci-docker-push: ci-docker-auth
	docker tag $(DOCKER_REPOSITORY):$(GIT_HASH) $(DOCKER_REPOSITORY):latest
	docker push $(DOCKER_REPOSITORY)

ci-test:
	@uv run pytest ctf/

ci-format:
	@uv run black .
	@uv run djlint ctf/frontend/templates/ --reformat

ci-lint:
	@uv run black . --check
	@uv run flake8
	@uv run djlint ctf/frontend/templates/ --lint

# ----- Formatting & Linting -----

.PHONY: format lint security test

# Auto-format Python code and Jinja templates in place.
format:
	@uv run black .
	@uv run djlint ctf/frontend/templates/ --reformat

# Check formatting and run static analysis without modifying files.
lint:
	@uv run black . --check
	@uv run flake8
	@uv run djlint ctf/frontend/templates/ --lint

# Security scan. Note: this CTF contains intentionally vulnerable code,
# so findings are expected and reviewed manually rather than gated in lint.
security:
	@uv run bandit -r . --ini .bandit

test:
	@uv run pytest ctf/
