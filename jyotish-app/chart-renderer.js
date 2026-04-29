/**
 * 星盘渲染 — 南印度 + 北印度风格 v3.0
 * 浅色极简主题，支持南/北印度风格切换
 */

import { SIGNS, SIGNS_CN, SIGNS_EN_SHORT, PLANET_SYMBOLS, PLANET_CN } from './jyotish-engine.js';
import { signName, getLang } from './i18n.js';

// 南印度星盘宫位映射（星座固定位置）
const SOUTH_INDIAN_LAYOUT = [
  [0,0],[0,1],[0,2],[0,3], // Pisces, Aries, Taurus, Gemini
  [1,3],[2,3],[3,3],       // Cancer, Leo, Virgo
  [3,2],[3,1],[3,0],       // Libra, Scorpio, Sagittarius
  [2,0],[1,0],             // Capricorn, Aquarius
];

// 北印度星盘宫位布局（固定上升在顶部菱形）
// 12宫按固定位置排列，上升始终在顶部菱形格
const NORTH_INDIAN_HOUSES = [
  // [row, col] — 从12宫开始，顺时针: 12,1,2,3,4,5,6,7,8,9,10,11
  // 顶行:         12,  1,   2
  // 右侧下行:          3,   4
  // 底行:    11, 10,  9,   8(中心偏), 7
  // 左侧上行:    6,   5
  [0,0],[0,1],[0,2],       // H12, H1, H2
  [1,2],[2,3],             // H3, H4
  [3,3],[3,2],[3,1],[3,0], // H5, H6, H7, H8
  [2,0],[1,0],             // H9, H10
  [1,1],                   // H11 (center-ish)
];

// 浅色主题色值
const THEME = {
  bg: '#ffffff',
  bgAsc: 'rgba(109,40,217,0.04)',
  border: '#c9c8c8',
  borderAsc: 'rgba(109,40,217,0.35)',
  signText: '#6b6b6b',
  signTextAsc: '#6d28d9',
  houseNum: '#8c8c8c',
  planetDefault: '#2e2e2e',
  planetExalted: '#16a34a',
  planetDebilitated: '#dc2626',
  planetOwn: '#d97706',
  ascLabel: '#6d28d9',
  combust: '#dc2626',
};

/**
 * 渲染南印度风格星盘
 */
