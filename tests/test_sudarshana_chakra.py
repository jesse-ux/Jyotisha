#!/usr/bin/env python3
"""Tests for sudarshana_chakra.py — three reference charts and convergence analysis."""

from __future__ import annotations
import os
import sys

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from sudarshana_chakra import SudarshanaChakraAnalyzer, calc_sudarshana_chakra, generate_sudarshana_report


def sample_planets():
    return {
        'Sun': 65.0,       # Gemini
        'Moon': 125.0,     # Leo
        'Mars': 280.0,     # Capricorn
        'Mercury': 75.0,   # Gemini
        'Jupiter': 100.0,  # Cancer
        'Venus': 340.0,    # Pisces
        'Saturn': 310.0,   # Aquarius
        'Rahu': 210.0,     # Scorpio
        'Ketu': 30.0,      # Taurus
    }


def test_generate_three_charts_has_all_reference_points():
    analyzer = SudarshanaChakraAnalyzer()
    charts = analyzer.generate_three_charts(sample_planets(), asc_lon=10.0)
    assert set(charts) == {'ascendant_lagna', 'moon_lagna', 'sun_lagna'}
    for chart in charts.values():
        assert 'Sun' in chart
        assert 'Moon' in chart
        assert 1 <= chart['Sun']['house'] <= 12
        assert 0 <= chart['Sun']['sign_idx'] <= 11


def test_house_from_refs_wraps_one_to_twelve():
    assert SudarshanaChakraAnalyzer._house_from_refs(0, 0) == 1
    assert SudarshanaChakraAnalyzer._house_from_refs(1, 0) == 2
    assert SudarshanaChakraAnalyzer._house_from_refs(11, 0) == 12
    assert SudarshanaChakraAnalyzer._house_from_refs(0, 11) == 2


def test_composite_analysis_scores_range():
    analyzer = SudarshanaChakraAnalyzer()
    result = analyzer.composite_analysis(sample_planets(), asc_lon=10.0)
    assert set(result).issuperset({'Sun', 'Moon', 'Mars'})
    for pdata in result.values():
        assert 0 <= pdata['composite_score'] <= 1
        assert pdata['favorable_count'] + pdata['unfavorable_count'] == 3
        assert 'interpretation' in pdata


def test_house_analysis_specific_house():
    analyzer = SudarshanaChakraAnalyzer()
    result = analyzer.house_analysis(sample_planets(), asc_lon=10.0, house_number=10)
    assert result['house'] == 10
    assert 'asc_lagna' in result
    assert 'moon_lagna' in result
    assert 'sun_lagna' in result
    assert 'interpretation' in result


def test_house_analysis_rejects_invalid_house():
    analyzer = SudarshanaChakraAnalyzer()
    result = analyzer.house_analysis(sample_planets(), asc_lon=10.0, house_number=13)
    assert 'error' in result


def test_life_area_analysis_has_core_areas():
    analyzer = SudarshanaChakraAnalyzer()
    result = analyzer.life_area_analysis(sample_planets(), asc_lon=10.0)
    for key in ('自我/健康', '财富/家庭', '婚姻/伴侣/合作', '事业/地位/名声', '收益/愿望/朋友圈'):
        assert key in result
        assert 'composite_strength' in result[key]


def test_full_sudarshana_result_structure():
    result = calc_sudarshana_chakra(sample_planets(), asc_lon=10.0, house=7)
    assert result['version'] == '2.0'
    assert 'reference_points' in result
    assert 'three_charts' in result
    assert 'composite_analysis' in result
    assert 'life_area_analysis' in result
    assert 'specific_house' in result
    assert 'convergence' in result
    assert 'overall_assessment' in result


def test_text_report_contains_title():
    report = generate_sudarshana_report(sample_planets(), asc_lon=10.0)
    assert isinstance(report, str)
    assert 'Sudarshana' in report or '苏达沙那' in report
