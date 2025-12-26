FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install git for setuptools-scm version detection
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Create non-root user with UID/GID 1000
RUN groupadd -g 1000 appgroup && useradd -u 1000 -g 1000 -m appuser

WORKDIR /app
COPY --chown=1000:1000 . .
RUN chown 1000:1000 /app

USER 1000:1000
RUN git config --global --add safe.directory /app && uv sync

EXPOSE 80
CMD ["uv", "run", "uvicorn", "wenfire.app:app", "--host", "0.0.0.0", "--port", "80"]