export function renderSouthIndianChart(container, chartData, options = {}) {
  const { planets, ascendant } = chartData;
  const ascIdx = SIGNS.indexOf(ascendant.sign);
  const size = options.size || 420;
  const title = options.title || '';

  // 按宫位分组行星
  const housePlanets = {};
  for (const [pname, pinfo] of Object.entries(planets)) {
    if (pinfo.error) continue;
    const h = pinfo.house;
    if (!housePlanets[h]) housePlanets[h] = [];
    housePlanets[h].push({ name: pname, ...pinfo });
  }

  const cellSize = size / 4;
  let svg = '';

  if (title) {
    svg += `<div style="text-align:center;font-size:12px;color:#6b6b6b;margin-bottom:6px;">${title}</div>`;
  }

  svg += `<svg viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;">`;

  // 背景
  svg += `<rect width="${size}" height="${size}" fill="${THEME.bg}" rx="10"/>`;

  // 绘制12个宫格
  for (let signIdx = 0; signIdx < 12; signIdx++) {
    const [row, col] = SOUTH_INDIAN_LAYOUT[signIdx];
    const x = col * cellSize;
    const y = row * cellSize;
    const signName = SIGNS[signIdx];
    const isAscSign = signIdx === ascIdx;

    // 宫格背景
    const bgColor = isAscSign ? THEME.bgAsc : THEME.bg;
    svg += `<rect x="${x+1}" y="${y+1}" width="${cellSize-2}" height="${cellSize-2}" fill="${bgColor}" rx="4"/>`;

    // 宫格边框
    const borderColor = isAscSign ? THEME.borderAsc : THEME.border;
    svg += `<rect x="${x+1}" y="${y+1}" width="${cellSize-2}" height="${cellSize-2}" fill="none" stroke="${borderColor}" stroke-width="1" rx="4"/>`;

    // 星座名（小字，左上角）
    const signColor = isAscSign ? THEME.signTextAsc : THEME.signText;
    svg += `<text x="${x+8}" y="${y+14}" font-size="9" fill="${signColor}" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-weight="${isAscSign?'600':'400'}">${SIGNS_EN_SHORT[signName]}</text>`;

    // 宫位编号
    const houseNum = ((signIdx - ascIdx + 12) % 12) + 1;
    svg += `<text x="${x+cellSize-10}" y="${y+14}" font-size="8" fill="${THEME.houseNum}" text-anchor="end" font-family="sans-serif">${houseNum}</text>`;

    // 该宫的行星
    const pInHouse = housePlanets[houseNum] || [];
    let py = y + 28;
    for (const p of pInHouse) {
      const symbol = PLANET_SYMBOLS[p.name] || '';
      let pColor = THEME.planetDefault;
      if (p.status === '入旺') pColor = THEME.planetExalted;
      else if (p.status === '落陷') pColor = THEME.planetDebilitated;
      else if (p.status === '入庙') pColor = THEME.planetOwn;

      const retroMark = p.retrograde ? ' ℞' : '';
      const combustMark = p.combust ? ' C' : '';
      const degStr = (p.degree_in_sign != null) ? p.degree_in_sign.toFixed(1) + '°' : '';
      svg += `<text x="${x+8}" y="${py}" font-size="12" fill="${pColor}" font-family="sans-serif">${symbol}${degStr}${retroMark}${combustMark}</text>`;
      py += 16;
    }

    // 上升标记
    if (isAscSign) {
      svg += `<text x="${x+cellSize/2}" y="${y+cellSize-8}" font-size="10" fill="${THEME.ascLabel}" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-weight="600">ASC</text>`;
    }
  }

  // ===== 中心区域 — 核心摘要 =====
  const cx = size / 2, cy0 = cellSize, cw = cellSize * 2;
  const summary = options.summary || null;
  // 背景框
  svg += `<rect x="${cy0+3}" y="${cy0+3}" width="${cw-6}" height="${cw-6}" fill="rgba(109,40,217,0.015)" rx="6"/>`;
  svg += `<rect x="${cy0+3}" y="${cy0+3}" width="${cw-6}" height="${cw-6}" fill="none" stroke="rgba(109,40,217,0.08)" stroke-width="0.5" rx="6"/>`;

  // Lagna 上升星座 + 度数
  const ascSignSymbol = {Aries:'♈',Taurus:'♉',Gemini:'♊',Cancer:'♋',Leo:'♌',Virgo:'♍',Libra:'♎',Scorpio:'♏',Sagittarius:'♐',Capricorn:'♑',Aquarius:'♒',Pisces:'♓'}[ascendant.sign] || '';
  svg += `<text x="${cx}" y="${cy0+20}" text-anchor="middle" font-size="12" fill="${THEME.ascLabel}" font-weight="700" font-family="-apple-system,BlinkMacSystemFont,sans-serif">${ascSignSymbol} ${signName(ascendant.sign)} ${(ascendant.degree_in_sign != null ? ascendant.degree_in_sign : ascendant.degree % 30).toFixed(2)}°</text>`;

  // 月亮星宿
  if (summary?.moonNakshatra) {
    svg += `<text x="${cx}" y="${cy0+34}" text-anchor="middle" font-size="9" fill="${THEME.signText}" font-family="sans-serif">☽ ${summary.moonNakshatra}</text>`;
  }

  // 分隔线
  svg += `<line x1="${cx-40}" y1="${cy0+42}" x2="${cx+40}" y2="${cy0+42}" stroke="rgba(109,40,217,0.12)" stroke-width="0.5"/>`;

  // 当前 Dasha
  if (summary?.dasha) {
    const dColor = THEME.planetDefault;
    svg += `<text x="${cx}" y="${cy0+56}" text-anchor="middle" font-size="10" fill="${dColor}" font-weight="600" font-family="sans-serif">Dasha</text>`;
    svg += `<text x="${cx}" y="${cy0+70}" text-anchor="middle" font-size="10" fill="${THEME.ascLabel}" font-weight="600" font-family="sans-serif">${summary.dasha.maha}/${summary.dasha.antar}</text>`;
    svg += `<text x="${cx}" y="${cy0+82}" text-anchor="middle" font-size="8" fill="${THEME.houseNum}" font-family="sans-serif">${summary.dasha.period}</text>`;
  }

  // AK / DK
  if (summary?.karaka) {
    const parts = [];
    if (summary.karaka.AK) parts.push(`AK:${summary.karaka.AK}`);
    if (summary.karaka.DK) parts.push(`DK:${summary.karaka.DK}`);
    if (parts.length) {
      svg += `<text x="${cx}" y="${cy0+96}" text-anchor="middle" font-size="9" fill="${THEME.planetDefault}" font-family="sans-serif">${parts.join(' · ')}</text>`;
    }
  }

  // 关键 Yoga（最多3个）
  if (summary?.topYogas && summary.topYogas.length > 0) {
    let ty = cy0 + 112;
    for (const y of summary.topYogas.slice(0, 3)) {
      const yColor = y.negative ? '#dc2626' : '#16a34a';
      svg += `<text x="${cx}" y="${ty}" text-anchor="middle" font-size="8" fill="${yColor}" font-family="sans-serif">◆ ${y.name_cn}</text>`;
      ty += 12;
    }
  }

  svg += '</svg>';
  container.innerHTML = svg;
}

/**
 * 渲染北印度风格星盘（Diamond 菱形布局）
 * 北印盘固定12宫位置，上升始终在顶部中心格
 */
