#!/usr/bin/env python3
"""Browser click smoke for the Jyotish app core interactive workflows."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "jyotish-app"
API_SERVER = ROOT / "scripts" / "jyotish_api_server.py"
TMP = Path(os.environ.get("TMPDIR") or tempfile.gettempdir())
SYSTEM_CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
OFFLINE_CONSOLE_ERROR_MARKERS = [
    "ERR_CONNECTION_REFUSED",
    "ERR_FAILED",
    "Failed to load resource",
]
EXPECTED_TRUST_HEALTH_STATUS = "健康检查通过：本地 API 服务、能力目录和 PWA 安装壳状态已记录"


class ClickSmokeTimeoutError(TimeoutError):
    """Raised when the full browser click smoke exceeds the command timeout."""


def free_ports(count: int = 2) -> list[int]:
    sockets: list[socket.socket] = []
    try:
        for _ in range(count):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
        return [sock.getsockname()[1] for sock in sockets]
    finally:
        for sock in sockets:
            sock.close()


def run(cmd: list[str], *, cwd: Path = ROOT, timeout: int = 12, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=check)


def curl_status(url: str, *, timeout: int = 4) -> tuple[bool, str]:
    completed = run(
        ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", url],
        timeout=timeout,
        check=False,
    )
    code = completed.stdout.strip()
    return completed.returncode == 0 and code.startswith(("2", "3", "4")), completed.stderr.strip() or code


def wait_for_url(url: str, *, timeout: float = 14.0, logs: list[Path] | None = None) -> None:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        ok, last = curl_status(url)
        if ok:
            return
        time.sleep(0.25)
    log_text = ""
    for log in logs or []:
        if log.exists():
            log_text += f"\n--- {log} ---\n{log.read_text(encoding='utf-8', errors='replace')[-4000:]}"
    raise RuntimeError(f"Timed out waiting for {url}: {last}{log_text}")


def start_process(cmd: list[str], cwd: Path, log_path: Path) -> subprocess.Popen[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = log_path.open("w", encoding="utf-8")
    return subprocess.Popen(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, text=True)


def stop_process(process: subprocess.Popen[str] | None) -> None:
    if process is None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def force_stop_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def process_snapshot(name: str, process: subprocess.Popen[str] | None, log_path: Path) -> dict[str, Any]:
    if process is None:
        return {"name": name, "started": False, "running": False}
    return {
        "name": name,
        "started": True,
        "pid": process.pid,
        "returncode": process.poll(),
        "running": process.poll() is None,
        "log_tail": read_log_tail(log_path),
    }


def run_with_timeout(callback, timeout_seconds: int):
    if timeout_seconds <= 0 or not hasattr(signal, "SIGALRM"):
        return callback()

    def _handle_timeout(signum, frame):
        raise ClickSmokeTimeoutError(f"click smoke timed out after {timeout_seconds}s")

    previous = signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(timeout_seconds)
    try:
        return callback()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def read_log_tail(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[-4000:]


def browser_launch_options() -> dict[str, Any]:
    if SYSTEM_CHROME.exists():
        return {"executable_path": str(SYSTEM_CHROME), "headless": True}
    return {"channel": "chrome", "headless": True}


def split_expected_offline_console_errors(messages: list[str]) -> tuple[list[str], list[str]]:
    expected: list[str] = []
    unexpected: list[str] = []
    for message in messages:
        if any(marker in message for marker in OFFLINE_CONSOLE_ERROR_MARKERS):
            expected.append(message)
        else:
            unexpected.append(message)
    return expected, unexpected


async def assert_pwa_surface(page: Any) -> dict[str, Any]:
    manifest_href = await page.locator('link[rel="manifest"]').get_attribute("href", timeout=5000)
    if not manifest_href or "manifest.webmanifest" not in manifest_href:
        raise AssertionError(f"manifest.webmanifest link missing: {manifest_href}")
    sw_capable = await page.evaluate("() => 'serviceWorker' in navigator")
    return {"manifest": manifest_href, "serviceWorker": bool(sw_capable)}


async def run_browser_clicks(web_base: str, api_base: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    console_errors: list[str] = []
    downloads: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(**browser_launch_options())
        context = await browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 820})
        page = await context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        await page.goto(web_base, wait_until="networkidle")
        pwa_surface = await assert_pwa_surface(page)
        await page.evaluate(
            """apiBase => {
              localStorage.setItem('YINDUZHANXING_API_BASE', apiBase);
              window.YINDUZHANXING_API_BASE = apiBase;
            }""",
            api_base,
        )
        await page.reload(wait_until="networkidle")

        await page.click("#first-use-demo")
        await page.click("#btn-calculate")
        await page.wait_for_selector("#page-chart.active", timeout=20000)
        chart_status = (await page.locator("#chart-compute-status").inner_text(timeout=5000)).strip()
        if "undefined" in await page.locator("body").inner_text(timeout=5000):
            raise AssertionError("click_smoke found visible undefined text after chart generation")

        await page.click(".ai-fab")
        await page.fill("#ai-input", "请概述这个星盘")
        await page.keyboard.press("Enter")
        await page.wait_for_function(
            """() => document.querySelector('.ai-messages')?.innerText.includes('/api/chat')
              || document.querySelector('.ai-messages')?.innerText.includes('OPENAI_API_KEY')""",
            timeout=12000,
        )
        ai_text = await page.locator(".ai-messages").inner_text(timeout=5000)
        for required in ["/api/chat", "OPENAI_API_KEY", "不要把 OpenAI API key 放进浏览器"]:
            if required not in ai_text:
                raise AssertionError(f"click_smoke AI text missing {required}")
        await page.click(".ai-panel-close")
        await page.wait_for_selector(".ai-panel.open", state="detached", timeout=5000)

        await page.click("#btn-export")
        await page.click('.export-item[data-format="html"]')
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#export-status')?.innerText || '';
              return text.includes('HTML 报告已开始下载') || text.includes('Trust Center') || text.includes('导出失败');
            }""",
            timeout=10000,
        )
        export_status = (await page.locator("#export-status").inner_text(timeout=5000)).strip()
        downloads.append("html-export-clicked")

        await page.click('.tab-btn[data-tab="transit-compare"]')
        await page.fill("#transit-start", "2026-06-23")
        await page.fill("#transit-end", "2026-06-24")
        await page.click("#btn-run-transit")
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#transit-result')?.innerText || '';
              return text.includes('过境') || text.includes('触发') || text.includes('Trust Center') || text.includes('无显著');
            }""",
            timeout=16000,
        )
        transit_text = (await page.locator("#transit-result").inner_text(timeout=5000)).strip()

        await page.click('.tab-btn[data-tab="synastry"]')
        await page.fill("#synastry-partner-date", "1991-02-02")
        await page.fill("#synastry-partner-time", "08:30")
        await page.fill("#synastry-partner-tz", "5.5")
        await page.click("#btn-run-synastry-full")
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#synastry-result')?.innerText || '';
              return text.includes('合盘计算暂不可用') || text.includes('Trust Center') || text.includes('Ashtakoot') || text.includes('匹配');
            }""",
            timeout=16000,
        )
        synastry_text = (await page.locator("#synastry-result").inner_text(timeout=5000)).strip()

        await page.click('.tab-btn[data-tab="prashna"]')
        await page.fill("#prashna-question", "这个工作机会是否值得争取？")
        await page.click("#btn-run-prashna")
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#prashna-result')?.innerText || '';
              return text.includes('问事计算暂不可用') || text.includes('Trust Center') || text.includes('Prashna') || text.includes('结论');
            }""",
            timeout=16000,
        )
        prashna_text = (await page.locator("#prashna-result").inner_text(timeout=5000)).strip()

        await browser.close()

    actionable_tokens = ["Trust Center", "普通用户启动路径", "网页服务", "本地 API 服务"]
    recovery_surface_text = "\n".join([transit_text, synastry_text, prashna_text])
    return {
        "success": True,
        "chart_status": chart_status,
        "ai_policy": "server_side_only",
        "html_download": downloads[0] if downloads else "",
        "export_status": export_status,
        "transit_checked": bool(transit_text),
        "synastry_checked": bool(synastry_text),
        "prashna_checked": bool(prashna_text),
        "pwa_surface": pwa_surface,
        "online_recovery_guidance_visible": any(token in recovery_surface_text for token in actionable_tokens),
        "console_errors": console_errors,
    }


async def fill_demo_chart(page: Any, api_base: str | None = None) -> None:
    if api_base:
        await page.evaluate(
            """apiBase => {
              localStorage.setItem('YINDUZHANXING_API_BASE', apiBase);
              window.YINDUZHANXING_API_BASE = apiBase;
            }""",
            api_base,
        )
        await page.reload(wait_until="networkidle")
    await page.click("#first-use-demo")
    await page.click("#btn-calculate")
    await page.wait_for_selector("#page-chart.active", timeout=20000)


async def run_pdf_fallback_smoke(web_base: str, api_base: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    console_errors: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(**browser_launch_options())
        context = await browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 820})
        page = await context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        await page.goto(web_base, wait_until="networkidle")
        await fill_demo_chart(page, api_base)
        await page.evaluate(
            """() => {
              window.JyotishAPI.generateReportArtifact = async () => ({
                success: false,
                fallback: 'html',
                error: 'PDF renderer unavailable in click smoke',
                html_base64: btoa('<!doctype html><html><body>fallback</body></html>'),
                html_filename: 'pdf-fallback-smoke.html',
              });
            }"""
        )
        await page.click("#btn-export")
        await page.click('.export-item[data-format="pdf"]')
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#export-status')?.innerText || '';
              return text.includes('后端已生成 HTML 报告') && text.includes('已下载：') && text.includes('可直接打开，或用浏览器打印为 PDF');
            }""",
            timeout=12000,
        )
        pdf_status = (await page.locator("#export-status").inner_text(timeout=5000)).strip()
        await browser.close()

    return {
        "success": True,
        "pdf_fallback_checked": True,
        "pdf_status": pdf_status,
        "console_errors": console_errors,
    }


