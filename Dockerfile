# VERSION must be passed at build time: --build-arg VERSION=$(uvx --from setuptools-scm python -m setuptools_scm)
# It is baked into the installed dist-info so importlib.metadata can read it at runtime
# without needing the .git directory to be present in the image.
ARG VERSION=0.0.0+unknown
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
ARG VERSION

# Install system dependencies: sqlite3 for DB ops, p7zip for extracting system CSVs
RUN apt-get update \
 && apt-get install -y --no-install-recommends sqlite3 p7zip-full \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1
# Copy files from the cache instead of hard-linking (required when cache is a mounted volume)
ENV UV_LINK_MODE=copy
# Omit development dependencies (ruff, etc.)
ENV UV_NO_DEV=1

# Install dependencies only (without the project itself) first.
# This layer is cached independently of the project source, so changing
# application code does not re-trigger a full dependency install.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy the project source and config files needed to install the package itself.
COPY ptn/ /app/ptn/
COPY pyproject.toml uv.lock /app/
ARG VERSION
RUN --mount=type=cache,target=/root/.cache/uv \
    SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION} uv sync --locked

# Place the venv's executables at the front of PATH so the entry point is found
ENV PATH="/app/.venv/bin:$PATH"

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
