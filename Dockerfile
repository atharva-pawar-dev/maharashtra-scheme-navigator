# =============================================================================
# MAHARASHTRA SCHEME NAVIGATOR — HARDENED MULTI-STAGE CONTAINERFILE
# =============================================================================

# Stage 1: Build Dependencies
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip && \
    pip install .

# -----------------------------------------------------------------------------
# Stage 2: Minimal Hardened Runtime
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production

# Install minimal OS runtime dependencies (curl for healthcheck, glib for image processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user and group (UID 10001)
RUN groupadd -g 10001 msnuser && \
    useradd -u 10001 -g msnuser -s /sbin/nologin -d /app msnuser

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application assets with non-root ownership
COPY --chown=msnuser:msnuser src ./src
COPY --chown=msnuser:msnuser static ./static
COPY --chown=msnuser:msnuser data ./data
COPY --chown=msnuser:msnuser configs ./configs

# Ensure writable data directory for non-root user
RUN mkdir -p /app/data && chown -R msnuser:msnuser /app/data

# Switch to unprivileged non-root user
USER 10001:10001

EXPOSE 8000

# Container liveness healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

ENTRYPOINT ["uvicorn", "scheme_navigator.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
