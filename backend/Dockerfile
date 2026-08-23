# ── Build stage — install dependencies ───────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runner
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code (tests excluded via .dockerignore)
COPY . .

# Make startup script executable
RUN chmod +x start.sh

EXPOSE 8000

# Runs migrations then starts the server
CMD ["./start.sh"]