async def run_mobile_smoke(web_base: str, api_base: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    console_errors: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(**browser_launch_options())
        context = await browser.new_context(
            accept_downloads=True,
            is_mobile=True,
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
        )
        page = await context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        await page.goto(web_base, wait_until="networkidle")
        pwa_surface = await assert_pwa_surface(page)
        await page.evaluate(
            """apiBase => {
              localStorage.setItem('YINDUZHANXING_API_BASE', apiBase);
              window.YINDUZHANXING_API_BASE = apiBase;
            }""",
            api_base,
        )
        await page.reload(wait_until="networkidle")
        await page.click("#first-use-demo")
        await page.click("#btn-calculate")
        await page.wait_for_selector("#page-chart.active", timeout=20000)
        await page.click(".ai-fab")
        await page.wait_for_selector(".ai-panel.open", timeout=8000)
        body_text = await page.locator("body").inner_text(timeout=5000)
        viewport_state = await page.evaluate(
            """() => ({
              scrollWidth: document.documentElement.scrollWidth,
              clientWidth: document.documentElement.clientWidth,
              activePage: document.querySelector('#page-chart.active')?.id || '',
              overflowCandidates: Array.from(document.querySelectorAll('body *'))
                .filter(el => !el.closest('.section-tabs, .planets-table-wrap, .transit-table-wrap, .table-wrap, .panchanga-week-table-wrap, .ai-panel:not(.open)'))
                .map(el => {
                  const box = el.getBoundingClientRect();
                  return {
                    tag: el.tagName,
                    id: el.id || '',
                    cls: String(el.className || '').slice(0, 120),
                    left: Math.round(box.left),
                    right: Math.round(box.right),
                    width: Math.round(box.width),
                    text: (el.innerText || el.textContent || '').trim().slice(0, 80),
                  };
                })
                .filter(item => item.width > 0 && (item.left < -2 || item.right > document.documentElement.clientWidth + 2))
                .slice(0, 12),
              aiPanel: (() => {
                const box = document.querySelector('.ai-panel.open')?.getBoundingClientRect();
                return box ? {x: box.x, width: box.width, right: box.right} : null;
              })(),
            })"""
        )
        await browser.close()

    if "undefined" in body_text or "NaN" in body_text:
        raise AssertionError("mobile click_smoke found undefined/NaN text")
    if viewport_state["overflowCandidates"]:
        raise AssertionError(f"mobile click_smoke found horizontal overflow: {viewport_state}")
    ai_panel = viewport_state.get("aiPanel")
    if not ai_panel or ai_panel["x"] < -1 or ai_panel["right"] > 391:
        raise AssertionError(f"mobile click_smoke AI panel out of viewport: {ai_panel}")
    return {
        "success": True,
        "mobile": True,
        "active_page": viewport_state["activePage"],
        "pwa_surface": pwa_surface,
        "console_errors": console_errors,
    }


async def run_mobile_tab_smoke(web_base: str, api_base: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    console_errors: list[str] = []
    target_tabs = ["complete", "vargas", "synastry", "prashna", "transit-compare"]
    async with async_playwright() as p:
        browser = await p.chromium.launch(**browser_launch_options())
        context = await browser.new_context(
            is_mobile=True,
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
        )
        page = await context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        await page.goto(web_base, wait_until="networkidle")
        await fill_demo_chart(page, api_base)
        visited: list[str] = []
        for tab in target_tabs:
            await page.locator(f'.tab-btn[data-tab="{tab}"]').scroll_into_view_if_needed(timeout=5000)
            await page.click(f'.tab-btn[data-tab="{tab}"]')
            await page.wait_for_function(
                """tab => document.querySelector(`#tab-${tab}`)?.classList.contains('active')""",
                arg=tab,
                timeout=8000,
            )
            visited.append(tab)
        body_text = await page.locator("body").inner_text(timeout=5000)
        overflow_candidates = await page.evaluate(
            """() => Array.from(document.querySelectorAll('body *'))
              .filter(el => !el.closest('.section-tabs, .planets-table-wrap, .transit-table-wrap, .table-wrap, .panchanga-week-table-wrap, .ai-panel:not(.open)'))
              .map(el => {
                const box = el.getBoundingClientRect();
                return {tag: el.tagName, id: el.id || '', cls: String(el.className || '').slice(0,80), left: box.left, right: box.right, width: box.width};
              })
              .filter(item => item.width > 0 && (item.left < -2 || item.right > document.documentElement.clientWidth + 2))
              .slice(0, 8)"""
        )
        await browser.close()

    if "undefined" in body_text or "NaN" in body_text:
        raise AssertionError("mobile tab click_smoke found undefined/NaN text")
    if overflow_candidates:
        raise AssertionError(f"mobile tab click_smoke found overflow: {overflow_candidates}")
    return {
        "success": True,
        "mobile_tab_switch_checked": True,
        "visited_tabs": visited,
        "console_errors": console_errors,
    }


async def run_mobile_trust_export_smoke(web_base: str, api_base: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    console_errors: list[str] = []
    downloads: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(**browser_launch_options())
        context = await browser.new_context(
            accept_downloads=True,
            is_mobile=True,
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
        )
        page = await context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("download", lambda download: downloads.append(download.suggested_filename))
        await page.goto(web_base, wait_until="networkidle")
        await fill_demo_chart(page, api_base)

        await page.click("#btn-export")
        await page.wait_for_selector("#export-menu:not(.hidden)", timeout=5000)
        export_menu_state = await page.evaluate(
            """() => {
              const menu = document.querySelector('#export-menu');
              const menuBox = menu?.getBoundingClientRect();
              const items = Array.from(document.querySelectorAll('#export-menu .export-item')).map(item => {
                const box = item.getBoundingClientRect();
                return {
                  format: item.dataset.format,
                  text: item.innerText.trim(),
                  left: Math.round(box.left),
                  right: Math.round(box.right),
                  top: Math.round(box.top),
                  bottom: Math.round(box.bottom),
                  width: Math.round(box.width),
                  height: Math.round(box.height),
                };
              });
              return {
                menu: menuBox ? {
                  left: Math.round(menuBox.left),
                  right: Math.round(menuBox.right),
                  top: Math.round(menuBox.top),
                  bottom: Math.round(menuBox.bottom),
                  width: Math.round(menuBox.width),
                  height: Math.round(menuBox.height),
                } : null,
                items,
                viewport: { width: window.innerWidth, height: window.innerHeight },
              };
            }"""
        )
        await page.click('.export-item[data-format="json"]')
        await page.wait_for_function(
            """() => (document.querySelector('#export-status')?.innerText || '').includes('JSON 数据已开始下载')""",
            timeout=8000,
        )
        export_status = (await page.locator("#export-status").inner_text(timeout=5000)).strip()

        await page.click('.tab-btn[data-tab="provenance"]')
        await page.wait_for_function(
            """() => document.querySelector('#tab-provenance')?.classList.contains('active')""",
            timeout=8000,
        )
        await page.wait_for_selector(".trust-center-panel", timeout=8000)
        await page.locator('[data-action="trust-run-health"]').scroll_into_view_if_needed(timeout=5000)
        await page.click('[data-action="trust-run-health"]')
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#trust-center-status')?.innerText || '';
              return text.includes('健康检查通过') || text.includes('健康检查未通过');
            }""",
            timeout=12000,
        )
        health_status = (await page.locator("#trust-center-status").inner_text(timeout=5000)).strip()
        await page.locator('[data-action="trust-export-local"]').scroll_into_view_if_needed(timeout=5000)
        await page.click('[data-action="trust-export-local"]')
        await page.wait_for_function(
            """() => (document.querySelector('#trust-center-status')?.innerText || '').includes('已导出本地资料 JSON')""",
            timeout=8000,
        )
        trust_export_status = (await page.locator("#trust-center-status").inner_text(timeout=5000)).strip()
        trust_text = await page.locator(".trust-center-panel").inner_text(timeout=5000)
        body_text = await page.locator("body").inner_text(timeout=5000)
        overflow_candidates = await page.evaluate(
            """() => Array.from(document.querySelectorAll('#tab-provenance *, .export-dropdown *'))
              .filter(el => !el.closest('.section-tabs, .provenance-table-wrap, .panchanga-week-table-wrap, .panchanga-month-scroll'))
              .map(el => {
                const box = el.getBoundingClientRect();
                return {
                  tag: el.tagName,
                  id: el.id || '',
                  cls: String(el.className || '').slice(0, 90),
                  left: Math.round(box.left),
                  right: Math.round(box.right),
                  width: Math.round(box.width),
                  text: (el.innerText || el.textContent || '').trim().slice(0, 80),
                };
              })
              .filter(item => item.width > 0 && (item.left < -2 || item.right > document.documentElement.clientWidth + 2))
              .slice(0, 12)"""
        )
        await browser.close()

    menu = export_menu_state.get("menu")
    items = export_menu_state.get("items") or []
    if not menu or menu["left"] < -1 or menu["right"] > 391:
        raise AssertionError(f"mobile export menu out of viewport: {export_menu_state}")
    if {item.get("format") for item in items} != {"json", "html", "pdf", "svg", "png"}:
        raise AssertionError(f"mobile export menu missing items: {items}")
    clipped_items = [item for item in items if item["left"] < -1 or item["right"] > 391 or item["height"] < 34]
    if clipped_items:
        raise AssertionError(f"mobile export menu clipped items: {clipped_items}")
    trust_text_casefold = trust_text.casefold()
    for token in ["Trust Center", "Local-first", "运行健康检查", "导出本地资料", "安装为应用"]:
        if token.casefold() not in trust_text_casefold:
            raise AssertionError(f"mobile Trust Center missing {token}: {trust_text}")
    if "undefined" in body_text or "NaN" in body_text:
        raise AssertionError("mobile Trust/export smoke found undefined/NaN text")
    if overflow_candidates:
        raise AssertionError(f"mobile Trust/export smoke found overflow: {overflow_candidates}")
    if not any(name.startswith("jyotish-chart-") for name in downloads):
        raise AssertionError(f"mobile JSON export download missing: {downloads}")
    if not any(name.startswith("jyotish-local-data-") for name in downloads):
        raise AssertionError(f"mobile local data export download missing: {downloads}")
    return {
        "success": True,
        "mobile_trust_export_checked": True,
        "export_status": export_status,
        "health_status": health_status,
        "trust_export_status": trust_export_status,
        "downloads": downloads,
        "console_errors": console_errors,
    }


async def run_import_workspace_smoke(web_base: str, api_base: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    console_errors: list[str] = []
    downloads: list[str] = []
    import_text = "\n".join([
        "Date of Birth: 1990-06-15",
        "Time of Birth: 12:30",
        "Place of Birth: Delhi",
        "Latitude: 28.6139 N",
        "Longitude: 77.2090 E",
        "Timezone: UTC+5:30",
    ])
    async with async_playwright() as p:
        browser = await p.chromium.launch(**browser_launch_options())
        context = await browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 820})
        page = await context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        await page.goto(web_base, wait_until="networkidle")
        await page.evaluate(
            """apiBase => {
              localStorage.clear();
              localStorage.setItem('YINDUZHANXING_API_BASE', apiBase);
              window.YINDUZHANXING_API_BASE = apiBase;
            }""",
            api_base,
        )
        await page.reload(wait_until="networkidle")

        await page.fill("#chart-import-text", "Date of Birth: 1990-06-15")
        await page.click("#chart-import-parse")
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#chart-import-result')?.innerText || '';
              return text.includes('仍需手动补充') && text.includes('出生时间') && text.includes('出生地经纬度');
            }""",
            timeout=8000,
        )
        import_recovery = (await page.locator("#chart-import-result").inner_text(timeout=5000)).strip()

        await page.fill("#chart-import-text", import_text)
        await page.click("#chart-import-parse")
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#chart-import-result')?.innerText || '';
              return text.includes('已识别完整出生信息') && text.includes('质量分');
            }""",
            timeout=8000,
        )
        import_status = (await page.locator("#chart-import-result").inner_text(timeout=5000)).strip()
        await page.click("#chart-import-apply")
        await page.wait_for_function(
            """() => document.querySelector('#birth-year')?.value === '1990'
              && document.querySelector('#birth-month')?.value === '6'
              && document.querySelector('#birth-day')?.value === '15'
              && document.querySelector('#birth-time')?.value === '12:30'
              && document.querySelector('#birth-tz')?.value === '5.5'""",
            timeout=5000,
        )
        await page.click("#btn-calculate")
        await page.wait_for_selector("#page-chart.active", timeout=20000)
        chart_status = (await page.locator("#chart-compute-status").inner_text(timeout=5000)).strip()

        await page.click("#btn-save-chart")
        await page.wait_for_function(
            """() => document.querySelector('#btn-save-chart')?.innerText.includes('已保存')""",
            timeout=8000,
        )
        await page.click("#btn-back")
        await page.wait_for_selector("#page-input.active", timeout=8000)
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#saved-chart-panel')?.innerText || '';
              return text.includes('本地星盘库') && text.includes('1 个星盘');
            }""",
            timeout=8000,
        )
        saved_panel = (await page.locator("#saved-chart-panel").inner_text(timeout=5000)).strip()
        await page.click("#saved-chart-panel [data-open-saved-chart]")
        await page.wait_for_selector("#page-chart.active", timeout=8000)

        await page.click('.tab-btn[data-tab="provenance"]')
        await page.wait_for_function(
            """() => document.querySelector('#tab-provenance')?.classList.contains('active')""",
            timeout=8000,
        )
        await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_selector("#provenance-panel", state="attached", timeout=8000)
        await page.click('[data-action="workspace-save-current"]')
        await page.wait_for_function(
            """() => (document.querySelector('#case-workspace-counts')?.innerText || '').includes('Charts')
              || (document.querySelector('#workspace-case-list')?.innerText || '').includes('星盘')""",
            timeout=8000,
        )
        case_workspace = (await page.locator("#case-workspace-summary").inner_text(timeout=5000)).strip()
        await page.click('[data-action="workspace-select-visible"]')
        async with page.expect_download(timeout=8000) as selected_download_info:
            await page.click('[data-action="workspace-export-selected-cases"]')
        selected_download = await selected_download_info.value
        downloads.append(selected_download.suggested_filename)
        async with page.expect_download(timeout=8000) as library_download_info:
            await page.click('[data-action="workspace-export-cases"]')
        library_download = await library_download_info.value
        downloads.append(library_download.suggested_filename)
        await page.wait_for_function("() => true", timeout=250)
        body_text = await page.locator("body").inner_text(timeout=5000)
        await browser.close()

    if "undefined" in body_text or "NaN" in body_text:
        raise AssertionError("import/workspace click_smoke found undefined/NaN text")
    if not any(name.startswith("jyotish-selected-cases-") for name in downloads):
        raise AssertionError(f"selected case export download missing: {downloads}")
    if not any(name.startswith("jyotish-case-library-") for name in downloads):
        raise AssertionError(f"case library export download missing: {downloads}")
    return {
        "success": True,
        "import_workspace_checked": True,
        "import_recovery": import_recovery,
        "import_status": import_status,
        "chart_status": chart_status,
        "saved_panel": saved_panel,
        "case_workspace_checked": bool(case_workspace),
        "downloads": downloads,
        "console_errors": console_errors,
    }


