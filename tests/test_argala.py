#!/usr/bin/env python3
"""Tests for argala.py — Primary Argala, Virodha Argala, special cases."""

from __future__ import annotations
import sys, os, pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), '..', 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from argala import (
    calc_argala, calc_argala_for_reference, classify_argala_rajayoga,
    PRIMARY_ARGALA, VIRODHARGALA_MAP, SECONDARY_ARGALA,
    NATURAL_MALEFICS, SIGNS,
)

# ── Primary Argala Tests ───────────────────────────────────────────

class TestPrimaryArgala:
    def test_2_4_11_are_primary(self):
        assert PRIMARY_ARGALA == {2, 4, 11}

    def test_virodha_map_correct(self):
        assert VIRODHARGALA_MAP == {2: 12, 4: 10, 11: 3}

    def test_secondary_are_5_9(self):
        assert SECONDARY_ARGALA == {5, 9}

    def test_argala_for_reference_structure(self):
        psi = {'Sun': 0, 'Moon': 3, 'Mars': 6, 'Mercury': 9}
        result = calc_argala_for_reference(0, psi)
        assert 'primary' in result
        assert 'specific' in result
        assert 'secondary' in result
        assert result['ref_sign_idx'] == 0

    def test_planets_in_2nd_house_form_argala(self):
        # Sun at Aries(0), reference Aries(0) → 2nd house is Taurus(1)
        # Put Moon in Taurus → H2 Argala
        psi = {'Moon': 1}  # Moon in Taurus
        result = calc_argala_for_reference(0, psi)
        assert len(result['primary']['H2']['planets']) > 0
        assert 'Moon' in result['primary']['H2']['planets']

    def test_no_planets_no_argala(self):
        psi = {'Sun': 5}  # Far from reference
        result = calc_argala_for_reference(0, psi)
        assert result['argala_count'] == 0


# ── Virodha Argala Tests ───────────────────────────────────────────

class TestVirodhaArgala:
    def test_blockers_in_12th_block_2nd(self):
        # Reference: Aries(0). 2nd house = Taurus(1), 12th house = Pisces(11)
        psi = {'Moon': 1, 'Mars': 11}  # Moon in 2nd, Mars in 12th
        result = calc_argala_for_reference(0, psi)
        assert len(result['primary']['H2']['blockers']) > 0

    def test_more_blockers_than_argala_not_effective(self):
        # 1 planet in H2, 2 planets in H12 → not effective
        psi = {'Moon': 1, 'Mars': 11, 'Saturn': 11}
        result = calc_argala_for_reference(0, psi)
        assert result['primary']['H2']['effective'] == False

    def test_more_argala_than_blockers_effective(self):
        psi = {'Moon': 1, 'Venus': 1, 'Mars': 11}
        result = calc_argala_for_reference(0, psi)
        assert result['primary']['H2']['effective'] == True


# ── Special Cases Tests ────────────────────────────────────────────

class TestSpecialArgala:
    def test_3rd_house_two_malefics_special_argala(self):
        # 3rd from Aries(0) = Gemini(2). Put Mars and Sun in Gemini
        psi = {'Mars': 2, 'Sun': 2}
        result = calc_argala_for_reference(0, psi)
        assert result['specific']['effective'] == True

    def test_3rd_house_one_malefic_no_special(self):
        psi = {'Mars': 2}
        result = calc_argala_for_reference(0, psi)
        assert result['specific']['effective'] == False

    def test_3rd_house_benefics_no_special(self):
        psi = {'Jupiter': 2, 'Venus': 2}
        result = calc_argala_for_reference(0, psi)
        assert result['specific']['effective'] == False


# ── Secondary Argala Tests ─────────────────────────────────────────

class TestSecondaryArgala:
    def test_secondary_5_9_present(self):
        psi = {'Jupiter': 4}  # Leo, 5th from Aries
        result = calc_argala_for_reference(0, psi)
        assert 'H5' in result['secondary']
        assert 'H9' in result['secondary']

    def test_secondary_planets_listed(self):
        psi = {'Jupiter': 4}  # 5th from Aries
        result = calc_argala_for_reference(0, psi)
        assert 'Jupiter' in result['secondary']['H5']['planets']


# ── Net Result Tests ───────────────────────────────────────────────

class TestNetResult:
    def test_supported_when_more_argala(self):
        psi = {'Moon': 1, 'Venus': 3, 'Jupiter': 10}  # 2nd, 4th, 11th occupied
        result = calc_argala_for_reference(0, psi)
        assert result['net_result'] == 'supported'

    def test_obstructed_when_more_virodha(self):
        psi = {'Mars': 11, 'Saturn': 9}  # 12th and 10th occupied → virodha
        result = calc_argala_for_reference(0, psi)
        assert result['net_result'] in ('obstructed', 'neutral')

    def test_neutral_when_balanced(self):
        psi = {}  # No planets
        result = calc_argala_for_reference(0, psi)
        assert result['net_result'] == 'neutral'


# ── Rajayoga Classification Tests ───────────────────────────────────

class TestRajayogaClassification:
    def test_poornargala_all_3(self):
        # Mock result with all 3 primary Argala occupied
        mock = {'primary': {
            'H2': {'planets': ['Moon'], 'blockers': []},
            'H4': {'planets': ['Venus'], 'blockers': []},
            'H11': {'planets': ['Jupiter'], 'blockers': []},
        }}
        result = classify_argala_rajayoga(mock)
        assert result['type'] == 'Poornargala'
        assert result['level'] == 4

    def test_tripadargala_2(self):
        mock = {'primary': {
            'H2': {'planets': ['Moon'], 'blockers': []},
            'H4': {'planets': [], 'blockers': []},
            'H11': {'planets': ['Jupiter'], 'blockers': []},
        }}
        result = classify_argala_rajayoga(mock)
        assert result['type'] == 'Tripadargala'

    def test_ardhargala_1(self):
        mock = {'primary': {
            'H2': {'planets': ['Moon'], 'blockers': []},
            'H4': {'planets': [], 'blockers': []},
            'H11': {'planets': [], 'blockers': []},
        }}
        result = classify_argala_rajayoga(mock)
        assert result['type'] == 'Ardhargala'

    def test_none_no_argala(self):
        mock = {'primary': {
            'H2': {'planets': [], 'blockers': []},
            'H4': {'planets': [], 'blockers': []},
            'H11': {'planets': [], 'blockers': []},
        }}
        result = classify_argala_rajayoga(mock)
        assert result['type'] == 'None'
        assert result['level'] == 0


# ── Full Chart Argala Tests ────────────────────────────────────────

class TestFullChartArgala:
    def test_calc_argala_returns_all_houses(self):
        psi = {'Sun': 0, 'Moon': 3, 'Mars': 6, 'Mercury': 9}
        result = calc_argala(psi, 0)
        assert len(result['houses']) == 12

    def test_calc_argala_has_summary(self):
        psi = {'Sun': 0, 'Moon': 3}
        result = calc_argala(psi, 0)
        assert 'summary' in result
        assert 'supported_count' in result['summary']

    def test_calc_argala_planet_refs(self):
        psi = {'Sun': 0, 'Moon': 3}
        result = calc_argala(psi, 0)
        assert 'planets' in result
        assert 'Sun' in result['planets']

    def test_include_nodes_flag(self):
        psi = {'Sun': 0, 'Rahu': 5, 'Ketu': 11}
        result_with = calc_argala(psi, 0, include_nodes=True)
        result_without = calc_argala(psi, 0, include_nodes=False)
        assert result_with['include_nodes'] == True
        assert result_without['include_nodes'] == False
