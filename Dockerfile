# ─── Jyotish Vedic Astrology Docker Image ───
# Build:  docker build -t jyotish-vedic .
# Run:    docker run -p 5200:5200 jyotish-vedic
# API:    http://localhost:5200/api/health

FROM python:3.11-slim

LABEL org.opencontainers.image.title="jyotish-vedic-astrology"
LABEL org.opencontainers.image.description="Vedic Astrology (Jyotish) calculation engine with AI-ready APIs"
LABEL org.opencontainers.image.source="https://github.com/732642856/yinduzhanxing"
LABEL org.opencontainers.image.licenses="MIT"

# ─── System deps ───
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ─── Python deps ───
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Application ───
COPY jyotish_vedic/ ./jyotish_vedic/
COPY scripts/      ./scripts/
COPY jyotish-app/  ./jyotish-app/
COPY mcp_server.py ./mcp_server.py
COPY assets/       ./assets/

# ─── Verify installation ───
RUN python -c "from jyotish_vedic import __version__; print(f'Jyotish v{__version__} ready')"
RUN python3 scripts/deployment_preflight.py

# ─── Ports ───
# 5200: REST API server
# 5300: jyotish-app static web frontend
EXPOSE 5200 5300

# ─── Health check ───
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5200/api/health || exit 1

# ─── Entry point: start both API + web frontend ───
CMD ["sh", "-c", "\
    echo 'Starting Jyotish API server on :5200...' && \
    python3 scripts/jyotish_api_server.py --port 5200 & \
    echo 'Starting jyotish-app on :5300...' && \
    cd jyotish-app && python3 -m http.server 5300 --bind 0.0.0.0 & \
    wait"]