export function renderNorthIndianChart(container, chartData, options = {}) {
  const { planets, ascendant } = chartData;
  const ascIdx = SIGNS.indexOf(ascendant.sign);
  const size = options.size || 420;
  const title = options.title || '';

  // 按宫位分组行星
  const housePlanets = {};
  for (const [pname, pinfo] of Object.entries(planets)) {
    if (pinfo.error) continue;
    const h = pinfo.house;
    if (!housePlanets[h]) housePlanets[h] = [];
    housePlanets[h].push({ name: pname, ...pinfo });
  }

  // 北印盘布局: 4x4 网格，外圈12格 = 12宫
  // 位置定义 (row, col) — 按宫位编号 1-12
  const houseCells = {
    1:  [0,1], 2:  [0,2],        // 顶行右半
    3:  [1,3], 4:  [2,3],        // 右列下半
    5:  [3,2], 6:  [3,1],        // 底行左半
    7:  [2,0], 8:  [1,0],        // 左列上半
    9:  [1,1], 10: [1,2],        // 内层上
    11: [2,2], 12: [2,1],        // 内层下
  };

  const cellSize = size / 4;
  let svg = '';

  if (title) {
    svg += `<div style="text-align:center;font-size:12px;color:#6b6b6b;margin-bottom:6px;">${title}</div>`;
  }

  svg += `<svg viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;">`;
  svg += `<rect width="${size}" height="${size}" fill="${THEME.bg}" rx="10"/>`;

  // 绘制菱形外框线
  const cx = size / 2, cy = size / 2, r = size * 0.47;
  svg += `<polygon points="${cx},${cy-r} ${cx+r},${cy} ${cx},${cy+r} ${cx-r},${cy}" fill="none" stroke="${THEME.border}" stroke-width="1.5"/>`;
  // 内层菱形
  const ri = r * 0.5;
  svg += `<polygon points="${cx},${cy-ri} ${cx+ri},${cy} ${cx},${cy+ri} ${cx-ri},${cy}" fill="none" stroke="${THEME.border}" stroke-width="1"/>`;
  // 对角线
  svg += `<line x1="${cx}" y1="${cy-r}" x2="${cx}" y2="${cy-ri}" stroke="${THEME.border}" stroke-width="0.5"/>`;
  svg += `<line x1="${cx}" y1="${cy+ri}" x2="${cx}" y2="${cy+r}" stroke="${THEME.border}" stroke-width="0.5"/>`;
  svg += `<line x1="${cx-r}" y1="${cy}" x2="${cx-ri}" y2="${cy}" stroke="${THEME.border}" stroke-width="0.5"/>`;
  svg += `<line x1="${cx+ri}" y1="${cy}" x2="${cx+r}" y2="${cy}" stroke="${THEME.border}" stroke-width="0.5"/>`;

  // 各宫位
  for (let house = 1; house <= 12; house++) {
    const [row, col] = houseCells[house];
    const x = col * cellSize;
    const y = row * cellSize;
    const isAsc = house === 1;

    // 计算该宫的星座
    const signIdx = (ascIdx + house - 1) % 12;
    const signName = SIGNS[signIdx];

    // 背景高亮上升宫
    if (isAsc) {
      svg += `<rect x="${x+2}" y="${y+2}" width="${cellSize-4}" height="${cellSize-4}" fill="${THEME.bgAsc}" rx="3" opacity="0.5"/>`;
    }

    // 星座名
    const signColor = isAsc ? THEME.signTextAsc : THEME.signText;
    svg += `<text x="${x+6}" y="${y+13}" font-size="8" fill="${signColor}" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-weight="${isAsc?'600':'400'}">${SIGNS_EN_SHORT[signName]}</text>`;

    // 宫位编号
    svg += `<text x="${x+cellSize-6}" y="${y+13}" font-size="7" fill="${THEME.houseNum}" text-anchor="end" font-family="sans-serif">H${house}</text>`;

    // 行星
    const pInHouse = housePlanets[house] || [];
    let py = y + 26;
    for (const p of pInHouse) {
      const symbol = PLANET_SYMBOLS[p.name] || '';
      let pColor = THEME.planetDefault;
      if (p.status === '入旺') pColor = THEME.planetExalted;
      else if (p.status === '落陷') pColor = THEME.planetDebilitated;
      else if (p.status === '入庙') pColor = THEME.planetOwn;
      const retroMark = p.retrograde ? ' ℞' : '';
      const degStr = (p.degree_in_sign != null) ? p.degree_in_sign.toFixed(1) + '°' : '';
      svg += `<text x="${x+6}" y="${py}" font-size="11" fill="${pColor}" font-family="sans-serif">${symbol}${degStr}${retroMark}</text>`;
      py += 14;
    }

    // 上升标记
    if (isAsc) {
      svg += `<text x="${x+cellSize/2}" y="${y+cellSize-6}" font-size="9" fill="${THEME.ascLabel}" text-anchor="middle" font-weight="600" font-family="sans-serif">ASC</text>`;
    }
  }

  svg += '</svg>';
  container.innerHTML = svg;
}

// 全局默认渲染函数（可切换风格）
let _chartStyle = 'south';

export function setChartStyle(style) { _chartStyle = style; }
export function getChartStyle() { return _chartStyle; }

export function renderChart(container, chartData, options = {}) {
  if (_chartStyle === 'north') {
    renderNorthIndianChart(container, chartData, options);
  } else {
    renderSouthIndianChart(container, chartData, options);
  }
}
