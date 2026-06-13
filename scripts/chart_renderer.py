#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南印度占星盘图可视化渲染器 v1.0

生成南印度风格 (4×4方格) 的可视化星盘SVG。
支持：D1(本命)/D9(Navamsa)/D10(Dasamsa)等分盘
"""

from typing import Dict, List, Optional

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

# 南印度盘星座固定布局（从左上角顺时针读数）
# 星座位置固定不变，行星散布其中
SOUTH_INDIAN_GRID = [
    # Row 0: Pisces, Aries, Taurus, Gemini
    [11, 0, 1, 2],
    # Row 1: Aquarius, (CENTER), (CENTER), Cancer
    [10, -1, -1, 3],
    # Row 2: Capricorn, (CENTER), (CENTER), Leo
    [9, -1, -1, 4],
    # Row 3: Sagittarius, Scorpio, Libra, Virgo
    [8, 7, 6, 5],
]

PLANET_SYMBOLS = {
    'Sun': '☉', 'Moon': '☽', 'Mars': '♂', 'Mercury': '☿',
    'Jupiter': '♃', 'Venus': '♀', 'Saturn': '♄',
    'Rahu': '☊', 'Ketu': '☋', 'Asc': 'Asc',
}

PLANET_COLORS = {
    'Sun': '#E65100', 'Moon': '#1565C0', 'Mars': '#C62828',
    'Mercury': '#2E7D32', 'Jupiter': '#F9A825', 'Venus': '#6A1B9A',
    'Saturn': '#37474F', 'Rahu': '#00695C', 'Ketu': '#BF360C',
}

SIGN_NAMES_CN = {
    'Aries': '白羊', 'Taurus': '金牛', 'Gemini': '双子', 'Cancer': '巨蟹',
    'Leo': '狮子', 'Virgo': '处女', 'Libra': '天秤', 'Scorpio': '天蝎',
    'Sagittarius': '射手', 'Capricorn': '摩羯', 'Aquarius': '水瓶', 'Pisces': '双鱼',
}

SIGN_ABBREV = {
    'Aries': 'Ar', 'Taurus': 'Ta', 'Gemini': 'Ge', 'Cancer': 'Cn',
    'Leo': 'Le', 'Virgo': 'Vi', 'Libra': 'Li', 'Scorpio': 'Sc',
    'Sagittarius': 'Sg', 'Capricorn': 'Cp', 'Aquarius': 'Aq', 'Pisces': 'Pi',
}

CELL_SIZE = 80
PADDING = 10
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 50
SVG_WIDTH = GRID_OFFSET_X * 2 + CELL_SIZE * 4
SVG_HEIGHT = GRID_OFFSET_Y * 2 + CELL_SIZE * 4 + 60


def render_south_indian_chart(planets: Dict, asc_sign: str, title: str = "D1 — Rashi Chart") -> str:
    """
    生成南印度风格星盘SVG字符串。

    Args:
        planets: {planet: sign_name} 或 {planet: {'sign': name, 'degree': float}}
        asc_sign: 上升星座名称
        title: 图表标题

    Returns:
        完整SVG字符串
    """
    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" style="font-family:Arial,sans-serif">')

    # 背景
    lines.append(f'<rect width="{SVG_WIDTH}" height="{SVG_HEIGHT}" fill="#fafafa" rx="8"/>')
    lines.append(f'<text x="{SVG_WIDTH/2}" y="25" text-anchor="middle" font-size="16" font-weight="bold" fill="#333">{title}</text>')

    # 绘制网格
    for row in range(4):
        for col in range(4):
            sign_idx = SOUTH_INDIAN_GRID[row][col]
            if sign_idx < 0:
                continue

            x = GRID_OFFSET_X + col * CELL_SIZE
            y = GRID_OFFSET_Y + row * CELL_SIZE
            sign_name = SIGNS[sign_idx]
            abbrev = SIGN_ABBREV[sign_name]

            # 单元格背景（上升星座高亮）
            is_asc = sign_name == asc_sign
            bg = '#fff3e0' if is_asc else '#fff'
            lines.append(f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" fill="{bg}" stroke="#ccc" stroke-width="1" rx="2"/>')

            # 星座缩写（左上角）
            lines.append(f'<text x="{x+5}" y="{y+14}" font-size="11" fill="#999">{abbrev}</text>')

            # 上升标记
            if is_asc:
                lines.append(f'<text x="{x+CELL_SIZE-5}" y="{y+14}" font-size="10" fill="#e65100" text-anchor="end">▲</text>')

            # 行星
            planet_y = y + 30
            for pname in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']:
                pdata = planets.get(pname)
                if not pdata:
                    continue
                p_sign = pdata if isinstance(pdata, str) else pdata.get('sign', '')
                p_deg = "" if isinstance(pdata, str) else f" {pdata.get('degree',0)%30:.0f}°"
                if p_sign == sign_name:
                    symbol = PLANET_SYMBOLS.get(pname, pname[:2])
                    color = PLANET_COLORS.get(pname, '#333')
                    lines.append(f'<text x="{x+CELL_SIZE/2}" y="{planet_y}" text-anchor="middle" font-size="13" fill="{color}" data-planet="{pname}"><title>{pname}</title>{symbol}{p_deg}</text>')
                    planet_y += 16

    # 中心区域（传统上写星盘信息）
    cx = GRID_OFFSET_X + 1.5 * CELL_SIZE
    cy = GRID_OFFSET_Y + 1.5 * CELL_SIZE
    lines.append(f'<text x="{cx}" y="{cy-5}" text-anchor="middle" font-size="10" fill="#999">Rasi Chart</text>')
    lines.append(f'<text x="{cx}" y="{cy+12}" text-anchor="middle" font-size="10" fill="#999">(D1)</text>')

    lines.append('</svg>')
    return '\n'.join(lines)


def render_html_report(birth_data: Dict, chart_data: Dict, analysis: Dict,
                       title: str = "印度占星分析报告") -> str:
    """
    生成完整的HTML分析报告。

    Args:
        birth_data: {'name': str, 'date': str, 'time': str, 'place': str}
        chart_data: 星盘数据（用于生成图表）
        analysis: 分析结果 {'career': {...}, 'relationship': {...}, 'remedies': {...}, ...}
        title: 报告标题

    Returns:
        完整HTML字符串
    """
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f5f5f5; color: #333; line-height:1.6; }}
.container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
.header {{ background: linear-gradient(135deg, #1a237e, #283593); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; text-align: center; }}
.header h1 {{ font-size: 24px; margin-bottom: 10px; }}
.header .subtitle {{ font-size: 14px; opacity: 0.8; }}
.card {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
.card h2 {{ font-size: 18px; color: #1a237e; margin-bottom: 12px; border-bottom: 2px solid #e8eaf6; padding-bottom: 8px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }}
.tag {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; margin: 2px; }}
.tag-yes {{ background: #e8f5e9; color: #2e7d32; }}
.tag-no {{ background: #ffebee; color: #c62828; }}
.tag-warn {{ background: #fff3e0; color: #e65100; }}
.strength-bar {{ height: 8px; border-radius: 4px; background: #e0e0e0; margin: 5px 0; overflow: hidden; }}
.strength-fill {{ height: 100%; border-radius: 4px; }}
.footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; padding: 20px; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 13px; }}
th {{ background: #f5f5f5; color: #555; font-weight: 600; }}
</style></head><body><div class="container">

<div class="header">
<h1>🔮 {title}</h1>
<div class="subtitle">印度占星 (Jyotish) · 基于BPHS标准 · Lahiri岁差</div>
</div>

<div class="card">
<h2>📋 出生信息</h2>
<div class="grid">
<div><strong>姓名：</strong>{birth_data.get('name', '—')}</div>
<div><strong>日期：</strong>{birth_data.get('date', '—')}</div>
<div><strong>时间：</strong>{birth_data.get('time', '—')}</div>
<div><strong>地点：</strong>{birth_data.get('place', '—')}</div>
</div>
</div>
'''

    # 星盘图
    if chart_data:
        svg_chart = render_south_indian_chart(
            chart_data.get('planets', {}),
            chart_data.get('asc_sign', 'Aries'),
            "D1 — Rashi Chart (本命盘)"
        )
        html += f'<div class="card"><h2>🌟 本命盘</h2><div style="text-align:center">{svg_chart}</div></div>'

    # 事业分析
    if analysis.get('career'):
        c = analysis['career']
        html += '<div class="card"><h2>💼 事业分析</h2>'
        html += f'<p><strong>评估：</strong>{c.get("assessment", "")}</p>'
        if c.get('fields'):
            html += '<p><strong>推荐领域：</strong><br/>'
            for f in c['fields'][:5]:
                perc = int(f.get('score', 0) / max(1, max(x.get('score', 0) for x in c['fields'] or [{'score': 1}])) * 100)
                color = '#1a237e' if perc > 70 else '#283593' if perc > 40 else '#5c6bc0'
                html += f'<span style="display:inline-block;width:{max(10,perc)}%;background:{color};color:white;padding:2px 8px;border-radius:4px;margin:2px;font-size:12px">{f["field"]}</span> '
            html += '</p>'
        html += '</div>'

    # 感情分析
    if analysis.get('relationship'):
        r = analysis['relationship']
        html += '<div class="card"><h2>💕 感情分析</h2>'
        html += f'<p><strong>评估：</strong>{r.get("assessment", "")}</p>'
        if r.get('partnership_style'):
            for s in r['partnership_style'][:1]:
                html += f'<p><strong>Venus：</strong>{s.get("expression", "")}</p>'
        html += '</div>'

    # 补救建议
    if analysis.get('remedies'):
        rem = analysis['remedies']
        html += '<div class="card"><h2>🪷 补救建议</h2>'
        html += f'<p>{rem.get("summary", "")}</p>'
        recs = rem.get('recommendations', {})
        if recs.get('gems'):
            html += '<p><strong>宝石建议：</strong><br/>'
            for g in recs['gems'][:3]:
                html += f'<span class="tag tag-yes">{g["planet"]}: {g["gem"]}</span> '
            html += '</p>'
        if recs.get('mantras'):
            html += '<p><strong>咒语建议：</strong><br/>'
            for m in recs['mantras'][:3]:
                html += f'<span class="tag tag-warn">{m["mantra"]} × {m["repetitions"]}</span> '
            html += '</p>'
        html += '</div>'

    html += '<div class="footer">Generated by yinduzhanxing v6.4.0 · MIT License · 仅供学习参考</div>'
    html += '</div></body></html>'
    return html
