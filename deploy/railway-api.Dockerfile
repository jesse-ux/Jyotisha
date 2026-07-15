FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install -r requirements.txt

COPY SKILL.md mcp_server.py ./
COPY assets ./assets
COPY jyotish_vedic ./jyotish_vedic
COPY references ./references
COPY scripts ./scripts
COPY skills ./skills

CMD ["sh", "-c", "exec python scripts/jyotish_api_server.py --host 0.0.0.0 --port \"${PORT:-5200}\""]
