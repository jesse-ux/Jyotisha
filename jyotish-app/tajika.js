/**
 * Tajika/Varshaphala 年运盘模块 v1.0
 * 移植自 Python tajika.py
 *
 * 支持:
 *   - Muntha（年度上升点移动）
 *   - Year Lord（年度守护星）
 *   - Mudda Dasha（年度大运）
 *   - Tri-Pataka（三旗系统）
 */

import { SIGNS, SIGN_LORDS } from './jyotish-engine.js';

const DASHA_ORDER = ['Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury'];
const DASHA_YEARS = { Ketu:7, Venus:20, Sun:6, Moon:10, Mars:7, Rahu:18, Jupiter:16, Saturn:19, Mercury:17 };

const MUNTHA_INTERP = {
  Aries: '年度主题：新开始、冒险、独立行动',
  Taurus: '年度主题：财务稳定、物质积累、感官享受',
  Gemini: '年度主题：学习、沟通、多元发展',
  Cancer: '年度主题：家庭、情感、内在安全感',
  Leo: '年度主题：创造力、领导力、自我表达',
  Virgo: '年度主题：健康、服务、细节完善',
  Libra: '年度主题：关系、合作、美学追求',
  Scorpio: '年度主题：转化、深层变革、隐藏事物',
  Sagittarius: '年度主题：远方旅行、哲学、高等教育',
  Capricorn: '年度主题：事业成就、社会地位、长期规划',
  Aquarius: '年度主题：社交网络、创新、人道主义',
  Pisces: '年度主题：灵性成长、隐退、创意灵感',
};

const YEAR_THEMES = {
  Sun: '权威、政府、父亲、领导力',
  Moon: '公众、母亲、情感、直觉',
  Mars: '行动、竞争、房地产、手术',
  Mercury: '沟通、商业、学习、旅行',
  Jupiter: '智慧、子女、宗教、财富',
  Venus: '爱情、艺术、奢侈品、婚姻',
  Saturn: '纪律、长寿、建筑、责任',
};

// ========== Muntha ==========
export function calcMuntha(birthAscIdx, age) {
  const munthaIdx = (birthAscIdx + age) % 12;
  const munthaSign = SIGNS[munthaIdx];
  const lord = SIGN_LORDS[munthaSign];
  return {
    muntha_sign: munthaSign,
    muntha_sign_idx: munthaIdx,
    muntha_lord: lord,
    age,
    interpretation: MUNTHA_INTERP[munthaSign] || '',
  };
}

// ========== Year Lord ==========
export function calcYearLord(birthAscIdx, age) {
  const munthaIdx = (birthAscIdx + age) % 12;
  const munthaSign = SIGNS[munthaIdx];
  const yearLord = SIGN_LORDS[munthaSign];
  const auxHouses = [2, 5, 9, 11];
  const auxLords = auxHouses.map(h => {
    const hSignIdx = (munthaIdx + h - 1) % 12;
    const hSign = SIGNS[hSignIdx];
    return { house: h, sign: hSign, lord: SIGN_LORDS[hSign] };
  });
  return {
    age,
    year_lord: yearLord,
    muntha_sign: munthaSign,
    auxiliary_lords: auxLords,
    year_theme: YEAR_THEMES[yearLord] || '',
  };
}

// ========== Mudda Dasha ==========
export function calcMuddaDasha(ascSignIdx, varshaLord, birthMonth) {
  const startIdx = DASHA_ORDER.indexOf(varshaLord);
  const sequence = [];
  let remaining = 12.0;

  for (let i = 0; i < 9; i++) {
    const lord = DASHA_ORDER[(startIdx + i) % 9];
    const years = DASHA_YEARS[lord];
    let months = years * 12.0 / 120.0;
    if (months > remaining) months = remaining;
    remaining -= months;
    sequence.push({ lord, months: Math.round(months * 100) / 100, order: i + 1 });
    if (remaining <= 0.01) break;
  }

  return { varsha_lord: varshaLord, dasha_sequence: sequence, total_months: 12 };
}

// ========== Tri-Pataka ==========
export function calcTriPataka(planetLons, varshaLord, munthaSignIdx) {
  const munthaLord = SIGN_LORDS[SIGNS[munthaSignIdx]];

  function strength(planet, lons) {
    if (!lons[planet]) return 'unknown';
    const lon = lons[planet];
    const si = Math.floor(lon / 30) % 12;
    const houseFromAsc = ((si - munthaSignIdx) % 12 + 12) % 12 + 1;
    if ([1, 4, 7, 10].includes(houseFromAsc)) return 'strong';
    if ([5, 9].includes(houseFromAsc)) return 'moderate';
    return 'weak';
  }

  const dlS = strength(varshaLord, planetLons);
  const mlS = strength(munthaLord, planetLons);
  const ylS = strength(varshaLord, planetLons);

  const strongCount = [dlS, mlS, ylS].filter(s => s === 'strong').length;
  const weakCount = [dlS, mlS, ylS].filter(s => s === 'weak').length;

  let verdict = 'mixed';
  if (strongCount >= 2) verdict = 'excellent';
  else if (weakCount >= 2) verdict = 'challenging';

  const interpMap = {
    excellent: '三旗中两旗以上强旺，年度运势极佳',
    mixed: '三旗力量参差不齐，年度运势起伏',
    challenging: '三旗中两旗以上衰弱，年度运势挑战较大',
  };

  return {
    dasha_lord: { planet: varshaLord, strength: dlS },
    muntha_lord: { planet: munthaLord, strength: mlS },
    year_lord: { planet: varshaLord, strength: ylS },
    verdict,
    interpretation: interpMap[verdict] || '',
  };
}

// ========== 完整 Tajika ==========
export function computeTajika(planets, ascSign, birthYear, birthMonth) {
  const ascIdx = SIGNS.indexOf(ascSign);
  const currentYear = new Date().getFullYear();
  const age = currentYear - birthYear;

  const muntha = calcMuntha(ascIdx, age);
  const yearLord = calcYearLord(ascIdx, age);
  const muddaDasha = calcMuddaDasha(ascIdx, yearLord.year_lord, birthMonth);

  // 构建 planetLons for tri-pataka
  const planetLons = {};
  for (const [pn, p] of Object.entries(planets)) {
    if (p && !p.error && p.degree != null) planetLons[pn] = p.degree;
  }
  const triPataka = calcTriPataka(planetLons, yearLord.year_lord, muntha.muntha_sign_idx);

  return { muntha, year_lord: yearLord, mudda_dasha: muddaDasha, tri_pataka: triPataka };
}
