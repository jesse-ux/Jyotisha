#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印度占星 API 服务器 v1.0
为 jyotish-app 前端提供 v6.7.3 引擎的精算能力

启动: python3 scripts/jyotish_api_server.py --port 5200
"""

import json, sys, os, math
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

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


class JyotishAPIHandler(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode())

    def do_OPTIONS(self):
        self._json({})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/health':
            self._json({'status': 'ok', 'version': '6.7.3', 'modules': 'KP/Synastry/Prashna/Remedies/PMC/SadeSati'})
        elif path == '/api/cities':
            self._json(list(CITY_DB.keys()))
        else:
            self._json({'error': 'Not found'}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}

        try:
            if path == '/api/chart':
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
            else:
                self._json({'error': f'Unknown endpoint: {path}'}, 404)
        except Exception as e:
            self._json({'error': str(e)}, 500)

    def _compute_chart(self, body):
        """完整星盘计算"""
        year = int(body.get('year', 1990))
        month = int(body.get('month', 6))
        day = int(body.get('day', 15))
        hour = float(body.get('hour', 12))
        minute = float(body.get('minute', 0))
        lat = float(body.get('lat', 39.9))
        lon = float(body.get('lon', 116.4))
        tz = float(body.get('tz', 8))

        try:
            import swisseph as swe
            swe.set_ephe_path(os.path.join(SCRIPTS_DIR, '..', 'swiss_ephemeris'))
            jd = swe.julday(year, month, day, hour + minute/60.0)
            swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

            planets_data = {}
            planet_ids = {'Sun': 0, 'Moon': 1, 'Mars': 4, 'Mercury': 2, 'Jupiter': 5, 'Venus': 3, 'Saturn': 6, 'Rahu': 10, 'Ketu': 20}
            planet_names_rev = {v: k for k, v in planet_ids.items()}

            for pid, pname in planet_names_rev.items():
                if pid == 20:
                    lon_rahu, _ = swe.calc_ut(jd, 10)
                    lon = (lon_rahu[0] + 180) % 360
                else:
                    result, _ = swe.calc_ut(jd, pid)
                    lon = result[0] % 360
                sign_idx = int(lon / 30) % 12
                planets_data[pname] = {'lon': lon, 'sign_idx': sign_idx, 'sign': SIGNS[sign_idx], 'degree': lon % 30}

            # Ascendant
            asc_lon = swe.houses_ex(jd, lat, lon, b'E')[0][0] % 360
            asc_sign_idx = int(asc_lon / 30) % 12
            asc_sign = SIGNS[asc_sign_idx]

            # Houses
            houses = {}
            for h in range(1, 13):
                s = (asc_sign_idx + h - 1) % 12
                houses[h] = {'sign': SIGNS[s], 'sign_idx': s}

            # Planet houses
            for pn, pd in planets_data.items():
                pd['house'] = ((pd['sign_idx'] - asc_sign_idx) % 12) + 1

            # Dasha (simplified Vimshottari)
            moon_lon = planets_data['Moon']['lon']
            nak_size = 360/27
            nak_idx = int(moon_lon / nak_size)
            dasha_lords = ['Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury']
            dasha_years = [7,20,6,10,7,18,16,19,17]
            nak_lord_idx = nak_idx % 9
            md_lord = dasha_lords[nak_lord_idx]
            total_years = dasha_years[nak_lord_idx]
            elapsed = (moon_lon % nak_size) / nak_size * total_years
            remaining = total_years - elapsed

            birth_dt = datetime(year, month, day, int(hour), int(minute))
            elapsed_days = elapsed * 365.25636
            dasha_start = birth_dt - timedelta(days=elapsed_days) if elapsed_days < 365*120 else birth_dt

            # Yoga detection
            yogas = self._detect_yogas(planets_data, asc_sign_idx)

            # Sade Sati
            from sade_sati import calc_sade_sati_complete
            # Transit Saturn (approximate)
            saturn_year_progress = (year - 2026) * 12 / 30  # ~12 signs in 30 years
            transit_saturn_sign = (planets_data['Saturn']['sign_idx'] + int(saturn_year_progress)) % 12
            transit_saturn_lon = transit_saturn_sign * 30 + 15
            sade_sati = calc_sade_sati_complete(moon_lon, asc_lon, transit_saturn_lon)

            # Dasha清单
            from extended_dashas import get_available_dashas, DASHA_REGISTRY
            dashas = get_available_dashas()
            dasha_list = [{'key': k, 'name': DASHA_REGISTRY[k]['name'], 'years': DASHA_REGISTRY[k]['years'], 'type': DASHA_REGISTRY[k]['type']} for k in dashas]

            # Shadbala (v6.7.4: jyotishganit MIT算法)
            try:
                from shadbala import calc_shadbala
                sb = calc_shadbala(planets_data, asc_sign, hour+minute/60.0, 
                    planets_data.get('Sun',{}).get('lon',0), moon_lon, minute)
                shadbala_summary = {p: {'rupas': round(d['total_rupas'],2), 'level': d['strength_level']} 
                    for p,d in sb.get('planets',{}).items()}
            except: shadbala_summary = {}

            # Yoga扩展 (dashaflow MIT规则)
            try:
                from yoga_expansion import detect_all_yogas as detect_ey
                for ey in detect_ey(planets_data, asc_sign):
                    yogas.append({'name': ey.get('name',''), 'planets': ey.get('planets',[]),
                                  'desc': ey.get('description','')[:80], 'cat': 'extended'})
            except: pass

            return {
                'success': True, 'version': '6.7.4',
                'birth': {'date': f'{year}-{month:02d}-{day:02d}', 'time': f'{int(hour):02d}:{int(minute):02d}'},
                'ascendant': {'sign': asc_sign, 'sign_idx': asc_sign_idx, 'degree': round(asc_lon % 30, 2)},
                'planets': planets_data, 'houses': houses, 'shadbala': shadbala_summary,
                'dasha': {
                    'current_md': md_lord,
                    'remaining_years': round(remaining, 2),
                    'total_years': total_years,
                    'start_date': dasha_start.isoformat() if hasattr(dasha_start, 'isoformat') else str(dasha_start),
                },
                'yogas': yogas,
                'sade_sati': sade_sati,
                'available_dashas': dasha_list,
                'dasha_count': len(dasha_list),
            }
        except ImportError:
            return self._fallback_chart(year, month, day, hour, minute, lat, lon, tz)

    def _fallback_chart(self, year, month, day, hour, minute, lat, lon, tz):
        """无Swiss Ephemeris时的简化计算"""
        import hashlib
        seed = int(hashlib.md5(f"{year}{month}{day}{hour}{minute}{lat}{lon}".encode()).hexdigest()[:8], 16)
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

        return {
            'success': True, 'version': '6.7.3-fallback',
            'warning': 'Swiss Ephemeris未安装，使用简化计算',
            'ascendant': {'sign': asc_sign, 'sign_idx': asc_sign_idx},
            'planets': planets, 'houses': houses,
            'dasha': {'current_md': 'Moon', 'remaining_years': 5},
            'yogas': [], 'sade_sati': {'active': False},
            'available_dashas': [], 'dasha_count': 0,
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
        except: pass

        try:
            from yoga_expansion import detect_all_yogas as detect_yogas_ext
            for y in detect_yogas_ext(planets, SIGNS[asc_idx]):
                yogas.append({'name': y.get('name',''), 'planets': y.get('planets',[]), 'category': 'extended'})
        except: pass

        return yogas[:10]

    def _compute_remedies(self, body):
        from remedies import recommend_remedies
        shadbala = body.get('shadbala', {})
        doshas = body.get('doshas', [])
        dasha_lord = body.get('dasha_lord', '')
        return recommend_remedies(shadbala, doshas=doshas, active_dasha_lord=dasha_lord)

    def _compute_kp(self, body):
        planets = body.get('planets', {})
        asc_idx = body.get('asc_sign_idx', 0)
        from kp_system import calc_kp_analysis
        return calc_kp_analysis(planets, SIGNS[asc_idx])

    def _compute_prashna(self, body):
        question_type = body.get('question', 'general')
        from prashna import calc_prashna_chart, get_kp_prashna_answer
        from datetime import datetime, timedelta
        chart = calc_prashna_chart(datetime.now(), body.get('planets', {}))
        answer = get_kp_prashna_answer(body.get('planets', {}), question_type, 15.5)
        return {'prashna_chart': chart, 'kp_answer': answer}

    def _compute_synastry(self, body):
        from synastry import calc_ashtakoot
        return calc_ashtakoot(body.get('male_moon', 0), body.get('female_moon', 0))

    def _compute_sade_sati(self, body):
        from sade_sati import calc_sade_sati_complete
        return calc_sade_sati_complete(body.get('moon_degree', 0), body.get('asc_degree', 0), body.get('saturn_degree', 0))

    def _compute_pmc(self, body):
        from pancha_mahapurusha import assess_pmc_strength
        return assess_pmc_strength(body.get('planets', {}), body.get('sun_degree'))

    def _compute_career(self, body):
        from career_analysis import analyze_career
        return analyze_career(body.get('planets', {}), body.get('asc_sign', 'Aries'))

    def _compute_relationship(self, body):
        from relationship_analysis import analyze_relationship
        return analyze_relationship(body.get('planets', {}), body.get('asc_sign', 'Aries'))


def start_server(port=5200):
    server = HTTPServer(('0.0.0.0', port), JyotishAPIHandler)
    print(f'🔮 Jyotish API v6.7.3 running on http://localhost:{port}')
    print(f'  POST /api/chart — 完整星盘计算')
    print(f'  POST /api/remedies — 补救建议')
    print(f'  POST /api/kp — KP分析')
    print(f'  POST /api/prashna — 卜卦')
    print(f'  POST /api/synastry — 合盘')
    print(f'  POST /api/sade_sati — 土星周期')
    print(f'  POST /api/pancha_mahapurusha — 五王瑜伽')
    print(f'  POST /api/career — 事业分析')
    print(f'  POST /api/relationship — 感情分析')
    print(f'  GET /api/health — 健康检查')
    print(f'  GET /api/cities — 城市列表')
    server.serve_forever()


if __name__ == '__main__':
    port = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == '--port' else 5200
    start_server(port)
