# Desktop Packaging Spike — Jyotish App

Date: 2026-06-23

## Decision

Use a staged desktop path:

1. **Now: PWA install** for the current Vite app. This is already live through `manifest.webmanifest`, `sw.js`, and the Trust Center install state.
2. **Short term: Pake shell** for a lightweight Mac/Windows/Linux desktop wrapper when the user can run both local services:
   - Vite/static app served from `jyotish-app/dist` or `npm run preview`.
   - Python API served by `scripts/jyotish_api_server.py` on `127.0.0.1:5200`.
3. **Later: Tauri shell with sidecar** when the app needs a one-click bundle that starts the Python API automatically and ships stricter desktop permissions.

This avoids prematurely adding Rust/Tauri scaffolding before the local API sidecar and signing strategy are fixed.

## Product Requirements

- Desktop shell must keep the current local-first data model: browser storage, local Python API, no cloud dependency for chart calculation.
- API calls must stay local-only by default: `127.0.0.1:5200` or explicit user override.
- Packaging must preserve installability signals: app name, icon, theme color, standalone display, cached shell, and Trust Center notes.
- PDF/HTML/JSON export and local case libraries must work in the shell.
- Offline behavior can cache the UI shell, but Python-backed calculations still require the local API process.

## Pake Path

Use when speed matters and the user accepts running the API separately.

Candidate flow:

```bash
cd jyotish-app
npm run build
npm run preview -- --host 127.0.0.1 --port 4173
python3 ../scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200
```

Then package the local web URL with Pake using the project icon/name. The exact Pake command should be pinned only after verifying the installed Pake CLI version, because CLI flags can change.

Risk: Pake wraps a URL. It does not solve local API lifecycle, signing/notarization, or multi-process supervision by itself.

## Tauri Path

Use when the app needs a true desktop artifact.

Tauri is the better long-term fit because it uses the system webview, has a security-focused Rust base, supports arbitrary frontends, and can model desktop permissions. It can later run the Python API as a sidecar or replace it with a Rust/native command layer.

Candidate architecture:

- `src-tauri/tauri.conf.json` points `frontendDist` to `../dist` and `devUrl` to Vite.
- A sidecar starts `python3 scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200`.
- Frontend still talks to `http://127.0.0.1:5200/api/...`.
- Permissions initially allow only app shell, local file download/export, and loopback HTTP.

Risk: Requires Rust toolchain, platform signing decisions, API sidecar packaging, and explicit lifecycle handling. Do not add scaffolding until these are tested on the target OS.

## Preflight Checklist

Run:

```bash
python3 scripts/desktop_packaging_preflight.py
python3 tests/run_frontend_click_smoke.py --mode all
```

Expected output:

- Vite package has `build` and `preview`.
- Manifest has name, standalone display, scope, start URL, theme color, and icon.
- Service worker caches shell files and excludes `/api/`.
- HTML links the manifest and icon.
- API server binds to `127.0.0.1` by default.
- Trust Center exposes install/local-first status.
- Browser click smoke reports `offline_recovery_guidance_visible: true` when the API is absent.

## 安装后首次打开

普通用户路径必须先验证“壳能打开”，再验证“本地 API 可诊断”：

1. **PWA installed shell**：运行 `python3 tests/run_frontend_click_smoke.py --mode all`。预期结果包含 `manifest.webmanifest`、`serviceWorker: true`、移动首屏检查、在线核心流程和离线恢复提示。
2. **Pake first launch**：先 `cd jyotish-app && npm run build && npm run preview -- --host 127.0.0.1 --port 4173`，再启动 `python3 ../scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200`。Pake 只包装 URL，不负责 Python API 生命周期。
3. **Tauri sidecar readiness**：在真正生成 `src-tauri` 前先跑 `python3 scripts/desktop_packaging_preflight.py`，确认 loopback API、manifest、service worker、Trust Center、离线恢复都仍可检查。若 `offline_recovery_guidance_visible` 不为 true，不应进入 Tauri sidecar 打包。

## Next Build Step

After this spike, the next practical step is a Pake smoke artifact only if the machine has Pake installed. If not, keep PWA as the release path and move to the ephemeris abstraction spike.
