FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Create non-root user with UID/GID 1000
RUN groupadd -g 1000 appgroup && useradd -u 1000 -g 1000 -m appuser

WORKDIR /app
COPY --chown=1000:1000 . .
RUN chown 1000:1000 /app

# Remove .git file (submodule pointer that won't work in container)
# and set fallback version for hatch-vcs
RUN rm -f .git

USER 1000:1000
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0
RUN uv sync

EXPOSE 80
CMD ["uv", "run", "uvicorn", "wenfire.app:app", "--host", "0.0.0.0", "--port", "80"]
