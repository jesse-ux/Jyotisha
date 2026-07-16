from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_railway_services_use_the_product_frontend_and_dynamic_ports() -> None:
    web = (ROOT / "deploy" / "railway-web.Dockerfile").read_text(encoding="utf-8")
    api = (ROOT / "deploy" / "railway-api.Dockerfile").read_text(encoding="utf-8")

    assert "COPY frontend/package.json frontend/package-lock.json" in web
    assert "--hostname 0.0.0.0" in web and "${PORT:-3000}" in web
    assert "next-env.d.ts" not in web

    assert "COPY SKILL.md mcp_server.py" in api
    assert "--host 0.0.0.0" in api and "${PORT:-5200}" in api
    assert "http.server" not in api


def test_web_image_copies_postcss_config_before_building_frontend() -> None:
    web = (ROOT / "deploy" / "railway-web.Dockerfile").read_text(encoding="utf-8")
    config_copy = "COPY frontend/next.config.ts frontend/postcss.config.mjs frontend/tsconfig.json ./"

    assert config_copy in web
    assert web.index(config_copy) < web.index("RUN npm run build")
