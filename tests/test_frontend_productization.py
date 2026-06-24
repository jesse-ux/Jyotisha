#!/usr/bin/env python3
"""Static frontend productization checks for the Jyotish web app."""

from __future__ import annotations

import re
import socket
import subprocess
import time
import json
import os
import sys
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "jyotish-app"
API_SERVER = ROOT / "scripts" / "jyotish_api_server.py"
TMP = Path(os.environ.get("TMPDIR", "/private/tmp"))


def read(relative: str) -> str:
    return (APP / relative).read_text(encoding="utf-8")


def runtime_ports() -> tuple[int, int]:
    sockets: list[socket.socket] = []
    try:
        for _ in range(2):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
        return sockets[0].getsockname()[1], sockets[1].getsockname()[1]
    finally:
        for sock in sockets:
            sock.close()


def wait_for_url(url: str, *, timeout: float = 12.0, logs: list[Path] | None = None) -> None:
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        completed = subprocess.run(
            ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if completed.returncode == 0 and completed.stdout.strip().startswith(("2", "3", "4")):
            return
        last_error = completed.stderr.strip() or completed.stdout.strip()
        time.sleep(0.25)
    log_text = ""
    for path in logs or []:
        if path.exists():
            log_text += f"\n--- {path} ---\n{path.read_text(encoding='utf-8', errors='replace')[-4000:]}"
    raise AssertionError(f"Timed out waiting for {url}: {last_error}{log_text}")


def skip_if_sandbox_denies_bind(log_path: Path) -> None:
    if not log_path.exists():
        return
    text = log_path.read_text(encoding="utf-8", errors="replace")
    if "PermissionError" in text and "Operation not permitted" in text and "socket.bind" in text:
        pytest.skip("sandbox disallows starting local listening servers in this pytest context")


def fetch_text(url: str) -> str:
    completed = subprocess.run(
        ["curl", "-sS", url],
        capture_output=True,
        text=True,
        timeout=8,
        check=True,
    )
    return completed.stdout


def fetch_json(url: str) -> dict:
    return json.loads(fetch_text(url))


def post_json(url: str, payload: dict) -> dict:
    completed = subprocess.run(
        [
            "curl",
            "-sS",
            "-X",
            "POST",
            "-H",
            "Content-Type: application/json",
            "--data-binary",
            json.dumps(payload),
            url,
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    return json.loads(completed.stdout)


def load_quality_gate_module():
    spec = importlib.util.spec_from_file_location("run_quality_gate", ROOT / "scripts" / "run_quality_gate.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_birth_payload() -> dict:
    return {
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "lat": 39.9,
        "lon": 116.4,
        "tz": 8,
    }


def start_process(cmd: list[str], cwd: Path, log_path: Path) -> subprocess.Popen[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("w", encoding="utf-8")
    return subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )


def stop_process(process: subprocess.Popen[str]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def test_result_page_keeps_core_user_tabs() -> None:
    html = read("index.html")
    expected_tabs = [
        "chart",
        "complete",
        "provenance",
        "karaka",
        "houses",
        "aspects",
        "yogas",
        "vargas",
        "ashtakavarga",
        "shadbala",
        "dasha",
        "transit",
        "deep",
        "extended",
        "remedies",
        "synastry",
        "prashna",
        "kp",
        "verify",
        "transit-compare",
    ]
    for tab in expected_tabs:
        assert f'data-tab="{tab}"' in html
        assert f'id="tab-{tab}"' in html or tab == "chart"

    assert 'id="birth-form"' in html
    assert 'id="chart-import-panel"' in html
    assert 'id="saved-chart-panel"' in html
    assert 'id="btn-save-chart"' in html
    assert 'id="remedies-section"' in html
    assert 'id="provenance-panel"' in html


def test_first_use_onboarding_is_actionable() -> None:
    html = read("index.html")
    main = read("main.js")
    style = read("style.css")
    gap_doc = ROOT / "docs" / "research" / "product_gap_matrix_2026_06_22.md"

    for token in [
        'id="first-use-panel"',
        'id="first-use-health"',
        'id="first-use-demo"',
        'id="first-use-import"',
        'id="first-use-status"',
        "data-first-use-action",
    ]:
        assert token in html

    for token in [
        "DEMO_BIRTH",
        "setupFirstUsePanel",
        "fillDemoBirth",
        "runFirstUseHealthCheck",
        "focusFirstUseImport",
        "first-use-demo",
        "first-use-health",
        "first-use-import",
        "first-use-status",
        "getAPIHealth",
        "fillBirthFormFromData",
        "window.__jyotishRuntimeHealth",
        "techniqueCount",
        "endpointCount",
        "audit?.registry?.technique_count",
        "audit?.surfaces?.api_endpoint_count",
        "本地 API 未连接",
        "示例盘已填入",
        "API endpoints 可被前端发现",
    ]:
        assert token in main

    for selector in [
        ".first-use-panel",
        ".first-use-head",
        ".first-use-grid",
        ".first-use-step",
        ".first-use-action",
        ".first-use-status",
    ]:
        assert selector in style

    assert re.search(r"\.first-use-grid,\s*\.runtime-health-grid,\s*\.trust-status-grid", style, re.S)
    assert gap_doc.exists()
    assert "First-use onboarding and empty-state path" in gap_doc.read_text(encoding="utf-8")


def test_chart_banner_avoids_undefined_api_fields() -> None:
    main = read("main.js")
    analysis = read("analysis-renderers.js")
    for token in [
        "getAscendantLord",
        "formatMoonNakshatra",
        "normalizePlanetRecord",
        "SIGN_LORDS[ascendant.sign]",
        "moon.nakshatra || moon.nakshatra_name",
        "moon.nakshatra_pada || moon.pada",
        "moonNakshatra ?",
        "ascendant.lord || getAscendantLord(ascendant)",
    ]:
        assert token in main
    for token in [
        "sanitizeRamanDetail",
        "缺星座",
        "buildChartSummary",
        "formatMoonNakshatra(moonP)",
    ]:
        assert token in main or token in analysis
    assert "`${t('asc.nakshatra')}: ${moonP.nakshatra} Pada ${moonP.nakshatra_pada}`" not in main
    assert "planetName(ascendant.lord)} (${ascendant.lord})" not in main
    assert "moonP ? `${moonP.nakshatra} P${moonP.nakshatra_pada}` : null" not in main
    assert "escapeHtml(d)</div>" not in analysis


def test_ai_chat_guides_server_side_secret_handling() -> None:
    ai_chat = read("ai-chat.js")
    i18n = read("i18n.js")

    for token in [
        "buildAISetupGuidance",
        "ai.setup.title",
        "ai.setup.server",
        "ai.setup.secret",
        "ai.setup.trust",
        "OPENAI_API_KEY",
        "服务端环境变量",
        "不要把 OpenAI API key 放进浏览器",
        "Trust Center",
    ]:
        assert token in ai_chat or token in i18n

    for unsafe in [
        "localStorage.setItem('jyotish_ai_endpoint'",
        "jyotish_ai_endpoint",
        "Custom endpoint failed",
        "在浏览器控制台输入",
        "你的API地址",
    ]:
        assert unsafe not in ai_chat
    assert ai_chat.count("function buildAISetupGuidance") == 1


def test_ai_chat_api_failures_have_recovery_guidance() -> None:
    ai_chat = read("ai-chat.js")
    for token in [
        "parseAIResponse",
        "buildAIRecoveryMessage",
        "/api/chat",
        "Trust Center",
        "普通用户启动路径",
        "网页服务",
        "本地 API",
        "服务端 AI 对话暂不可用",
    ]:
        assert token in ai_chat
    assert "const data = await resp.json();" not in ai_chat


def test_export_failure_recovery_guides_health_check() -> None:
    main = read("main.js")
    export_js = read("export.js")
    advanced = read("jyotish-advanced.js")

    for token in [
        "getPDFExportRecoveryMessage",
        "getGenericExportRecoveryMessage",
        "后端已生成 HTML 报告",
        "已下载：",
        "可直接打开，或用浏览器打印为 PDF",
        "已改为导出 HTML 报告",
        "Trust Center 运行健康检查",
        "普通用户启动路径",
        "网页服务",
        "本地 API",
        "report_artifact API unavailable",
        "formatReportArtifactStatus",
        "report_artifact_fallback",
        "artifact_status",
        "download_filename",
        "download_mime",
        "fallback_reason",
        "后端已生成 HTML 报告",
        "已下载：",
        "可直接打开，或用浏览器打印为 PDF",
    ]:
        assert token in main or token in export_js

    assert "alert(`导出失败：" not in main
    assert "setExportStatus(`导出失败：${error?.message || '导出模块加载失败'}`" not in main
    assert "const subLord = DASHA_ORDER[subIdx];" in advanced
    assert "sub_lord: subLord" in advanced
    assert "sub_lord,\n" not in advanced


def test_annual_workbench_renders_tajika_strength_layers() -> None:
    skill_map = read("skill-map.js")
    for token in [
        "tajika_strength",
        "renderTajikaStrengthCards",
        "formatTajikaStrengthPlanet",
        "Harsha Bala",
        "Panchavargiya Bala",
        "strongest_planets",
        "combined_strength",
        "年度强度",
    ]:
        assert token in skill_map


def test_muhurta_workbench_renders_date_range_solver() -> None:
    skill_map = read("skill-map.js")
    for token in [
        "range_search",
        "renderMuhurtaRangeSolver",
        "muhurta_date_range_solver",
        "best_windows",
        "recommended_windows",
        "rejected_dates",
        "择日候选",
        "范围择日",
    ]:
        assert token in skill_map


def test_deep_varga_avastha_workbench_renders_templates() -> None:
    skill_map = read("skill-map.js")
    for token in [
        "deepVargaAvastha",
        "renderDeepVargaAvasthaResult",
        "deep_varga_templates",
        "avastha_summary",
        "dominant_states",
        "template_cards",
        "risk_flags",
        "D24/D30/D60",
    ]:
        assert token in skill_map


def test_runtime_smoke_covers_ai_and_report_recovery() -> None:
    smoke = (ROOT / "tests" / "run_frontend_runtime_smoke.py").read_text(encoding="utf-8")
    for token in [
        "/api/report_artifact",
        "AI_BROWSER_KEY_DISABLED",
        "ai-chat.js",
        "i18n.js",
        "chat_policy",
        "report_artifact_smoke",
        "ai_bridge_policy_smoke",
    ]:
        assert token in smoke


def test_click_smoke_covers_core_interactive_workflows() -> None:
    smoke_path = ROOT / "tests" / "run_frontend_click_smoke.py"
    quality_gate = (ROOT / "scripts" / "run_quality_gate.py").read_text(encoding="utf-8")
    assert smoke_path.exists()
    smoke = smoke_path.read_text(encoding="utf-8")
    for token in [
        "YINDUZHANXING_API_BASE",
        "first-use-demo",
        "btn-calculate",
        "ai-fab",
        "ai-input",
        "btn-export",
        "export-status",
        "btn-run-transit",
        "btn-run-synastry-full",
        "btn-run-prashna",
        "Trust Center",
        "click_smoke",
        "--mode",
        "pdf",
        "offline",
        "mobile",
        "mobile-trust",
        "import-files",
        "manifest.webmanifest",
        "serviceWorker",
        "first-use-health",
        "run_offline_smoke",
        "expected_offline_console_errors",
        "run_pdf_fallback_smoke",
        "run_import_workspace_smoke",
        "run_import_file_smoke",
        "run_mobile_trust_export_smoke",
        "run_offline_shell_reload_smoke",
        "run_mobile_tab_smoke",
        "后端已生成 HTML 报告",
        "已下载：",
        "可直接打开，或用浏览器打印为 PDF",
        "pdf_fallback_checked",
        "import_workspace_checked",
        "import_recovery",
        "pdf_import_recovery",
        "mobile_file_import_entry_checked",
        "PDF文本抽取失败",
        "pdf_import_recovery =",
        "仍需手动补充",
        "mobile_trust_export_checked",
        "jyotish-local-data-",
        "--timeout",
        "run_with_timeout",
        "process_snapshot",
        "force_stop_process",
        "jyotish-selected-cases-",
        "jyotish-case-library-",
        "offline_shell_reload_checked",
        "offline_shell_expected_console_errors",
        "mobile_tab_switch_checked",
    ]:
        assert token in smoke
    for token in [
        "--skip-frontend-click",
        "--frontend-click-timeout",
        "tests/run_frontend_click_smoke.py",
        "--mode",
        "all",
        "--timeout",
        "format_failure_summary",
        "Run the focused command above",
        "--keep-logs",
        "process_snapshot",
        'APP = ROOT / "jyotish-app"',
        "cwd=APP",
    ]:
        assert token in quality_gate


def test_quality_gate_formats_actionable_failure_summary() -> None:
    quality_gate = load_quality_gate_module()
    summary = quality_gate.format_failure_summary(
        "frontend click smoke",
        ["python3", "tests/run_frontend_click_smoke.py", "--mode", "all", "--timeout", "1"],
        124,
        stdout='{"valid": false, "reason": "click smoke timed out after 1s"}',
        stderr='{"process_snapshot": {"api": {"pid": 11, "running": true}, "web": {"pid": 12, "running": true}}}',
    )
    for token in [
        "Quality gate failed",
        "frontend click smoke",
        "exit code: 124",
        "tests/run_frontend_click_smoke.py --mode all --timeout 1",
        "click smoke timed out after 1s",
        "process_snapshot",
        "Run the focused command above",
        "--keep-logs",
        "Trust Center",
    ]:
        assert token in summary


def test_quality_gate_declares_fast_browser_release_profiles() -> None:
    quality_gate = (ROOT / "scripts" / "run_quality_gate.py").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for token in [
        "--profile",
        "choices=[\"quick\", \"browser\", \"release\"]",
        "QUALITY_GATE_PROFILES",
        "quick",
        "browser",
        "release",
        "skip_slow",
        "skip_yoga_logic",
        "skip_frontend_click",
        "frontend_click_mode",
        "import-files",
        "mobile-trust",
        "run_profile",
        "check_release_hygiene",
        "release_hygiene_check",
        "RELEASE_CRITICAL_UNTRACKED_PATHS",
    ]:
        assert token in quality_gate
    for token in [
        "质量门分层",
        "quick：快速开发守门",
        "browser：完整浏览器守门",
        "release：发布前守门",
        "python3 scripts/run_quality_gate.py --profile quick",
        "python3 scripts/run_quality_gate.py --profile browser",
        "python3 scripts/run_quality_gate.py --profile release",
    ]:
        assert token in readme


def test_release_quality_gate_tracks_untracked_product_files() -> None:
    quality_gate = load_quality_gate_module()
    assert quality_gate.QUALITY_GATE_PROFILES["release"]["check_release_hygiene"] is True
    assert quality_gate.QUALITY_GATE_PROFILES["browser"]["check_release_hygiene"] is False
    for path in [
        "jyotish-app/skill-map.js",
        "jyotish-app/public/manifest.webmanifest",
        "scripts/audit_fragments.py",
        "scripts/deep_varga_avastha.py",
        "tests/run_frontend_click_smoke.py",
        "tests/test_frontend_productization.py",
        "docs/research/whole_machine_git_audit_2026_06_23.md",
        "task_plan.md",
        "progress.md",
    ]:
        assert path in quality_gate.RELEASE_CRITICAL_UNTRACKED_PATHS


def test_github_release_quality_gate_runs_browser_release_profile() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release-quality-gate.yml").read_text(encoding="utf-8")
    for token in [
        "workflow_dispatch",
        "pull_request",
        "python-version: '3.11'",
        "node-version: '20'",
        "npm ci --prefix jyotish-app",
        "python -m pip install playwright",
        "python -m playwright install --with-deps chromium",
        "python scripts/run_quality_gate.py --profile release --frontend-click-timeout 240",
    ]:
        assert token in workflow


def test_auth_and_subscription_failures_have_recovery_guidance() -> None:
    auth = read("auth.js")
    subscription = read("subscription.js")
    i18n = read("i18n.js")
    for token in [
        "buildAuthRecoveryMessage",
        "showAuthError",
        "auth.recovery.api",
        "Trust Center",
        "普通用户启动路径",
        "网页服务",
        "本地 API",
        "auth.recovery.retry",
        "buildSubscriptionRecoveryMessage",
        "showSubscriptionNotice",
        "sub.recovery.iap",
    ]:
        assert token in auth or token in subscription or token in i18n

    assert "const data = await resp.json();" not in auth
    assert "alert(t('sub.iap.unavail'))" not in subscription


def test_api_bridge_failures_have_recovery_guidance() -> None:
    bridge = read("api-bridge.js")
    public_bridge = read("public/api-bridge.js")
    assert bridge == public_bridge
    for token in [
        "parseApiResponse",
        "buildAPIRecoveryMessage",
        "Trust Center",
        "普通用户启动路径",
        "网页服务",
        "本地 API",
        "本地 API 未连接",
        "lastAttempt",
    ]:
        assert token in bridge
    assert "const data = await resp.json();" not in bridge
    assert "const data = await resp.json();" not in public_bridge


def test_chart_compute_failures_have_visible_recovery_guidance() -> None:
    html = read("index.html")
    main = read("main.js")
    style = read("style.css")
    for token in [
        'id="chart-compute-status"',
        "setChartComputeStatus",
        "buildChartComputeRecoveryMessage",
        "Trust Center",
        "普通用户启动路径",
        "网页服务",
        "本地 API",
        "本地 API 未连接",
    ]:
        assert token in html or token in main or token in style
    assert "alert('计算失败: ' + e.message)" not in main
    assert "alert(t('alert.error') + err.message)" not in main
    assert ".chart-compute-status" in style


def test_transit_compare_failures_have_recovery_guidance() -> None:
    main = read("main.js")
    for token in [
        "parseTransitCompareResponse",
        "buildTransitCompareRecoveryMessage",
        "buildTransitRenderRecoveryMessage",
        "Trust Center",
        "普通用户启动路径",
        "网页服务",
        "本地 API 服务",
        "过境数据需本地 API 服务",
        "Transit 计算暂不可用",
    ]:
        assert token in main
    assert "const data = await resp.json();" not in main
    assert "过境数据需API服务器" not in main
    assert "'Transit 计算失败: ' + err.message" not in main


def test_interactive_api_workflows_have_recovery_guidance() -> None:
    main = read("main.js")
    for token in [
        "buildInteractiveAPIRecoveryMessage",
        "renderInlineAPIError",
        "Trust Center",
        "普通用户启动路径",
        "网页服务",
        "本地 API 服务",
        "合盘计算暂不可用",
        "问事计算暂不可用",
        "校正时间应用暂不可用",
    ]:
        assert token in main

    for unsafe in [
        "alert('校正时间应用失败: ' + (error?.message || error))",
        "'合盘 API 不可用，请先启动 python3 scripts/jyotish_api_server.py --port 5200'",
        "'问事 API 不可用，请先启动 python3 scripts/jyotish_api_server.py --port 5200'",
    ]:
        assert unsafe not in main


def test_ephemeris_abstraction_feasibility_is_probeable() -> None:
    probe = ROOT / "scripts" / "ephemeris_backend_probe.py"
    doc = ROOT / "docs" / "research" / "ephemeris_abstraction_feasibility_2026_06_23.md"
    gap_doc = ROOT / "docs" / "research" / "product_gap_matrix_2026_06_22.md"

    assert probe.exists()
    assert doc.exists()
    probe_text = probe.read_text(encoding="utf-8")
    doc_text = doc.read_text(encoding="utf-8")
    gap_text = gap_doc.read_text(encoding="utf-8")
    for token in [
        "swisseph_python",
        "swisseph_wasm",
        "xalen_ephemeris",
        "vedastro",
        "pyjhora_benchmark",
        "license_posture",
        "replacement_readiness",
        "candidate_backends",
    ]:
        assert token in probe_text
        assert token in doc_text or token in gap_text


def test_ephemeris_adapter_contract_and_parity_matrix_are_defined() -> None:
    contract = ROOT / "scripts" / "ephemeris_adapter_contract.py"
    parity_doc = ROOT / "docs" / "research" / "ephemeris_adapter_contract_2026_06_23.md"
    gap_doc = ROOT / "docs" / "research" / "product_gap_matrix_2026_06_22.md"

    assert contract.exists()
    assert parity_doc.exists()
    contract_text = contract.read_text(encoding="utf-8")
    parity_text = parity_doc.read_text(encoding="utf-8")
    gap_text = gap_doc.read_text(encoding="utf-8")

    for token in [
        "EphemerisAdapterContract",
        "PARITY_CASES",
        "longitude_delta_arcsec",
        "sun_moon_asc_nodes",
        "swisseph_python",
        "candidate_backend",
        "ayanamsa_value",
        "retrograde",
        "acceptance_thresholds",
    ]:
        assert token in contract_text
        assert token in parity_text or token in gap_text


def test_ephemeris_candidate_adapter_spike_is_gated() -> None:
    spike = ROOT / "scripts" / "ephemeris_candidate_adapter_spike.py"
    doc = ROOT / "docs" / "research" / "ephemeris_candidate_adapter_spike_2026_06_23.md"
    gap_doc = ROOT / "docs" / "research" / "product_gap_matrix_2026_06_22.md"

    assert spike.exists()
    assert doc.exists()
    spike_text = spike.read_text(encoding="utf-8")
    doc_text = doc.read_text(encoding="utf-8")
    gap_text = gap_doc.read_text(encoding="utf-8")

    for token in [
        "swisseph_wasm_candidate",
        "xalen_ephemeris_candidate",
        "candidate_backend",
        "candidate_adapter_spike",
        "license_gate",
        "package_license",
        "AGPL-3.0",
        "GPL-3.0-or-later",
        "runtime_setting_exposure",
        "parity_gate_required",
    ]:
        assert token in spike_text
        assert token in doc_text or token in gap_text


def test_api_bridge_exports_productized_backend_actions() -> None:
    bridge = read("api-bridge.js")
    public_bridge = read("public/api-bridge.js")
    assert bridge == public_bridge

    for token in [
        "AI_BROWSER_KEY_DISABLED",
        "aiKeyPolicy: 'server_side_only'",
        "不要把 OpenAI API key 放进浏览器",
    ]:
        assert token in bridge

    for unsafe in [
        "YINDUZHANXING_AI_KEY",
        "apiKey: AI_KEY",
        "Authorization': 'Bearer ' + AI_KEY",
        "copse.top",
        "AI_KEY_NOT_CONFIGURED",
    ]:
        assert unsafe not in bridge

    required_functions = [
        "getCapabilityAudit",
        "getTechniqueCatalog",
        "runTechniqueExample",
        "computeAnnual",
        "computeMuhurta",
        "computePanchangaRange",
        "computeBhavaChalit",
        "computeSudarshana",
        "computeNakshatraFull",
        "computeVargaFull",
        "computeJaimini",
        "computeAshtakavarga",
        "computeShadbala",
        "computeYogas",
        "computeAspects",
        "computeRectificationGate",
        "computeCaseValidation",
        "computeDivisionalYoga",
        "computeKakshya",
        "computeBhavaBala",
        "computeTransitTriggers",
        "computeCareer",
        "computeRelationship",
        "computeKP",
        "computePrashna",
        "computeSynastry",
        "computeRemedies",
        "computeSadeSati",
        "computePanchaMahapurusha",
        "generateReportArtifact",
        "computeThematicReport",
        "getAPIHealth",
    ]
    for name in required_functions:
        assert f"async function {name}" in bridge
        assert re.search(rf"\b{name},", bridge), f"{name} must be exported on window.JyotishAPI"


def test_bhava_chalit_uses_user_selected_house_system() -> None:
    skill_map = read("skill-map.js")
    for token in [
        "resolveBhavaHouseSystem",
        "calculationSettings?.houseSystem",
        "house_system: resolveBhavaHouseSystem(context)",
        "...buildBirthPayload(context)",
        "available_house_systems",
        "selected_house_system",
        "requested_house_system",
        "renderBhavaChalitResult",
        "Placidus",
        "Sripati",
    ]:
        assert token in skill_map
    assert "if (action === 'bhava') return { ...base, mode: 'compare', house_system: 'sripati' }" not in skill_map


def test_skill_workbench_exposes_all_expected_advanced_actions() -> None:
    skill_map = read("skill-map.js")
    main = read("main.js")
    style = read("style.css")
    expected_actions = [
        "varga",
        "annual",
        "muhurta",
        "bhava",
        "sudarshana",
        "nakshatra",
        "jaimini",
        "ashtakavarga",
        "shadbala",
        "yogas",
        "aspects",
        "rectification",
        "caseValidation",
        "divisionalYoga",
        "deepVargaAvastha",
        "kakshya",
        "bhavaBala",
        "transitTrigger",
        "thematicReport",
        "career",
        "relationship",
        "kpQuick",
        "prashnaQuick",
        "synastryQuick",
    ]
    for action in expected_actions:
        assert f"['{action}'" in skill_map
        assert f"action === '{action}'" in skill_map or f"data-action=\"${{escapeAttr(id)}}\"" in skill_map

    assert "renderAshtakavargaTechniqueResult" in skill_map
    assert "renderShadbalaTechniqueResult" in skill_map
    assert "renderYogaTechniqueResult" in skill_map
    assert "renderDeepVargaAvasthaResult" in skill_map
    assert "deep_varga_avastha" in skill_map
    assert "Sayanadi/Shayanadi" in skill_map
    assert "D24/D30/D60" in skill_map
    assert "pav_summary" in skill_map
    assert "sodhita_summary" in skill_map
    assert "advanced_layer" in skill_map
    assert "curse_yogas" in skill_map
    assert "rule_variants" in skill_map
    assert "technique-json" in skill_map
    assert "capability_audit" in skill_map or "getCapabilityAudit" in skill_map
    for token in [
        "TECHNIQUE_API_ENDPOINTS",
        "TECHNIQUE_COMMAND_ACTIONS",
        "TECHNIQUE_ID_ACTIONS",
        "TECHNIQUE_EXPLORER_PRIORITY",
        "renderTechniqueDirectory",
        "buildTechniqueDirectoryRows",
        "renderTechniqueDirectoryRows",
        "bindTechniqueDirectory",
        "bindTechniqueExplorerActions",
        "runTechniqueExplorerAction",
        "renderTechniqueExplorerResult",
        "renderTechniqueExplorerLoading",
        "buildExplorerPayloadPreview",
        "resolveTechniqueExplorerAction",
        "actionForEndpoint",
        "endpointForAction",
        "readTechniqueDirectoryFilters",
        "filterTechniqueDirectoryRows",
        "normalizeDirectoryText",
        "uniqueSorted",
        "renderDashaTechniqueResult",
        "renderRemediesExplorerResult",
        "renderThematicReportResult",
        "technique-directory-search",
        "technique-directory-domain",
        "technique-directory-status",
        "technique-directory-surface",
        "data-technique-directory-results",
        "data-technique-run",
        "data-technique-result",
        "data-technique-endpoint",
        "technique_example",
        "getTechniqueCatalogOrAudit",
        "runTechniqueExample",
        "current_dasha",
        "top_kala_support",
        "active_yuddha",
        "sputa_drik_bala",
        "curse_conjunctions",
        "vimshottari_analysis",
        "renderDashaLevelLine",
        "fragment_sources",
        "workflow_orchestration",
        "evidence_source",
        "full_reading_used",
        "full-reading:",
        "module_status",
        "warning_count",
        "real evidence path",
        "api_docs",
        "method_docs",
        "renderTechniqueApiDocs",
        "getTechniqueApiDoc",
        "cURL / OpenAPI",
        "technique-api-docs",
        "Trust Center 运行健康检查",
        "本地 API 服务",
        "orchestrator_bridge.py",
        "reading_orchestrator.py",
        "mevg_gate",
        "mevg_automation.py",
        "computeDashaSystem",
        "computeThematicReport",
        "thematic-report",
        "/api/thematic_report",
        "computeRemedies",
        "computeSadeSati",
        "computePanchaMahapurusha",
        "data-technique-filter",
        "productization?.rows",
        "ux_productization?.rows",
        "api_endpoints",
    ]:
        assert token in skill_map

    for token in [
        "renderVimshottariAnalysisBlock",
        "dasha-analysis-block",
        "dasha-analysis-grid",
        "vimshottari_analysis",
    ]:
        assert token in main or token in style


def test_remedies_ui_keeps_evidence_boundary_and_hidden_json() -> None:
    main = read("main.js")
    style = read("style.css")

    for token in [
        "remedies.evidence_chain",
        "remedies-evidence-grid",
        "remedies-evidence-card",
        "remedies-boundary",
        "remedies-next-action",
        "remedies-json",
        "technique-json",
    ]:
        assert token in main or token in style

    assert "不能替代医疗、法律、投资或心理咨询" in main
    assert "低风险优先" in main
    assert "需要谨慎确认" in main


def test_provenance_panchanga_workspace_panel_is_productized() -> None:
    main = read("main.js")
    style = read("style.css")
    export_js = read("export.js")
    glossary = read("glossary.js")
    html = read("index.html")
    manifest = read("public/manifest.webmanifest")
    sw = read("public/sw.js")
    gap_doc = ROOT / "docs" / "research" / "product_gap_matrix_2026_06_22.md"

    assert gap_doc.exists()
    doc_text = gap_doc.read_text(encoding="utf-8")
    for token in [
        "Calculation settings and provenance center",
        "Panchanga calendar product",
        "Saved chart workspace",
        "Fragment Triage Queue",
        "vedika-io/xalen-ephemeris",
    ]:
        assert token in doc_text

    for token in [
        "buildCalculationProvenance",
        "renderProvenancePanel",
        "renderPanchangaRange",
        "Panchanga Preview",
        "panchanga-range",
        "panchanga-month",
        "PANCHANGA_ACTIVITIES",
        "PANCHANGA_CONDITIONS",
        "PANCHANGA_CONDITION_MODES",
        "renderPanchangaMonthGrid",
        "panchanga-activity",
        "panchanga-condition",
        "panchanga-condition-mode",
        "panchanga-condition-option",
        "PANCHANGA_CONDITION_GUIDE",
        "normalizePanchangaConditionMode",
        "getPanchangaConditionModeLabel",
        "renderPanchangaFestivalDetails",
        "renderPanchangaLocationSummary",
        "festivalDetails",
        "search_summary",
        "getSelectedPanchangaConditions",
        "normalizePanchangaConditions",
        "getPanchangaConditionSelectionLabel",
        "renderPanchangaConditionGuide",
        "getPanchangaConditionLabel",
        "filterPanchangaRowsByCondition",
        "rowMatchesPanchangaCondition",
        "CALCULATION_SETTINGS_KEY",
        "DEFAULT_CALCULATION_SETTINGS",
        "CALCULATION_SETTING_OPTIONS",
        "ephemerisBackend",
        "ephemeris_backend",
        "yogaVariant",
        "jaiminiKarakaVariant",
        "kpSignificatorVariant",
        "ashtakavargaVariant",
        "shadbalaVariant",
        "dashaReference",
        "yoga_variant",
        "jaimini_karaka_variant",
        "kp_significator_variant",
        "ashtakavarga_variant",
        "shadbala_variant",
        "dasha_reference",
        "ruleVariantStatus",
        "Rule Variants",
        "readCalculationSettings",
        "writeCalculationSettings",
        "normalizeCalculationSettings",
        "applyCalculationSettingsToPayload",
        "attachCalculationSettings",
        "renderCalculationSettingsPanel",
        "renderCalculationSelect",
        "renderTerminologyModePreview",
        "saveCalculationSettingsFromPanel",
        "save-calculation-settings",
        "data-setting-key",
        "calculationSettings",
        "TERMINOLOGY_MODE_KEY",
        "TERMINOLOGY_MODE_OPTIONS",
        "readTerminologyMode",
        "writeTerminologyMode",
        "getTerminologyModeOption",
        "renderTerminologyModePanel",
        "saveTerminologyModeFromPanel",
        "save-terminology-mode",
        "terminology-mode",
        "setGlossaryTerminologyMode",
        "terminologyMode",
        "terminology_mode",
        "平衡模式",
        "术语模式",
        "星历底座",
        "xalen-ephemeris Apache-2.0 可行性记录",
        "TRUST_CENTER_STORAGE_KEYS",
        "initPWAInstallability",
        "navigator.serviceWorker.register('/sw.js')",
        "beforeinstallprompt",
        "__jyotishDeferredInstallPrompt",
        "renderTrustCenterPanel",
        "getRuntimeHealthStatus",
        "renderRuntimeHealthPanel",
        "runTrustCenterHealthCheck",
        "__jyotishRuntimeHealth",
        "getAPIHealth",
        "trust-run-health",
        "Runtime Health",
        "运行健康检查",
        "Technique catalog",
        "Packaging preflight",
        "getTrustCenterStats",
        "getPWAStatus",
        "updateTrustCenterPWAStatus",
        "getRuntimeHealthStatus",
        "renderRuntimeHealthPanel",
        "runTrustCenterHealthCheck",
        "__jyotishRuntimeHealth",
        "trust-run-health",
        "/api/health",
        "Technique catalog",
        "Runtime Health",
        "运行健康检查",
        "运行体检",
        "Pake shell",
        "Tauri shell with sidecar",
        "desktop_packaging_preflight.py",
        "exportTrustCenterLocalData",
        "clearTrustCenterLocalData",
        "promptPWAInstall",
        "trust-export-local",
        "trust-clear-local",
        "pwa-install",
        "Trust Center",
        "Local-first",
        "Rahu Kala",
        "Yamaganda",
        "Gulika",
        "exportPanchangaRangeCSV",
        "exportPanchangaRangeICS",
        "solar_times",
        "sunrise_sunset",
        "end_times",
        "vrataTags",
        "conditionTags",
        "conditionLabels",
        "renderPanchangaConditionBadges",
        "renderVrataTagBadges",
        "formatEndTimeSummary",
        "subDaySummary",
        "formatSubDaySummary",
        "choghadiya",
        "horaWindows",
        "activityVerdict",
        "text/calendar",
        "Condition tags",
        "renderTithiLordInsight",
        "tithi_lord_analysis",
        "jyotish_chart_library",
        "CHART_LIBRARY_KEY",
        "setupSavedChartPanel",
        "renderSavedChartPanel",
        "saveCurrentChartToLibrary",
        "openSavedChartFromPanel",
        "sortChartLibrary",
        "buildLegacyWorkspaceChartId",
        "findChartLibraryEntry",
        "normalizeBirthIdPart",
        "resolveTimezoneValue",
        "resolveTypedBirthCity",
        "getBrowserTimezoneOffset",
        "recordSynastryWorkflow",
        "recordPrashnaWorkflow",
        "ensureClientWorkflows",
        "buildWorkflowExportExtras",
        "buildKPReportSummary",
        "workspace-save-current",
        "workspace-open-selected",
        "workspace-delete-selected",
        "workspace-export-selected",
        "renderChartWorkspaceList",
        "saveCurrentChartToWorkspace",
        "openSelectedWorkspaceChart",
        "synastry-partner-library",
        "btn-run-synastry-library",
        "renderSynastryPartnerLibrary",
        "getSelectedSynastryLibraryEntry",
        "runSynastryWithPartnerChart",
        "SYNASTRY_PAIR_LIBRARY_KEY",
        "jyotish_synastry_pair_library",
        "PRASHNA_CASE_LIBRARY_KEY",
        "jyotish_prashna_case_library",
        "renderSynastryPairWorkspace",
        "saveCurrentSynastryPair",
        "exportCurrentSynastryPair",
        "exportCurrentSynastryHTMLReport",
        "buildSynastryWorkflowFromPair",
        "buildBiWheelComparisonData",
        "buildBiWheelAxisRow",
        "buildSynastryPlanetPoint",
        "buildCompositeStyleMidpoints",
        "midpointLongitude",
        "renderBiWheelComparisonView",
        "renderCompositeStyleStrip",
        "normalizeReplayComparison",
        "compositeStyle",
        "partnerOverlayHouse",
        "buildSynastrySpouseStatusContext",
        "buildSpouseStatusSnapshot",
        "collectSpouseStatusStrengths",
        "collectSpouseStatusRisks",
        "formatSpouseStatusEvidence",
        "renderSpouseStatusComparison",
        "renderSpouseStatusCard",
        "normalizeReplaySpouseStatus",
        "spouseStatus",
        "spouse_status_yoga.py",
        "buildULDKTimingContext",
        "buildULDKTimingSnapshot",
        "normalizeDKPoint",
        "normalizeULPoint",
        "collectULDKTimingStrengths",
        "collectULDKTimingRisks",
        "formatULDKTimingEvidence",
        "renderULDKTimingComparison",
        "renderULDKTimingCard",
        "normalizeReplayULDKTiming",
        "ulDkTiming",
        "UL/DK 与关系时机",
        "buildRelationshipReportTemplate",
        "relationshipKutaMeaning",
        "renderRelationshipReport",
        "renderRelationshipReportList",
        "relationshipReport",
        "relationship_report",
        "strongestKutas",
        "weakKutas",
        "save-synastry-pair",
        "export-synastry-pair",
        "export-synastry-html",
        "readPrashnaCaseLibrary",
        "writePrashnaCaseLibrary",
        "buildPrashnaCaseRecord",
        "renderPrashnaCaseWorkspace",
        "saveCurrentPrashnaCase",
        "exportCurrentPrashnaCase",
        "kp_horary",
        "renderKPHoraryEvidence",
        "ruling_planets",
        "cuspal_sub_lord",
        "house_significators",
        "judgement_matrix",
        "horary_number",
        "KP Horary",
        "save-prashna-case",
        "export-prashna-case",
        "exportWorkspaceCaseLibrary",
        "workspace-export-cases",
        "workspace-case-import-file",
        "importWorkspaceCaseLibrary",
        "mergeWorkspaceCaseLibrary",
        "mergeLibraryById",
        "workspace-case-import-status",
        "workspace-case-search",
        "workspace-case-type",
        "workspace-case-group",
        "workspace-case-relation",
        "CASE_GROUP_PRESETS",
        "CASE_RELATION_PRESETS",
        "buildDefaultChartWorkspaceMeta",
        "normalizeWorkspaceMeta",
        "getCaseDefaultMeta",
        "getCaseGroupLabel",
        "getCaseRelationValue",
        "getCaseRelationLabel",
        "renderCaseMetaLine",
        "formatWorkspaceCaseTitle",
        "workspace-open-chart",
        "filterCaseRecords",
        "normalizeCaseSearchText",
        "readCaseWorkspaceFilter",
        "refreshCaseWorkspaceList",
        "renderCaseWorkspaceRows",
        "renderCaseWorkspaceCounts",
        "_caseWorkspaceSelection",
        "renderCaseSelectControl",
        "workspace-toggle-case",
        "workspace-select-visible",
        "workspace-clear-selection",
        "workspace-export-selected-cases",
        "workspace-delete-selected-cases",
        "workspace-edit-case",
        "editWorkspaceCaseMetadata",
        "getWorkspaceCaseStore",
        "applyWorkspaceCaseMetadata",
        "selectVisibleWorkspaceCases",
        "exportSelectedWorkspaceCases",
        "deleteSelectedWorkspaceCases",
        "resolveSelectedCaseRecords",
        "getVisibleCaseSelectionKeys",
        "_caseWorkspacePreview",
        "workspace-preview-case",
        "workspace-clear-preview",
        "previewWorkspaceCase",
        "findWorkspaceCaseRecord",
        "renderWorkspaceCasePreviewPanel",
        "renderWorkspaceCasePreview",
        "renderWorkspaceCasePreviewCards",
        "renderChartCasePreviewCards",
        "renderSynastryCasePreviewCards",
        "renderPrashnaCasePreviewCards",
        "renderCasePreviewCard",
        "getCaseKindLabel",
        "openSavedSynastryPair",
        "deleteSavedSynastryPair",
        "openSavedPrashnaCase",
        "deleteSavedPrashnaCase",
        "workspace-open-pair",
        "workspace-delete-pair",
        "workspace-open-prashna",
        "workspace-delete-prashna",
        "renderSavedSynastryPair",
        "buildSynastryReplayDeep",
        "normalizeReplayD9",
        "switchToTab",
        "case_library",
        "PRODUCT_GAP_DOC",
        "provenance-action",
        "loadExportModule",
        "exportHTMLReport",
        "exportPDFReport",
        "buildExportRecoveryMessage",
        "getPDFExportRecoveryMessage",
        "已改为导出 HTML 报告",
    ]:
        assert token in main

    for selector in [
        ".provenance-grid",
        ".provenance-kv-grid",
        ".provenance-table",
        ".roadmap-grid",
        ".panchanga-range-controls",
        ".panchanga-month-grid",
        ".panchanga-tag-row",
        ".panchanga-activity-badge",
        ".panchanga-condition-filter",
        ".panchanga-condition-head",
        ".panchanga-condition-options",
        ".panchanga-condition-guide",
        ".panchanga-festival-details",
        ".panchanga-festival-card",
        ".calculation-settings-panel",
        ".calculation-settings-grid",
        ".rule-variant-panel",
        ".rule-variant-grid",
        ".calculation-settings-save",
        ".terminology-mode-preview",
        ".terminology-mode-panel",
        ".terminology-mode-options",
        ".terminology-mode-option.active",
        ".terminology-mode-save",
        ".runtime-health-panel",
        ".runtime-health-grid",
        ".runtime-health-item",
        ".runtime-health-note",
        ".trust-center-panel",
        ".trust-status-grid",
        ".trust-status-card",
        ".runtime-health-panel",
        ".runtime-health-grid",
        ".runtime-health-item",
        ".runtime-health-note",
        ".trust-center-copy",
        ".provenance-action.danger",
        ".panchanga-range-summary",
        ".panchanga-week-table",
        ".workspace-library",
        ".workspace-chart-row",
        ".synastry-library-panel",
        ".synastry-pair-actions",
        ".synastry-pair-workspace",
        ".synastry-pair-row",
        ".relationship-report-template",
        ".relationship-report-grid",
        ".relationship-report-sections",
        ".relationship-evidence-card",
        ".relationship-report-boundary",
        ".biwheel-comparison-view",
        ".biwheel-axis-grid",
        ".biwheel-comparison-table",
        ".composite-style-strip",
        ".spouse-status-comparison",
        ".spouse-status-grid",
        ".spouse-status-card",
        ".uldk-timing-comparison",
        ".uldk-timing-grid",
        ".uldk-timing-card",
        ".prashna-case-actions",
        ".prashna-case-workspace",
        ".prashna-case-row",
        ".case-workspace-summary",
        ".case-row-actions",
        ".mini-action",
        ".case-replay-banner",
        ".file-action",
        ".workspace-import-status",
        ".case-workspace-controls",
        ".case-bulk-actions",
        ".case-select-control",
        ".case-preview-panel",
        ".case-preview-grid",
        ".case-preview-card",
        ".case-meta-line",
        ".tithi-lord-insight",
        ".saved-chart-panel",
        ".saved-chart-item",
        ".btn-save-chart",
        ".export-status",
        ".export-item.is-exporting",
    ]:
        assert selector in style

    assert "provenance: extras.provenance" in export_js
    assert "calculation_settings" in export_js
    assert "provenance.nodeMode" in export_js
    assert "provenance.houseSystem" in export_js
    assert "provenance.sunrisePolicy" in export_js
    assert "provenance.geocoderPolicy" in export_js
    assert "provenance.ephemerisBackend" in export_js
    assert "provenance.terminologyMode" in export_js
    assert "provenance.yogaVariant" in export_js
    assert "provenance.jaiminiKarakaVariant" in export_js
    assert "provenance.kpSignificatorVariant" in export_js
    assert "provenance.ashtakavargaVariant" in export_js
    assert "provenance.shadbalaVariant" in export_js
    assert "provenance.dashaReference" in export_js
    assert "provenance.terminologyMode" in export_js
    assert "modules.workflows" in export_js
    assert "用户工作流结果" in export_js
    assert "_kpWorkflowReport" in export_js
    assert "_prashnaWorkflowReport" in export_js
    assert "_synastryWorkflowReport" in export_js
    assert "_relationshipReportBullets" in export_js
    assert "_relationshipReportList" in export_js
    assert "_relationshipBoundary" in export_js
    assert "relationship_report" in export_js
    assert "relationship-deliverable" in export_js
    assert "relationship-evidence-grid" in export_js
    assert "comparison-print-table" in export_js
    assert "composite-print-grid" in export_js
    assert "uldk-print-grid" in export_js
    assert "UL/DK 与关系时机" in export_js
    assert "spouse-print-grid" in export_js
    assert "relationship-boundary" in export_js
    assert "break-inside: avoid" in export_js
    assert "UL/DK 时机" in main
    assert "Jaimini · Dasha trigger" in main
    assert "computeArudha(chart.planets" in main
    assert "computeKaraka(chart.planets" in main
    assert "_caseLibraryWorkflowReport" in export_js
    assert "_dateLabel" in export_js
    assert "KP Sublord" in export_js
    assert "Prashna 问事" in export_js
    assert "合盘 Synastry" in export_js
    assert "exportHTMLReport" in export_js
    assert "exportPDFReport" in export_js
    assert "generateReportArtifact" in export_js
    assert "formatReportArtifactStatus" in export_js
    assert "downloaded_filename" in export_js
    assert "result.download_filename || result.delivery?.filename" in export_js
    assert "result.download_mime || result.delivery?.mime" in export_js
    assert "result.user_message || delivery.user_message" in export_js
    assert "delivery" in export_js
    assert "downloadBase64File" in export_js
    assert "pdf_base64" in export_js
    assert "jyotish-report-" in export_js
    assert 'data-format="html"' in read("index.html")
    assert 'data-format="pdf"' in read("index.html")
    assert 'id="export-status"' in read("index.html")
    assert 'aria-live="polite"' in read("index.html")
    assert 'rel="manifest"' in html
    assert "/manifest.webmanifest" in html
    assert "/pwa-icon.svg" in html
    assert "theme-color" in html
    assert '"display": "standalone"' in manifest
    assert '"scope": "/"' in manifest
    assert '"purpose": "any maskable"' in manifest
    assert "jyotish-shell-v1" in sw
    assert "self.addEventListener('install'" in sw
    assert "caches.open(CACHE_NAME)" in sw
    assert "url.pathname.startsWith('/api/')" in sw
    assert "request.mode === 'navigate'" in sw
    assert "cached || (request.mode === 'navigate' ? caches.match('/index.html') : undefined)" in sw
    assert "/api/report_artifact" in read("api-bridge.js")
    assert "_exportInProgress" in main
    assert "setExportBusy" in main

    for token in [
        "TERMINOLOGY_MODE_LABELS",
        "setGlossaryTerminologyMode",
        "getGlossaryTerminologyMode",
        "buildTerminologyDisplay",
        "平衡模式",
        "入门解释",
        "专业模式保留中文、英文与 Sanskrit 名称",
    ]:
        assert token in glossary
    assert "setExportStatus" in main
    assert "getExportFormatLabel" in main
    assert "clearExportStatusSoon" in main
    assert "import('./export.js')" in main
    assert "from './export.js'" not in main
    assert "parseFloat($('birth-tz').value)" not in main
    assert "window.confirm(`删除" in main
    assert "window.confirm('清空本地星盘" in main


def test_mobile_layout_keeps_dense_sections_single_column() -> None:
    style = read("style.css")
    assert "@media" in style
    for selector in [
        ".skill-stage-grid",
        ".skill-module-grid",
        ".capability-source-grid",
        ".ux-queue-grid",
        ".technique-directory-controls",
        ".technique-directory-grid",
        ".technique-explorer-actions",
        ".technique-explorer-run",
        ".technique-explorer-result",
        ".technique-explorer-loading",
        ".technique-example-badge",
        ".thematic-report-grid",
        ".thematic-report-card",
        ".saved-chart-item",
        ".technique-action-grid",
        ".technique-insight-grid",
        ".remedies-grid",
        ".provenance-grid",
        ".roadmap-grid",
        ".panchanga-condition-options",
        ".panchanga-condition-guide",
        ".panchanga-festival-details",
        ".calculation-settings-grid",
        ".rule-variant-grid",
        ".runtime-health-grid",
        ".terminology-mode-options",
        ".relationship-report-grid",
        ".relationship-report-sections",
        ".biwheel-axis-grid",
        ".composite-style-strip",
        ".spouse-status-grid",
        ".uldk-timing-grid",
        ".synastry-deep-grid",
        ".synastry-d9-compare",
        ".prashna-insight-grid",
        ".prashna-advanced-grid",
        ".prashna-saham-strip",
        ".kp-house-grid",
    ]:
        assert selector in style

    assert ".technique-json pre" in style
    assert "overflow: auto" in style
    assert ".kp-focus-select { width: 100%; min-height: 44px; }" in style
    assert ".synastry-deep-grid,\n  .synastry-d9-compare { grid-template-columns: 1fr; }" in style
    assert ".relationship-report-grid,\n  .relationship-report-sections { grid-template-columns: 1fr; }" in style
    assert ".technique-directory-controls,\n  .technique-directory-grid { grid-template-columns: 1fr; }" in style
    assert ".technique-insight-grid,\n  .thematic-report-grid { grid-template-columns: 1fr; }" in style
    assert ".technique-directory-card-head { flex-direction: column; }" in style
    assert ".panchanga-condition-options,\n  .panchanga-condition-guide,\n  .panchanga-festival-details { grid-template-columns: 1fr; }" in style
    assert ".panchanga-condition-filter { grid-column: span 1; }" in style
    assert ".calculation-settings-grid,\n  .rule-variant-grid,\n  .first-use-grid,\n  .runtime-health-grid,\n  .trust-status-grid,\n  .terminology-mode-options,\n  .case-workspace-controls { grid-template-columns: 1fr; }" in style
    assert ".case-workspace-counts,\n  .case-bulk-actions,\n  .workspace-chart-list,\n  .case-preview-panel { max-width: 100%; }" in style
    assert "健康检查通过：本地 API 服务、能力目录和 PWA 安装壳状态已记录" in read("main.js")
    assert ".biwheel-axis-grid,\n  .composite-style-strip { grid-template-columns: 1fr; }" in style
    assert ".spouse-status-grid { grid-template-columns: 1fr; }" in style
    assert ".uldk-timing-grid { grid-template-columns: 1fr; }" in style
    assert ".prashna-insight-grid,\n  .prashna-advanced-grid,\n  .prashna-mini-grid,\n  .prashna-saham-strip { grid-template-columns: 1fr; }" in style
    assert ".kp-house-grid { grid-template-columns: 1fr; }" in style
    assert ".saved-chart-item { grid-template-columns: 1fr; }" in style
    assert ".btn-save-chart { min-height: 44px; padding: 8px 14px; }" in style
    assert "overflow-wrap: anywhere" in style


def test_desktop_packaging_spike_is_documented_and_checkable() -> None:
    spike = (ROOT / "docs" / "research" / "desktop_packaging_spike_2026_06_23.md").read_text(encoding="utf-8")
    preflight = (ROOT / "scripts" / "desktop_packaging_preflight.py").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    main = read("main.js")
    gap_doc = (ROOT / "docs" / "research" / "product_gap_matrix_2026_06_22.md").read_text(encoding="utf-8")

    for token in [
        "PWA install",
        "Pake shell",
        "Tauri shell with sidecar",
        "127.0.0.1:5200",
        "scripts/desktop_packaging_preflight.py",
    ]:
        assert token in spike

    for token in [
        "manifest.webmanifest",
        "jyotish-shell-v1",
        "url.pathname.startsWith('/api/')",
        "JYOTISH_API_HOST', '127.0.0.1'",
        "pwa-install",
        "tauri-sidecar-spike",
        "first_launch_checks",
        "tests/run_frontend_click_smoke.py",
        "--mode",
        "all",
        "offline_recovery_guidance_visible",
        "PWA installed shell",
        "Pake first launch",
        "Tauri sidecar readiness",
        "toolchain_probe",
        "non_destructive",
        "rustc",
        "cargo",
        "xcodebuild",
        "pake",
        "tauri",
        "GPL-3.0",
        "signing_notarization",
    ]:
        assert token in preflight

    assert "desktop_packaging_spike_2026_06_23.md" in readme
    assert "desktop_packaging_preflight.py" in readme
    assert "tests/run_frontend_click_smoke.py --mode all" in readme
    assert "普通用户启动路径" in readme
    assert "先启动网页服务：cd jyotish-app && npm run dev -- --host 127.0.0.1 --port 5173" in readme
    assert "再启动本地 API 服务：python3 scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200" in readme
    assert "打开 Trust Center，点击运行健康检查" in readme
    assert "PWA 安装壳只包装网页服务，本地 API 服务仍需单独启动" in readme
    assert "安装后首次打开" in spike
    assert "offline_recovery_guidance_visible" in spike
    assert "Pake 适合快速 URL 壳" in main
    assert "Packaging preflight" in main
    assert "trust-run-health" in main
    assert "getRuntimeHealthStatus" in main
    assert "runTrustCenterHealthCheck" in main
    assert "Completed spike: desktop packaging path is documented" in gap_doc

    quality_gate = (ROOT / "scripts" / "run_quality_gate.py").read_text(encoding="utf-8")
    assert "普通用户启动路径" in quality_gate
    assert "cd jyotish-app && npm run dev -- --host 127.0.0.1 --port 5173" in quality_gate
    assert "python3 scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200" in quality_gate


def test_user_startup_labels_are_consistent_across_recovery_surfaces() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    quality_gate = (ROOT / "scripts" / "run_quality_gate.py").read_text(encoding="utf-8")
    app_text = "\n".join([
        read("main.js"),
        read("api-bridge.js"),
        read("public/api-bridge.js"),
        read("ai-chat.js"),
        read("auth.js"),
        read("subscription.js"),
        read("i18n.js"),
        read("skill-map.js"),
    ])
    for token in [
        "网页服务",
        "本地 API 服务",
        "PWA 安装壳",
        "Trust Center",
        "普通用户启动路径",
    ]:
        assert token in readme
        assert token in quality_gate
        assert token in app_text
    for command in [
        "cd jyotish-app && npm run dev -- --host 127.0.0.1 --port 5173",
        "python3 scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200",
    ]:
        assert command in readme
        assert command in quality_gate
        assert command not in app_text
    for old_hint in [
        "npm run web",
        "python3 scripts/jyotish_api_server.py --port 5200",
        "PWA shell",
        "PWA 壳",
        "Local API",
    ]:
        assert old_hint not in app_text


def test_karaka_i18n_declares_7_and_8_karaka_convention_boundary() -> None:
    html = read("index.html")
    i18n = read("i18n.js")
    for text in [
        "7-Karaka 与 8-Karaka 是两种传承口径",
        "Rahu 是否纳入会改变部分角色归属",
        "实际解读需先固定所用体系",
    ]:
        assert text in html
        assert text in i18n


def test_frontend_backend_contracts_with_api_handler() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from jyotish_api_server import JyotishAPIHandler

    handler = object.__new__(JyotishAPIHandler)
    audit = handler._capability_audit()
    assert audit["productization"]["summary"]["productized"] == audit["registry"]["technique_count"]
    assert audit["ux_productization"]["summary"]["excellent"] == audit["registry"]["technique_count"]
    assert audit["priority_gaps"] == []

    catalog = handler._technique_catalog()
    assert catalog["summary"]["technique_count"] == audit["registry"]["technique_count"]
    assert catalog["summary"]["runnable_count"] >= 20
    assert "/api/ashtakavarga" in catalog["filters"]["api_endpoints"]
    assert "/api/thematic_report" in catalog["filters"]["api_endpoints"]
    assert catalog["example_payloads"]["/api/ashtakavarga"]["planets"]
    assert catalog["example_payloads"]["/api/thematic_report"]["theme"] == "marriage"
    assert catalog["api_docs"]["/api/thematic_report"]["method"] == "POST"
    assert "curl -sS -X POST" in catalog["api_docs"]["/api/thematic_report"]["curl"]
    assert catalog["api_docs"]["/api/thematic_report"]["openapi"]["path"] == "/api/thematic_report"
    assert any(row["method_docs"]["api_doc_key"] == "/api/thematic_report" for row in catalog["techniques"])
    example = handler._compute_technique_example({"endpoint": "/api/ashtakavarga"})
    assert example["endpoint"] == "technique_example"
    assert example["target_endpoint"] == "/api/ashtakavarga"
    assert example["result"]["summary"]["strongest_houses"]
    thematic_example = handler._compute_technique_example({"endpoint": "/api/thematic_report"})
    assert thematic_example["target_endpoint"] == "/api/thematic_report"
    assert thematic_example["result"]["endpoint"] == "thematic_report"
    assert thematic_example["result"]["themes"]["marriage"]["summary"]

    chart = handler._compute_chart(sample_birth_payload())
    assert chart["success"] is True
    assert chart["remedies"]["evidence_chain"]
    assert chart["special_lagnas"]
    assert chart["tithi_lord_analysis"]["tithi_lord"]
    assert 0 <= chart["tithi_lord_analysis"]["tithi_score"] <= 1

    payload = {
        "planets": chart["planets"],
        "ascendant": chart["ascendant"],
    }
    ashtakavarga = handler._compute_ashtakavarga(payload)
    assert ashtakavarga["summary"]["strongest_houses"]
    assert ashtakavarga["pav_summary"]["top_planets"]
    assert ashtakavarga["sodhita_summary"]["top_signs"]
    assert ashtakavarga["yoga_pinda_summary"]["top_planets"]
    assert "yoga_pinda" in ashtakavarga["rule_variants"]["selected"]
    assert ashtakavarga["result"]["pav"]["matrix_shape"] == {"planets": 7, "signs": 12, "sources": 8}
    assert ashtakavarga["result"]["yoga_pinda"]["all_valid"] is True

    kp = handler._compute_kp(payload)
    assert kp
    assert "error" not in kp


def test_local_frontend_and_api_runtime_smoke() -> None:
    api_port, web_port = runtime_ports()
    origin = f"http://127.0.0.1:{web_port}"
    api_log = TMP / f"jyotish-api-smoke-{api_port}.log"
    web_log = TMP / f"jyotish-web-smoke-{web_port}.log"
    api = start_process(
        [
            sys.executable,
            str(API_SERVER),
            "--port",
            str(api_port),
            "--allow-origin",
            origin,
        ],
        ROOT,
        api_log,
    )
    web = start_process(
        [
            "npm",
            "run",
            "dev",
            "--",
            "--host",
            "127.0.0.1",
            "--port",
            str(web_port),
        ],
        APP,
        web_log,
    )
    try:
        try:
            wait_for_url(f"http://127.0.0.1:{api_port}/api/health", logs=[api_log])
            wait_for_url(f"{origin}/", logs=[web_log])
        except AssertionError:
            skip_if_sandbox_denies_bind(api_log)
            skip_if_sandbox_denies_bind(web_log)
            raise

        html = fetch_text(f"{origin}/")
        assert 'id="birth-form"' in html
        assert 'id="tab-kp"' in html
        assert "/main.js" in html
        assert "/api-bridge.js" in html

        health = fetch_json(f"http://127.0.0.1:{api_port}/api/health")
        assert health["status"] == "ok"
        assert "Remedies" in health["modules"]
        assert "Ashtakavarga" in health["modules"]

        audit = fetch_json(f"http://127.0.0.1:{api_port}/api/capability_audit")
        assert audit["productization"]["summary"]["productized"] == audit["registry"]["technique_count"]
        assert audit["ux_productization"]["summary"]["excellent"] == audit["registry"]["technique_count"]
        assert audit["priority_gaps"] == []

        chart = post_json(f"http://127.0.0.1:{api_port}/api/chart", sample_birth_payload())
        assert chart["success"] is True
        assert chart["planets"]["Moon"]["lon"] >= 0
        assert chart["remedies"]["evidence_chain"]

        av_payload = {
            "planets": chart["planets"],
            "ascendant": chart["ascendant"],
        }
        ashtakavarga = post_json(f"http://127.0.0.1:{api_port}/api/ashtakavarga", av_payload)
        assert ashtakavarga["summary"]["strongest_houses"]
        assert ashtakavarga["pav_summary"]["top_planets"]
        assert ashtakavarga["sodhita_summary"]["top_signs"]

        kp = post_json(f"http://127.0.0.1:{api_port}/api/kp", av_payload)
        assert kp
        assert "error" not in kp
    finally:
        stop_process(web)
        stop_process(api)