async def run_import_file_smoke(web_base: str, api_base: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    console_errors: list[str] = []
    txt_path = TMP / "jyotish-import-smoke.txt"
    pdf_path = TMP / "jyotish-import-smoke.pdf"
    txt_path.write_text(
        "\n".join([
            "Date of Birth: 1988-11-09",
            "Time of Birth: 06:45",
            "Place of Birth: Mumbai",
            "Latitude: 19.0760 N",
            "Longitude: 72.8777 E",
            "Timezone: UTC+5:30",
        ]),
        encoding="utf-8",
    )
    pdf_path.write_bytes(b"%PDF-1.4\n% jyotish smoke placeholder\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(**browser_launch_options())
        context = await browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 820})
        page = await context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        await page.goto(web_base, wait_until="networkidle")
        await page.evaluate(
            """apiBase => {
              localStorage.clear();
              localStorage.setItem('YINDUZHANXING_API_BASE', apiBase);
              window.YINDUZHANXING_API_BASE = apiBase;
            }""",
            api_base,
        )
        await page.reload(wait_until="networkidle")

        await page.set_input_files("#chart-import-file", str(txt_path))
        await page.wait_for_function(
            """() => (document.querySelector('#chart-import-result')?.innerText || '').includes('已选择：jyotish-import-smoke.txt')""",
            timeout=5000,
        )
        await page.click("#chart-import-parse")
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#chart-import-result')?.innerText || '';
              return text.includes('已识别完整出生信息') && text.includes('质量分') && text.includes('1988-11-9');
            }""",
            timeout=8000,
        )
        text_file_import = (await page.locator("#chart-import-result").inner_text(timeout=5000)).strip()
        await page.click("#chart-import-apply")
        await page.wait_for_function(
            """() => document.querySelector('#birth-year')?.value === '1988'
              && document.querySelector('#birth-month')?.value === '11'
              && document.querySelector('#birth-day')?.value === '9'
              && document.querySelector('#birth-time')?.value === '06:45'
              && document.querySelector('#birth-tz')?.value === '5.5'""",
            timeout=5000,
        )

        await page.evaluate(
            """() => {
              window.JyotishAPI.importChart = async () => {
                throw new Error('PDF import smoke forced failure');
              };
            }"""
        )
        await page.set_input_files("#chart-import-file", str(pdf_path))
        await page.wait_for_function(
            """() => (document.querySelector('#chart-import-result')?.innerText || '').includes('已选择：jyotish-import-smoke.pdf')""",
            timeout=5000,
        )
        await page.click("#chart-import-parse")
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#chart-import-result')?.innerText || '';
              return text.includes('PDF文本抽取失败') && text.includes('可复制PDF文字后粘贴到文本框');
            }""",
            timeout=8000,
        )
        pdf_import_recovery = (await page.locator("#chart-import-result").inner_text(timeout=5000)).strip()
        mobile_context = await browser.new_context(is_mobile=True, viewport={"width": 390, "height": 844}, device_scale_factor=2)
        mobile_page = await mobile_context.new_page()
        await mobile_page.goto(web_base, wait_until="networkidle")
        mobile_entry_state = await mobile_page.evaluate(
            """() => {
              const label = document.querySelector('.chart-import-file');
              const input = document.querySelector('#chart-import-file');
              const labelBox = label?.getBoundingClientRect();
              const inputBox = input?.getBoundingClientRect();
              return {
                labelText: label?.innerText || '',
                labelBox: labelBox ? { left: labelBox.left, right: labelBox.right, width: labelBox.width, height: labelBox.height } : null,
                inputBox: inputBox ? { left: inputBox.left, right: inputBox.right, width: inputBox.width, height: inputBox.height } : null,
                viewportWidth: window.innerWidth,
              };
            }"""
        )
        await mobile_context.close()
        await browser.close()

    if not mobile_entry_state.get("labelBox") or mobile_entry_state["labelBox"]["right"] > 391:
        raise AssertionError(f"mobile file import entry out of viewport: {mobile_entry_state}")
    if mobile_entry_state["labelBox"]["height"] < 40 or "上传文件" not in mobile_entry_state.get("labelText", ""):
        raise AssertionError(f"mobile file import entry not usable: {mobile_entry_state}")
    if console_errors:
        raise AssertionError(f"import file smoke console errors: {console_errors}")
    return {
        "success": True,
        "import_file_checked": True,
        "text_file_import": text_file_import,
        "pdf_import_recovery": pdf_import_recovery,
        "mobile_file_import_entry_checked": True,
        "console_errors": console_errors,
    }


