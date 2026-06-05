#!/usr/bin/env python3
"""用PyJhora计算单张星盘的Yoga列表 - 被build_standard_test_charts.py调用"""
import sys, json, datetime, io

# 抑制PyJhora的所有输出（stdout + stderr + logging）
class SuppressAll:
    def __enter__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        return self
    def __exit__(self, *a):
        sys.stdout = self._stdout
        sys.stderr = self._stderr

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

try:
    with SuppressAll():
        from jhora.horoscope.chart import yoga as yoga_mod
        from jhora.panchanga import drik
        from jhora.panchanga.drik import Place
        import jhora.utils as utils
    PYJHORA_OK = True
except Exception as e:
    PYJHORA_OK = False
    IMPORT_ERR = str(e)

def tz_to_float(tz_str):
    """将 +05:30 格式转为 5.5 小时浮点数"""
    tz_str = tz_str.strip()
    sign = -1 if tz_str.startswith('-') else 1
    tz_str = tz_str.lstrip('+-')
    parts = tz_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1]) if len(parts) > 1 else 0
    return sign * (hours + minutes / 60.0)

def _planet_dict_from_pyjhora_positions(positions, asc_sign):
    """Convert PyJHora planet positions to the skill validation schema."""
    names = {
        0: "Sun",
        1: "Moon",
        2: "Mars",
        3: "Mercury",
        4: "Jupiter",
        5: "Venus",
        6: "Saturn",
        7: "Rahu",
        8: "Ketu",
    }
    out = {}
    for pid, (sign_idx, degree) in positions:
        if pid not in names:
            continue
        out[names[pid]] = {
            "sign": SIGNS[sign_idx],
            "house": ((sign_idx - asc_sign) % 12) + 1,
            "degree": degree,
        }
    return out


def _upagraha_payload(name, longitude_pair, asc_sign):
    sign_idx, degree = longitude_pair
    return {
        "name": name,
        "sign": SIGNS[sign_idx],
        "house": ((sign_idx - asc_sign) % 12) + 1,
        "degree": degree,
    }


def compute_yogas(chart):
    """计算给定星盘的所有Yoga，并输出 D1/D9/tithi/Gulika 验证上下文。"""
    if not PYJHORA_OK:
        return {"error": f"PyJhora import failed: {IMPORT_ERR}"}
    try:
        with SuppressAll():
            # 构造Place对象（timezone是浮点数小时）
            tz = tz_to_float(chart["tz"])
            place = Place(chart["city"], chart["lat"], chart["lon"], tz)

            # 构造datetime并转JD
            date_str = chart["date"] + " " + chart["time"]
            if date_str.count(':') == 1:
                date_str += ":00"
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            jd = utils.gregorian_to_jd(dt)
            dob = drik.Date(dt.year, dt.month, dt.day)
            tob = (dt.hour, dt.minute, dt.second)

            # 计算 D1/Rasi Yoga。v2 逻辑正确性验证必须与 Skill 的 D1 Yoga 引擎逐层对齐；
            # 不能使用 get_yoga_details_for_all_charts()，否则会把 D2/D9/D10 等分盘 Yoga 混入，
            # 造成大量“Skill 漏检”的假阴性。
            result = yoga_mod.get_yoga_details(jd, place, divisional_chart_factor=1)
            yogas = list(result[0].keys()) if result and len(result) > 0 else []

            d1_positions = drik.dhasavarga(jd, place, 1)[:9]
            d9_positions = drik.dhasavarga(jd, place, 9)[:9]
            asc_info = drik.ascendant(jd, place)
            d1_asc_sign, d1_asc_degree = asc_info[0], asc_info[1]
            d9_asc_sign, d9_asc_degree = drik.dasavarga_from_long(d1_asc_sign * 30 + d1_asc_degree, 9)
            tithi_info = drik.tithi(jd, place)
            tithi_no = int(tithi_info[0]) if tithi_info else None
            lunar_phase = None
            if tithi_no:
                lunar_phase = "waxing" if tithi_no <= 15 else "waning"
            gulika = drik.gulika_longitude(dob, tob, place, divisional_chart_factor=1)
            maandi = drik.maandi_longitude(dob, tob, place, divisional_chart_factor=1)

        context = {
            "schema_version": "2.0",
            "jd": jd,
            "d1": {
                "ascendant": SIGNS[d1_asc_sign],
                "ascendant_degree": d1_asc_degree,
                "planets": _planet_dict_from_pyjhora_positions(d1_positions, d1_asc_sign),
            },
            "d9": {
                "ascendant": SIGNS[d9_asc_sign],
                "ascendant_degree": d9_asc_degree,
                "planets": _planet_dict_from_pyjhora_positions(d9_positions, d9_asc_sign),
            },
            "panchanga": {
                "tithi": tithi_no,
                "paksha": lunar_phase,
                "is_waning_moon": lunar_phase == "waning",
                "raw_tithi": tithi_info,
            },
            "upagraha": {
                "gulika": _upagraha_payload("Gulika", gulika, d1_asc_sign),
                "maandi": _upagraha_payload("Maandi", maandi, d1_asc_sign),
            },
        }
        return {"yogas": yogas, "count": len(yogas), "status": "ok", "context": context}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        chart = json.loads(sys.argv[1])
    else:
        # Read from stdin
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"error": "No chart data"}))
            sys.exit(1)
        chart = json.loads(raw)
    result = compute_yogas(chart)
    # 最后一行必须是纯净JSON
    print(json.dumps(result, ensure_ascii=False))
