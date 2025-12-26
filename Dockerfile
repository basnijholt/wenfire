FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Create non-root user with UID/GID 1000
RUN groupadd -g 1000 appgroup &&     useradd -u 1000 -g 1000 -m appuser

WORKDIR /app
COPY --chown=1000:1000 . .

USER 1000:1000
RUN uv sync

EXPOSE 80
CMD ["uv", "run", "uvicorn", "wenfire.app:app", "--host", "0.0.0.0", "--port", "80"]