async def run_offline_smoke(web_base: str, api_base: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    console_errors: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(**browser_launch_options())
        context = await browser.new_context(viewport={"width": 390, "height": 844})
        page = await context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        await page.goto(web_base, wait_until="networkidle")
        pwa_surface = await assert_pwa_surface(page)
        await page.evaluate(
            """apiBase => {
              localStorage.setItem('YINDUZHANXING_API_BASE', apiBase);
              window.YINDUZHANXING_API_BASE = apiBase;
            }""",
            api_base,
        )
        await page.reload(wait_until="networkidle")

        await page.click("#first-use-health")
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#first-use-status')?.innerText || '';
              return text.includes('本地 API 未连接') || text.includes('普通用户启动路径') || text.includes('本地 API 服务');
            }""",
            timeout=10000,
        )
        health_status = (await page.locator("#first-use-status").inner_text(timeout=5000)).strip()

        await page.click("#first-use-demo")
        await page.click("#btn-calculate")
        await page.wait_for_function(
            """() => {
              const text = document.querySelector('#chart-compute-status')?.innerText || '';
              return text.includes('本地 API 未连接') || text.includes('Trust Center') || text.includes('星盘已生成');
            }""",
            timeout=12000,
        )
        chart_status = (await page.locator("#chart-compute-status").inner_text(timeout=5000)).strip()
        body_text = await page.locator("body").inner_text(timeout=5000)
        if "undefined" in body_text or "NaN" in body_text:
            raise AssertionError("offline click_smoke found undefined/NaN text")
        recovery_text = "\n".join([health_status, chart_status])
        for token in ["本地 API 未连接", "普通用户启动路径", "本地 API 服务"]:
            if token not in recovery_text:
                raise AssertionError(f"offline recovery text missing {token}: {recovery_text}")
        await browser.close()

    expected_offline_console_errors, unexpected_console_errors = split_expected_offline_console_errors(console_errors)
    return {
        "success": True,
        "offline_checked": True,
        "mobile": True,
        "health_status": health_status,
        "chart_status": chart_status,
        "offline_recovery_guidance_visible": True,
        "pwa_surface": pwa_surface,
        "expected_offline_console_errors": expected_offline_console_errors,
        "console_errors": unexpected_console_errors,
    }


async def run_offline_shell_reload_smoke(web_base: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    console_errors: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(**browser_launch_options())
        context = await browser.new_context(viewport={"width": 390, "height": 844})
        page = await context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        await page.goto(web_base, wait_until="networkidle")
        await page.wait_for_function(
            """() => window.__jyotishPWAStatus?.serviceWorker === 'registered'
              || window.__jyotishPWAStatus?.serviceWorker === 'failed'
              || window.__jyotishPWAStatus?.serviceWorker === 'unsupported'""",
            timeout=10000,
        )
        pwa_status = await page.evaluate("() => window.__jyotishPWAStatus || {}")
        await page.wait_for_function(
            """() => navigator.serviceWorker?.controller || window.__jyotishPWAStatus?.serviceWorker !== 'registered'""",
            timeout=10000,
        )
        await context.set_offline(True)
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_selector("#first-use-panel", timeout=10000)
        shell_text = await page.locator("#first-use-panel").inner_text(timeout=5000)
        await browser.close()

    for token in ["首次使用", "运行健康检查", "填入示例盘"]:
        if token not in shell_text:
            raise AssertionError(f"offline shell reload missing {token}: {shell_text}")
    if not shell_text:
        raise AssertionError(f"offline shell reload missing first-use content: {shell_text}")
    offline_shell_expected_console_errors, unexpected_console_errors = split_expected_offline_console_errors(console_errors)
    return {
        "success": True,
        "offline_shell_reload_checked": True,
        "serviceWorker": pwa_status.get("serviceWorker"),
        "offline_shell_expected_console_errors": offline_shell_expected_console_errors,
        "console_errors": unexpected_console_errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Jyotish browser click smoke")
    parser.add_argument("--mode", choices=["core", "mobile", "offline", "pdf", "workspace", "mobile-trust", "import-files", "all"], default="core")
    parser.add_argument("--keep-logs", action="store_true")
    parser.add_argument("--timeout", type=int, default=180, help="Fail the full smoke command after this many seconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_process: subprocess.Popen[str] | None = None
    web_process: subprocess.Popen[str] | None = None
    api_port, web_port = free_ports(2)
    web_base = f"http://127.0.0.1:{web_port}"
    api_base = f"http://127.0.0.1:{api_port}"
    api_log = TMP / f"jyotish-click-api-{api_port}.log"
    web_log = TMP / f"jyotish-click-web-{web_port}.log"

    def execute_smoke() -> dict[str, Any]:
        nonlocal api_process, web_process
        if args.mode in {"core", "mobile", "pdf", "workspace", "mobile-trust", "import-files", "all"}:
            api_process = start_process(
                [sys.executable, str(API_SERVER), "--port", str(api_port), "--allow-origin", web_base],
                ROOT,
                api_log,
            )
            wait_for_url(f"{api_base}/api/health", logs=[api_log])
        web_process = start_process(
            ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(web_port)],
            APP,
            web_log,
        )
        wait_for_url(f"{web_base}/", logs=[web_log])

        import asyncio

        if args.mode == "offline":
            offline_port = free_ports(1)[0]
            offline = asyncio.run(run_offline_smoke(web_base, f"http://127.0.0.1:{offline_port}"))
            shell_reload = asyncio.run(run_offline_shell_reload_smoke(web_base))
            result = {"success": True, "offline": offline, "offline_shell_reload": shell_reload}
        elif args.mode == "mobile":
            mobile = asyncio.run(run_mobile_smoke(web_base, api_base))
            mobile_tabs = asyncio.run(run_mobile_tab_smoke(web_base, api_base))
            result = {"success": True, "mobile": mobile, "mobile_tabs": mobile_tabs}
        elif args.mode == "pdf":
            pdf_fallback = asyncio.run(run_pdf_fallback_smoke(web_base, api_base))
            result = {"success": True, "pdf_fallback": pdf_fallback}
        elif args.mode == "workspace":
            workspace = asyncio.run(run_import_workspace_smoke(web_base, api_base))
            result = {"success": True, "workspace": workspace}
        elif args.mode == "mobile-trust":
            mobile_trust = asyncio.run(run_mobile_trust_export_smoke(web_base, api_base))
            result = {"success": True, "mobile_trust": mobile_trust}
        elif args.mode == "import-files":
            import_files = asyncio.run(run_import_file_smoke(web_base, api_base))
            result = {"success": True, "import_files": import_files}
        elif args.mode == "all":
            core = asyncio.run(run_browser_clicks(web_base, api_base))
            mobile = asyncio.run(run_mobile_smoke(web_base, api_base))
            mobile_tabs = asyncio.run(run_mobile_tab_smoke(web_base, api_base))
            pdf_fallback = asyncio.run(run_pdf_fallback_smoke(web_base, api_base))
            workspace = asyncio.run(run_import_workspace_smoke(web_base, api_base))
            mobile_trust = asyncio.run(run_mobile_trust_export_smoke(web_base, api_base))
            import_files = asyncio.run(run_import_file_smoke(web_base, api_base))
            offline_port = free_ports(1)[0]
            offline = asyncio.run(run_offline_smoke(web_base, f"http://127.0.0.1:{offline_port}"))
            shell_reload = asyncio.run(run_offline_shell_reload_smoke(web_base))
            result = {
                "success": True,
                "core": core,
                "mobile": mobile,
                "mobile_tabs": mobile_tabs,
                "pdf_fallback": pdf_fallback,
                "workspace": workspace,
                "mobile_trust": mobile_trust,
                "import_files": import_files,
                "offline": offline,
                "offline_shell_reload": shell_reload,
            }
        else:
            result = asyncio.run(run_browser_clicks(web_base, api_base))
        result.update({"valid": True, "click_smoke": True, "web_base": web_base, "api_base": api_base})
        return result

    try:
        result = run_with_timeout(execute_smoke, args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        skipped = "Executable doesn't exist" in str(exc) or "No such file or directory" in str(exc)
        payload = {
            "valid": False,
            "click_smoke": True,
            "skipped": skipped,
            "reason": str(exc),
            "api_log": read_log_tail(api_log),
            "web_log": read_log_tail(web_log),
            "timeout": args.timeout,
            "process_snapshot": {
                "api": process_snapshot("api", api_process, api_log),
                "web": process_snapshot("web", web_process, web_log),
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 0 if skipped else 1
    finally:
        force_stop_process(web_process)
        force_stop_process(api_process)
        if not args.keep_logs:
            for path in [api_log, web_log]:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass


if __name__ == "__main__":
    raise SystemExit(main())
