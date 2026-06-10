"""Jaimini Chara Dasha (Variable Period) system.

Chara Dasha is the most important Jaimini dasha system. Dasha periods are
calculated from sign lords and follow Prakriti/Vikriti Chakra sequences.

Reference: Jaimini Sutramritam, Chapters I-II; Jyotish-Prasana
"""

from ..engine.time_utils import ZODIAC
from dataclasses import dataclass
from typing import List, Dict, Optional

# Sign lords (Graha lords of Rasis)
# Aries & Scorpio = Mars, Taurus & Libra = Venus, Gemini & Virgo = Mercury,
# Cancer = Moon, Leo = Sun, Sagittarius & Pisces = Jupiter,
# Capricorn & Aquarius = Saturn
SIGN_LORDS = {
    0: 'Ma', 1: 'Ve', 2: 'Me', 3: 'Mo', 4: 'Su',
    5: 'Me', 6: 'Ve', 7: 'Ma', 8: 'Ju', 9: 'Sa',
    10: 'Sa', 11: 'Ju'
}

# Lord to signs mapping
LORD_SIGNS = {}
for sign_idx, lord in SIGN_LORDS.items():
    if lord not in LORD_SIGNS:
        LORD_SIGNS[lord] = []
    LORD_SIGNS[lord].append(sign_idx)


@dataclass
class DashaPeriod:
    """A single dasha period."""
    sign_idx: int       # 0-11 zodiac sign index
    sign_name: str      # 'Aries', 'Taurus', etc.
    lord: str           # Planet lord of this sign
    years: float        # Duration in years
    start_date: float   # Julian day when this period starts
    end_date: float     # Julian day when this period ends
    sub_periods: List['DashaPeriod'] = None  # Antar/Bhukti sub-periods


def _sign_type(sign_idx):
    """Return sign type: 'odd' or 'even' (0-indexed: 0=Aries=odd)."""
    return 'odd' if sign_idx % 2 == 0 else 'even'


def _count_forward(sign_a, sign_b):
    """Count number of signs from sign_a to sign_b moving forward (inclusive of sign_a)."""
    if sign_b >= sign_a:
        return sign_b - sign_a + 1
    else:
        return (12 - sign_a) + sign_b + 1


def _count_backward(sign_a, sign_b):
    """Count number of signs from sign_a to sign_b moving backward."""
    if sign_b <= sign_a:
        return sign_a - sign_b + 1
    else:
        return sign_a + (12 - sign_b) + 1


