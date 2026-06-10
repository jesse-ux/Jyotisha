"""Chart data structure — integrates planetary positions, houses, and Jaimini analysis."""

from datetime import datetime

from ..engine.ephemeris import get_all_planets, get_rahu_ketu
from ..engine.houses import calc_houses, calc_ascendant, WHOLE_SIGN, HOUSE_SYSTEMS
from ..engine.time_utils import parse_dms, format_dms, zodiac_position, local_to_utc, parse_timezone, ZODIAC, ZODIAC_FULL
from ..core.karakas import calc_chara_karakas, karaka_report
from ..core.dashas import calc_chara_dasha, format_dasha_table, calc_all_dasha_years
from ..core.padas import calc_all_padas, calc_upapada, pada_report
from ..core.lagnas import calc_all_special_lagnas, lagna_report
from ..core.divisions import calc_all_divisions, division_report
from ..core.argala import calc_all_argalas, argala_report, classify_argala_rajayoga, calc_karakamsa_rajayoga
from ..panchanga.panchanga import calc_panchanga, format_panchanga


class Chart:
    """A Jaimini astrological chart with tropical zodiac."""

    def __init__(self, year, month, day, hour, minute, second,
                 lat, lon, tz_offset=0.0, name="", house_system='W'):
        """
        Args:
            year, month, day: Local date
            hour, minute, second: Local time
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees (East positive)
            tz_offset: Timezone offset from UTC in hours (e.g., +8 for CST)
            name: Optional chart name/label
            house_system: 'W' = Whole Sign, 'P' = Placidus, 'E' = Equal
        """
        self.name = name
        self.house_system = house_system

        # Convert to UTC
        utc_dt = local_to_utc(year, month, day, hour, minute, second, tz_offset)

        self.utc_year = utc_dt.year
        self.utc_month = utc_dt.month
        self.utc_day = utc_dt.day
        self.utc_hour = utc_dt.hour
        self.utc_minute = utc_dt.minute
        self.utc_second = utc_dt.second + (utc_dt.microsecond / 1_000_000)

        self.lat = lat
        self.lon = lon
        self.tz_offset = tz_offset

        # Compute positions
        self.planets = get_all_planets(
            self.utc_year, self.utc_month, self.utc_day,
            self.utc_hour, self.utc_minute, self.utc_second
        )

        self.ascendant = calc_ascendant(
            self.utc_year, self.utc_month, self.utc_day,
            self.utc_hour, self.utc_minute, self.utc_second,
            lat, lon
        )

        self.houses = calc_houses(
            self.utc_year, self.utc_month, self.utc_day,
            self.utc_hour, self.utc_minute, self.utc_second,
            lat, lon, system=house_system
        )

        # Panchanga (five limbs of Vedic timekeeping)
        local_dt = datetime(year, month, day, hour, minute, second)
        self.panchanga = calc_panchanga(
            self.planets['Su']['lon'],
            self.planets['Mo']['lon'],
            local_dt.weekday()
        )

        # Jaimini analysis
        self.karakas_7 = calc_chara_karakas(self.planets, include_rahu=False)
        self.karakas_8 = calc_chara_karakas(self.planets, include_rahu=True)

        self.dasha_years = calc_all_dasha_years(self.planets)
        self.chara_dasha = calc_chara_dasha(
            0,  # Will be computed by the engine
            self.houses, self.planets, chakra='prakriti'
        )

        # Compute birth Julian Day for dasha
        from ..engine.ephemeris import julian_day
        self.birth_jd = julian_day(
            self.utc_year, self.utc_month, self.utc_day,
            self.utc_hour, self.utc_minute, self.utc_second
        )

        # Recompute dasha with correct birth_jd
        self.chara_dasha = calc_chara_dasha(
            self.birth_jd, self.houses, self.planets, chakra='prakriti'
        )

        # Layer 2: Arudha Padas
        self.asc_sign_idx = int(self.ascendant // 30)
        self.padas = calc_all_padas(self.asc_sign_idx, self.planets)
        self.upapada = calc_upapada(self.asc_sign_idx, self.planets)

        # Layer 3: Special Lagnas (HL, GL, VL)
        self.special_lagnas = calc_all_special_lagnas(
            year, month, day, hour, minute, second,
            lat, lon, self.asc_sign_idx, tz_offset
        )

        # Layer 4: Divisional charts (D-3, D-9, D-12)
        self.divisions = calc_all_divisions(self.planets, self.ascendant)

        # Argala analysis (Jaimini judgment system)
        self.argalas = calc_all_argalas(self.houses, self.planets)

        # Argala Rajayoga for Ascendant (most important reference point)
        self.lagna_rajayoga = classify_argala_rajayoga(
            self.argalas[1]  # House 1 = Ascendant
        )

        # Karakamsa Rajayoga
        ak = self.karakas_7[0]  # Atmakaraka is always first
        self.karakamsa_rajayoga = calc_karakamsa_rajayoga(
            ak['planet'], ak['lon'],
            self.divisions, self.planets
        )

    @classmethod
    def from_iso(cls, dt_str, tz_str, lat, lon, name="", house_system='W'):
        """Create chart from ISO datetime string and timezone string.

        Example:
            Chart.from_iso('1949-10-01 15:00:00', '+8', '39°54′25″', '116°23′50″')
        """
        from datetime import datetime
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        lat_deg = parse_dms(lat)
        lon_deg = parse_dms(lon)
        tz = parse_timezone(tz_str)
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second,
                   lat_deg, lon_deg, tz, name=name, house_system=house_system)

    def asc_sign(self):
        """Return the ascendant sign index (0-11) and name."""
        idx = int(self.ascendant // 30)
        return idx, ZODIAC[idx]

    def to_dict(self):
        """Serialize chart data to a JSON-compatible dictionary for API responses."""
        # Planets
        planets_dict = {}
        for name, pos in self.planets.items():
            planets_dict[name] = {
                "lon": pos["lon"],
                "lat": pos.get("lat", 0.0),
                "speed": pos.get("speed", 0.0),
                "retrograde": pos.get("retrograde", False),
                "sign_idx": pos["sign_idx"],
                "sign": pos["sign"],
                "sign_deg": pos.get("sign_deg", pos["lon"] % 30),
                "sign_str": pos["sign_str"],
            }

        # Houses
        houses_list = []
        for h in self.houses:
            planets_in_h = self.planets_in_house(h["house"])
            houses_list.append({
                "house": h["house"],
                "cusp": h["cusp"],
                "sign_idx": h["sign_idx"],
                "sign": h["sign"],
                "sign_deg": h["sign_deg"],
                "sign_str": h["sign_str"],
                "planets": planets_in_h,
            })

        # Karakas
        karakas_7_list = []
        for k in self.karakas_7:
            karakas_7_list.append({
                "planet": k["planet"],
                "karaka": k["karaka"],
                "karaka_full": k["karaka_full"],
                "degree_in_sign": k["degree_in_sign"],
                "sign": k["sign"],
                "sign_idx": k["sign_idx"],
                "lon": k["lon"],
                "rank": k["rank"],
            })

        # Dasha years
        dasha_years_list = []
        for d in self.dasha_years:
            dasha_years_list.append({
                "sign_idx": d["sign_idx"],
                "sign_name": d["sign_name"],
                "lord": d["lord"],
                "years": d["years"],
            })

        # Chara Dasha periods (all 12 mahadashas with full antars)
        dasha_periods = []
        for p in self.chara_dasha:
            antars = []
            if hasattr(p, "sub_periods") and p.sub_periods:
                for a in p.sub_periods:
                    antars.append({
                        "sign_idx": a.sign_idx,
                        "sign_name": a.sign_name,
                        "lord": a.lord,
                        "years": round(a.years, 3),
                    })
            dasha_periods.append({
                "sign_idx": p.sign_idx,
                "sign_name": p.sign_name,
                "lord": p.lord,
                "years": p.years,
                "start_jd": p.start_date,
                "end_jd": p.end_date,
                "antar": antars,
            })

        # Padas
        padas_dict = {}
        for h_num, pada in self.padas.items():
            padas_dict[str(h_num)] = {
                "house": h_num,
                "name": pada.get("name", ""),
                "sign_idx": pada["sign_idx"],
                "sign": pada["sign"],
                "sign_full": pada.get("sign_full", pada["sign"]),
                "lord": pada["lord"],
            }

        # Upapada
        upapada_dict = {
            "sign_idx": self.upapada["sign_idx"],
            "sign": self.upapada["sign"],
            "sign_full": self.upapada["sign_full"],
            "lord": self.upapada["lord"],
            "description": self.upapada.get("description", ""),
        }

        # Special lagnas
        lagnas_dict = {}
        for name, lagna in self.special_lagnas.items():
            if isinstance(lagna, dict) and "sign_idx" in lagna and "sign" in lagna:
                lagnas_dict[name] = {
                    "sign_idx": lagna["sign_idx"],
                    "sign": lagna["sign"],
                    "sign_full": lagna.get("sign_full", lagna["sign"]),
                    "lord": lagna.get("lord", ""),
                }
            else:
                lagnas_dict[name] = lagna

        # Divisions
        divisions_dict = {}
        for div_name, div_data in self.divisions.items():
            div_planets = {}
            for p_name, p_data in div_data.items():
                div_planets[p_name] = {
                    "sign_idx": p_data["sign_idx"],
                    "sign": p_data["sign"],
                }
            divisions_dict[div_name] = div_planets

        # Argalas (full detail)
        argalas_full = {}
        for h_num, arg in self.argalas.items():
            primary = {}
            for key in ["H2", "H4", "H11"]:
                if key in arg.get("primary", {}):
                    p = arg["primary"][key]
                    primary[key] = {
                        "planet": p.get("planet", ""),
                        "house": p.get("house", 0),
                    }
            virodh = {}
            for key in ["H12", "H10", "H3"]:
                if key in arg.get("virodhargala", {}):
                    v = arg["virodhargala"][key]
                    virodh[key] = {
                        "planet": v.get("planet", ""),
                        "house": v.get("house", 0),
                    }
            secondary = {}
            for key in ["H5", "H9"]:
                if key in arg.get("secondary", {}):
                    s = arg["secondary"][key]
                    secondary[key] = {
                        "planet": s.get("planet", ""),
                        "house": s.get("house", 0),
                    }
            argalas_full[str(h_num)] = {
                "ref_sign": arg.get("ref_sign", ""),
                "primary": primary,
                "secondary": secondary,
                "specific": arg.get("specific", {}),
                "virodhargala": virodh,
                "argala_count": arg.get("argala_count", 0),
                "virodhargala_count": arg.get("virodhargala_count", 0),
                "net_result": arg.get("net_result", "neutral"),
            }

        # Ascendant
        asc_sign_idx = int(self.ascendant // 30)
        asc_sign_deg = self.ascendant % 30

        return {
            "algorithm": {
                "engine": "Jaimini Tropical Astrology Engine",
                "version": "1.0.0",
                "tradition": "Jaimini (Jyotish-Prasana, Jaimini Sutramritam)",
                "zodiac": "Tropical (Sayana) — no Ayanamsa applied",
                "house_system": HOUSE_SYSTEMS.get(self.house_system, self.house_system),
                "ephemeris": "NASA JPL DE421 (Skyfield) — precision ~0.001 arcsec",
                "karaka_system": "7-planet Chara Karaka (Rangacharya system, excluding Rahu)",
                "dasha_system": "Jaimini Chara Dasha (Prakriti Chakra, sign-based, 9th-house start)",
                "pada_system": "Jaimini Arudha Padas (with exception rule: pada in 1st/7th → shift to 10th)",
                "division_system": "Jaimini Varga (D-9 Navamsa, D-3 Drekkana, D-12 Dwadashamsha) — 阳顺阴逆",
                "argala_system": "Jaimini Argala/Virodhargala (houses 2/4/11 primary, 12/10/3 obstruction)",
                "note": "纯 Jaimini 回归黄道体系，不含 Parashara 内容 (无 Vimshottari, 无 Shadbala, 无行星相位, 无不等宫制)",
            },
            "input": {
                "date": f"{self.utc_year:04d}-{self.utc_month:02d}-{self.utc_day:02d}",
                "time": f"{self.utc_hour:02d}:{self.utc_minute:02d}:{self.utc_second:06.3f}",
                "tz": self.tz_offset,
                "lat": self.lat,
                "lon": self.lon,
                "name": self.name,
                "house_system": self.house_system,
            },
            "ascendant": {
                "lon": self.ascendant,
                "sign_idx": asc_sign_idx,
                "sign": ZODIAC[asc_sign_idx],
                "sign_deg": asc_sign_deg,
                "sign_str": f"{ZODIAC[asc_sign_idx]} {asc_sign_deg:.2f}°",
            },
            "planets": planets_dict,
            "houses": houses_list,
            "panchanga": self.panchanga,
            "karakas_7": karakas_7_list,
            "dasha_years": dasha_years_list,
            "chara_dasha": dasha_periods,
            "padas": padas_dict,
            "upapada": upapada_dict,
            "special_lagnas": lagnas_dict,
            "divisions": divisions_dict,
            "argalas": argalas_full,
            "lagna_rajayoga": self.lagna_rajayoga,
            "karakamsa_rajayoga": {
                "karakamsa_sign": self.karakamsa_rajayoga["karakamsa_sign"],
                "ak_planet": self.karakamsa_rajayoga["ak_planet"],
                "is_rajayoga": self.karakamsa_rajayoga["is_rajayoga"],
                "yoga_level": self.karakamsa_rajayoga["yoga_level"],
                "description": self.karakamsa_rajayoga["description"],
            },
        }

    def planets_in_house(self, house_num):
        """Return list of planets in a given house (1-12)."""
        h = self.houses[house_num - 1]
        result = []
        for name, pos in self.planets.items():
            lon = pos['lon']
            sign_idx = int(lon // 30)
            if sign_idx == h['sign_idx']:
                result.append(name)
        return result

    def planet_house(self, planet_name):
        """Return the house number (1-12) where a planet is located."""
        if planet_name not in self.planets:
            return None
        lon = self.planets[planet_name]['lon']
        sign_idx = int(lon // 30)
        for h in self.houses:
            if h['sign_idx'] == sign_idx:
                return h['house']
        return 1

    def summary(self):
        """Generate a comprehensive text summary of the chart."""
        lines = []

        # Header
        asc_sign_idx, asc_name = self.asc_sign()
        asc_str = zodiac_position(self.ascendant)[2]
        lines.append("=" * 70)
        lines.append(f"JAIMINI ASTROLOGY CHART (Tropical Zodiac)")
        lines.append(f"{self.name}" if self.name else "Chart Summary")
        lines.append("=" * 70)
        lines.append(f"Ascendant: {asc_str}  |  House System: {HOUSE_SYSTEMS.get(self.house_system, self.house_system)}")
        lines.append("")

        # Panchanga
        lines.append("-" * 70)
        lines.append("PANCHANGA (五支历法)")
        lines.append("-" * 70)
        lines.append(format_panchanga(self.panchanga))
        lines.append("")

        # Planetary Positions
        lines.append("-" * 70)
        lines.append(f"{'Planet':<12}{'Longitude':<24}{'Sign':<8}{'House':<8}{'Speed(°/d)':<12}{'Retro'}")
        lines.append("-" * 70)

        planet_order = ['Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa', 'Ra', 'Ke', 'Ur', 'Ne', 'Pl']
        for p in planet_order:
            if p not in self.planets:
                continue
            pos = self.planets[p]
            house = self.planet_house(p)
            speed_str = f"{pos['speed']:.4f}"
            retro = 'R' if pos.get('retrograde') else ''
            lines.append(
                f"{p:<12}"
                f"{pos['sign_str']:<24}"
                f"{pos['sign']:<8}"
                f"{house:<8}"
                f"{speed_str:<12}"
                f"{retro}"
            )

        # Houses (Whole Sign cusps)
        lines.append("")
        lines.append("-" * 70)
        lines.append("HOUSE CUSPS (Whole Sign)")
        lines.append("-" * 70)
        for h in self.houses:
            planets = self.planets_in_house(h['house'])
            planets_str = ', '.join(planets) if planets else '—'
            lines.append(f"House {h['house']:2d}: {h['sign']:<5} | Planets: {planets_str}")

        # Karakas
        lines.append("")
        lines.append(karaka_report(self.karakas_7))

        # Arudha Padas
        lines.append("")
        lines.append(pada_report(self.padas))
        if self.upapada:
            lines.append(f"\n  Upapada (UL): {self.upapada['sign_full']} "
                         f"(lord: {self.upapada['lord']})")
            lines.append(f"  {self.upapada['description']}")

        # Special Lagnas
        lines.append("")
        lines.append(lagna_report(self.special_lagnas))

        # Divisional Charts
        lines.append("")
        lines.append(division_report(self.divisions, 'D9'))
        lines.append("")
        lines.append(division_report(self.divisions, 'D3'))

        # Argala Analysis
        lines.append("")
        lines.append(argala_report(self.argalas))

        # Rajayoga Summary
        lines.append("")
        lines.append("=" * 60)
        lines.append("RAJAYOGA SUMMARY")
        lines.append("=" * 60)
        lines.append(f"  Lagna Argala Rajayoga: {self.lagna_rajayoga['type']} — {self.lagna_rajayoga['desc']}")
        kr = self.karakamsa_rajayoga
        lines.append(f"  Karakamsa Rajayoga: {'YES' if kr['is_rajayoga'] else 'No'} (level {kr['yoga_level']})")
        lines.append(f"    Karakamsa Sign: {kr['karakamsa_sign']} | AK ({kr['ak_planet']}) own Navamsa: {kr['ak_in_own_navamsa']}")
        lines.append(f"    {kr['description']}")

        # Dasha Years Summary
        lines.append("")
        lines.append("-" * 70)
        lines.append("DASHA YEARS (All Signs)")
        lines.append("-" * 70)
        for d in self.dasha_years:
            lines.append(f"  {d['sign_name']:<8} ({d['lord']}): {d['years']} years")

        # Chara Dasha Timeline
        lines.append("")
        lines.append(format_dasha_table(self.chara_dasha, include_antar=True))

        return "\n".join(lines)
