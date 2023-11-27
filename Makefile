GIT_HASH := $(shell git rev-parse HEAD)
ifndef GIT_HASH
	$(error GIT_HASH is not set)
endif

# ----- Docker -----

NAMESPACE=$(DOCKER_REGISTRY_NAME)
DOCKER_REGISTRY=registry.uw.systems
DOCKER_CONTAINER_NAME=llm-security-challenge
DOCKER_REPOSITORY=$(DOCKER_REGISTRY)/$(NAMESPACE)/$(DOCKER_CONTAINER_NAME)

docker-image:
	docker build -f Dockerfile --rm -t $(DOCKER_REPOSITORY):local .

ci-docker-auth:
	@echo "Logging in to $(DOCKER_REGISTRY) as $(DOCKER_REGISTRY_USERNAME)"
	@aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 955244480243.dkr.ecr.us-east-1.amazonaws.com

ci-docker-build: ci-docker-auth
	@docker build -f Dockerfile \
		--no-cache \
		-t $(DOCKER_REPOSITORY):$(GIT_HASH) .

ci-docker-push: ci-docker-auth
	docker tag $(DOCKER_REPOSITORY):$(GIT_HASH) $(DOCKER_REPOSITORY):latest
	docker push $(DOCKER_REPOSITORY)