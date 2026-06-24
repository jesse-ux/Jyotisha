#!/usr/bin/env python3
"""Check whether the Jyotish web app is ready for PWA/Pake/Tauri packaging."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "jyotish-app"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(condition: bool, label: str, failures: list[str]) -> None:
    if not condition:
        failures.append(label)


def probe_command(binary: str, args: list[str] | None = None) -> dict:
    path = shutil.which(binary)
    result = {
        "binary": binary,
        "available": bool(path),
        "path": path,
        "version": None,
    }
    if not path:
        return result
    try:
        completed = subprocess.run(
            [path, *(args or ["--version"])],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
        result["version"] = (completed.stdout or completed.stderr).strip().splitlines()[0] if (completed.stdout or completed.stderr).strip() else ""
    except Exception as exc:
        result["version"] = f"probe_failed: {exc}"
    return result


def toolchain_probe() -> dict:
    probes = {
        "node": probe_command("node"),
        "npm": probe_command("npm"),
        "rustc": probe_command("rustc"),
        "cargo": probe_command("cargo"),
        "xcodebuild": probe_command("xcodebuild", ["-version"]),
        "pake": probe_command("pake"),
        "tauri": probe_command("tauri"),
    }
    xcode_version = probes["xcodebuild"].get("version") or ""
    xcode_ready = bool(probes["xcodebuild"]["available"] and "requires Xcode" not in xcode_version)
    return {
        "non_destructive": True,
        "note": "Probe only checks local CLI presence/version; it does not run npm build, pake, tauri build, signing, notarization, or generate packages.",
        "license_gate": {
            "pake": "Pake upstream is GPL-3.0; review distribution compatibility before shipping a bundled desktop app.",
            "tauri": "Tauri app distribution still needs platform permissions, sidecar lifecycle design, signing_notarization, and Apple Developer decisions on macOS.",
        },
        "commands": probes,
        "readiness": {
            "pwa": True,
            "pake": bool(probes["node"]["available"] and probes["npm"]["available"] and probes["rustc"]["available"] and probes["cargo"]["available"] and probes["pake"]["available"]),
            "tauri": bool(probes["node"]["available"] and probes["npm"]["available"] and probes["rustc"]["available"] and probes["cargo"]["available"] and probes["tauri"]["available"]),
            "macos_signing_notarization": xcode_ready,
        },
        "warnings": [
            "xcodebuild exists but full Xcode is not selected; macOS signing_notarization is not ready."
        ] if probes["xcodebuild"]["available"] and not xcode_ready else [],
    }


def main() -> int:
    failures: list[str] = []
    package = json.loads(read(APP / "package.json"))
    manifest = json.loads(read(APP / "public" / "manifest.webmanifest"))
    sw = read(APP / "public" / "sw.js")
    html = read(APP / "index.html")
    api_server = read(ROOT / "scripts" / "jyotish_api_server.py")
    main_js = read(APP / "main.js")
    click_smoke = read(ROOT / "tests" / "run_frontend_click_smoke.py")

    scripts = package.get("scripts", {})
    require("build" in scripts, "jyotish-app/package.json missing build script", failures)
    require("preview" in scripts, "jyotish-app/package.json missing preview script", failures)
    require(manifest.get("name") == "Jyotish Vedic Astrology", "manifest name mismatch", failures)
    require(manifest.get("display") == "standalone", "manifest display must be standalone", failures)
    require(manifest.get("scope") == "/", "manifest scope must be /", failures)
    require(manifest.get("start_url") == "/", "manifest start_url must be /", failures)
    require(bool(manifest.get("theme_color")), "manifest theme_color missing", failures)
    require(any(icon.get("src") == "/pwa-icon.svg" for icon in manifest.get("icons", [])), "manifest icon missing", failures)
    require("CACHE_NAME = 'jyotish-shell-v1'" in sw, "service worker cache name missing", failures)
    require("url.pathname.startsWith('/api/')" in sw, "service worker must bypass API requests", failures)
    require("caches.match('/index.html')" in sw, "service worker fallback missing", failures)
    require('rel="manifest"' in html and "/manifest.webmanifest" in html, "index missing manifest link", failures)
    require("/pwa-icon.svg" in html, "index missing app icon", failures)
    require("JYOTISH_API_HOST', '127.0.0.1'" in api_server, "API host default must stay loopback", failures)
    require("Trust Center" in main_js and "Local-first" in main_js, "Trust Center status missing", failures)
    require("pwa-install" in main_js and "promptPWAInstall" in main_js, "PWA install action missing", failures)
    require(bool(re.search(r"127\.0\.0\.1:5200", main_js)), "Trust Center must show loopback API boundary", failures)
    require("tests/run_frontend_click_smoke.py" in read(ROOT / "scripts" / "run_quality_gate.py"), "quality gate must run browser click smoke", failures)
    require("--mode" in click_smoke and "all" in click_smoke, "click smoke must support --mode all", failures)
    require("offline_recovery_guidance_visible" in click_smoke, "click smoke must verify offline recovery guidance", failures)
    require("manifest.webmanifest" in click_smoke and "serviceWorker" in click_smoke, "click smoke must verify PWA installed shell", failures)

    if failures:
        print(json.dumps({"valid": False, "failures": failures}, ensure_ascii=False, indent=2))
        return 1
    first_launch_checks = [
        {
            "path": "PWA installed shell",
            "command": "python3 tests/run_frontend_click_smoke.py --mode all",
            "expected": "manifest.webmanifest, serviceWorker, mobile shell, online workflow, and offline recovery guidance",
        },
        {
            "path": "Pake first launch",
            "command": "cd jyotish-app && npm run build && npm run preview -- --host 127.0.0.1 --port 4173",
            "expected": "URL shell can open the built app; local API still needs python3 scripts/jyotish_api_server.py on 127.0.0.1:5200",
        },
        {
            "path": "Tauri sidecar readiness",
            "command": "python3 scripts/desktop_packaging_preflight.py",
            "expected": "loopback API boundary, sidecar route, manifest, service worker, and Trust Center remain visible before scaffolding",
        },
    ]
    print(json.dumps({
        "valid": True,
        "packaging_paths": ["pwa", "pake-url-shell", "tauri-sidecar-spike"],
        "app_dir": str(APP),
        "api_default": "127.0.0.1:5200",
        "first_launch_checks": first_launch_checks,
        "toolchain_probe": toolchain_probe(),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
