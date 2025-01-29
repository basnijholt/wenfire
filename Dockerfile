FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
COPY . .
RUN uv sync
EXPOSE 80
CMD ["uv", "run", "uvicorn", "wenfire.app:app", "--host", "0.0.0.0", "--port", "80"]
