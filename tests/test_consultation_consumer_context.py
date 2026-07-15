#!/usr/bin/env python3
"""Chat-facing consultation contract regression tests."""

from __future__ import annotations

import os
import sys

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from jyotish_api_server import (  # noqa: E402
    JyotishAPIHandler,
    _attach_local_consultation_layers,
    _build_consumer_context,
)
from unified_consultation_orchestrator import UnifiedConsultationOrchestrator  # noqa: E402


def _handler() -> JyotishAPIHandler:
    return JyotishAPIHandler.__new__(JyotishAPIHandler)


def _base_chart() -> dict:
    longitudes = {
        'Sun': 120.9,
        'Moon': 31.4,
        'Mars': 173.2,
        'Mercury': 140.1,
        'Jupiter': 222.1,
        'Venus': 120.2,
        'Saturn': 329.5,
        'Rahu': 215.8,
        'Ketu': 35.8,
    }
    asc_lon = 205.19
    asc_idx = int(asc_lon / 30)
    planets = {
        name: {
            'lon': lon,
            'degree': lon % 30,
            'sign_idx': int(lon / 30),
            'house': ((int(lon / 30) - asc_idx) % 12) + 1,
        }
        for name, lon in longitudes.items()
    }
    return {
        'success': True,
        'ascendant': {'lon': asc_lon, 'sign_idx': asc_idx, 'sign': 'Libra'},
        'planets': planets,
        'houses': {house: {'sign_idx': (asc_idx + house - 1) % 12} for house in range(1, 13)},
        'dasha': {'current_md': 'Sun'},
        'modules': {'dasha': {'current_md': 'Sun'}},
    }


def test_local_consultation_layers_supply_d10_a10_and_narayana_without_vedastro() -> None:
    chart = _attach_local_consultation_layers(
        _handler(),
        _base_chart(),
        {'year': 1995, 'month': 8, 'day': 18, 'hour': 12, 'minute': 0},
        {'current_date': '2026-07-14'},
    )

    modules = chart['modules']
    assert 'D9_Navamsa' in modules['varga_full']
    assert 'D10_Dasamsa' in modules['varga_full']
    assert modules['arudha_padas']['padas']['A10']['name'] == 'Karma Pada (A10)'
    assert modules['narayana_dasha']['current_dasha']['md']
    assert chart['local_consultation_layers']['status'] == 'ready'

    packet = UnifiedConsultationOrchestrator().machine_evidence_packet(
        chart=chart,
        route_packet={'question_type': 'career', 'primary_theme': 'career'},
        vedastro_official={'status': 'blocked', 'runtime_truth': {'status': 'blocked'}},
    )
    assert packet['sections']['D10']['status'] == 'used'
    assert packet['sections']['A10']['status'] == 'used'
    assert packet['sections']['narayana_dasha']['status'] == 'used'


def test_consumer_context_treats_unconfigured_vedastro_as_optional_cross_check() -> None:
    chart = _attach_local_consultation_layers(
        _handler(),
        _base_chart(),
        {'year': 1995, 'month': 8, 'day': 18, 'hour': 12, 'minute': 0},
        {'current_date': '2026-07-14'},
    )
    orchestrator = UnifiedConsultationOrchestrator()
    route = orchestrator.resolve_route('请分析我的事业方向', ['career'])
    official = {
        'status': 'service_endpoint_not_configured',
        'runtime_truth': {
            'status': 'partial',
            'official_execution_layers': {'chart_core': 'blocked'},
            'fallback_active': False,
        },
    }
    packet = orchestrator.machine_evidence_packet(
        chart=chart,
        route_packet=route,
        vedastro_official=official,
    )
    context = _build_consumer_context(
        question='请分析我的事业方向',
        route_packet=route,
        chart=chart,
        rectification={
            'summary': {
                'headline': '可读主盘，但高敏分盘需要降级',
                'warned': ['D9', 'D10'],
                'disabled': [],
            },
        },
        machine_evidence_packet=packet,
        vedastro_official=official,
    )

    assert context['core_status'] == 'ready'
    assert context['hard_blockers'] == []
    assert context['missing_route_layers'] == []
    assert context['answer_policy']['can_answer_direction'] is True
    assert context['answer_policy']['should_lead_with_limitations'] is False
    assert context['answer_policy']['provider_unavailable_is_fatal'] is False
    assert context['optional_unavailable_layers'][0]['layer'] == 'vedastro_official_cross_check'


def test_consumer_context_only_leads_with_limits_for_unavailable_precise_timing() -> None:
    orchestrator = UnifiedConsultationOrchestrator()
    route = orchestrator.resolve_route('具体哪一个月份适合跳槽？', ['career'])
    packet = {
        'sections': {
            'D1': {'status': 'used'},
            'D10': {'status': 'used'},
            'A10': {'status': 'used'},
            'dasha_boundaries': {'status': 'used'},
            'narayana_dasha': {'status': 'missing'},
            'external_oracle_status': {'status': 'official_blocked'},
        },
    }
    context = _build_consumer_context(
        question='具体哪一个月份适合跳槽？',
        route_packet=route,
        chart={'success': True},
        rectification={'summary': {'warned': ['D10'], 'disabled': []}},
        machine_evidence_packet=packet,
        vedastro_official={'status': 'blocked'},
    )

    assert context['core_status'] == 'degraded'
    assert context['answer_policy']['can_answer_direction'] is True
    assert context['answer_policy']['can_answer_precise_timing'] is False
    assert context['answer_policy']['should_lead_with_limitations'] is True


