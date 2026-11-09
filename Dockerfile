# ─── Stage 1: Build / install dependencies ─────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install only production deps into an isolated prefix so dev-only packages
# (pytest, etc.) never land in the final image.
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Stage 2: Lean runtime image ────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Create non-root user BEFORE copying files so chown is cheap.
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app

# Copy installed packages from builder stage.
COPY --from=builder /install /usr/local

# Copy application source (excludes dev files via .dockerignore).
COPY --chown=appuser:appuser . .

USER 10001

EXPOSE 5500

# Liveness probe: curl must succeed for the container to be healthy.
# curl is included in python:3.12-slim; no extra install needed.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5500/healthz')" || exit 1

# Graceful shutdown: uvicorn handles SIGTERM natively.
# --workers defaults to 1; override with UVICORN_WORKERS env var for multi-core.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5500"]
