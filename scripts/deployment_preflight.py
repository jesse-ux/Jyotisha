#!/usr/bin/env python3
"""Check ordinary-user delivery paths before publishing a Jyotish build."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "jyotish-app"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(condition: bool, label: str, failures: list[str]) -> None:
    if not condition:
        failures.append(label)


def delivery_matrix() -> list[dict]:
    return [
        {
            "id": "local-dev",
            "label": "Local dev",
            "user_url": "http://127.0.0.1:5173",
            "commands": [
                ".venv/bin/python scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200",
                "cd jyotish-app && npm run dev -- --host 127.0.0.1 --port 5173",
            ],
            "api_required": True,
            "scope": "Full web/app user experience with local API.",
        },
        {
            "id": "docker-compose",
            "label": "Docker Compose",
            "user_url": "http://localhost:5300",
            "commands": ["docker compose up -d"],
            "api_required": True,
            "scope": "Bundled API + web shell for local ordinary-user trials.",
        },
        {
            "id": "static-demo-pwa",
            "label": "Static demo / PWA",
            "user_url": "https://<static-host>/",
            "commands": ["cd jyotish-app && npm run build"],
            "api_required": False,
            "scope": "public demo shell; full advanced techniques require a local API service.",
        },
        {
            "id": "desktop-shell",
            "label": "Desktop shell",
            "user_url": "pwa://installed-app or pake://local-url",
            "commands": [
                "cd jyotish-app && npm run build && npm run preview -- --host 127.0.0.1 --port 4173",
                "python3 scripts/desktop_packaging_preflight.py",
            ],
            "api_required": True,
            "scope": "PWA/Pake now; Tauri sidecar only after API lifecycle and signing are fixed.",
        },
    ]


def main() -> int:
    failures: list[str] = []
    readme = read(ROOT / "README.md")
    dockerfile = read(ROOT / "Dockerfile")
    compose = read(ROOT / "docker-compose.yml")
    package = json.loads(read(APP / "package.json"))
    manifest = json.loads(read(APP / "public" / "manifest.webmanifest"))
    sw = read(APP / "public" / "sw.js")
    index_html = read(APP / "index.html")
    main_js = read(APP / "main.js")

    require("普通用户交付形态" in readme, "README missing ordinary-user delivery matrix", failures)
    require("python3 scripts/deployment_preflight.py" in readme, "README missing deployment preflight command", failures)
    require("static_demo_boundary_visible" in readme, "README missing static demo boundary marker", failures)
    require('id="static-demo-boundary"' in index_html, "static demo capability boundary must be visible on first screen", failures)
    require("renderStaticDemoBoundary" in main_js, "Trust Center must render static demo capability boundary", failures)
    require("http://localhost:5300" in compose, "docker-compose missing ordinary web URL note", failures)
    require("python3 scripts/deployment_preflight.py" in dockerfile, "Dockerfile must run deployment preflight", failures)
    require("build" in package.get("scripts", {}), "jyotish-app missing build script", failures)
    require("preview" in package.get("scripts", {}), "jyotish-app missing preview script", failures)
    require(manifest.get("display") == "standalone", "PWA manifest must remain standalone", failures)
    require("url.pathname.startsWith('/api/')" in sw, "service worker must bypass API requests", failures)

    result = {
        "valid": not failures,
        "failures": failures,
        "delivery_matrix": delivery_matrix(),
        "static_demo_boundary_visible": "static shell is labeled; local API-only capabilities are listed for ordinary users.",
        "ordinary_user_note": "公开演示环境只能完整展示静态壳；完整高级技法需要本地 API 服务。",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
