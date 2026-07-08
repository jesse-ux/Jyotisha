#!/usr/bin/env python3
"""Security boundary tests for the lightweight Jyotish API server."""

from __future__ import annotations

import base64
import json
import os
import sys
import time
from io import BytesIO
from pathlib import Path

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import jyotish_api_server  # noqa: E402
from jyotish_api_server import (  # noqa: E402
    DEFAULT_ALLOWED_ORIGINS,
    BadRequest,
    JyotishAPIHandler,
    _load_local_module,
    _parse_allowed_origins,
)


def _handler() -> JyotishAPIHandler:
    return JyotishAPIHandler.__new__(JyotishAPIHandler)


class _FakeHeaders(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class _FakeServer:
    allowed_origins = DEFAULT_ALLOWED_ORIGINS


class _ResponseCaptureHandler(JyotishAPIHandler):
    def __init__(self) -> None:
        self.headers = _FakeHeaders()
        self.server = _FakeServer()
        self.path = '/api/capability_audit'
        self.wfile = BytesIO()
        self.status_code = None
        self.response_headers = []

    def send_response(self, code, message=None):  # noqa: ANN001
        self.status_code = code

    def send_header(self, key, value):  # noqa: ANN001
        self.response_headers.append((key, value))

    def end_headers(self):
        return None

    def _capability_audit(self):
        raise RuntimeError('simulated internal failure')

    def payload(self) -> dict:
        return json.loads(self.wfile.getvalue().decode('utf-8'))


class _HealthCaptureHandler(JyotishAPIHandler):
    def __init__(self) -> None:
        self.headers = _FakeHeaders()
        self.server = _FakeServer()
        self.path = '/api/health'
        self.wfile = BytesIO()
        self.status_code = None
        self.response_headers = []

    def send_response(self, code, message=None):  # noqa: ANN001
        self.status_code = code

    def send_header(self, key, value):  # noqa: ANN001
        self.response_headers.append((key, value))

    def end_headers(self):
        return None

    def payload(self) -> dict:
        return json.loads(self.wfile.getvalue().decode('utf-8'))


class _VedAstroStatusCaptureHandler(JyotishAPIHandler):
    def __init__(self) -> None:
        self.headers = _FakeHeaders()
        self.server = _FakeServer()
        self.path = '/api/vedastro/status'
        self.wfile = BytesIO()
        self.status_code = None
        self.response_headers = []

    def send_response(self, code, message=None):  # noqa: ANN001
        self.status_code = code

    def send_header(self, key, value):  # noqa: ANN001
        self.response_headers.append((key, value))

    def end_headers(self):
        return None

    def payload(self) -> dict:
        return json.loads(self.wfile.getvalue().decode('utf-8'))


class _HighRigorJobCaptureHandler(JyotishAPIHandler):
    def __init__(self, path: str) -> None:
        self.headers = _FakeHeaders()
        self.server = _FakeServer()
        self.path = path
        self.wfile = BytesIO()
        self.status_code = None
        self.response_headers = []

    def send_response(self, code, message=None):  # noqa: ANN001
        self.status_code = code

    def send_header(self, key, value):  # noqa: ANN001
        self.response_headers.append((key, value))

    def end_headers(self):
        return None

    def payload(self) -> dict:
        return json.loads(self.wfile.getvalue().decode('utf-8'))


class _PostCaptureHandler(JyotishAPIHandler):
    def __init__(self, path: str, payload: dict) -> None:
        raw = json.dumps(payload).encode('utf-8')
        self.headers = _FakeHeaders({'Content-Length': str(len(raw))})
        self.server = _FakeServer()
        self.path = path
        self.rfile = BytesIO(raw)
        self.wfile = BytesIO()
        self.status_code = None
        self.response_headers = []

    def send_response(self, code, message=None):  # noqa: ANN001
        self.status_code = code

    def send_header(self, key, value):  # noqa: ANN001
        self.response_headers.append((key, value))

    def end_headers(self):
        return None

    def payload(self) -> dict:
        return json.loads(self.wfile.getvalue().decode('utf-8'))


def test_default_cors_origins_are_local_only() -> None:
    assert 'http://localhost:3456' in DEFAULT_ALLOWED_ORIGINS
    assert '*' not in DEFAULT_ALLOWED_ORIGINS
    assert 'https://example.com' not in DEFAULT_ALLOWED_ORIGINS


def test_env_cors_parser_ignores_empty_entries() -> None:
    assert _parse_allowed_origins('https://app.example.com, ,http://localhost:3456') == {
        'https://app.example.com',
        'http://localhost:3456',
    }


def test_get_internal_errors_are_json_wrapped() -> None:
    handler = _ResponseCaptureHandler()

    handler.do_GET()

    assert handler.status_code == 500
    assert ('Content-Type', 'application/json; charset=utf-8') in handler.response_headers
    payload = handler.payload()
    assert payload['success'] is False
    assert payload['error'] == 'Internal server error'
    assert payload['error_code'] == 'ERR_INTERNAL'


def test_health_endpoint_exposes_runtime_accuracy_metadata() -> None:
    handler = _HealthCaptureHandler()

    handler.do_GET()

    assert handler.status_code == 200
    payload = handler.payload()
    assert payload['status'] == 'ok'
    assert payload['ayanamsa_default'] == 'lahiri'
    assert 'swisseph_available' in payload
    assert 'swisseph_version' in payload


def test_vedastro_status_endpoint_exposes_safe_adapter_state(monkeypatch) -> None:
    monkeypatch.setenv('VEDASTRO_API_ENDPOINT', 'https://vedastro.example.test/secret/path')
    monkeypatch.delenv('VEDASTRO_ENABLE_NETWORK', raising=False)
    handler = _VedAstroStatusCaptureHandler()

    handler.do_GET()

    assert handler.status_code == 200
    payload = handler.payload()
    assert payload['adapter'] == 'vedastro_service_adapter'
    assert payload['configured'] is True
    assert payload['network_enabled'] is False
    assert payload['status'] == 'network_execution_disabled'
    assert payload['endpoint_host'] == 'vedastro.example.test'
    assert 'secret/path' not in json.dumps(payload)
    assert payload['required_env']['endpoint'] == 'VEDASTRO_API_ENDPOINT'
    assert payload['live_profile'] == 'vedastro-live'


def test_vedastro_status_endpoint_honors_explicit_network_disable_even_when_local_env_exists(monkeypatch) -> None:
    monkeypatch.setenv('VEDASTRO_API_ENDPOINT', 'https://vedastro.example.test/secret/path')
    monkeypatch.setenv('VEDASTRO_ENABLE_NETWORK', '0')
    handler = _VedAstroStatusCaptureHandler()

    handler.do_GET()

    payload = handler.payload()
    assert payload['network_enabled'] is False
    assert payload['status'] == 'network_execution_disabled'


def test_vedastro_range_scan_endpoint_uses_user_birth_and_returns_controlled_blocked_state(monkeypatch) -> None:
    monkeypatch.delenv('VEDASTRO_API_ENDPOINT', raising=False)
    monkeypatch.delenv('VEDASTRO_ENABLE_NETWORK', raising=False)
    handler = _PostCaptureHandler('/api/vedastro/range_scan', {
        'domain': 'relationship',
        'start_date': '2026-01-01',
        'end_date': '2026-12-31',
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'second': 0,
        'lat': 36.4467,
        'lon': -122.4194,
        'tz': 8,
        'ayanamsa_policy': 'lahiri',
        'node_policy': 'mean',
    })

    handler.do_POST()

    assert handler.status_code == 200
    payload = handler.payload()
    assert payload['success'] is True
    assert payload['endpoint'] == 'vedastro_range_scan'
    assert payload['ui_domain'] == 'relationship'
    assert payload['adapter_domain'] == 'marriage'
    assert payload['result']['status'] == 'service_endpoint_not_configured'
    assert payload['result']['operation'] == 'range_scan'
    assert payload['result']['request_preview']['year'] == 1955
    assert payload['result']['request_preview']['lat'] == 36.4467
    assert payload['result']['request_preview']['domain'] == 'marriage'
    assert payload['boundary'] == 'VedAstro range scan is optional external timing evidence; local Jyotish gates remain authoritative.'


def test_vedastro_gateway_status_route_is_cn_safe(monkeypatch) -> None:
    monkeypatch.setenv('VEDASTRO_GATEWAY_MODE', 'cn_gateway')
    handler = _handler()

    result = handler._compute_vedastro_gateway_status()

    assert result['scope'] == 'vedastro_gateway'
    assert result['mode'] == 'cn_gateway'
    assert result['direct_browser_access_allowed'] is False
    assert result['frontend_secret_safe'] is True


def test_vedastro_gateway_run_route_returns_gateway_packet(monkeypatch) -> None:
    monkeypatch.setenv('JYOTISH_SKIP_LOCAL_ENV', '1')
    monkeypatch.setenv('VEDASTRO_GATEWAY_MODE', 'cn_gateway')
    monkeypatch.setenv('VEDASTRO_CACHE_TTL_SECONDS', '604800')
    monkeypatch.setenv('VEDASTRO_FULL_CATALOG_SAMPLE_LIMIT', '0')
    handler = _handler()

    result = handler._compute_vedastro_gateway_run({
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'second': 0,
        'lat': 36.4467,
        'lon': -122.4194,
        'tz': 8,
        'question': '事业机会什么时候出现',
        'themes': ['career', 'health'],
        'reference_date': '2026-07-02',
    })

    assert result['scope'] == 'vedastro_gateway_run'
    assert result['gateway_status']['mode'] == 'cn_gateway'
    assert result['honesty_boundary']['all_641_methods_executed'] is False
    assert result['user_visibility']['mainland_cn_safe'] is True


def test_professional_reading_composes_high_rigor_and_gateway(monkeypatch) -> None:
    handler = _handler()

    def fake_high_rigor(body):
        return {
            'success': True,
            'endpoint': 'high_rigor_workflow',
            'body': dict(body),
            'technique_audit': [{'technique': 'MEVG / Global Web Evidence', 'status': 'queued'}],
        }

    def fake_gateway(body):
        return {
            'scope': 'vedastro_gateway_run',
            'status': 'local_fallback',
            'user_visibility': {'boundary': 'VedAstro Gateway Boundary'},
            'honesty_boundary': {'all_641_methods_executed': False},
        }

    monkeypatch.setattr(handler, '_compute_high_rigor_workflow', fake_high_rigor)
    monkeypatch.setattr(handler, '_compute_vedastro_gateway_run', fake_gateway)

    result = handler._compute_professional_reading({
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 36.4467,
        'lon': -122.4194,
        'tz': 8,
        'question': '盲推事业',
        'themes': ['career', 'health'],
        'blind_mode': True,
    })

    assert result['endpoint'] == 'professional_reading'
    assert result['professional_reading']['high_rigor_workflow']['endpoint'] == 'high_rigor_workflow'
    assert result['professional_reading']['vedastro_gateway']['scope'] == 'vedastro_gateway_run'
    assert result['professional_reading']['user_led_calibration_controls']['blind_mode'] is True
    assert result['professional_reading']['visibility_contract']['requires_technique_audit_table'] is True


@pytest.mark.parametrize(
    ('key', 'value', 'minimum', 'maximum'),
    [
        ('lat', 91, -90, 90),
        ('lon', 181, -180, 180),
        ('tz', 15, -14, 14),
        ('minute', 60, 0, 59),
    ],
)
def test_numeric_bounds_reject_invalid_values(key, value, minimum, maximum) -> None:
    handler = _handler()
    with pytest.raises(BadRequest):
        handler._get_float({key: value}, key, 0, minimum, maximum)


def test_chart_date_validation_rejects_impossible_date() -> None:
    handler = _handler()
    with pytest.raises(BadRequest, match='Invalid birth date'):
        handler._compute_chart({'year': 2026, 'month': 2, 'day': 31})


def test_high_rigor_workflow_plan_only_exposes_official_hard_override_contract() -> None:
    handler = _handler()

    result = handler._high_rigor_workflow_plan_only(
        {
            'year': 1955,
            'month': 2,
            'day': 24,
            'hour': 19,
            'minute': 15,
            'lat': 37.7749,
            'lon': -122.4194,
            'tz': 8,
        },
        ['career', 'marriage', 'wealth'],
        [],
    )

    assert result['source_priority']['mode'] == 'vedastro_official_snapshot_first'
    assert result['execution_plan'][-1] == 'return_official_primary_supplemental_fallback_conflict_contract'


def test_high_rigor_vedastro_official_summary_passes_through_contract_fields(monkeypatch) -> None:
    monkeypatch.delenv('VEDASTRO_FREE_TIER_QUEUE', raising=False)
    monkeypatch.delenv('VEDASTRO_FREE_TIER_QUEUE_ENABLED', raising=False)
    monkeypatch.delenv('VEDASTRO_ENABLE_FREE_TIER_QUEUE', raising=False)
    handler = _handler()

    chart = {
        'modules': {
            'vedastro_range_scan_result': {
                'status': 'ok',
                'event_count': 3,
                'official_full_snapshot': {
                    'status': 'partial',
                    'source_metadata': {
                        'official_full_capability_catalog': {'status': 'partial', 'summary': {'catalog_method_count': 641}},
                    },
                },
                'source_metadata': {
                    'official_full_capability_dynamic_selection': {},
                    'official_report_references': {},
                },
            }
        },
        'ai_prompt_pack': {
            'evidence_snapshot': {
                'vedastro_official_snapshot': {
                    'status': 'partial',
                    'official_primary_evidence': {'chart_core': {'status': 'ok'}},
                    'local_supplemental_evidence': {'narayana_current': {'role': 'required_local_supplement'}},
                    'fallback_used': ['local_chart_fallback'],
                    'blocked_items': ['official_event_radar_partial'],
                    'conflicts': [{'type': 'official_local_dasha_conflict'}],
                }
            }
        },
    }

    result = handler._high_rigor_vedastro_official_summary(chart)

    assert result['official_primary_evidence']['chart_core']['status'] == 'ok'
    assert result['local_supplemental_evidence']['narayana_current']['role'] == 'required_local_supplement'
    assert result['fallback_used'] == ['local_chart_fallback']
    assert result['blocked_items'] == ['official_event_radar_partial']
    assert result['conflicts'] == [{'type': 'official_local_dasha_conflict'}]
    runtime_truth = result['runtime_truth']
    assert runtime_truth['catalog_boundary'] == 'catalog_recognized_not_full_runtime_execution'
    assert runtime_truth['official_execution_layers']['chart_core'] == 'ok'
    assert runtime_truth['official_execution_layers']['event_radar'] == 'partial'
    assert runtime_truth['official_execution_layers']['catalog_status'] == 'partial'
    assert runtime_truth['fallback_active'] is True
    assert runtime_truth['blocked_items'] == ['official_event_radar_partial']
    assert runtime_truth['free_tier_strategy']['using_free_tier'] is True
    assert runtime_truth['free_tier_strategy']['queue_enabled'] is False
    assert runtime_truth['free_tier_strategy']['cache_hit'] is False
    assert runtime_truth['free_tier_strategy']['guard_status'] == 'degraded_or_partial'


def test_high_rigor_vedastro_official_summary_exposes_top_reader_contract_from_full_snapshot() -> None:
    handler = _handler()

    chart = {
        'modules': {
            'vedastro_range_scan_result': {
                'status': 'partial',
                'event_count': 2,
                'source_metadata': {
                    'official_full_capability_catalog_status': 'partial',
                    'official_full_capability_catalog_summary': {'catalog_method_count': 641},
                },
            },
            'vedastro_official_full_snapshot': {
                'status': 'partial',
                'available': True,
                'strict_workflow_primary_route': 'career',
                'strict_workflow_routes_available': ['career', 'relationship', 'finance'],
                'strict_workflow_contracts': {
                    'career': {
                        'question_type': 'career',
                        'official_primary_evidence': {'chart_core': {'status': 'ok'}},
                        'local_supplemental_evidence': {'narayana_current': {'role': 'required_local_supplement'}},
                        'fallback_used': ['local_chart_fallback'],
                        'blocked_items': ['official_event_radar_partial'],
                        'conflicts': [{'type': 'official_local_dasha_conflict'}],
                        'adjudication_stages': {
                            'promise': {'status': 'present'},
                            'activation': {
                                'status': 'present',
                                'required_timing_systems': ['Vimshottari', 'Narayana'],
                            },
                        },
                        'multi_reference_reading_summary': {
                            'root_frame': {'signal': 'career_promise'},
                            'modifier_frame': {'functional_benefic_malefic': {'used': True}},
                        },
                        'technique_audit_summary': {
                            'functional_benefic_malefic': {'gate': 'hard', 'used': True},
                        },
                        'verdict': 'high_probability_window',
                        'dominant_label': 'career_status',
                        'main_conflicts': [{'type': 'official_local_dasha_conflict'}],
                    }
                },
                'source_metadata': {
                    'official_full_capability_catalog': {
                        'status': 'partial',
                        'summary': {'catalog_method_count': 641},
                    }
                },
                'raw_response': {'official': 'raw'},
            },
        },
        'ai_prompt_pack': {
            'evidence_snapshot': {
                'vedastro_official_full_snapshot': {
                    'status': 'partial',
                    'strict_workflow_primary_route': 'career',
                    'strict_workflow_routes_available': ['career', 'relationship', 'finance'],
                    'strict_workflow_contracts': {
                        'career': {
                            'question_type': 'career',
                            'adjudication_stages': {
                                'promise': {'status': 'present'},
                                'activation': {
                                    'status': 'present',
                                    'required_timing_systems': ['Vimshottari', 'Narayana'],
                                },
                            },
                            'multi_reference_reading_summary': {
                                'root_frame': {'signal': 'career_promise'},
                                'modifier_frame': {'functional_benefic_malefic': {'used': True}},
                            },
                            'technique_audit_summary': {
                                'functional_benefic_malefic': {'gate': 'hard', 'used': True},
                            },
                            'verdict': 'high_probability_window',
                            'dominant_label': 'career_status',
                            'main_conflicts': [{'type': 'official_local_dasha_conflict'}],
                            'official_primary_evidence': {'chart_core': {'status': 'ok'}},
                            'local_supplemental_evidence': {'narayana_current': {'role': 'required_local_supplement'}},
                            'fallback_used': ['local_chart_fallback'],
                            'blocked_items': ['official_event_radar_partial'],
                            'conflicts': [{'type': 'official_local_dasha_conflict'}],
                        }
                    },
                }
            }
        },
    }

    result = handler._high_rigor_vedastro_official_summary(chart)
    contract = result['strict_workflow_contracts']['career']

    assert result['strict_workflow_primary_route'] == 'career'
    assert result['strict_workflow_routes_available'] == ['career', 'relationship', 'finance']
    assert contract['adjudication_stages']['activation']['required_timing_systems'] == ['Vimshottari', 'Narayana']
    assert contract['multi_reference_reading_summary']['modifier_frame']['functional_benefic_malefic']['used'] is True
    assert result['technique_audit_summary']['functional_benefic_malefic']['gate'] == 'hard'
    assert result['adjudication_stages']['promise']['status'] == 'present'
    assert result['multi_reference_reading_summary']['root_frame']['signal'] == 'career_promise'
    assert result['verdict'] == 'high_probability_window'
    assert result['dominant_label'] == 'career_status'
    assert result['main_conflicts'] == [{'type': 'official_local_dasha_conflict'}]
    assert result['runtime_truth']['primary_route'] == 'career'
    assert result['runtime_truth']['routes_available'] == ['career', 'relationship', 'finance']
    assert result['raw_response'] == {'official': 'raw'}


def test_high_rigor_vedastro_official_summary_uses_module_snapshot_cache_truth_when_range_scan_snapshot_missing() -> None:
    handler = _handler()
    chart = {
        'birth': {'ayanamsa_display': 'Lahiri', 'ayanamsa_name': 'lahiri', 'node_mode': 'mean'},
        'modules': {
            'vedastro_range_scan_result': {
                'status': 'ok',
                'source_metadata': {},
            },
            'vedastro_official_full_snapshot': {
                'status': 'official_snapshot_budget_exhausted',
                'strict_workflow_primary_route': 'career',
                'strict_workflow_routes_available': ['career'],
                'strict_workflow_contracts': {
                    'career': {
                        'official_primary_evidence': {'chart_core': {'status': 'ok'}},
                    },
                },
                'source_metadata': {
                    'semantic_cache': {
                        'cache_hit': True,
                    },
                },
            },
        },
        'ai_prompt_pack': {
            'evidence_snapshot': {
                'vedastro_official_snapshot': {
                    'status': 'official_snapshot_budget_exhausted',
                },
            },
        },
    }

    result = handler._high_rigor_vedastro_official_summary(chart)

    assert result['status'] == 'official_snapshot_budget_exhausted'
    assert result['runtime_truth']['free_tier_strategy']['cache_hit'] is True


def test_api_prompt_pack_official_snapshot_carries_strict_workflow_contracts() -> None:
    handler = _handler()

    chart = {
        'birth': {'ayanamsa_display': 'Raman', 'ayanamsa_name': 'raman', 'node_mode': 'mean'},
        'ascendant': {'sign': 'Leo'},
        'planets': {'Moon': {'sign': 'Virgo'}},
        'dasha': {'current_md': 'Saturn'},
        'modules': {
            'vedastro_official_full_snapshot': {
                'status': 'partial',
                'available': True,
                'operation': 'official_full_snapshot',
                'primary_source': 'vedastro_official',
                'strict_workflow_primary_route': 'relationship',
                'strict_workflow_routes_available': ['relationship', 'career', 'finance'],
                'strict_workflow_contracts': {
                    'relationship': {
                        'question_type': 'relationship',
                        'official_primary_evidence': {'chart_core': {'status': 'ok'}},
                        'local_supplemental_evidence': {'upapada_lagna': {'present': True}},
                        'fallback_used': [],
                        'blocked_items': [],
                        'conflicts': [],
                    }
                },
                'source_metadata': {},
            }
        },
    }

    prompt_pack = handler._build_chart_prompt_pack(chart)
    official = prompt_pack['evidence_snapshot']['vedastro_official_full_snapshot']

    assert official['strict_workflow_primary_route'] == 'relationship'
    assert official['strict_workflow_routes_available'] == ['relationship', 'career', 'finance']
    assert official['strict_workflow_contracts']['relationship']['official_primary_evidence']['chart_core']['status'] == 'ok'


def test_consultation_workflow_surfaces_top_reader_contract_in_official_summary(monkeypatch) -> None:
    handler = _handler()

    fake_chart = {
        'success': True,
        'birth_info': {'date': '1955-02-24', 'time': '19:15', 'tz': 8},
        'special_lagnas': {'precision': 'sunrise_correct'},
        'chart': {
            'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
            'planets': _sample_planets(),
        },
        'modules': {
            'vedastro_range_scan_result': {
                'backend': 'vedastro_service_adapter_candidate',
                'status': 'partial',
                'event_count': 1,
                'source_metadata': {
                    'official_full_capability_catalog_status': 'partial',
                    'official_full_capability_catalog_summary': {
                        'catalog_method_count': 641,
                        'executed_method_count': 0,
                    },
                },
            },
            'vedastro_official_full_snapshot': {
                'status': 'partial',
                'available': True,
                'strict_workflow_primary_route': 'career',
                'strict_workflow_routes_available': ['career', 'relationship', 'finance'],
                'strict_workflow_contracts': {
                    'career': {
                        'question_type': 'career',
                        'official_primary_evidence': {'chart_core': {'status': 'ok'}},
                        'local_supplemental_evidence': {'narayana_current': {'role': 'required_local_supplement'}},
                        'fallback_used': [],
                        'blocked_items': ['official_event_radar_partial'],
                        'conflicts': [{'type': 'official_local_dasha_conflict'}],
                        'adjudication_stages': {
                            'promise': {'status': 'present'},
                            'activation': {
                                'status': 'present',
                                'required_timing_systems': ['Vimshottari', 'Narayana'],
                            },
                        },
                        'multi_reference_reading_summary': {
                            'root_frame': {'signal': 'career_promise'},
                            'modifier_frame': {'functional_benefic_malefic': {'used': True}},
                        },
                        'technique_audit_summary': {
                            'functional_benefic_malefic': {'gate': 'hard', 'used': True},
                        },
                        'verdict': 'high_probability_window',
                        'dominant_label': 'career_status',
                        'main_conflicts': [{'type': 'official_local_dasha_conflict'}],
                    }
                },
                'source_metadata': {
                    'official_full_capability_catalog': {
                        'status': 'partial',
                        'summary': {'catalog_method_count': 641},
                    }
                },
            },
        },
        'ai_prompt_pack': {
            'evidence_snapshot': {
                'vedastro_official_full_snapshot': {
                    'status': 'partial',
                    'strict_workflow_primary_route': 'career',
                    'strict_workflow_routes_available': ['career', 'relationship', 'finance'],
                    'strict_workflow_contracts': {
                        'career': {
                            'question_type': 'career',
                            'official_primary_evidence': {'chart_core': {'status': 'ok'}},
                            'local_supplemental_evidence': {'narayana_current': {'role': 'required_local_supplement'}},
                            'fallback_used': [],
                            'blocked_items': ['official_event_radar_partial'],
                            'conflicts': [{'type': 'official_local_dasha_conflict'}],
                            'adjudication_stages': {
                                'promise': {'status': 'present'},
                                'activation': {
                                    'status': 'present',
                                    'required_timing_systems': ['Vimshottari', 'Narayana'],
                                },
                            },
                            'multi_reference_reading_summary': {
                                'root_frame': {'signal': 'career_promise'},
                                'modifier_frame': {'functional_benefic_malefic': {'used': True}},
                            },
                            'technique_audit_summary': {
                                'functional_benefic_malefic': {'gate': 'hard', 'used': True},
                            },
                            'verdict': 'high_probability_window',
                            'dominant_label': 'career_status',
                            'main_conflicts': [{'type': 'official_local_dasha_conflict'}],
                        }
                    },
                }
            },
        },
    }

    monkeypatch.setattr(handler, '_compute_chart', lambda body: fake_chart)
    monkeypatch.setattr(handler, '_compute_rectification_gate', lambda body: {
        'success': True,
        'endpoint': 'rectification_gate',
        'summary': {'recommended_events': ['career_change']},
    })
    monkeypatch.setattr(handler, '_compute_thematic_report', lambda body: {
        'success': True,
        'endpoint': 'thematic_report',
        'mode': 'derived_chart_evidence',
        'theme_count': len(body.get('theme') or []),
        'themes': {theme: {'summary': f'{theme} report'} for theme in body.get('theme') or []},
    })
    monkeypatch.setattr(handler, '_run_high_rigor_historical_backtest', lambda birth, events: {
        'scope': 'historical_event_backtest',
        'summary': {'total_events': len(events)},
        'events': events,
    })

    result = handler._compute_consultation_workflow({
        'entry_mode': 'direct_chart',
        'question': '请直接排盘并重点看事业',
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
        'theme': ['career'],
        'blind': True,
    })

    contract = result['vedastro_official']['strict_workflow_contracts']['career']
    assert result['vedastro_official']['strict_workflow_primary_route'] == 'career'
    assert contract['adjudication_stages']['activation']['required_timing_systems'] == ['Vimshottari', 'Narayana']
    assert contract['multi_reference_reading_summary']['root_frame']['signal'] == 'career_promise'
    assert result['vedastro_official']['technique_audit_summary']['functional_benefic_malefic']['gate'] == 'hard'
    assert result['vedastro_official']['dominant_label'] == 'career_status'


def test_synastry_rejects_non_numeric_moon_degree() -> None:
    handler = _handler()
    with pytest.raises(BadRequest, match='male_moon must be a number'):
        handler._compute_synastry({'male_moon': 'not-a-number', 'female_moon': 120})


def test_synastry_normalizes_360_degree_boundary() -> None:
    handler = _handler()
    result = handler._compute_synastry({'male_moon': 360, 'female_moon': 0})
    assert result['male_details']['nakshatra'] == result['female_details']['nakshatra']
    assert result['max_score'] == 36.0


def test_synastry_api_uses_full_ashtakoot_engine() -> None:
    from ashtakoot import calculate_ashtakoot

    handler = _handler()
    api_result = handler._compute_synastry({'male_moon': 0, 'female_moon': 60})
    engine_result = calculate_ashtakoot(0, 60)

    assert api_result['method'] == engine_result['method']
    assert api_result['scores'] == engine_result['scores']
    assert api_result['total_score'] == engine_result['total_score']
    assert api_result['is_match_approved'] == engine_result['is_match_approved']
    assert api_result['scores']['Vashya'] == 0.5
    assert 'BadConstellations' in api_result['additional_kutas']


def test_prashna_rejects_non_string_question() -> None:
    handler = _handler()
    with pytest.raises(BadRequest, match='question must be a string'):
        handler._compute_prashna({'question': {'bad': 'shape'}, 'planets': {}})


def test_prashna_returns_chart_and_answer_for_valid_request() -> None:
    handler = _handler()
    result = handler._compute_prashna({
        'question': 'career',
        'question_text': '这个工作机会是否值得争取？',
        'horary_number': 140,
        'planets': {'Saturn': {'sign': 'Pisces'}, 'Moon': {'sign': 'Scorpio'}},
    })
    assert 'prashna_chart' in result
    assert 'kp_answer' in result
    assert result['kp_answer']['question_type'] == 'career'
    assert result['kp_answer_v2']['primary_house'] == 10
    assert 'arudha' in result
    assert 'sphutas' in result
    assert 'sahams' in result
    assert 'lost_item' in result
    assert 'kunda' in result
    kp_horary = result['kp_horary']
    assert kp_horary['method'] == 'KP Horary'
    assert kp_horary['horary_number'] == 140
    assert kp_horary['question_houses']['primary'] == 10
    assert kp_horary['ruling_planets']['ascendant_lord']
    assert kp_horary['ruling_planets']['moon_star_lord']
    assert kp_horary['cuspal_sub_lord']['house'] == 10
    assert kp_horary['cuspal_sub_lord']['kp_lords']['sub_lord']
    assert kp_horary['house_significators']['10']
    assert kp_horary['judgement_matrix']


def test_prashna_advanced_legacy_functions_exist() -> None:
    import prashna

    planet_lons = {
        'Sun': 10,
        'Moon': 70,
        'Mars': 120,
        'Mercury': 25,
        'Jupiter': 150,
        'Venus': 45,
        'Saturn': 210,
        'Rahu': 300,
        'Ketu': 120,
    }
    assert prashna.cast_prashna('2026-06-22 12:00', 28.6, 77.2)['ascendant']
    assert prashna.calc_arudha(15.5, planet_lons)['arudha_house']
    assert prashna.calc_sphutas(planet_lons, 15.5)['trisphuta']
    assert prashna.calc_life_sphutas(15.5, 70, 10)['signal']
    assert prashna.calc_sahams(planet_lons, 15.5)['count'] >= 5
    assert prashna.analyze_lost_item(planet_lons, 15.5)['summary']
    assert prashna.kunda_verify(15.5)['nakshatra']


def test_dasha_system_rejects_unknown_key() -> None:
    handler = _handler()
    with pytest.raises(BadRequest, match='Unknown dasha system'):
        handler._compute_dasha_system({'dasha': 'not-a-dasha'})


def test_dasha_system_returns_periods_for_valid_request() -> None:
    handler = _handler()
    result = handler._compute_dasha_system({
        'dasha': 'yogini',
        'year': 1990,
        'month': 6,
        'day': 15,
        'hour': 12,
        'minute': 0,
        'planets': {'Moon': {'lon': 120}, 'Sun': {'lon': 80}},
        'ascendant': {'sign_idx': 0},
    })
    assert result['success'] is True
    assert result['key'] == 'yogini'
    assert result['precision'] == 'calculator'
    assert result['periods']
    assert result['periods'][0]['lord'] in {
        'Mangala',
        'Pingala',
        'Dhanya',
        'Bhramari',
        'Bhadrika',
        'Ulka',
        'Siddha',
        'Sankata',
    }
    assert {'lord', 'start', 'end', 'years'} <= set(result['periods'][0])
    assert 'vimshottari_analysis' not in result


def test_vimshottari_dasha_reuses_analyzer_fragment() -> None:
    handler = _handler()
    result = handler._compute_dasha_system({
        'dasha': 'vimshottari',
        'year': 1990,
        'month': 6,
        'day': 15,
        'hour': 12,
        'minute': 0,
        'today': '2026-06-23',
        'planets': {'Moon': {'lon': 123}, 'Sun': {'lon': 80}},
        'ascendant': {'sign_idx': 0},
    })

    analysis = result['vimshottari_analysis']
    assert result['success'] is True
    assert 'dasha_analyzer.py' in result['fragment_sources']
    assert analysis['source'] == 'dasha_analyzer.py + dasha_calculator_enhanced.py'
    assert analysis['nakshatra']['name']
    assert analysis['current']['mahadasha']['lord']
    assert analysis['current']['antardasha']['lord']
    assert analysis['five_levels']['mahadasha']['lord'] == analysis['current']['mahadasha']['lord']
    assert analysis['summary']['headline'].startswith('当前处于')


def test_relationship_returns_spouse_status_fragment() -> None:
    handler = _handler()
    result = handler._compute_relationship({
        'asc_sign': 'Cancer',
        'planets': {
            'Sun': {'sign': 'Leo', 'degree': 20, 'house': 2, 'dignity': 'own'},
            'Moon': {'sign': 'Cancer', 'degree': 12, 'house': 1, 'dignity': 'own'},
            'Mars': {'sign': 'Sagittarius', 'degree': 26, 'house': 6, 'dignity': 'friendly'},
            'Mercury': {'sign': 'Virgo', 'degree': 8, 'house': 3, 'dignity': 'own'},
            'Jupiter': {'sign': 'Pisces', 'degree': 14, 'house': 9, 'dignity': 'own'},
            'Venus': {'sign': 'Taurus', 'degree': 2, 'house': 11, 'dignity': 'own'},
            'Saturn': {'sign': 'Capricorn', 'degree': 28, 'house': 7, 'dignity': 'own'},
            'Rahu': {'sign': 'Gemini', 'degree': 18, 'house': 12},
            'Ketu': {'sign': 'Sagittarius', 'degree': 18, 'house': 6},
        },
        'dasha_info': {'maha_dasha': 'Venus', 'antar_dasha': 'Jupiter'},
    })
    assert 'spouse_status_yoga' in result
    assert result['spouse_status_yoga']['principles']
    assert 'spouse_status_yoga.py' in result['fragment_sources']
    assert result['spouse_status_yoga']['overall_score'] >= 0
    assert 'relationship_timing' in result
    assert 'darakaraka_reader.py' in result['fragment_sources']
    assert 'jaimini.py' in result['fragment_sources']
    assert result['relationship_timing']['darakaraka']['dk_planet']
    assert result['relationship_timing']['upapada']['sign']
    assert result['relationship_timing']['dasha_focus']['hits']
    assert result['relationship_timing']['evidence']


def test_chart_returns_remedies_with_shadbala_summary() -> None:
    handler = _handler()
    result = handler._compute_chart({
        'year': 1990,
        'month': 6,
        'day': 15,
        'hour': 12,
        'minute': 0,
        'lat': 39.9,
        'lon': 116.4,
        'tz': 8,
    })
    assert 'remedies' in result
    assert 'summary' in result['remedies']
    assert 'recommendations' in result['remedies']


def test_chart_returns_sunrise_correct_special_lagnas() -> None:
    handler = _handler()
    result = handler._compute_chart({
        'year': 1990,
        'month': 6,
        'day': 15,
        'hour': 10,
        'minute': 30,
        'lat': 28.6,
        'lon': 77.2,
        'tz': 5.5,
    })
    special = result['special_lagnas']
    assert special['capability_status'] == 'covered'
    assert special['precision'] == 'sunrise_correct'
    assert 'sunrise_local_time' in special
    assert 'ghatis_elapsed_from_sunrise' in special
    assert all(key in special for key in ('HL', 'GL', 'VL'))


def test_remedies_accepts_api_rupas_shape() -> None:
    remedies = _load_local_module('remedies')

    result = remedies.recommend_remedies({'Sun': {'rupas': 0.4, 'level': '弱'}})
    assert result['weak_planets'] == ['Sun']
    assert result['recommendations']['mantras']


def test_remedies_endpoint_accepts_numeric_shadbala_shorthand() -> None:
    handler = _handler()
    result = handler._compute_remedies({
        'shadbala': {'Sun': 0.42, 'Moon': 0.68},
        'dasha_lord': 'Saturn',
        'doshas': ['Mangal Dosha'],
    })

    assert result['weak_planets'] == ['Sun']
    assert 'Moon' in result['moderate_planets']
    assert any(item['source'] == 'shadbala' and item['planet'] == 'Sun' for item in result['evidence_chain'])


def test_import_chart_accepts_plain_text() -> None:
    handler = _handler()
    result = handler._import_chart_text({
        'text': 'Date of Birth: 1990-06-15\nTime of Birth: 12:30\nPlace of Birth: Delhi\nTimezone: UTC+5:30',
    })
    assert result['success'] is True
    assert result['extractor'] == 'text'
    assert '1990-06-15' in result['text']


def test_import_chart_accepts_base64_text_file() -> None:
    handler = _handler()
    content = base64.b64encode(b'DOB: 1990-06-15\nTOB: 12:30\nCity: Mumbai').decode()
    result = handler._import_chart_text({'filename': 'chart.txt', 'content_base64': content})
    assert result['success'] is True
    assert result['extractor'] == 'text'
    assert 'Mumbai' in result['text']


def test_import_chart_requires_input() -> None:
    handler = _handler()
    with pytest.raises(BadRequest, match='text or content_base64 is required'):
        handler._import_chart_text({})


def test_import_chart_rejects_bad_base64() -> None:
    handler = _handler()
    with pytest.raises(BadRequest, match='Invalid base64 content'):
        handler._import_chart_text({'filename': 'chart.txt', 'content_base64': 'not-base64!'})


def test_import_chart_rejects_oversized_file() -> None:
    handler = _handler()
    content = base64.b64encode(b'x' * (1536 * 1024 + 1)).decode()
    with pytest.raises(BadRequest, match='Import file too large'):
        handler._import_chart_text({'filename': 'chart.txt', 'content_base64': content})


def test_report_artifact_generates_html_fallback_artifact() -> None:
    handler = _handler()
    result = handler._compute_report_artifact({
        'format': 'html',
        'name': 'client report',
        'html': '<!doctype html><html><body><h1>Jyotish</h1></body></html>',
    })

    assert result['success'] is True
    assert result['endpoint'] == 'report_artifact'
    assert result['format'] == 'html'
    assert result['html_filename'].endswith('.html')
    assert result['html_base64']
    assert os.path.exists(result['html_path'])
    assert result['artifact_status'] == 'html_ready'
    assert result['primary_artifact'] == 'html'
    assert result['download_filename'] == result['html_filename']
    assert result['download_mime'] == 'text/html;charset=utf-8'
    assert result['fallback_reason'] is None
    assert result['user_message']
    assert result['next_action']
    assert result['delivery']['format'] == 'html'
    assert result['delivery']['filename'] == result['html_filename']
    assert result['delivery']['artifact_status'] == 'html_ready'
    assert result['delivery']['user_message']
    assert result['delivery']['next_action']


def test_report_artifact_can_render_functional_benefic_malefic_summary() -> None:
    handler = _handler()
    result = handler._compute_report_artifact({
        'format': 'html',
        'name': 'functional-role-report',
        'html': '<!doctype html><html><body><h1>Jyotish</h1></body></html>',
        'functional_benefic_malefic': {
            'status': 'used',
            'ascendant': 'Leo',
            'functional_benefics': ['Sun', 'Mars', 'Jupiter'],
            'functional_malefics': ['Venus', 'Saturn'],
            'functional_neutrals': ['Mercury'],
            'yogakarakas': ['Mars'],
            'effect_on_confidence': '高严谨模式下必须叠加功能性吉凶星。',
        },
    })

    assert result['success'] is True
    html = Path(result['html_path']).read_text(encoding='utf-8')
    assert 'Functional Benefic/Malefic' in html
    assert 'Leo' in html
    assert 'Sun, Mars, Jupiter' in html
    assert 'Venus, Saturn' in html
    assert 'Mercury' in html
    assert 'Mars' in html
    assert 'Yogakarakas' in html
    assert 'Functional Neutrals' in html
    assert '高严谨模式下必须叠加功能性吉凶星。' in html


def test_report_artifact_can_render_vimsopaka_semantic_summary() -> None:
    handler = _handler()
    result = handler._compute_report_artifact({
        'format': 'html',
        'name': 'vimsopaka-semantic-report',
        'html': '<!doctype html><html><body><h1>Jyotish</h1></body></html>',
        'vimsopaka_semantic_summary': {
            'status': 'used',
            'highlights': ['Sun: 极友(Great Friend)', 'Moon: 落陷取消(Neecha Bhanga)'],
            'warnings': ['Mars: 极敌(Great Enemy)'],
        },
    })

    assert result['success'] is True
    html = Path(result['html_path']).read_text(encoding='utf-8')
    assert 'Vimsopaka Semantic Summary' in html
    assert 'Great Friend' in html
    assert 'Neecha Bhanga' in html
    assert 'Great Enemy' in html


def test_report_artifact_can_render_vedastro_external_overview() -> None:
    handler = _handler()
    result = handler._compute_report_artifact({
        'format': 'html',
        'name': 'vedastro-overview-report',
        'html': '<!doctype html><html><body><h1>Jyotish</h1></body></html>',
        'vedastro_overview': {
            'status': 'ok',
            'source': 'vedastro_service_adapter_candidate',
            'ingestion_profile': 'main_entry_overview',
            'search_scope': 'single_day_overview',
            'reference_date': '2026-06-29',
            'event_count': 5,
            'domain_statuses': {'career': 'ok', 'marriage': 'ok', 'wealth': 'ok'},
            'top_events_by_domain': {
                'marriage': {'signal_label': 'Jupiter in 7th marriage window', 'start': '2026-06-29'},
                'career': {'signal_label': 'Jupiter in 10th career window', 'start': '2026-06-29'},
            },
            'boundary_note': 'This is overview only and does not replace explicit long-range scans.',
        },
    })

    assert result['success'] is True
    html = Path(result['html_path']).read_text(encoding='utf-8')
    assert 'VedAstro External Overview' in html
    assert 'main_entry_overview' in html
    assert 'single_day_overview' in html
    assert '2026-06-29' in html
    assert 'Jupiter in 7th marriage window' in html
    assert 'overview only' in html


def test_report_artifact_can_render_relationship_strict_narrative_summary() -> None:
    handler = _handler()
    result = handler._compute_report_artifact({
        'format': 'html',
        'name': 'relationship-strict-report',
        'html': '<!doctype html><html><body><h1>Jyotish</h1></body></html>',
        'relationship_narrative': {
            'headline': '婚恋严格裁决已接入 synastry taxonomy，可把合盘支持翻译成次级关系语义。',
            'strengths': ['合盘支持已进入婚恋主链，但它只说明关系兼容度有帮助。'],
            'risks': ['当前 confidence cap 偏低，dual dasha / external timing / marriage convergence 存在冲突或不足。'],
            'boundaries': ['婚恋高严谨模式至少需要 D1、D9、UL、Vimshottari 与 Narayana dual dasha 同时在场。'],
        },
    })

    assert result['success'] is True
    html = Path(result['html_path']).read_text(encoding='utf-8')
    assert 'Relationship Strict Narrative' in html
    assert 'synastry taxonomy' in html
    assert 'dual dasha' in html
    assert 'D1、D9、UL' in html


def test_report_artifact_relationship_strict_narrative_keeps_conflict_downgrade_language() -> None:
    handler = _handler()
    result = handler._compute_report_artifact({
        'format': 'html',
        'name': 'relationship-strict-conflict-report',
        'html': '<!doctype html><html><body><h1>Jyotish</h1></body></html>',
        'relationship_narrative': {
            'headline': '婚恋 strict workflow 已识别支持层，但 timing conflict 仍要求降置信度。',
            'strengths': ['D9、UL 与部分 synastry taxonomy 已在场。'],
            'risks': ['dual dasha 与 external timing 发生冲突，不能把窗口直接抬成 legal marriage。'],
            'boundaries': ['存在 timing conflict 时，最终婚恋 narrative 必须明确降置信度。'],
            'markdown': '### 婚恋严格裁决\n- 当前 dual dasha 与 external timing 存在冲突，必须降置信度，不能把 supportive kuta 直接提升为 legal marriage。\n',
        },
    })

    assert result['success'] is True
    html = Path(result['html_path']).read_text(encoding='utf-8')
    assert 'timing conflict' in html
    assert 'dual dasha' in html
    assert '降置信度' in html


def test_report_artifact_relationship_strict_narrative_surfaces_public_formalization_candidate_boundary() -> None:
    handler = _handler()
    result = handler._compute_report_artifact({
        'format': 'html',
        'name': 'relationship-strict-public-formalization-report',
        'html': '<!doctype html><html><body><h1>Jyotish</h1></body></html>',
        'relationship_narrative': {
            'headline': '当前关系更接近 public_formalization candidate，而不是 legal marriage。',
            'strengths': ['公开化/可见度支持正在升温，但仍属于 context-only 线索。'],
            'risks': ['dual dasha 与 marriage convergence 还不足以把事件抬升为法律婚姻。'],
            'boundaries': ['public_formalization_candidate 只表示公开化候选，不等于法律婚姻，不能越权替代 legal_marriage。'],
            'markdown': '### 婚恋严格裁决\n- public_formalization_candidate 已进入 secondary-context，但仍不能替代 legal_marriage。\n',
        },
    })

    assert result['success'] is True
    html = Path(result['html_path']).read_text(encoding='utf-8')
    assert 'public_formalization_candidate' in html
    assert '不等于法律婚姻' in html
    assert 'legal_marriage' in html


def test_report_artifact_relationship_strict_narrative_warns_public_formalization_candidate_not_to_be_misread_as_near_marriage() -> None:
    handler = _handler()
    result = handler._compute_report_artifact({
        'format': 'html',
        'name': 'relationship-strict-public-formalization-conflict-report',
        'html': '<!doctype html><html><body><h1>Jyotish</h1></body></html>',
        'relationship_narrative': {
            'headline': '当前更接近 public_formalization candidate，但 timing conflict 仍然存在。',
            'strengths': ['公开化候选正在形成，但仍只是 context-only 层。'],
            'risks': ['当前 dual dasha / external timing 仍有冲突，不能误读成接近结婚。'],
            'boundaries': ['public_formalization_candidate 不等于法律婚姻，不能越权替代 legal_marriage。'],
            'markdown': '### 婚恋严格裁决\n- public_formalization_candidate 已进入 secondary-context，但当前 dual dasha 与 external timing 仍有冲突，不能误读成接近结婚，也不能替代 legal_marriage。\n',
        },
    })

    assert result['success'] is True
    html = Path(result['html_path']).read_text(encoding='utf-8')
    assert 'public_formalization_candidate' in html
    assert '不能误读成接近结婚' in html
    assert 'legal_marriage' in html


def test_report_artifact_relationship_strict_narrative_surfaces_weak_core_promise_guardrail_for_public_formalization_candidate() -> None:
    handler = _handler()
    result = handler._compute_report_artifact({
        'format': 'html',
        'name': 'relationship-strict-weak-core-promise-report',
        'html': '<!doctype html><html><body><h1>Jyotish</h1></body></html>',
        'relationship_narrative': {
            'headline': '当前更接近 public_formalization candidate，但 core marriage promise 仍偏弱。',
            'strengths': [
                '合盘支持已进入婚恋主链，但它只说明关系兼容度有帮助。',
                '公开化/关系可见度候选正在增强，但仍未达到法律婚姻落地。',
            ],
            'risks': ['当前 core marriage promise 偏弱，不能误读成接近结婚。'],
            'boundaries': [
                'protective kuta support 只能辅助，不得越权抬升 legal_marriage。',
                'public_formalization_candidate 不等于法律婚姻。',
            ],
            'markdown': '### 婚恋严格裁决\n- public_formalization_candidate 与 synastry_support 可以同时存在，但在 weak core marriage promise 下，仍不能写成婚姻逼近，也不能替代 legal_marriage。\n',
        },
    })

    assert result['success'] is True
    html = Path(result['html_path']).read_text(encoding='utf-8')
    assert 'public_formalization_candidate' in html
    assert '合盘支持已进入婚恋主链' in html
    assert '不能误读成接近结婚' in html
    assert 'legal_marriage' in html
    assert 'relationship-caution' in html


def test_report_artifact_can_render_career_and_finance_strict_narrative_summary() -> None:
    handler = _handler()
    result = handler._compute_report_artifact({
        'format': 'html',
        'name': 'career-finance-strict-report',
        'html': '<!doctype html><html><body><h1>Jyotish</h1></body></html>',
        'career_narrative': {
            'headline': '事业严格裁决已接入主链，当前结论将强制引用本命 promise、双重大运、官方时间窗与结构阻力。',
            'strengths': ['月度主状态：机会进入。', '落地形式：职位/项目/公开职责抬头。'],
            'risks': ['阻力来源：功能性凶星与结构摩擦仍在。'],
            'boundaries': ['时间置信度：以月级为主，日级只作辅助。'],
        },
        'finance_narrative': {
            'headline': '财富严格裁决已接入主链，当前结论会强制区分收入兑现、现金流动作与风险摩擦。',
            'strengths': ['月度主状态：收入兑现。', '落地形式：定金/回款/短期现金流改善。'],
            'risks': ['阻力来源：波动性收入，不宜过度放大利润预期。'],
            'boundaries': ['时间置信度：以兑现窗口而非全年静态判断为主。'],
        },
    })

    assert result['success'] is True
    html = Path(result['html_path']).read_text(encoding='utf-8')
    assert 'Career Strict Narrative' in html
    assert '事业严格裁决已接入主链' in html
    assert '月度主状态：机会进入' in html
    assert '阻力来源：功能性凶星与结构摩擦仍在' in html
    assert 'Finance Strict Narrative' in html
    assert '财富严格裁决已接入主链' in html
    assert '落地形式：定金/回款/短期现金流改善' in html


def test_report_artifact_pdf_fallback_exposes_user_visible_delivery(monkeypatch) -> None:
    class BrokenReportBuilder:
        @staticmethod
        def _html_to_pdf(_html_path, _pdf_path):
            return False

    def fake_load_local_module(name):
        if name == 'report_builder':
            return BrokenReportBuilder
        return _load_local_module(name)

    monkeypatch.setattr(jyotish_api_server, '_load_local_module', fake_load_local_module)
    handler = _handler()
    result = handler._compute_report_artifact({
        'format': 'pdf',
        'name': '../client pdf report',
        'html': '<!doctype html><html><body><h1>Jyotish PDF</h1></body></html>',
    })

    assert result['success'] is True
    assert result['format'] == 'pdf'
    assert result['fallback'] == 'html'
    assert result['artifact_status'] == 'pdf_fallback_html_ready'
    assert result['primary_artifact'] == 'html'
    assert result['download_filename'] == result['html_filename']
    assert result['download_mime'] == 'text/html;charset=utf-8'
    assert result['download_filename'].endswith('.html')
    assert '/' not in result['download_filename']
    assert result['fallback_reason']
    assert 'PDF renderer unavailable' in result['message']
    assert 'HTML' in result['user_message']
    assert 'PDF' in result['user_message']
    assert result['delivery']['fallback'] is True
    assert result['delivery']['artifact_status'] == 'pdf_fallback_html_ready'
    assert result['delivery']['filename'] == result['download_filename']
    assert result['delivery']['fallback_reason'] == result['fallback_reason']
    assert result['delivery']['user_message'] == result['user_message']


@pytest.mark.parametrize(
    'html',
    [
        '<script>alert(1)</script>',
        '<img src=x onerror="alert(1)">',
        '<a href="javascript:alert(1)">x</a>',
    ],
)
def test_report_artifact_rejects_active_html(html: str) -> None:
    handler = _handler()
    with pytest.raises(BadRequest, match='active content'):
        handler._compute_report_artifact({'format': 'html', 'html': html})


def test_oracle_evidence_api_validates_uploaded_packets() -> None:
    handler = _handler()
    draft_packet = {
        'case_id': 'template_steve_jobs_dasha_lahiri',
        'status': 'draft',
        'evidence_packet': {
            'status': 'draft',
            'metadata': {
                'tool_name': '',
                'tool_version_or_url': '',
                'capture_date': '',
                'source_artifact': '',
                'ayanamsa': '',
                'node_mode': '',
                'timezone': '',
                'operator_note': '',
            },
        },
        'target': {
            'moon_sidereal_longitude_deg': None,
            'vimshottari_start_date': None,
            'shadbala_components': {},
        },
    }

    draft_result = handler._compute_oracle_evidence({'packet': draft_packet})

    assert draft_result['success'] is True
    assert draft_result['endpoint'] == 'oracle_evidence'
    assert draft_result['report']['summary']['valid_packets'] == 0
    assert draft_result['report']['summary']['ready_for_calibration'] == 0
    assert draft_result['report']['summary']['production_tuning_allowed'] is False
    first = draft_result['report']['packets'][0]
    assert first['valid'] is False
    assert 'missing_metadata:tool_name' in first['problems']
    assert 'missing_external_artifact' in first['problems']
    assert 'status_not_external_verified:draft' in first['problems']

    filled_packet = {
        **draft_packet,
        'status': 'external_verified',
        'evidence_packet': {
            'status': 'external_verified',
            'metadata': {
                'tool_name': 'Local Engine',
                'tool_version_or_url': 'this-repo',
                'capture_date': '2026-06-25',
                'source_artifact': 'scripts/jyotish_engine.py output',
                'ayanamsa': 'lahiri',
                'node_mode': 'mean',
                'timezone': 'UTC+08:00',
                'operator_note': 'Local run',
            },
        },
        'target': {
            'moon_sidereal_longitude_deg': 311.7897,
            'vimshottari_start_date': '1986-05-18',
            'shadbala_components': {
                'Sun': {
                    'sthana': 100.0,
                    'dig': 50.0,
                    'kala': 100.0,
                    'chesta': 40.0,
                    'naisargika': 60.0,
                    'drik': 30.0,
                },
            },
        },
    }

    local_result = handler._compute_oracle_evidence({'packet': filled_packet})

    local_first = local_result['report']['packets'][0]
    assert local_first['valid'] is False
    assert 'local_engine_artifact_rejected' in local_first['problems']


def test_capability_audit_scans_registry_and_local_sources() -> None:
    handler = _handler()
    audit = handler._capability_audit()

    assert audit['success'] is True
    assert audit['registry']['technique_count'] >= 60
    assert audit['surfaces']['engine_command_count'] >= 30
    assert '/api/chart' in audit['surfaces']['api_endpoints']
    assert '/api/tajika' in audit['surfaces']['api_endpoints']
    assert 'varga-full' not in audit['surfaces']['engine_not_api']
    assert 'jaimini' not in audit['surfaces']['engine_not_api']
    assert 'ashtakavarga' not in audit['surfaces']['engine_not_api']
    assert 'shadbala' not in audit['surfaces']['engine_not_api']
    assert 'yoga' not in audit['surfaces']['engine_not_api']
    assert 'aspects' not in audit['surfaces']['engine_not_api']
    assert 'muhurta' not in audit['surfaces']['engine_not_api']
    assert audit['local_open_source']['source_count'] >= 3
    assert any(source['name'] == 'dashaflow' for source in audit['local_open_source']['sources'])
    assert all(gap.get('command') != 'varga-full' for gap in audit['priority_gaps'])
    assert 'Muhurta' in audit['surfaces']['app_visible_topics']
    assert 'Tajika' in audit['surfaces']['app_visible_topics']
    assert 'Bhava Chalit' in audit['surfaces']['app_visible_topics']
    assert 'Sudarshana' in audit['surfaces']['app_visible_topics']
    assert 'Jaimini' in audit['surfaces']['app_visible_topics']
    assert 'Ashtakavarga' in audit['surfaces']['app_visible_topics']
    assert 'Shadbala' in audit['surfaces']['app_visible_topics']
    assert 'Yoga' in audit['surfaces']['app_visible_topics']
    assert 'Aspects' in audit['surfaces']['app_visible_topics']
    assert 'Birth Rectification' in audit['surfaces']['app_visible_topics']
    assert 'Case Validation' in audit['surfaces']['app_visible_topics']
    assert 'Divisional Yoga' in audit['surfaces']['app_visible_topics']
    assert 'Kakshya' in audit['surfaces']['app_visible_topics']
    assert '/api/deep_varga_avastha' in audit['surfaces']['api_endpoints']
    assert all(gap['kind'] != 'app_visibility' for gap in audit['priority_gaps'])
    productization = audit['productization']
    summary = productization['summary']
    assert sum(summary.values()) == audit['registry']['technique_count']
    assert summary['productized'] > 0
    assert productization['rows']
    assert all('next_action' in row for row in productization['rows'])
    ux = audit['ux_productization']
    assert set(ux['criteria']) == {
        'clear_entry',
        'human_readable_conclusion',
        'evidence_chain',
        'next_action',
        'json_hidden',
        'mobile_scannable',
    }
    assert sum(ux['summary'].values()) == audit['registry']['technique_count']
    assert ux['rows']
    assert ux['summary']['excellent'] == audit['registry']['technique_count']
    assert ux['summary']['usable'] == 0
    assert ux['summary']['thin'] == 0
    assert ux['summary']['not_user_ready'] == 0
    assert all(0 <= row['ux_score'] <= 6 for row in ux['rows'])
    assert all('ux_next_action' in row for row in ux['next_queue'])
    ux_by_id = {row['id']: row for row in ux['rows']}
    assert ux_by_id['birth_time_rectifier']['ux_level'] in {'excellent', 'usable'}
    assert ux_by_id['case_validator']['ux_level'] in {'excellent', 'usable'}
    assert ux_by_id['divisional_yoga']['ux_level'] in {'excellent', 'usable'}
    assert ux_by_id['deep_varga_avastha']['ux_level'] in {'excellent', 'usable'}
    assert ux_by_id['kakshya']['ux_level'] in {'excellent', 'usable'}
    for technique_id in ['ashtakavarga_pav', 'ashtakavarga_sodhita', 'remedies']:
        assert ux_by_id[technique_id]['ux_level'] == 'excellent'
    for technique_id in ['bhava_bala', 'career_engine', 'kp_system', 'prashna', 'synastry_16factor', 'transit_trigger']:
        assert ux_by_id[technique_id]['ux_level'] in {'excellent', 'usable'}


def test_technique_catalog_exposes_runnable_api_examples() -> None:
    handler = _handler()
    catalog = handler._technique_catalog()

    assert catalog['success'] is True
    assert catalog['summary']['technique_count'] >= 60
    assert catalog['summary']['runnable_count'] >= 20
    assert '/api/ashtakavarga' in catalog['filters']['api_endpoints']
    assert '/api/tajika' in catalog['filters']['api_endpoints']
    assert '/api/deep_varga_avastha' in catalog['filters']['api_endpoints']
    assert catalog['example_payloads']['/api/ashtakavarga']['planets']
    assert catalog['example_payloads']['/api/deep_varga_avastha']['planets']
    assert any(row['id'] == 'ashtakavarga_pav' and row['runnable'] for row in catalog['techniques'])
    assert any(row['id'] == 'deep_varga_avastha' and row['runnable'] for row in catalog['techniques'])

    result = handler._compute_technique_example({'endpoint': '/api/ashtakavarga'})
    assert result['success'] is True
    assert result['endpoint'] == 'technique_example'
    assert result['target_endpoint'] == '/api/ashtakavarga'
    assert result['result']['summary']['strongest_houses']

    deep = handler._compute_technique_example({'endpoint': '/api/deep_varga_avastha'})
    assert deep['success'] is True
    assert deep['target_endpoint'] == '/api/deep_varga_avastha'
    assert deep['result']['report']['deep_varga_templates']['D60']['template_cards']

    with pytest.raises(BadRequest):
        handler._compute_technique_example({'endpoint': '/api/report_artifact'})


def test_chara_dasha_endpoint_alias_returns_jaimini_dasha_payload() -> None:
    handler = _handler()
    result = handler._compute_chara_dasha({
        'planets': jyotish_api_server.SAMPLE_PLANETS,
        'ascendant': jyotish_api_server.SAMPLE_ASCENDANT,
        'year': 1990,
        'month': 1,
        'day': 1,
        'hour': 12,
        'minute': 0,
        'lat': 28.6,
        'lon': 77.2,
        'tz': 5.5,
        'antardasha': True,
    })

    assert result['success'] is True
    assert result['endpoint'] == 'chara_dasha'
    assert result['alias_of'] == 'jaimini'
    assert result['mode'] == 'dasha'
    assert result['result']['chara_dasha']


def test_capability_audit_lists_chara_dasha_endpoint() -> None:
    handler = _handler()
    audit = handler._capability_audit()

    assert '/api/dasha/chara' in audit['surfaces']['api_endpoints']


def test_technique_catalog_exposes_chara_dasha_example() -> None:
    handler = _handler()
    catalog = handler._technique_catalog()

    assert '/api/dasha/chara' in catalog['filters']['api_endpoints']
    assert catalog['example_payloads']['/api/dasha/chara']['antardasha'] is True

    result = handler._compute_technique_example({'endpoint': '/api/dasha/chara'})
    assert result['success'] is True
    assert result['target_endpoint'] == '/api/dasha/chara'
    assert result['result']['result']['chara_dasha']


def test_thematic_report_declares_orchestrator_fragments() -> None:
    handler = _handler()
    result = handler._compute_thematic_report({'theme': 'marriage'})

    assert result['success'] is True
    assert result['endpoint'] == 'thematic_report'
    assert 'reading_orchestrator.py' in result['fragment_sources']
    assert 'orchestrator_bridge.py' in result['fragment_sources']
    assert result['workflow_orchestration']['bridge']['class'] == 'OrchestratorBridge'
    assert result['workflow_orchestration']['reading_theme_count'] >= 7
    assert 'marriage' in result['workflow_orchestration']['selected_report_themes']


def test_technique_catalog_exposes_high_rigor_workflow_entrypoint() -> None:
    handler = _handler()
    catalog = handler._technique_catalog()

    assert '/api/high_rigor_workflow' in catalog['filters']['api_endpoints']
    assert catalog['example_payloads']['/api/high_rigor_workflow']['theme'] == ['career', 'marriage', 'wealth']
    example = handler._compute_technique_example({'endpoint': '/api/high_rigor_workflow'})
    assert example['target_endpoint'] == '/api/high_rigor_workflow'
    assert example['result']['endpoint'] == 'high_rigor_workflow'
    assert example['result']['mode'] == 'plan_only_no_external_calls'


def test_thematic_report_derives_evidence_from_birth_payload() -> None:
    handler = _handler()
    result = handler._compute_thematic_report({
        'theme': ['marriage', 'career', 'wealth'],
        'year': 1990,
        'month': 1,
        'day': 1,
        'hour': 12,
        'minute': 0,
        'lat': 39.9,
        'lon': 116.4,
        'tz': 8,
    })

    assert result['success'] is True
    assert result['mode'] == 'derived_chart_evidence'
    assert result['evidence_source']['sample_fallback'] is False
    assert result['evidence_source']['source'] == 'full_reading_modules'
    assert result['evidence_source']['full_reading_used'] is True
    assert result['evidence_source']['full_reading_module_count'] >= 40
    assert result['evidence_source']['module_status']['full_reading'] == 'ok'
    assert result['evidence_source']['evidence_counts']['marriage'] >= 3
    assert result['evidence_source']['evidence_counts']['career'] >= 2
    marriage_sources = {
        item['details']['source']
        for item in result['themes']['marriage']['evidence']
    }
    assert 'chart' in marriage_sources
    assert 'full_reading.modules.marriage_counting' in marriage_sources
    assert 'full_reading.modules.relationship_strict_evidence.user_narrative' in marriage_sources
    assert any(item['details'].get('derived') for item in result['themes']['career']['evidence'])


def test_thematic_report_derives_relationship_strict_narrative_evidence() -> None:
    handler = _handler()
    result = handler._compute_thematic_report({
        'theme': ['marriage'],
        'year': 1990,
        'month': 1,
        'day': 1,
        'hour': 12,
        'minute': 0,
        'lat': 39.9,
        'lon': 116.4,
        'tz': 8,
    })

    assert result['success'] is True
    marriage_evidence = result['themes']['marriage']['evidence']
    strict_rows = [
        item for item in marriage_evidence
        if item['details'].get('source') == 'full_reading.modules.relationship_strict_evidence.user_narrative'
    ]
    assert strict_rows
    strict_note = strict_rows[0]['conclusion']
    assert 'dual dasha' in strict_note
    assert 'D9' in strict_note
    assert 'legal_marriage' in strict_note or '婚恋' in strict_note


def test_thematic_report_derives_career_and_finance_strict_narrative_evidence() -> None:
    handler = _handler()
    result = handler._compute_thematic_report({
        'theme': ['career', 'wealth'],
        'year': 1990,
        'month': 1,
        'day': 1,
        'hour': 12,
        'minute': 0,
        'lat': 39.9,
        'lon': 116.4,
        'tz': 8,
    })

    assert result['success'] is True
    career_evidence = result['themes']['career']['evidence']
    finance_evidence = result['themes']['wealth']['evidence']
    career_rows = [
        item for item in career_evidence
        if item['details'].get('source') == 'full_reading.modules.career_strict_evidence.user_narrative'
    ]
    finance_rows = [
        item for item in finance_evidence
        if item['details'].get('source') == 'full_reading.modules.finance_strict_evidence.user_narrative'
    ]
    assert career_rows
    assert finance_rows
    assert '月度主状态' in career_rows[0]['conclusion']
    assert 'D10' in career_rows[0]['conclusion'] or '事业' in career_rows[0]['conclusion']
    assert '月度主状态' in finance_rows[0]['conclusion']
    assert 'D2' in finance_rows[0]['conclusion'] or '财富' in finance_rows[0]['conclusion']


def test_thematic_report_final_chinese_summary_and_narrative_force_monthly_adjudication_layers() -> None:
    handler = _handler()
    result = handler._compute_thematic_report({
        'theme': ['marriage', 'career', 'wealth'],
        'year': 1990,
        'month': 1,
        'day': 1,
        'hour': 12,
        'minute': 0,
        'lat': 39.9,
        'lon': 116.4,
        'tz': 8,
    })

    assert result['success'] is True
    marriage = result['themes']['marriage']
    career = result['themes']['career']
    wealth = result['themes']['wealth']

    for payload in (marriage, career, wealth):
        assert '月度主状态' in payload['summary']
        assert '落地形式' in payload['summary']
        assert '阻力来源' in payload['narrative']
        assert '时间置信度' in payload['narrative']


def test_apply_monthly_adjudication_to_theme_report_injects_four_layers_into_final_chinese_fields() -> None:
    handler = _handler()
    payload = {
        'summary': '事业格局整体积极向好。',
        'narrative': '事业维度上，本命 promise 与 D10 形成交叉支持。',
        'evidence': [
            {
                'technique': 'Career-strict-narrative',
                'details': {
                    'monthly_frame': {
                        'primary_state': {'value': '推进'},
                        'manifestation_mode': {'value': '职位/项目/职责抬头'},
                        'friction_source': {'value': '流程卡顿但机会仍在'},
                        'time_confidence': {'value': 'month_supported'},
                    }
                },
            }
        ],
        'recommendations': ['原始建议一。'],
    }

    result = handler._apply_monthly_adjudication_to_theme_report('career', payload)

    assert '月度主状态：进入可主动推进窗口。' in result['summary']
    assert '落地形式：更像职位、项目或职责开始抬头。' in result['summary']
    assert '阻力来源：机会未消失，但流程、对接或资源节奏会更磨人。' in result['narrative']
    assert '时间置信度：以月份判断最稳，具体日期只能作辅助观察。' in result['narrative']
    assert any('月度主状态：进入可主动推进窗口。' in item for item in result['recommendations'])
    assert any('阻力来源：机会未消失，但流程、对接或资源节奏会更磨人。' in item for item in result['recommendations'])
    assert any('本轮重点拆成：角色定位、项目合作、组织权责、迁移动向。' in item for item in result['recommendations'])
    assert result['monthly_adjudication_summary']['primary_state']['value'] == '推进'
    assert result['monthly_adjudication_summary_humanized']['time_confidence'] == '以月份判断最稳，具体日期只能作辅助观察。'
    assert result['interpretation_axes'][0]['axis'] == '角色定位'
    assert 'judgement' in result['interpretation_axes'][0]
    assert '第10宫' in result['interpretation_axes'][0]['judgement']
    assert '进入可主动推进窗口' in result['interpretation_axes'][0]['judgement']
    assert '以月份判断最稳' in result['interpretation_axes'][0]['judgement']
    assert result['narrative_contract']['monthly_frame_applied'] is True


def test_thematic_report_interpretation_axes_are_strict_paragraphs_for_each_theme() -> None:
    handler = _handler()
    result = handler._compute_thematic_report({
        'theme': ['marriage', 'career', 'wealth'],
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
    })

    assert result['success'] is True
    career_axes = result['themes']['career']['interpretation_axes']
    marriage_axes = result['themes']['marriage']['interpretation_axes']
    wealth_axes = result['themes']['wealth']['interpretation_axes']
    career_bundle = result['themes']['career']['strict_adjudication_bundle']

    assert len(career_axes) >= 4
    assert len(marriage_axes) >= 4
    assert len(wealth_axes) >= 4

    assert career_bundle['interpretation_axes'][0]['axis'] == '角色定位'
    assert career_bundle['monthly_adjudication_summary']['primary_state']['value']
    assert 'strict_audit_gate' in career_bundle
    assert career_axes[0]['axis'] == '角色定位'
    assert 'judgement' in career_axes[0]
    assert '第10宫' in career_axes[0]['judgement']
    assert '时间边界' in career_axes[0]['judgement']

    assert marriage_axes[0]['axis'] == '关系推进'
    assert '第7宫' in marriage_axes[0]['judgement'] or 'D9' in marriage_axes[0]['judgement']
    assert '时间边界' in marriage_axes[0]['judgement']

    assert wealth_axes[0]['axis'] == '收入兑现'
    assert '第2宫' in wealth_axes[0]['judgement'] or '第11宫' in wealth_axes[0]['judgement']
    assert '时间边界' in wealth_axes[0]['judgement']


def test_fragment_audit_blocks_registry_surface_drift() -> None:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
    from audit_fragments import audit

    result = audit()
    assert result['valid'] is True, result['problems']
    assert result['registry']['technique_count'] >= 60
    assert result['workspace_residue']['untracked_count'] >= 0
    assert isinstance(result['workspace_residue']['untracked_files'], list)
    assert result['workspace_residue']['git_lost_found_count'] >= 0
    assert isinstance(result['workspace_residue']['git_lost_found_files'], list)
    assert result['open_source_sources']['source_count'] >= 3
    assert all(row['commands'] for row in result['rows'] if row['status'] in {'covered', 'complete'})
    assert not any(problem['kind'] == 'missing_output_path' for problem in result['problems'])


def test_fragment_audit_accepts_script_symbol_output_paths() -> None:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
    from audit_fragments import output_path_exists

    assert output_path_exists("scripts/yoga_engine.py:is_badhaka")[0] is True
    assert output_path_exists("scripts/prashna.py:calc_sphutas")[0] is True
    assert output_path_exists("scripts/tajika.py.graha_yuddha")[0] is True


def _sample_planets() -> dict:
    return {
        'Sun': {'lon': 80.0},
        'Moon': {'lon': 123.0},
        'Mars': {'lon': 210.0},
        'Mercury': {'lon': 75.0},
        'Jupiter': {'lon': 15.0},
        'Venus': {'lon': 102.0},
        'Saturn': {'lon': 330.0},
        'Rahu': {'lon': 5.0},
        'Ketu': {'lon': 185.0},
    }


def test_muhurta_endpoint_returns_activity_checks() -> None:
    handler = _handler()
    result = handler._compute_muhurta({
        'date': '2026-06-22',
        'activity': 'business',
        'planets': _sample_planets(),
    })

    assert result['success'] is True
    assert result['report']['query_date'] == '2026-06-22'
    assert 'business' in result['report']['activity_checks']


def test_muhurta_endpoint_returns_date_range_solver() -> None:
    handler = _handler()
    result = handler._compute_muhurta({
        'start_date': '2026-06-22',
        'end_date': '2026-06-28',
        'activity': 'business',
        'limit': 3,
        'lat': 28.6,
        'lon': 77.2,
        'tz': 5.5,
    })

    assert result['success'] is True
    assert result['endpoint'] == 'muhurta'
    solver = result['range_search']
    assert solver['mode'] == 'muhurta_date_range_solver'
    assert solver['activity'] == 'business'
    assert solver['candidate_count'] <= 3
    assert solver['best_windows']
    assert solver['constraints']['avoid_inauspicious_periods'] is True


def test_panchanga_range_endpoint_returns_calendar_rows() -> None:
    handler = _handler()
    result = handler._compute_panchanga_range({
        'start_date': '2026-06-22',
        'end_date': '2026-06-24',
        'sunrise': '06:00',
        'sunset': '18:00',
    })

    assert result['success'] is True
    assert result['endpoint'] == 'panchanga_range'
    assert result['report']['day_count'] == 3
    assert result['report']['days'][0]['inauspicious_periods']['rahu_kala']['label'] == 'Rahu Kala'
    assert 'condition_tags' in result['report']['days'][0]
    assert 'festival_details' in result['report']['days'][0]
    assert 'search_summary' in result['report']
    assert result['report']['calculation_policy']['festival_rules']


def test_panchanga_range_endpoint_uses_location_when_available() -> None:
    handler = _handler()
    result = handler._compute_panchanga_range({
        'start_date': '2026-06-22',
        'end_date': '2026-06-22',
        'lat': 28.6,
        'lon': 77.2,
        'tz': 5.5,
    })

    assert result['report']['location']['lon'] == 77.2
    assert result['report']['calculation_policy']['sunrise_sunset'] in {
        'SwissEph rise_trans',
        'location-aware solar approximation',
        'mixed SwissEph rise_trans with approximation fallback',
    }
    assert 'solar_times' in result['report']['days'][0]


def test_panchanga_range_rejects_large_ranges() -> None:
    handler = _handler()
    with pytest.raises(BadRequest, match='panchanga range must be <= 63 days'):
        handler._compute_panchanga_range({
            'start_date': '2026-01-01',
            'end_date': '2026-04-01',
        })


def test_rectification_gate_returns_varga_risk_summary() -> None:
    handler = _handler()
    result = handler._compute_rectification_gate({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
        'declared_accuracy': 'minute',
        'time_source': 'family_vague',
    })

    assert result['success'] is True
    assert result['endpoint'] == 'rectification_gate'
    assert result['effective_accuracy'] == '15min'
    assert 'headline' in result['summary']
    assert result['summary']['recommended_events']


def test_high_rigor_workflow_reuses_existing_rectification_backtest_and_vedastro_layers(monkeypatch) -> None:
    handler = _handler()

    fake_chart = {
        'success': True,
        'birth_info': {'date': '1955-02-24', 'time': '19:15', 'tz': 8},
        'chart': {
            'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
            'planets': _sample_planets(),
        },
        'modules': {
            'vedastro_range_scan_result': {
                'backend': 'vedastro_service_adapter_candidate',
                'status': 'partial',
                'event_count': 2,
                'source_metadata': {
                    'official_full_capability_catalog_status': 'partial',
                    'official_full_capability_catalog_summary': {
                        'catalog_method_count': 641,
                        'executed_method_count': 0,
                    },
                    'official_full_capability_domain_routing': {
                        'career': {'auto_method_count': 298, 'high_priority_methods': ['DasaAtRange']},
                    },
                    'official_full_capability_dynamic_selection': {
                        'career': {
                            'selected_methods': [
                                {'method': 'SearchEvents', 'citation_id': 'vedastro:career:SearchEvents'},
                            ],
                            'report_reference': {
                                'theme': 'career',
                                'citation_ids': ['vedastro:career:SearchEvents'],
                                'auto_count': 1,
                            },
                        },
                    },
                    'official_report_references': {
                        'career': {'citation_ids': ['vedastro:career:SearchEvents'], 'auto_count': 1},
                    },
                },
                'official_full_snapshot': {
                    'status': 'partial',
                    'source_metadata': {
                        'official_full_capability_catalog': {
                            'status': 'partial',
                            'summary': {'catalog_method_count': 641},
                            'domain_routing': {
                                'career': {'auto_method_count': 298, 'high_priority_methods': ['DasaAtRange']},
                            },
                            'dynamic_selection': {
                                'career': {
                                    'selected_methods': [
                                        {'method': 'SearchEvents', 'citation_id': 'vedastro:career:SearchEvents'},
                                    ],
                                    'report_reference': {
                                        'theme': 'career',
                                        'citation_ids': ['vedastro:career:SearchEvents'],
                                        'auto_count': 1,
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        'ai_prompt_pack': {
            'evidence_snapshot': {
                'vedastro_official_snapshot': {
                    'official_full_capability_catalog_summary': {
                        'catalog_method_count': 641,
                    },
                    'official_full_capability_domain_routing': {
                        'career': {'auto_method_count': 298, 'high_priority_methods': ['DasaAtRange']},
                    },
                    'official_full_capability_dynamic_selection': {
                        'career': {
                            'selected_methods': [
                                {'method': 'SearchEvents', 'citation_id': 'vedastro:career:SearchEvents'},
                            ],
                            'report_reference': {
                                'theme': 'career',
                                'citation_ids': ['vedastro:career:SearchEvents'],
                                'auto_count': 1,
                            },
                        },
                    },
                    'official_report_references': {
                        'career': {'citation_ids': ['vedastro:career:SearchEvents'], 'auto_count': 1},
                    },
                },
            },
        },
    }

    monkeypatch.setattr(handler, '_compute_chart', lambda body: fake_chart)
    monkeypatch.setattr(handler, '_compute_rectification_gate', lambda body: {
        'success': True,
        'endpoint': 'rectification_gate',
        'summary': {'recommended_events': ['career_change', 'relocation']},
    })
    monkeypatch.setattr(handler, '_compute_thematic_report', lambda body: {
        'success': True,
        'endpoint': 'thematic_report',
        'mode': 'derived_chart_evidence',
        'theme_count': len(body.get('theme') or []),
        'themes': {theme: {'summary': f'{theme} report'} for theme in body.get('theme') or []},
    })

    class FakeBacktest:
        @staticmethod
        def build_report(payload):
            return {
                'scope': 'historical_event_backtest',
                'summary': {'total_events': len(payload['events']), 'strong_hits': 1},
                'events': payload['events'],
            }

    def fake_loader(name):
        if name == 'historical_event_backtest':
            return FakeBacktest
        return _load_local_module(name)

    monkeypatch.setattr(jyotish_api_server, '_load_local_module', fake_loader)

    result = handler._compute_high_rigor_workflow({
        'question': '请高严谨分析我的事业、婚恋和财富',
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
        'events': [
            {'id': 'career_turn_2019', 'date': '2019-12-15', 'domain': 'career'},
            {'id': 'project_end_2025', 'date': '2025-02-28', 'domain': 'wealth'},
        ],
    })

    assert result['success'] is True
    assert result['endpoint'] == 'high_rigor_workflow'
    assert result['reused_modules'] == [
        'vedastro_evidence_orchestrator',
        'birth_time_rectifier',
        'historical_event_backtest',
        'report_orchestrator',
        'reading_orchestrator',
        'orchestrator_bridge',
    ]
    assert result['source_priority']['mode'] == 'vedastro_official_snapshot_first'
    assert result['vedastro_official']['official_full_capability_catalog_summary']['catalog_method_count'] == 641
    assert result['vedastro_official']['official_full_capability_domain_routing']['career']['auto_method_count'] == 298
    assert result['vedastro_official']['official_report_references']['career']['citation_ids'] == ['vedastro:career:SearchEvents']
    assert result['rectification']['endpoint'] == 'rectification_gate'
    assert result['historical_event_backtest']['summary']['total_events'] == 2
    assert result['thematic_report']['mode'] == 'derived_chart_evidence'
    assert result['routes'] == ['career', 'relationship', 'finance']
    assert result['unified_orchestrator']['name'] == 'UnifiedConsultationOrchestrator'
    assert result['unified_orchestrator']['surface'] == 'api_web'
    assert result['unified_orchestrator']['route']['question_type'] == 'career'


def test_consultation_workflow_uses_unified_orchestrator_contract(monkeypatch) -> None:
    handler = _handler()

    fake_chart = {
        'success': True,
        'birth_info': {'date': '1955-02-24', 'time': '19:15', 'tz': 8},
        'special_lagnas': {'precision': 'sunrise_correct'},
        'chart': {
            'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
            'planets': _sample_planets(),
        },
        'modules': {
            'vedastro_range_scan_result': {
                'backend': 'vedastro_service_adapter_candidate',
                'status': 'partial',
                'event_count': 1,
                'source_metadata': {
                    'official_full_capability_catalog_status': 'partial',
                    'official_full_capability_catalog_summary': {
                        'catalog_method_count': 641,
                        'executed_method_count': 0,
                    },
                },
            },
        },
        'ai_prompt_pack': {
            'evidence_snapshot': {
                'vedastro_official_snapshot': {
                    'official_full_capability_catalog_summary': {
                        'catalog_method_count': 641,
                    },
                },
            },
        },
    }

    monkeypatch.setattr(handler, '_compute_chart', lambda body: fake_chart)
    monkeypatch.setattr(handler, '_compute_rectification_gate', lambda body: {
        'success': True,
        'endpoint': 'rectification_gate',
        'summary': {'recommended_events': ['career_change']},
    })
    monkeypatch.setattr(handler, '_compute_thematic_report', lambda body: {
        'success': True,
        'endpoint': 'thematic_report',
        'mode': 'derived_chart_evidence',
        'theme_count': len(body.get('theme') or []),
        'themes': {theme: {'summary': f'{theme} report'} for theme in body.get('theme') or []},
    })

    class FakeBacktest:
        @staticmethod
        def build_report(payload):
            return {
                'scope': 'historical_event_backtest',
                'summary': {'total_events': len(payload['events']), 'strong_hits': 0},
                'events': payload['events'],
            }

    def fake_loader(name):
        if name == 'historical_event_backtest':
            return FakeBacktest
        return _load_local_module(name)

    monkeypatch.setattr(jyotish_api_server, '_load_local_module', fake_loader)

    result = handler._compute_consultation_workflow({
        'entry_mode': 'direct_chart',
        'question': '请直接排盘并重点看事业',
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
        'theme': ['career'],
        'blind': True,
    })

    assert result['success'] is True
    assert result['endpoint'] == 'consultation_workflow'
    assert result['entry_mode'] == 'direct_chart'
    assert result['routing']['question_type'] == 'career'
    assert result['unified_orchestrator']['name'] == 'UnifiedConsultationOrchestrator'
    assert result['unified_orchestrator']['surface'] == 'api_web'
    assert result['runtime_planner']['planner_name'] == 'UnifiedConsultationRuntimePlanner'
    assert result['runtime_planner']['entry_mode'] == 'direct_chart'
    assert result['runtime_planner']['route']['question_type'] == 'career'
    assert result['runtime_planner']['sync_steps'][0] == 'compute_chart'
    assert result['runtime_planner']['executed_steps'] == [
        'compute_chart',
        'run_rectification_gate',
        'run_thematic_report',
    ]
    assert 'run_historical_event_backtest' in result['runtime_planner']['skipped_steps']
    assert result['source_priority']['mode'] == 'vedastro_official_snapshot_first'
    assert result['runtime_evidence_log']['surface'] == 'api_web'
    assert result['runtime_evidence_log']['route']['question_type'] == 'career'
    assert result['runtime_evidence_log']['vedastro_cloud_state'] in {
        'official_verified',
        'official_blocked',
        'local_fallback',
    }
    assert result['runtime_evidence_log']['quality_gate']['technique_audit_table_required'] is True
    assert result['runtime_evidence_log']['quality_gate']['technique_audit_table'][0]['technique'] == 'VedAstro Cloud State'
    assert result['machine_evidence_packet']['status'] == 'partial'
    assert result['real_case_calibration']['status'] == 'partial_scored'
    assert result['real_case_calibration']['batch_id'] == 'real_case_studies_batch1'
    assert result['runtime_evidence_log']['evidence_packet_contract']['status'] == 'partial'
    assert result['runtime_evidence_log']['real_case_calibration']['status'] == 'partial_scored'
    assert result['runtime_evidence_log']['blind_technical_mode']['enabled'] is True
    assert 'conversation_feedback' in result['runtime_evidence_log']['blind_technical_mode']['disallowed_sources']
    assert result['chart']['special_lagnas']['precision'] == 'sunrise_correct'


def test_consultation_workflow_reuses_chart_data_for_thematic_report_without_recursive_full_reading(monkeypatch) -> None:
    handler = _handler()
    fake_chart = {
        'success': True,
        'birth_info': {'date': '1955-02-24', 'time': '19:15', 'tz': 8},
        'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
        'planets': _sample_planets(),
        'chart': {
            'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
            'planets': _sample_planets(),
        },
        'modules': {},
        'special_lagnas': {'precision': 'sunrise_correct'},
    }

    seen = {}

    monkeypatch.setattr(handler, '_compute_chart', lambda body: fake_chart)
    monkeypatch.setattr(handler, '_compute_rectification_gate', lambda body: {
        'success': True,
        'endpoint': 'rectification_gate',
        'summary': {'recommended_events': []},
    })
    monkeypatch.setattr(handler, '_run_high_rigor_historical_backtest', lambda birth, events: {
        'scope': 'historical_event_backtest',
        'summary': {'total_events': 0},
        'events': [],
    })

    def fake_thematic_report(body):
        seen['body'] = dict(body)
        return {
            'success': True,
            'endpoint': 'thematic_report',
            'mode': 'upstream_contract_reuse',
            'evidence_source': {
                'mode': 'upstream_contract_reuse',
                'source': 'consultation_workflow_upstream_contract',
            },
            'themes': {},
            'theme_count': len(body.get('theme') or []),
        }

    monkeypatch.setattr(handler, '_compute_thematic_report', fake_thematic_report)

    result = handler._compute_consultation_workflow({
        'entry_mode': 'direct_chart',
        'question': '请直接排盘并进入互动解盘',
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
        'theme': ['career', 'marriage', 'wealth'],
    })

    assert result['success'] is True
    assert seen['body']['chart_data']['birth_info']['date'] == '1955-02-24'
    assert seen['body']['chart_data']['ascendant']['sign'] == 'Cancer'
    assert seen['body']['skip_full_reading_for_thematic'] is True
    assert 'upstream_contract' in seen['body']
    assert 'strict_workflow_contracts' in seen['body']['upstream_contract']
    assert result['runtime_planner']['executed_steps'] == [
        'compute_chart',
        'run_rectification_gate',
        'run_thematic_report',
    ]
    assert 'run_historical_event_backtest' in result['runtime_planner']['skipped_steps']


def test_consultation_workflow_rectification_entry_reuses_chart_without_duplicate_compute(monkeypatch) -> None:
    handler = _handler()
    fake_chart = {
        'success': True,
        'birth_info': {'date': '1955-02-24', 'time': '19:15', 'tz': 8},
        'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
        'planets': _sample_planets(),
        'chart': {
            'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
            'planets': _sample_planets(),
        },
        'modules': {},
        'special_lagnas': {'precision': 'sunrise_correct'},
    }

    calls = {'count': 0}
    seen = {}

    def fake_chart_compute(body):
        calls['count'] += 1
        return fake_chart

    monkeypatch.setattr(handler, '_compute_chart', fake_chart_compute)
    monkeypatch.setattr(handler, '_compute_rectification_gate', lambda body: {
        'success': True,
        'endpoint': 'rectification_gate',
        'summary': {'recommended_events': ['marriage', 'career_change']},
    })
    monkeypatch.setattr(handler, '_run_high_rigor_historical_backtest', lambda birth, events: {
        'scope': 'historical_event_backtest',
        'summary': {'total_events': 0},
        'events': [],
    })

    def fake_thematic_report(body):
        seen['body'] = dict(body)
        return {
            'success': True,
            'endpoint': 'thematic_report',
            'mode': 'upstream_contract_reuse',
            'themes': {theme: {'summary': f'{theme} report'} for theme in body.get('theme') or []},
            'theme_count': len(body.get('theme') or []),
        }

    monkeypatch.setattr(handler, '_compute_thematic_report', fake_thematic_report)

    result = handler._compute_consultation_workflow({
        'entry_mode': 'rectification',
        'question': '先做生时校正，再看婚恋',
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
        'theme': ['marriage'],
    })

    assert result['success'] is True
    assert result['entry_mode'] == 'rectification'
    assert result['runtime_planner']['entry_mode'] == 'rectification'
    assert result['runtime_planner']['executed_steps'] == [
        'run_rectification_gate',
        'compute_chart',
        'run_thematic_report',
    ]
    assert calls['count'] == 1
    assert seen['body']['chart_data']['birth_info']['date'] == '1955-02-24'
    assert seen['body']['skip_full_reading_for_thematic'] is True


def test_consultation_workflow_rectification_entry_sends_empty_objects_before_chart(monkeypatch) -> None:
    handler = _handler()
    fake_chart = {
        'success': True,
        'birth_info': {'date': '1955-02-24', 'time': '19:15', 'tz': 8},
        'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
        'planets': _sample_planets(),
        'modules': {},
    }

    seen = {}

    monkeypatch.setattr(handler, '_compute_chart', lambda body: fake_chart)

    def fake_rectification_gate(body):
        seen['rectification_body'] = dict(body)
        return {
            'success': True,
            'endpoint': 'rectification_gate',
            'summary': {'recommended_events': []},
        }

    monkeypatch.setattr(handler, '_compute_rectification_gate', fake_rectification_gate)
    monkeypatch.setattr(handler, '_compute_thematic_report', lambda body: {
        'success': True,
        'endpoint': 'thematic_report',
        'mode': 'derived_chart_evidence',
        'theme_count': len(body.get('theme') or []),
    })

    result = handler._compute_consultation_workflow({
        'entry_mode': 'rectification',
        'question': '先做生时校正，再看事业',
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
        'theme': ['career'],
    })

    assert result['success'] is True
    assert result['runtime_planner']['executed_steps'][0] == 'run_rectification_gate'
    assert seen['rectification_body']['planets'] == {}
    assert seen['rectification_body']['ascendant'] == {}


def test_consultation_workflow_prashna_entry_uses_prashna_without_compute_chart(monkeypatch) -> None:
    handler = _handler()
    calls = {'chart': 0, 'prashna': 0}
    seen = {}

    def fake_chart_compute(body):
        calls['chart'] += 1
        return {'success': True, 'modules': {}}

    def fake_prashna(body):
        calls['prashna'] += 1
        seen['prashna_body'] = dict(body)
        return {
            'success': True,
            'endpoint': 'prashna',
            'question': body.get('question'),
            'timing': {'recommendation': '可以进行Prashna分析'},
            'judgement': {'summary': '可问'},
        }

    def fake_thematic_report(body):
        seen['theme_body'] = dict(body)
        return {
            'success': True,
            'endpoint': 'thematic_report',
            'mode': 'upstream_contract_reuse',
            'report': {'sections': []},
        }

    monkeypatch.setattr(handler, '_compute_chart', fake_chart_compute)
    monkeypatch.setattr(handler, '_compute_prashna', fake_prashna)
    monkeypatch.setattr(handler, '_compute_thematic_report', fake_thematic_report)
    monkeypatch.setattr(handler, '_compute_rectification_gate', lambda body: {'success': True, 'summary': {'recommended_events': []}})

    result = handler._compute_consultation_workflow({
        'entry_mode': 'prashna',
        'question': '这个合作能成吗',
        'question_text': '这个合作能成吗',
        'theme': ['wealth'],
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
    })

    assert result['success'] is True
    assert result['entry_mode'] == 'prashna'
    assert result['runtime_planner']['entry_mode'] == 'prashna'
    assert result['runtime_planner']['executed_steps'] == ['run_prashna', 'run_thematic_report']
    assert calls['chart'] == 0
    assert calls['prashna'] == 1
    assert seen['prashna_body']['question'] == '这个合作能成吗'


def test_consultation_workflow_builds_audited_remedies_from_guided_topic_gate(monkeypatch) -> None:
    handler = _handler()

    fake_chart = {
        'success': True,
        'birth_info': {'date': '1955-02-24', 'time': '19:15', 'tz': 8},
        'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
        'planets': _sample_planets(),
        'chart': {
            'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
            'planets': _sample_planets(),
        },
        'modules': {
            'guided_topics': [
                {
                    'id': 'career',
                    'title': '事业',
                    'strict_audit_gate': {
                        'topic': 'career',
                        'primary_planets': ['Saturn'],
                        'active_dasha_lord': 'Saturn',
                        'strength_context': {
                            'Saturn': {'total_rupas': 0.42, 'strength_level': 'weak'},
                        },
                        'dosha_context': ['delay_signature'],
                    },
                },
            ],
        },
        'special_lagnas': {'precision': 'sunrise_correct'},
    }

    monkeypatch.setattr(handler, '_compute_chart', lambda body: fake_chart)
    monkeypatch.setattr(handler, '_compute_rectification_gate', lambda body: {'success': True, 'summary': {'recommended_events': []}})
    monkeypatch.setattr(handler, '_compute_thematic_report', lambda body: {'success': True, 'endpoint': 'thematic_report', 'report': {'sections': []}})

    result = handler._compute_consultation_workflow({
        'entry_mode': 'direct_chart',
        'question': '请直接排盘并看事业',
        'theme': ['career'],
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
    })
    remedies = result.get('audited_remedies') or {}
    assert remedies['status'] == 'ok'
    assert remedies['source'] == 'strict_audit_gate'
    assert remedies['topic'] == 'career'
    assert remedies['active_dasha_lord'] == 'Saturn'


def test_consultation_workflow_timing_route_builds_muhurta_panchanga_sidecar(monkeypatch) -> None:
    handler = _handler()
    fake_chart = {
        'success': True,
        'birth_info': {'date': '1955-02-24', 'time': '19:15', 'tz': 8},
        'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
        'planets': _sample_planets(),
        'chart': {
            'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
            'planets': _sample_planets(),
        },
        'modules': {},
        'special_lagnas': {'precision': 'sunrise_correct'},
    }
    seen = {}

    monkeypatch.setattr(handler, '_compute_chart', lambda body: fake_chart)
    monkeypatch.setattr(handler, '_compute_rectification_gate', lambda body: {
        'success': True,
        'endpoint': 'rectification_gate',
        'summary': {'recommended_events': []},
    })
    monkeypatch.setattr(handler, '_compute_thematic_report', lambda body: {
        'success': True,
        'endpoint': 'thematic_report',
        'mode': 'derived_chart_evidence',
        'theme_count': len(body.get('theme') or []),
    })

    def fake_muhurta(body):
        seen['muhurta_body'] = dict(body)
        return {
            'status': 'ok',
            'source': 'local_muhurta.py',
            'activity': 'business',
            'report_mode': 'muhurta_date_range_solver',
            'panchanga': {'query_date': '2026-07-08'},
            'best_windows': [{'date': '2026-07-08'}],
        }

    monkeypatch.setattr(handler, '_compute_muhurta_panchanga', fake_muhurta)

    result = handler._compute_consultation_workflow({
        'entry_mode': 'direct_chart',
        'question': '2026年何时适合谈合作和推进项目的应期',
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
        'reference_date': '2026-07-08',
        'theme': ['career'],
    })
    assert result['success'] is True
    assert 'run_muhurta_panchanga' in result['runtime_planner']['executed_steps']
    assert result['muhurta_panchanga']['status'] == 'ok'
    assert result['muhurta_panchanga']['activity'] == 'business'
    assert seen['muhurta_body']['reference_date'] == '2026-07-08'


def test_thematic_report_handles_missing_dasa_convergence_without_crash(monkeypatch) -> None:
    handler = _handler()

    monkeypatch.setattr(handler, '_derive_thematic_evidence', lambda raw, report_orchestrator: {
        'chart_data': {
            'planets': _sample_planets(),
            'ascendant': {'lon': 92.0, 'sign': 'Cancer'},
            'houses': {},
            'dasha': {},
            'yogas': [],
            'ashtakavarga': {},
        },
        'evidence': {
            'career': [
                {
                    'technique': 'career_test',
                    'chart': 'D1',
                    'conclusion': 'career ok',
                    'sentiment': 'positive',
                    'strength': 'moderate',
                    'details': {'source': 'test'},
                }
            ],
            'marriage': [],
            'wealth': [],
            'health': [],
            'spirituality': [],
        },
        'module_status': {'full_reading': 'skipped_reuse_chart_data'},
        'warnings': [],
        'evidence_counts': {'career': 1, 'marriage': 0, 'wealth': 0, 'health': 0, 'spirituality': 0},
        'full_reading_used': False,
        'full_reading_summary': {},
        'full_reading_module_count': 0,
    })

    result = handler._compute_thematic_report({
        'theme': ['career'],
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
    })

    assert result['success'] is True
    assert result['mode'] == 'derived_chart_evidence'
    assert result['themes']['career']['evidence']


def test_derived_career_evidence_handles_none_top_convergent_domains() -> None:
    handler = _handler()
    items = handler._derived_career_evidence(
        {
            'planets': _sample_planets(),
            'ascendant': {'sign': 'Cancer'},
            'houses': {},
        },
        {
            'career': {'summary': 'career ok'},
            'shadbala': {'planets': {'Sun': {'rupas': 5.0}}},
            'full_modules': {'dasa_convergence': {'top_convergent_domains': None}},
        },
    )

    assert items


def test_case_validation_endpoint_returns_evidence_summary() -> None:
    handler = _handler()
    result = handler._compute_case_validation({
        'planets': {
            **_sample_planets(),
            'Moon': {'lon': 45.0},
            'Venus': {'lon': 40.0},
            'Saturn': {'lon': 10.0},
        },
        'ascendant': {'lon': 0.0},
        'current_md': 'Venus',
        'predicted_events': ['艺术创作', '关系发展'],
        'transit_desc': 'Jupiter tr 7',
    })

    assert result['success'] is True
    assert result['endpoint'] == 'case_validation'
    assert result['summary']['validated_count'] >= 1
    assert 'overall_confidence' in result['summary']
    assert 'mevg_automation.py' in result['fragment_sources']
    assert result['mevg_gate']['source'] == 'mevg_automation.py'
    assert result['summary']['gate_status'] in {'NOT_INITIALIZED', 'OPEN', 'CLOSED', 'UNKNOWN', 'UNAVAILABLE'}


def test_divisional_yoga_endpoint_returns_varga_yoga_summary() -> None:
    handler = _handler()
    result = handler._compute_divisional_yoga({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
        'divisions': ['D9', 'D10', 'D12'],
    })

    assert result['success'] is True
    assert result['endpoint'] == 'divisional_yoga'
    assert result['summary']['total_yogas'] >= 0
    assert {'D9', 'D10', 'D12'} <= set(result['result'])


def test_deep_varga_avastha_endpoint_returns_templates() -> None:
    handler = _handler()
    result = handler._compute_deep_varga_avastha({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
    })

    assert result['success'] is True
    assert result['endpoint'] == 'deep_varga_avastha'
    report = result['report']
    assert report['avastha_summary']['dominant_states']
    assert {'D24', 'D30', 'D60'} <= set(report['deep_varga_templates'])
    assert report['deep_varga_templates']['D24']['template_cards']
    assert report['deep_varga_templates']['D30']['risk_flags']
    assert report['deep_varga_templates']['D60']['next_action']


def test_kakshya_endpoint_returns_degree_trigger_summary() -> None:
    handler = _handler()
    result = handler._compute_kakshya({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
    })

    assert result['success'] is True
    assert result['endpoint'] == 'kakshya'
    assert result['summary']['average_strength'] >= 0
    assert result['summary']['strongest']
    assert 'planets' in result['result']


def test_bhava_bala_endpoint_returns_house_strength_summary() -> None:
    handler = _handler()
    result = handler._compute_bhava_bala_api({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
    })

    assert result['success'] is True
    assert result['endpoint'] == 'bhava_bala'
    assert result['summary']['strongest']
    assert result['summary']['weakest']
    assert 'houses' in result['result']


def test_transit_endpoint_returns_trigger_summary() -> None:
    handler = _handler()
    result = handler._compute_transit_triggers({
        'natal_planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
        'start': '2026-06-22',
        'end': '2026-07-22',
        'planets_to_check': ['Saturn', 'Jupiter'],
    })

    assert result['success'] is True
    assert result['endpoint'] == 'transit'
    assert 'total_triggers' in result['summary']
    assert 'triggers' in result


def test_annual_endpoint_returns_varshaphala_report() -> None:
    handler = _handler()
    result = handler._compute_annual({
        'year': 1990,
        'month': 6,
        'day': 15,
        'hour': 12,
        'minute': 0,
        'lat': 28.6,
        'lon': 77.2,
        'tz': 5.5,
        'target_year': 2026,
    })

    assert result['success'] is True
    assert result['report']['target_year'] == 2026
    assert 'muntha' in result['report']
    strength = result['report']['tajika_strength']
    assert strength['method'] == 'Tajika Harsha/Panchavargiya Bala'
    assert 'harsha_bala' in strength
    assert 'panchavargiya_bala' in strength
    assert strength['summary']['strongest_planets']
    assert strength['summary']['next_action']


def test_tajika_endpoint_alias_returns_varshaphala_report() -> None:
    handler = _handler()
    result = handler._compute_tajika({
        'year': 1990,
        'month': 6,
        'day': 15,
        'hour': 12,
        'minute': 0,
        'lat': 28.6,
        'lon': 77.2,
        'tz': 5.5,
        'target_year': 2026,
    })

    assert result['success'] is True
    assert result['endpoint'] == 'tajika'
    assert result['alias_of'] == 'annual'
    assert result['report']['target_year'] == 2026
    assert 'muntha' in result['report']
    strength = result['report']['tajika_strength']
    assert strength['method'] == 'Tajika Harsha/Panchavargiya Bala'
    assert strength['summary']['strongest_planets']


def test_bhava_chalit_endpoint_compares_shifted_houses() -> None:
    handler = _handler()
    result = handler._compute_bhava_chalit({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
        'mc_lon': 10.0,
        'house_system': 'sripati',
    })

    assert result['success'] is True
    assert result['result']['house_system'] == 'sripati'
    assert 'rashi_chart' in result['result']


def test_bhava_chalit_endpoint_exposes_user_selected_house_systems() -> None:
    handler = _handler()
    base = {
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
        'mc_lon': 10.0,
        'year': 1990,
        'month': 6,
        'day': 15,
        'hour': 12,
        'minute': 0,
        'lat': 28.6,
        'lon': 77.2,
        'tz': 5.5,
    }

    sripati = handler._compute_bhava_chalit({**base, 'house_system': 'sripati'})
    placidus = handler._compute_bhava_chalit({**base, 'house_system': 'placidus'})

    for result, expected in [(sripati, 'sripati'), (placidus, 'placidus')]:
        assert result['success'] is True
        assert result['requested_house_system'] == expected
        assert result['selected_house_system'] == expected
        assert 'placidus' in result['available_house_systems']
        assert 'sripati' in result['available_house_systems']
        assert result['result']['selected_house_system'] == expected
        assert result['result']['requested_house_system'] == expected
        assert len(result['result']['boundaries']['houses']) == 12
        assert result['result']['summary']['total_planets'] >= 7
        assert result['result']['calculation_note']


def test_sudarshana_endpoint_returns_three_reference_points() -> None:
    handler = _handler()
    result = handler._compute_sudarshana({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
    })

    assert result['success'] is True
    assert {'ascendant_lagna', 'moon_lagna', 'sun_lagna'} <= set(result['result']['reference_points'])


def test_nakshatra_full_endpoint_returns_power_layers() -> None:
    handler = _handler()
    result = handler._compute_nakshatra_full({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
        'age': 36,
    })

    assert result['success'] is True
    assert 'tara_bala' in result['result']
    assert 'sub_lords' in result['result']


def test_varga_full_endpoint_returns_extended_standard_divisions() -> None:
    handler = _handler()
    result = handler._compute_varga_full({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
        'divisions': ['D9', 'D60', 'D81', 'D108', 'D144'],
    })

    assert result['success'] is True
    assert result['mode'] == 'standard'
    assert result['divisions'] == [9, 60, 81, 108, 144]
    assert 'D144_Dwadasamsa-Dwadasamsa' in result['result']
    assert result['result']['D81_Navamsa-Navamsa']['planets']['Moon']['house'] in range(1, 13)


def test_varga_full_endpoint_supports_custom_and_composite_modes() -> None:
    handler = _handler()
    custom = handler._compute_varga_full({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
        'custom': 150,
    })
    composite = handler._compute_varga_full({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
        'composite': '9,12',
    })

    assert custom['mode'] == 'custom'
    assert custom['result']['Moon']['div'] == 150
    assert composite['mode'] == 'composite'
    assert composite['result']['composite_div'] == 'D9×D12=D108'


def test_varga_full_endpoint_supports_d2_d3_variants() -> None:
    handler = _handler()
    result = handler._compute_varga_full({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
        'divisions': 'D3',
        'variant': 'khara',
    })

    assert result['success'] is True
    assert result['mode'] == 'variant'
    assert result['result']['div'] == 3
    assert result['result']['Moon']['variant'] == 'khara'


def test_jaimini_endpoint_returns_karakas_and_arudha() -> None:
    handler = _handler()
    result = handler._compute_jaimini({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
        'year': 1990,
        'month': 6,
        'hour': 12,
        'minute': 0,
    })

    assert result['success'] is True
    assert 'chara_karaka_7' in result['result']
    assert 'Atmakaraka' in result['result']['chara_karaka_7']['karaka_table']
    assert 'arudha_padas' in result['result']


def test_ashtakavarga_endpoint_preserves_sav_invariant() -> None:
    handler = _handler()
    result = handler._compute_ashtakavarga({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
    })

    assert result['success'] is True
    assert result['result']['sav']['total'] == 337
    assert result['result']['sav']['valid'] is True
    assert result['summary']['strongest_houses']
    assert result['pav_summary']['top_planets']
    assert result['sodhita_summary']['top_signs']


def test_remedies_endpoint_returns_evidence_chain() -> None:
    handler = _handler()
    result = handler._compute_remedies({
        'shadbala': {
            'Sun': {'total_rupas': 0.42},
            'Moon': {'rupas': 0.68},
        },
        'dasha_lord': 'Sun',
        'doshas': ['Mangal Dosha'],
    })

    assert result['weak_planets'] == ['Sun']
    assert 'evidence_chain' in result
    assert any(item['source'] == 'shadbala' and item['planet'] == 'Sun' for item in result['evidence_chain'])
    assert any(item['source'] == 'dasha' for item in result['evidence_chain'])
    assert result['next_action']


def test_shadbala_endpoint_returns_ranked_planet_strength() -> None:
    handler = _handler()
    result = handler._compute_shadbala({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
        'hour': 12,
        'minute': 0,
    })

    assert result['success'] is True
    assert result['result']['ranking']
    assert 'total_rupas' in result['result']['planets']['Sun']
    assert result['rule_variants']['selected'] == ['core_sixfold', 'advanced_evidence']
    assert result['advanced_layer']['source'] == 'scripts/shadbala_advanced.py'
    assert result['advanced_layer']['top_kala_support']
    assert 'sputa_drik_bala' in result['advanced_layer']


def test_chart_ai_prompt_pack_exposes_functional_benefic_malefic_layer() -> None:
    handler = _handler()

    result = handler._compute_chart({
        'year': 1990,
        'month': 6,
        'day': 15,
        'hour': 12,
        'minute': 0,
        'lat': 39.9,
        'lon': 116.4,
        'tz': 8,
    })

    prompt_pack = result['ai_prompt_pack']
    functional = prompt_pack['evidence_snapshot']['functional_benefic_malefic']
    assert functional['status'] == 'used'
    assert functional['ascendant']
    assert isinstance(functional['functional_benefics'], list)
    assert isinstance(functional['functional_malefics'], list)
    assert functional['effect_on_confidence']
    vedastro = prompt_pack['evidence_snapshot']['vedastro_overview']
    assert vedastro['source'] == 'vedastro_service_adapter_candidate'
    assert vedastro['ingestion_profile'] == 'main_entry_overview'
    assert vedastro['visibility'] == 'user_visible_overview_only'
    official = prompt_pack['evidence_snapshot']['vedastro_official_full_snapshot']
    assert official['primary_source'] == 'vedastro_official'
    assert 'official_python_path' in official
    assert 'official_bundle_status' in official
    assert 'official_chart_available' in official
    assert 'official_full_capability_catalog_status' in official
    assert 'official_full_capability_catalog_summary' in official
    assert 'official_full_capability_domain_routing' in official
    assert 'official_full_capability_dynamic_selection' in official
    assert 'official_report_references' in official


def test_chart_auto_attaches_vedastro_main_entry_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://example.invalid/api")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "0")
    monkeypatch.setenv("JYOTISH_SKIP_LOCAL_ENV", "1")

    handler = _handler()
    result = handler._compute_chart({
        'year': 1990,
        'month': 6,
        'day': 15,
        'hour': 12,
        'minute': 0,
        'lat': 39.9,
        'lon': 116.4,
        'tz': 8,
    })

    assert "modules" in result
    vedastro = result["modules"]["vedastro_range_scan_result"]
    assert vedastro["backend"] == "vedastro_service_adapter_candidate"
    assert vedastro["status"] == "network_execution_disabled"


def test_api_chart_response_cache_reuses_cached_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JYOTISH_API_CHART_CACHE_TTL_SECONDS", "600")
    monkeypatch.delenv("VEDASTRO_API_ENDPOINT", raising=False)
    monkeypatch.delenv("VEDASTRO_ENABLE_NETWORK", raising=False)
    payload = {
        'year': 1990,
        'month': 6,
        'day': 15,
        'hour': 12,
        'minute': 0,
        'second': 0,
        'lat': 39.9,
        'lon': 116.4,
        'tz': 8,
        'ayanamsa': 'lahiri',
        'node_mode': 'mean',
        'today': '2026-06-30',
        'transit_date': '2026-06-30',
    }
    cache_payload = jyotish_api_server._build_api_chart_cache_payload(payload)
    stored = jyotish_api_server._store_api_chart_response_cache(
        cache_payload,
        {'success': True, 'modules': {'chart': {'planets': {}, 'ascendant': {}}}},
    )
    cached = jyotish_api_server._load_api_chart_response_cache(cache_payload)

    assert stored['runtime_cache']['scope'] == 'api_chart_response'
    assert stored['runtime_cache']['cache_hit'] is False
    assert cached is not None
    assert cached['runtime_cache']['cache_hit'] is True
    assert cached['runtime_cache']['cache_key'] == stored['runtime_cache']['cache_key']


def test_api_chart_cache_key_tracks_vedastro_runtime_state(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        'year': 1990,
        'month': 6,
        'day': 15,
        'hour': 12,
        'minute': 0,
        'second': 0,
        'lat': 39.9,
        'lon': 116.4,
        'tz': 8,
        'ayanamsa': 'lahiri',
        'node_mode': 'mean',
        'today': '2026-06-30',
        'transit_date': '2026-06-30',
    }
    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://vedastro.example.test/api")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "0")
    key_disabled = jyotish_api_server._api_chart_cache_key(
        jyotish_api_server._build_api_chart_cache_payload(payload)
    )

    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "1")
    key_enabled = jyotish_api_server._api_chart_cache_key(
        jyotish_api_server._build_api_chart_cache_payload(payload)
    )

    assert key_disabled != key_enabled


def test_high_rigor_plan_only_surfaces_chart_cache_and_queue_strategy() -> None:
    handler = _handler()

    result = handler._high_rigor_workflow_plan_only(
        {
            'year': 1955,
            'month': 2,
            'day': 24,
            'hour': 19,
            'minute': 15,
            'lat': 36.4467,
            'lon': -122.4194,
            'tz': 8,
        },
        ['career'],
        [],
    )

    strategy = result['execution_strategy']
    assert strategy['chart_path']['mode'] == 'sync_chart_response_cache'
    assert strategy['chart_path']['cache_scope'] == 'api_chart_response'
    assert strategy['queue_recommendation']['recommended'] is True
    assert strategy['queue_recommendation']['lane'] == 'high_rigor_workflow'


def test_high_rigor_async_submit_returns_job_id(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = _handler()

    monkeypatch.setattr(handler, '_enqueue_high_rigor_job', lambda body: {
        'success': True,
        'endpoint': 'high_rigor_workflow_async',
        'mode': 'async_submitted',
        'job_id': 'hrw_test_job_1',
        'status': 'queued',
        'poll_path': '/api/high_rigor_workflow/jobs/hrw_test_job_1',
    })

    result = handler._compute_high_rigor_workflow({
        'async': True,
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
    })

    assert result['mode'] == 'async_submitted'
    assert result['job_id'] == 'hrw_test_job_1'
    assert result['status'] == 'queued'
    assert result['poll_path'].endswith('/hrw_test_job_1')


def test_chart_async_submit_returns_job_id(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = _handler()

    monkeypatch.setattr(handler, '_enqueue_chart_job', lambda body: {
        'success': True,
        'endpoint': 'chart_async',
        'mode': 'async_submitted',
        'job_id': 'chart_test_job_1',
        'status': 'queued',
        'poll_path': '/api/chart/jobs/chart_test_job_1',
        'scope': 'api_chart_response',
    })

    result = handler._compute_chart({
        'async': True,
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
    })

    assert result['mode'] == 'async_submitted'
    assert result['job_id'] == 'chart_test_job_1'
    assert result['status'] == 'queued'
    assert result['poll_path'].endswith('/chart_test_job_1')
    assert result['scope'] == 'api_chart_response'


def test_high_rigor_job_poll_endpoint_returns_cached_job_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jyotish_api_server, '_load_high_rigor_job_record', lambda job_id: {
        'success': True,
        'endpoint': 'high_rigor_workflow_async',
        'mode': 'async_result',
        'job_id': job_id,
        'status': 'completed',
        'result': {'success': True, 'endpoint': 'high_rigor_workflow'},
    })
    handler = _HighRigorJobCaptureHandler('/api/high_rigor_workflow/jobs/hrw_test_job_2')

    handler.do_GET()

    assert handler.status_code == 200
    payload = handler.payload()
    assert payload['job_id'] == 'hrw_test_job_2'
    assert payload['status'] == 'completed'
    assert payload['result']['endpoint'] == 'high_rigor_workflow'


def test_chart_job_poll_endpoint_returns_cached_job_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jyotish_api_server, '_load_async_job_record', lambda scope, job_id: {
        'success': True,
        'endpoint': 'chart_async',
        'mode': 'async_result',
        'job_id': job_id,
        'status': 'completed',
        'scope': scope,
        'result': {'success': True, 'runtime_cache': {'scope': 'api_chart_response'}},
    })
    handler = _HighRigorJobCaptureHandler('/api/chart/jobs/chart_test_job_2')

    handler.do_GET()

    assert handler.status_code == 200
    payload = handler.payload()
    assert payload['job_id'] == 'chart_test_job_2'
    assert payload['status'] == 'completed'
    assert payload['scope'] == 'api_chart_response'
    assert payload['result']['runtime_cache']['scope'] == 'api_chart_response'


def test_high_rigor_async_job_executes_in_background(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = _handler()
    writes: list[tuple[str, dict]] = []

    def fake_write(job_id: str, payload: dict) -> dict:
        writes.append((job_id, dict(payload)))
        return payload

    def fake_sync(body: dict) -> dict:
        time.sleep(0.05)
        return {'success': True, 'endpoint': 'high_rigor_workflow', 'body': dict(body)}

    monkeypatch.setattr(jyotish_api_server, '_write_high_rigor_job_record', fake_write)
    monkeypatch.setattr(handler, '_compute_high_rigor_workflow_sync', fake_sync)

    result = handler._enqueue_high_rigor_job({
        'async': True,
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
    })

    assert result['mode'] == 'async_submitted'
    assert result['status'] == 'queued'
    assert writes[0][1]['status'] == 'queued'
    assert writes[1][1]['status'] == 'running'
    assert len(writes) == 2

    deadline = time.time() + 1.0
    while len(writes) < 3 and time.time() < deadline:
        time.sleep(0.01)

    assert len(writes) >= 3
    assert writes[-1][1]['status'] == 'completed'
    assert writes[-1][1]['mode'] == 'async_result'
    assert writes[-1][1]['result']['endpoint'] == 'high_rigor_workflow'


def test_chart_async_job_executes_in_background(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = _handler()
    writes: list[tuple[str, str, dict]] = []

    def fake_write(scope: str, job_id: str, payload: dict) -> dict:
        writes.append((scope, job_id, dict(payload)))
        return payload

    def fake_sync(body: dict) -> dict:
        time.sleep(0.05)
        return {
            'success': True,
            'modules': {'chart': {'planets': {}, 'ascendant': {}}},
            'runtime_cache': {'scope': 'api_chart_response'},
        }

    monkeypatch.setattr(jyotish_api_server, '_write_async_job_record', fake_write)
    monkeypatch.setattr(handler, '_compute_chart_sync', fake_sync)

    result = handler._enqueue_chart_job({
        'async': True,
        'year': 1955,
        'month': 2,
        'day': 24,
        'hour': 19,
        'minute': 15,
        'lat': 37.7749,
        'lon': -122.4194,
        'tz': 8,
    })

    assert result['endpoint'] == 'chart_async'
    assert result['mode'] == 'async_submitted'
    assert result['status'] == 'queued'
    assert writes[0][0] == 'api_chart_response'
    assert writes[0][2]['status'] == 'queued'
    assert writes[1][2]['status'] == 'running'

    deadline = time.time() + 1.0
    while len(writes) < 3 and time.time() < deadline:
        time.sleep(0.01)

    assert len(writes) >= 3
    assert writes[-1][2]['status'] == 'completed'
    assert writes[-1][2]['mode'] == 'async_result'
    assert writes[-1][2]['result']['runtime_cache']['scope'] == 'api_chart_response'
    assert 'modules' in writes[-1][2]['result']


def test_yogas_endpoint_returns_summary_counts() -> None:
    handler = _handler()
    result = handler._compute_yogas_api({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
    })

    assert result['success'] is True
    assert 'extended_count' in result['result']['summary']
    assert 'rule_engine_count' in result['result']['summary']
    assert 'curse_count' in result['result']['summary']
    assert any(item['key'] == 'curse_conjunctions' for item in result['rule_variants']['available'])


def test_yogas_endpoint_reuses_curse_yoga_fragment() -> None:
    handler = _handler()
    planets = _sample_planets()
    planets['Mars'] = {'lon': 210.0}
    planets['Saturn'] = {'lon': 211.0}
    result = handler._compute_yogas_api({
        'planets': planets,
        'ascendant': {'lon': 92.0},
        'current_dasha': 'Saturn',
    })

    curse_layer = result['result']['curse_yogas']
    assert result['success'] is True
    assert result['result']['summary']['curse_count'] == 1
    assert curse_layer['overall_risk'] in {'high', 'critical'}
    assert curse_layer['curses_detected'][0]['type'] == 'yama_yoga'
    assert result['rule_variants']['selected'][-1] == 'curse_conjunctions'


def test_aspects_endpoint_returns_pair_summary() -> None:
    handler = _handler()
    result = handler._compute_aspects({
        'planets': _sample_planets(),
        'ascendant': {'lon': 92.0},
    })

    assert result['success'] is True
    assert result['result']['summary']['total_aspects'] >= 0
    assert 'by_type' in result['result']['summary']
