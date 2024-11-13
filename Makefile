GIT_HASH := $(shell git rev-parse HEAD)
ifndef GIT_HASH
	$(error GIT_HASH is not set)
endif

# ----- Docker -----

NAMESPACE=$(DOCKER_REGISTRY_NAME)
DOCKER_REGISTRY=955244480243.dkr.ecr.us-east-1.amazonaws.com
DOCKER_CONTAINER_NAME=bsides-llm-ctf
DOCKER_REPOSITORY=$(DOCKER_REGISTRY)/$(DOCKER_CONTAINER_NAME)

docker-image:
	docker build -f ctf/Dockerfile --rm -t $(DOCKER_REPOSITORY):local .

ci-docker-auth:
	@echo "Logging in to $(DOCKER_REGISTRY) as $(DOCKER_REGISTRY_USERNAME)"
	@aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 955244480243.dkr.ecr.us-east-1.amazonaws.com

ci-docker-build: ci-docker-auth
	@docker build -f ctf/Dockerfile \
		--no-cache \
		-t $(DOCKER_REPOSITORY):$(GIT_HASH) .

ci-docker-push: ci-docker-auth
	docker tag $(DOCKER_REPOSITORY):$(GIT_HASH) $(DOCKER_REPOSITORY):latest
	docker push $(DOCKER_REPOSITORY)

ci-test:
	@poetry run pytest ctf/

ci-format:
	@poetry run black .
	@djlint ctf/templates/ --reformat

ci-lint:
	@poetry run black . --check
	@poetry run flake8
	@djlint ctf/templates/ --lint

ci-semgrep:
	@semgrep --config "p/auto"
