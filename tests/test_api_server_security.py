#!/usr/bin/env python3
"""Security boundary tests for the lightweight Jyotish API server."""

from __future__ import annotations

import base64
import json
import os
import sys
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


def test_vedastro_range_scan_endpoint_uses_user_birth_and_returns_controlled_blocked_state(monkeypatch) -> None:
    monkeypatch.delenv('VEDASTRO_API_ENDPOINT', raising=False)
    monkeypatch.delenv('VEDASTRO_ENABLE_NETWORK', raising=False)
    handler = _PostCaptureHandler('/api/vedastro/range_scan', {
        'domain': 'relationship',
        'start_date': '2026-01-01',
        'end_date': '2026-12-31',
        'year': REDACTED_YEAR,
        'month': 4,
        'day': 17,
        'hour': 14,
        'minute': 49,
        'second': 0,
        'lat': 36.4467,
        'lon': 114.2,
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
    assert payload['result']['request_preview']['year'] == REDACTED_YEAR
    assert payload['result']['request_preview']['lat'] == 36.4467
    assert payload['result']['request_preview']['domain'] == 'marriage'
    assert payload['boundary'] == 'VedAstro range scan is optional external timing evidence; local Jyotish gates remain authoritative.'


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
        'case_id': 'template_user_REDACTED_YEAR_moon_longitude_lahiri',
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
