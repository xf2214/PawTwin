FROM node:24-bookworm-slim AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.9.9 AS uv-bin
FROM python:3.12-slim-bookworm AS runtime
COPY --from=uv-bin /uv /uvx /usr/local/bin/
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PAWTWIN_MODE=local \
    PAWTWIN_FRONTEND_DIST=/app/frontend/dist \
    PATH="/app/.venv/bin:$PATH"
COPY pyproject.toml uv.lock .python-version ./
COPY backend/ ./backend/
RUN uv sync --frozen --no-dev --no-editable \
    && useradd --create-home --uid 10001 app
COPY --from=frontend-build /build/frontend/dist/ ./frontend/dist/
USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)"
CMD ["uvicorn", "pawtwin.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
