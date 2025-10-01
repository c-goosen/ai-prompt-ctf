# Dockerfile
# Uses multi-stage builds requiring Docker 17.05 or higher
# See https://docs.docker.com/develop/develop-images/multistage-build/

# Creating a python base with shared environment variables
FROM python:3.12 AS python-base
ENV UV_CACHE_DIR="/opt/uv-cache" \
    UV_PROJECT_ENVIRONMENT="/opt/venv" \
    PYSETUP_PATH="/opt/pysetup"

ENV PATH="/opt/venv/bin:$PATH"

# builder-base is used to build dependencies
FROM python-base AS builder-base
RUN buildDeps="build-essential" \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
        curl vim git python3-dev
RUN apt-get install -y --no-install-recommends $buildDeps
RUN rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# We copy our Python requirements here to cache them
# and install only runtime deps using uv
WORKDIR $PYSETUP_PATH
COPY ./uv.lock ./pyproject.toml ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12 AS production
ENV FASTAPI_ENV=production

EXPOSE 8000/tcp

# Copy the virtual environment from the builder stage
COPY --from=builder-base /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN adduser THM_PASSWORD --allow-bad-names

# Create user with the name appuser
RUN groupadd -g 1500 appuser && \
    useradd -m -u 1500 -g appuser appuser

COPY --chown=appuser:appuser ./ /app
COPY --chown=appuser:appuser .env/ /app
USER appuser
WORKDIR /app

# Download NLTK data
RUN python -m nltk.downloader punkt

ENTRYPOINT FORWARDED_ALLOW_IPS="*" gunicorn -k uvicorn.workers.UvicornWorker app:app -b 0.0.0.0:8000 --forwarded-allow-ips '*' --workers 2
CMD FORWARDED_ALLOW_IPS="*" gunicorn -k uvicorn.workers.UvicornWorker app:app -b 0.0.0.0:8000 --forwarded-allow-ips '*' --workers 2