def calc_dasha_years(sign_idx, planet_positions):
    """Calculate Chara Dasha years for a single sign.

    Based on the Jaimini formula:
    - Odd signs: count forward from sign to its lord's position
    - Even signs: count backward from sign to its lord's position
    - Maximum 12 years

    Args:
        sign_idx: Sign index (0-11)
        planet_positions: dict mapping planet name to dict with 'lon' key

    Returns:
        int: Dasha years (1-12)
    """
    lord = SIGN_LORDS[sign_idx]
    lord_lon = planet_positions[lord]['lon']
    lord_sign = int(lord_lon // 30)

    if _sign_type(sign_idx) == 'odd':
        years = _count_forward(sign_idx, lord_sign)
    else:
        years = _count_backward(sign_idx, lord_sign)

    return min(years, 12)


def calc_all_dasha_years(planet_positions):
    """Calculate Chara Dasha years for all 12 signs.

    Returns:
        list of (sign_idx, sign_name, lord, years)
    """
    results = []
    for i in range(12):
        years = calc_dasha_years(i, planet_positions)
        results.append({
            'sign_idx': i,
            'sign_name': ZODIAC[i],
            'lord': SIGN_LORDS[i],
            'years': years,
        })
    return results


def prakriti_chakra_order(start_sign):
    """Generate the Prakriti Chakra sign sequence starting from a given sign.

    Prakriti Chakra: odd signs count forward, even signs count backward.
    This determines the dasha sequence order (Prakriti version).

    Args:
        start_sign: Starting sign index (0-11)

    Yields:
        sign indices in Prakriti Chakra order
    """
    current = start_sign
    visited = set()
    direction = 1 if _sign_type(current) == 'odd' else -1

    while len(visited) < 12:
        if current not in visited:
            visited.add(current)
            yield current

        # When we reach the last unvisited sign in current direction,
        # switch direction
        next_sign = (current + direction) % 12
        if next_sign in visited:
            # Find the next unvisited sign
            for s in range(12):
                if s not in visited:
                    current = s
                    direction = 1 if _sign_type(current) == 'odd' else -1
                    break
        else:
            current = next_sign


def vikriti_chakra_order(start_sign):
    """Generate the Vikriti Chakra sign sequence.

    Vikriti Chakra: reverse of Prakriti - odd signs count backward, even forward.
    """
    current = start_sign
    visited = set()
    direction = -1 if _sign_type(current) == 'odd' else 1

    while len(visited) < 12:
        if current not in visited:
            visited.add(current)
            yield current

        next_sign = (current + direction) % 12
        if next_sign in visited:
            for s in range(12):
                if s not in visited:
                    current = s
                    direction = -1 if _sign_type(current) == 'odd' else 1
                    break
        else:
            current = next_sign


def udaya_chakra_order(start_sign):
    """Generate the Udaya Chakra sign sequence.

    Udaya Chakra: always forward regardless of sign type.
    """
    for i in range(12):
        yield (start_sign + i) % 12


def calc_chara_dasha(birth_jd, houses, planet_positions, chakra='prakriti', start_house=9):
    """Calculate the full Chara Dasha timeline from birth.

    Args:
        birth_jd: Julian Day of birth
        houses: List of house dicts from calc_houses()
        planet_positions: Dict of planet positions from get_all_planets()
        chakra: 'prakriti', 'vikriti', or 'udaya' - the counting system
        start_house: Which house determines the starting sign (default: 9th)

    Returns:
        list of DashaPeriod objects, each containing sub_periods
    """
    # Find the starting sign: sign occupied by lord of start_house
    start_house_idx = start_house - 1
    start_house_sign = houses[start_house_idx]['sign_idx']
    start_house_lord = SIGN_LORDS[start_house_sign]
    lord_lon = planet_positions[start_house_lord]['lon']
    start_sign = int(lord_lon // 30)

    # Calculate dasha years for all signs
    all_years = calc_all_dasha_years(planet_positions)
    years_map = {d['sign_idx']: d['years'] for d in all_years}

    # Generate sign sequence
    if chakra == 'prakriti':
        sequence = list(prakriti_chakra_order(start_sign))
    elif chakra == 'vikriti':
        sequence = list(vikriti_chakra_order(start_sign))
    elif chakra == 'udaya':
        sequence = list(udaya_chakra_order(start_sign))
    else:
        raise ValueError(f"Unknown chakra: {chakra}")

    # Generate Mahadasha periods
    current_jd = birth_jd
    dasha_periods = []

    for sign_idx in sequence:
        years = years_map[sign_idx]
        info = all_years[sign_idx]
        end_jd = current_jd + years * 365.25  # Approximate

        period = DashaPeriod(
            sign_idx=sign_idx,
            sign_name=info['sign_name'],
            lord=info['lord'],
            years=years,
            start_date=current_jd,
            end_date=end_jd,
        )

        # Generate Antar (Bhukti) sub-periods
        sub_periods = _calc_antar_dasha(
            sign_idx, years, current_jd, end_jd,
            sequence, years_map, all_years
        )
        period.sub_periods = sub_periods

        dasha_periods.append(period)
        current_jd = end_jd

    return dasha_periods


def _calc_antar_dasha(maha_sign, maha_years, maha_start, maha_end, sequence, years_map, all_years):
    """Calculate Antar/Bhukti sub-periods within a Mahadasha.

    Sub-periods are proportional to each sign's dasha years.
    """
    total_years = sum(years_map[s] for s in sequence)
    sub_periods = []

    # Sub-periods start from the Mahadasha sign, following the same sequence
    maha_pos = sequence.index(maha_sign)
    sub_sequence = sequence[maha_pos:] + sequence[:maha_pos]

    current_start = maha_start

    for sign_idx in sub_sequence:
        sub_years = (years_map[sign_idx] / total_years) * maha_years
        sub_end = current_start + sub_years * 365.25

        info = all_years[sign_idx]
        sp = DashaPeriod(
            sign_idx=sign_idx,
            sign_name=info['sign_name'],
            lord=info['lord'],
            years=sub_years,
            start_date=current_start,
            end_date=sub_end,
        )
        sub_periods.append(sp)
        current_start = sub_end

    return sub_periods


def format_dasha_table(dasha_periods, include_antar=True):
    """Format Chara Dasha periods as a readable text table.

    Args:
        dasha_periods: result from calc_chara_dasha()
        include_antar: whether to include Antar sub-periods

    Returns:
        str: Formatted dasha table
    """
    lines = []
    lines.append("=" * 80)
    lines.append("CHARA DASHA (Jaimini System, Tropical Zodiac, Prakriti Chakra)")
    lines.append("=" * 80)
    lines.append(f"{'Mahadasha':<16}{'Lord':<8}{'Years':<8}{'Start (JD)':<15}{'End (JD)':<15}")
    lines.append("-" * 80)

    for period in dasha_periods:
        lines.append(
            f"{period.sign_name:<16}"
            f"{period.lord:<8}"
            f"{period.years:<8.2f}"
            f"{period.start_date:<15.2f}"
            f"{period.end_date:<15.2f}"
        )

        if include_antar and period.sub_periods:
            lines.append(f"  {'─' * 70}")
            lines.append(f"  {'Antar (Bhukti) sub-periods:':<30}")
            for sp in period.sub_periods:
                # Calculate relative portion
                portion = sp.years / period.years * 100
                lines.append(
                    f"    {sp.sign_name:<14}"
                    f"{sp.lord:<8}"
                    f"{sp.years:<8.3f}"
                    f"({portion:5.1f}%)"
                )
            lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)


def get_current_dasha(dasha_periods, jd):
    """Get the current active Mahadasha and Antar for a given Julian Day.

    Args:
        dasha_periods: result from calc_chara_dasha()
        jd: Julian Day to query

    Returns:
        tuple of (mahadasha, antar) where each is a DashaPeriod or None
    """
    for period in dasha_periods:
        if period.start_date <= jd < period.end_date:
            if period.sub_periods:
                for sp in period.sub_periods:
                    if sp.start_date <= jd < sp.end_date:
                        return period, sp
            return period, None
    return None, None
