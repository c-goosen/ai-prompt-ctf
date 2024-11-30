# Dockerfile
# Uses multi-stage builds requiring Docker 17.05 or higher
# See https://docs.docker.com/develop/develop-images/multistage-build/


# Creating a python base with shared environment variables
FROM python:3.12 AS python-base
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# builder-base is used to build dependencies
FROM python-base AS builder-base
RUN buildDeps="build-essential" \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
        curl vim git python3-dev
RUN apt-get install -y --no-install-recommends $buildDeps
RUN rm -rf /var/lib/apt/lists/*

# Install Poetry - respects $POETRY_VERSION & $POETRY_HOME
ENV POETRY_VERSION=1.7.1
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=${POETRY_HOME} python3 - --version ${POETRY_VERSION} && \
    chmod a+x /opt/poetry/bin/poetry

# We copy our Python requirements here to cache them
# and install only runtime deps using poetry
WORKDIR $PYSETUP_PATH
COPY ./poetry.lock ./pyproject.toml ./
#RUN poetry install --only main  # respects

RUN poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true
RUN poetry run python -m pip wheel setuptools
#RUN poetry run python -m pip install pandas==2.2.3 --no-use-pep517
RUN poetry install --no-root --no-interaction --only main

FROM python:3.12 AS production
ENV FASTAPI_ENV=production

EXPOSE 8000/tcp

COPY --from=builder-base $VENV_PATH $VENV_PATH
RUN adduser THM_PASSWORD --allow-bad-names

# Create user with the name poetry
RUN groupadd -g 1500 poetry && \
    useradd -m -u 1500 -g poetry poetry

COPY --chown=poetry:poetry ./ /app
COPY --chown=poetry:poetry .env/ /app
USER poetry
WORKDIR /app
RUN python -m nltk.downloader punkt
# ENTRYPOINT /docker-entrypoint.sh $0 $@

ENTRYPOINT FORWARDED_ALLOW_IPS="*" gunicorn -k uvicorn.workers.UvicornWorker app:app -b 0.0.0.0:8000 --forwarded-allow-ips '*' --workers 2
CMD FORWARDED_ALLOW_IPS="*" gunicorn -k uvicorn.workers.UvicornWorker app:app -b 0.0.0.0:8000 --forwarded-allow-ips '*' --workers 2

