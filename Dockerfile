
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY . .
RUN uv sync
EXPOSE 80
CMD ["uvicorn", "wenfire.app:app", "--host", "0.0.0.0", "--port", "80"]
