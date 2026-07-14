#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印度占星 API 服务器 v1.0
为 jyotish-app 前端提供 v6.9.14 引擎的精算能力

启动: python3 scripts/jyotish_api_server.py --port 5200
"""

import argparse
import base64
import html as html_lib
import io
import json, sys, os, math
import importlib.util
import hashlib
import re
import secrets
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

try:
    from scripts.local_env import load_local_env
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from local_env import load_local_env
try:
    from scripts.unified_consultation_orchestrator import UnifiedConsultationOrchestrator
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from unified_consultation_orchestrator import UnifiedConsultationOrchestrator
try:
    from scripts.skill_experience import (
        build_rectification_questionnaire,
        score_rectification_answers,
        summarize_execution_status,
    )
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from skill_experience import (
        build_rectification_questionnaire,
        score_rectification_answers,
        summarize_execution_status,
    )
try:
    from scripts.candidate_time_sensitivity_scan import scan_candidate_times
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from candidate_time_sensitivity_scan import scan_candidate_times
try:
    from scripts.western_oracle_adapter import build_packet_from_oracle_payload
    from scripts.western_chart_engine import build_tropical_western_evidence_packet
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from western_oracle_adapter import build_packet_from_oracle_payload
    from western_chart_engine import build_tropical_western_evidence_packet

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPTS_DIR, '..'))
sys.path.insert(0, SCRIPTS_DIR)
load_local_env(REPO_ROOT)
_LOCAL_MODULE_CACHE = {}
_API_CHART_CACHE_SCOPE = 'api_chart_response'
_HIGH_RIGOR_JOB_SCOPE = 'high_rigor_workflow'
_UNIFIED_CONSULTATION_ORCHESTRATOR = UnifiedConsultationOrchestrator()
_ASYNC_JOB_WORKERS = max(int(os.environ.get('JYOTISH_ASYNC_JOB_WORKERS', '2')), 1)
_ASYNC_JOB_QUEUE_SIZE = max(int(os.environ.get('JYOTISH_ASYNC_JOB_QUEUE_SIZE', '8')), 0)
_ASYNC_JOB_EXECUTOR = ThreadPoolExecutor(
    max_workers=_ASYNC_JOB_WORKERS,
    thread_name_prefix='jyotish-job',
)
_ASYNC_JOB_CAPACITY = threading.BoundedSemaphore(_ASYNC_JOB_WORKERS + _ASYNC_JOB_QUEUE_SIZE)
_RATE_LIMIT_LOCK = threading.Lock()
_RATE_LIMIT_BUCKETS: dict[str, tuple[float, int]] = {}


def build_evidence_packet_view(job_record: dict | None) -> dict:
    """Public, token-protected job view. Excludes prompt internals and raw input."""
    job_record = job_record or {}
    result = job_record.get('result')
    result = result if isinstance(result, dict) else {}
    return {
        'scope': 'evidence_packet_view',
        'job_id': job_record.get('job_id'),
        'status': job_record.get('status', 'unknown'),
        'execution_status': summarize_execution_status(result),
        'machine_evidence_packet': result.get('machine_evidence_packet') or {},
        'technique_audit': result.get('technique_audit') or result.get('technique_audit_table') or [],
        'warnings': result.get('warnings') or [],
    }


def _rate_limit_per_minute() -> int:
    raw = str(os.environ.get('JYOTISH_API_RATE_LIMIT_PER_MINUTE', '120')).strip()
    try:
        return max(int(raw), 0)
    except ValueError:
        return 120


def enforce_rate_limit(client_id: str, *, now: float | None = None) -> None:
    limit = _rate_limit_per_minute()
    if limit == 0:
        return
    now = time.time() if now is None else now
    with _RATE_LIMIT_LOCK:
        window, count = _RATE_LIMIT_BUCKETS.get(client_id, (now, 0))
        if now - window >= 60:
            window, count = now, 0
        if count >= limit:
            raise RateLimited('Rate limit exceeded')
        _RATE_LIMIT_BUCKETS[client_id] = (window, count + 1)


def async_job_runtime_status() -> dict:
    scopes = (_HIGH_RIGOR_JOB_SCOPE, _API_CHART_CACHE_SCOPE)
    if _async_job_backend() == "sqlite":
        with _sqlite_job_connection() as connection:
            counts = {
                scope: connection.execute("SELECT COUNT(*) FROM async_jobs WHERE scope = ?", (scope,)).fetchone()[0]
                for scope in scopes
            }
        storage = "sqlite_single_host"
    else:
        counts = {
            scope: len(list(_async_job_dir(scope).glob('*.json')))
            if _async_job_dir(scope).is_dir() else 0
            for scope in scopes
        }
        storage = "local_file_single_host"
    return {
        'scope': 'async_job_runtime_status',
        'storage': storage,
        'worker_count': _ASYNC_JOB_WORKERS,
        'queue_size': _ASYNC_JOB_QUEUE_SIZE,
        'ttl_seconds': _async_job_ttl_seconds(),
        'record_counts': counts,
        'boundary': 'SQLite supports single-host persistence. No distributed queue or multi-node worker guarantee.',
    }


def _submit_background_job(callback):
    if not _ASYNC_JOB_CAPACITY.acquire(blocking=False):
        raise JobQueueFull('Async job queue is full')
    try:
        future = _ASYNC_JOB_EXECUTOR.submit(callback)
    except Exception:
        _ASYNC_JOB_CAPACITY.release()
        raise
    future.add_done_callback(lambda _future: _ASYNC_JOB_CAPACITY.release())
    return future


def _western_evidence_packet_from_body(
    body: dict,
    route_packet: dict,
    *,
    birth_payload: dict | None = None,
) -> dict | None:
    explicit_packet = body.get('western_evidence_packet')
    if isinstance(explicit_packet, dict):
        return explicit_packet
    oracle_payload = body.get('western_oracle_payload') or body.get('western_astrology_oracle')
    if isinstance(oracle_payload, dict):
        try:
            return build_packet_from_oracle_payload(oracle_payload, route_packet=route_packet)
        except Exception as exc:  # pragma: no cover - defensive contract boundary
            return {
                'system': 'western_astrology',
                'status': 'blocked',
                'route': dict(route_packet),
                'signals': [],
                'missing_sections': ['western_oracle_payload'],
                'adapter_error': exc.__class__.__name__,
                'boundary': 'Western oracle payload was supplied but could not be normalized.',
            }
    automatic = body.get('western_mode', body.get('western_auto_compute', 'auto'))
    if automatic in {False, 'off', 'external_only'} or body.get('entry_mode') == 'prashna' or not isinstance(birth_payload, dict):
        return None
    try:
        return build_tropical_western_evidence_packet(
            route_packet=route_packet,
            year=int(birth_payload['year']), month=int(birth_payload['month']), day=int(birth_payload['day']),
            hour=int(birth_payload['hour']), minute=int(birth_payload['minute']), second=int(birth_payload.get('second', 0)),
            latitude=float(birth_payload['lat']), longitude=float(birth_payload['lon']),
            timezone=body.get('western_timezone') or birth_payload['tz'],
            house_system=str(body.get('western_house_system', 'P')),
        )
    except Exception as exc:  # pragma: no cover - defensive boundary
        return {
            'system': 'western_astrology',
            'status': 'blocked',
            'route': dict(route_packet),
            'signals': [],
            'missing_sections': ['native_tropical_calculation'],
            'adapter_error': exc.__class__.__name__,
            'boundary': 'Native Western natal calculation could not be materialized.',
        }


def execute_consultation_workflow(
    handler,
    *,
    body: dict,
    surface: str = 'api_web',
    chart_override: dict | None = None,
) -> dict:
    birth_payload = handler._high_rigor_birth_payload(body)
    themes = handler._high_rigor_requested_themes(body)
    events = handler._high_rigor_events(body)
    question = body.get('question') or ''
    entry_mode = body.get('entry_mode', 'direct_chart')
    high_rigor = bool(body.get('return_high_rigor_shape'))
    try:
        from scripts.three_engine_parity_replay_validator import validate_manifest
    except ModuleNotFoundError:  # pragma: no cover - direct script execution
        from three_engine_parity_replay_validator import validate_manifest
    external_parity_gate = validate_manifest(
        Path(__file__).resolve().parents[1] / 'references/oracle/three_engine_parity_replay_manifest.json'
    )
    route_packet = _UNIFIED_CONSULTATION_ORCHESTRATOR.resolve_route(question, themes)
    western_evidence_packet = _western_evidence_packet_from_body(body, route_packet, birth_payload=birth_payload)
    unified_contract = _UNIFIED_CONSULTATION_ORCHESTRATOR.shared_contract(
        entry_mode=entry_mode,
        question=question,
        themes=themes,
        route_packet=route_packet,
        surface=surface,
    )
    runtime_planner = _UNIFIED_CONSULTATION_ORCHESTRATOR.runtime_planner(
        entry_mode=entry_mode,
        question=question,
        themes=themes,
        route_packet=route_packet,
        events=events,
        surface=surface,
        high_rigor=high_rigor,
    )
    executed_steps = []
    known_steps = [
        'run_prashna',
        'compute_chart',
        'run_rectification_gate',
        'run_muhurta_panchanga',
        'run_historical_event_backtest',
        'run_thematic_report',
    ]
    if body.get('dry_run') or body.get('plan_only'):
        result = handler._high_rigor_workflow_plan_only(birth_payload, themes, events)
        result['endpoint'] = 'consultation_workflow'
        result['entry_mode'] = entry_mode
        result['routing'] = route_packet
        result['unified_orchestrator'] = unified_contract
        result['runtime_planner'] = {
            **runtime_planner,
            'executed_steps': [],
            'skipped_steps': known_steps,
        }
        result['runtime_evidence_log'] = _UNIFIED_CONSULTATION_ORCHESTRATOR.runtime_evidence_log(
            surface=surface,
            entry_mode=entry_mode,
            route_packet=route_packet,
            executed_steps=[],
            skipped_steps=known_steps,
            western_evidence_packet=western_evidence_packet,
            blind=bool(body.get('blind') or body.get('blind_technical_mode')),
        )
        if western_evidence_packet:
            result['western_evidence_packet'] = western_evidence_packet
        if body.get('return_high_rigor_shape'):
            result['endpoint'] = 'high_rigor_workflow'
            result['high_rigor_external_parity'] = {
                'status': 'pass' if external_parity_gate.get('status') == 'pass' else 'blocked',
                'parity_status': external_parity_gate.get('status'),
                'reason': external_parity_gate.get('blocked_reason') or 'three_engine_parity_not_passed',
                'require_external_parity': bool(body.get('require_external_parity')),
            }
            if body.get('require_external_parity') and external_parity_gate.get('status') != 'pass':
                result['success'] = False
                result['blocked_reason'] = 'external_parity_not_passed'
        return result

    chart = dict(chart_override) if isinstance(chart_override, dict) else {}
    prashna = {}
    rectification = {}
    muhurta_panchanga = {}
    computed_chart = bool(chart)

    for step in runtime_planner.get('sync_steps', []):
        if step == 'run_prashna':
            prashna = handler._compute_prashna({
                **birth_payload,
                'question': body.get('question', 'general'),
                'question_text': body.get('question_text', ''),
                'horary_number': body.get('horary_number'),
                'planets': body.get('planets', {}),
                'asc_degree': body.get('asc_degree', 15.5),
            })
            executed_steps.append('run_prashna')
        elif step == 'run_muhurta_panchanga':
            muhurta_panchanga = handler._compute_muhurta_panchanga({
                **birth_payload,
                'reference_date': body.get('reference_date') or body.get('transit_date') or body.get('today') or body.get('current_date'),
                'question': question,
                'themes': themes,
                'activity': body.get('muhurta_activity'),
            })
            executed_steps.append('run_muhurta_panchanga')
        elif step == 'run_rectification_gate':
            chart_planets = chart.get('planets') if isinstance(chart, dict) else {}
            chart_ascendant = chart.get('ascendant') if isinstance(chart, dict) else {}
            rectification = handler._compute_rectification_gate({
                **birth_payload,
                'planets': chart_planets if isinstance(chart_planets, dict) else {},
                'ascendant': chart_ascendant if isinstance(chart_ascendant, dict) else {},
                'declared_accuracy': body.get('declared_accuracy', body.get('accuracy', 'minute')),
                'time_source': body.get('time_source', 'family_clear'),
            })
            executed_steps.append('run_rectification_gate')
        elif step == 'compute_chart':
            if not computed_chart:
                chart = handler._compute_chart(birth_payload)
                computed_chart = True
            executed_steps.append('compute_chart')

    historical_backtest = {}
    if 'run_historical_event_backtest' in runtime_planner.get('sync_steps', []):
        historical_backtest = handler._run_high_rigor_historical_backtest(birth_payload, events)
        executed_steps.append('run_historical_event_backtest')

    chart_for_theme = dict(chart) if isinstance(chart, dict) else {}
    if entry_mode == 'prashna' and isinstance(prashna, dict):
        chart_for_theme.setdefault('prashna', prashna)
    if isinstance(chart_for_theme.get('modules'), dict):
        chart_for_theme.update(chart_for_theme.get('modules', {}).get('chart') or {})

    modules = chart.get('modules') if isinstance(chart.get('modules'), dict) else {}
    prompt_snapshot = (((chart.get('ai_prompt_pack') or {}).get('evidence_snapshot')) or {}) if isinstance(chart, dict) else {}
    strict_workflow_contracts = prompt_snapshot.get('strict_workflow_contracts') if isinstance(prompt_snapshot.get('strict_workflow_contracts'), dict) else {}
    chart_guided_topics = modules.get('guided_topics') if isinstance(modules.get('guided_topics'), list) else []
    audited_remedies = handler._build_audited_remedies_from_guided_topics(chart_guided_topics)

    thematic_report = {}
    if 'run_thematic_report' in runtime_planner.get('sync_steps', []):
        thematic_report = handler._compute_thematic_report({
            **birth_payload,
            **chart_for_theme,
            'chart_data': {
                **chart_for_theme,
                'skip_full_reading_for_thematic': True,
            },
            'theme': themes,
            'skip_full_reading_for_thematic': True,
            'upstream_contract': {
                'chart': chart_for_theme,
                'strict_workflow_contracts': strict_workflow_contracts,
                'guided_topics': chart_guided_topics,
            },
        })
        executed_steps.append('run_thematic_report')

    vedastro_official = handler._high_rigor_vedastro_official_summary(chart)
    vedastro_archive_manifest = handler._compute_vedastro_gateway_archives()
    runtime_truth = vedastro_official.get('runtime_truth') if isinstance(vedastro_official.get('runtime_truth'), dict) else {}
    interpretation_source_runtime_coverage = handler._interpretation_source_runtime_coverage(chart)
    skipped_steps = [step for step in known_steps if step not in executed_steps]
    machine_evidence_packet = _UNIFIED_CONSULTATION_ORCHESTRATOR.machine_evidence_packet(
        chart=chart,
        route_packet=route_packet,
        vedastro_official=vedastro_official,
        vedastro_archive_manifest=vedastro_archive_manifest,
    )
    real_case_calibration = _UNIFIED_CONSULTATION_ORCHESTRATOR.real_case_calibration_catalog(
        route_packet=route_packet,
        machine_evidence_packet=machine_evidence_packet,
    )
    runtime_evidence_log = _UNIFIED_CONSULTATION_ORCHESTRATOR.runtime_evidence_log(
        surface=surface,
        entry_mode=entry_mode,
        route_packet=route_packet,
        executed_steps=executed_steps,
        skipped_steps=skipped_steps,
        vedastro_official=vedastro_official,
        interpretation_source_runtime_coverage=interpretation_source_runtime_coverage,
        machine_evidence_packet=machine_evidence_packet,
        real_case_calibration=real_case_calibration,
        western_evidence_packet=western_evidence_packet,
        blind=bool(body.get('blind') or body.get('blind_technical_mode')),
    )

    result = {
        'success': True,
        'endpoint': 'consultation_workflow',
        'mode': 'vedastro_official_first_existing_modules_reused',
        'entry_mode': entry_mode,
        'question': question,
        'routes': ['career', 'relationship', 'finance'],
        'themes': themes,
        'routing': route_packet,
        'unified_orchestrator': unified_contract,
        'runtime_planner': {
            **runtime_planner,
            'executed_steps': executed_steps,
            'skipped_steps': skipped_steps,
        },
        'source_priority': {
            'mode': 'vedastro_official_snapshot_first',
            'priority': [
                'vedastro_official_snapshot',
                'local_supplemental_modules',
                'local_fallback_only_when_official_blocked',
            ],
            'boundary': 'Official VedAstro raw evidence is preferred; local modules supplement, cross-check, and fallback when official calls are blocked.',
        },
        'reused_modules': [
            'vedastro_evidence_orchestrator',
            'birth_time_rectifier',
            'historical_event_backtest',
            'report_orchestrator',
            'reading_orchestrator',
            'orchestrator_bridge',
        ],
        'chart': chart,
        'rectification': rectification,
        'historical_event_backtest': historical_backtest,
        'thematic_report': thematic_report,
        'prashna': prashna,
        'muhurta_panchanga': muhurta_panchanga,
        'audited_remedies': audited_remedies,
        'vedastro_official': vedastro_official,
        'runtime_truth': runtime_truth,
        'external_parity_gate': external_parity_gate,
        'interpretation_source_runtime_coverage': interpretation_source_runtime_coverage,
        'machine_evidence_packet': machine_evidence_packet,
        'western_evidence_packet': western_evidence_packet or {},
        'real_case_calibration': real_case_calibration,
        'runtime_evidence_log': runtime_evidence_log,
        'next_questions': handler._high_rigor_next_questions(rectification, historical_backtest),
        'boundary': (
            'This endpoint composes existing project workflows. It does not claim that every VedAstro callable '
            'is executed for every chart; the official capability catalog is carried as evidence metadata and '
            'domain-relevant routes execute according to the configured sample/network limits.'
        ),
    }
    if high_rigor:
        result['high_rigor_external_parity'] = {
            'status': 'pass' if external_parity_gate.get('status') == 'pass' else 'blocked',
            'parity_status': external_parity_gate.get('status'),
            'reason': external_parity_gate.get('blocked_reason') or 'three_engine_parity_not_passed',
            'require_external_parity': bool(body.get('require_external_parity')),
        }
        if body.get('require_external_parity') and external_parity_gate.get('status') != 'pass':
            result['success'] = False
            result['blocked_reason'] = 'external_parity_not_passed'
    if body.get('return_high_rigor_shape'):
        result['endpoint'] = 'high_rigor_workflow'
    return result


def _load_local_module(module_name):
    cached = _LOCAL_MODULE_CACHE.get(module_name)
    if cached:
        return cached
    module_path = os.path.join(SCRIPTS_DIR, f'{module_name}.py')
    spec = importlib.util.spec_from_file_location(f'_jyotish_local_{module_name}', module_path)
    if not spec or not spec.loader:
        raise ImportError(f'Cannot load local module: {module_name}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _LOCAL_MODULE_CACHE[module_name] = module
    return module


def _api_chart_cache_dir() -> Path:
    path = Path(REPO_ROOT) / 'scratch' / 'local' / 'api_chart_cache'
    path.mkdir(parents=True, exist_ok=True)
    return path


def _high_rigor_job_dir() -> Path:
    path = Path(REPO_ROOT) / 'scratch' / 'local' / 'high_rigor_jobs'
    path.mkdir(parents=True, exist_ok=True)
    return path


def _async_job_dir(scope: str) -> Path:
    if scope == _HIGH_RIGOR_JOB_SCOPE:
        return _high_rigor_job_dir()
    path = Path(REPO_ROOT) / 'scratch' / 'local' / f'{scope}_jobs'
    path.mkdir(parents=True, exist_ok=True)
    return path


def _api_chart_cache_ttl_seconds() -> float:
    raw = str(os.environ.get('JYOTISH_API_CHART_CACHE_TTL_SECONDS', '900')).strip()
    try:
        ttl = float(raw)
    except ValueError:
        ttl = 900.0
    return max(ttl, 0.0)


def _free_tier_queue_enabled_env() -> bool:
    raw_values = [
        str(os.environ.get("VEDASTRO_FREE_TIER_QUEUE", "")).strip().lower(),
        str(os.environ.get("VEDASTRO_FREE_TIER_QUEUE_ENABLED", "")).strip().lower(),
        str(os.environ.get("VEDASTRO_ENABLE_FREE_TIER_QUEUE", "")).strip().lower(),
    ]
    return any(value in {"1", "true", "yes", "on"} for value in raw_values)


def _vedastro_runtime_fingerprint() -> dict:
    endpoint = os.environ.get('VEDASTRO_API_ENDPOINT', '').strip()
    return {
        'endpoint_host': (urlparse(endpoint).netloc or '').lower(),
        'network_enabled': str(os.environ.get('VEDASTRO_ENABLE_NETWORK', '')).strip().lower() in {'1', 'true', 'yes'},
        'has_api_key': bool(os.environ.get('VEDASTRO_API_KEY', '').strip()),
    }


def _build_api_chart_cache_payload(body: dict) -> dict:
    return {
        'birth': {
            'year': body.get('year'),
            'month': body.get('month'),
            'day': body.get('day'),
            'hour': body.get('hour'),
            'minute': body.get('minute'),
            'second': body.get('second', 0),
            'lat': body.get('lat'),
            'lon': body.get('lon'),
            'tz': body.get('tz'),
        },
        'calculation': {
            'ayanamsa': body.get('ayanamsa', 'lahiri'),
            'node_mode': body.get('node_mode', body.get('nodeMode', 'mean')),
            'today': body.get('today') or body.get('current_date'),
            'transit_date': body.get('transit_date'),
        },
        'vedastro_runtime': _vedastro_runtime_fingerprint(),
    }


def _api_chart_cache_key(cache_payload: dict) -> str:
    canonical = json.dumps(cache_payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def _api_chart_cache_path(cache_key: str) -> Path:
    return _api_chart_cache_dir() / f'{cache_key}.json'


def _attach_api_chart_runtime_cache(payload: dict, *, cache_key: str, created_at_unix: float, cache_hit: bool) -> dict:
    payload_copy = json.loads(json.dumps(payload))
    ttl_seconds = _api_chart_cache_ttl_seconds()
    created_at = datetime.utcfromtimestamp(created_at_unix).strftime('%Y-%m-%dT%H:%M:%SZ')
    expires_at = datetime.utcfromtimestamp(created_at_unix + ttl_seconds).strftime('%Y-%m-%dT%H:%M:%SZ')
    payload_copy['runtime_cache'] = {
        'scope': _API_CHART_CACHE_SCOPE,
        'cache_hit': cache_hit,
        'cache_key': cache_key,
        'cache_created_at': created_at,
        'cache_expires_at': expires_at,
        'cache_ttl_seconds': ttl_seconds,
    }
    return payload_copy


def _load_api_chart_response_cache(cache_payload: dict) -> dict | None:
    ttl_seconds = _api_chart_cache_ttl_seconds()
    if ttl_seconds <= 0:
        return None
    cache_key = _api_chart_cache_key(cache_payload)
    cache_path = _api_chart_cache_path(cache_key)
    if not cache_path.exists():
        return None
    try:
        record = json.loads(cache_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(record, dict):
        return None
    created_at_unix = record.get('created_at')
    payload = record.get('payload')
    if not isinstance(created_at_unix, (int, float)) or not isinstance(payload, dict):
        return None
    if time.time() - float(created_at_unix) > ttl_seconds:
        return None
    return _attach_api_chart_runtime_cache(
        payload,
        cache_key=cache_key,
        created_at_unix=float(created_at_unix),
        cache_hit=True,
    )


def _store_api_chart_response_cache(cache_payload: dict, payload: dict) -> dict:
    cache_key = _api_chart_cache_key(cache_payload)
    created_at_unix = time.time()
    payload_with_cache = _attach_api_chart_runtime_cache(
        payload,
        cache_key=cache_key,
        created_at_unix=created_at_unix,
        cache_hit=False,
    )
    ttl_seconds = _api_chart_cache_ttl_seconds()
    if ttl_seconds > 0:
        record = {
            'cache_key': cache_key,
            'created_at': created_at_unix,
            'payload': payload_with_cache,
        }
        _api_chart_cache_path(cache_key).write_text(
            json.dumps(record, ensure_ascii=False, sort_keys=True),
            encoding='utf-8',
        )
    return payload_with_cache


def _high_rigor_job_path(job_id: str) -> Path:
    return _high_rigor_job_dir() / f'{job_id}.json'


def _async_job_path(scope: str, job_id: str) -> Path:
    return _async_job_dir(scope) / f'{job_id}.json'


def _async_job_ttl_seconds() -> float:
    raw = str(os.environ.get('JYOTISH_ASYNC_JOB_TTL_SECONDS', '3600')).strip()
    try:
        return max(float(raw), 1.0)
    except ValueError:
        return 3600.0


def _async_job_backend() -> str:
    return "sqlite" if os.environ.get("JYOTISH_ASYNC_JOB_BACKEND", "file").strip().lower() == "sqlite" else "file"


def _sqlite_job_db_path() -> Path:
    return Path(REPO_ROOT) / "scratch" / "local" / "async_jobs.sqlite3"


def _sqlite_job_connection() -> sqlite3.Connection:
    path = _sqlite_job_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS async_jobs (scope TEXT NOT NULL, job_id TEXT NOT NULL, expires_at REAL, payload TEXT NOT NULL, PRIMARY KEY (scope, job_id))"
    )
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return connection


def prune_expired_async_jobs() -> dict:
    """Best-effort startup cleanup for local job records; never reads payloads."""
    removed = 0
    scanned = 0
    if _async_job_backend() == "sqlite":
        with _sqlite_job_connection() as connection:
            scanned = connection.execute("SELECT COUNT(*) FROM async_jobs").fetchone()[0]
            removed = connection.execute(
                "DELETE FROM async_jobs WHERE expires_at IS NOT NULL AND expires_at <= ?", (time.time(),)
            ).rowcount
        return {'scope': 'async_job_cleanup', 'scanned': scanned, 'removed': removed}
    for scope in (_HIGH_RIGOR_JOB_SCOPE, _API_CHART_CACHE_SCOPE):
        directory = _async_job_dir(scope)
        if not directory.is_dir():
            continue
        for path in directory.glob('*.json'):
            scanned += 1
            try:
                record = json.loads(path.read_text(encoding='utf-8'))
                expires_at = record.get('expires_at_unix') if isinstance(record, dict) else None
                if isinstance(expires_at, (int, float)) and time.time() >= float(expires_at):
                    path.unlink()
                    removed += 1
            except (OSError, json.JSONDecodeError):
                continue
    return {'scope': 'async_job_cleanup', 'scanned': scanned, 'removed': removed}


def _new_async_job_identity(prefix: str) -> dict:
    return {
        'job_id': f'{prefix}_{secrets.token_hex(16)}',
        'access_token': secrets.token_urlsafe(32),
    }


def _access_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _load_high_rigor_job_record(job_id: str, *, access_token: str = '') -> dict | None:
    return _load_async_job_record(
        _HIGH_RIGOR_JOB_SCOPE,
        job_id,
        access_token=access_token,
    )


def _write_high_rigor_job_record(job_id: str, payload: dict) -> dict:
    return _write_async_job_record(_HIGH_RIGOR_JOB_SCOPE, job_id, payload)


def _load_async_job_record(scope: str, job_id: str, *, access_token: str = '') -> dict | None:
    path = None
    if _async_job_backend() == "sqlite":
        with _sqlite_job_connection() as connection:
            row = connection.execute(
                "SELECT payload FROM async_jobs WHERE scope = ? AND job_id = ?", (scope, job_id)
            ).fetchone()
        if row is None:
            return None
        try:
            record = json.loads(row[0])
        except json.JSONDecodeError:
            return None
    else:
        path = _async_job_path(scope, job_id)
        if not path.exists():
            return None
        try:
            record = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            return None
    expires_at = record.get('expires_at_unix')
    if isinstance(expires_at, (int, float)) and time.time() >= float(expires_at):
        if _async_job_backend() == "sqlite":
            with _sqlite_job_connection() as connection:
                connection.execute("DELETE FROM async_jobs WHERE scope = ? AND job_id = ?", (scope, job_id))
        elif path is not None:
            try:
                path.unlink()
            except OSError:
                pass
        return None
    expected = record.get('access_token_hash')
    if not isinstance(expected, str) or not access_token:
        raise JobAccessDenied('Async job access token required')
    if not secrets.compare_digest(expected, _access_token_hash(access_token)):
        raise JobAccessDenied('Async job access token invalid')
    return record


def _write_async_job_record(scope: str, job_id: str, payload: dict) -> dict:
    if _async_job_backend() == "sqlite":
        with _sqlite_job_connection() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO async_jobs (scope, job_id, expires_at, payload) VALUES (?, ?, ?, ?)",
                (scope, job_id, payload.get("expires_at_unix"), json.dumps(payload, ensure_ascii=False, sort_keys=True)),
            )
        return payload
    path = _async_job_path(scope, job_id)
    temp_path = path.with_suffix(f'.{secrets.token_hex(8)}.tmp')
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding='utf-8')
    os.chmod(temp_path, 0o600)
    os.replace(temp_path, path)
    return payload


def _attach_vedastro_main_entry_overview(chart_result, birth_payload):
    if not isinstance(chart_result, dict):
        return chart_result
    modules = chart_result.setdefault('modules', {})
    if not isinstance(modules, dict):
        modules = {}
        chart_result['modules'] = modules
    if modules.get('vedastro_range_scan_result'):
        return chart_result

    try:
        orchestrator = _load_local_module('vedastro_evidence_orchestrator')
        priority = _load_local_module('vedastro_priority')
    except Exception:
        return chart_result

    reference_date = str(
        birth_payload.get('transit_date')
        or birth_payload.get('today')
        or datetime.utcnow().strftime('%Y-%m-%d')
    )[:10]
    vedastro_evidence = orchestrator.orchestrate_vedastro_evidence({
        'year': birth_payload.get('year'),
        'month': birth_payload.get('month'),
        'day': birth_payload.get('day'),
        'hour': birth_payload.get('hour'),
        'minute': birth_payload.get('minute'),
        'second': birth_payload.get('second', 0),
        'lat': birth_payload.get('lat'),
        'lon': birth_payload.get('lon'),
        'tz': birth_payload.get('tz'),
        'ayanamsa_policy': birth_payload.get('ayanamsa') or 'lahiri',
        'node_policy': birth_payload.get('node_mode') or birth_payload.get('nodeMode') or 'mean',
    }, route='overview', reference_date=reference_date, case_id='api_chart')
    if isinstance(vedastro_evidence, dict):
        metadata = vedastro_evidence.get('source_metadata')
        if not isinstance(metadata, dict):
            metadata = {}
        metadata.setdefault('ingestion_profile', 'main_entry_overview')
        metadata.setdefault('reference_date', reference_date)
        vedastro_evidence['source_metadata'] = metadata
    modules['vedastro_range_scan_result'] = vedastro_evidence
    official_snapshot = vedastro_evidence.get('official_full_snapshot') if isinstance(vedastro_evidence, dict) else None
    if isinstance(official_snapshot, dict):
        priority.apply_vedastro_source_priority(chart_result, official_snapshot=official_snapshot)
    return chart_result


def _attach_guided_topics(chart_result):
    if not isinstance(chart_result, dict):
        return chart_result
    modules = chart_result.setdefault('modules', {})
    if not isinstance(modules, dict):
        modules = {}
        chart_result['modules'] = modules
    if isinstance(modules.get('guided_topics'), list):
        return chart_result
    try:
        builder = _load_local_module('guided_topic_discovery').build_guided_topics
        modules['guided_topics'] = builder(chart_result)
    except Exception as exc:
        modules['guided_topics'] = []
        warnings = chart_result.setdefault('warnings', [])
        if isinstance(warnings, list):
            warnings.append(f'guided-topics: {exc}')
    return chart_result


def _build_vedastro_overview_payload_from_chart(chart):
    modules = chart.get('modules') if isinstance(chart, dict) else {}
    overview = modules.get('vedastro_range_scan_result') if isinstance(modules, dict) else {}
    if not isinstance(overview, dict):
        return {
            'status': 'blocked',
            'source': 'vedastro_service_adapter_candidate',
            'ingestion_profile': None,
            'search_scope': None,
            'reference_date': None,
            'event_count': 0,
            'domain_statuses': {},
            'top_events_by_domain': {},
            'boundary_note': 'VedAstro main-entry overview was not attached.',
            'visibility': 'user_visible_overview_only',
        }
    metadata = overview.get('source_metadata') if isinstance(overview.get('source_metadata'), dict) else {}
    return {
        'status': overview.get('status') or 'blocked',
        'source': overview.get('backend') or 'vedastro_service_adapter_candidate',
        'ingestion_profile': metadata.get('ingestion_profile'),
        'search_scope': metadata.get('search_scope'),
        'reference_date': metadata.get('reference_date'),
        'event_count': int(overview.get('event_count', 0) or 0),
        'domain_statuses': metadata.get('domain_statuses') or {},
        'top_events_by_domain': overview.get('top_events_by_domain') or {},
        'boundary_note': (
            overview.get('reason')
            or 'This is overview only and does not replace explicit long-range VedAstro scans.'
        ),
        'visibility': 'user_visible_overview_only',
    }


def _build_vedastro_official_full_snapshot_payload_from_chart(chart):
    modules = chart.get('modules') if isinstance(chart, dict) else {}
    snapshot = modules.get('vedastro_official_full_snapshot') if isinstance(modules, dict) else {}
    strict_workflow_contracts = snapshot.get('strict_workflow_contracts') if isinstance(snapshot, dict) else {}
    if not isinstance(strict_workflow_contracts, dict):
        strict_workflow_contracts = {}
    if not isinstance(snapshot, dict) or not snapshot:
        return {
            'status': 'blocked',
            'available': False,
            'operation': 'official_full_snapshot',
            'primary_source': 'vedastro_official',
            'strict_workflow_primary_route': None,
            'strict_workflow_routes_available': [],
            'strict_workflow_contracts': {},
            'boundary_note': 'VedAstro official full snapshot is not attached.',
        }
    manifest = snapshot.get('request_manifest') if isinstance(snapshot.get('request_manifest'), dict) else {}
    requests = manifest.get('requests') if isinstance(manifest.get('requests'), list) else []
    sections = snapshot.get('snapshot_sections') if isinstance(snapshot.get('snapshot_sections'), dict) else {}
    metadata = snapshot.get('source_metadata') if isinstance(snapshot.get('source_metadata'), dict) else {}
    official_bundle = metadata.get('official_python_bundle') if isinstance(metadata.get('official_python_bundle'), dict) else {}
    full_catalog = metadata.get('official_full_capability_catalog') if isinstance(metadata.get('official_full_capability_catalog'), dict) else {}
    coverage = official_bundle.get('coverage') if isinstance(official_bundle.get('coverage'), dict) else {}
    official_chart = snapshot.get('official_chart') if isinstance(snapshot.get('official_chart'), dict) else {}
    dynamic_selection = full_catalog.get('dynamic_selection') if isinstance(full_catalog.get('dynamic_selection'), dict) else {}
    report_references = {
        theme: selection.get('report_reference')
        for theme, selection in dynamic_selection.items()
        if isinstance(selection, dict) and isinstance(selection.get('report_reference'), dict)
    }
    return {
        'status': snapshot.get('status') or 'blocked',
        'available': bool(snapshot.get('available')),
        'operation': snapshot.get('operation') or 'official_full_snapshot',
        'primary_source': snapshot.get('primary_source') or 'vedastro_official',
        'official_python_path': metadata.get('official_python_path'),
        'official_bundle_status': official_bundle.get('status'),
        'official_primary_sections_ok': coverage.get('filled_sections') or [],
        'official_chart_available': bool(official_chart.get('planets')) and bool(official_chart.get('ascendant')),
        'official_full_capability_catalog_status': full_catalog.get('status'),
        'official_full_capability_catalog_summary': full_catalog.get('summary') or {},
        'official_full_capability_catalog_coverage': full_catalog.get('coverage') or {},
        'official_full_capability_domain_routing': full_catalog.get('domain_routing') or {},
        'official_full_capability_dynamic_selection': dynamic_selection,
        'official_report_references': report_references,
        'strict_workflow_primary_route': snapshot.get('strict_workflow_primary_route'),
        'strict_workflow_routes_available': snapshot.get('strict_workflow_routes_available') or list(strict_workflow_contracts.keys()),
        'strict_workflow_contracts': strict_workflow_contracts,
        'section_statuses': snapshot.get('section_statuses') or {},
        'snapshot_section_keys': sorted(sections.keys()),
        'request_section_count': len(requests),
        'request_sections': [item.get('section') for item in requests if isinstance(item, dict)],
        'method_catalog': manifest.get('method_catalog') or {},
        'user_visibility': snapshot.get('user_visibility') or 'backend_raw_evidence_not_direct_user_report',
        'source_metadata': snapshot.get('source_metadata') or {},
        'boundary_note': (
            snapshot.get('reason')
            or 'VedAstro official full snapshot is the primary raw evidence layer; user reports consume selected slices only.'
        ),
    }


def _preferred_strict_contract(strict_workflow_contracts, primary_route=None):
    if not isinstance(strict_workflow_contracts, dict) or not strict_workflow_contracts:
        return None, {}
    route = primary_route if primary_route in strict_workflow_contracts else next(iter(strict_workflow_contracts.keys()))
    contract = strict_workflow_contracts.get(route)
    return route, contract if isinstance(contract, dict) else {}


def _strict_adjudication_bundle_from_contract(contract, *, interpretation_axes=None, monthly_humanized=None):
    if not isinstance(contract, dict) or not contract:
        return {}
    bundle = {
        'question_type': contract.get('question_type'),
        'confidence_cap': contract.get('confidence_cap'),
        'blocked': bool(contract.get('blocked')),
        'reason': contract.get('reason'),
        'strict_audit_gate': contract.get('technique_audit_summary') or {},
        'monthly_adjudication_summary': contract.get('monthly_adjudication_summary') or {},
        'official_day_signal_summary': contract.get('official_day_signal_summary') or {},
        'interpretation_axes': interpretation_axes or contract.get('interpretation_axes') or [],
        'monthly_adjudication_summary_humanized': monthly_humanized or contract.get('monthly_adjudication_summary_humanized') or {},
        'narrative_contract': contract.get('narrative_contract') or {},
    }
    return bundle

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

DEFAULT_ALLOWED_ORIGINS = {
    'http://localhost:3456',
    'http://127.0.0.1:3456',
    'http://localhost:3457',
    'http://127.0.0.1:3457',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
}
MAX_REQUEST_BYTES = 2 * 1024 * 1024
MAX_IMPORT_FILE_BYTES = 1536 * 1024
MAX_IMPORT_TEXT_CHARS = 500_000
MAX_REPORT_HTML_CHARS = 1_200_000
MAX_REPORT_BASE64_BYTES = 8 * 1024 * 1024
REPORT_ARTIFACT_DIR = os.path.join('/private/tmp', 'jyotish-reports')

API_COMMAND_MAP = {
    'chart': '/api/chart',
    'kp': '/api/kp',
    'prashna': '/api/prashna',
    'synastry': '/api/synastry',
    'ashtakoot': '/api/synastry',
    'dasha': '/api/dasha',
    'chara-dasha': '/api/dasha/chara',
    'remedies': '/api/remedies',
    'sade_sati': '/api/sade_sati',
    'pancha_mahapurusha': '/api/pancha_mahapurusha',
    'career': '/api/career',
    'relationship': '/api/relationship',
    'full-reading': '/api/chart',
    'tajika': '/api/tajika',
    'solar-return': '/api/annual',
    'muhurta': '/api/muhurta',
    'panchanga-range': '/api/panchanga_range',
    'bhava-chalit': '/api/bhava_chalit',
    'sudarshana': '/api/sudarshana',
    'nakshatra-full': '/api/nakshatra_full',
    'varga-full': '/api/varga_full',
    'jaimini': '/api/jaimini',
    'ashtakavarga': '/api/ashtakavarga',
    'shadbala': '/api/shadbala',
    'yoga': '/api/yogas',
    'aspects': '/api/aspects',
    'rectification': '/api/rectification_gate',
    'case-validation': '/api/case_validation',
    'divisional-yoga': '/api/divisional_yoga',
    'deep-varga-avastha': '/api/deep_varga_avastha',
    'kakshya': '/api/kakshya',
    'bhava-bala': '/api/bhava_bala',
    'transit-trigger': '/api/transit',
    'audit-capabilities': '/api/capability_audit',
    'thematic-report': '/api/thematic_report',
    'consultation-workflow': '/api/consultation_workflow',
    'high-rigor-workflow': '/api/high_rigor_workflow',
    'report-artifact': '/api/report_artifact',
}

TECHNIQUE_EXAMPLE_ENDPOINTS = {
    '/api/ashtakavarga',
    '/api/bhava_bala',
    '/api/bhava_chalit',
    '/api/career',
    '/api/case_validation',
    '/api/dasha',
    '/api/dasha/chara',
    '/api/divisional_yoga',
    '/api/deep_varga_avastha',
    '/api/jaimini',
    '/api/kakshya',
    '/api/kp',
    '/api/muhurta',
    '/api/nakshatra_full',
    '/api/pancha_mahapurusha',
    '/api/prashna',
    '/api/rectification_gate',
    '/api/relationship',
    '/api/remedies',
    '/api/sade_sati',
    '/api/shadbala',
    '/api/sudarshana',
    '/api/synastry',
    '/api/consultation_workflow',
    '/api/high_rigor_workflow',
    '/api/thematic_report',
    '/api/transit',
    '/api/varga_full',
    '/api/yogas',
}

SAMPLE_PLANETS = {
    'Sun': {'lon': 280.0, 'degree': 10.0, 'degree_in_sign': 10.0, 'sign_idx': 9, 'sign': 'Capricorn', 'house': 10},
    'Moon': {'lon': 123.0, 'degree': 3.0, 'degree_in_sign': 3.0, 'sign_idx': 4, 'sign': 'Leo', 'house': 5},
    'Mars': {'lon': 210.0, 'degree': 0.0, 'degree_in_sign': 0.0, 'sign_idx': 7, 'sign': 'Scorpio', 'house': 8},
    'Mercury': {'lon': 275.0, 'degree': 5.0, 'degree_in_sign': 5.0, 'sign_idx': 9, 'sign': 'Capricorn', 'house': 10},
    'Jupiter': {'lon': 15.0, 'degree': 15.0, 'degree_in_sign': 15.0, 'sign_idx': 0, 'sign': 'Aries', 'house': 1},
    'Venus': {'lon': 330.0, 'degree': 0.0, 'degree_in_sign': 0.0, 'sign_idx': 11, 'sign': 'Pisces', 'house': 12},
    'Saturn': {'lon': 300.0, 'degree': 0.0, 'degree_in_sign': 0.0, 'sign_idx': 10, 'sign': 'Aquarius', 'house': 11},
    'Rahu': {'lon': 45.0, 'degree': 15.0, 'degree_in_sign': 15.0, 'sign_idx': 1, 'sign': 'Taurus', 'house': 2},
    'Ketu': {'lon': 225.0, 'degree': 15.0, 'degree_in_sign': 15.0, 'sign_idx': 7, 'sign': 'Scorpio', 'house': 8},
}
SAMPLE_ASCENDANT = {'sign': 'Aries', 'sign_idx': 0, 'degree': 12.0, 'degree_in_sign': 12.0, 'lon': 12.0}

# 城市数据库（简化版）
CITY_DB = {
    '北京': (39.9, 116.4, 8), '上海': (31.2, 121.5, 8), '广州': (23.1, 113.3, 8),
    '深圳': (22.5, 114.1, 8), '成都': (30.6, 104.1, 8), '重庆': (29.6, 106.5, 8),
    '杭州': (30.3, 120.2, 8), '南京': (32.1, 118.8, 8), '武汉': (30.6, 114.3, 8),
    '西安': (34.3, 108.9, 8), '郑州': (34.8, 113.7, 8), '长沙': (28.2, 113.0, 8),
    '天津': (39.1, 117.2, 8), '香港': (22.3, 114.2, 8), '台北': (25.0, 121.5, 8),
    'New York': (40.7, -74.0, -5), 'London': (51.5, -0.1, 0),
    'Tokyo': (35.7, 139.7, 9), 'Sydney': (-33.9, 151.2, 10),
    'Delhi': (28.6, 77.2, 5.5), 'Mumbai': (19.1, 72.9, 5.5),
    'Paris': (48.9, 2.3, 1), 'Berlin': (52.5, 13.4, 1),
    'Los Angeles': (34.1, -118.2, -8), 'Chicago': (41.9, -87.6, -6),
    'San Francisco': (37.8, -122.4, -8), 'Seattle': (47.6, -122.3, -8),
    'Boston': (42.4, -71.1, -5), 'Toronto': (43.7, -79.4, -5),
    'Singapore': (1.3, 103.8, 8), 'Dubai': (25.2, 55.3, 4),
}


class BadRequest(ValueError):
    """Client-side request validation failed."""


class Forbidden(PermissionError):
    """Request failed the local API trust boundary."""


class UnsupportedMediaType(ValueError):
    """Request body media type is not supported."""


class JobAccessDenied(PermissionError):
    """Async job capability token is missing or invalid."""


class JobQueueFull(RuntimeError):
    """Bounded async worker queue has no remaining capacity."""


class RateLimited(RuntimeError):
    """Client exceeded the local fixed-window request budget."""


class JyotishAPIHandler(BaseHTTPRequestHandler):
    server_version = 'JyotishAPI/6.9.14'

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._send_cors_headers()
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Vary', 'Origin')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode())

    def _error_json(self, message, status=500, error_code='ERR_INTERNAL'):
        self._json({'success': False, 'error': message, 'error_code': error_code}, status)

    def _html(self, content, status=200):
        encoded = content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self._send_cors_headers()
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_cors_headers(self):
        origin = self.headers.get('Origin')
        allowed = getattr(self.server, 'allowed_origins', DEFAULT_ALLOWED_ORIGINS)
        if origin in allowed:
            self.send_header('Access-Control-Allow-Origin', origin)

    def _enforce_request_security(self, *, require_json=False):
        origin = self.headers.get('Origin')
        allowed = getattr(self.server, 'allowed_origins', DEFAULT_ALLOWED_ORIGINS)
        if origin and origin not in allowed:
            raise Forbidden('Origin is not allowed')
        host = (self.headers.get('Host') or '').split(':', 1)[0].strip('[]').lower()
        if host and host not in {'localhost', '127.0.0.1', '::1'}:
            raise Forbidden('Host is not allowed')
        if require_json:
            content_type = (self.headers.get('Content-Type') or '').split(';', 1)[0].strip().lower()
            if content_type != 'application/json':
                raise UnsupportedMediaType('Content-Type must be application/json')
        if urlparse(self.path).path.startswith('/api/'):
            client = getattr(self, 'client_address', ('unknown',))[0]
            enforce_rate_limit(str(client))

    def _job_access_token(self):
        authorization = self.headers.get('Authorization') or ''
        scheme, _, token = authorization.partition(' ')
        return token.strip() if scheme.lower() == 'bearer' else ''

    def _vedastro_status(self):
        adapter = _load_local_module('vedastro_service_adapter')
        endpoint = os.environ.get('VEDASTRO_API_ENDPOINT', '').strip()
        network_flag = os.environ.get('VEDASTRO_ENABLE_NETWORK', '').strip().lower()
        network_enabled = network_flag in {'1', 'true', 'yes'}
        parsed = urlparse(endpoint) if endpoint else None
        configured = bool(endpoint)
        if not configured:
            status = 'service_endpoint_not_configured'
        elif not network_enabled:
            status = 'network_execution_disabled'
        else:
            status = 'live_ready'
        artifact_dir = getattr(adapter, 'ARTIFACT_DIR', None)
        latest_artifact = None
        if artifact_dir and os.path.isdir(artifact_dir):
            artifacts = sorted(
                (os.path.join(artifact_dir, name) for name in os.listdir(artifact_dir) if name.endswith('.json')),
                key=lambda path: os.path.getmtime(path),
                reverse=True,
            )
            if artifacts:
                latest_artifact = os.path.relpath(artifacts[0], REPO_ROOT)
        return {
            'adapter': 'vedastro_service_adapter',
            'backend': 'vedastro_service_adapter_candidate',
            'status': status,
            'configured': configured,
            'network_enabled': network_enabled,
            'endpoint_host': parsed.netloc if parsed else None,
            'required_env': {
                'endpoint': 'VEDASTRO_API_ENDPOINT',
                'network': 'VEDASTRO_ENABLE_NETWORK',
                'api_key_optional': 'VEDASTRO_API_KEY',
            },
            'live_profile': 'vedastro-live',
            'transport': 'http_json_service_boundary',
            'range_scan_role': adapter.VEDASTRO_CALCULATION_COVERAGE['range_scan_role'],
            'official_events_builder_methods': adapter.VEDASTRO_CALCULATION_COVERAGE['official_events_builder_methods'],
            'artifact_dir': 'scratch/local/vedastro_adapter',
            'latest_artifact': latest_artifact,
            'boundary': 'VedAstro is optional external timing evidence; local Jyotish gates remain authoritative.',
        }

    def do_OPTIONS(self):
        try:
            self._enforce_request_security()
            self._json({})
        except RateLimited as exc:
            self._error_json(str(exc), 429, 'ERR_RATE_LIMITED')
        except Forbidden as exc:
            self._error_json(str(exc), 403, 'ERR_FORBIDDEN')

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            self._enforce_request_security()
            if path == '/':
                page = Path(REPO_ROOT) / 'web' / 'index.html'
                if not page.is_file():
                    self._error_json('Home page unavailable', 404, 'ERR_NOT_FOUND')
                else:
                    self._html(page.read_text(encoding='utf-8'))
            elif path == '/evidence':
                page = Path(REPO_ROOT) / 'web' / 'evidence_packet.html'
                if not page.is_file():
                    self._error_json('Evidence Packet page unavailable', 404, 'ERR_NOT_FOUND')
                else:
                    self._html(page.read_text(encoding='utf-8'))
            elif path == '/rectification':
                page = Path(REPO_ROOT) / 'web' / 'rectification.html'
                if not page.is_file():
                    self._error_json('Rectification page unavailable', 404, 'ERR_NOT_FOUND')
                else:
                    self._html(page.read_text(encoding='utf-8'))
            elif path == '/api/health':
                swisseph_available = False
                swisseph_version = None
                try:
                    import swisseph as swe
                    swisseph_available = True
                    swisseph_version = getattr(swe, 'version', None) or getattr(swe, '__version__', None)
                except Exception:
                    swisseph_available = False
                    swisseph_version = None
                self._json({
                    'status': 'ok',
                    'version': '6.9.14',
                    'swisseph_available': swisseph_available,
                    'swisseph_version': swisseph_version,
                    'ayanamsa_default': 'lahiri',
                    'modules': 'Chart/KP/Synastry/Prashna/Remedies/Dasha/Varga/Jaimini/Ashtakavarga/Shadbala/Yoga/Aspects/Tajika/Muhurta/BhavaChalit/BhavaBala/Sudarshana/Nakshatra/Transit/RectificationGate/CaseValidation/DivisionalYoga/Kakshya',
                    'async_job_runtime': async_job_runtime_status(),
                })
            elif path == '/api/cities':
                self._json(list(CITY_DB.keys()))
            elif path == '/api/capability_audit':
                self._json(self._capability_audit())
            elif path == '/api/technique_catalog':
                self._json(self._technique_catalog())
            elif path == '/api/vedastro/status':
                self._json(self._vedastro_status())
            elif path == '/api/vedastro_gateway/status':
                self._json(self._compute_vedastro_gateway_status())
            elif path == '/api/vedastro_gateway/archives':
                self._json(self._compute_vedastro_gateway_archives())
            elif path.startswith('/api/vedastro_gateway/jobs/'):
                job_id = path.rsplit('/', 1)[-1]
                result = self._compute_vedastro_gateway_job(job_id)
                if result is None:
                    self._error_json('Not found', 404, 'ERR_NOT_FOUND')
                else:
                    self._json(result)
            elif path.startswith('/api/chart/jobs/'):
                job_id = path.rsplit('/', 1)[-1]
                result = self._get_chart_job(job_id)
                if result is None:
                    self._error_json('Not found', 404, 'ERR_NOT_FOUND')
                else:
                    self._json(result)
            elif path.startswith('/api/high_rigor_workflow/jobs/'):
                job_id = path.rsplit('/', 1)[-1]
                result = self._get_high_rigor_job(job_id)
                if result is None:
                    self._error_json('Not found', 404, 'ERR_NOT_FOUND')
                else:
                    self._json(result)
            elif path.startswith('/api/evidence_packet/chart/'):
                job_id = path.rsplit('/', 1)[-1]
                result = self._get_chart_job(job_id)
                if result is None:
                    self._error_json('Not found', 404, 'ERR_NOT_FOUND')
                else:
                    self._json(build_evidence_packet_view(result))
            elif path.startswith('/api/evidence_packet/high_rigor_workflow/'):
                job_id = path.rsplit('/', 1)[-1]
                result = self._get_high_rigor_job(job_id)
                if result is None:
                    self._error_json('Not found', 404, 'ERR_NOT_FOUND')
                else:
                    self._json(build_evidence_packet_view(result))
            elif path == '/api/real_case_revalidation':
                self._json(self._real_case_revalidation())
            else:
                self._error_json('Not found', 404, 'ERR_NOT_FOUND')
        except RateLimited as exc:
            self._error_json(str(exc), 429, 'ERR_RATE_LIMITED')
        except (Forbidden, JobAccessDenied) as exc:
            self._error_json(str(exc), 403, 'ERR_FORBIDDEN')
        except Exception:
            import logging
            logging.exception("[api_server] GET request failed for %s", path)
            self._error_json('Internal server error', 500, 'ERR_INTERNAL')

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            self._enforce_request_security(require_json=True)
            body = self._read_json_body()
            if path == '/api/location/resolve':
                city = str(body.get('city') or '').strip()
                city_aliases = {'beijing': '北京', 'shanghai': '上海', 'guangzhou': '广州', 'shenzhen': '深圳'}
                query = city_aliases.get(city.casefold(), city)
                matched = next((name for name in CITY_DB if name.casefold() == query.casefold()), None)
                if not matched:
                    self._error_json('City not found in local city database', 404, 'ERR_CITY_NOT_FOUND')
                else:
                    lat, lon, tz = CITY_DB[matched]
                    self._json({'status': 'local_city_match', 'city': matched, 'lat': lat, 'lon': lon, 'tz': tz})
            elif path == '/api/chart':
                result = self._compute_chart(body)
                self._json(result)
            elif path == '/api/remedies':
                result = self._compute_remedies(body)
                self._json(result)
            elif path == '/api/kp':
                result = self._compute_kp(body)
                self._json(result)
            elif path == '/api/prashna':
                result = self._compute_prashna(body)
                self._json(result)
            elif path == '/api/synastry':
                result = self._compute_synastry(body)
                self._json(result)
            elif path == '/api/dasha':
                result = self._compute_dasha_system(body)
                self._json(result)
            elif path == '/api/dasha/chara':
                result = self._compute_chara_dasha(body)
                self._json(result)
            elif path == '/api/sade_sati':
                result = self._compute_sade_sati(body)
                self._json(result)
            elif path == '/api/pancha_mahapurusha':
                result = self._compute_pmc(body)
                self._json(result)
            elif path == '/api/career':
                result = self._compute_career(body)
                self._json(result)
            elif path == '/api/relationship':
                result = self._compute_relationship(body)
                self._json(result)
            elif path == '/api/vedastro/range_scan':
                result = self._compute_vedastro_range_scan(body)
                self._json(result)
            elif path == '/api/vedastro_gateway/run':
                result = self._compute_vedastro_gateway_run(body)
                self._json(result)
            elif path == '/api/vedastro_gateway/enqueue':
                result = self._compute_vedastro_gateway_enqueue(body)
                self._json(result)
            elif path.startswith('/api/vedastro_gateway/jobs/') and path.endswith('/run'):
                job_id = path.split('/')[-2]
                result = self._compute_vedastro_gateway_run_job(job_id)
                if result is None:
                    self._error_json('Not found', 404, 'ERR_NOT_FOUND')
                else:
                    self._json(result)
            elif path == '/api/professional_reading':
                result = self._compute_professional_reading(body)
                self._json(result)
            elif path == '/api/import_chart':
                result = self._import_chart_text(body)
                self._json(result)
            elif path == '/api/report_artifact':
                result = self._compute_report_artifact(body)
                self._json(result)
            elif path == '/api/oracle_evidence':
                result = self._compute_oracle_evidence(body)
                self._json(result)
            elif path == '/api/annual':
                result = self._compute_annual(body)
                self._json(result)
            elif path == '/api/tajika':
                result = self._compute_tajika(body)
                self._json(result)
            elif path == '/api/muhurta':
                result = self._compute_muhurta(body)
                self._json(result)
            elif path == '/api/panchanga_range':
                result = self._compute_panchanga_range(body)
                self._json(result)
            elif path == '/api/bhava_chalit':
                result = self._compute_bhava_chalit(body)
                self._json(result)
            elif path == '/api/sudarshana':
                result = self._compute_sudarshana(body)
                self._json(result)
            elif path == '/api/nakshatra_full':
                result = self._compute_nakshatra_full(body)
                self._json(result)
            elif path == '/api/varga_full':
                result = self._compute_varga_full(body)
                self._json(result)
            elif path == '/api/jaimini':
                result = self._compute_jaimini(body)
                self._json(result)
            elif path == '/api/ashtakavarga':
                result = self._compute_ashtakavarga(body)
                self._json(result)
            elif path == '/api/shadbala':
                result = self._compute_shadbala(body)
                self._json(result)
            elif path == '/api/yogas':
                result = self._compute_yogas_api(body)
                self._json(result)
            elif path == '/api/aspects':
                result = self._compute_aspects(body)
                self._json(result)
            elif path == '/api/rectification/questionnaire':
                self._json(build_rectification_questionnaire(body))
            elif path == '/api/rectification/sensitivity_scan':
                uncertainty = int(body.get('time_uncertainty_minutes') or 30)
                step_minutes = int(body.get('step_minutes') or (5 if uncertainty > 15 else 1))
                self._json(scan_candidate_times(
                    body,
                    uncertainty_minutes=uncertainty,
                    step_minutes=step_minutes,
                ))
            elif path == '/api/rectification/answers':
                questionnaire = body.get('questionnaire')
                answers = body.get('answers')
                if not isinstance(questionnaire, dict) or not isinstance(answers, dict):
                    raise BadRequest('questionnaire and answers must be JSON objects')
                self._json(score_rectification_answers(questionnaire, answers))
            elif path == '/api/rectification_gate':
                result = self._compute_rectification_gate(body)
                self._json(result)
            elif path == '/api/case_validation':
                result = self._compute_case_validation(body)
                self._json(result)
            elif path == '/api/divisional_yoga':
                result = self._compute_divisional_yoga(body)
                self._json(result)
            elif path == '/api/deep_varga_avastha':
                result = self._compute_deep_varga_avastha(body)
                self._json(result)
            elif path == '/api/kakshya':
                result = self._compute_kakshya(body)
                self._json(result)
            elif path == '/api/bhava_bala':
                result = self._compute_bhava_bala_api(body)
                self._json(result)
            elif path == '/api/transit':
                result = self._compute_transit_triggers(body)
                self._json(result)
            elif path == '/api/thematic_report':
                result = self._compute_thematic_report(body)
                self._json(result)
            elif path == '/api/high_rigor_workflow':
                result = self._compute_high_rigor_workflow(body)
                self._json(result)
            elif path == '/api/consultation_workflow':
                result = self._compute_consultation_workflow(body)
                self._json(result)
            elif path == '/api/technique_example':
                result = self._compute_technique_example(body)
                self._json(result)
            else:
                self._error_json(f'Unknown endpoint: {path}', 404, 'ERR_NOT_FOUND')
        except RateLimited as exc:
            self._error_json(str(exc), 429, 'ERR_RATE_LIMITED')
        except BadRequest as e:
            self._error_json(str(e), 400, 'ERR_BAD_REQUEST')
        except Forbidden as exc:
            self._error_json(str(exc), 403, 'ERR_FORBIDDEN')
        except UnsupportedMediaType as exc:
            self._error_json(str(exc), 415, 'ERR_UNSUPPORTED_MEDIA_TYPE')
        except JobQueueFull as exc:
            self._error_json(str(exc), 503, 'ERR_JOB_QUEUE_FULL')
        except Exception:
            import logging
            logging.exception("[api_server] request failed for %s", path)
            self._error_json('Internal server error', 500, 'ERR_INTERNAL')

    def _read_json_body(self):
        raw_length = self.headers.get('Content-Length', '0')
        try:
            length = int(raw_length)
        except ValueError as e:
            raise BadRequest('Invalid Content-Length') from e
        if length < 0:
            raise BadRequest('Invalid Content-Length')
        if length > MAX_REQUEST_BYTES:
            raise BadRequest(f'Request body too large; max {MAX_REQUEST_BYTES} bytes')
        if length == 0:
            return {}
        try:
            body = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as e:
            raise BadRequest('Invalid JSON body') from e
        if not isinstance(body, dict):
            raise BadRequest('JSON body must be an object')
        return body

    def _get_int(self, body, key, default, min_value=None, max_value=None):
        value = body.get(key, default)
        try:
            number = int(value)
        except (TypeError, ValueError) as e:
            raise BadRequest(f'{key} must be an integer') from e
        self._check_range(key, number, min_value, max_value)
        return number


    def _parse_timezone(self, body, lat, lon, year, month, day, hour, minute, second):
        tz = body.get('tz')
        if tz is not None and tz != "":
            return self._get_float(body, 'tz', 8, -14, 14)
        from datetime import datetime
        try:
            dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
        except (TypeError, ValueError) as exc:
            raise BadRequest('Invalid birth date') from exc
        try:
            calculation_service = _load_local_module('domain_calculation_service')
            return calculation_service.infer_timezone_offset(
                lat=lat,
                lon=lon,
                local_datetime=dt,
            )
        except ValueError as exc:
            raise BadRequest(str(exc)) from exc

    def _get_float(self, body, key, default, min_value=None, max_value=None):
        value = body.get(key, default)
        try:
            number = float(value)
        except (TypeError, ValueError) as e:
            raise BadRequest(f'{key} must be a number') from e
        if not math.isfinite(number):
            raise BadRequest(f'{key} must be finite')
        self._check_range(key, number, min_value, max_value)
        return number

    def _check_range(self, key, number, min_value, max_value):
        if min_value is not None and number < min_value:
            raise BadRequest(f'{key} must be >= {min_value}')
        if max_value is not None and number > max_value:
            raise BadRequest(f'{key} must be <= {max_value}')

    def _validate_planets(self, planets):
        if not isinstance(planets, dict):
            raise BadRequest('planets must be an object')
        return planets

    def _normalize_degree(self, body, key, default):
        return self._get_float(body, key, default, 0, 360) % 360

    def _get_birth_second(self, body, default=0.0):
        return self._get_float(body, 'second', body.get('birth_second', default), 0, 59)

    def _birth_hour_decimal(self, hour, minute, second=0.0):
        return float(hour) + float(minute) / 60.0 + float(second) / 3600.0

    def _format_birth_time(self, hour, minute, second=0.0):
        second_int = int(float(second))
        base = f'{int(hour):02d}:{int(minute):02d}'
        return f'{base}:{second_int:02d}' if second_int else base

    def _safe_report_slug(self, value):
        slug = re.sub(r'[^a-zA-Z0-9._-]+', '-', str(value or 'jyotish-report')).strip('-._')
        return (slug[:80] or 'jyotish-report')

    def _validate_report_html(self, html):
        if not isinstance(html, str) or not html.strip():
            raise BadRequest('html must be a non-empty string')
        if len(html) > MAX_REPORT_HTML_CHARS:
            raise BadRequest(f'html too large; max {MAX_REPORT_HTML_CHARS} characters')
        active_patterns = [
            r'<\s*script\b',
            r'<\s*iframe\b',
            r'<\s*object\b',
            r'<\s*embed\b',
            r'\son[a-z]+\s*=',
            r'javascript\s*:',
        ]
        if any(re.search(pattern, html, re.IGNORECASE) for pattern in active_patterns):
            raise BadRequest('report html cannot include active content')
        return html

    def _inject_functional_benefic_malefic_summary(self, html, snapshot):
        if not isinstance(snapshot, dict):
            return html
        if snapshot.get('status') in {None, 'blocked', 'not_used'}:
            return html
        benefics = snapshot.get('functional_benefics')
        malefics = snapshot.get('functional_malefics')
        if not isinstance(benefics, list) or not isinstance(malefics, list):
            return html
        neutrals = snapshot.get('functional_neutrals') if isinstance(snapshot.get('functional_neutrals'), list) else []
        yogakarakas = snapshot.get('yogakarakas') if isinstance(snapshot.get('yogakarakas'), list) else []

        def _escape(value):
            return html_lib.escape(str(value or ''))

        ascendant = _escape(snapshot.get('ascendant') or snapshot.get('asc_sign') or 'Unknown')
        benefic_text = _escape(', '.join(str(item) for item in benefics) or 'None')
        malefic_text = _escape(', '.join(str(item) for item in malefics) or 'None')
        neutral_text = _escape(', '.join(str(item) for item in neutrals) or 'None')
        yogakaraka_text = _escape(', '.join(str(item) for item in yogakarakas) or 'None')
        confidence_text = _escape(snapshot.get('effect_on_confidence') or 'Functional role layer was used in the final judgement.')
        source_text = _escape(snapshot.get('source') or 'strict_functional_benefic_malefic_v1')

        summary = (
            '<section data-functional-role-summary="true" '
            'style="margin:24px 0;padding:16px;border:1px solid #d9dde8;border-radius:8px;'
            'background:#f7f9fc;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;">'
            '<h2 style="margin:0 0 12px;font-size:20px;">Functional Benefic/Malefic</h2>'
            f'<p style="margin:0 0 8px;"><strong>Ascendant:</strong> {ascendant}</p>'
            f'<p style="margin:0 0 8px;"><strong>Functional Benefics:</strong> {benefic_text}</p>'
            f'<p style="margin:0 0 8px;"><strong>Functional Malefics:</strong> {malefic_text}</p>'
            f'<p style="margin:0 0 8px;"><strong>Functional Neutrals:</strong> {neutral_text}</p>'
            f'<p style="margin:0 0 8px;"><strong>Yogakarakas:</strong> {yogakaraka_text}</p>'
            f'<p style="margin:0 0 8px;"><strong>Confidence Impact:</strong> {confidence_text}</p>'
            f'<p style="margin:0;color:#5b6472;font-size:13px;"><strong>Source:</strong> {source_text}</p>'
            '</section>'
        )
        body_close = re.search(r'</body\s*>', html, re.IGNORECASE)
        if body_close:
            return html[:body_close.start()] + summary + html[body_close.start():]
        return html + summary

    def _inject_vimsopaka_semantic_summary(self, html, snapshot):
        if not isinstance(snapshot, dict):
            return html
        if snapshot.get('status') in {None, 'blocked'}:
            return html
        highlights = snapshot.get('highlights') if isinstance(snapshot.get('highlights'), list) else []
        warnings = snapshot.get('warnings') if isinstance(snapshot.get('warnings'), list) else []
        if not highlights and not warnings:
            return html

        def _escape(value):
            return html_lib.escape(str(value or ''))

        def _line_items(items):
            return ''.join(f'<li>{_escape(item)}</li>' for item in items) or '<li>None</li>'

        summary = (
            '<section data-vimsopaka-semantic-summary="true" '
            'style="margin:24px 0;padding:16px;border:1px solid #d9dde8;border-radius:8px;'
            'background:#f7f9fc;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;">'
            '<h2 style="margin:0 0 12px;font-size:20px;">Vimsopaka Semantic Summary</h2>'
            f'<p style="margin:0 0 8px;"><strong>Status:</strong> {_escape(snapshot.get("status"))}</p>'
            '<p style="margin:0 0 8px;"><strong>Highlights:</strong></p>'
            f'<ul style="margin:0 0 8px 18px;padding:0;">{_line_items(highlights)}</ul>'
            '<p style="margin:0 0 8px;"><strong>Warnings:</strong></p>'
            f'<ul style="margin:0 0 8px 18px;padding:0;">{_line_items(warnings)}</ul>'
            '</section>'
        )
        body_close = re.search(r'</body\s*>', html, re.IGNORECASE)
        if body_close:
            return html[:body_close.start()] + summary + html[body_close.start():]
        return html + summary

    def _inject_relationship_narrative_summary(self, html, narrative):
        if not isinstance(narrative, dict):
            return html
        headline = narrative.get('headline')
        if not headline:
            return html

        def _escape(value):
            return html_lib.escape(str(value or ''))

        def _list_html(items):
            if not isinstance(items, list) or not items:
                return '<li>暂无补充。</li>'
            return ''.join(f'<li>{_escape(item)}</li>' for item in items[:6])

        risks = narrative.get("risks")
        boundaries = narrative.get("boundaries")
        caution_block = ''
        if (
            isinstance(risks, list)
            and any('不能误读成接近结婚' in str(item) for item in risks)
        ) or (
            isinstance(boundaries, list)
            and any('不等于法律婚姻' in str(item) for item in boundaries)
        ):
            caution_block = (
                '<div class="relationship-caution" '
                'style="margin:12px 0 16px;padding:12px 14px;border:1px solid #f3d19c;'
                'border-left:4px solid #c67a00;border-radius:8px;background:#fff8ed;color:#7a4b00;">'
                '<strong style="display:block;margin:0 0 6px;">Caution</strong>'
                '<span style="display:block;font-size:13px;line-height:1.6;">'
                '当前公开化/关系可见度候选不能被误读成接近法律婚姻；若 core marriage promise、dual dasha 或 external timing 仍未收敛，'
                '必须继续降置信度并保持 context-only 解释。'
                '</span>'
                '</div>'
            )

        summary = (
            '<section data-relationship-strict-narrative="true" '
            'style="margin:24px 0;padding:16px;border:1px solid #d9dde8;border-radius:8px;'
            'background:#fbfcff;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;">'
            '<h2 style="margin:0 0 12px;font-size:20px;">Relationship Strict Narrative</h2>'
            f'<p style="margin:0 0 12px;">{_escape(headline)}</p>'
            f'{caution_block}'
            '<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;">'
            '<div><strong>Strengths</strong><ul style="margin:8px 0 0 18px;padding:0;">'
            f'{_list_html(narrative.get("strengths"))}</ul></div>'
            '<div><strong>Risks</strong><ul style="margin:8px 0 0 18px;padding:0;">'
            f'{_list_html(narrative.get("risks"))}</ul></div>'
            '<div><strong>Boundaries</strong><ul style="margin:8px 0 0 18px;padding:0;">'
            f'{_list_html(narrative.get("boundaries"))}</ul></div>'
            '</div>'
            '</section>'
        )
        body_close = re.search(r'</body\s*>', html, re.IGNORECASE)
        if body_close:
            return html[:body_close.start()] + summary + html[body_close.start():]
        return html + summary

    def _inject_generic_strict_narrative_summary(self, html, narrative, *, title, section_key, subtitle):
        if not isinstance(narrative, dict):
            return html
        headline = narrative.get('headline')
        if not headline:
            return html

        def _escape(value):
            return html_lib.escape(str(value or ''))

        def _list_html(items):
            if not isinstance(items, list) or not items:
                return '<li>暂无补充。</li>'
            return ''.join(f'<li>{_escape(item)}</li>' for item in items[:6])

        summary = (
            f'<section data-{section_key}="true" '
            'style="margin:24px 0;padding:16px;border:1px solid #d9dde8;border-radius:8px;'
            'background:#fbfcff;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;">'
            f'<h2 style="margin:0 0 12px;font-size:20px;">{_escape(title)}</h2>'
            f'<p style="margin:0 0 8px;font-size:13px;color:#5b6472;">{_escape(subtitle)}</p>'
            f'<p style="margin:0 0 12px;">{_escape(headline)}</p>'
            '<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;">'
            '<div><strong>Strengths</strong><ul style="margin:8px 0 0 18px;padding:0;">'
            f'{_list_html(narrative.get("strengths"))}</ul></div>'
            '<div><strong>Risks</strong><ul style="margin:8px 0 0 18px;padding:0;">'
            f'{_list_html(narrative.get("risks"))}</ul></div>'
            '<div><strong>Boundaries</strong><ul style="margin:8px 0 0 18px;padding:0;">'
            f'{_list_html(narrative.get("boundaries"))}</ul></div>'
            '</div>'
            '</section>'
        )
        body_close = re.search(r'</body\s*>', html, re.IGNORECASE)
        if body_close:
            return html[:body_close.start()] + summary + html[body_close.start():]
        return html + summary

    def _inject_vedastro_overview_summary(self, html, overview):
        if not isinstance(overview, dict):
            return html
        if not overview.get('status'):
            return html

        def _escape(value):
            return html_lib.escape(str(value or ''))

        domain_statuses = overview.get('domain_statuses') if isinstance(overview.get('domain_statuses'), dict) else {}
        top_events = overview.get('top_events_by_domain') if isinstance(overview.get('top_events_by_domain'), dict) else {}
        domain_lines = ''.join(
            f'<li><strong>{_escape(domain)}:</strong> {_escape(status)}</li>'
            for domain, status in domain_statuses.items()
        ) or '<li>None</li>'
        top_event_lines = ''.join(
            f'<li><strong>{_escape(domain)}:</strong> {_escape((payload or {}).get("signal_label") or (payload or {}).get("event_id") or "-")} · {_escape((payload or {}).get("start") or "-")}</li>'
            for domain, payload in top_events.items()
            if isinstance(payload, dict)
        ) or '<li>None</li>'

        summary = (
            '<section data-vedastro-overview-summary="true" '
            'style="margin:24px 0;padding:16px;border:1px solid #d9dde8;border-radius:8px;'
            'background:#f7f9fc;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;">'
            '<h2 style="margin:0 0 12px;font-size:20px;">VedAstro External Overview</h2>'
            f'<p style="margin:0 0 8px;"><strong>Status:</strong> {_escape(overview.get("status"))}</p>'
            f'<p style="margin:0 0 8px;"><strong>Ingestion Profile:</strong> {_escape(overview.get("ingestion_profile"))}</p>'
            f'<p style="margin:0 0 8px;"><strong>Search Scope:</strong> {_escape(overview.get("search_scope"))}</p>'
            f'<p style="margin:0 0 8px;"><strong>Reference Date:</strong> {_escape(overview.get("reference_date"))}</p>'
            f'<p style="margin:0 0 8px;"><strong>Event Count:</strong> {_escape(overview.get("event_count"))}</p>'
            '<p style="margin:0 0 8px;"><strong>Domain Statuses:</strong></p>'
            f'<ul style="margin:0 0 8px 18px;padding:0;">{domain_lines}</ul>'
            '<p style="margin:0 0 8px;"><strong>Top Events By Domain:</strong></p>'
            f'<ul style="margin:0 0 8px 18px;padding:0;">{top_event_lines}</ul>'
            f'<p style="margin:0;color:#5b6472;font-size:13px;"><strong>Boundary:</strong> {_escape(overview.get("boundary_note"))}</p>'
            '</section>'
        )
        body_close = re.search(r'</body\s*>', html, re.IGNORECASE)
        if body_close:
            return html[:body_close.start()] + summary + html[body_close.start():]
        return html + summary

    def _artifact_base64(self, path):
        size = os.path.getsize(path)
        if size > MAX_REPORT_BASE64_BYTES:
            return None
        with open(path, 'rb') as fh:
            return base64.b64encode(fh.read()).decode('ascii')

    def _compute_vedastro_range_scan(self, body):
        ui_domain = str(body.get('domain') or 'career').strip().lower()
        domain_map = {
            'career': 'career',
            'relationship': 'marriage',
            'marriage': 'marriage',
            'finance': 'wealth',
            'wealth': 'wealth',
        }
        if ui_domain not in domain_map:
            raise BadRequest('domain must be career, relationship, marriage, finance, or wealth')
        start_date = str(body.get('start_date') or '').strip()
        end_date = str(body.get('end_date') or '').strip()
        if not start_date or not end_date:
            raise BadRequest('start_date and end_date are required')
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError as e:
            raise BadRequest('start_date and end_date must be YYYY-MM-DD') from e
        if end_dt < start_dt:
            raise BadRequest('end_date must be on or after start_date')

        year = self._get_int(body, 'year', None, 1800, 2400)
        month = self._get_int(body, 'month', None, 1, 12)
        day = self._get_int(body, 'day', None, 1, 31)
        hour = self._get_float(body, 'hour', 12, 0, 23)
        minute = self._get_float(body, 'minute', 0, 0, 59)
        second = self._get_birth_second(body)
        lat = self._get_float(body, 'lat', 0, -90, 90)
        lon = self._get_float(body, 'lon', 0, -180, 180)
        tz = self._parse_timezone(body, lat, lon, year, month, day, hour, minute, second)
        try:
            datetime(year, month, day, int(hour), int(minute), int(second))
        except ValueError as e:
            raise BadRequest('Invalid birth date') from e

        adapter_domain = domain_map[ui_domain]
        case = {
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'minute': minute,
            'second': second,
            'lat': lat,
            'lon': lon,
            'tz': tz,
            'ayanamsa_policy': body.get('ayanamsa_policy') or body.get('ayanamsa') or 'lahiri',
            'node_policy': body.get('node_policy') or body.get('node_mode') or 'mean',
        }
        result = _load_local_module('vedastro_service_adapter').run_range_scan_for_case(
            case,
            adapter_domain,
            start_date,
            end_date,
            case_id=str(body.get('case_id') or 'user_chart'),
        )
        return {
            'success': True,
            'endpoint': 'vedastro_range_scan',
            'ui_domain': ui_domain,
            'adapter_domain': adapter_domain,
            'result': result,
            'boundary': 'VedAstro range scan is optional external timing evidence; local Jyotish gates remain authoritative.',
        }

    def _compute_oracle_evidence(self, body):
        packet = body.get('packet')
        if not isinstance(packet, dict):
            raise BadRequest('packet must be an object')
        case_id = packet.get('case_id')
        if not case_id:
            raise BadRequest('packet.case_id is required')

        collection_queue = _load_local_module('oracle_collection_queue')
        evidence_validator = _load_local_module('oracle_evidence_validator')
        target = packet.get('target') if isinstance(packet.get('target'), dict) else {}
        target_fields = collection_queue._target_fields(target)
        status = packet.get('status') or packet.get('evidence_packet', {}).get('status') or 'draft'
        evidence_packet = packet.get('evidence_packet') if isinstance(packet.get('evidence_packet'), dict) else {}
        metadata = evidence_packet.get('metadata') if isinstance(evidence_packet.get('metadata'), dict) else {}
        task = {
            'task_id': f'uploaded_{case_id}',
            'case_id': case_id,
            'status': status,
            'target_fields': target_fields,
            'missing_target_fields': collection_queue._missing_target_fields(target),
            'evidence_packet': {
                'capture_id': evidence_packet.get('capture_id') or f'uploaded_{case_id}',
                'status': evidence_packet.get('status') or status,
                'case_id': case_id,
                'required_metadata_fields': collection_queue.REQUIRED_EVIDENCE_METADATA_FIELDS,
                'metadata': metadata,
                'target_placeholders': {
                    field: collection_queue._target_value(target, field)
                    for field in target_fields
                },
                'integrity_checks': {
                    'must_not_come_from_local_engine': True,
                    'requires_external_artifact': True,
                    'requires_status_external_verified_before_calibration': True,
                    'reject_global_shadbala_scaling': 'target.shadbala_components' in target_fields,
                },
                'promotion_status_after_fill': 'external_verified',
            },
        }
        report = evidence_validator.build_report({
            'scope': 'uploaded_oracle_evidence_packet',
            'schema_version': 1,
            'tasks': [task],
        })
        return {
            'success': True,
            'endpoint': 'oracle_evidence',
            'scope': report['scope'],
            'report': report,
            'summary': report['summary'],
            'packets': report['packets'],
            'boundary': report['boundary'],
        }

    def _compute_report_artifact(self, body):
        html = self._validate_report_html(body.get('html'))
        html = self._inject_functional_benefic_malefic_summary(
            html,
            body.get('functional_benefic_malefic'),
        )
        html = self._inject_vimsopaka_semantic_summary(
            html,
            body.get('vimsopaka_semantic_summary'),
        )
        html = self._inject_relationship_narrative_summary(
            html,
            body.get('relationship_narrative'),
        )
        html = self._inject_generic_strict_narrative_summary(
            html,
            body.get('career_narrative'),
            title='Career Strict Narrative',
            section_key='career-strict-narrative',
            subtitle='事业严格裁决正文，要求显式引用月度主状态、落地形式、阻力来源与时间置信度。',
        )
        html = self._inject_generic_strict_narrative_summary(
            html,
            body.get('finance_narrative'),
            title='Finance Strict Narrative',
            section_key='finance-strict-narrative',
            subtitle='财富严格裁决正文，要求显式区分收入兑现、现金流动作、摩擦来源与时间边界。',
        )
        html = self._inject_vedastro_overview_summary(
            html,
            body.get('vedastro_overview'),
        )
        fmt = body.get('format', 'html')
        if fmt not in {'html', 'pdf'}:
            raise BadRequest('format must be html or pdf')
        slug = self._safe_report_slug(body.get('name') or body.get('filename'))
        stamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S-%f')
        os.makedirs(REPORT_ARTIFACT_DIR, exist_ok=True)
        html_filename = f'{slug}-{stamp}.html'
        html_path = os.path.join(REPORT_ARTIFACT_DIR, html_filename)
        with open(html_path, 'w', encoding='utf-8') as fh:
            fh.write(html)

        result = {
            'success': True,
            'endpoint': 'report_artifact',
            'format': fmt,
            'html_filename': html_filename,
            'html_path': html_path,
            'html_size_kb': round(os.path.getsize(html_path) / 1024, 1),
            'html_base64': self._artifact_base64(html_path),
            'mime': 'text/html;charset=utf-8',
            'source': 'scripts/report_builder.py',
            'artifact_status': 'html_ready',
            'primary_artifact': 'html',
            'download_filename': html_filename,
            'download_mime': 'text/html;charset=utf-8',
            'fallback_reason': None,
            'user_message': 'HTML report artifact generated.',
            'next_action': 'Open the downloaded HTML file directly, or print it to PDF from the browser.',
            'delivery': {
                'artifact_status': 'html_ready',
                'format': 'html',
                'filename': html_filename,
                'mime': 'text/html;charset=utf-8',
                'fallback': False,
                'user_message': 'HTML report artifact generated.',
                'next_action': 'Open the downloaded HTML file directly, or print it to PDF from the browser.',
            },
        }
        if fmt == 'pdf':
            pdf_filename = f'{slug}-{stamp}.pdf'
            pdf_path = os.path.join(REPORT_ARTIFACT_DIR, pdf_filename)
            try:
                ok = _load_local_module('report_builder')._html_to_pdf(html_path, pdf_path)
            except Exception as exc:
                ok = False
                result['pdf_error'] = str(exc)
            result.update({
                'pdf_available': bool(ok and os.path.exists(pdf_path)),
                'pdf_filename': pdf_filename,
                'pdf_path': pdf_path if os.path.exists(pdf_path) else None,
            })
            if result['pdf_available']:
                result.update({
                    'format': 'pdf',
                    'mime': 'application/pdf',
                    'pdf_size_kb': round(os.path.getsize(pdf_path) / 1024, 1),
                    'pdf_base64': self._artifact_base64(pdf_path),
                    'artifact_status': 'pdf_ready',
                    'primary_artifact': 'pdf',
                    'download_filename': pdf_filename,
                    'download_mime': 'application/pdf',
                    'fallback_reason': None,
                    'user_message': 'PDF report artifact generated.',
                    'next_action': 'Open the downloaded PDF file for reading, printing, or archiving.',
                    'delivery': {
                        'artifact_status': 'pdf_ready',
                        'format': 'pdf',
                        'filename': pdf_filename,
                        'mime': 'application/pdf',
                        'fallback': False,
                        'user_message': 'PDF report artifact generated.',
                        'next_action': 'Open the downloaded PDF file for reading, printing, or archiving.',
                    },
                })
            else:
                result['fallback'] = 'html'
                result['message'] = 'PDF renderer unavailable; HTML artifact generated as fallback.'
                result['fallback_reason'] = result.get('pdf_error') or 'PDF renderer unavailable'
                result['artifact_status'] = 'pdf_fallback_html_ready'
                result['primary_artifact'] = 'html'
                result['download_filename'] = html_filename
                result['download_mime'] = 'text/html;charset=utf-8'
                result['user_message'] = 'PDF renderer unavailable; HTML report artifact generated as fallback.'
                result['next_action'] = 'Open the downloaded HTML file directly, or print it to PDF from the browser.'
                result['delivery'] = {
                    'artifact_status': 'pdf_fallback_html_ready',
                    'format': 'html',
                    'filename': html_filename,
                    'mime': 'text/html;charset=utf-8',
                    'fallback': True,
                    'fallback_reason': result['fallback_reason'],
                    'user_message': result['user_message'],
                    'next_action': result['next_action'],
                }
        return result

    def _compute_thematic_report(self, body):
        report_orchestrator = _load_local_module('report_orchestrator')
        reading_orchestrator = _load_local_module('reading_orchestrator')
        orchestrator_bridge = _load_local_module('orchestrator_bridge')
        chart_data = body.get('chart_data') if isinstance(body.get('chart_data'), dict) else body
        upstream_contract = body.get('upstream_contract') if isinstance(body.get('upstream_contract'), dict) else {}

        custom_evidence = body.get('evidence')
        has_custom_evidence = isinstance(custom_evidence, dict) and bool(custom_evidence)
        derived_context = None
        strict_workflow_contracts = upstream_contract.get('strict_workflow_contracts') if isinstance(upstream_contract.get('strict_workflow_contracts'), dict) else {}
        upstream_guided_topics = upstream_contract.get('guided_topics') if isinstance(upstream_contract.get('guided_topics'), list) else []
        if not has_custom_evidence and not strict_workflow_contracts and self._can_derive_thematic_evidence(chart_data):
            derived_context = self._derive_thematic_evidence(chart_data, report_orchestrator)

        if derived_context:
            chart = self._build_thematic_chart_data(derived_context.get('chart_data', chart_data), report_orchestrator)
        else:
            chart = self._build_thematic_chart_data(chart_data, report_orchestrator)
        orchestrator = report_orchestrator.ThematicReportOrchestrator(chart)

        if has_custom_evidence:
            self._inject_thematic_evidence(orchestrator, custom_evidence, report_orchestrator)
            mode = 'custom_evidence'
        elif derived_context and derived_context.get('evidence'):
            self._inject_thematic_evidence(orchestrator, derived_context['evidence'], report_orchestrator)
            mode = 'derived_chart_evidence'
        elif strict_workflow_contracts:
            mode = 'upstream_contract_reuse'
        else:
            self._inject_sample_thematic_evidence(orchestrator, report_orchestrator)
            mode = 'sample_evidence'

        theme_values = self._requested_thematic_report_themes(body, report_orchestrator)
        reports = {}
        for theme in theme_values:
            report = orchestrator.generate_report(theme)
            reports[theme.value] = self._apply_monthly_adjudication_to_theme_report(
                theme.value,
                report.to_dict(),
            )

        return {
            'success': True,
            'endpoint': 'thematic_report',
            'source': 'scripts/report_orchestrator.py',
            'fragment_sources': [
                'report_orchestrator.py',
                'reading_orchestrator.py',
                'orchestrator_bridge.py',
            ],
            'workflow_orchestration': self._thematic_workflow_status(
                reading_orchestrator,
                orchestrator_bridge,
                report_orchestrator,
                theme_values,
            ),
            'mode': mode,
            'evidence_source': (
                {
                    'mode': 'upstream_contract_reuse',
                    'source': 'consultation_workflow_upstream_contract',
                    'sample_fallback': False,
                    'strict_workflow_routes_available': list(strict_workflow_contracts.keys()),
                    'guided_topic_count': len(upstream_guided_topics),
                }
                if mode == 'upstream_contract_reuse'
                else self._thematic_evidence_source(mode, derived_context, has_custom_evidence)
            ),
            'themes': reports,
            'theme_count': len(reports),
            'available_themes': [theme.value for theme in report_orchestrator.ThemeName],
            'boundary': '主题化报告用于组织证据、裁决冲突和生成叙事；具体预测仍需本命承诺、Dasha、Transit 与案例验证共同收敛。',
        }

    def _compute_high_rigor_workflow(self, body):
        if body.get('async') or body.get('enqueue'):
            return self._enqueue_high_rigor_job(body)
        return self._compute_consultation_workflow({
            **dict(body or {}),
            'surface': 'api_web',
            'return_high_rigor_shape': True,
        })

    def _compute_consultation_workflow(self, body):
        return execute_consultation_workflow(
            self,
            body=dict(body or {}),
            surface=body.get('surface', 'api_web'),
        )

    def _build_audited_remedies_from_guided_topics(self, guided_topics):
        if not isinstance(guided_topics, list):
            return {'status': 'blocked', 'reason': 'guided_topics_missing'}
        selected_gate = None
        selected_topic = None
        for topic in guided_topics:
            if not isinstance(topic, dict):
                continue
            gate = topic.get('strict_audit_gate')
            if isinstance(gate, dict):
                selected_gate = gate
                selected_topic = topic
                break
        if not isinstance(selected_gate, dict):
            return {'status': 'blocked', 'reason': 'strict_audit_gate_missing'}
        strength_context = selected_gate.get('strength_context') if isinstance(selected_gate.get('strength_context'), dict) else {}
        dosha_context = selected_gate.get('dosha_context') if isinstance(selected_gate.get('dosha_context'), list) else []
        active_dasha_lord = selected_gate.get('active_dasha_lord') if isinstance(selected_gate.get('active_dasha_lord'), str) else ''
        if not strength_context:
            return {'status': 'blocked', 'reason': 'strength_context_missing', 'source': 'strict_audit_gate'}
        payload = self._compute_remedies({
            'shadbala': strength_context,
            'doshas': dosha_context,
            'dasha_lord': active_dasha_lord,
        })
        if not isinstance(payload, dict):
            payload = {'recommendations': payload}
        return {
            'status': 'ok',
            'source': 'strict_audit_gate',
            'topic': (
                selected_gate.get('topic')
                or selected_topic.get('id')
                or selected_topic.get('title')
                or 'general'
            ),
            'active_dasha_lord': active_dasha_lord,
            'recommendations': payload.get('recommendations') or payload,
            'raw': payload,
        }

    def _compute_high_rigor_workflow_sync(self, body):
        body_copy = dict(body or {})
        body_copy.pop('async', None)
        body_copy.pop('enqueue', None)
        return self._compute_high_rigor_workflow(body_copy)

    def _compute_vedastro_gateway_status(self):
        from scripts.vedastro_gateway import gateway_status

        return gateway_status()

    def _compute_vedastro_gateway_archives(self):
        from scripts.vedastro_gateway import list_official_raw_response_archives

        return list_official_raw_response_archives()

    def _compute_vedastro_gateway_job(self, job_id):
        from scripts.vedastro_gateway import get_gateway_job

        return get_gateway_job(str(job_id))

    def _compute_vedastro_gateway_enqueue(self, body):
        from scripts.vedastro_gateway import enqueue_gateway_job

        payload = dict(body or {})
        birth_payload = self._high_rigor_birth_payload(payload)
        themes = self._high_rigor_requested_themes(payload)
        reference_date = (
            payload.get('reference_date')
            or payload.get('transit_date')
            or payload.get('today')
            or payload.get('current_date')
            or datetime.now().strftime('%Y-%m-%d')
        )
        return enqueue_gateway_job(
            birth_payload,
            question=str(payload.get('question') or payload.get('query') or ''),
            themes=themes,
            reference_date=str(reference_date),
        )

    def _compute_vedastro_gateway_run_job(self, job_id):
        from scripts.vedastro_gateway import run_gateway_job

        return run_gateway_job(str(job_id))

    def _compute_vedastro_gateway_run(self, body):
        from scripts.vedastro_gateway import run_gateway_packet

        payload = dict(body or {})
        birth_payload = self._high_rigor_birth_payload(payload)
        themes = self._high_rigor_requested_themes(payload)
        reference_date = (
            payload.get('reference_date')
            or payload.get('transit_date')
            or payload.get('today')
            or payload.get('current_date')
            or datetime.now().strftime('%Y-%m-%d')
        )
        return run_gateway_packet(
            birth_payload,
            question=str(payload.get('question') or payload.get('query') or ''),
            themes=themes,
            reference_date=str(reference_date),
        )

    def _compute_professional_reading(self, body):
        payload = dict(body or {})
        high_rigor_payload = {
            **payload,
            'surface': payload.get('surface') or 'professional_reading_web',
            'return_high_rigor_shape': True,
        }
        high_rigor_payload.pop('async', None)
        high_rigor_payload.pop('enqueue', None)
        high_rigor = self._compute_high_rigor_workflow(high_rigor_payload)
        gateway = self._compute_vedastro_gateway_run(payload)
        return {
            'success': True,
            'endpoint': 'professional_reading',
            'schema_version': 1,
            'professional_reading': {
                'input': {
                    'question': payload.get('question') or payload.get('query') or '',
                    'themes': self._high_rigor_requested_themes(payload),
                    'blind_mode': bool(payload.get('blind_mode')),
                    'reference_date': payload.get('reference_date')
                    or payload.get('transit_date')
                    or payload.get('today')
                    or payload.get('current_date'),
                },
                'high_rigor_workflow': high_rigor,
                'vedastro_gateway': gateway,
                'technique_audit_table_required_rows': [
                    'Functional Benefic/Malefic',
                    'MEVG / Global Web Evidence',
                    'Real Case Calibration',
                    'VedAstro Gateway Boundary',
                    'VedAstro Raw Archive Manifest',
                ],
                'visibility_contract': {
                    'requires_technique_audit_table': True,
                    'requires_source_governance': True,
                    'requires_confidence_boundary': True,
                    'requires_user_visible_blocked_reasons': True,
                },
                'user_led_calibration_controls': {
                    'blind_mode': bool(payload.get('blind_mode')),
                    'disable_life_event_feedback': bool(payload.get('disable_life_event_feedback') or payload.get('blind_mode')),
                    'allow_user_event_selection': bool(payload.get('allow_user_event_selection', True)),
                    'note': 'User feedback must stay explicit and option-based; do not infer from prior chat memory in blind mode.',
                },
            },
        }

    def _high_rigor_workflow_plan_only(self, birth_payload, themes, events):
        return {
            'success': True,
            'endpoint': 'high_rigor_workflow',
            'mode': 'plan_only_no_external_calls',
            'routes': ['career', 'relationship', 'finance'],
            'themes': themes,
            'event_count': len(events),
            'source_priority': {
                'mode': 'vedastro_official_snapshot_first',
                'priority': [
                    'vedastro_official_snapshot',
                    'local_supplemental_modules',
                    'local_fallback_only_when_official_blocked',
                ],
            },
            'reused_modules': [
                'vedastro_evidence_orchestrator',
                'birth_time_rectifier',
                'historical_event_backtest',
                'report_orchestrator',
                'reading_orchestrator',
                'orchestrator_bridge',
            ],
            'execution_plan': [
                'compute_chart_with_vedastro_main_entry_overview',
                'run_rectification_gate',
                'run_historical_event_backtest_when_events_exist',
                'generate_thematic_report_for_selected_themes',
                'return_official_primary_supplemental_fallback_conflict_contract',
            ],
            'contract': {
                'official_primary_evidence': {},
                'local_supplemental_evidence': {},
                'fallback_used': [],
                'blocked_items': [],
                'conflicts': [],
            },
            'execution_strategy': {
                'chart_path': {
                    'mode': 'sync_chart_response_cache',
                    'cache_scope': _API_CHART_CACHE_SCOPE,
                    'cache_ttl_seconds': _api_chart_cache_ttl_seconds(),
                    'note': '普通 chart 入口优先复用 API 级最终结果缓存，避免重复拉取官方快照与 prompt pack。',
                },
                'queue_recommendation': {
                    'recommended': True,
                    'lane': 'high_rigor_workflow',
                    'reason': '高严谨链路会叠加 rectification/backtest/thematic report，适合后续进入异步/队列层，而不是始终阻塞同步用户请求。',
                },
            },
            'boundary': 'Plan-only mode is used by API Explorer samples to avoid accidental heavy VedAstro calls. Remove dry_run/plan_only to execute the full workflow and return the official-primary evidence contract.',
        }

    def _enqueue_high_rigor_job(self, body):
        identity = _new_async_job_identity('hrw')
        job_id = identity['job_id']
        queued_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        poll_path = f'/api/high_rigor_workflow/jobs/{job_id}'
        record = {
            'success': True,
            'endpoint': 'high_rigor_workflow_async',
            'mode': 'async_submitted',
            'job_id': job_id,
            'status': 'queued',
            'queued_at': queued_at,
            'poll_path': poll_path,
            'scope': _HIGH_RIGOR_JOB_SCOPE,
            'access_token': identity['access_token'],
            'expires_at_unix': time.time() + _async_job_ttl_seconds(),
        }
        stored_record = dict(record)
        stored_record.pop('access_token')
        stored_record['access_token_hash'] = _access_token_hash(identity['access_token'])
        _write_high_rigor_job_record(job_id, stored_record)

        body_copy = dict(body or {})

        def _run_job() -> None:
            running = dict(stored_record)
            running['status'] = 'running'
            running['started_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            _write_high_rigor_job_record(job_id, running)
            try:
                result = self._compute_high_rigor_workflow_sync(body_copy)
                completed = dict(running)
                completed['status'] = 'completed'
                completed['completed_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                completed['mode'] = 'async_result'
                completed['result'] = result
                _write_high_rigor_job_record(job_id, completed)
            except Exception as exc:
                failed = dict(running)
                failed['status'] = 'failed'
                failed['completed_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                failed['mode'] = 'async_result'
                failed['error'] = str(exc)
                _write_high_rigor_job_record(job_id, failed)

        _submit_background_job(_run_job)
        return record

    def _enqueue_async_job(self, *, scope, endpoint, job_prefix, poll_base, compute_fn):
        identity = _new_async_job_identity(job_prefix)
        job_id = identity['job_id']
        queued_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        poll_path = f'{poll_base}/{job_id}'
        record = {
            'success': True,
            'endpoint': endpoint,
            'mode': 'async_submitted',
            'job_id': job_id,
            'status': 'queued',
            'queued_at': queued_at,
            'poll_path': poll_path,
            'scope': scope,
            'access_token': identity['access_token'],
            'expires_at_unix': time.time() + _async_job_ttl_seconds(),
        }
        stored_record = dict(record)
        stored_record.pop('access_token')
        stored_record['access_token_hash'] = _access_token_hash(identity['access_token'])
        _write_async_job_record(scope, job_id, stored_record)

        def _run_job() -> None:
            running = dict(stored_record)
            running['status'] = 'running'
            running['started_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            _write_async_job_record(scope, job_id, running)
            try:
                result = compute_fn()
                completed = dict(running)
                completed['status'] = 'completed'
                completed['completed_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                completed['mode'] = 'async_result'
                completed['result'] = result
                _write_async_job_record(scope, job_id, completed)
            except Exception as exc:
                failed = dict(running)
                failed['status'] = 'failed'
                failed['completed_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                failed['mode'] = 'async_result'
                failed['error'] = str(exc)
                _write_async_job_record(scope, job_id, failed)

        _submit_background_job(_run_job)
        return record

    def _get_high_rigor_job(self, job_id):
        return _load_high_rigor_job_record(job_id, access_token=self._job_access_token())

    def _get_chart_job(self, job_id):
        return _load_async_job_record(
            _API_CHART_CACHE_SCOPE,
            job_id,
            access_token=self._job_access_token(),
        )

    def _high_rigor_birth_payload(self, body):
        required = ('year', 'month', 'day', 'hour', 'minute', 'lat', 'lon')
        missing = [key for key in required if body.get(key) is None]
        if missing:
            raise BadRequest(f'missing birth fields: {", ".join(missing)}')
        year = self._get_int(body, 'year', 1990, 1800, 2400)
        month = self._get_int(body, 'month', 1, 1, 12)
        day = self._get_int(body, 'day', 1, 1, 31)
        hour = self._get_float(body, 'hour', 12, 0, 23)
        minute = self._get_float(body, 'minute', 0, 0, 59)
        second = self._get_birth_second(body)
        lat = self._get_float(body, 'lat', 0, -90, 90)
        lon = self._get_float(body, 'lon', 0, -180, 180)
        tz = self._parse_timezone(body, lat, lon, year, month, day, hour, minute, second)
        return {
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'minute': minute,
            'second': second,
            'lat': lat,
            'lon': lon,
            'tz': tz,
            'ayanamsa': body.get('ayanamsa', 'lahiri'),
            'node_mode': body.get('node_mode', body.get('nodeMode', 'mean')),
            'today': body.get('today') or body.get('current_date'),
            'transit_date': body.get('transit_date') or body.get('reference_date'),
        }

    def _high_rigor_requested_themes(self, body):
        raw = body.get('themes', body.get('theme', ['career', 'marriage', 'wealth']))
        try:
            return _UNIFIED_CONSULTATION_ORCHESTRATOR.normalize_themes(raw)
        except ValueError as exc:
            message = str(exc)
            if message.startswith('Unknown theme:'):
                detail = message.split(':', 1)[1].strip()
                raise BadRequest(f'Unknown high-rigor theme: {detail}') from exc
            raise BadRequest('theme/themes must be a string, list, or all') from exc

    def _high_rigor_events(self, body):
        events = body.get('events') or body.get('historical_events') or []
        if events is None:
            return []
        if not isinstance(events, list):
            raise BadRequest('events must be an array')
        normalized = []
        aliases = {
            'relationship': 'marriage',
            'finance': 'wealth',
            'money': 'wealth',
            'job': 'career',
            'work': 'career',
            '事业': 'career',
            '婚恋': 'marriage',
            '财富': 'wealth',
        }
        for index, event in enumerate(events[:80]):
            if not isinstance(event, dict):
                raise BadRequest('event items must be objects')
            date = event.get('date') or event.get('time') or event.get('event_date')
            domain = event.get('domain') or event.get('category') or event.get('type')
            if not date or not domain:
                continue
            domain_key = aliases.get(str(domain).strip().lower(), str(domain).strip().lower())
            normalized.append({
                **event,
                'id': event.get('id') or f'event_{index + 1}',
                'date': str(date)[:10],
                'domain': domain_key,
                'summary': event.get('summary') or event.get('desc') or event.get('description') or '',
            })
        return normalized

    def _run_high_rigor_historical_backtest(self, birth_payload, events):
        if not events:
            return {
                'scope': 'historical_event_backtest',
                'summary': {
                    'total_events': 0,
                    'strong_hits': 0,
                    'weak_hits': 0,
                    'misses': 0,
                    'blocked_events': 0,
                    'unsupported_domain_events': 0,
                },
                'events': [],
                'boundary': 'No historical events were supplied; rectification remains interview-guided only.',
            }
        module = _load_local_module('historical_event_backtest')
        payload = {
            'subject': {
                'year': int(birth_payload['year']),
                'month': int(birth_payload['month']),
                'day': int(birth_payload['day']),
                'hour': int(float(birth_payload['hour'])),
                'minute': int(float(birth_payload['minute'])),
                'lat': float(birth_payload['lat']),
                'lon': float(birth_payload['lon']),
                'tz': float(birth_payload['tz']),
                'node_mode': birth_payload.get('node_mode', 'mean'),
            },
            'events': events,
        }
        return module.build_report(payload)

    def _high_rigor_vedastro_official_summary(self, chart):
        prompt_pack = chart.get('ai_prompt_pack') if isinstance(chart, dict) else {}
        evidence_snapshot = prompt_pack.get('evidence_snapshot') if isinstance(prompt_pack, dict) else {}
        prompt_official = evidence_snapshot.get('vedastro_official_snapshot') if isinstance(evidence_snapshot, dict) else {}
        if not isinstance(prompt_official, dict):
            prompt_official = {}
        prompt_full_snapshot = evidence_snapshot.get('vedastro_official_full_snapshot') if isinstance(evidence_snapshot, dict) else {}
        if not isinstance(prompt_full_snapshot, dict):
            prompt_full_snapshot = {}
        modules = chart.get('modules') if isinstance(chart, dict) else {}
        if not isinstance(modules, dict):
            modules = {}
        range_scan = modules.get('vedastro_range_scan_result') if isinstance(modules, dict) else {}
        if not isinstance(range_scan, dict):
            range_scan = {}
        full_snapshot_payload = _build_vedastro_official_full_snapshot_payload_from_chart(chart)
        official_snapshot = range_scan.get('official_full_snapshot') if isinstance(range_scan, dict) else {}
        if not isinstance(official_snapshot, dict):
            official_snapshot = {}
        if not official_snapshot and isinstance(modules.get('vedastro_official_full_snapshot'), dict):
            official_snapshot = modules.get('vedastro_official_full_snapshot') or {}
        metadata = official_snapshot.get('source_metadata') if isinstance(official_snapshot, dict) else {}
        catalog = metadata.get('official_full_capability_catalog') if isinstance(metadata, dict) else {}
        if not isinstance(catalog, dict):
            catalog = {}
        range_metadata = range_scan.get('source_metadata') if isinstance(range_scan, dict) else {}
        if not isinstance(range_metadata, dict):
            range_metadata = {}
        strict_workflow_contracts = (
            prompt_full_snapshot.get('strict_workflow_contracts')
            or full_snapshot_payload.get('strict_workflow_contracts')
            or {}
        )
        if not isinstance(strict_workflow_contracts, dict):
            strict_workflow_contracts = {}
        strict_workflow_primary_route = (
            prompt_full_snapshot.get('strict_workflow_primary_route')
            or full_snapshot_payload.get('strict_workflow_primary_route')
        )
        strict_workflow_routes_available = (
            prompt_full_snapshot.get('strict_workflow_routes_available')
            or full_snapshot_payload.get('strict_workflow_routes_available')
            or list(strict_workflow_contracts.keys())
        )
        if not isinstance(strict_workflow_routes_available, list):
            strict_workflow_routes_available = list(strict_workflow_contracts.keys())
        _selected_route, primary_contract = _preferred_strict_contract(
            strict_workflow_contracts,
            strict_workflow_primary_route,
        )
        dynamic_selection = (
            prompt_official.get('official_full_capability_dynamic_selection')
            or catalog.get('dynamic_selection')
            or prompt_full_snapshot.get('official_full_capability_dynamic_selection')
            or full_snapshot_payload.get('official_full_capability_dynamic_selection')
            or range_metadata.get('official_full_capability_dynamic_selection')
            or {}
        )
        report_references = (
            prompt_official.get('official_report_references')
            or prompt_full_snapshot.get('official_report_references')
            or full_snapshot_payload.get('official_report_references')
            or range_metadata.get('official_report_references')
            or {
                theme: selection.get('report_reference')
                for theme, selection in dynamic_selection.items()
                if isinstance(selection, dict) and isinstance(selection.get('report_reference'), dict)
            }
        )
        status = (
            prompt_official.get('status')
            or official_snapshot.get('status')
            or range_scan.get('status')
            or 'blocked'
        )
        chart_core_status = 'blocked'
        official_primary_evidence = (
            primary_contract.get('official_primary_evidence')
            or prompt_official.get('official_primary_evidence')
            or {}
        )
        if not isinstance(official_primary_evidence, dict):
            official_primary_evidence = {}
        chart_core = official_primary_evidence.get('chart_core')
        if isinstance(chart_core, dict) and chart_core.get('status'):
            chart_core_status = chart_core.get('status')
        elif full_snapshot_payload.get('available'):
            chart_core_status = 'ok'
        event_radar_status = 'blocked'
        if (
            prompt_official.get('blocked_items')
            or prompt_official.get('fallback_used')
            or prompt_official.get('conflicts')
        ):
            event_radar_status = 'partial'
        elif range_scan.get('status') == 'ok':
            event_radar_status = 'ok'
        elif range_scan.get('status'):
            event_radar_status = 'partial'
        runtime_truth = {
            'status': status,
            'catalog_boundary': 'catalog_recognized_not_full_runtime_execution',
            'primary_route': strict_workflow_primary_route or _selected_route,
            'routes_available': strict_workflow_routes_available,
            'official_execution_layers': {
                'chart_core': chart_core_status,
                'event_radar': event_radar_status,
                'catalog_status': (
                    prompt_official.get('official_full_capability_catalog_status')
                    or catalog.get('status')
                    or range_metadata.get('official_full_capability_catalog_status')
                    or official_snapshot.get('status')
                    or 'blocked'
                ),
            },
            'fallback_active': bool(
                primary_contract.get('fallback_used')
                or prompt_official.get('fallback_used')
            ),
            'blocked_items': (
                primary_contract.get('blocked_items')
                or prompt_official.get('blocked_items')
                or []
            ),
            'conflicts': (
                primary_contract.get('conflicts')
                or prompt_official.get('conflicts')
                or []
            ),
            'free_tier_strategy': {
                'using_free_tier': not bool(os.environ.get('VEDASTRO_API_KEY', '').strip()),
                'queue_enabled': _free_tier_queue_enabled_env(),
                'cache_hit': bool(
                    (((official_snapshot.get('source_metadata') or {}).get('semantic_cache') or {}).get('cache_hit'))
                    if isinstance(official_snapshot, dict)
                    else False
                ),
                'guard_status': (
                    'degraded_or_partial'
                    if status in {'partial', 'blocked', 'official_snapshot_budget_exhausted'}
                    or bool(prompt_official.get('blocked_items'))
                    else 'within_free_tier_strategy'
                ),
            },
        }
        raw_response = (
            official_snapshot.get('raw_response')
            or official_snapshot.get('official_raw_response')
            or official_snapshot.get('raw_payload')
            or official_snapshot.get('raw')
            or prompt_full_snapshot.get('raw_response')
            or prompt_full_snapshot.get('official_raw_response')
            or prompt_full_snapshot.get('raw_payload')
            or prompt_full_snapshot.get('raw')
        )
        return {
            'status': status,
            'range_scan_status': range_scan.get('status') if isinstance(range_scan, dict) else None,
            'event_count': int(range_scan.get('event_count', 0) or 0) if isinstance(range_scan, dict) else 0,
            'official_full_capability_catalog_status': (
                prompt_official.get('official_full_capability_catalog_status')
                or catalog.get('status')
                or range_metadata.get('official_full_capability_catalog_status')
            ),
            'official_full_capability_catalog_summary': (
                prompt_official.get('official_full_capability_catalog_summary')
                or prompt_full_snapshot.get('official_full_capability_catalog_summary')
                or full_snapshot_payload.get('official_full_capability_catalog_summary')
                or catalog.get('summary')
                or range_metadata.get('official_full_capability_catalog_summary')
                or {}
            ),
            'official_full_capability_domain_routing': (
                prompt_official.get('official_full_capability_domain_routing')
                or prompt_full_snapshot.get('official_full_capability_domain_routing')
                or full_snapshot_payload.get('official_full_capability_domain_routing')
                or catalog.get('domain_routing')
                or range_metadata.get('official_full_capability_domain_routing')
                or {}
            ),
            'official_full_capability_dynamic_selection': dynamic_selection,
            'official_report_references': report_references,
            'strict_workflow_primary_route': strict_workflow_primary_route,
            'strict_workflow_routes_available': strict_workflow_routes_available,
            'strict_workflow_contracts': strict_workflow_contracts,
            'official_primary_evidence': (
                primary_contract.get('official_primary_evidence')
                or prompt_official.get('official_primary_evidence')
                or {}
            ),
            'local_supplemental_evidence': (
                primary_contract.get('local_supplemental_evidence')
                or prompt_official.get('local_supplemental_evidence')
                or {}
            ),
            'fallback_used': (
                primary_contract.get('fallback_used')
                or prompt_official.get('fallback_used')
                or []
            ),
            'blocked_items': (
                primary_contract.get('blocked_items')
                or prompt_official.get('blocked_items')
                or []
            ),
            'conflicts': (
                primary_contract.get('conflicts')
                or prompt_official.get('conflicts')
                or []
            ),
            'technique_audit_summary': primary_contract.get('technique_audit_summary') or {},
            'adjudication_stages': primary_contract.get('adjudication_stages') or {},
            'multi_reference_reading_summary': primary_contract.get('multi_reference_reading_summary') or {},
            'verdict': primary_contract.get('verdict'),
            'dominant_label': primary_contract.get('dominant_label'),
            'main_conflicts': primary_contract.get('main_conflicts') or primary_contract.get('conflicts') or [],
            'runtime_truth': runtime_truth,
            'raw_response': raw_response,
            'boundary': 'VedAstro official snapshot and capability catalog are consumed as primary evidence metadata; execution breadth depends on configured network and sample limits.',
        }

    def _interpretation_source_runtime_coverage(self, chart):
        modules = chart.get('modules') if isinstance(chart, dict) else {}
        if not isinstance(modules, dict):
            modules = {}
        prompt_pack = chart.get('ai_prompt_pack') if isinstance(chart, dict) else {}
        evidence_snapshot = prompt_pack.get('evidence_snapshot') if isinstance(prompt_pack, dict) else {}
        interpretation_pack = evidence_snapshot.get('interpretation_source_pack') if isinstance(evidence_snapshot.get('interpretation_source_pack'), dict) else {}
        candidates = {
            'dasha_timing_layer_used',
            'varga_strength_layer_used',
            'annual_special_layer_context',
            'modifier_obstacle_layer_used',
        }
        proven_markers = []
        guided_topics = modules.get('guided_topics') if isinstance(modules.get('guided_topics'), list) else []
        for topic in guided_topics:
            if not isinstance(topic, dict):
                continue
            strict_gate = topic.get('strict_audit_gate')
            if not isinstance(strict_gate, dict):
                continue
            secondary = strict_gate.get('secondary_context')
            if not isinstance(secondary, list):
                continue
            for item in secondary:
                if isinstance(item, str) and item in candidates and item not in proven_markers:
                    proven_markers.append(item)
        return {
            'source_pack_status': interpretation_pack.get('status') or 'used',
            'proven_runtime_markers': proven_markers,
            'runtime_visibility_status': 'partial' if proven_markers else 'blocked',
            'not_fully_closed': [
                'references/open_source_sources/jyotishganit',
                'references/open_source_sources/jaimini-tropical',
                'references/open_source_sources/VedicAstro',
                'references/open_source_sources/rishi-ai-mcp',
                'references/open_source_sources/vedic-astro-skills',
                'references/open_source_sources/dashaflow',
            ],
            'boundary': 'Inventory/grading exists, but full runtime invocation is only proven for surfaced strict-workflow markers, not every local source asset.',
        }

    def _high_rigor_next_questions(self, rectification, historical_backtest):
        questions = []
        summary = rectification.get('summary') if isinstance(rectification, dict) else {}
        if not isinstance(summary, dict):
            summary = {}
        for item in summary.get('recommended_events') or []:
            questions.append({
                'type': 'yes_no_or_date',
                'topic': item,
                'question': f'你是否有日期较明确的 {item} 事件？如果有，请补年份/月/日。',
            })
        backtest_summary = historical_backtest.get('summary') if isinstance(historical_backtest, dict) else {}
        if not isinstance(backtest_summary, dict):
            backtest_summary = {}
        if int(backtest_summary.get('total_events', 0) or 0) < 5:
            questions.append({
                'type': 'free_text',
                'topic': 'event_sample_size',
                'question': '目前历史事件少于5个。请补充搬家、升学、工作转折、家庭重大事件、奖项/收入变化等日期。',
            })
        return questions[:8]

    def _thematic_workflow_status(self, reading_orchestrator, orchestrator_bridge, report_orchestrator, theme_values):
        reading_themes = []
        for theme in getattr(reading_orchestrator, 'ReadingTheme'):
            reading_themes.append({
                'key': theme.value,
                'label': theme.name,
            })
        report_themes = [theme.value for theme in getattr(report_orchestrator, 'ThemeName')]
        selected = [theme.value for theme in theme_values]
        return {
            'stage': 'report_pipeline_bridge',
            'reading_theme_count': len(reading_themes),
            'reading_themes': reading_themes,
            'report_themes': report_themes,
            'selected_report_themes': selected,
            'bridge': {
                'class': getattr(orchestrator_bridge, 'OrchestratorBridge').__name__,
                'capabilities': [
                    'chapter_to_technique_results',
                    'inject_dasha_results',
                    'inject_full_reading_modules',
                ],
            },
            'boundary': 'reading_orchestrator 的 registry 执行层尚未绑定到全部实时 API；当前产品路径使用 report_orchestrator 生成报告，并显式声明桥接能力。',
        }

    def _requested_thematic_report_themes(self, body, report_orchestrator):
        raw = body.get('themes', body.get('theme', 'all'))
        if raw in (None, '', 'all'):
            values = [theme.value for theme in report_orchestrator.ThemeName]
        elif isinstance(raw, str):
            values = [raw]
        elif isinstance(raw, list):
            values = raw
        else:
            raise BadRequest('theme/themes must be a string, list, or all')
        mapping = {theme.value: theme for theme in report_orchestrator.ThemeName}
        themes = []
        for value in values:
            key = str(value).strip().lower()
            if key not in mapping:
                raise BadRequest(f'Unknown thematic report theme: {value}')
            themes.append(mapping[key])
        return themes or list(report_orchestrator.ThemeName)

    def _build_thematic_chart_data(self, raw, report_orchestrator):
        if not isinstance(raw, dict) or not raw:
            return report_orchestrator.MockDataFactory.create_sample_chart()
        birth_chart_data = report_orchestrator.BirthChartData
        dasha_timeline = self._normalize_thematic_dasha_timeline(raw)
        return birth_chart_data(
            d1_houses=self._safe_dict(raw.get('d1_houses') or raw.get('houses')),
            d9_houses=self._safe_dict(raw.get('d9_houses') or raw.get('navamsa_houses')),
            d10_houses=self._safe_dict(raw.get('d10_houses') or raw.get('dashamsa_houses')),
            d2_houses=self._safe_dict(raw.get('d2_houses')),
            d20_houses=self._safe_dict(raw.get('d20_houses')),
            d30_houses=self._safe_dict(raw.get('d30_houses')),
            d60_houses=self._safe_dict(raw.get('d60_houses')),
            planets=self._safe_dict(raw.get('planets')),
            current_dasha=self._current_thematic_dasha_label(raw),
            dasha_timeline=dasha_timeline,
            yogas=raw.get('yogas') if isinstance(raw.get('yogas'), list) else [],
            ashtakavarga=self._safe_dict(raw.get('ashtakavarga')),
        )

    def _safe_dict(self, value):
        return value if isinstance(value, dict) else {}

    def _current_thematic_dasha_label(self, raw):
        dasha = raw.get('dasha') if isinstance(raw.get('dasha'), dict) else {}
        current = dasha.get('current_dasha') if isinstance(dasha.get('current_dasha'), dict) else {}
        md = dasha.get('current_md') or current.get('mahadasha') or current.get('maha') or current.get('lord') or raw.get('current_md')
        ad = dasha.get('current_ad') or current.get('antardasha') or current.get('antar') or raw.get('current_ad')
        if md and ad:
            return f'{md}-{ad}'
        return str(md or raw.get('current_dasha') or '')

    def _normalize_thematic_dasha_timeline(self, raw):
        dasha = raw.get('dasha') if isinstance(raw.get('dasha'), dict) else {}
        source = raw.get('dasha_timeline') or dasha.get('timeline') or raw.get('periods') or []
        if not isinstance(source, list):
            return []
        timeline = []
        for period in source[:24]:
            if not isinstance(period, dict):
                continue
            start_year = self._year_from_any(period.get('start') or period.get('start_date'), datetime.utcnow().year)
            end_year = self._year_from_any(period.get('end') or period.get('end_date'), start_year + 1)
            maha = self._thematic_period_lord(period.get('mahadasha') or period.get('maha') or period.get('lord') or period.get('name'))
            antar = self._thematic_period_lord(period.get('antardasha') or period.get('antar') or period.get('sub_lord'))
            timeline.append({
                'mahadasha': maha or 'Unknown',
                'antardasha': antar or 'Unknown',
                'start': start_year,
                'end': end_year,
            })
        return timeline

    def _thematic_period_lord(self, value):
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            for key in ('lord', 'planet', 'name', 'mahadasha', 'maha', 'antardasha', 'antar'):
                item = value.get(key)
                if isinstance(item, str) and item.strip():
                    return item.strip()
        return ''

    def _year_from_any(self, value, default):
        if isinstance(value, (int, float)):
            return int(value)
        match = re.search(r'\d{4}', str(value or ''))
        return int(match.group(0)) if match else default

    def _inject_sample_thematic_evidence(self, orchestrator, report_orchestrator):
        factory = report_orchestrator.MockDataFactory()
        orchestrator.add_techniques(report_orchestrator.ThemeName.MARRIAGE, factory.create_marriage_techniques())
        orchestrator.add_techniques(report_orchestrator.ThemeName.CAREER, factory.create_career_techniques())
        orchestrator.add_techniques(report_orchestrator.ThemeName.WEALTH, factory.create_wealth_techniques())
        orchestrator.add_techniques(report_orchestrator.ThemeName.HEALTH, factory.create_health_techniques())
        orchestrator.add_techniques(report_orchestrator.ThemeName.SPIRITUALITY, factory.create_spirituality_techniques())

    def _inject_thematic_evidence(self, orchestrator, evidence, report_orchestrator):
        theme_map = {theme.value: theme for theme in report_orchestrator.ThemeName}
        strength_map = {level.value: level for level in report_orchestrator.StrengthLevel}
        for theme_name, items in evidence.items():
            theme = theme_map.get(str(theme_name).strip().lower())
            if not theme:
                raise BadRequest(f'Unknown evidence theme: {theme_name}')
            if not isinstance(items, list):
                raise BadRequest('evidence theme values must be arrays')
            results = []
            for index, item in enumerate(items[:40]):
                if not isinstance(item, dict):
                    raise BadRequest('evidence items must be objects')
                strength = strength_map.get(str(item.get('strength', 'moderate')).strip().lower(), report_orchestrator.StrengthLevel.MODERATE)
                results.append(report_orchestrator.TechniqueResult(
                    technique=str(item.get('technique') or f'{theme.value}_evidence_{index + 1}')[:80],
                    chart=str(item.get('chart') or 'D1')[:24],
                    conclusion=str(item.get('conclusion') or item.get('summary') or '未提供结论')[:800],
                    sentiment=str(item.get('sentiment') or 'neutral').strip().lower(),
                    strength=strength,
                    details=item.get('details') if isinstance(item.get('details'), dict) else {},
                ))
            orchestrator.add_techniques(theme, results)

    def _can_derive_thematic_evidence(self, raw):
        if not isinstance(raw, dict) or not raw:
            return False
        has_birth = all(raw.get(key) is not None for key in ('year', 'month', 'day'))
        has_planets = isinstance(raw.get('planets'), dict) and bool(raw.get('planets'))
        return has_birth or has_planets

    def _derive_thematic_evidence(self, raw, report_orchestrator):
        warnings = []
        module_status = {}

        def collect(key, fn):
            try:
                value = fn()
                module_status[key] = 'ok'
                return value
            except Exception as exc:
                module_status[key] = 'warning'
                warnings.append({'module': key, 'error': str(exc)[:240]})
                return None

        has_birth = all(raw.get(key) is not None for key in ('year', 'month', 'day'))
        skip_full_reading = bool(raw.get('skip_full_reading_for_thematic'))
        full_reading = (
            collect('full_reading', lambda: self._compute_full_reading_for_thematic(raw))
            if has_birth and not skip_full_reading
            else None
        )
        if skip_full_reading:
            module_status['full_reading'] = 'skipped_reuse_chart_data'
        full_modules = full_reading.get('modules', {}) if isinstance(full_reading, dict) else {}
        chart = None
        if full_reading:
            chart = self._chart_from_full_reading(full_reading)
        if not chart and has_birth:
            chart = collect('chart', lambda: self._compute_chart(raw))
        if not chart:
            normalized, _, _ = self._normalized_planets_from_body(raw)
            chart = {
                'success': True,
                'planets': normalized,
                'ascendant': raw.get('ascendant', SAMPLE_ASCENDANT),
                'houses': raw.get('houses', {}),
                'dasha': raw.get('dasha', {}),
                'yogas': raw.get('yogas', []),
                'source': 'provided_planets',
            }
            module_status.setdefault('chart', 'provided_planets')

        payload = dict(raw)
        payload['planets'] = chart.get('planets') or payload.get('planets') or {}
        payload['ascendant'] = chart.get('ascendant') or payload.get('ascendant') or SAMPLE_ASCENDANT
        if chart.get('dasha') and not isinstance(payload.get('dasha'), str):
            payload['dasha'] = chart.get('dasha')
        asc_sign = payload.get('asc_sign') or payload['ascendant'].get('sign') or SIGNS[payload['ascendant'].get('sign_idx', 0)]
        payload['asc_sign'] = asc_sign if asc_sign in SIGNS else SIGNS[0]
        dasha_payload = {**payload, 'dasha': 'vimshottari'}
        if chart.get('dasha', {}).get('current_md'):
            dasha_payload['current_md'] = chart['dasha']['current_md']

        dasha = full_modules.get('dasha') or collect('dasha', lambda: self._compute_dasha_system(dasha_payload))
        yogas = full_modules.get('yoga') or collect('yogas', lambda: self._compute_yogas_api(payload))
        shadbala = full_modules.get('shadbala') or collect('shadbala', lambda: self._compute_shadbala(payload))
        ashtakavarga = full_modules.get('ashtakavarga') or collect('ashtakavarga', lambda: self._compute_ashtakavarga(payload))
        relationship = collect('relationship', lambda: self._compute_relationship({
            **payload,
            'dasha_info': self._thematic_dasha_info(chart, dasha),
        }))
        career = collect('career', lambda: self._compute_career(payload))
        jaimini = full_modules.get('jaimini') or collect('jaimini', lambda: self._compute_jaimini({**payload, 'mode': 'all'}))

        enriched = {
            **payload,
            'houses': chart.get('houses') or raw.get('houses') or {},
            'dasha': dasha or chart.get('dasha') or {},
            'periods': (dasha or {}).get('periods') or (dasha or {}).get('timeline') or [],
            'yogas': chart.get('yogas') or [],
            'ashtakavarga': ashtakavarga or {},
        }
        if yogas and isinstance(yogas.get('result'), dict):
            enriched['yogas'] = list(enriched['yogas']) + (yogas['result'].get('extended_yogas') or [])
        elif isinstance(yogas, dict):
            enriched['yogas'] = list(enriched['yogas']) + (yogas.get('yogas') or [])

        evidence = self._build_derived_thematic_evidence(
            enriched,
            dasha=dasha,
            yogas=yogas,
            shadbala=shadbala,
            ashtakavarga=ashtakavarga,
            relationship=relationship,
            career=career,
            jaimini=jaimini,
            full_reading=full_reading,
            full_modules=full_modules,
            report_orchestrator=report_orchestrator,
        )
        return {
            'chart_data': enriched,
            'evidence': evidence,
            'module_status': module_status,
            'warnings': warnings,
            'evidence_counts': {theme: len(items) for theme, items in evidence.items()},
            'full_reading_used': bool(full_reading),
            'full_reading_summary': full_reading.get('summary', {}) if isinstance(full_reading, dict) else {},
            'full_reading_module_count': len(full_modules) if isinstance(full_modules, dict) else 0,
        }

    def _thematic_evidence_source(self, mode, derived_context, has_custom_evidence):
        if mode == 'derived_chart_evidence' and derived_context:
            full_reading_used = bool(derived_context.get('full_reading_used'))
            return {
                'mode': mode,
                'source': 'full_reading_modules' if full_reading_used else 'birth_or_chart_payload',
                'sample_fallback': False,
                'full_reading_used': full_reading_used,
                'full_reading_module_count': derived_context.get('full_reading_module_count', 0),
                'full_reading_summary': derived_context.get('full_reading_summary', {}),
                'module_status': derived_context.get('module_status', {}),
                'warning_count': len(derived_context.get('warnings', [])),
                'warnings': derived_context.get('warnings', [])[:6],
                'evidence_counts': derived_context.get('evidence_counts', {}),
            }
        return {
            'mode': mode,
            'source': 'caller_evidence' if has_custom_evidence else 'report_orchestrator.MockDataFactory',
            'sample_fallback': mode == 'sample_evidence',
        }

    def _build_derived_thematic_evidence(self, chart_data, **context):
        evidence = {
            'marriage': [],
            'career': [],
            'wealth': [],
            'health': [],
            'spirituality': [],
        }
        evidence['marriage'].extend(self._derived_marriage_evidence(chart_data, context))
        evidence['career'].extend(self._derived_career_evidence(chart_data, context))
        evidence['wealth'].extend(self._derived_wealth_evidence(chart_data, context))
        evidence['health'].extend(self._derived_health_evidence(chart_data, context))
        evidence['spirituality'].extend(self._derived_spirituality_evidence(chart_data, context))
        return evidence

    def _derived_marriage_evidence(self, chart_data, context):
        h7 = self._theme_house_snapshot(chart_data, 7)
        relationship = context.get('relationship') or {}
        timing = relationship.get('relationship_timing') if isinstance(relationship, dict) else {}
        full_modules = context.get('full_modules') if isinstance(context.get('full_modules'), dict) else {}
        items = [
            self._theme_evidence(
                'D1-7th-house',
                'D1',
                f"第7宫为{h7['sign']}，宫内星体：{h7['planets_label']}；用于判断婚姻承诺与伴侣互动基调。",
                'neutral' if h7['planets_label'] == '无' else 'positive',
                'moderate',
                source='chart',
                details=h7,
            ),
        ]
        spouse = relationship.get('spouse_status_yoga') if isinstance(relationship, dict) else {}
        if spouse:
            items.append(self._theme_evidence(
                'Spouse-status-yoga',
                'D1/D9',
                spouse.get('summary') or spouse.get('headline') or '配偶状态 Yoga 已由关系引擎计算，可作为婚姻主题证据。',
                'positive' if spouse.get('score', 0) and spouse.get('score', 0) >= 50 else 'neutral',
                'moderate',
                source='relationship',
                details={'fragment': 'spouse_status_yoga.py', 'score': spouse.get('score')},
            ))
        if timing:
            items.append(self._theme_evidence(
                'DK-UL-Dasha timing',
                'Dasha',
                timing.get('summary') or 'DK、UL 与 Dasha 触发已进入婚姻时机证据链。',
                'positive' if timing.get('level') in {'strong', 'watch'} else 'neutral',
                'strong' if timing.get('level') == 'strong' else 'moderate',
                source='relationship_timing',
                details={'fragment': timing.get('source'), 'clues': timing.get('timing_clues', [])},
            ))
        marriage_counting = full_modules.get('marriage_counting') if isinstance(full_modules, dict) else {}
        if isinstance(marriage_counting, dict) and marriage_counting.get('interpretation'):
            items.append(self._theme_evidence(
                'Marriage-counting',
                'D1/D9',
                marriage_counting.get('interpretation'),
                'positive' if (marriage_counting.get('marriage_count') or 0) <= 1 else 'neutral',
                'moderate',
                source='full_reading.modules.marriage_counting',
                details={
                    'marriage_count': marriage_counting.get('marriage_count'),
                    'd9_marriage_quality': marriage_counting.get('d9_marriage_quality'),
                },
            ))
        vivah = full_modules.get('vivah_saham') if isinstance(full_modules, dict) else {}
        if isinstance(vivah, dict) and vivah.get('vivah_saham'):
            items.append(self._theme_evidence(
                'Vivah-saham',
                'Tajika',
                vivah.get('note') or 'Vivah Saham 已由 full-reading 计算，可作为婚姻事件敏感点。',
                'neutral',
                'moderate',
                source='full_reading.modules.vivah_saham',
                details=vivah.get('vivah_saham') if isinstance(vivah.get('vivah_saham'), dict) else vivah,
            ))
        strict_relationship = full_modules.get('relationship_strict_evidence') if isinstance(full_modules, dict) else {}
        user_narrative = strict_relationship.get('user_narrative') if isinstance(strict_relationship, dict) else {}
        if isinstance(user_narrative, dict) and user_narrative.get('markdown'):
            items.append(self._theme_evidence(
                'Relationship-strict-narrative',
                'Strict',
                user_narrative.get('markdown'),
                'neutral',
                'strong',
                source='full_reading.modules.relationship_strict_evidence.user_narrative',
                details={
                    'headline': user_narrative.get('headline'),
                    'strengths': user_narrative.get('strengths', [])[:3],
                    'risks': user_narrative.get('risks', [])[:3],
                    'boundaries': user_narrative.get('boundaries', [])[:3],
                    'monthly_frame': user_narrative.get('monthly_frame', {}),
                },
            ))
        return items

    def _derived_career_evidence(self, chart_data, context):
        h10 = self._theme_house_snapshot(chart_data, 10)
        career = context.get('career') or {}
        shadbala = context.get('shadbala') or {}
        full_modules = context.get('full_modules') if isinstance(context.get('full_modules'), dict) else {}
        top_strength = self._top_shadbala_planet(shadbala)
        items = [
            self._theme_evidence(
                'D1-10th-house',
                'D1',
                f"第10宫为{h10['sign']}，宫内星体：{h10['planets_label']}；这是事业角色、名望与外在职责的主轴。",
                'positive' if h10['planets'] else 'neutral',
                'moderate',
                source='chart',
                details=h10,
            ),
        ]
        if career:
            items.append(self._theme_evidence(
                'Career-engine',
                'D1',
                self._first_text_from_dict(career, ['summary', 'career_summary', 'dominant_theme', 'recommendation']) or '事业引擎已根据行星与上升星座生成职业倾向。',
                'positive',
                'moderate',
                source='career_analysis.py',
                details={'keys': sorted(career.keys())[:10]},
            ))
        if top_strength:
            items.append(self._theme_evidence(
                'Shadbala-career-support',
                'Strength',
                f"Shadbala 排名中 {top_strength['planet']} 支持度最高（{top_strength['rupas']} rupas），可作为事业执行力/资源侧证。",
                'positive',
                'moderate',
                source='shadbala',
                details=top_strength,
            ))
        convergence = full_modules.get('dasa_convergence') if isinstance(full_modules, dict) else {}
        if not isinstance(convergence, dict):
            convergence = {}
        top_domains = convergence.get('top_convergent_domains') if isinstance(convergence, dict) else []
        if not isinstance(top_domains, list):
            top_domains = []
        career_domain = next(
            (
                row for row in top_domains
                if isinstance(row, dict) and any(token in str(row.get('domain', '')).lower() for token in ('career', 'profession', 'status', 'work'))
            ),
            None,
        )
        if not career_domain and isinstance(convergence.get('domain_activations'), dict):
            for domain, row in convergence['domain_activations'].items():
                if any(token in str(domain).lower() for token in ('career', 'profession', 'status', 'work')):
                    career_domain = {'domain': domain, **(row if isinstance(row, dict) else {})}
                    break
        if career_domain:
            items.append(self._theme_evidence(
                'Dasa-convergence-career',
                'Multi-Dasha',
                career_domain.get('interpretation') or '多 Dasha 收敛模块已命中事业相关领域，需结合 Transit 确认兑现窗口。',
                'positive',
                'strong' if career_domain.get('convergence_level') in {'L2', 'L3'} else 'moderate',
                source='full_reading.modules.dasa_convergence',
                details=career_domain,
            ))
        strict_career = full_modules.get('career_strict_evidence') if isinstance(full_modules, dict) else {}
        user_narrative = strict_career.get('user_narrative') if isinstance(strict_career, dict) else {}
        if isinstance(user_narrative, dict) and user_narrative.get('markdown'):
            items.append(self._theme_evidence(
                'Career-strict-narrative',
                'Strict',
                user_narrative.get('markdown'),
                'neutral',
                'strong',
                source='full_reading.modules.career_strict_evidence.user_narrative',
                details={
                    'headline': user_narrative.get('headline'),
                    'strengths': user_narrative.get('strengths', [])[:3],
                    'risks': user_narrative.get('risks', [])[:3],
                    'boundaries': user_narrative.get('boundaries', [])[:3],
                    'monthly_frame': user_narrative.get('monthly_frame', {}),
                },
            ))
        return items

    def _derived_wealth_evidence(self, chart_data, context):
        h2 = self._theme_house_snapshot(chart_data, 2)
        h11 = self._theme_house_snapshot(chart_data, 11)
        ashtakavarga = context.get('ashtakavarga') or {}
        av_summary = self._ashtakavarga_summary_for_theme(ashtakavarga)
        full_modules = context.get('full_modules') if isinstance(context.get('full_modules'), dict) else {}
        items = [
            self._theme_evidence(
                '2nd-and-11th-house',
                'D1',
                f"第2宫({h2['sign']})与第11宫({h11['sign']})共同描述收入、积累与收益网络。",
                'neutral',
                'moderate',
                source='chart',
                details={'second': h2, 'eleventh': h11},
            ),
        ]
        if av_summary:
            strongest = av_summary.get('strongest_houses') or []
            wealth_hit = any(row.get('house') in (2, 11) for row in strongest)
            items.append(self._theme_evidence(
                'Ashtakavarga-wealth',
                'AV',
                av_summary.get('headline') or 'Ashtakavarga 已生成财富宫位支持度。',
                'positive' if wealth_hit else 'neutral',
                'strong' if wealth_hit else 'moderate',
                source='ashtakavarga',
                details={'strongest_houses': strongest, 'sav_total': av_summary.get('sav_total')},
            ))
        yogas_doshas = full_modules.get('yogas_doshas') if isinstance(full_modules, dict) else {}
        dhana = yogas_doshas.get('dhana_yogas') if isinstance(yogas_doshas, dict) else {}
        dhana_yogas = dhana.get('yogas') if isinstance(dhana, dict) else []
        if dhana_yogas:
            items.append(self._theme_evidence(
                'Dhana-yoga-full-reading',
                'D1',
                dhana.get('summary') or f"full-reading 检出 {len(dhana_yogas)} 条 Dhana Yoga，可作为财富主题的直接证据。",
                'positive',
                'strong' if any(row.get('strength') == 'strong' for row in dhana_yogas if isinstance(row, dict)) else 'moderate',
                source='full_reading.modules.yogas_doshas',
                details={'yogas': dhana_yogas[:4]},
            ))
        strict_finance = full_modules.get('finance_strict_evidence') if isinstance(full_modules, dict) else {}
        user_narrative = strict_finance.get('user_narrative') if isinstance(strict_finance, dict) else {}
        if isinstance(user_narrative, dict) and user_narrative.get('markdown'):
            items.append(self._theme_evidence(
                'Finance-strict-narrative',
                'Strict',
                user_narrative.get('markdown'),
                'neutral',
                'strong',
                source='full_reading.modules.finance_strict_evidence.user_narrative',
                details={
                    'headline': user_narrative.get('headline'),
                    'strengths': user_narrative.get('strengths', [])[:3],
                    'risks': user_narrative.get('risks', [])[:3],
                    'boundaries': user_narrative.get('boundaries', [])[:3],
                    'monthly_frame': user_narrative.get('monthly_frame', {}),
                },
            ))
        return items

    def _derived_health_evidence(self, chart_data, context):
        h6 = self._theme_house_snapshot(chart_data, 6)
        h8 = self._theme_house_snapshot(chart_data, 8)
        h12 = self._theme_house_snapshot(chart_data, 12)
        yogas = context.get('yogas') or {}
        curse = ((yogas.get('result') or {}).get('curse_yogas') or {}) if isinstance(yogas, dict) else {}
        risk = curse.get('overall_risk')
        full_modules = context.get('full_modules') if isinstance(context.get('full_modules'), dict) else {}
        items = [
            self._theme_evidence(
                '6-8-12-health-axis',
                'D1',
                f"健康轴线：6宫{h6['sign']}、8宫{h8['sign']}、12宫{h12['sign']}，用于观察疾病、突发与消耗主题。",
                'negative' if any(row['planets'] for row in (h6, h8, h12)) else 'neutral',
                'moderate',
                source='chart',
                details={'sixth': h6, 'eighth': h8, 'twelfth': h12},
            ),
        ]
        if risk:
            items.append(self._theme_evidence(
                'Curse-yoga-risk',
                'D1',
                f"凶星合相风险层返回 {risk}，作为健康/压力主题的高风险提示证据之一。",
                'negative' if risk in {'high', 'medium'} else 'neutral',
                'moderate',
                source='curse_yoga_detector.py',
                details={'risk': risk, 'detected': curse.get('curses_detected', [])[:4]},
            ))
        validation = full_modules.get('validation') if isinstance(full_modules, dict) else {}
        if isinstance(validation, dict) and validation.get('checked'):
            items.append(self._theme_evidence(
                'Calculation-validation-gate',
                'Validation',
                f"full-reading 完成 {validation.get('checked')} 项计算校验，通过 {validation.get('passed')} 项；健康判断可基于已校验星盘继续审慎解释。",
                'positive' if validation.get('valid') else 'negative',
                'strong' if validation.get('valid') else 'moderate',
                source='full_reading.modules.validation',
                details={
                    'valid': validation.get('valid'),
                    'passed': validation.get('passed'),
                    'failed': validation.get('failed'),
                },
            ))
        trimshamsa = full_modules.get('trimshamsa_d30') if isinstance(full_modules, dict) else {}
        crisis = trimshamsa.get('marriage_crisis') if isinstance(trimshamsa, dict) else None
        if crisis:
            items.append(self._theme_evidence(
                'Trimshamsa-D30-risk',
                'D30',
                'D30 Trimshamsa 已进入压力/危机侧证；健康主题需把风险提示与现实医疗信息分开处理。',
                'negative' if isinstance(crisis, dict) and crisis.get('risk_level') in {'high', 'medium'} else 'neutral',
                'moderate',
                source='full_reading.modules.trimshamsa_d30',
                details=crisis if isinstance(crisis, dict) else {'crisis': crisis},
            ))
        return items

    def _derived_spirituality_evidence(self, chart_data, context):
        h9 = self._theme_house_snapshot(chart_data, 9)
        h12 = self._theme_house_snapshot(chart_data, 12)
        planets = chart_data.get('planets') if isinstance(chart_data.get('planets'), dict) else {}
        jupiter = planets.get('Jupiter', {}) if isinstance(planets.get('Jupiter'), dict) else {}
        ketu = planets.get('Ketu', {}) if isinstance(planets.get('Ketu'), dict) else {}
        jaimini = context.get('jaimini') or {}
        karakamsha = self._extract_jaimini_karakamsha(jaimini)
        full_modules = context.get('full_modules') if isinstance(context.get('full_modules'), dict) else {}
        items = [
            self._theme_evidence(
                '9th-and-12th-spirit',
                'D1',
                f"第9宫({h9['sign']})与第12宫({h12['sign']})显示信念、导师、修行与出离倾向。",
                'positive' if h9['planets'] or h12['planets'] else 'neutral',
                'moderate',
                source='chart',
                details={'ninth': h9, 'twelfth': h12},
            ),
            self._theme_evidence(
                'Jupiter-Ketu-spiritual-karaka',
                'D1',
                f"Jupiter 位于{jupiter.get('sign', '未知')}第{jupiter.get('house', '-')}宫，Ketu 位于{ketu.get('sign', '未知')}第{ketu.get('house', '-')}宫。",
                'positive' if jupiter.get('house') in (1, 5, 9, 12) or ketu.get('house') in (9, 12) else 'neutral',
                'moderate',
                source='chart',
                details={'Jupiter': jupiter, 'Ketu': ketu},
            ),
        ]
        if karakamsha:
            items.append(self._theme_evidence(
                'Karakamsha',
                'D9/D1',
                karakamsha.get('interpretation') or karakamsha.get('description') or 'Karakamsha 已由 Jaimini 模块计算，用于灵性使命与内在驱动力。',
                'positive',
                'moderate',
                source='jaimini.py',
                details=karakamsha,
            ))
        d20 = self._extract_vimsamsa_spiritual_context(full_modules)
        if d20:
            items.append(self._theme_evidence(
                'Vimsamsa-D20-spiritual-context',
                'D20',
                d20.get('summary') or 'D20 Vimsamsa 分盘已进入灵性主题证据链，用于观察修行、信念与内在追求。',
                'positive',
                'moderate',
                source=d20.get('source', 'full_reading.modules.varga_full'),
                details=d20,
            ))
        return items

    def _theme_evidence(self, technique, chart, conclusion, sentiment, strength, *, source, details=None):
        return {
            'technique': technique,
            'chart': chart,
            'conclusion': str(conclusion)[:800],
            'sentiment': sentiment,
            'strength': strength,
            'details': {
                **(details if isinstance(details, dict) else {}),
                'source': source,
                'derived': True,
            },
        }

    def _strict_monthly_frame_from_theme_report(self, report_payload):
        if not isinstance(report_payload, dict):
            return {}
        evidence = report_payload.get('evidence')
        if not isinstance(evidence, list):
            return {}
        for item in evidence:
            if not isinstance(item, dict):
                continue
            details = item.get('details')
            if not isinstance(details, dict):
                continue
            monthly_frame = details.get('monthly_frame')
            if isinstance(monthly_frame, dict) and monthly_frame:
                return monthly_frame
        return {}

    def _humanize_monthly_adjudication(self, theme_name, primary_state, manifestation_mode, friction_source, time_confidence):
        primary_map = {
            '推进': '进入可主动推进窗口',
            '启动': '进入新线索浮出的阶段',
            '观察': '更适合观察与试探，不宜过早定性',
            '筛选': '更适合边接触边筛选，先排除不合适的人或事',
            '整固': '更像守成整固，而不是激进扩张',
            '重组': '更像旧结构拆开重排，再决定下一步',
            '收束': '更像阶段性收尾、定局或止损',
        }
        timing_map = {
            'day_supported': '月份与少数关键日期都可参考，日期判断相对更实用。',
            'month_supported': '以月份判断最稳，具体日期只能作辅助观察。',
            'month_only': '只能判断月级趋势，暂时不宜把结论压到具体某一天。',
            'blocked': '时间证据仍不足，当前只能保守看趋势，不宜下精确日期判断。',
        }
        manifestation_map = {
            'career': {
                '职业定位推进': '更像职业定位开始推进，适合明确方向、角色或赛道。',
                '职位/项目/职责抬头': '更像职位、项目或职责开始抬头。',
                '项目/合作推进': '更像项目、合作、签约或公开职责往前走。',
            },
            'marriage': {
                '关系观察/筛选': '更像先接触、观察、筛选，再决定是否深入推进。',
                '公开化/关系可见度上升': '更像关系可见度上升，或公开互动开始变多。',
            },
            'wealth': {
                '现金流结构观察': '更像先看现金流结构与回款节奏，而不是立刻看到大额留存。',
                '定金/回款/短期现金流改善': '更像定金、回款或短期现金流出现改善。',
            },
        }
        friction_map = {
            '流程卡顿但机会仍在': '机会未消失，但流程、对接或资源节奏会更磨人。',
            '执行压力伴随机会': '机会和压力会一起出现，往往不是轻松拿下，而是边扛边推进。',
            '时间证据不足': '时间证据还不够密，能看趋势，但不宜把结论说得过满。',
        }

        humanized = {
            'primary_state': primary_map.get(primary_state, primary_state or ''),
            'manifestation_mode': manifestation_map.get(theme_name, {}).get(manifestation_mode, manifestation_mode or ''),
            'friction_source': friction_map.get(friction_source, friction_source or ''),
            'time_confidence': timing_map.get(time_confidence, time_confidence or ''),
        }
        return humanized

    @staticmethod
    def _theme_evidence_lookup(report_payload):
        if not isinstance(report_payload, dict):
            return {}
        evidence = report_payload.get('evidence')
        if not isinstance(evidence, list):
            return {}
        lookup = {}
        for item in evidence:
            if not isinstance(item, dict):
                continue
            technique = str(item.get('technique') or '').strip()
            if technique and technique not in lookup:
                lookup[technique] = item
        return lookup

    @staticmethod
    def _normalize_sentence(text):
        value = str(text or '').replace('\n', ' ').strip()
        if not value:
            return ''
        value = re.sub(r'\s+', ' ', value)
        value = value.replace('。，', '。').replace('，。', '。').replace('..', '.')
        if value[-1] not in '。！？!?':
            value = value + '。'
        return value.replace('。。', '。')

    def _join_adjudication_parts(self, parts):
        normalized = [self._normalize_sentence(part) for part in parts if str(part or '').strip()]
        return " ".join(normalized).replace('。。', '。').strip()

    @staticmethod
    def _strip_humanized_prefix(text):
        value = str(text or '').strip()
        if value.startswith('更像'):
            return value[2:].strip()
        return value

    def _join_brief_points(self, items):
        cleaned = []
        for item in items or []:
            value = self._normalize_sentence(item)
            if not value:
                continue
            cleaned.append(value.rstrip('。！？!?'))
        return '；'.join(cleaned)

    @staticmethod
    def _matching_strict_lines(lines, keywords):
        if not isinstance(lines, list):
            return []
        matches = []
        for line in lines:
            value = str(line or '').strip()
            if value and any(keyword in value for keyword in keywords):
                matches.append(value)
        return matches

    @staticmethod
    def _extract_confidence_cap(strict_item):
        if not isinstance(strict_item, dict):
            return ''
        conclusion = str(strict_item.get('conclusion') or '')
        match = re.search(r'confidence_cap:\s*([a-z_]+)', conclusion)
        if not match:
            return ''
        return match.group(1).strip().lower()

    def _confidence_cap_cn(self, confidence_cap):
        mapping = {
            'high': '高',
            'moderate': '中',
            'low': '低',
            'blocked': '阻塞',
            'unknown': '未知',
        }
        return mapping.get(str(confidence_cap or '').strip().lower(), str(confidence_cap or '').strip())

    def _strict_axis_payload_for_theme(self, theme_name, report_payload, humanized):
        lookup = self._theme_evidence_lookup(report_payload)
        strict_key_map = {
            'career': 'Career-strict-narrative',
            'marriage': 'Relationship-strict-narrative',
            'wealth': 'Finance-strict-narrative',
        }
        strict_item = lookup.get(strict_key_map.get(theme_name, '')) or {}
        strict_details = strict_item.get('details') if isinstance(strict_item.get('details'), dict) else {}
        strengths = strict_details.get('strengths') if isinstance(strict_details.get('strengths'), list) else []
        risks = strict_details.get('risks') if isinstance(strict_details.get('risks'), list) else []
        boundaries = strict_details.get('boundaries') if isinstance(strict_details.get('boundaries'), list) else []
        confidence_cap = self._extract_confidence_cap(strict_item)
        return {
            'lookup': lookup,
            'strict_item': strict_item,
            'strict_details': strict_details,
            'strengths': strengths,
            'risks': risks,
            'boundaries': boundaries,
            'confidence_cap': confidence_cap,
            'humanized': humanized,
        }

    def _career_axis_judgements(self, report_payload, humanized):
        payload = self._strict_axis_payload_for_theme('career', report_payload, humanized)
        lookup = payload['lookup']
        strengths = payload['strengths']
        risks = payload['risks']
        boundaries = payload['boundaries']
        confidence_cap = payload['confidence_cap']

        d10 = ((lookup.get('D1-10th-house') or {}).get('details') or {})
        convergence = lookup.get('Dasa-convergence-career') or {}
        shadbala = lookup.get('Shadbala-career-support') or {}
        tenth_sign = d10.get('sign') or '未知'
        tenth_planets = d10.get('planets_label') or '无'
        role_supports = self._matching_strict_lines(strengths, ['A10', 'Amatyakaraka', 'Karakamsha'])
        role_risks = self._matching_strict_lines(risks, ['Argala', '阻力', '卡顿'])
        org_supports = self._matching_strict_lines(strengths, ['A10', 'Amatyakaraka'])
        migration_boundary = self._matching_strict_lines(boundaries, ['VedAstro', '时间置信度', 'D10'])
        convergence_text = str(convergence.get('conclusion') or convergence.get('details', {}).get('interpretation') or '').strip()
        shadbala_text = str(shadbala.get('conclusion') or '').strip()
        manifestation_core = self._strip_humanized_prefix(humanized.get('manifestation_mode'))
        role_support_text = self._join_brief_points(role_supports[:3])
        org_support_text = self._join_brief_points(org_supports[:2])

        axes = [
            {
                'axis': '角色定位',
                'judgement': self._join_adjudication_parts([
                    f"角色定位这一轴，第10宫在{tenth_sign}，宫内{tenth_planets}，所以事业判断的主问题不是单看有没有机会，而是你会以什么角色、职责和公众面貌被看见。",
                    f"当前严格链已经把这几层并入主裁决：{role_support_text}。" if role_support_text else '',
                    f"这也是为什么本轮月度主状态不是静态守成，而是{humanized.get('primary_state')}；落地形式更偏{manifestation_core}。",
                    role_risks[0] if role_risks else '',
                    f"置信上限：{self._confidence_cap_cn(confidence_cap)}。" if confidence_cap else '',
                    f"时间边界：{humanized.get('time_confidence')}",
                ]),
                'evidence_anchor': ['D1-10th-house', 'Career-strict-narrative'],
            },
            {
                'axis': '项目合作',
                'judgement': self._join_adjudication_parts([
                    "项目合作这一轴，当前不是完全空白，但也还没到可以直接写成长期稳定落袋的程度。",
                    convergence_text or '多重时间系统已经触到事业域，但还需要更多现实确认。',
                    f"所以更像先有合作入口、项目接触或职责试探，再决定是否真正推进到签约、常驻或长期绑定。",
                    f"阻力层面，{humanized.get('friction_source')}",
                    f"时间边界：{humanized.get('time_confidence')}",
                ]),
                'evidence_anchor': ['Dasa-convergence-career', 'Career-strict-narrative'],
            },
            {
                'axis': '组织权责',
                'judgement': self._join_adjudication_parts([
                    "组织权责这一轴，比起单纯换工作，更像权责结构、上级关系和专业角色承担被重新摆到台前。",
                    f"严格链里最关键的支撑是这几层：{org_support_text}。" if org_support_text else '',
                    shadbala_text,
                    "这意味着你容易被要求承担更明确的职责、结果或对外可见任务，但通常不是轻松抬升，而是伴随现实压力同步出现。",
                    f"时间边界：{humanized.get('time_confidence')}",
                ]),
                'evidence_anchor': ['Career-strict-narrative', 'Shadbala-career-support'],
            },
            {
                'axis': '迁移动向',
                'judgement': self._join_adjudication_parts([
                    "迁移动向这一轴，当前主链并没有把“异地定局”抬成事业主题的最强主轴。",
                    f"现有证据更集中在第10宫职责触发与{manifestation_core}，而不是直接给出长期搬家、长期异地驻扎已经坐实的锚点。",
                    migration_boundary[0] if migration_boundary else '如果后续官方日窗口或外部事件层补到 relocation / travel 命中，才适合进一步上调迁移判断。',
                    f"时间边界：{humanized.get('time_confidence')}",
                ]),
                'evidence_anchor': ['D1-10th-house', 'Career-strict-narrative'],
            },
        ]
        return axes

    def _marriage_axis_judgements(self, report_payload, humanized):
        payload = self._strict_axis_payload_for_theme('marriage', report_payload, humanized)
        lookup = payload['lookup']
        strengths = payload['strengths']
        risks = payload['risks']
        boundaries = payload['boundaries']
        confidence_cap = payload['confidence_cap']

        seventh = ((lookup.get('D1-7th-house') or {}).get('details') or {})
        timing = lookup.get('DK-UL-Dasha timing') or {}
        counting = lookup.get('Marriage-counting') or {}
        vivah = lookup.get('Vivah-saham') or {}

        seventh_sign = seventh.get('sign') or '未知'
        seventh_planets = seventh.get('planets_label') or '无'
        d9_quality = (((counting.get('details') or {}).get('d9_marriage_quality')) or {})
        timing_conclusion = str(timing.get('conclusion') or '').strip()
        vivah_conclusion = str(vivah.get('conclusion') or '').strip()
        manifestation_core = self._strip_humanized_prefix(humanized.get('manifestation_mode'))
        ul_supports = self._matching_strict_lines(strengths, ['Upapada', 'UL'])
        low_confidence = self._matching_strict_lines(risks, ['confidence cap', '冲突', '不足'])
        boundary_focus = self._matching_strict_lines(boundaries, ['D1、D9、UL', 'legal_marriage', 'dual dasha'])

        axes = [
            {
                'axis': '关系推进',
                'judgement': self._join_adjudication_parts([
                    f"关系推进这一轴，第7宫在{seventh_sign}，宫内{seventh_planets}，说明伴侣关系会成为需要正面面对的人生主轴，而不是轻描淡写带过的副题。",
                    timing_conclusion,
                    f"当前月度主状态是{humanized.get('primary_state')}，所以更像关系线索开始浮出，而不是已经进入婚约定局。",
                    f"置信上限：{self._confidence_cap_cn(confidence_cap)}。" if confidence_cap else '',
                    f"时间边界：{humanized.get('time_confidence')}",
                ]),
                'evidence_anchor': ['D1-7th-house', 'DK-UL-Dasha timing', 'Relationship-strict-narrative'],
            },
            {
                'axis': '对象筛选',
                'judgement': self._join_adjudication_parts([
                    "对象筛选这一轴，是当前婚恋判断里最不能跳过的一层。",
                    f"严格链已经明确当前落地形式更偏{manifestation_core}，也就是说重点不是立刻确认关系，而是先看谁值得继续推进。",
                    str(counting.get('conclusion') or ''),
                    d9_quality.get('quality_rating') or '',
                    "这类组合更像先识别重复的关系模式，再决定是否深入，而不是因为出现线索就直接抬升成结婚窗口。",
                    f"时间边界：{humanized.get('time_confidence')}",
                ]),
                'evidence_anchor': ['Marriage-counting', 'Relationship-strict-narrative'],
            },
            {
                'axis': '公开化程度',
                'judgement': self._join_adjudication_parts([
                    "公开化程度这一轴，当前可以看见关系可见度会慢慢增加，但它和法律婚姻不是一回事。",
                    ul_supports[0] if ul_supports else '',
                    vivah_conclusion,
                    "因此更合理的读法是：先有互动增加、公开接触增多或身边人开始知道，再看后续是否真的跨进更正式的承诺层。",
                    f"时间边界：{humanized.get('time_confidence')}",
                ]),
                'evidence_anchor': ['Relationship-strict-narrative', 'Vivah-saham'],
            },
            {
                'axis': '承诺边界',
                'judgement': self._join_adjudication_parts([
                    "承诺边界这一轴，必须压住过度乐观的解读。",
                    low_confidence[0] if low_confidence else '',
                    boundary_focus[0] if boundary_focus else '在 D1、D9、UL 与 dual dasha 没有更完整闭环前，不能把当前关系窗口直接包装成结婚必然落地。',
                    "所以这轮最严谨的结论是：婚恋线在动，但更像进入观察、筛选和校验阶段，而不是已经可以宣布承诺定局。",
                    f"时间边界：{humanized.get('time_confidence')}",
                ]),
                'evidence_anchor': ['Relationship-strict-narrative', 'DK-UL-Dasha timing'],
            },
        ]
        return axes

    def _wealth_axis_judgements(self, report_payload, humanized):
        payload = self._strict_axis_payload_for_theme('wealth', report_payload, humanized)
        lookup = payload['lookup']
        risks = payload['risks']
        boundaries = payload['boundaries']
        confidence_cap = payload['confidence_cap']

        houses = ((lookup.get('2nd-and-11th-house') or {}).get('details') or {})
        second = houses.get('second') if isinstance(houses.get('second'), dict) else {}
        eleventh = houses.get('eleventh') if isinstance(houses.get('eleventh'), dict) else {}
        av = lookup.get('Ashtakavarga-wealth') or {}
        dhana = lookup.get('Dhana-yoga-full-reading') or {}

        second_label = second.get('planets_label') or '无'
        second_sign = second.get('sign') or '未知'
        eleventh_label = eleventh.get('planets_label') or '无'
        eleventh_sign = eleventh.get('sign') or '未知'
        manifestation_core = self._strip_humanized_prefix(humanized.get('manifestation_mode'))
        dhana_yogas = (((dhana.get('details') or {}).get('yogas')) or [])
        dhana_texts = [
            str(row.get('interpretation') or '').strip()
            for row in dhana_yogas
            if isinstance(row, dict) and str(row.get('interpretation') or '').strip()
        ]
        risk_lines = self._matching_strict_lines(risks, ['wealth_convergence', 'Shadbala', '时间证据不足'])
        boundary_lines = self._matching_strict_lines(boundaries, ['D2/D11', '官方财富日窗口', '时间置信度'])

        axes = [
            {
                'axis': '收入兑现',
                'judgement': self._join_adjudication_parts([
                    f"收入兑现这一轴，要先看第2宫与第11宫：第2宫在{second_sign}且有{second_label}，第11宫在{eleventh_sign}且{eleventh_label}。",
                    f"所以财富并不是纯抽象的“有财没财”，而是收入、积累与收益网络怎么落地的问题。",
                    dhana_texts[0] if dhana_texts else '',
                    f"当前月度主状态是{humanized.get('primary_state')}，说明线索在起，但还不是立刻把全年收入上限一次性坐实。",
                    f"时间边界：{humanized.get('time_confidence')}",
                ]),
                'evidence_anchor': ['2nd-and-11th-house', 'Dhana-yoga-full-reading', 'Finance-strict-narrative'],
            },
            {
                'axis': '现金流节奏',
                'judgement': self._join_adjudication_parts([
                    "现金流节奏这一轴，比总资产量级更值得先看。",
                    str(av.get('conclusion') or ''),
                    f"严格链已经把当前落地形式定义成{manifestation_core}，所以这阶段更适合盯定金、回款、分期进账、项目进度款，而不是先幻想一次性大额沉淀。",
                    f"时间边界：{humanized.get('time_confidence')}",
                ]),
                'evidence_anchor': ['Ashtakavarga-wealth', 'Finance-strict-narrative'],
            },
            {
                'axis': '合作分账',
                'judgement': self._join_adjudication_parts([
                    "合作分账这一轴，重点不在“有没有人给钱”，而在“钱以什么合作结构进来、最后能留下多少”。",
                    dhana_texts[1] if len(dhana_texts) > 1 else (dhana_texts[0] if dhana_texts else ''),
                    "这更像依托合作、技能输出、项目撮合或资源交换来形成收入，而不是完全脱离人脉与协作的独立孤立进账。",
                    boundary_lines[1] if len(boundary_lines) > 1 else '',
                    f"时间边界：{humanized.get('time_confidence')}",
                ]),
                'evidence_anchor': ['Dhana-yoga-full-reading', 'Finance-strict-narrative'],
            },
            {
                'axis': '风险留存',
                'judgement': self._join_adjudication_parts([
                    "风险留存这一轴，是当前财富判断必须保守的地方。",
                    risk_lines[0] if risk_lines else '',
                    risk_lines[1] if len(risk_lines) > 1 else '',
                    f"置信上限：{self._confidence_cap_cn(confidence_cap)}。" if confidence_cap else '',
                    "因此这轮更适合把财富理解为现金流和结构在动，而不是把它夸大成稳定高留存已经形成。",
                    f"时间边界：{humanized.get('time_confidence')}",
                ]),
                'evidence_anchor': ['Finance-strict-narrative'],
            },
        ]
        return axes

    def _interpretation_axes_for_theme(self, theme_name):
        mapping = {
            'career': ['角色定位', '项目合作', '组织权责', '迁移动向'],
            'marriage': ['关系推进', '对象筛选', '公开化程度', '承诺边界'],
            'wealth': ['收入兑现', '现金流节奏', '合作分账', '风险留存'],
        }
        axes = mapping.get(theme_name, ['主轴判断', '次轴验证', '现实阻力', '时间边界'])
        return [{'axis': axis} for axis in axes]

    def _strict_interpretation_axes_for_theme(self, theme_name, report_payload, humanized):
        builder_map = {
            'career': self._career_axis_judgements,
            'marriage': self._marriage_axis_judgements,
            'wealth': self._wealth_axis_judgements,
        }
        builder = builder_map.get(theme_name)
        if builder:
            return builder(report_payload, humanized)
        return self._interpretation_axes_for_theme(theme_name)

    def _theme_strict_audit_gate(self, theme_name, report_payload):
        if not isinstance(report_payload, dict):
            return {}
        direct = report_payload.get('technique_audit_summary')
        if isinstance(direct, dict) and direct:
            return direct
        evidence = report_payload.get('evidence')
        if not isinstance(evidence, list):
            return {}
        strict_prefix = {
            'career': 'Career-strict-narrative',
            'marriage': 'Relationship-strict-narrative',
            'wealth': 'Finance-strict-narrative',
        }.get(theme_name)
        for item in evidence:
            if not isinstance(item, dict):
                continue
            if strict_prefix and item.get('technique') != strict_prefix:
                continue
            details = item.get('details')
            if isinstance(details, dict):
                gate = details.get('technique_audit_summary')
                if isinstance(gate, dict) and gate:
                    return gate
        return {}

    def _apply_monthly_adjudication_to_theme_report(self, theme_name, report_payload):
        if not isinstance(report_payload, dict):
            return report_payload
        monthly_frame = self._strict_monthly_frame_from_theme_report(report_payload)
        if not monthly_frame:
            return report_payload

        primary_state = (monthly_frame.get('primary_state') or {}).get('value')
        manifestation_mode = (monthly_frame.get('manifestation_mode') or {}).get('value')
        friction_source = (monthly_frame.get('friction_source') or {}).get('value')
        time_confidence = (monthly_frame.get('time_confidence') or {}).get('value')
        humanized = self._humanize_monthly_adjudication(
            theme_name,
            primary_state,
            manifestation_mode,
            friction_source,
            time_confidence,
        )
        axes = self._strict_interpretation_axes_for_theme(theme_name, report_payload, humanized)
        strict_audit_gate = self._theme_strict_audit_gate(theme_name, report_payload)
        narrative_contract = {
            'theme': theme_name,
            'monthly_frame_applied': True,
        }
        strict_bundle = {
            'theme': theme_name,
            'monthly_adjudication_summary': monthly_frame,
            'monthly_adjudication_summary_humanized': humanized,
            'strict_audit_gate': strict_audit_gate,
            'interpretation_axes': axes,
            'narrative_contract': narrative_contract,
        }

        summary = str(report_payload.get('summary') or '')
        summary_parts = [summary] if summary else []
        if humanized.get('primary_state'):
            summary_parts.append(f"月度主状态：{humanized.get('primary_state')}。")
        if humanized.get('manifestation_mode'):
            summary_parts.append(f"落地形式：{humanized.get('manifestation_mode')}。")
        report_payload['summary'] = " ".join(part for part in summary_parts if part).strip()

        narrative = str(report_payload.get('narrative') or '')
        narrative_parts = [narrative] if narrative else []
        if humanized.get('friction_source'):
            narrative_parts.append(f"阻力来源：{humanized.get('friction_source')}。")
        if humanized.get('time_confidence'):
            narrative_parts.append(f"时间置信度：{humanized.get('time_confidence')}。")
        report_payload['narrative'] = " ".join(part for part in narrative_parts if part).strip()

        recommendations = report_payload.get('recommendations')
        if isinstance(recommendations, list):
            enriched_recommendations = list(recommendations)
            monthly_recommendation_parts = []
            if humanized.get('primary_state'):
                monthly_recommendation_parts.append(f"月度主状态：{humanized.get('primary_state')}。")
            if humanized.get('manifestation_mode'):
                monthly_recommendation_parts.append(f"落地形式：{humanized.get('manifestation_mode')}。")
            if humanized.get('friction_source'):
                monthly_recommendation_parts.append(f"阻力来源：{humanized.get('friction_source')}。")
            if humanized.get('time_confidence'):
                monthly_recommendation_parts.append(f"时间置信度：{humanized.get('time_confidence')}。")
            if monthly_recommendation_parts:
                enriched_recommendations.append(" ".join(monthly_recommendation_parts))
            if axes:
                enriched_recommendations.append(
                    "本轮重点拆成：" + "、".join(str(item.get('axis')) for item in axes[:4]) + "。"
                )
            report_payload['recommendations'] = enriched_recommendations

        report_payload['monthly_adjudication_summary'] = monthly_frame
        report_payload['monthly_adjudication_summary_humanized'] = humanized
        report_payload['interpretation_axes'] = axes
        report_payload['strict_adjudication_bundle'] = strict_bundle
        report_payload['strict_audit_gate'] = strict_audit_gate
        report_payload['narrative_contract'] = narrative_contract
        report_payload['summary'] = report_payload['summary'].replace('。。', '。')
        report_payload['narrative'] = report_payload['narrative'].replace('。。', '。')
        if isinstance(report_payload.get('recommendations'), list):
            report_payload['recommendations'] = [
                str(item).replace('。。', '。')
                for item in report_payload['recommendations']
            ]
        return report_payload

    def _theme_house_snapshot(self, chart_data, house_num):
        houses = chart_data.get('houses') if isinstance(chart_data.get('houses'), dict) else {}
        house = houses.get(house_num) or houses.get(str(house_num)) or {}
        asc = chart_data.get('ascendant') if isinstance(chart_data.get('ascendant'), dict) else {}
        if house.get('sign'):
            sign = house.get('sign')
        else:
            asc_idx = self._sign_idx_from_value(asc.get('sign_idx', asc.get('sign')), 0)
            sign = SIGNS[(asc_idx + house_num - 1) % 12]
        planets = []
        for planet, pdata in (chart_data.get('planets') or {}).items():
            if isinstance(pdata, dict) and pdata.get('house') == house_num:
                planets.append(planet)
        return {
            'house': house_num,
            'sign': sign,
            'planets': planets,
            'planets_label': '、'.join(planets) if planets else '无',
        }

    def _top_shadbala_planet(self, shadbala):
        if not isinstance(shadbala, dict):
            return None
        result = shadbala.get('result') if isinstance(shadbala.get('result'), dict) else shadbala
        planets = result.get('planets') if isinstance(result, dict) else {}
        rows = []
        for planet, data in (planets or {}).items():
            if not isinstance(data, dict):
                continue
            rupas = data.get('total_rupas', data.get('rupas'))
            if isinstance(rupas, (int, float)):
                rows.append({'planet': planet, 'rupas': round(rupas, 2)})
        rows.sort(key=lambda row: row['rupas'], reverse=True)
        return rows[0] if rows else None

    def _ashtakavarga_summary_for_theme(self, ashtakavarga):
        if not isinstance(ashtakavarga, dict):
            return {}
        summary = ashtakavarga.get('summary')
        if isinstance(summary, dict) and summary:
            return summary
        sav = ashtakavarga.get('sav') if isinstance(ashtakavarga.get('sav'), dict) else {}
        scores = sav.get('scores') if isinstance(sav.get('scores'), dict) else {}
        if not scores:
            return {}
        rows = []
        for sign, score in scores.items():
            if not isinstance(score, (int, float)):
                continue
            sign_idx = SIGNS.index(sign) if sign in SIGNS else None
            house = sign_idx + 1 if sign_idx is not None else None
            rows.append({'sign': sign, 'house': house, 'score': score})
        rows.sort(key=lambda row: row['score'], reverse=True)
        total = sum(row['score'] for row in rows)
        return {
            'headline': 'Ashtakavarga SAV 已由 full-reading 计算，财富宫位以第2/11宫支持度为重点。',
            'strongest_houses': rows[:4],
            'sav_total': total,
            'source': 'full_reading.modules.ashtakavarga',
        }

    def _extract_jaimini_karakamsha(self, jaimini):
        if not isinstance(jaimini, dict):
            return {}
        result = jaimini.get('result') if isinstance(jaimini.get('result'), dict) else jaimini
        karakamsha = result.get('karakamsha') if isinstance(result, dict) else {}
        return karakamsha if isinstance(karakamsha, dict) else {}

    def _extract_vimsamsa_spiritual_context(self, full_modules):
        if not isinstance(full_modules, dict):
            return {}
        varga = full_modules.get('varga_full')
        if not isinstance(varga, dict):
            return {}
        d20 = varga.get('D20_Vimsamsa') or varga.get('D20') or varga.get('Vimsamsa')
        if not isinstance(d20, dict):
            return {}
        placements = []
        for planet in ('Jupiter', 'Ketu', 'Moon', 'Sun', 'Ascendant'):
            pdata = d20.get(planet)
            if isinstance(pdata, dict):
                placements.append({
                    'planet': planet,
                    'sign': pdata.get('sign'),
                    'house': pdata.get('house') or pdata.get('house_in_d20'),
                    'dignity': pdata.get('dignity'),
                })
        if not placements:
            return {}
        return {
            'summary': 'D20 Vimsamsa 已从 full-reading 分盘层读取，Jupiter/Ketu/Moon/Sun/Ascendant 作为灵性主题侧证。',
            'placements': placements,
            'source': 'full_reading.modules.varga_full',
        }

    def _first_text_from_dict(self, value, keys):
        if not isinstance(value, dict):
            return ''
        for key in keys:
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                return item.strip()
            if isinstance(item, dict):
                nested = self._first_text_from_dict(item, keys)
                if nested:
                    return nested
        return ''

    def _thematic_dasha_info(self, chart, dasha):
        current = {}
        if isinstance(chart.get('dasha'), dict):
            current.update(chart['dasha'])
        analysis = dasha.get('vimshottari_analysis') if isinstance(dasha, dict) else None
        if isinstance(analysis, dict):
            md = ((analysis.get('current') or {}).get('mahadasha') or {}).get('lord')
            ad = ((analysis.get('current') or {}).get('antardasha') or {}).get('lord')
            if md:
                current['maha_dasha'] = md
            if ad:
                current['antar_dasha'] = ad
        return current

    def _parse_birth_datetime(self, body):
        year = self._get_int(body, 'year', 1990, 1800, 2400)
        month = self._get_int(body, 'month', 6, 1, 12)
        day = self._get_int(body, 'day', 15, 1, 31)
        hour = self._get_float(body, 'hour', 12, 0, 23)
        minute = self._get_float(body, 'minute', 0, 0, 59)
        second = self._get_birth_second(body)
        try:
            return datetime(year, month, day, int(hour), int(minute), int(second))
        except ValueError as e:
            raise BadRequest('Invalid birth date') from e

    def _compute_full_reading_for_thematic(self, body):
        engine = _load_local_module('jyotish_engine')
        year = self._get_int(body, 'year', 1990, 1800, 2400)
        month = self._get_int(body, 'month', 6, 1, 12)
        day = self._get_int(body, 'day', 15, 1, 31)
        hour = self._get_float(body, 'hour', 12, 0, 23)
        minute = self._get_float(body, 'minute', 0, 0, 59)
        second = self._get_birth_second(body)
        lat = self._get_float(body, 'lat', 39.9, -90, 90)
        lon = self._get_float(body, 'lon', 116.4, -180, 180)
        tz = self._parse_timezone(body, lat, lon, year, month, day, hour, minute, second)
        try:
            datetime(year, month, day, int(hour), int(minute), int(second))
        except ValueError as e:
            raise BadRequest('Invalid birth date') from e

        node_mode = body.get('node_mode', body.get('nodeMode', 'mean'))
        if not isinstance(node_mode, str) or node_mode not in {'mean', 'true'}:
            node_mode = 'mean'

        args = type('Args', (), {
            'year': year,
            'month': month,
            'day': day,
            'hour': int(hour),
            'minute': int(minute),
            'second': int(second),
            'lat': lat,
            'lon': lon,
            'tz': tz,
            'node_mode': node_mode,
            'ayanamsa': body.get('ayanamsa', 'lahiri'),
            'age': body.get('age'),
            'today': body.get('today') or body.get('current_date'),
            'transit_date': body.get('transit_date'),
            'target_year': body.get('target_year'),
        })()
        result = engine.cmd_full_reading(args)
        if not isinstance(result, dict) or not isinstance(result.get('modules'), dict):
            raise BadRequest('full-reading did not return modules')
        return result

    def _chart_from_full_reading(self, full_reading):
        if not isinstance(full_reading, dict):
            return None
        modules = full_reading.get('modules') if isinstance(full_reading.get('modules'), dict) else {}
        chart = full_reading.get('chart') if isinstance(full_reading.get('chart'), dict) else modules.get('chart')
        if not isinstance(chart, dict) or not isinstance(chart.get('planets'), dict):
            return None
        normalized = dict(chart)
        normalized['success'] = True
        normalized['planets'] = chart.get('planets') or {}
        normalized['ascendant'] = chart.get('ascendant') or SAMPLE_ASCENDANT
        normalized['houses'] = chart.get('houses') or modules.get('house_map') or {}
        normalized['dasha'] = modules.get('dasha') or chart.get('dasha') or {}
        yoga_module = modules.get('yoga') if isinstance(modules.get('yoga'), dict) else {}
        normalized['yogas'] = (
            chart.get('yogas')
            or yoga_module.get('yogas')
            or yoga_module.get('detected_yogas')
            or []
        )
        normalized['ashtakavarga'] = modules.get('ashtakavarga') or chart.get('ashtakavarga') or {}
        normalized['shadbala'] = modules.get('shadbala') or chart.get('shadbala') or {}
        normalized['birth'] = chart.get('birth_info') or full_reading.get('birth_info') or {}
        normalized['source'] = 'full_reading.modules.chart'
        return normalized

    def _sign_idx_from_value(self, value, default=0):
        if isinstance(value, str):
            if value not in SIGNS:
                raise BadRequest('sign must be a valid sign')
            return SIGNS.index(value)
        try:
            idx = int(value)
        except (TypeError, ValueError):
            return default
        return max(0, min(11, idx))

    def _planet_lon(self, planets, planet):
        data = planets.get(planet, {}) if isinstance(planets, dict) else {}
        if not isinstance(data, dict):
            return None
        lon = data.get('lon')
        if isinstance(lon, (int, float)) and math.isfinite(lon):
            return lon % 360
        sign_idx = data.get('sign_idx')
        if sign_idx is None and data.get('sign') in SIGNS:
            sign_idx = SIGNS.index(data['sign'])
        degree = data.get('degree', data.get('degree_in_sign', 0))
        try:
            return (int(sign_idx) * 30 + float(degree)) % 360
        except (TypeError, ValueError):
            return None

    def _fallback_dasha_periods(self, birth_dt, dasha_key, info):
        extended_dashas = _load_local_module('extended_dashas')
        DASHA_ORDER = extended_dashas.DASHA_ORDER
        cycle_years = float(info.get('years') or 36)
        if cycle_years <= 0:
            cycle_years = 36
        period_years = round(cycle_years / len(DASHA_ORDER), 2)
        periods = []
        current = birth_dt
        for lord in DASHA_ORDER:
            end_date = current + timedelta(days=period_years * 365.25636)
            periods.append({
                'lord': lord,
                'years': period_years,
                'start': current.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
            })
            current = end_date
        return periods

    def _import_chart_text(self, body):
        filename = str(body.get('filename', ''))[:160]
        text = body.get('text')
        content_b64 = body.get('content_base64')
        if text is not None:
            if not isinstance(text, str):
                raise BadRequest('text must be a string')
            return self._import_text_response(text, filename, 'text')
        if content_b64 is None:
            raise BadRequest('text or content_base64 is required')
        if not isinstance(content_b64, str):
            raise BadRequest('content_base64 must be a string')
        try:
            data = base64.b64decode(content_b64, validate=True)
        except Exception as e:
            raise BadRequest('Invalid base64 content') from e
        if len(data) > MAX_IMPORT_FILE_BYTES:
            raise BadRequest(f'Import file too large; max {MAX_IMPORT_FILE_BYTES} bytes')
        is_pdf = filename.lower().endswith('.pdf') or data.startswith(b'%PDF')
        if is_pdf:
            text, extractor = self._extract_pdf_text(data)
        else:
            text = data.decode('utf-8', errors='ignore')
            extractor = 'text'
        return self._import_text_response(text, filename, extractor)

    def _import_text_response(self, text, filename, extractor):
        normalized = str(text or '').replace('\x00', '').strip()
        if not normalized:
            raise BadRequest('No extractable text found')
        truncated = len(normalized) > MAX_IMPORT_TEXT_CHARS
        if truncated:
            normalized = normalized[:MAX_IMPORT_TEXT_CHARS]
        return {
            'success': True,
            'filename': filename,
            'extractor': extractor,
            'text': normalized,
            'text_length': len(normalized),
            'truncated': truncated,
        }

    def _extract_pdf_text(self, data):
        errors = []
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                text = '\n'.join((page.extract_text() or '') for page in pdf.pages[:12])
            if text.strip():
                return text, 'pdfplumber'
        except Exception as e:
            errors.append(str(e))
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            text = '\n'.join((page.extract_text() or '') for page in reader.pages[:12])
            if text.strip():
                return text, 'pypdf'
        except Exception as e:
            errors.append(str(e))
        raise BadRequest('PDF has no extractable text; OCR is not supported yet')

    def _compute_chart(self, body):
        if body.get('async') or body.get('enqueue'):
            return self._enqueue_chart_job(body)
        return self._compute_chart_sync(body)

    def _enqueue_chart_job(self, body):
        body_copy = dict(body or {})
        body_copy.pop('async', None)
        body_copy.pop('enqueue', None)
        return self._enqueue_async_job(
            scope=_API_CHART_CACHE_SCOPE,
            endpoint='chart_async',
            job_prefix='chart',
            poll_base='/api/chart/jobs',
            compute_fn=lambda: self._compute_chart_sync(body_copy),
        )

    def _compute_chart_sync(self, body):
        """完整星盘计算"""
        cache_payload = _build_api_chart_cache_payload(body)
        cached_result = _load_api_chart_response_cache(cache_payload)
        if isinstance(cached_result, dict):
            return cached_result

        year = self._get_int(body, 'year', 1990, 1800, 2400)
        month = self._get_int(body, 'month', 6, 1, 12)
        day = self._get_int(body, 'day', 15, 1, 31)
        hour = self._get_float(body, 'hour', 12, 0, 23)
        minute = self._get_float(body, 'minute', 0, 0, 59)
        second = self._get_birth_second(body)
        lat = self._get_float(body, 'lat', 39.9, -90, 90)
        lon = self._get_float(body, 'lon', 116.4, -180, 180)
        tz = self._parse_timezone(body, lat, lon, year, month, day, hour, minute, second)
        try:
            datetime(year, month, day, int(hour), int(minute), int(second))
        except ValueError as e:
            raise BadRequest('Invalid birth date') from e

        try:
            calculation_service = _load_local_module('domain_calculation_service')
            canonical_chart = calculation_service.compute_chart({
                'year': year,
                'month': month,
                'day': day,
                'hour': hour,
                'minute': minute,
                'second': second,
                'lat': lat,
                'lon': lon,
                'tz': tz,
                'ayanamsa': body.get('ayanamsa', 'lahiri'),
                'node_mode': body.get('node_mode', body.get('nodeMode', 'mean')),
            })
            canonical_birth = canonical_chart['birth_info']
            planets_data = canonical_chart['planets']
            ascendant_data = canonical_chart['ascendant']
            asc_lon = float(ascendant_data['lon'])
            asc_sign = ascendant_data['sign']
            asc_sign_idx = SIGNS.index(asc_sign)
            birth_hour_decimal = self._birth_hour_decimal(hour, minute, second)
            jd = float(canonical_birth['julian_day'])
            ayanamsa = float(canonical_birth['ayanamsa'])
            ayanamsa_name = canonical_birth['ayanamsa_name']
            ayanamsa_display = canonical_birth['ayanamsa_display']

            houses = {}
            for h in range(1, 13):
                house = canonical_chart.get('houses', {}).get(f'house_{h}', {})
                sign = house.get('cusp_sign', SIGNS[(asc_sign_idx + h - 1) % 12])
                houses[h] = {
                    'sign': sign,
                    'sign_idx': SIGNS.index(sign),
                    'cusp_degree': house.get('cusp_degree'),
                }

            moon_lon = float(planets_data['Moon']['lon'])
            birth_dt = datetime(year, month, day, int(hour), int(minute), int(second))
            canonical_dasha = calculation_service.compute_vimshottari_timeline(
                birth_dt=birth_dt,
                moon_lon=moon_lon,
                current_date=birth_dt,
            )
            dasha_balance = canonical_dasha['birth_balance']
            md_lord = dasha_balance['lord']
            remaining = dasha_balance['remaining_years']
            total_years = canonical_dasha['periods'][0]['years']
            dasha_start = datetime.strptime(canonical_dasha['periods'][0]['start'], '%Y-%m-%d')

            yogas = self._detect_yogas(planets_data, asc_sign_idx)
            reference_date = (
                body.get('transit_date')
                or body.get('today')
                or body.get('current_date')
                or datetime.now().strftime('%Y-%m-%d')
            )
            sade_sati = calculation_service.compute_sade_sati(
                moon_degree=moon_lon,
                asc_degree=asc_lon,
                reference_date=reference_date,
                tz=tz,
                ayanamsa=ayanamsa_name,
            )

            # Dasha清单
            extended_dashas = _load_local_module('extended_dashas')
            dashas = extended_dashas.get_available_dashas()
            dasha_list = [{'key': k, 'name': extended_dashas.DASHA_REGISTRY[k]['name'], 'years': extended_dashas.DASHA_REGISTRY[k]['years'], 'type': extended_dashas.DASHA_REGISTRY[k]['type']} for k in dashas]

            try:
                jaimini = _load_local_module('jaimini')
                special_lagnas = jaimini.calc_special_lagnas_precise(
                    asc_sign_idx, year, month, day, int(hour), minute + second / 60.0, lat, lon, tz
                )
            except Exception as e:
                import logging
                logging.warning(f"[api_server] special lagnas calculation failed: {e}")
                special_lagnas = {}

            # Shadbala (v6.9.15: absolute component sum, no global 1200 downscaling)
            try:
                from shadbala import calc_shadbala
                sb = calc_shadbala(
                    planets_data,
                    asc_sign,
                    birth_hour_decimal,
                    planets_data.get('Sun',{}).get('lon',0),
                    moon_lon,
                )
                shadbala_summary = {p: {'rupas': round(d['total_rupas'],2), 'level': d['strength_level']} 
                    for p,d in sb.get('planets',{}).items()}
            except Exception as e:
                import logging
                logging.warning(f"[api_server] shadbala calculation failed: {e}")
                shadbala_summary = {}

            try:
                remedies_module = _load_local_module('remedies')
                remedies = remedies_module.recommend_remedies(shadbala_summary, active_dasha_lord=md_lord)
            except Exception as e:
                import logging
                logging.warning(f"[api_server] remedies calculation failed: {e}")
                remedies = {}

            try:
                tithi_analyzer = _load_local_module('tithi_analyzer')
                tithi_lord_analysis = tithi_analyzer.analyze_tithi({'planets': planets_data})
            except Exception as e:
                import logging
                logging.warning(f"[api_server] tithi lord analysis failed: {e}")
                tithi_lord_analysis = {}

            # Yoga扩展 (dashaflow MIT规则)
            try:
                from yoga_expansion import detect_all_yogas as detect_ey
                for ey in detect_ey(planets_data, asc_sign):
                    yogas.append({'name': ey.get('name',''), 'planets': ey.get('planets',[]),
                                  'desc': ey.get('description','')[:80], 'cat': 'extended'})
            except Exception as e:
                import logging
                logging.warning(f"[api_server] yoga expansion detection failed: {e}")
            result = {
                'success': True, 'version': '6.9.15',
                'birth': {
                    'date': f'{year}-{month:02d}-{day:02d}',
                    'time': self._format_birth_time(hour, minute, second),
                    'hour': int(hour),
                    'minute': int(minute),
                    'second': int(second),
                    'tz': f"UTC{'+' if tz >= 0 else ''}{tz}",
                    'lat': lat,
                    'lon': lon,
                    'julian_day': round(jd, 6),
                    'ayanamsa': round(ayanamsa, 4),
                    'ayanamsa_name': ayanamsa_name,
                    'ayanamsa_display': ayanamsa_display,
                    'node_mode': canonical_chart['calculation_contract']['effective']['node_mode'],
                },
                'ascendant': {
                    'sign': asc_sign,
                    'sign_idx': asc_sign_idx,
                    'degree': round(asc_lon % 30, 2),
                    'degree_in_sign': round(asc_lon % 30, 2),
                    'lon': round(asc_lon, 4),
                },
                'planets': planets_data, 'houses': houses, 'shadbala': shadbala_summary,
                'dasha': {
                    'current_md': md_lord,
                    'remaining_years': round(remaining, 2),
                    'total_years': total_years,
                    'start_date': dasha_start.isoformat() if hasattr(dasha_start, 'isoformat') else str(dasha_start),
                    'periods': canonical_dasha['periods'],
                    'birth_balance': canonical_dasha['birth_balance'],
                    'calculation_contract': canonical_dasha['calculation_contract'],
                    'result_hash': canonical_dasha['result_hash'],
                },
                'yogas': yogas,
                'sade_sati': sade_sati,
                'remedies': remedies,
                'tithi_lord_analysis': tithi_lord_analysis,
                'special_lagnas': special_lagnas,
                'available_dashas': dasha_list,
                'dasha_count': len(dasha_list),
                'calculation_contract': canonical_chart['calculation_contract'],
                'result_hash': canonical_chart['result_hash'],
            }
            result['modules'] = {
                'chart': {
                    'planets': result['planets'],
                    'ascendant': result['ascendant'],
                    'houses': result['houses'],
                    'birth_info': result['birth'],
                    'calculation_contract': result['calculation_contract'],
                    'result_hash': result['result_hash'],
                },
                'dasha': result['dasha'],
                'shadbala': {'planets': sb.get('planets', {})} if 'sb' in locals() and isinstance(sb, dict) else {},
            }
            _attach_vedastro_main_entry_overview(result, {
                'year': year,
                'month': month,
                'day': day,
                'hour': int(hour),
                'minute': int(minute),
                'second': int(second),
                'lat': lat,
                'lon': lon,
                'tz': tz,
                'ayanamsa': ayanamsa_name,
                'node_mode': body.get('node_mode', body.get('nodeMode', 'mean')),
                'today': body.get('today') or body.get('current_date'),
                'transit_date': body.get('transit_date'),
            })
            _attach_guided_topics(result)
            result['ai_prompt_pack'] = self._build_chart_prompt_pack(result)
            return _store_api_chart_response_cache(cache_payload, result)
        except ImportError:
            fallback = self._fallback_chart(year, month, day, hour, minute, second, lat, lon, tz)
            return _store_api_chart_response_cache(cache_payload, fallback)

    def _fallback_chart(self, year, month, day, hour, minute, second, lat, lon, tz):
        """无Swiss Ephemeris时的简化计算"""
        import hashlib
        seed = int(hashlib.md5(f"{year}{month}{day}{hour}{minute}{second}{lat}{lon}".encode()).hexdigest()[:8], 16)
        asc_sign_idx = seed % 12
        asc_sign = SIGNS[asc_sign_idx]

        planets = {}
        planet_names = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']
        import random
        rng = random.Random(seed)
        for pn in planet_names:
            sign_idx = (asc_sign_idx + rng.randint(0, 11)) % 12
            deg = rng.uniform(0, 30)
            planets[pn] = {
                'sign': SIGNS[sign_idx], 'sign_idx': sign_idx,
                'degree': deg, 'lon': sign_idx * 30 + deg,
                'house': ((sign_idx - asc_sign_idx) % 12) + 1,
            }

        houses = {}
        for h in range(1, 13):
            s = (asc_sign_idx + h - 1) % 12
            houses[h] = {'sign': SIGNS[s], 'sign_idx': s}

        try:
            jaimini = _load_local_module('jaimini')
            special_lagnas = jaimini.calc_special_lagnas_precise(
                asc_sign_idx, year, month, day, int(hour), minute + second / 60.0, lat, lon, tz
            )
        except Exception:
            jaimini = _load_local_module('jaimini')
            special_lagnas = jaimini.calc_special_lagnas(asc_sign_idx, int(hour), minute + second / 60.0)

        result = {
            'success': True, 'version': '6.9.15-fallback',
            'warning': 'Swiss Ephemeris未安装，使用简化计算',
            'birth': {
                'date': f'{year}-{month:02d}-{day:02d}',
                'time': self._format_birth_time(hour, minute, second),
                'hour': int(hour),
                'minute': int(minute),
                'second': int(second),
                'tz': f"UTC{'+' if tz >= 0 else ''}{tz}",
                'lat': lat,
                'lon': lon,
            },
            'ascendant': {'sign': asc_sign, 'sign_idx': asc_sign_idx},
            'planets': planets, 'houses': houses,
            'dasha': {'current_md': 'Moon', 'remaining_years': 5},
            'yogas': [], 'sade_sati': {'active': False},
            'tithi_lord_analysis': _load_local_module('tithi_analyzer').analyze_tithi({'planets': planets}),
            'special_lagnas': special_lagnas,
            'available_dashas': [], 'dasha_count': 0,
        }
        result['modules'] = {
            'chart': {
                'planets': result['planets'],
                'ascendant': result['ascendant'],
                'houses': result['houses'],
                'birth_info': result['birth'],
            },
            'dasha': result['dasha'],
            'shadbala': {},
        }
        _attach_vedastro_main_entry_overview(result, {
            'year': year,
            'month': month,
            'day': day,
            'hour': int(hour),
            'minute': int(minute),
            'second': int(second),
            'lat': lat,
            'lon': lon,
            'tz': tz,
            'ayanamsa': 'lahiri',
            'node_mode': 'mean',
        })
        _attach_guided_topics(result)
        result['ai_prompt_pack'] = self._build_chart_prompt_pack(result)
        return result

    def _build_chart_prompt_pack(self, chart):
        birth = chart.get('birth') or chart.get('birth_info') or {}
        ascendant = chart.get('ascendant') or {}
        planets = chart.get('planets') or {}
        dasha = chart.get('dasha') or {}
        shadbala = chart.get('shadbala') or {}
        functional_layer = self._functional_benefic_malefic_snapshot(planets, ascendant)
        vedastro_overview = _build_vedastro_overview_payload_from_chart(chart)
        vedastro_official_full_snapshot = _build_vedastro_official_full_snapshot_payload_from_chart(chart)
        _attach_guided_topics(chart)
        modules = chart.get('modules') if isinstance(chart.get('modules'), dict) else {}
        guided_topics = modules.get('guided_topics') if isinstance(modules.get('guided_topics'), list) else []
        try:
            capability_evidence_pool = _load_local_module('capability_evidence_pool').build_capability_evidence_pool_summary()
        except Exception:
            capability_evidence_pool = {
                'scope': 'backend_capability_evidence_pool',
                'total_entries': 0,
                'conclusion_policy': {
                    'all_89_entries_must_not_be_flattened_into_conclusions': True,
                },
            }
        top_strength = sorted(
            [
                {
                    'planet': planet,
                    'rupas': pdata.get('rupas'),
                    'level': pdata.get('level'),
                }
                for planet, pdata in shadbala.items()
                if isinstance(pdata, dict)
            ],
            key=lambda row: row.get('rupas') if isinstance(row.get('rupas'), (int, float)) else -1,
            reverse=True,
        )[:7]
        core_planets = {
            planet: {
                'source': pdata.get('source'),
                'sign': pdata.get('sign'),
                'degree': pdata.get('degree'),
                'degree_in_sign': pdata.get('degree_in_sign'),
                'house': pdata.get('house'),
                'lon': pdata.get('lon'),
                'vargas': pdata.get('vargas'),
            }
            for planet, pdata in planets.items()
            if planet in {'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'}
            and isinstance(pdata, dict)
        }
        ayanamsa_display = birth.get('ayanamsa_display') or 'Lahiri'
        node_mode = birth.get('node_mode') or 'mean'
        prompt_lines = [
            '你是一个审慎的 AI Native 印度/吠陀占星分析助手。',
            '请只基于 evidence_snapshot 中的计算证据生成解读，不要编造星盘不存在的配置。',
            f'本盘使用 {ayanamsa_display} ayanamsa，节点口径为 {node_mode}。',
            '不要仅凭单一配置下结论；核心判断至少交叉 D1、D9、Dasha、Shadbala/Ashtakavarga 或 Transit 中的两个证据层。',
            '必须显式标注置信度和边界：Dasha/PDF 起点差异、Shadbala 外部绝对值 oracle 尚未完成时，不得声称已经完全校准。',
            'VedAstro 官方全量快照是第一原始证据层；若该层 blocked，必须把本地结果标记为 fallback。',
            '必须按 promise → activation → manifestation → label 输出；每个判断都要说明属于承诺、激活、落地形式还是标签层。',
            '未完成 MEVG / Real Case Calibration 时必须降级或标 blocked，不得把内部一致性写成已验证结论。',
        ]
        oracle_progress = {
            'scope': 'external_oracle_evidence_validation',
            'collection_queue': 'external_oracle_collection_queue',
            'total_packets': 5,
            'valid_packets': 0,
            'ready_for_calibration': 0,
            'production_tuning_allowed': False,
            'artifact_policy': 'references/oracle/artifacts/',
            'promotion_rule': 'external_verified requires source_artifact, filled target values, and non-local-engine external evidence.',
            'boundary': 'Dasha/Shadbala absolute values are not externally calibrated until enough packets pass validation.',
        }
        return {
            'schema_version': 1,
            'mode': 'jyotish_structured_prompt_pack',
            'prompt_zh': '\n'.join(prompt_lines),
            'evidence_snapshot': {
                'birth': birth,
                'ayanamsa': {
                    'name': birth.get('ayanamsa_name', 'lahiri'),
                    'display': ayanamsa_display,
                    'value': birth.get('ayanamsa'),
                    'node_mode': node_mode,
                },
                'core': {
                    'ascendant': ascendant,
                    **core_planets,
                },
                'timing': {
                    'current_mahadasha': dasha.get('current_md') or dasha.get('maha_dasha'),
                    'remaining_years': dasha.get('remaining_years'),
                    'start_date': dasha.get('start_date'),
                },
                'strength': {
                    'shadbala_ranking': top_strength,
                },
                'functional_benefic_malefic': functional_layer,
                'interpretation_source_pack': {
                    'status': 'fallback_prompt_pack_only',
                    'source': 'api_chart_prompt_pack_fallback',
                    'core_rule_source_refs': [
                        'references/prediction-boundary-protocol.md',
                        'references/event_judgment_skeleton.md',
                        'references/planetary-dignity-complete-reference.md',
                        'references/retrograde-combustion-war-guide.md',
                        'references/transit-multi-reference-guide.md',
                    ],
                    'promote_batch2_source_refs': [
                        'references/vimshottari_dasha_guide.md',
                        'references/pratyantar-calculation-guide.md',
                        'references/divisional-chart-deep-reading.md',
                        'references/shadbala-complete-methodology.md',
                        'references/ashtakavarga-complete-system.md',
                        'references/tajika-yoga-complete-guide.md',
                        'references/jaimini-complete-system.md',
                        'references/kp-astrology-complete-system.md',
                        'references/argala-complete-guide.md',
                        'references/badhaka-obstacle-planet-guide.md',
                        'references/condition-dasha-complete.md',
                    ],
                    'reference_only_source_refs': [
                        'references/dasa-convergence-methodology.md',
                        'references/multi-dasha-convergence-protocol.md',
                        'references/yoga-strength-scoring-system.md',
                    ],
                },
                'prediction_boundary_contract': {
                    'status': 'fallback_prompt_pack_only',
                    'source_refs': [
                        'references/prediction-boundary-protocol.md',
                        'references/event_judgment_skeleton.md',
                        'references/planetary-dignity-complete-reference.md',
                        'references/retrograde-combustion-war-guide.md',
                        'references/transit-multi-reference-guide.md',
                    ],
                    'event_judgment_skeleton': {
                        'required_sections': ['promise', 'activation', 'manifestation', 'label'],
                    },
                    'confidence_boundary': {
                        'mevg_status': 'blocked',
                        'real_case_calibration_status': 'blocked',
                        'unverified_claim_policy': 'downgrade_or_block',
                    },
                },
                'domain_invocation_layers': {
                    'dasha_timing': {
                        'status': 'fallback_prompt_pack_only',
                        'source_refs': [
                            'references/vimshottari_dasha_guide.md',
                            'references/pratyantar-calculation-guide.md',
                            'references/condition-dasha-complete.md',
                        ],
                    },
                    'varga_strength': {
                        'status': 'fallback_prompt_pack_only',
                        'source_refs': [
                            'references/divisional-chart-deep-reading.md',
                            'references/shadbala-complete-methodology.md',
                            'references/ashtakavarga-complete-system.md',
                        ],
                    },
                    'annual_special': {
                        'status': 'fallback_prompt_pack_only',
                        'source_refs': [
                            'references/tajika-yoga-complete-guide.md',
                            'references/jaimini-complete-system.md',
                            'references/kp-astrology-complete-system.md',
                        ],
                    },
                    'modifier_obstacle': {
                        'status': 'fallback_prompt_pack_only',
                        'source_refs': [
                            'references/argala-complete-guide.md',
                            'references/badhaka-obstacle-planet-guide.md',
                        ],
                    },
                },
                'output_template_contract': {
                    'status': 'fallback_prompt_pack_only',
                    'language': 'zh',
                    'required_sections': ['promise', 'activation', 'manifestation', 'label', 'confidence_boundary'],
                    'golden_test_status': 'required',
                },
                'mevg_collection_queue': {
                    'status': 'queued',
                    'trigger': 'fortune_question_strict_workflow',
                    'required_jobs': ['global_web_evidence', 'source_grading', 'conflict_arbitration'],
                },
                'real_case_calibration_layer': {
                    'status': 'queued',
                    'domain_buckets': ['career', 'finance', 'relationship', 'health', 'rectification', 'timing'],
                    'source_roots': ['references/real_case_studies', 'docs/benchmark'],
                },
                'technical_debt_contract': {
                    'status': 'tracked',
                    'narayana': {
                        'status': 'partial',
                        'status_breakdown': {
                            'closed': ['mahadasha_present'],
                            'blocked': ['external_oracle_parity_not_closed'],
                        },
                        'open_items': ['antardasha_pratyantar_oracle_parity'],
                    },
                    'tajika': {
                        'status': 'partial',
                        'status_breakdown': {
                            'closed': ['tajika_yoga_reference_layer_visible'],
                            'blocked': ['precise_solar_return_and_muntha_oracle_not_closed'],
                        },
                        'open_items': ['solar_return_precision', 'muntha_placeholder_audit'],
                    },
                    'oracle_parity': {
                        'status': 'blocked',
                        'required_systems': ['VedAstro', 'PyJHora', 'jyotishganit'],
                        'priority_domains': ['Dasha', 'Shadbala', 'Tajika', 'Narayana'],
                    },
                },
                'remaining_priority1_batch_queue': {
                    'status': 'queued',
                    'next_batches': [
                        'real_case_studies_batch1',
                        'rishi_ai_mcp_batch1',
                        'vedic_astro_skills_batch1',
                        'references_batch2',
                    ],
                    'batch_statuses': {
                        'real_case_studies_batch1': 'next',
                        'rishi_ai_mcp_batch1': 'pending',
                        'vedic_astro_skills_batch1': 'pending',
                        'references_batch2': 'pending',
                    },
                },
                'oracle_parity_queue': {
                    'status': 'queued',
                    'systems': ['VedAstro', 'PyJHora', 'jyotishganit'],
                    'priority_domains': ['Dasha', 'Shadbala', 'Tajika', 'Narayana'],
                },
                'release_hygiene_plan': {
                    'status': 'tracked',
                    'git_sync_required': True,
                    'gc_log_policy': 'separate_safe_cleanup_plan_required',
                },
                'vedastro_official_full_snapshot': vedastro_official_full_snapshot,
                'vedastro_overview': vedastro_overview,
                'guided_topics': guided_topics,
                'capability_evidence_pool': capability_evidence_pool,
                'quality_boundary': {
                    'external_oracle_status': 'D1/D9/VedAstro longitude boundary covered; Dasha/Shadbala external absolute calibration still requires multi-source oracle expansion.',
                },
                'oracle_progress': oracle_progress,
            },
            'retrieval_plan': {
                'local_reference_docs': [
                    'references/ai-reading-workflow-prompt.md',
                    'references/comprehensive-reading-workflow.md',
                    'references/prediction-boundary-protocol.md',
                    'references/event_judgment_skeleton.md',
                    'references/planetary-dignity-complete-reference.md',
                    'references/retrograde-combustion-war-guide.md',
                    'references/transit-multi-reference-guide.md',
                    'references/vimshottari_dasha_guide.md',
                    'references/pratyantar-calculation-guide.md',
                    'references/divisional-chart-deep-reading.md',
                    'references/shadbala-complete-methodology.md',
                    'references/ashtakavarga-complete-system.md',
                    'references/tajika-yoga-complete-guide.md',
                    'references/jaimini-complete-system.md',
                    'references/kp-astrology-complete-system.md',
                    'references/argala-complete-guide.md',
                    'references/badhaka-obstacle-planet-guide.md',
                    'references/condition-dasha-complete.md',
                    'references/dasa-convergence-methodology.md',
                    'references/multi-dasha-convergence-protocol.md',
                    'references/yoga-strength-scoring-system.md',
                    'references/shadbala-interpretation-methodology.md',
                    'references/navamsa-d9-interpretation-template.md',
                ],
                'retrieval_tags': [
                    'no_single_factor_conclusion',
                    'd1_d9_dasha_cross_validation',
                    'oracle_boundary_visible',
                    'external_oracle_evidence_validation',
                    'confidence_labeled_reading',
                ],
            },
        }

    def _functional_benefic_malefic_snapshot(self, planets, ascendant):
        try:
            from functional_benefics import derive_functional_benefic_malefic
            asc_sign = ascendant.get('sign')
            return derive_functional_benefic_malefic(asc_sign)
        except Exception as exc:
            return {
                'status': 'blocked',
                'ascendant': ascendant.get('sign'),
                'functional_benefics': [],
                'functional_malefics': [],
                'functional_neutrals': [],
                'yogakarakas': [],
                'owned_houses': {},
                'effect_on_confidence': f'未完成功能性吉凶星判定，需降低高严谨结论置信度: {exc}',
                'source': 'strict_functional_benefic_malefic_v1',
            }

    def _detect_yogas(self, planets, asc_idx):
        yogas = []
        KENDRA = {1,4,7,10}
        try:
            from pancha_mahapurusha import detect_pancha_mahapurusha
            pmc = detect_pancha_mahapurusha(planets)
            for y in pmc:
                if y['is_valid']:
                    yogas.append({'name': y['name'], 'planets': [y['planet']], 'category': 'PMC'})
        except Exception as e:
            import logging
            logging.warning(f"[api_server] pancha_mahapurusha detection failed: {e}")

        try:
            from yoga_expansion import detect_all_yogas as detect_yogas_ext
            for y in detect_yogas_ext(planets, SIGNS[asc_idx]):
                yogas.append({'name': y.get('name',''), 'planets': y.get('planets',[]), 'category': 'extended'})
        except Exception as e:
            import logging
            logging.warning(f"[api_server] yoga expansion in _detect_yogas failed: {e}")

        return yogas[:10]

    def _compute_remedies(self, body):
        remedies_module = _load_local_module('remedies')
        shadbala = body.get('shadbala', {})
        doshas = body.get('doshas', [])
        dasha_lord = body.get('dasha_lord', '')
        if not isinstance(shadbala, dict):
            raise BadRequest('shadbala must be an object')
        if not isinstance(doshas, list):
            raise BadRequest('doshas must be an array')
        if not isinstance(dasha_lord, str):
            raise BadRequest('dasha_lord must be a string')
        return remedies_module.recommend_remedies(shadbala, doshas=doshas, active_dasha_lord=dasha_lord)

    def _compute_kp(self, body):
        planets = self._validate_planets(body.get('planets', {}))
        asc_idx = self._get_int(body, 'asc_sign_idx', 0, 0, 11)
        from kp_system import calc_kp_analysis
        return calc_kp_analysis(planets, SIGNS[asc_idx])

    def _compute_prashna(self, body):
        try:
            from prashna_context import PrashnaContextError, build_prashna_context
        except ModuleNotFoundError:  # pragma: no cover - package import path
            from scripts.prashna_context import PrashnaContextError, build_prashna_context
        if "planets" in body or "asc_degree" in body:
            raise BadRequest("Prashna planets and ascendant are backend-computed; client values are forbidden")
        try:
            context = build_prashna_context(body)
        except PrashnaContextError as exc:
            raise BadRequest(str(exc)) from exc
        return {
            "success": True,
            "status": "computed",
            "prashna_context": context,
            "verdict": {
                "status": "blocked",
                "reason": "Prashna adjudication is disabled until Tajika/Saham/Sphuta kernels pass classic golden cases.",
            },
        }

        # Legacy client-supplied-chart pipeline below is unreachable pending deletion.
        question_type = body.get('question', 'general')
        if not isinstance(question_type, str):
            raise BadRequest('question must be a string')
        question_text = body.get('question_text', '')
        if not isinstance(question_text, str):
            raise BadRequest('question_text must be a string')
        from prashna import (
            QUESTION_CATEGORIES,
            analyze_lost_item,
            build_kp_horary_evidence,
            calc_prashna_chart,
            calc_life_sphutas,
            calc_sahams,
            calc_sphutas,
            detect_prashna_arudha,
            get_kp_prashna_answer,
            get_kp_prashna_answer_v2,
            kunda_verify,
            nadi_prashna_analysis,
            prashna_timing_score,
        )
        from datetime import datetime
        planets = self._validate_planets(body.get('planets', {}))
        asc_degree = self._normalize_degree(body, 'asc_degree', 15.5)
        horary_number = body.get('horary_number')
        if horary_number in ('', None):
            horary_number = None
        else:
            horary_number = self._get_int(body, 'horary_number', None, 1, 249)
        question_key = question_type[:80]
        chart = calc_prashna_chart(datetime.now(), planets, asc_degree)
        answer = get_kp_prashna_answer(planets, question_key, asc_degree)
        answer_v2 = get_kp_prashna_answer_v2(planets, question_key, asc_degree)
        kp_horary = build_kp_horary_evidence(planets, question_key, asc_degree, horary_number)
        question_house = QUESTION_CATEGORIES.get(question_key, QUESTION_CATEGORIES['general'])['primary']
        arudha = detect_prashna_arudha(planets, asc_degree, question_house)
        nadi = nadi_prashna_analysis(planets, asc_degree, question_key)
        timing = prashna_timing_score(planets, asc_degree, question_key)
        planet_lons = {}
        for pname in ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'):
            p_lon = self._planet_lon(planets, pname)
            if p_lon is not None:
                planet_lons[pname] = p_lon
        sphutas = calc_sphutas(planet_lons, asc_degree)
        life_sphutas = calc_life_sphutas(
            asc_degree,
            planet_lons.get('Moon', 0),
            planet_lons.get('Sun', 0),
            sphutas.get('gulika', {}).get('longitude', 0),
        )
        sahams = calc_sahams(planet_lons, asc_degree)
        lost_item = analyze_lost_item(planet_lons, asc_degree)
        kunda = kunda_verify(asc_degree)
        conclusion = answer_v2.get('kp_answer') or answer.get('kp_answer')
        return {
            'success': True,
            'question_text': question_text[:160],
            'question_category': question_key,
            'prashna_chart': chart,
            'kp_answer': answer,
            'kp_answer_v2': answer_v2,
            'kp_horary': kp_horary,
            'arudha': arudha,
            'nadi': nadi,
            'timing': timing,
            'sphutas': sphutas,
            'life_sphutas': life_sphutas,
            'sahams': sahams,
            'lost_item': lost_item,
            'kunda': kunda,
            'summary': {
                'conclusion': conclusion,
                'confidence': answer_v2.get('confidence', answer.get('confidence')),
                'primary_house': question_house,
                'question_lord': answer_v2.get('question_lord', answer.get('question_lord')),
                'next_action': timing.get('recommendation', '结合现实信息复核后再行动'),
            },
        }

    def _compute_synastry(self, body):
        from ashtakoot import calculate_ashtakoot

        result = calculate_ashtakoot(
            self._normalize_degree(body, 'male_moon', 0),
            self._normalize_degree(body, 'female_moon', 0),
        )
        # Backward-compatible aliases for older frontend/report consumers.
        result['is_approved'] = result.get('is_match_approved', False)
        result['assessment'] = (
            '优秀' if result.get('total_score', 0) >= 28 else
            '良好' if result.get('total_score', 0) >= 21 else
            '一般' if result.get('total_score', 0) >= 18 else
            '不推荐'
        )
        result['male'] = result.get('male_details', {})
        result['female'] = result.get('female_details', {})
        return result

    def _compute_dasha_system(self, body):
        dasha_key = body.get('dasha', body.get('name', 'vimshottari'))
        if not isinstance(dasha_key, str):
            raise BadRequest('dasha must be a string')
        dasha_key = dasha_key.strip().lower()
        extended_dashas = _load_local_module('extended_dashas')
        info = extended_dashas.DASHA_REGISTRY.get(dasha_key)
        if not info:
            raise BadRequest('Unknown dasha system')

        birth_dt = self._parse_birth_datetime(body)
        planets = self._validate_planets(body.get('planets', {}))
        ascendant = body.get('ascendant', {})
        if ascendant is not None and not isinstance(ascendant, dict):
            raise BadRequest('ascendant must be an object')

        moon_lon = self._planet_lon(planets, 'Moon')
        if moon_lon is None:
            moon_lon = self._normalize_degree(body, 'moon_lon', 0)
        sun_lon = self._planet_lon(planets, 'Sun')
        if sun_lon is None:
            sun_lon = self._normalize_degree(body, 'sun_lon', 0)

        nak_size = 360 / 27
        moon_nak_idx = int(moon_lon / nak_size) % 27
        moon_pada = int((moon_lon % nak_size) / (nak_size / 4)) + 1
        moon_sign_idx = int(moon_lon / 30) % 12
        sun_sign_idx = int(sun_lon / 30) % 12
        asc_sign_idx = self._sign_idx_from_value(
            body.get('asc_sign_idx', ascendant.get('sign_idx', ascendant.get('sign'))),
            0,
        )
        d9_asc_sign_idx = self._sign_idx_from_value(body.get('d9_asc_sign_idx', asc_sign_idx), asc_sign_idx)
        tithi_num = self._get_int(body, 'tithi_num', 1, 1, 30)

        vimshottari_analysis = None
        canonical_dasha = None
        if dasha_key == 'vimshottari':
            calculation_service = _load_local_module('domain_calculation_service')
            canonical_dasha = calculation_service.compute_vimshottari_timeline(
                birth_dt=birth_dt,
                moon_lon=moon_lon,
                current_date=(
                    self._parse_optional_date(body.get('today') or body.get('current_date'))
                    if body.get('today') or body.get('current_date')
                    else None
                ),
            )
            periods = canonical_dasha['periods']
            precision = 'canonical_birth_balance'
            vimshottari_analysis = self._compute_vimshottari_analysis_layer(
                birth_dt,
                moon_lon,
                body.get('today') or body.get('current_date'),
            )
        else:
            periods = extended_dashas.calc_any_dasha(
                dasha_key,
                birth_dt,
                moon_nak_idx=moon_nak_idx,
                moon_pada=moon_pada,
                asc_sign_idx=asc_sign_idx,
                moon_sign_idx=moon_sign_idx,
                sun_sign_idx=sun_sign_idx,
                d9_asc_sign_idx=d9_asc_sign_idx,
                tithi_num=tithi_num,
            )
            calc_fn = extended_dashas.DASHA_CALCULATORS.get(dasha_key)
            precision = 'generic' if not calc_fn or calc_fn.__name__ == 'calc_generic_dasha' else 'calculator'
        if not periods:
            periods = self._fallback_dasha_periods(birth_dt, dasha_key, info)
            precision = 'generic'

        result = {
            'success': True,
            'key': dasha_key,
            'name': info.get('name', dasha_key),
            'type': info.get('type', 'other'),
            'cycle_years': info.get('years'),
            'precision': precision,
            'periods': periods,
        }
        if vimshottari_analysis:
            result['vimshottari_analysis'] = vimshottari_analysis
            result['fragment_sources'] = ['dasha_analyzer.py', 'dasha_calculator_enhanced.py']
        if canonical_dasha:
            result['birth_balance'] = canonical_dasha['birth_balance']
            result['calculation_contract'] = canonical_dasha['calculation_contract']
            result['result_hash'] = canonical_dasha['result_hash']
        return result

    def _compute_vimshottari_analysis_layer(self, birth_dt, moon_lon, current_date=None):
        try:
            analyzer = _load_local_module('dasha_analyzer')
            enhanced = _load_local_module('dasha_calculator_enhanced')
            nak_info, nak_progress, pada = analyzer.lon_to_nakshatra(moon_lon % 360)
            timeline, elapsed, remaining, start_lord = analyzer.build_dasha_timeline(
                birth_dt.strftime('%Y-%m-%d'),
                nak_info,
                nak_progress,
            )
            today = self._parse_optional_date(current_date) if current_date else datetime.now()
            current_idx, current_md = analyzer.find_current(timeline, today)
            antardashas = analyzer.build_antardasha(current_md)
            current_ad = analyzer.find_current_sub(antardashas, today)
            years_into_md = max(0.0, (today - current_md['start']).days / 365.25636)
            five_levels = enhanced.calculate_five_level_dasha(current_md['lord'], years_into_md)
            formatted_timeline = [self._format_datetime_period(period) for period in timeline]
            formatted_antardashas = [self._format_datetime_period(period) for period in antardashas]
            current_period = self._format_datetime_period(current_md)
            current_sub = self._format_datetime_period(current_ad)
            remaining_days = max(0, (current_ad['end'] - today).days)
            theme = enhanced.PLANET_MODERN_MEANINGS.get(current_md['lord'], {})
            return {
                'source': 'dasha_analyzer.py + dasha_calculator_enhanced.py',
                'nakshatra': {
                    'name': nak_info[0],
                    'lord': nak_info[1],
                    'years': nak_info[2],
                    'pada': pada,
                    'progress_pct': round(nak_progress * 100, 2),
                    'elapsed_years_at_birth': elapsed,
                    'remaining_years_at_birth': remaining,
                },
                'current': {
                    'mahadasha': current_period,
                    'antardasha': current_sub,
                    'remaining_days': remaining_days,
                    'remaining_months': round(remaining_days / 30.44, 1),
                    'theme': theme.get('theme', ''),
                    'keywords': theme.get('keywords', []),
                },
                'five_levels': five_levels,
                'timeline_from_true_md_start': formatted_timeline,
                'current_antardashas': formatted_antardashas,
                'summary': {
                    'headline': f"当前处于 {current_md['lord']} Mahadasha / {current_ad['lord']} Antardasha",
                    'note': '该增强层复用 dasha_analyzer.py，主 periods 合同仍保持出生后周期列表。',
                    'next_action': '用当前 MD/AD 作为时间主轴，再用本命承诺、Transit 和案例验证收敛事件。',
                },
                'current_index': current_idx,
            }
        except Exception as exc:
            import logging
            logging.warning(f"[api_server] vimshottari analysis layer failed: {exc}")
            return None

    def _parse_optional_date(self, value):
        if not isinstance(value, str) or not value.strip():
            raise BadRequest('current_date must be YYYY-MM-DD')
        try:
            return datetime.strptime(value.strip()[:10], '%Y-%m-%d')
        except ValueError as e:
            raise BadRequest('current_date must be YYYY-MM-DD') from e

    def _format_datetime_period(self, period):
        return {
            'lord': period.get('lord'),
            'years': round(period.get('years', 0), 4) if isinstance(period.get('years'), (int, float)) else period.get('years'),
            'start': period.get('start').strftime('%Y-%m-%d') if hasattr(period.get('start'), 'strftime') else period.get('start'),
            'end': period.get('end').strftime('%Y-%m-%d') if hasattr(period.get('end'), 'strftime') else period.get('end'),
        }

    def _compute_sade_sati(self, body):
        calculation_service = _load_local_module('domain_calculation_service')
        reference_date = (
            body.get('reference_date')
            or body.get('transit_date')
            or body.get('current_date')
            or datetime.now().strftime('%Y-%m-%d')
        )
        return calculation_service.compute_sade_sati(
            moon_degree=self._normalize_degree(body, 'moon_degree', 0),
            asc_degree=self._normalize_degree(body, 'asc_degree', 0),
            reference_date=reference_date,
            tz=self._get_float(body, 'tz', 0, -14, 14),
            ayanamsa=body.get('ayanamsa', 'lahiri'),
        )

    def _compute_pmc(self, body):
        from pancha_mahapurusha import assess_pmc_strength
        sun_degree = None
        if body.get('sun_degree') is not None:
            sun_degree = self._normalize_degree(body, 'sun_degree', 0)
        return assess_pmc_strength(self._validate_planets(body.get('planets', {})), sun_degree)

    def _compute_career(self, body):
        from career_analysis import analyze_career
        asc_sign = body.get('asc_sign', 'Aries')
        if asc_sign not in SIGNS:
            raise BadRequest('asc_sign must be a valid sign')
        return analyze_career(self._validate_planets(body.get('planets', {})), asc_sign)

    def _compute_relationship(self, body):
        from relationship_analysis import analyze_relationship
        from spouse_status_yoga import analyze_spouse_status
        asc_sign = body.get('asc_sign', 'Aries')
        if asc_sign not in SIGNS:
            raise BadRequest('asc_sign must be a valid sign')
        planets, planet_lons = self._planet_lons_from_body(body)
        normalized, _, asc_sign_idx = self._normalized_planets_from_body({'planets': planets, 'ascendant': {'sign': asc_sign}})
        planets_for_analysis = normalized or planets
        result = analyze_relationship(planets_for_analysis, asc_sign)
        chart_data = {
            'ascendant': {'sign': asc_sign},
            'planets': planets_for_analysis,
        }
        d9_data = body.get('d9') if isinstance(body.get('d9'), dict) else None
        result['spouse_status_yoga'] = analyze_spouse_status(chart_data, d9_data)
        result['relationship_timing'] = self._compute_relationship_timing_evidence(
            body,
            planets_for_analysis,
            planet_lons,
            asc_sign_idx,
            asc_sign,
            d9_data,
        )
        result['fragment_sources'] = sorted(set(result.get('fragment_sources', []) + [
            'relationship_analysis.py',
            'spouse_status_yoga.py',
            'darakaraka_reader.py',
            'jaimini.py',
        ]))
        return result

    def _compute_relationship_timing_evidence(self, body, planets, planet_lons, asc_sign_idx, asc_sign, d9_data=None):
        jaimini = _load_local_module('jaimini')
        varga = _load_local_module('varga')
        evidence = []
        timing_clues = []
        planet_degs = {planet: lon % 30 for planet, lon in planet_lons.items()}
        ck7 = jaimini.calc_chara_karaka_7(planet_degs) if planet_degs else {}
        dk = (ck7.get('karaka_table') or {}).get('Darakaraka') or {}
        dk_planet = dk.get('planet')

        darakaraka = None
        if dk_planet:
            d9_planets = {}
            for planet, lon in planet_lons.items():
                d9_pos = varga.calc_varga(lon, 9)
                d9_planets[planet] = {
                    'sign': d9_pos.get('sign'),
                    'house': d9_pos.get('house'),
                    'degree': d9_pos.get('degree_in_sign', d9_pos.get('degree')),
                    'degree_in_sign': d9_pos.get('degree_in_sign', d9_pos.get('degree')),
                }
            chart_data = {
                'ascendant': {'sign': asc_sign},
                'planets': planets,
                'd9': {'planets': d9_planets},
            }
            try:
                darakaraka = _load_local_module('darakaraka_reader').analyze_darakaraka(chart_data, use_8_karaka=True)
                timing_clues.extend(darakaraka.get('timing_clues') or [])
                evidence.append({
                    'label': 'Darakaraka (DK)',
                    'value': f"{dk_planet} · H{darakaraka.get('dk_house', '-')}",
                    'note': f"{darakaraka.get('core_profile') or '配偶象征星'}；婚姻质量 {darakaraka.get('marriage_quality_score', '-')}/100",
                })
            except Exception as exc:
                darakaraka = {'error': str(exc), 'dk_planet': dk_planet}

        upapada = jaimini.calc_upapada(asc_sign_idx, planet_lons) if planet_lons else None
        if upapada:
            evidence.append({
                'label': 'Upapada Lagna (UL)',
                'value': f"{upapada.get('sign')} · 2nd {upapada.get('second_from_ul', '-')}",
                'note': upapada.get('description') or '婚姻外显与关系持续性证据',
            })

        h7_sign = SIGNS[(asc_sign_idx + 6) % 12]
        h7_lord = {
            'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
            'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
            'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter',
        }.get(h7_sign)
        dasha_focus = self._relationship_dasha_focus(body, dk_planet, h7_lord)
        if dasha_focus:
            timing_clues.extend(dasha_focus.get('clues', []))
            evidence.append({
                'label': 'Dasha trigger',
                'value': dasha_focus.get('label', '待补充'),
                'note': dasha_focus.get('note', ''),
            })

        score = 0
        if darakaraka and not darakaraka.get('error'):
            quality = darakaraka.get('marriage_quality_score')
            if isinstance(quality, (int, float)):
                score += 2 if quality >= 65 else 1 if quality >= 45 else 0
            if darakaraka.get('timing_clues'):
                score += 1
        if upapada:
            score += 1
        if dasha_focus and dasha_focus.get('level') != 'neutral':
            score += 1
        level = 'strong' if score >= 4 else 'watch' if score >= 2 else 'thin'
        summary = {
            'strong': 'DK、UL 与运限触发能形成较完整的关系时机证据链。',
            'watch': '已有 DK/UL 或运限线索，适合继续用 D9、行运和现实事件复核。',
            'thin': '关系时机证据仍偏薄，需要更完整出生数据或当前运限。',
        }[level]
        return {
            'level': level,
            'score': score,
            'summary': summary,
            'darakaraka': darakaraka,
            'upapada': upapada,
            'dasha_focus': dasha_focus,
            'timing_clues': list(dict.fromkeys(timing_clues))[:6],
            'evidence': evidence,
            'source': 'darakaraka_reader.py + jaimini.py',
        }

    def _relationship_dasha_focus(self, body, dk_planet=None, h7_lord=None):
        raw = body.get('dasha_info') or body.get('dasha') or {}
        if not isinstance(raw, dict):
            return None
        candidates = [
            raw.get('maha_dasha'), raw.get('maha'), raw.get('md'), raw.get('maha_lord'),
            raw.get('antar_dasha'), raw.get('antar'), raw.get('ad'), raw.get('antar_lord'),
            raw.get('pratyantar'), raw.get('pd'), raw.get('pratyantar_lord'),
        ]
        active = [str(item) for item in candidates if item]
        if not active:
            return None
        focus = {'Venus', 'Jupiter', 'Moon', 'Mars'}
        if dk_planet:
            focus.add(dk_planet)
        if h7_lord:
            focus.add(h7_lord)
        hits = [planet for planet in active if planet in focus]
        label = ' / '.join(active[:3])
        if hits:
            return {
                'level': 'activated',
                'label': label,
                'hits': hits,
                'note': f"当前运限触及 {'、'.join(hits)}，关系/承诺主题更容易被事件激活。",
                'clues': [f"Dasha 命中 {'、'.join(hits)}，作为关系时机窗口观察。"],
            }
        return {
            'level': 'neutral',
            'label': label,
            'hits': [],
            'note': '当前运限未明显命中 Venus/Jupiter/Moon/Mars/DK/7主，关系时机需更多行运或事件证据。',
            'clues': [],
        }

    def _planet_lons_from_body(self, body):
        planets = self._validate_planets(body.get('planets', {}))
        planet_lons = {}
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
            lon = self._planet_lon(planets, planet)
            if lon is not None:
                planet_lons[planet] = lon
        return planets, planet_lons

    def _normalized_planets_from_body(self, body):
        planets, planet_lons = self._planet_lons_from_body(body)
        asc_sign_idx = self._asc_sign_idx_from_body(body)
        normalized = {}
        for planet, lon in planet_lons.items():
            source = planets.get(planet, {}) if isinstance(planets, dict) else {}
            sign_idx = int(lon / 30) % 12
            sign = SIGNS[sign_idx]
            house = source.get('house') if isinstance(source, dict) else None
            if house is None:
                house = ((sign_idx - asc_sign_idx) % 12) + 1
            normalized[planet] = {
                **(source if isinstance(source, dict) else {}),
                'lon': lon,
                'degree': lon,
                'degree_in_sign': lon % 30,
                'sign_idx': sign_idx,
                'sign': sign,
                'house': int(house),
            }
        return normalized, planet_lons, asc_sign_idx

    def _asc_sign_idx_from_body(self, body):
        ascendant = body.get('ascendant', {})
        if isinstance(ascendant, dict):
            if ascendant.get('sign_idx') is not None:
                return self._sign_idx_from_value(ascendant.get('sign_idx'), 0)
            if ascendant.get('sign') in SIGNS:
                return SIGNS.index(ascendant.get('sign'))
            if ascendant.get('lon') is not None:
                try:
                    return int((float(ascendant.get('lon')) % 360) / 30) % 12
                except (TypeError, ValueError) as e:
                    raise BadRequest('ascendant lon must be a number') from e
        return int(self._asc_lon_from_body(body) / 30) % 12

    def _chart_payload_from_body(self, body):
        planets, planet_lons = self._planet_lons_from_body(body)
        chart_data = {'planets': {}}
        for planet, lon in planet_lons.items():
            sign_idx = int(lon / 30) % 12
            source = planets.get(planet, {}) if isinstance(planets, dict) else {}
            chart_data['planets'][planet] = {
                **(source if isinstance(source, dict) else {}),
                'degree': lon,
                'lon': lon,
                'sign_idx': sign_idx,
                'sign': SIGNS[sign_idx],
                'degree_in_sign': lon % 30,
            }
        ascendant = body.get('ascendant', {})
        if isinstance(ascendant, dict):
            chart_data['ascendant'] = ascendant
        return chart_data, planet_lons

    def _asc_lon_from_body(self, body, default=0):
        ascendant = body.get('ascendant', {})
        if ascendant is None:
            ascendant = {}
        if not isinstance(ascendant, dict):
            raise BadRequest('ascendant must be an object')
        asc_lon = ascendant.get('lon', ascendant.get('degree_raw'))
        if asc_lon is None and ascendant.get('sign') in SIGNS:
            try:
                return (
                    SIGNS.index(ascendant['sign']) * 30
                    + float(ascendant.get('degree_in_sign', ascendant.get('degree', 0)))
                ) % 360
            except (TypeError, ValueError) as e:
                raise BadRequest('ascendant degree must be a number') from e
        if asc_lon is None and ascendant.get('sign_idx') is not None:
            try:
                sign_idx = int(ascendant.get('sign_idx')) % 12
                degree = float(ascendant.get('degree_in_sign', ascendant.get('degree', 0)))
                return (sign_idx * 30 + degree) % 360
            except (TypeError, ValueError) as e:
                raise BadRequest('ascendant sign_idx/degree must be numeric') from e
        if asc_lon is None:
            return self._normalize_degree(body, 'asc_lon', default)
        try:
            number = float(asc_lon)
        except (TypeError, ValueError) as e:
            raise BadRequest('ascendant lon must be a number') from e
        if not math.isfinite(number):
            raise BadRequest('ascendant lon must be finite')
        return number % 360

    def _parse_varga_divisions(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, str):
            raw_items = [item.strip() for item in value.split(',') if item.strip()]
        elif isinstance(value, list):
            raw_items = value
        else:
            raise BadRequest('divisions must be a comma string or list')
        divisions = []
        for item in raw_items:
            token = str(item).strip().upper()
            if token.startswith('D'):
                token = token[1:]
            if not re.fullmatch(r'\d+', token):
                raise BadRequest('divisions must contain D-numbers such as D9 or 9')
            division = int(token)
            if division < 1 or division > 300:
                raise BadRequest('division must be between 1 and 300')
            divisions.append(division)
        return divisions or None

    def _parse_varga_composite(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, str):
            raw_parts = [part.strip() for part in value.split(',') if part.strip()]
        elif isinstance(value, list):
            raw_parts = value
        else:
            raise BadRequest('composite must be "m,n" or a two-item list')
        if len(raw_parts) != 2:
            raise BadRequest('composite requires exactly two division factors')
        parts = []
        for part in raw_parts:
            try:
                number = int(part)
            except (TypeError, ValueError) as e:
                raise BadRequest('composite factors must be integers') from e
            if number < 2 or number > 300:
                raise BadRequest('composite factors must be between 2 and 300')
            parts.append(number)
        return parts[0], parts[1]

    def _compute_varga_full(self, body):
        _, planet_lons = self._planet_lons_from_body(body)
        if not planet_lons:
            raise BadRequest('planets must include longitude data')
        asc_lon = self._asc_lon_from_body(body)
        divisions = self._parse_varga_divisions(body.get('divisions'))
        composite = self._parse_varga_composite(body.get('composite'))
        custom_n = None
        if body.get('custom') is not None:
            custom_n = self._get_int(body, 'custom', 0, 2, 300)
        variant = body.get('variant')
        if variant is not None and not isinstance(variant, str):
            raise BadRequest('variant must be a string')

        mode_count = sum([
            custom_n is not None,
            composite is not None,
            bool(variant),
        ])
        if mode_count > 1:
            raise BadRequest('custom, composite, and variant modes are mutually exclusive')

        module = _load_local_module('divisional_charts_extended')
        calc = module.DivisionalChartsCalculator()

        try:
            if custom_n is not None:
                result = {'custom_div': custom_n}
                result['Ascendant'] = calc.calc_custom_varga(asc_lon, custom_n)
                for planet, lon in planet_lons.items():
                    result[planet] = calc.calc_custom_varga(lon, custom_n)
                return {
                    'success': True,
                    'endpoint': 'varga_full',
                    'mode': 'custom',
                    'source': 'divisional_charts_extended',
                    'result': result,
                }

            if composite is not None:
                outer, inner = composite
                result = {
                    'composite_div': f'D{outer}×D{inner}=D{outer * inner}',
                    'outer': outer,
                    'inner': inner,
                }
                result['Ascendant'] = calc.calc_composite_varga(asc_lon, outer, inner)
                for planet, lon in planet_lons.items():
                    result[planet] = calc.calc_composite_varga(lon, outer, inner)
                return {
                    'success': True,
                    'endpoint': 'varga_full',
                    'mode': 'composite',
                    'source': 'divisional_charts_extended',
                    'result': result,
                }

            if variant:
                if not divisions or len(divisions) != 1 or divisions[0] not in (2, 3):
                    raise BadRequest('variant mode requires exactly one division: D2 or D3')
                division = divisions[0]
                result = {'variant': variant, 'div': division}
                result['Ascendant'] = calc.calc_varga_with_variant(asc_lon, division, variant)
                for planet, lon in planet_lons.items():
                    result[planet] = calc.calc_varga_with_variant(lon, division, variant)
                return {
                    'success': True,
                    'endpoint': 'varga_full',
                    'mode': 'variant',
                    'source': 'divisional_charts_extended',
                    'result': result,
                }

            available = {varga.division: varga for varga in module.VargaType}
            selected = [available[division] for division in (divisions or sorted(available))]
            result = {}
            for varga in selected:
                key = f'D{varga.division}_{varga.varga_name}'
                result[key] = calc._calculate_single_varga(varga, planet_lons, asc_lon)
        except KeyError as e:
            raise BadRequest('unsupported standard division; use custom mode for arbitrary D-N') from e
        except ValueError as e:
            raise BadRequest(str(e)) from e

        return {
            'success': True,
            'endpoint': 'varga_full',
            'mode': 'standard',
            'source': 'divisional_charts_extended',
            'divisions': [varga.division for varga in selected],
            'result': result,
        }

    def _compute_jaimini(self, body):
        planets, planet_lons, asc_sign_idx = self._normalized_planets_from_body(body)
        if not planet_lons:
            raise BadRequest('planets must include longitude data')
        mode = body.get('mode', 'all')
        if not isinstance(mode, str):
            raise BadRequest('mode must be a string')
        mode = mode.strip().lower() or 'all'
        allowed_modes = {'all', 'karaka', 'dasha', 'karakamsha', 'arudha', 'special'}
        if mode not in allowed_modes:
            raise BadRequest(f'mode must be one of: {", ".join(sorted(allowed_modes))}')
        antardasha = bool(body.get('antardasha', False))
        year = self._get_int(body, 'year', datetime.now().year, 1800, 2400)
        month = self._get_int(body, 'month', 1, 1, 12)
        hour = self._get_int(body, 'hour', 12, 0, 23)
        minute = self._get_int(body, 'minute', 0, 0, 59)
        second = self._get_birth_second(body)
        jaimini = _load_local_module('jaimini')
        varga = _load_local_module('varga')
        planet_degs = {planet: lon % 30 for planet, lon in planet_lons.items()}
        result = {}
        if mode in ('all', 'karaka'):
            result['chara_karaka_7'] = jaimini.calc_chara_karaka_7(planet_degs)
            result['chara_karaka_8'] = jaimini.calc_chara_karaka_8(planet_degs)
        if mode in ('all', 'dasha'):
            if antardasha:
                result['chara_dasha'] = jaimini.calc_chara_dasha_with_antardasha(asc_sign_idx, planet_lons, year, month)
            else:
                result['chara_dasha'] = jaimini.calc_chara_dasha(asc_sign_idx, planet_lons, year, month)
        if mode in ('all', 'karakamsha'):
            ck7 = result.get('chara_karaka_7') or jaimini.calc_chara_karaka_7(planet_degs)
            ak_name = ck7['karaka_table']['Atmakaraka']['planet']
            ak_d9 = varga.calc_varga(planet_lons.get(ak_name, 0), 9)
            result['karakamsha'] = jaimini.calc_karakamsha(
                ak_d9.get('sign', 'Aries'),
                ak_d9.get('degree_in_sign', 0),
            )
        if mode in ('all', 'arudha'):
            result['arudha_padas'] = jaimini.calc_arudha_padas(asc_sign_idx, planet_lons)
            result['graha_padas'] = jaimini.calc_graha_padas(planet_lons)
        if mode in ('all', 'special'):
            result['special_lagnas'] = jaimini.calc_special_lagnas(asc_sign_idx, hour, minute + second / 60.0)
        return {
            'success': True,
            'endpoint': 'jaimini',
            'mode': mode,
            'ascendant': SIGNS[asc_sign_idx],
            'result': result,
        }

    def _compute_ashtakavarga(self, body):
        planets, _, asc_sign_idx = self._normalized_planets_from_body(body)
        if not planets:
            raise BadRequest('planets must include longitude data')
        ashtakavarga = _load_local_module('ashtakavarga')
        result = ashtakavarga.calc_ashtakavarga(planets, asc_sign_idx)
        pav = ashtakavarga.calc_prastara_av(planets, asc_sign_idx)
        sodhita = ashtakavarga.calc_sodhita_av(result.get('bav', {}), planets, asc_sign_idx)
        yoga_pinda = result.get('yoga_pinda') or ashtakavarga.calc_yoga_pinda(result.get('bav', {}), planets, asc_sign_idx)
        result['pav'] = pav
        result['sodhita'] = sodhita
        result['yoga_pinda'] = yoga_pinda
        summary = self._summarize_ashtakavarga(result, pav, sodhita, yoga_pinda)
        return {
            'success': True,
            'endpoint': 'ashtakavarga',
            'rule_variants': self._ashtakavarga_rule_variants(),
            'summary': summary,
            'pav_summary': summary['pav_summary'],
            'sodhita_summary': summary['sodhita_summary'],
            'yoga_pinda_summary': summary['yoga_pinda_summary'],
            'result': result,
        }

    def _summarize_ashtakavarga(self, result, pav, sodhita, yoga_pinda=None):
        house_rows = []
        for key, item in (result.get('house_scores') or {}).items():
            try:
                house_num = int(str(key).split('_')[-1])
            except (TypeError, ValueError):
                house_num = 0
            house_rows.append({
                'house': house_num,
                'sign': item.get('sign'),
                'score': item.get('sav_score', 0),
                'level': item.get('level', ''),
            })
        house_rows.sort(key=lambda item: item.get('score', 0), reverse=True)
        strongest = house_rows[:3]
        weakest = sorted(house_rows, key=lambda item: item.get('score', 0))[:3]

        pav_totals = []
        for planet, source_scores in (pav.get('pav_summary') or {}).items():
            total = sum(value for value in source_scores.values() if isinstance(value, (int, float)))
            top_sources = sorted(source_scores.items(), key=lambda pair: pair[1], reverse=True)[:3]
            pav_totals.append({
                'planet': planet,
                'total': total,
                'top_sources': [{'source': source, 'bindus': bindus} for source, bindus in top_sources],
            })
        pav_totals.sort(key=lambda item: item['total'], reverse=True)

        sodhita_scores = sodhita.get('sodhita_sav', {}).get('assessment', [])
        sodhita_rank = sorted(sodhita_scores, key=lambda item: item.get('score', 0), reverse=True)
        raw_total = result.get('sav', {}).get('total', 0)
        sodhita_total = sodhita.get('sodhita_sav', {}).get('total', 0)
        reduction_total = raw_total - sodhita_total if isinstance(raw_total, (int, float)) and isinstance(sodhita_total, (int, float)) else 0
        yoga_pinda = yoga_pinda or result.get('yoga_pinda') or {}
        yoga_rows = yoga_pinda.get('planets') or {}
        yoga_rank = sorted(yoga_rows.items(), key=lambda item: item[1].get('yoga_pinda', 0), reverse=True)
        leader = strongest[0] if strongest else {}
        headline = (
            f"Ashtakavarga总分{raw_total}，重点支持H{leader.get('house')} {leader.get('sign')}"
            if leader else f"Ashtakavarga总分{raw_total}"
        )
        return {
            'headline': headline,
            'sav_total': raw_total,
            'sav_valid': result.get('sav', {}).get('valid'),
            'strongest_houses': strongest,
            'weakest_houses': weakest,
            'pav_summary': {
                'headline': f"PAV显示{pav_totals[0]['planet']}贡献结构最强" if pav_totals else 'PAV已生成贡献矩阵',
                'top_planets': pav_totals[:3],
                'validation_passed': pav.get('all_valid'),
            },
            'sodhita_summary': {
                'headline': f"Sodhita净化后总分{sodhita_total}，扣减{reduction_total}",
                'top_signs': sodhita_rank[:3],
                'weak_signs': sorted(sodhita_scores, key=lambda item: item.get('score', 0))[:3],
                'reduction_total': reduction_total,
            },
            'yoga_pinda_summary': {
                'headline': (
                    f"Yoga Pinda以{yoga_rank[0][0]}最高（{yoga_rank[0][1].get('yoga_pinda', 0)}）"
                    if yoga_rank else 'Yoga Pinda未返回'
                ),
                'top_planets': [
                    {'planet': planet, 'yoga_pinda': row.get('yoga_pinda'), 'sign': row.get('sign')}
                    for planet, row in yoga_rank[:3]
                ],
                'weak_planets': [
                    {'planet': planet, 'yoga_pinda': row.get('yoga_pinda'), 'sign': row.get('sign')}
                    for planet, row in sorted(yoga_rows.items(), key=lambda item: item[1].get('yoga_pinda', 0))[:3]
                ],
                'total_yoga_pinda': yoga_pinda.get('summary', {}).get('total_yoga_pinda', 0),
                'validation_passed': yoga_pinda.get('all_valid'),
            },
            'next_action': '先用SAV定领域强弱，再用PAV追溯贡献源，用Sodhita检验净支持度，并用Yoga Pinda比较行星承载力。',
        }

    def _compute_shadbala(self, body):
        planets, planet_lons, asc_sign_idx = self._normalized_planets_from_body(body)
        if not {'Sun', 'Moon'} <= set(planet_lons):
            raise BadRequest('planets must include Sun and Moon longitude data')
        birth_hour = self._get_float(body, 'birth_hour', body.get('hour', 12), 0, 23)
        birth_minute = self._get_float(body, 'birth_minute', body.get('minute', 0), 0, 59)
        birth_second = self._get_birth_second(body)
        birth_hour_decimal = self._birth_hour_decimal(birth_hour, birth_minute, birth_second)
        result = _load_local_module('shadbala').calc_shadbala(
            planets,
            SIGNS[asc_sign_idx],
            birth_hour_decimal,
            planet_lons['Sun'],
            planet_lons['Moon'],
        )
        advanced = self._compute_shadbala_advanced_layer(body, planets, result)
        return {
            'success': True,
            'endpoint': 'shadbala',
            'rule_variants': self._shadbala_rule_variants(bool(advanced)),
            'advanced_layer': advanced,
            'result': result,
        }

    def _compute_yogas_api(self, body):
        planets, _, asc_sign_idx = self._normalized_planets_from_body(body)
        if not planets:
            raise BadRequest('planets must include longitude data')
        asc_sign = SIGNS[asc_sign_idx]
        extended = _load_local_module('yoga_expansion').detect_all_yogas(planets, asc_sign)
        try:
            engine_yogas = _load_local_module('yoga_engine').detect_yogas(planets, asc_sign)
        except Exception:
            engine_yogas = []
        curse_yogas = self._compute_curse_yoga_layer(body, planets, asc_sign)
        result = {
            'extended_yogas': extended,
            'rule_engine_yogas': engine_yogas,
            'curse_yogas': curse_yogas,
            'summary': {
                'extended_count': len(extended),
                'rule_engine_count': len(engine_yogas),
                'curse_count': len(curse_yogas.get('curses_detected', [])),
                'risk': curse_yogas.get('overall_risk', 'low'),
            },
            'rule_variants': self._yoga_rule_variants(bool(curse_yogas.get('curses_detected'))),
        }
        return {
            'success': True,
            'endpoint': 'yogas',
            'ascendant': asc_sign,
            'rule_variants': result['rule_variants'],
            'result': result,
        }

    def _ashtakavarga_rule_variants(self):
        return {
            'selected': ['sav_bav', 'prastara_av', 'sodhita_av', 'yoga_pinda'],
            'available': [
                {'key': 'sav_bav', 'label': 'SAV/BAV', 'status': 'active', 'source': 'scripts/ashtakavarga.py'},
                {'key': 'prastara_av', 'label': 'Prastara AV / PAV', 'status': 'active', 'source': 'scripts/ashtakavarga.py'},
                {'key': 'sodhita_av', 'label': 'Sodhita AV', 'status': 'active', 'source': 'scripts/ashtakavarga.py'},
                {'key': 'yoga_pinda', 'label': 'Yoga Pinda', 'status': 'active', 'source': 'scripts/ashtakavarga.py'},
            ],
            'boundary': '当前按本地 BAV 贡献规则生成 SAV、PAV、Sodhita 与 Yoga Pinda；后续可继续加入 Sarvashtakavarga 规则版本对比。',
        }

    def _shadbala_rule_variants(self, advanced_enabled):
        return {
            'selected': ['core_sixfold', 'advanced_evidence'] if advanced_enabled else ['core_sixfold'],
            'available': [
                {'key': 'core_sixfold', 'label': '六重力量主算法', 'status': 'active', 'source': 'scripts/shadbala.py'},
                {'key': 'advanced_evidence', 'label': 'Kala/Yuddha/Sputa 增强证据', 'status': 'active' if advanced_enabled else 'unavailable', 'source': 'scripts/shadbala_advanced.py'},
            ],
            'boundary': '增强层只作为证据补充，不覆盖主 Shadbala 的总分与排名。',
        }

    def _yoga_rule_variants(self, curse_enabled):
        return {
            'selected': ['extended_algorithm', 'json_rule_engine'] + (['curse_conjunctions'] if curse_enabled else []),
            'available': [
                {'key': 'extended_algorithm', 'label': '算法 Yoga 扩展', 'status': 'active', 'source': 'scripts/yoga_expansion.py'},
                {'key': 'json_rule_engine', 'label': 'JSON 规则引擎', 'status': 'active', 'source': 'scripts/yoga_engine.py + references/yoga_rules.json'},
                {'key': 'curse_conjunctions', 'label': '凶星合相命名', 'status': 'active', 'source': 'scripts/curse_yoga_detector.py'},
            ],
            'boundary': '凶星合相属于高风险提示层，只能作为 Yoga 证据之一，不能替代健康、法律或安全建议。',
        }

    def _compute_curse_yoga_layer(self, body, planets, asc_sign):
        current_dasha = body.get('current_dasha') or body.get('dasha_lord')
        chart_data = {
            'ascendant': {'sign': asc_sign},
            'planets': self._planets_for_legacy_fragments(planets),
        }
        context = body.get('context')
        if isinstance(context, dict):
            chart_data['context'] = context
        try:
            return _load_local_module('curse_yoga_detector').detect_curse_yogas(chart_data, current_dasha=current_dasha)
        except Exception as exc:
            import logging
            logging.warning(f"[api_server] curse yoga layer failed: {exc}")
            return {'curses_detected': [], 'overall_risk': 'unknown', 'risk_score': 0, 'error': 'curse yoga layer unavailable'}

    def _planets_for_legacy_fragments(self, planets):
        legacy = {}
        for planet, data in planets.items():
            if not isinstance(data, dict):
                continue
            row = dict(data)
            row['lon'] = data.get('lon', data.get('degree'))
            row['degree'] = data.get('degree_in_sign', data.get('degree', 0))
            row['degree_in_sign'] = row['degree']
            legacy[planet] = row
        return legacy

    def _compute_shadbala_advanced_layer(self, body, planets, base_result):
        try:
            advanced_mod = _load_local_module('shadbala_advanced')
            birth_hour = self._get_float(body, 'birth_hour', body.get('hour', 12), 0, 23)
            birth_minute = self._get_float(body, 'birth_minute', body.get('minute', 0), 0, 59)
            birth_second = self._get_birth_second(body)
            year = self._get_int(body, 'year', datetime.now().year, 1800, 2400)
            month = self._get_int(body, 'month', 1, 1, 12)
            day = self._get_int(body, 'day', 1, 1, 31)
            lat = self._get_float(body, 'lat', body.get('birth_lat', 0), -90, 90)
            lon = self._get_float(body, 'lon', body.get('birth_lon', 0), -180, 180)
            tz = self._parse_timezone(body, lat, lon, year, month, day, birth_hour, birth_minute, birth_second)
            hour_decimal = self._birth_hour_decimal(birth_hour, birth_minute, birth_second)
            solar_lon = planets.get('Sun', {}).get('lon', 0)
            base_planets = base_result.get('planets', {}) if isinstance(base_result, dict) else {}
            comparison_planets = {}
            kala_additions = {}
            drik_sputa = {}
            for planet, pdata in planets.items():
                if planet not in base_planets:
                    continue
                comparison_planets[planet] = {
                    **pdata,
                    'degree': pdata.get('lon', pdata.get('degree', 0)),
                    'shadbala_total': base_planets.get(planet, {}).get('total_virupas', 0),
                }
            for planet in comparison_planets:
                kala_additions[planet] = round(advanced_mod.calc_varsha_maasa_dina_hora_bala(
                    planet, year, month, day, hour_decimal, solar_lon, lat, lon, tz
                ), 2)
                drik_sputa[planet] = round(advanced_mod.calc_drik_bala_sputa(planet, comparison_planets), 2)
            yuddha = advanced_mod.calc_yuddha_bala(comparison_planets)
            active_yuddha = {planet: value for planet, value in yuddha.items() if abs(value) > 0}
            top_kala = sorted(kala_additions.items(), key=lambda item: item[1], reverse=True)[:3]
            return {
                'source': 'scripts/shadbala_advanced.py',
                'method': 'Kala Bala完整子项 + Yuddha Bala + Sputa Drishti 证据层',
                'kala_vmdh': kala_additions,
                'top_kala_support': [{'planet': planet, 'virupas': value} for planet, value in top_kala],
                'yuddha_bala': yuddha,
                'active_yuddha': active_yuddha,
                'sputa_drik_bala': drik_sputa,
                'next_action': '若高级层与主排名冲突，先保留主 Shadbala 排名，再把冲突作为需要人工复核的证据。',
            }
        except Exception as exc:
            import logging
            logging.warning(f"[api_server] shadbala advanced layer failed: {exc}")
            return {}

    def _compute_aspects(self, body):
        _, planet_lons = self._planet_lons_from_body(body)
        if len(planet_lons) < 2:
            raise BadRequest('planets must include at least two longitude values')
        asc_lon = self._asc_lon_from_body(body)
        result = _load_local_module('aspects').calc_all_aspects(planet_lons, asc_lon)
        return {
            'success': True,
            'endpoint': 'aspects',
            'result': result,
        }

    def _compute_annual(self, body):
        target_year = self._get_int(body, 'target_year', datetime.now().year, 1800, 2400)
        birth_dt = self._parse_birth_datetime(body)
        lat = self._get_float(body, 'lat', body.get('birth_lat', 0), -90, 90)
        lon = self._get_float(body, 'lon', body.get('birth_lon', 0), -180, 180)
        tz = self._parse_timezone(
            body,
            lat,
            lon,
            birth_dt.year,
            birth_dt.month,
            birth_dt.day,
            birth_dt.hour,
            birth_dt.minute,
            birth_dt.second,
        )
        solar_return = _load_local_module('solar_return')
        report = solar_return.solar_return_full_report(
            birth_dt.year,
            birth_dt.month,
            birth_dt.day,
            birth_dt.hour,
            birth_dt.minute,
            lat,
            lon,
            tz,
            target_year,
            ayanamsa_name=body.get('ayanamsa', 'lahiri'),
        )
        return {'success': True, 'endpoint': 'annual', 'report': report}

    def _compute_tajika(self, body):
        result = self._compute_annual(body)
        return {
            **result,
            'endpoint': 'tajika',
            'alias_of': 'annual',
        }

    def _compute_chara_dasha(self, body):
        payload = dict(body or {})
        payload['mode'] = 'dasha'
        result = self._compute_jaimini(payload)
        return {
            **result,
            'endpoint': 'chara_dasha',
            'alias_of': 'jaimini',
        }

    def _compute_muhurta(self, body):
        has_range = body.get('start_date') or body.get('end_date') or body.get('start') or body.get('end')
        query_date = body.get('date') or datetime.now().strftime('%Y-%m-%d')
        if not isinstance(query_date, str):
            raise BadRequest('date must be a string')
        try:
            query_dt = datetime.strptime(query_date[:10], '%Y-%m-%d')
        except ValueError as e:
            raise BadRequest('date must be YYYY-MM-DD') from e
        activity = body.get('activity')
        if activity is not None and not isinstance(activity, str):
            raise BadRequest('activity must be a string')
        hour_from_sunrise = self._get_float(body, 'hour_from_sunrise', 6.0, 0, 24)
        sunrise = body.get('sunrise', '06:00')
        sunset = body.get('sunset', '18:00')
        if not isinstance(sunrise, str) or not isinstance(sunset, str):
            raise BadRequest('sunrise/sunset must be HH:MM strings')
        sun_lon = self._planet_lon(body.get('planets', {}), 'Sun')
        moon_lon = self._planet_lon(body.get('planets', {}), 'Moon')
        muhurta = _load_local_module('muhurta')
        if sun_lon is None or moon_lon is None:
            sun_lon, moon_lon = muhurta._approx_sun_moon_lon(query_dt.year, query_dt.month, query_dt.day)
        weekday = (query_dt.weekday() + 1) % 7  # Python Mon=0; module Sun=0
        activities = [activity] if activity else None
        report = muhurta.muhurta_full_report(
            sun_lon,
            moon_lon,
            weekday,
            hour_from_sunrise=hour_from_sunrise,
            query_date_str=query_date[:10],
            activities=activities,
        )
        result = {'success': True, 'endpoint': 'muhurta', 'report': report}
        if has_range:
            start_raw = body.get('start_date') or body.get('start') or query_date
            end_raw = body.get('end_date') or body.get('end') or start_raw
            if not isinstance(start_raw, str) or not isinstance(end_raw, str):
                raise BadRequest('start_date/end_date must be strings')
            try:
                start_dt = datetime.strptime(start_raw[:10], '%Y-%m-%d')
                end_dt = datetime.strptime(end_raw[:10], '%Y-%m-%d')
            except ValueError as e:
                raise BadRequest('start_date/end_date must be YYYY-MM-DD') from e
            if end_dt < start_dt:
                raise BadRequest('end_date must be on or after start_date')
            if (end_dt - start_dt).days > 62:
                raise BadRequest('muhurta range must be <= 63 days')
            lat = lon = tz = None
            has_location = any(key in body for key in ('lat', 'lon', 'tz'))
            if has_location:
                lat = self._get_float(body, 'lat', 0, -90, 90)
                lon = self._get_float(body, 'lon', 0, -180, 180)
                tz = self._get_float(body, 'tz', 0, -14, 14)
            limit = self._get_int(body, 'limit', 5, 1, 20)
            try:
                result['range_search'] = muhurta.muhurta_range_search(
                    start_dt.strftime('%Y-%m-%d'),
                    end_dt.strftime('%Y-%m-%d'),
                    activity=activity or 'business',
                    limit=limit,
                    hour_from_sunrise=hour_from_sunrise,
                    sunrise=sunrise,
                    sunset=sunset,
                    lat=lat,
                    lon=lon,
                    tz=tz,
                    ayanamsa_name=body.get('ayanamsa', 'lahiri'),
                )
            except ValueError as e:
                raise BadRequest(str(e)) from e
        return result

    def _compute_panchanga_range(self, body):
        start_raw = body.get('start_date') or body.get('start') or datetime.now().strftime('%Y-%m-%d')
        end_raw = body.get('end_date') or body.get('end') or start_raw
        if not isinstance(start_raw, str) or not isinstance(end_raw, str):
            raise BadRequest('start_date/end_date must be strings')
        try:
            start_dt = datetime.strptime(start_raw[:10], '%Y-%m-%d')
            end_dt = datetime.strptime(end_raw[:10], '%Y-%m-%d')
        except ValueError as e:
            raise BadRequest('start_date/end_date must be YYYY-MM-DD') from e
        if end_dt < start_dt:
            raise BadRequest('end_date must be on or after start_date')
        if (end_dt - start_dt).days > 62:
            raise BadRequest('panchanga range must be <= 63 days')

        activity = body.get('activity')
        if activity is not None and not isinstance(activity, str):
            raise BadRequest('activity must be a string')
        sunrise = body.get('sunrise', '06:00')
        sunset = body.get('sunset', '18:00')
        if not isinstance(sunrise, str) or not isinstance(sunset, str):
            raise BadRequest('sunrise/sunset must be HH:MM strings')
        hour_from_sunrise = self._get_float(body, 'hour_from_sunrise', 6.0, 0, 24)
        lat = lon = tz = None
        has_location = any(key in body for key in ('lat', 'lon', 'tz'))
        if has_location:
            lat = self._get_float(body, 'lat', 0, -90, 90)
            lon = self._get_float(body, 'lon', 0, -180, 180)
            tz = self._get_float(body, 'tz', 0, -14, 14)
        muhurta = _load_local_module('muhurta')
        try:
            report = muhurta.panchanga_range_report(
                start_dt.strftime('%Y-%m-%d'),
                end_dt.strftime('%Y-%m-%d'),
                hour_from_sunrise=hour_from_sunrise,
                sunrise=sunrise,
                sunset=sunset,
                activity=activity,
                lat=lat,
                lon=lon,
                tz=tz,
            )
        except ValueError as e:
            raise BadRequest(str(e)) from e
        return {'success': True, 'endpoint': 'panchanga_range', 'report': report}

    def _compute_muhurta_panchanga(self, body):
        reference_date = body.get('reference_date') or body.get('transit_date') or body.get('today') or datetime.now().strftime('%Y-%m-%d')
        if not isinstance(reference_date, str):
            raise BadRequest('reference_date must be a string')
        date_str = reference_date[:10]
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError as e:
            raise BadRequest('reference_date must be YYYY-MM-DD') from e
        raw_activity = body.get('activity')
        if raw_activity is not None and not isinstance(raw_activity, str):
            raise BadRequest('activity must be a string')
        activity = (raw_activity or '').strip().lower()
        question_text = str(body.get('question') or '')
        themes = body.get('themes') if isinstance(body.get('themes'), list) else []
        if activity not in {'marriage', 'business', 'travel', 'medical', 'education'}:
            if 'marriage' in themes or any(token in question_text for token in ('婚', '恋', 'marry', 'wedding', 'relationship')):
                activity = 'marriage'
            elif any(token in question_text for token in ('travel', '迁移', '搬家', '出行')):
                activity = 'travel'
            elif any(token in question_text for token in ('medical', '手术', '治疗', '健康')):
                activity = 'medical'
            elif any(token in question_text for token in ('education', '学习', '考试', '申请')):
                activity = 'education'
            else:
                activity = 'business'
        muhurta = _load_local_module('muhurta')
        return muhurta.build_muhurta_sidecar(
            date_str=date_str,
            activity=activity,
            lat=self._get_float(body, 'lat', 0, -90, 90),
            lon=self._get_float(body, 'lon', 0, -180, 180),
            tz=self._get_float(body, 'tz', 0, -14, 14),
            ayanamsa_name=body.get('ayanamsa', 'lahiri'),
        )

    def _compute_rectification_gate(self, body):
        asc_lon = self._asc_lon_from_body(body)
        declared_accuracy = body.get('declared_accuracy', body.get('accuracy', 'minute'))
        time_source = body.get('time_source', 'family_clear')
        if not isinstance(declared_accuracy, str):
            raise BadRequest('declared_accuracy must be a string')
        if not isinstance(time_source, str):
            raise BadRequest('time_source must be a string')

        module = _load_local_module('birth_time_rectifier')
        is_boundary, boundary_note = module.check_lagna_boundary(asc_lon)
        effective_accuracy = module.get_effective_accuracy(declared_accuracy, time_source)
        enabled_vargas = module.get_enabled_vargas(effective_accuracy)
        normalized_planets, _, _ = self._normalized_planets_from_body(body)
        recommended_events = module.recommend_event_types(normalized_planets)
        confidence_seed = module.calculate_confidence(0, 0, effective_accuracy, is_boundary)

        disabled = sorted([key for key, value in enabled_vargas.items() if value == 'disabled'])
        warned = sorted([key for key, value in enabled_vargas.items() if value == 'enabled_with_warning'])
        enabled = sorted([key for key, value in enabled_vargas.items() if value == 'enabled'])
        if is_boundary:
            headline = '出生时间高度敏感，建议先做事件反验'
            next_action = '优先录入婚姻、迁移、事业转折、健康危机等日期明确事件，再比较相邻候选时间。'
        elif warned or disabled:
            headline = '可读主盘，但高敏分盘需要降级'
            next_action = 'D1 可正常阅读；D9/D10 以上结论需标注时间精度限制。'
        else:
            headline = '出生时间风险较低，可进入完整解盘'
            next_action = '保留原始出生记录来源；重要预测仍建议用 Dasha/Transit/案例验证交叉确认。'

        return {
            'success': True,
            'endpoint': 'rectification_gate',
            'ascendant': {
                'lon': asc_lon,
                'sign': SIGNS[int(asc_lon / 30) % 12],
                'degree_in_sign': round(asc_lon % 30, 4),
            },
            'declared_accuracy': declared_accuracy,
            'time_source': time_source,
            'effective_accuracy': effective_accuracy,
            'lagna_boundary': {
                'is_sensitive': is_boundary,
                'note': boundary_note,
            },
            'enabled_vargas': enabled_vargas,
            'summary': {
                'headline': headline,
                'enabled': enabled,
                'warned': warned,
                'disabled': disabled,
                'confidence_floor': confidence_seed.get('assessment'),
                'recommended_events': recommended_events,
                'next_action': next_action,
            },
        }

    def _compute_case_validation(self, body):
        planets, _, _ = self._normalized_planets_from_body(body)
        current_md = body.get('current_md', body.get('dasha_lord', ''))
        if current_md is not None and not isinstance(current_md, str):
            raise BadRequest('current_md must be a string')
        predicted_events = body.get('predicted_events', [])
        if predicted_events is None:
            predicted_events = []
        if not isinstance(predicted_events, list):
            raise BadRequest('predicted_events must be an array')
        transit_desc = body.get('transit_desc', '')
        if transit_desc is not None and not isinstance(transit_desc, str):
            raise BadRequest('transit_desc must be a string')

        analysis = {
            'planets': {},
            'dasha': {
                'current_md': current_md,
                'predicted_events': [str(item)[:120] for item in predicted_events[:12]],
            },
            'transit': transit_desc or {},
        }
        for planet, data in planets.items():
            if planet not in {'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'}:
                continue
            dignity = self._case_dignity_label(planet, data.get('sign'))
            if dignity:
                analysis['planets'][planet] = {
                    'planet': planet,
                    'sign': data.get('sign'),
                    'house': data.get('house'),
                    'dignity': dignity,
                }

        validator = _load_local_module('case_validator')
        raw = validator.validate_interpretation(analysis)
        validations = raw.get('validations', [])
        validated = [item for item in validations if item.get('validated')]
        unvalidated = [item for item in validations if not item.get('validated')]
        headline = '案例库支持度较强' if raw.get('overall_confidence', 0) >= 70 else '案例支持不足，需谨慎措辞'
        if not validations:
            headline = '当前星盘缺少可验证声明'
        next_action = (
            '优先使用已验证配置做结论；未验证项只作为假设，并补充真实案例或外部来源。'
            if unvalidated else
            '可以进入解释层，但仍需保留具体事件预测的置信度上限。'
        )
        mevg_gate = self._mevg_gate_status()
        return {
            'success': True,
            'endpoint': 'case_validation',
            'fragment_sources': ['case_validator.py', 'mevg_automation.py'],
            'analysis': analysis,
            'result': raw,
            'mevg_gate': mevg_gate,
            'summary': {
                'headline': headline,
                'overall_confidence': raw.get('overall_confidence', 0),
                'validated_count': len(validated),
                'unvalidated_count': len(unvalidated),
                'case_base': raw.get('case_base', ''),
                'gate_status': mevg_gate.get('gate_status'),
                'top_cases': sorted({
                    case
                    for item in validated
                    for case in item.get('cases', [])
                    if isinstance(case, str)
                })[:8],
                'next_action': next_action,
            },
        }

    def _mevg_gate_status(self):
        try:
            mevg = _load_local_module('mevg_automation')
            state_path = getattr(mevg, 'MEVG_STATE_FILE', None)
            checks = getattr(mevg, 'VALIDATION_CHECKS', [])
            threshold = getattr(mevg, 'GATE_THRESHOLD', 0.30)
            if not state_path or not os.path.exists(state_path):
                return {
                    'source': 'mevg_automation.py',
                    'gate_status': 'NOT_INITIALIZED',
                    'threshold': threshold,
                    'case_count': 0,
                    'failed_count': 0,
                    'fail_rate': 0,
                    'checks': checks,
                    'next_action': '运行 MEVG 案例验证后再把外部门控作为预测置信度依据。',
                }
            with open(state_path, 'r', encoding='utf-8') as fh:
                state = json.load(fh)
            cases = state.get('cases', {}) if isinstance(state, dict) else {}
            failed = sum(1 for item in cases.values() if isinstance(item, dict) and item.get('verdict') == 'FAIL')
            fail_rate = failed / len(cases) if cases else 0
            return {
                'source': 'mevg_automation.py',
                'gate_status': state.get('gate_status', 'UNKNOWN'),
                'threshold': threshold,
                'case_count': len(cases),
                'failed_count': failed,
                'fail_rate': round(fail_rate, 3),
                'last_updated': state.get('last_updated'),
                'checks': checks,
                'next_action': '若门控 CLOSED，应先校准失败案例，再输出新的预测型解读。',
            }
        except Exception as exc:
            import logging
            logging.warning(f"[api_server] MEVG gate status unavailable: {exc}")
            return {
                'source': 'mevg_automation.py',
                'gate_status': 'UNAVAILABLE',
                'error': str(exc),
                'next_action': 'MEVG 自动化状态不可用；预测项必须降级为待验证假设。',
            }

    def _case_dignity_label(self, planet, sign):
        exalted = {
            'Sun': 'Aries',
            'Moon': 'Taurus',
            'Mars': 'Capricorn',
            'Mercury': 'Virgo',
            'Jupiter': 'Cancer',
            'Venus': 'Pisces',
            'Saturn': 'Libra',
        }
        debilitated = {
            'Sun': 'Libra',
            'Moon': 'Scorpio',
            'Mars': 'Cancer',
            'Mercury': 'Pisces',
            'Jupiter': 'Capricorn',
            'Venus': 'Virgo',
            'Saturn': 'Aries',
        }
        own_signs = {
            'Sun': {'Leo'},
            'Moon': {'Cancer'},
            'Mars': {'Aries', 'Scorpio'},
            'Mercury': {'Gemini', 'Virgo'},
            'Jupiter': {'Sagittarius', 'Pisces'},
            'Venus': {'Taurus', 'Libra'},
            'Saturn': {'Capricorn', 'Aquarius'},
        }
        if not sign:
            return ''
        if exalted.get(planet) == sign:
            return 'exalted'
        if debilitated.get(planet) == sign:
            return 'debilitated'
        if sign in own_signs.get(planet, set()):
            return 'own_sign'
        if planet == 'Mars':
            return 'strong'
        if planet == 'Venus' and sign in {'Taurus', 'Libra', 'Pisces'}:
            return 'strong'
        return ''

    def _compute_divisional_yoga(self, body):
        normalized, _, asc_sign_idx = self._normalized_planets_from_body(body)
        if not normalized:
            raise BadRequest('planets must include longitude data')
        divisions = body.get('divisions', ['D9', 'D10', 'D12'])
        if isinstance(divisions, str):
            divisions = [item.strip().upper() for item in divisions.split(',') if item.strip()]
        if not isinstance(divisions, list):
            raise BadRequest('divisions must be a list or comma string')
        allowed = {'D9', 'D10', 'D12'}
        selected = []
        for item in divisions:
            token = str(item).strip().upper()
            if token not in allowed:
                raise BadRequest('divisional_yoga supports D9, D10, and D12')
            selected.append(token)
        selected = selected or ['D9', 'D10', 'D12']
        module = _load_local_module('divisional_yoga')
        results = {}
        total = 0
        for division in selected:
            yogas = module.detect_varga_yogas(normalized, division, SIGNS[asc_sign_idx])
            results[division] = {
                'yoga_count': len(yogas),
                'yogas': yogas,
            }
            total += len(yogas)
        headline = '分盘 Yoga 有可用证据' if total else '分盘 Yoga 暂无强命中'
        return {
            'success': True,
            'endpoint': 'divisional_yoga',
            'ascendant': SIGNS[asc_sign_idx],
            'divisions': selected,
            'result': results,
            'summary': {
                'headline': headline,
                'total_yogas': total,
                'next_action': '把 D9 用于关系/内在成熟，D10 用于事业兑现，D12 用于家族与父母主题；不要把分盘 Yoga 当作单点结论。',
            },
        }

    def _compute_deep_varga_avastha(self, body):
        _, planet_lons, _ = self._normalized_planets_from_body(body)
        if not planet_lons:
            raise BadRequest('planets must include longitude data')
        asc_lon = self._asc_lon_from_body(body)
        report = _load_local_module('deep_varga_avastha').build_deep_varga_avastha_report(
            planet_lons,
            asc_lon=asc_lon,
        )
        return {
            'success': True,
            'endpoint': 'deep_varga_avastha',
            'report': report,
        }

    def _compute_kakshya(self, body):
        normalized, _, asc_sign_idx = self._normalized_planets_from_body(body)
        if not normalized:
            raise BadRequest('planets must include longitude data')
        result = _load_local_module('kakshya').calc_kakshya_scores(normalized, asc_sign_idx)
        planets = result.get('planets', {})
        strongest = sorted(
            planets.items(),
            key=lambda item: item[1].get('kakshya_strength', 0),
            reverse=True,
        )[:3]
        weakest = sorted(
            planets.items(),
            key=lambda item: item[1].get('kakshya_strength', 0),
        )[:3]
        avg = sum(item.get('kakshya_strength', 0) for item in planets.values()) / max(len(planets), 1)
        headline = 'Kakshya 度数层支持较强' if avg >= 6.5 else 'Kakshya 度数层需要谨慎使用'
        return {
            'success': True,
            'endpoint': 'kakshya',
            'ascendant': SIGNS[asc_sign_idx],
            'result': result,
            'summary': {
                'headline': headline,
                'average_strength': round(avg, 2),
                'strongest': [{'planet': name, **data} for name, data in strongest],
                'weakest': [{'planet': name, **data} for name, data in weakest],
                'next_action': '把 Kakshya 用作 Ashtakavarga/Transit 的度数级触发层，只在已有 Dasha 或主题承诺时提高事件窗口权重。',
            },
        }

    def _compute_bhava_bala_api(self, body):
        normalized, _, asc_sign_idx = self._normalized_planets_from_body(body)
        if not normalized:
            raise BadRequest('planets must include longitude data')
        asc_lon = self._asc_lon_from_body(body)
        asc_sign = SIGNS[asc_sign_idx]
        asc_degree = asc_lon % 30
        house_signs = [SIGNS[(asc_sign_idx + i) % 12] for i in range(12)]
        house_degrees = [asc_degree for _ in range(12)]
        planet_shadbala = self._planet_shadbala_from_body(body, normalized)
        result = _load_local_module('bhava_bala').calc_bhava_bala(
            house_signs,
            house_degrees,
            asc_sign,
            asc_degree,
            normalized,
            planet_shadbala,
        )
        houses = result.get('houses', [])
        strongest = sorted(houses, key=lambda item: item.get('total', 0), reverse=True)[:3]
        weakest = sorted(houses, key=lambda item: item.get('total', 0))[:3]
        headline = '宫位力量结构清晰' if strongest and strongest[0].get('total', 0) >= 45 else '宫位力量偏分散'
        return {
            'success': True,
            'endpoint': 'bhava_bala',
            'ascendant': asc_sign,
            'result': result,
            'summary': {
                'headline': headline,
                'strongest': strongest,
                'weakest': weakest,
                'next_action': '优先阅读最强宫位对应的人生领域；最弱宫位只作为风险提示，需要结合宫主、Dasha 与 Transit 确认。',
            },
        }

    def _planet_shadbala_from_body(self, body, planets):
        raw = body.get('planet_shadbala') or body.get('shadbala') or {}
        result = {}
        if isinstance(raw, dict):
            for planet, value in raw.items():
                if isinstance(value, dict):
                    number = value.get('virupas', value.get('total_virupas', value.get('score', value.get('rupas'))))
                else:
                    number = value
                try:
                    result[planet] = float(number)
                except (TypeError, ValueError):
                    continue
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            if planet in result:
                continue
            pdata = planets.get(planet, {})
            dignity = self._case_dignity_label(planet, pdata.get('sign'))
            score = 35.0
            if dignity in {'exalted', 'own_sign'}:
                score = 55.0
            elif dignity == 'strong':
                score = 45.0
            elif dignity == 'debilitated':
                score = 24.0
            if pdata.get('house') in (1, 4, 7, 10):
                score += 5.0
            result[planet] = score
        return result

    def _compute_transit_triggers(self, body):
        start_raw = body.get('start', body.get('start_date', datetime.now().strftime('%Y-%m-%d')))
        end_raw = body.get('end', body.get('end_date'))
        if not isinstance(start_raw, str):
            raise BadRequest('start must be YYYY-MM-DD')
        if end_raw is not None and not isinstance(end_raw, str):
            raise BadRequest('end must be YYYY-MM-DD')
        try:
            start_date = datetime.strptime(start_raw[:10], '%Y-%m-%d')
            end_date = datetime.strptime((end_raw or (start_date + timedelta(days=90)).strftime('%Y-%m-%d'))[:10], '%Y-%m-%d')
        except ValueError as e:
            raise BadRequest('start/end must be YYYY-MM-DD') from e
        if end_date < start_date:
            raise BadRequest('end must be after start')
        if (end_date - start_date).days > 730:
            raise BadRequest('transit search range must be <= 730 days')

        planets_to_check = body.get('planets_to_check')
        raw_planets = body.get('natal_planets', body.get('chart_planets'))
        if raw_planets is None and isinstance(body.get('planets'), dict):
            raw_planets = body.get('planets')
        elif raw_planets is None and isinstance(body.get('planets'), list):
            planets_to_check = body.get('planets')
            raw_planets = {}
        if planets_to_check is not None:
            if not isinstance(planets_to_check, list):
                raise BadRequest('planets_to_check must be an array')
            planets_to_check = [str(item) for item in planets_to_check[:9]]

        planets = self._validate_planets(raw_planets or {})
        body_for_asc = {**body, 'planets': planets}
        asc_lon = self._asc_lon_from_body(body_for_asc)
        natal_data = {'asc': asc_lon, 'planets': planets}
        result = _load_local_module('transit_trigger').search_all_transit_triggers(
            natal_data,
            start_date,
            end_date,
            planets_to_check=planets_to_check,
            ayanamsa_name=body.get('ayanamsa', 'lahiri'),
        )
        top_triggers = result.get('triggers', [])[:6]
        headline = '发现可观察过境触发点' if result.get('total_triggers', 0) else '当前区间未发现精确触发'
        return {
            'success': True,
            'endpoint': 'transit',
            'result': result,
            'triggers': result.get('triggers', []),
            'summary': {
                'headline': headline,
                'period': result.get('search_period', {}),
                'total_triggers': result.get('total_triggers', 0),
                'top_triggers': top_triggers,
                'next_action': '把过境触发作为时间窗口，不单独定事件；优先与 Dasha、Ashtakavarga、Kakshya 和本命承诺交叉确认。',
            },
        }

    def _compute_bhava_chalit(self, body):
        _, planet_lons = self._planet_lons_from_body(body)
        if not planet_lons:
            raise BadRequest('planets must include longitude data')
        ascendant = body.get('ascendant', {})
        if not isinstance(ascendant, dict):
            raise BadRequest('ascendant must be an object')
        asc_lon = ascendant.get('lon')
        if asc_lon is None and ascendant.get('sign') in SIGNS:
            asc_lon = SIGNS.index(ascendant['sign']) * 30 + float(ascendant.get('degree_in_sign', ascendant.get('degree', 0)))
        if asc_lon is None:
            asc_lon = self._normalize_degree(body, 'asc_lon', 0)
        else:
            asc_lon = float(asc_lon) % 360
        mc_lon = self._normalize_degree(body, 'mc_lon', (asc_lon + 270) % 360)
        house_system = body.get('house_system', 'sripati')
        if not isinstance(house_system, str):
            raise BadRequest('house_system must be a string')
        requested_house_system = house_system.lower().strip()
        mode = body.get('mode', 'compare')
        if not isinstance(mode, str):
            raise BadRequest('mode must be a string')
        calculator = _load_local_module('bhava_chalit').BhavaChalitCalculator()
        available_house_systems = sorted(calculator.HOUSE_SYSTEMS.keys())
        if requested_house_system not in calculator.HOUSE_SYSTEMS:
            raise BadRequest(f'unknown house_system: {house_system}')
        selected_house_system = requested_house_system
        jd = lat = lon = None
        fallback_reason = ''
        calculation_note = f'Bhava Chalit uses {calculator.HOUSE_SYSTEMS[selected_house_system]}.'
        if selected_house_system in {'placidus', 'koch'}:
            try:
                year = self._get_int(body, 'year', 1990, 1800, 2400)
                month = self._get_int(body, 'month', 6, 1, 12)
                day = self._get_int(body, 'day', 15, 1, 31)
                hour = self._get_float(body, 'hour', 12, 0, 23)
                minute = self._get_float(body, 'minute', 0, 0, 59)
                second = self._get_birth_second(body)
                lat = self._get_float(body, 'lat', body.get('birth_lat', 0), -90, 90)
                lon = self._get_float(body, 'lon', body.get('birth_lon', 0), -180, 180)
                tz = self._parse_timezone(body, lat, lon, year, month, day, hour, minute, second)
                datetime(year, month, day, int(hour), int(minute), int(second))
                import swisseph as swe
                hour_ut = self._birth_hour_decimal(hour, minute, second) - tz
                jd = swe.julday(year, month, day, hour_ut)
                calculation_note = f'{selected_house_system} cusps use swisseph houses with birth JD and location.'
            except Exception as exc:
                fallback_reason = f'{selected_house_system} requires swisseph plus valid birth date, lat, lon and tz; fell back to sripati: {exc}'
                selected_house_system = 'sripati'
                jd = lat = lon = None
                calculation_note = 'Fallback to Sripati because time-based house cusps were unavailable.'
        if mode == 'chart':
            result = calculator.get_bhava_chalit_chart(planet_lons, asc_lon, mc_lon, selected_house_system, jd, lat, lon)
        elif mode == 'boundaries':
            result = calculator.calculate_bhava_boundaries(asc_lon, mc_lon, selected_house_system, jd, lat, lon)
        else:
            result = calculator.compare_rashi_vs_bhava(planet_lons, asc_lon, mc_lon, selected_house_system, jd, lat, lon)
        result.setdefault('summary', {
            'total_planets': len(planet_lons),
            'shifted_count': result.get('shifted_count', 0),
            'shifted_names': [shift.get('planet') for shift in result.get('shifts', []) if isinstance(shift, dict)],
        })
        result['requested_house_system'] = requested_house_system
        result['selected_house_system'] = selected_house_system
        result['available_house_systems'] = available_house_systems
        result['fallback_reason'] = fallback_reason
        result['calculation_note'] = calculation_note
        return {
            'success': True,
            'endpoint': 'bhava_chalit',
            'mode': mode,
            'requested_house_system': requested_house_system,
            'selected_house_system': selected_house_system,
            'available_house_systems': available_house_systems,
            'fallback_reason': fallback_reason,
            'calculation_note': calculation_note,
            'result': result,
        }

    def _compute_sudarshana(self, body):
        _, planet_lons = self._planet_lons_from_body(body)
        if not {'Sun', 'Moon'} <= set(planet_lons):
            raise BadRequest('planets must include Sun and Moon longitude data')
        ascendant = body.get('ascendant', {})
        if not isinstance(ascendant, dict):
            raise BadRequest('ascendant must be an object')
        asc_lon = ascendant.get('lon')
        if asc_lon is None and ascendant.get('sign') in SIGNS:
            asc_lon = SIGNS.index(ascendant['sign']) * 30 + float(ascendant.get('degree_in_sign', ascendant.get('degree', 0)))
        if asc_lon is None:
            asc_lon = self._normalize_degree(body, 'asc_lon', 0)
        else:
            asc_lon = float(asc_lon) % 360
        house = body.get('house')
        if house is not None:
            house = self._get_int(body, 'house', 1, 1, 12)
        result = _load_local_module('sudarshana_chakra').calc_sudarshana_chakra(planet_lons, asc_lon, house)
        return {'success': True, 'endpoint': 'sudarshana', 'result': result}

    def _compute_nakshatra_full(self, body):
        chart_data, _ = self._chart_payload_from_body(body)
        age = body.get('age')
        if age is not None:
            age = self._get_float(body, 'age', 0, 0, 150)
        transit_date = body.get('transit_date')
        if transit_date is not None and not isinstance(transit_date, str):
            raise BadRequest('transit_date must be a string')
        result = _load_local_module('nakshatra_advanced').nakshatra_full_report(
            chart_data,
            age=age,
            transit_date=transit_date,
        )
        return {'success': True, 'endpoint': 'nakshatra_full', 'result': result}

    def _capability_audit(self):
        registry = self._read_technique_registry()
        techniques = registry.get('techniques', {})
        engine_commands = self._scan_engine_commands()
        api_endpoints = self._scan_api_endpoints()
        app_tabs = self._scan_app_tabs()
        local_sources = self._scan_local_open_source_sources()
        command_set = set(engine_commands)
        api_command_map = API_COMMAND_MAP
        api_backed_commands = sorted(
            command
            for command, endpoint in api_command_map.items()
            if endpoint in api_endpoints or command in command_set
        )
        app_visible_topics = self._app_visible_topics(app_tabs)
        registry_commands = sorted({
            command
            for technique in techniques.values()
            for command in technique.get('commands', [])
            if isinstance(command, str)
        })
        registry_only_commands = sorted(set(registry_commands) - command_set)
        engine_not_api = sorted(command_set - set(api_backed_commands))
        status_counts = {}
        domain_counts = {}
        for technique in techniques.values():
            status = technique.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            for domain in technique.get('domains', []):
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

        direct_sources = [s for s in local_sources if s.get('reuse') == 'direct']
        caution_sources = [s for s in local_sources if s.get('reuse') == 'caution']
        unknown_sources = [s for s in local_sources if s.get('reuse') == 'unknown']
        priority_gaps = self._build_priority_gaps(techniques, engine_not_api, app_visible_topics)
        productization = self._build_productization_matrix(
            techniques,
            command_set,
            set(api_backed_commands),
            app_visible_topics,
        )
        ux_productization = self._build_ux_productization_matrix(productization['rows'])

        return {
            'success': True,
            'generated_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
            'registry': {
                'version': registry.get('version'),
                'technique_count': len(techniques),
                'status_counts': status_counts,
                'domain_counts': dict(sorted(domain_counts.items())),
                'source_inspiration': registry.get('source_inspiration', []),
            },
            'techniques': [
                {
                    'id': key,
                    'name': value.get('name', key),
                    'status': value.get('status', 'unknown'),
                    'domains': value.get('domains', []),
                    'commands': value.get('commands', []),
                    'output_paths': value.get('output_paths', []),
                    'audit_label': value.get('audit_label', value.get('name', key)),
                    'limitation': value.get('limitation', ''),
                    'missing_impact': value.get('missing_impact', ''),
                }
                for key, value in sorted(techniques.items())
            ],
            'surfaces': {
                'engine_command_count': len(engine_commands),
                'engine_commands': engine_commands,
                'api_endpoint_count': len(api_endpoints),
                'api_endpoints': api_endpoints,
                'api_backed_commands': api_backed_commands,
                'engine_not_api': engine_not_api,
                'registry_only_commands': registry_only_commands,
                'app_tab_count': len(app_tabs),
                'app_tabs': app_tabs,
                'app_visible_topics': app_visible_topics,
            },
            'local_open_source': {
                'source_count': len(local_sources),
                'direct_reuse_count': len(direct_sources),
                'caution_count': len(caution_sources),
                'unknown_count': len(unknown_sources),
                'sources': local_sources,
            },
            'external_research': self._external_research_matrix(),
            'priority_gaps': priority_gaps,
            'productization': productization,
            'ux_productization': ux_productization,
        }

    def _technique_catalog(self):
        audit = self._capability_audit()
        rows = self._build_technique_catalog_rows(audit)
        domains = sorted({
            domain
            for row in rows
            for domain in row.get('domains', [])
        })
        endpoints = sorted({
            endpoint
            for row in rows
            for endpoint in row.get('api_endpoints', [])
        })
        return {
            'success': True,
            'generated_at': audit.get('generated_at'),
            'registry': audit.get('registry', {}),
            'summary': {
                'technique_count': len(rows),
                'domain_count': len(domains),
                'api_endpoint_count': len(endpoints),
                'runnable_count': sum(1 for row in rows if row.get('runnable')),
            },
            'filters': {
                'domains': domains,
                'levels': ['productized', 'api_backed', 'engine_or_full_reading', 'registry_only'],
                'statuses': sorted({row.get('status') for row in rows if row.get('status')}),
                'api_endpoints': endpoints,
            },
            'api_command_map': API_COMMAND_MAP,
            'example_payloads': self._technique_example_payloads(),
            'api_docs': self._technique_api_docs(),
            'techniques': rows,
        }

    def _build_technique_catalog_rows(self, audit):
        product_rows = {
            row.get('id'): row
            for row in audit.get('productization', {}).get('rows', [])
            if row.get('id')
        }
        ux_rows = {
            row.get('id'): row
            for row in audit.get('ux_productization', {}).get('rows', [])
            if row.get('id')
        }
        api_endpoints = set(audit.get('surfaces', {}).get('api_endpoints', []))
        rows = []
        for technique in audit.get('techniques', []):
            product = product_rows.get(technique.get('id'), {})
            ux = ux_rows.get(technique.get('id'), {})
            commands = sorted(set((technique.get('commands') or []) + (product.get('commands') or [])))
            mapped = [
                API_COMMAND_MAP.get(command)
                for command in commands
                if API_COMMAND_MAP.get(command) in api_endpoints
            ]
            if technique.get('id') == 'jaimini_chara_dasha' and '/api/dasha/chara' in api_endpoints:
                mapped.append('/api/dasha/chara')
            runnable = [endpoint for endpoint in mapped if endpoint in TECHNIQUE_EXAMPLE_ENDPOINTS]
            primary_endpoint = self._primary_catalog_endpoint(technique, mapped, runnable)
            rows.append({
                'id': technique.get('id'),
                'name': technique.get('name'),
                'audit_label': technique.get('audit_label'),
                'status': technique.get('status'),
                'domains': sorted(set((technique.get('domains') or []) + (product.get('domains') or []))),
                'commands': commands,
                'api_commands': product.get('api_commands', []),
                'api_endpoints': sorted(set(mapped)),
                'runnable': bool(runnable),
                'example_endpoint': runnable[0] if runnable else '',
                'method_docs': self._technique_method_doc(technique, product, primary_endpoint),
                'output_paths': sorted(set((technique.get('output_paths') or []) + (product.get('output_paths') or []))),
                'level': product.get('level', 'registry_only'),
                'reason': product.get('reason') or technique.get('limitation') or '',
                'next_action': product.get('next_action') or ux.get('ux_next_action') or technique.get('missing_impact') or '',
                'ux_level': ux.get('ux_level', 'not_user_ready'),
                'ux_score': ux.get('ux_score', 0),
                'visible_markers': product.get('visible_markers', []),
            })
        order = {'registry_only': 0, 'engine_or_full_reading': 1, 'api_backed': 2, 'productized': 3}
        return sorted(rows, key=lambda row: (order.get(row.get('level'), 0), row.get('name') or ''))

    def _primary_catalog_endpoint(self, technique, mapped, runnable):
        candidates = runnable or mapped or []
        if not candidates:
            return ''
        text = ' '.join([
            str(technique.get('id', '')),
            str(technique.get('name', '')),
            str(technique.get('audit_label', '')),
            ' '.join(technique.get('domains') or []),
        ]).lower()
        endpoint_keywords = [
            ('/api/thematic_report', ['thematic', '主题', 'report_orchestrator', 'reading', 'report']),
            ('/api/high_rigor_workflow', ['high_rigor', '高严谨', 'rectification', 'backtest', 'vedastro']),
            ('/api/relationship', ['relationship', 'spouse', '婚姻', '感情']),
            ('/api/career', ['career', '事业']),
            ('/api/dasha', ['dasha', 'vimshottari']),
            ('/api/dasha/chara', ['chara dasha', 'chara_dasha', 'jaimini dasha']),
            ('/api/yogas', ['yoga', 'dosha']),
            ('/api/shadbala', ['shadbala']),
            ('/api/deep_varga_avastha', ['deep_varga_avastha', 'deep varga', 'avastha', 'sayanadi', 'shayanadi', 'd24', 'd30', 'd60']),
            ('/api/ashtakavarga', ['ashtakavarga']),
            ('/api/jaimini', ['jaimini', 'karaka', 'arudha']),
        ]
        for endpoint, keywords in endpoint_keywords:
            if endpoint in candidates and any(keyword in text for keyword in keywords):
                return endpoint
        return candidates[0]

    def _compute_technique_example(self, body):
        endpoint = body.get('endpoint')
        if not isinstance(endpoint, str):
            raise BadRequest('endpoint must be a string')
        endpoint = endpoint.strip()
        if endpoint not in TECHNIQUE_EXAMPLE_ENDPOINTS:
            raise BadRequest('endpoint is not runnable from technique explorer')
        payloads = self._technique_example_payloads()
        payload = body.get('payload')
        if payload is None:
            payload = payloads.get(endpoint)
        if not isinstance(payload, dict):
            raise BadRequest('payload must be an object')
        payload = self._sanitize_technique_example_payload(endpoint, payload)
        result = self._dispatch_technique_endpoint(endpoint, payload)
        return {
            'success': True,
            'endpoint': 'technique_example',
            'target_endpoint': endpoint,
            'sample_payload': payload,
            'result': result,
        }

    def _real_case_revalidation(self):
        validator_path = os.path.join(REPO_ROOT, 'tests', 'run_real_case_revalidation.py')
        spec = importlib.util.spec_from_file_location('_jyotish_real_case_revalidation', validator_path)
        if not spec or not spec.loader:
            raise RuntimeError('Cannot load real case revalidation runner')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        args = argparse.Namespace(
            python=sys.executable,
            min_pass_rate=0.98,
            degree_tolerance=1.0,
        )
        report = module.build_report(args)
        return {
            'success': bool(report.get('valid')),
            'endpoint': 'real_case_revalidation',
            'scope': report.get('scope'),
            'accuracy_boundary': '公开人物星座级一致率，不是人生事件预测准确率。',
            'public_reference': {
                'label': '公开人物星座级一致率',
                'passed': report.get('gated_passed_checks'),
                'total': report.get('gated_total_checks'),
                'pass_rate': report.get('pass_rate'),
            },
            'all_checks': {
                'passed': report.get('passed_checks'),
                'total': report.get('total_checks'),
            },
            'controversial_reference': {
                'case_count': report.get('controversial_reference_cases'),
                'note': '来源矛盾、时区争议或边界度数样本保留展示，但不计入发布阻断口径。',
            },
            'failures': report.get('failures', []),
        }

    def _dispatch_technique_endpoint(self, endpoint, payload):
        dispatch = {
            '/api/ashtakavarga': self._compute_ashtakavarga,
            '/api/bhava_bala': self._compute_bhava_bala_api,
            '/api/bhava_chalit': self._compute_bhava_chalit,
            '/api/career': self._compute_career,
            '/api/case_validation': self._compute_case_validation,
            '/api/dasha': self._compute_dasha_system,
            '/api/dasha/chara': self._compute_chara_dasha,
            '/api/deep_varga_avastha': self._compute_deep_varga_avastha,
            '/api/divisional_yoga': self._compute_divisional_yoga,
            '/api/jaimini': self._compute_jaimini,
            '/api/kakshya': self._compute_kakshya,
            '/api/kp': self._compute_kp,
            '/api/muhurta': self._compute_muhurta,
            '/api/nakshatra_full': self._compute_nakshatra_full,
            '/api/pancha_mahapurusha': self._compute_pmc,
            '/api/prashna': self._compute_prashna,
            '/api/rectification_gate': self._compute_rectification_gate,
            '/api/relationship': self._compute_relationship,
            '/api/remedies': self._compute_remedies,
            '/api/sade_sati': self._compute_sade_sati,
            '/api/shadbala': self._compute_shadbala,
            '/api/sudarshana': self._compute_sudarshana,
            '/api/synastry': self._compute_synastry,
            '/api/consultation_workflow': self._compute_consultation_workflow,
            '/api/high_rigor_workflow': self._compute_high_rigor_workflow,
            '/api/thematic_report': self._compute_thematic_report,
            '/api/transit': self._compute_transit_triggers,
            '/api/varga_full': self._compute_varga_full,
            '/api/yogas': self._compute_yogas_api,
        }
        return dispatch[endpoint](payload)

    def _sanitize_technique_example_payload(self, endpoint, payload):
        text = json.dumps(payload, ensure_ascii=False, default=str)
        if len(text) > 120_000:
            raise BadRequest('technique example payload too large')
        if endpoint == '/api/transit':
            start_raw = str(payload.get('start', payload.get('start_date', datetime.now().strftime('%Y-%m-%d'))))[:10]
            try:
                start = datetime.strptime(start_raw, '%Y-%m-%d')
            except ValueError as e:
                raise BadRequest('transit start must be YYYY-MM-DD') from e
            end = payload.get('end') or payload.get('end_date')
            if end:
                try:
                    end_dt = datetime.strptime(str(end)[:10], '%Y-%m-%d')
                except ValueError as e:
                    raise BadRequest('transit end must be YYYY-MM-DD') from e
                if (end_dt - start).days > 180:
                    payload = {**payload, 'end': (start + timedelta(days=180)).strftime('%Y-%m-%d')}
            else:
                payload = {**payload, 'end': (start + timedelta(days=90)).strftime('%Y-%m-%d')}
        return payload

    def _technique_api_docs(self):
        docs = {}
        payloads = self._technique_example_payloads()
        for endpoint in sorted(TECHNIQUE_EXAMPLE_ENDPOINTS):
            payload = payloads.get(endpoint, {})
            docs[endpoint] = {
                'method': 'POST',
                'endpoint': endpoint,
                'curl': self._curl_example(endpoint, payload),
                'openapi': self._openapi_operation(endpoint, payload),
                'notes': self._endpoint_method_notes(endpoint),
            }
        return docs

    def _technique_method_doc(self, technique, product, endpoint):
        return {
            'summary': product.get('reason') or technique.get('limitation') or technique.get('audit_label') or technique.get('name') or '',
            'boundary': product.get('next_action') or technique.get('missing_impact') or '把该技法作为证据层使用，并结合 Dasha、Transit、案例验证共同收敛。',
            'primary_endpoint': endpoint,
            'source_paths': sorted(set((technique.get('output_paths') or []) + (product.get('output_paths') or [])))[:8],
            'api_doc_key': endpoint if endpoint in TECHNIQUE_EXAMPLE_ENDPOINTS else '',
        }

    def _curl_example(self, endpoint, payload):
        body = json.dumps(payload or {}, ensure_ascii=False, indent=2, sort_keys=True)
        return (
            "curl -sS -X POST http://127.0.0.1:5200"
            f"{endpoint} \\\n"
            "  -H 'Content-Type: application/json' \\\n"
            "  --data-binary "
            + json.dumps(body, ensure_ascii=False)
        )

    def _openapi_operation(self, endpoint, payload):
        return {
            'path': endpoint,
            'post': {
                'summary': self._endpoint_summary(endpoint),
                'operationId': self._endpoint_operation_id(endpoint),
                'requestBody': {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'object',
                                'additionalProperties': True,
                                'example': payload or {},
                            },
                        },
                    },
                },
                'responses': {
                    '200': {
                        'description': 'Successful Jyotish calculation result',
                        'content': {
                            'application/json': {
                                'schema': {'type': 'object', 'additionalProperties': True},
                            },
                        },
                    },
                    '400': {'description': 'Invalid payload or unsupported option'},
                },
            },
        }

    def _endpoint_operation_id(self, endpoint):
        return 'post' + ''.join(part.title() for part in endpoint.strip('/').replace('_', '-').split('-'))

    def _endpoint_summary(self, endpoint):
        labels = {
            '/api/ashtakavarga': 'Compute SAV/BAV/PAV/Sodhita Ashtakavarga evidence',
            '/api/bhava_bala': 'Compute Bhava Bala house strength evidence',
            '/api/bhava_chalit': 'Compare Rashi and Bhava Chalit house placements',
            '/api/career': 'Compute career analysis from planets and ascendant',
            '/api/case_validation': 'Run case validation and MEVG gate status',
            '/api/dasha': 'Compute Dasha periods and Vimshottari analysis layer',
            '/api/dasha/chara': 'Compute explicit Jaimini Chara Dasha timing layer',
            '/api/deep_varga_avastha': 'Compute Sayanadi/Shayanadi avastha and D24/D30/D60 templates',
            '/api/divisional_yoga': 'Detect D9/D10/D12 divisional yogas',
            '/api/jaimini': 'Compute Jaimini karaka, arudha, dasha, and karakamsha data',
            '/api/kakshya': 'Compute Kakshya degree-level trigger support',
            '/api/kp': 'Compute KP significator and sublord analysis',
            '/api/muhurta': 'Compute Muhurta day quality evidence',
            '/api/nakshatra_full': 'Compute advanced Nakshatra report',
            '/api/pancha_mahapurusha': 'Assess Pancha Mahapurusha yoga strength',
            '/api/prashna': 'Compute Prashna chart and answer evidence',
            '/api/rectification_gate': 'Evaluate birth-time precision gate',
            '/api/relationship': 'Compute relationship and spouse-status evidence',
            '/api/remedies': 'Generate low-risk remedies from doshas/strength/dasha',
            '/api/sade_sati': 'Compute Sade Sati status and phase',
            '/api/shadbala': 'Compute Shadbala plus advanced evidence layer',
            '/api/sudarshana': 'Compute Sudarshana Chakra evidence',
            '/api/synastry': 'Compute 16-factor/Ashtakoot compatibility score',
            '/api/consultation_workflow': 'Unified user consultation workflow for direct charting or rectification-first entry',
            '/api/high_rigor_workflow': 'Compose VedAstro-first chart evidence, rectification gate, historical backtest, and thematic report',
            '/api/thematic_report': 'Generate thematic report with sample/custom/derived evidence',
            '/api/transit': 'Search transit trigger windows',
            '/api/varga_full': 'Compute divisional chart positions',
            '/api/yogas': 'Compute yoga rule-engine and curse-yoga evidence',
        }
        return labels.get(endpoint, f'Run {endpoint} calculation')

    def _endpoint_method_notes(self, endpoint):
        notes = {
            '/api/thematic_report': '传 birth/chart payload 时会进入 derived_chart_evidence；只传 theme 时使用样例证据。',
            '/api/consultation_workflow': '统一 direct_chart / rectification 入口；网页/app 与 skill/MCP 共用同一套问题路由和官方优先证据 contract。',
            '/api/high_rigor_workflow': '复用 chart、rectification_gate、historical_event_backtest 与 thematic_report；不重写底层算法。',
            '/api/shadbala': 'advanced_layer 是证据补充，不覆盖主 Shadbala 总分。',
            '/api/yogas': 'curse_yogas 是高风险提示层，不能替代健康/法律/安全建议。',
            '/api/case_validation': 'MEVG 只读门控不运行外部子进程。',
            '/api/report_artifact': '报告 artifact 不在 Technique Explorer 白名单内，避免把任意 HTML 当作样例执行。',
        }
        return notes.get(endpoint, '样例 payload 可直接复制到本地 API；正式报告仍需结合上下文和边界说明。')

    def _technique_example_payloads(self):
        today = datetime.utcnow().strftime('%Y-%m-%d')
        transit_end = (datetime.utcnow() + timedelta(days=60)).strftime('%Y-%m-%d')
        base = {
            'planets': SAMPLE_PLANETS,
            'ascendant': SAMPLE_ASCENDANT,
        }
        birth = {
            'year': 1990,
            'month': 1,
            'day': 1,
            'hour': 12,
            'minute': 0,
            'lat': 28.6,
            'lon': 77.2,
            'tz': 5.5,
        }
        return {
            '/api/ashtakavarga': base,
            '/api/bhava_bala': base,
            '/api/bhava_chalit': {**base, 'mode': 'compare', 'house_system': 'sripati'},
            '/api/career': {'planets': SAMPLE_PLANETS, 'asc_sign': 'Aries'},
            '/api/case_validation': {**base, 'current_md': 'Jupiter', 'predicted_events': ['事业巅峰', '关系发展'], 'transit_desc': 'Double Jupiter Saturn activation'},
            '/api/dasha': {**base, **birth, 'dasha': 'vimshottari'},
            '/api/dasha/chara': {**base, **birth, 'antardasha': True},
            '/api/deep_varga_avastha': base,
            '/api/divisional_yoga': {**base, 'divisions': ['D9', 'D10', 'D12']},
            '/api/jaimini': {**base, **birth, 'mode': 'all'},
            '/api/kakshya': base,
            '/api/kp': {'planets': SAMPLE_PLANETS, 'asc_sign_idx': 0},
            '/api/muhurta': {'date': today, 'activity': 'business', 'hour_from_sunrise': 6.0},
            '/api/nakshatra_full': {**base, 'age': 36, 'transit_date': today},
            '/api/pancha_mahapurusha': {'planets': SAMPLE_PLANETS, 'sun_degree': SAMPLE_PLANETS['Sun']['lon']},
            '/api/prashna': {'planets': SAMPLE_PLANETS, 'question': 'general'},
            '/api/rectification_gate': {**base, 'declared_accuracy': 'minute', 'time_source': 'family_clear'},
            '/api/relationship': {'planets': SAMPLE_PLANETS, 'asc_sign': 'Aries', 'dasha_info': {'maha_dasha': 'Venus', 'antar_dasha': 'Jupiter'}},
            '/api/remedies': {'shadbala': {'Sun': {'rupas': 4.1}, 'Moon': {'rupas': 3.8}}, 'doshas': ['manglik'], 'dasha_lord': 'Venus'},
            '/api/sade_sati': {'moon_degree': SAMPLE_PLANETS['Moon']['lon'], 'asc_degree': SAMPLE_ASCENDANT['lon'], 'saturn_degree': SAMPLE_PLANETS['Saturn']['lon']},
            '/api/shadbala': {**base, **birth},
            '/api/sudarshana': base,
            '/api/synastry': {'male_moon': SAMPLE_PLANETS['Moon']['lon'], 'female_moon': 243.0},
            '/api/high_rigor_workflow': {
                **birth,
                'lat': 36.42,
                'lon': 114.2,
                'tz': 8,
                'dry_run': True,
                'theme': ['career', 'marriage', 'wealth'],
                'events': [
                    {'date': '2019-12-15', 'domain': 'career', 'summary': '事业逐渐好转'},
                    {'date': '2025-02-28', 'domain': 'wealth', 'summary': '项目结束与现金流变化'},
                ],
            },
            '/api/consultation_workflow': {
                **birth,
                'lat': 36.42,
                'lon': 114.2,
                'tz': 8,
                'dry_run': True,
                'entry_mode': 'direct_chart',
                'theme': ['career', 'marriage', 'wealth'],
                'question': '请直接排盘并进入互动解盘',
            },
            '/api/thematic_report': {'theme': 'marriage'},
            '/api/transit': {'natal_planets': SAMPLE_PLANETS, 'ascendant': SAMPLE_ASCENDANT, 'start': today, 'end': transit_end, 'planets_to_check': ['Saturn', 'Jupiter', 'Rahu', 'Ketu']},
            '/api/varga_full': {**base, 'divisions': ['D9', 'D10']},
            '/api/yogas': base,
        }

    def _read_technique_registry(self):
        path = os.path.join(REPO_ROOT, 'references', 'technique_registry.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
        return {'version': None, 'techniques': {}}

    def _scan_engine_commands(self):
        path = os.path.join(SCRIPTS_DIR, 'jyotish_engine.py')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []
        return sorted(set(re.findall(r"add_parser\(['\"]([^'\"]+)['\"]", text)))

    def _scan_api_endpoints(self):
        path = os.path.abspath(__file__)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []
        return sorted(set(re.findall(r"path == ['\"](/api/[^'\"]+)['\"]", text)))

    def _scan_app_tabs(self):
        path = os.path.join(REPO_ROOT, 'jyotish-app', 'index.html')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []
        return sorted(set(re.findall(r'data-tab="([^"]+)"', text)))

    def _scan_app_source_text(self):
        root = os.path.join(REPO_ROOT, 'jyotish-app')
        if not os.path.isdir(root):
            return ''
        chunks = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d for d in dirnames
                if d not in {'node_modules', 'dist', '.vite', '.git'}
            ]
            for filename in filenames:
                if not filename.endswith(('.js', '.html', '.css')):
                    continue
                try:
                    with open(os.path.join(dirpath, filename), 'r', encoding='utf-8', errors='ignore') as f:
                        chunks.append(f.read(40000))
                except OSError:
                    continue
        return '\n'.join(chunks).lower()

    def _scan_local_open_source_sources(self):
        root = os.path.join(REPO_ROOT, 'references', 'open_source_sources')
        if not os.path.isdir(root):
            return []
        sources = []
        for name in sorted(os.listdir(root)):
            path = os.path.join(root, name)
            if not os.path.isdir(path):
                continue
            files = []
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = [d for d in dirnames if d not in {'.git', '__pycache__', '.pytest_cache'}]
                for filename in filenames:
                    rel = os.path.relpath(os.path.join(dirpath, filename), path)
                    files.append(rel)
                    if len(files) >= 500:
                        break
                if len(files) >= 500:
                    break
            license_name = self._detect_source_license(path, files)
            if license_name == 'unknown':
                license_name = self._license_from_research_index(name)
            sources.append({
                'name': name,
                'path': os.path.relpath(path, REPO_ROOT),
                'file_count': len(files),
                'license': license_name,
                'reuse': self._reuse_level(license_name),
                'modules': self._infer_source_modules(files),
                'has_readme': any(os.path.basename(f).lower() == 'readme.md' for f in files),
                'has_skill': any(os.path.basename(f).lower() == 'skill.md' for f in files),
            })
        return sources

    def _detect_source_license(self, source_path, files):
        license_files = [
            f for f in files
            if os.path.basename(f).lower() in {'license', 'license.md', 'licence', 'licence.md', 'copying'}
        ]
        text = ''
        for rel in license_files[:2]:
            try:
                with open(os.path.join(source_path, rel), 'r', encoding='utf-8', errors='ignore') as f:
                    text += '\n' + f.read(6000)
            except OSError:
                continue
        haystack = (text + '\n' + source_path).lower()
        if 'agpl' in haystack:
            return 'AGPL'
        if 'gpl' in haystack and 'lesser' not in haystack:
            return 'GPL'
        if 'apache license' in haystack or 'apache-2.0' in haystack:
            return 'Apache-2.0'
        if 'mit license' in haystack or '/mit' in haystack:
            return 'MIT'
        return 'unknown'

    def _license_from_research_index(self, source_name):
        scan_path = os.path.join(REPO_ROOT, 'references', 'open-source-jyotish-scan-2026.md')
        integration_path = os.path.join(REPO_ROOT, 'references', 'open_source_sources', 'INTEGRATION_REPORT.md')
        text = ''
        for path in (scan_path, integration_path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    text += '\n' + f.read()
            except OSError:
                continue
        if not text:
            return 'unknown'
        escaped = re.escape(source_name)
        patterns = [
            rf'\|\s*\*\*{escaped}\*\*\s*\|[^|\n]*\|\s*(MIT|Apache-2\.0|AGPL|GPL)',
            rf'{escaped}[^\n]{{0,80}}\((MIT|Apache-2\.0|AGPL|GPL)',
            rf'{escaped}[^\n]{{0,80}}\|\s*(MIT|Apache-2\.0|AGPL|GPL)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                license_name = match.group(1)
                if license_name.lower() == 'mit':
                    return 'MIT (research)'
                if license_name.lower().startswith('apache'):
                    return 'Apache-2.0 (research)'
                return f'{license_name.upper()} (research)'
        return 'unknown'

    def _reuse_level(self, license_name):
        base_license = (license_name or '').split(' ', 1)[0]
        if base_license in {'MIT', 'Apache-2.0'}:
            return 'direct'
        if base_license in {'AGPL', 'GPL'}:
            return 'caution'
        return 'unknown'

    def _infer_source_modules(self, files):
        module_keywords = {
            'ashtakavarga': ['ashtakavarga'],
            'shadbala': ['shadbala', 'strength'],
            'dasha': ['dasha', 'dasa', 'dashas'],
            'jaimini': ['jaimini', 'karaka', 'arudha'],
            'kp': ['kp', 'sublord', 'horary'],
            'prashna': ['prashna', 'prasna', 'horary'],
            'muhurta': ['muhurta', 'muhurtha'],
            'tajika': ['tajika', 'varsha', 'solar_return'],
            'synastry': ['synastry', 'matchmaking', 'compat'],
            'remedies': ['remedies', 'upaya'],
            'panchanga': ['panchang', 'panchanga', 'tithi'],
            'varga': ['varga', 'divisional'],
            'yoga': ['yoga'],
            'transit': ['transit', 'gochar'],
        }
        lower_files = [f.lower() for f in files]
        found = []
        for module, keywords in module_keywords.items():
            if any(any(keyword in f for keyword in keywords) for f in lower_files):
                found.append(module)
        return found

    def _app_visible_topics(self, tabs):
        mapping = {
            'chart': 'D1/Rashi',
            'complete': 'Full Reading',
            'karaka': 'Jaimini Karaka',
            'houses': 'Bhava',
            'aspects': 'Aspects',
            'yogas': 'Yoga',
            'vargas': 'Varga',
            'ashtakavarga': 'Ashtakavarga',
            'shadbala': 'Shadbala',
            'dasha': 'Dasha',
            'transit': 'Transit',
            'deep': 'PACDARES/Argala',
            'extended': 'Bhava Bala/Vimsopaka',
            'remedies': 'Remedies',
            'synastry': 'Synastry',
            'prashna': 'Prashna',
            'kp': 'KP',
            'verify': 'Verification',
            'transit-compare': 'Transit Compare',
        }
        topics = [mapping[t] for t in tabs if t in mapping]
        source_text = self._scan_app_source_text()
        source_markers = {
            'Muhurta': ['computemuhurta', 'muhurta'],
            'Tajika': ['computeannual', 'varshaphala', 'tajika'],
            'Solar Return': ['computeannual', 'solar return', 'varshaphala'],
            'Bhava Chalit': ['computebhavachalit', 'bhava chalit', 'bhava_chalit'],
            'Sudarshana': ['computesudarshana', 'sudarshana'],
            'Nakshatra Full': ['computenakshatrafull', 'nakshatra_full'],
            'Varga Full': ['computevargafull', 'varga_full'],
            'Jaimini': ['computejaimini', '/api/jaimini'],
            'Ashtakavarga': ['computeashtakavarga', '/api/ashtakavarga'],
            'Shadbala': ['computeshadbala', '/api/shadbala'],
            'Yoga': ['computeyogas', '/api/yogas'],
            'Aspects': ['computeaspects', '/api/aspects'],
            'Birth Rectification': ['computerectificationgate', '/api/rectification_gate', 'rectification', 'rect-prompt'],
            'Case Validation': ['computecasevalidation', '/api/case_validation', 'case validation', 'mevg'],
            'Deep Varga Avastha': ['deepvargaavastha', '/api/deep_varga_avastha', 'sayanadi/shayanadi', 'd24/d30/d60'],
            'Divisional Yoga': ['computedivisionalyoga', '/api/divisional_yoga', 'divisional yoga'],
            'Kakshya': ['computekakshya', '/api/kakshya', 'kakshya'],
            'Career': ['computecareer', '/api/career', 'career analysis', '事业分析'],
            'Relationship': ['computerelationship', '/api/relationship', 'relationship analysis', '感情分析'],
            'KP System': ['computekp', '/api/kp', 'kp sublord', 'kp分析'],
            'Prashna': ['computeprashna', '/api/prashna', 'prashna', '问事'],
            'Synastry 16-factor': ['computesynastry', '/api/synastry', 'ashtakoot', '合盘'],
            'Bhava Bala': ['computebhavabala', '/api/bhava_bala', 'bhava bala'],
            'Transit Trigger': ['computetransittriggers', '/api/transit', 'transit trigger', '过境触发'],
            'Thematic Report': ['computethematicreport', '/api/thematic_report', 'thematic report', '主题化报告'],
        }
        for topic, markers in source_markers.items():
            if any(marker in source_text for marker in markers) and topic not in topics:
                topics.append(topic)
        return topics

    def _build_priority_gaps(self, techniques, engine_not_api, app_visible_topics):
        api_gap_commands = {'varga-full', 'bhava-chalit', 'sudarshana', 'tajika', 'solar-return', 'muhurta', 'nakshatra-full', 'audit-capabilities'}
        gaps = []
        for command in sorted(api_gap_commands & set(engine_not_api)):
            related = [
                value.get('name', key)
                for key, value in techniques.items()
                if command in value.get('commands', [])
            ][:4]
            gaps.append({
                'kind': 'engine_not_api',
                'command': command,
                'priority': 'high',
                'reason': '引擎已有命令，但 Web API/用户端未直接承载完整工作流。',
                'related_techniques': related,
            })
        visible_lower = ' '.join(app_visible_topics).lower()
        for topic in ['muhurta', 'tajika', 'solar return', 'bhava chalit', 'sudarshana']:
            if topic not in visible_lower:
                gaps.append({
                    'kind': 'app_visibility',
                    'topic': topic,
                    'priority': 'medium',
                    'reason': '前端缺少独立入口或专题化展示，用户不容易发现已有能力。',
                })
        return gaps[:12]

    def _build_productization_matrix(self, techniques, engine_commands, api_backed_commands, app_visible_topics):
        app_text = ' '.join(app_visible_topics).lower()
        productized_markers = {
            'd1': ['d1', 'rashi', 'chart', '本命盘'],
            'd9': ['d9', 'navamsa', 'varga', '分盘'],
            'd10': ['d10', 'dasamsa', 'varga'],
            'varga': ['varga', '分盘'],
            'jaimini': ['jaimini', 'karaka', 'arudha'],
            'karaka': ['karaka', 'jaimini'],
            'arudha': ['arudha', 'jaimini'],
            'ashtakavarga': ['ashtakavarga'],
            'shadbala': ['shadbala'],
            'yoga': ['yoga', '格局'],
            'dosha': ['dosha', 'remedies'],
            'dasha': ['dasha'],
            'nakshatra': ['nakshatra'],
            'muhurta': ['muhurta'],
            'tajika': ['tajika', 'solar return', 'varshaphala'],
            'annual': ['tajika', 'solar return', 'varshaphala'],
            'bhava': ['bhava'],
            'bhava-bala': ['bhava bala', 'bhava'],
            'transit': ['transit'],
            'transit-trigger': ['transit trigger', 'transit', '过境触发'],
            'kp': ['kp'],
            'prashna': ['prashna'],
            'synastry': ['synastry'],
            'relationship': ['relationship', 'synastry'],
            'remedies': ['remedies'],
            'aspects': ['aspects'],
            'sudarshana': ['sudarshana'],
            'career': ['career'],
            'marriage': ['navamsa', 'synastry', 'relationship'],
            'birth': ['birth rectification', 'rectification', '生时校正'],
            'rectification': ['birth rectification', 'rectification', '生时校正'],
            'case': ['case validation', 'mevg', '验证'],
            'validation': ['case validation', 'mevg', '验证'],
            'misconceptions': ['case validation', 'mevg', '验证'],
            'muhurtha': ['muhurta'],
            'varshaphala': ['tajika', 'solar return', 'varshaphala'],
            'deep-varga-avastha': ['deep varga avastha', 'deep varga', 'd24/d30/d60'],
            'avastha': ['deep varga avastha', 'sayanadi/shayanadi'],
            'd24': ['d24/d30/d60'],
            'd30': ['d24/d30/d60'],
            'd60': ['d24/d30/d60'],
            'divisional': ['divisional yoga', 'varga', '分盘'],
            'kakshya': ['kakshya', 'ashtakavarga'],
        }
        api_only_commands = sorted(api_backed_commands - {'chart', 'full-reading'})
        rows = []
        summary = {
            'productized': 0,
            'api_backed': 0,
            'engine_or_full_reading': 0,
            'registry_only': 0,
        }

        for key, technique in sorted(techniques.items()):
            commands = [c for c in technique.get('commands', []) if isinstance(c, str)]
            domains = [d for d in technique.get('domains', []) if isinstance(d, str)]
            output_paths = technique.get('output_paths', [])
            inferred_commands = self._inferred_commands_for_technique(key, technique)
            all_commands = sorted(set(commands + inferred_commands))
            api_commands = [command for command in commands if command in api_backed_commands]
            api_commands = sorted(set(api_commands + [command for command in inferred_commands if command in api_backed_commands]))
            engine_hits = [command for command in all_commands if command in engine_commands]
            marker_terms = []
            for token in [key, *domains, *all_commands]:
                token_lower = token.lower()
                marker_terms.extend(productized_markers.get(token_lower, []))
                marker_terms.append(token_lower.replace('-', ' '))
                marker_terms.append(token_lower.replace('_', ' '))
            visible_markers = sorted({
                marker
                for marker in marker_terms
                if marker and marker in app_text
            })

            if visible_markers and (api_commands or 'full-reading' in commands or output_paths):
                level = 'productized'
                reason = '前端已有可见入口，并且有 API/full-reading/输出路径承载。'
            elif api_commands:
                level = 'api_backed'
                reason = '已有 Web API，但用户端需要更明确的专题解释或引导。'
            elif engine_hits or 'full-reading' in commands or output_paths:
                level = 'engine_or_full_reading'
                reason = '引擎、完整解盘或输出路径已覆盖，但缺少独立产品化入口。'
            else:
                level = 'registry_only'
                reason = '注册表中存在，但未自动识别到命令/API/前端入口。'

            summary[level] += 1
            rows.append({
                'id': key,
                'name': technique.get('name', key),
                'level': level,
                'reason': reason,
                'domains': domains,
                'commands': all_commands,
                'api_commands': api_commands,
                'output_paths': output_paths,
                'visible_markers': visible_markers[:6],
                'status': technique.get('status', 'unknown'),
                'next_action': self._productization_next_action(level, all_commands, api_commands, visible_markers),
            })

        next_queue = [
            row for row in rows
            if row['level'] in {'api_backed', 'engine_or_full_reading', 'registry_only'}
        ]
        priority_order = {'api_backed': 0, 'engine_or_full_reading': 1, 'registry_only': 2}
        next_queue.sort(key=lambda row: (priority_order[row['level']], row['name']))
        return {
            'summary': summary,
            'rows': rows,
            'next_queue': next_queue[:18],
            'api_only_commands': api_only_commands,
        }

    def _inferred_commands_for_technique(self, key, technique):
        domains = set(technique.get('domains') or [])
        name = str(technique.get('name', '')).lower()
        path_text = ' '.join(str(path).lower() for path in technique.get('output_paths', []))
        inferred = []
        if key == 'career_engine' or 'career_analysis.py' in path_text or 'career' in domains:
            inferred.append('career')
        if key == 'relationship_engine' or 'relationship_analysis.py' in path_text or 'relationship' in domains:
            inferred.append('relationship')
        if key == 'kp_system' or 'kp_system.py' in path_text or 'kp' in domains:
            inferred.append('kp')
        if key == 'prashna' or 'prashna.py' in path_text or 'prashna' in domains:
            inferred.append('prashna')
        if key == 'synastry_16factor' or 'synastry.py' in path_text or 'synastry' in domains:
            inferred.append('synastry')
        if key == 'remedies' or 'remedies.py' in path_text or 'remedies' in domains:
            inferred.append('remedies')
        if key == 'bhava_bala' or 'bhava_bala.py' in path_text:
            inferred.append('bhava-bala')
        if key == 'transit_trigger' or 'transit_trigger.py' in path_text:
            inferred.append('transit-trigger')
        if key == 'thematic_report_orchestrator' or 'report_orchestrator.py' in path_text or {'report', 'reading'} & domains:
            inferred.append('thematic-report')
        if key == 'divisional_yoga' or 'divisional_yoga.py' in path_text:
            inferred.append('divisional-yoga')
        if key == 'deep_varga_avastha' or 'deep_varga_avastha.py' in path_text:
            inferred.append('deep-varga-avastha')
        if key == 'birth_time_rectifier' or 'birth_time_rectifier.py' in path_text:
            inferred.append('rectification')
        if key == 'case_validator' or 'case_validator.py' in path_text:
            inferred.append('case-validation')
        if key == 'kakshya' or 'kakshya.py' in path_text:
            inferred.append('kakshya')
        if key == 'muhurtha' or 'muhurtha' in domains or 'muhurtha_election.py' in path_text:
            inferred.append('muhurta')
        if key == 'varshaphala' or 'varshaphala' in domains or 'varshaphala.py' in path_text:
            inferred.append('solar-return')
        if 'ashtakavarga' in domains and 'prastara' in name:
            inferred.append('ashtakavarga')
        if 'ashtakavarga' in domains and 'sodhita' in name:
            inferred.append('ashtakavarga')
        if key == 'bhrigu_bindu' or 'calc_bhrigu_bindu' in path_text:
            inferred.append('full-reading')
            inferred.append('varga-full')
        return sorted(set(inferred))

    def _productization_next_action(self, level, commands, api_commands, visible_markers):
        if level == 'api_backed':
            return '把 API 结果转成结论卡、证据卡和交叉验证提示。'
        if level == 'engine_or_full_reading':
            if any(command in {'transit', 'narayana-dasha', 'nakshatra-dasha', 'vivah-saham', 'transit-ll7l'} for command in commands):
                return '优先 API 化，并加入高级技法工作台或专题 Tab。'
            return '梳理到完整解盘主流程，补用户可见入口。'
        if level == 'registry_only':
            return '确认是否仍是有效技法；若有效，补命令/API/输出路径。'
        if visible_markers:
            return '继续优化解释层和移动端可读性。'
        return '保持监控。'

    def _build_ux_productization_matrix(self, product_rows):
        rows = []
        summary = {
            'excellent': 0,
            'usable': 0,
            'thin': 0,
            'not_user_ready': 0,
        }
        criteria_keys = [
            'clear_entry',
            'human_readable_conclusion',
            'evidence_chain',
            'next_action',
            'json_hidden',
            'mobile_scannable',
        ]
        for row in product_rows:
            criteria = self._ux_criteria_for_row(row)
            score = sum(1 for key in criteria_keys if criteria.get(key))
            if score >= 5:
                ux_level = 'excellent'
            elif score >= 4:
                ux_level = 'usable'
            elif score >= 2:
                ux_level = 'thin'
            else:
                ux_level = 'not_user_ready'
            summary[ux_level] += 1
            missing = [key for key in criteria_keys if not criteria.get(key)]
            rows.append({
                **row,
                'ux_score': score,
                'ux_level': ux_level,
                'criteria': criteria,
                'missing_ux': missing,
                'ux_next_action': self._ux_next_action(ux_level, missing, row),
            })
        queue = [row for row in rows if row['ux_level'] != 'excellent']
        level_order = {'not_user_ready': 0, 'thin': 1, 'usable': 2, 'excellent': 3}
        queue.sort(key=lambda row: (level_order[row['ux_level']], -row['ux_score'], row['name']))
        return {
            'criteria': criteria_keys,
            'summary': summary,
            'rows': rows,
            'next_queue': queue[:18],
        }

    def _ux_criteria_for_row(self, row):
        level = row.get('level')
        commands = set(row.get('commands') or [])
        api_commands = set(row.get('api_commands') or [])
        domains = set(row.get('domains') or [])
        visible_markers = set(row.get('visible_markers') or [])
        name = row.get('name', '').lower()
        row_id = row.get('id', '').lower()
        has_api = bool(api_commands - {'full-reading'}) or any(
            command in api_commands
            for command in {'dasha', 'jaimini', 'ashtakavarga', 'shadbala', 'yoga', 'muhurta', 'solar-return', 'sudarshana', 'nakshatra-full', 'varga-full', 'rectification', 'case-validation', 'deep-varga-avastha', 'divisional-yoga', 'kakshya', 'career', 'relationship', 'kp', 'prashna', 'synastry', 'remedies', 'bhava-bala', 'transit-trigger', 'thematic-report'}
        )
        source_backed = level == 'productized' and bool(row.get('output_paths'))
        clear_entry = level == 'productized' and bool(visible_markers)
        human_readable = bool(
            source_backed
            or commands & {'full-reading', 'chart', 'dasha', 'jaimini', 'ashtakavarga', 'muhurta', 'solar-return', 'sudarshana', 'rectification', 'case-validation', 'deep-varga-avastha', 'divisional-yoga', 'kakshya', 'career', 'relationship', 'kp', 'prashna', 'synastry', 'remedies', 'bhava-bala', 'transit-trigger', 'thematic-report'}
            or domains & {'core', 'relationship', 'marriage', 'career', 'remedies', 'muhurta', 'muhurtha', 'tajika', 'varshaphala', 'birth', 'case', 'misconceptions', 'divisional', 'kakshya', 'kp', 'prashna', 'synastry', 'ashtakavarga', 'bhava', 'transit', 'avastha', 'd24', 'd30', 'd60'}
            or any(token in name for token in ['reading', 'analysis', 'report'])
        )
        evidence_chain = bool(
            has_api
            or source_backed
            or commands & {'full-reading', 'varga-full', 'ashtakavarga', 'shadbala', 'jaimini', 'yoga', 'dasha', 'case-validation', 'deep-varga-avastha', 'divisional-yoga', 'kakshya', 'career', 'relationship', 'kp', 'prashna', 'synastry', 'remedies', 'bhava-bala', 'transit-trigger', 'thematic-report'}
            or domains & {'strength', 'timing', 'varga', 'dasha', 'jaimini', 'ashtakavarga', 'remedies', 'birth', 'case', 'misconceptions', 'divisional', 'kakshya', 'kp', 'prashna', 'synastry', 'bhava', 'transit', 'avastha', 'd24', 'd30', 'd60'}
        )
        next_action = bool(
            domains & {'remedies', 'muhurta', 'muhurtha', 'career', 'relationship', 'marriage', 'timing', 'event', 'birth', 'case', 'varshaphala', 'divisional', 'kakshya', 'kp', 'prashna', 'synastry', 'bhava', 'transit', 'avastha', 'd24', 'd30', 'd60'}
            or row.get('next_action')
        )
        hidden_json_rows = {
            'bhava_bala',
            'birth_time_rectifier',
            'career_engine',
            'case_validator',
            'deep_varga_avastha',
            'divisional_yoga',
            'kakshya',
            'misconceptions',
            'relationship_engine',
            'remedies',
            'transit_trigger',
            'full_reading_strict',
        }
        json_hidden = level == 'productized' and (
            bool(api_commands)
            or row_id in hidden_json_rows
            or (not row_id.endswith('_engine') and '.py' not in name)
        )
        mobile_scannable = clear_entry and (human_readable or evidence_chain)
        return {
            'clear_entry': clear_entry,
            'human_readable_conclusion': human_readable,
            'evidence_chain': evidence_chain,
            'next_action': next_action,
            'json_hidden': json_hidden,
            'mobile_scannable': mobile_scannable,
        }

    def _ux_next_action(self, ux_level, missing, row):
        if ux_level == 'excellent':
            return '保持现有入口，继续做文案和移动端微调。'
        if 'human_readable_conclusion' in missing:
            return '把计算结果转成用户可读结论卡，并说明它支持哪个判断。'
        if 'clear_entry' in missing:
            return '补清晰入口或把该技法合并进完整解盘主流程。'
        if 'evidence_chain' in missing:
            return '补证据链：引用具体行星、宫位、分盘、Dasha 或相位。'
        if 'json_hidden' in missing:
            return '默认隐藏 JSON，只保留展开查看；主视图展示摘要。'
        if 'mobile_scannable' in missing:
            return '重排移动端卡片密度，保证三分钟内能读到结论。'
        return row.get('next_action') or '补用户体验解释层。'

    def _external_research_matrix(self):
        return [
            {
                'name': 'PyJHora',
                'url': 'https://github.com/naturalstupid/PyJHora',
                'license': 'AGPL-3.0',
                'reuse': 'benchmark_only',
                'notes': '最强传统算法对标；许可证不适合直接复制进 MIT 仓库。',
                'best_for': ['Dasha族', '分盘变体', 'Ashtakavarga高级层', 'JHora口径校准'],
            },
            {
                'name': 'dashaflow',
                'url': 'https://github.com/adarshj322/dashaflow',
                'license': 'MIT',
                'reuse': 'direct',
                'notes': '本地已有源码；适合复用 Ashtakavarga、Shadbala、Jaimini、合盘、Muhurta 的轻量实现。',
                'best_for': ['Ashtakavarga', 'Shadbala', 'Jaimini', 'Synastry', 'Muhurta'],
            },
            {
                'name': 'jyotishganit',
                'url': 'https://github.com/northtara/jyotishganit',
                'license': 'MIT',
                'reuse': 'direct',
                'notes': '高精度结构化计算与 JSON-LD 输出思路，适合用于数据层校准。',
                'best_for': ['D1-D60', 'Panchanga', 'Shadbala', 'JSON-LD'],
            },
            {
                'name': 'VedicAstro',
                'url': 'https://github.com/diliprk/VedicAstro',
                'license': 'unspecified/readme badge',
                'reuse': 'review_before_copy',
                'notes': 'KP 与 Horary 很有价值，但复制前必须确认许可证文件。',
                'best_for': ['KP Sublord', 'ABCD Significators', 'Horary'],
            },
            {
                'name': 'VedAstro',
                'url': 'https://github.com/VedAstro/VedAstro',
                'license': 'MIT',
                'reuse': 'direct_or_port',
                'notes': 'C# API 平台范式，可参考 Web/API 产品化结构。',
                'best_for': ['API Platform', 'Muhurta', 'Panchanga', 'AI Astrologer'],
            },
            {
                'name': 'xalen-ephemeris',
                'url': 'https://github.com/vedika-io/xalen-ephemeris',
                'license': 'Apache-2.0',
                'reuse': 'direct_or_port',
                'notes': 'Rust 高精度星历与多传统系统，适合未来替代/补强天文底座。',
                'best_for': ['Ephemeris', 'Ayanamsa', 'House Systems', 'KP/Jaimini/Tajika'],
            },
        ]


def _parse_allowed_origins(value):
    if not value:
        return DEFAULT_ALLOWED_ORIGINS
    return {item.strip() for item in value.split(',') if item.strip()}


def start_server(port=5200, host='127.0.0.1', allowed_origins=None):
    cleanup = prune_expired_async_jobs()
    server = ThreadingHTTPServer((host, port), JyotishAPIHandler)
    server.daemon_threads = True
    server.allowed_origins = allowed_origins or DEFAULT_ALLOWED_ORIGINS
    print(f'Jyotish API v6.9.14 running on http://{host}:{port}')
    print(f"  Async job cleanup: scanned={cleanup['scanned']}, removed={cleanup['removed']}")
    print(f'  CORS origins: {", ".join(sorted(server.allowed_origins))}')
    print(f'  POST /api/chart — 完整星盘计算')
    print(f'  POST /api/remedies — 补救建议')
    print(f'  POST /api/kp — KP分析')
    print(f'  POST /api/prashna — 卜卦')
    print(f'  POST /api/synastry — 合盘')
    print(f'  POST /api/dasha — 单Dasha时间线')
    print(f'  POST /api/sade_sati — 土星周期')
    print(f'  POST /api/pancha_mahapurusha — 五王瑜伽')
    print(f'  POST /api/career — 事业分析')
    print(f'  POST /api/relationship — 感情分析')
    print(f'  POST /api/annual — 年运/Tajika')
    print(f'  POST /api/muhurta — 择日')
    print(f'  POST /api/panchanga_range — Panchanga日期范围')
    print(f'  POST /api/bhava_chalit — Bhava Chalit')
    print(f'  POST /api/sudarshana — Sudarshana Chakra')
    print(f'  POST /api/nakshatra_full — Nakshatra深层报告')
    print(f'  POST /api/varga_full — BPHS扩展分盘/变体/自定义/复合')
    print(f'  POST /api/jaimini — Jaimini Karaka/Arudha/Chara Dasha')
    print(f'  POST /api/ashtakavarga — Ashtakavarga SAV/BAV')
    print(f'  POST /api/shadbala — Shadbala六重力量')
    print(f'  POST /api/yogas — Yoga格局检测')
    print(f'  POST /api/aspects — 精确相位')
    print(f'  POST /api/report_artifact — HTML/PDF报告工件生成')
    print(f'  POST /api/thematic_report — 主题化报告/冲突裁决')
    print(f'  GET /api/health — 健康检查')
    print(f'  GET /api/cities — 城市列表')
    print(f'  GET /api/capability_audit — 能力审计')
    server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Jyotish API server')
    parser.add_argument('--port', type=int, default=5200)
    parser.add_argument('--host', default=os.environ.get('JYOTISH_API_HOST', '127.0.0.1'))
    parser.add_argument(
        '--allow-origin',
        action='append',
        default=[],
        help='Allowed browser origin; may be repeated. Defaults to local Vite origins.',
    )
    args = parser.parse_args()
    env_origins = _parse_allowed_origins(os.environ.get('JYOTISH_ALLOWED_ORIGINS'))
    cli_origins = set(args.allow_origin)
    start_server(args.port, host=args.host, allowed_origins=cli_origins or env_origins)