def test_thematic_career_evidence_uses_local_d10_a10_and_narayana() -> None:
    handler = _handler()
    chart = _attach_local_consultation_layers(
        handler,
        _base_chart(),
        {'year': 1995, 'month': 8, 'day': 18, 'hour': 12, 'minute': 0},
        {'current_date': '2026-07-14'},
    )

    items = handler._derived_career_evidence(
        chart,
        {
            'career': {'summary': 'career ready'},
            'shadbala': {},
            'full_modules': chart['modules'],
        },
    )

    by_technique = {item['technique']: item for item in items}
    assert by_technique['D10-Dashamsha-local']['chart'] == 'D10'
    assert by_technique['A10-Karma-Pada-local']['chart'] == 'A10'
    assert by_technique['Narayana-Dasha-local']['chart'] == 'Narayana'
    assert '已完成' in by_technique['D10-Dashamsha-local']['conclusion']


def test_thematic_report_reuses_attached_chart_modules_without_claiming_d10_missing(monkeypatch) -> None:
    handler = _handler()
    chart = _attach_local_consultation_layers(
        handler,
        _base_chart(),
        {'year': 1995, 'month': 8, 'day': 18, 'hour': 12, 'minute': 0},
        {'current_date': '2026-07-14'},
    )

    monkeypatch.setattr(handler, '_compute_dasha_system', lambda body: chart['modules']['dasha'])
    monkeypatch.setattr(handler, '_compute_yogas_api', lambda body: {})
    monkeypatch.setattr(handler, '_compute_shadbala', lambda body: {})
    monkeypatch.setattr(handler, '_compute_ashtakavarga', lambda body: {})
    monkeypatch.setattr(handler, '_compute_relationship', lambda body: {})
    monkeypatch.setattr(handler, '_compute_career', lambda body: {'summary': 'career ready'})
    monkeypatch.setattr(handler, '_compute_jaimini', lambda body: chart['modules'].get('jaimini', {}))

    result = handler._compute_thematic_report({
        'theme': ['career'],
        'chart_data': {
            **chart,
            'skip_full_reading_for_thematic': True,
        },
        'skip_full_reading_for_thematic': True,
    })

    career = result['themes']['career']
    techniques = {item['technique'] for item in career['evidence']}
    assert result['mode'] == 'derived_chart_evidence'
    assert result['evidence_source']['source'] == 'reused_chart_modules'
    assert result['evidence_source']['chart_modules_reused'] is True
    assert 'D10-Dashamsha-local' in techniques
    assert 'A10-Karma-Pada-local' in techniques
    assert 'Narayana-Dasha-local' in techniques
    assert 'Dashamsha 未提供显著信息' not in career['narrative']


def test_strict_narrative_tolerates_optional_none_contracts() -> None:
    from jyotish_engine import _base_strict_narrative_payload

    payload = _base_strict_narrative_payload(
        '事业',
        {
            'event_judgement': None,
            'adjudication_stages': None,
            'prediction_boundary_contract': None,
        },
        fallback_headline='事业结构可读',
        strengths=[],
        risks=[],
        boundaries=[],
    )

    assert payload['headline'] == '事业结构可读'
    assert 'confidence_cap: unknown' in payload['markdown']


def test_consumer_context_does_not_surface_optional_provider_as_user_limitation() -> None:
    context = _build_consumer_context(
        question='请分析我的事业方向',
        route_packet={'question_type': 'career', 'primary_theme': 'career'},
        chart={'success': True},
        rectification={'summary': {'warned': ['D9'], 'disabled': []}},
        machine_evidence_packet={
            'sections': {
                'D1': {'status': 'used'},
                'D10': {'status': 'used'},
                'A10': {'status': 'used'},
                'dasha_boundaries': {'status': 'used'},
                'narayana_dasha': {'status': 'used'},
                'external_oracle_status': {'status': 'official_blocked'},
            },
        },
        vedastro_official={'status': 'blocked'},
    )

    assert context['user_facing_limitation'] is None
    assert context['optional_unavailable_layers'][0]['layer'] == 'vedastro_official_cross_check'


def test_failed_vedastro_raw_packet_is_not_marked_as_used() -> None:
    packet = UnifiedConsultationOrchestrator().machine_evidence_packet(
        chart=_base_chart(),
        route_packet={'question_type': 'career', 'primary_theme': 'career'},
        vedastro_official={
            'status': 'partial',
            'runtime_truth': {
                'status': 'partial',
                'official_execution_layers': {'chart_core': 'blocked'},
            },
            'raw_response': {
                'sections': {
                    'chart_core': {'Status': 'Fail', 'Payload': {'status': 'python_package_not_installed'}},
                },
            },
        },
    )

    assert packet['sections']['vedastro_official_raw_response']['status'] == 'received_unverified'
