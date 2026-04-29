/**
 * Jyotish Transit System v2.0 — 全面行星过境分析
 * 修复: UTC时区处理 / 可配置日期 / 全行星表格 / 深度分析
 */
import { initEngine, SIGNS, SIGNS_CN, SIGN_LORDS, PLANET_CN, PLANET_SYMBOLS, PLANET_ASPECTS, NAKSHATRA_LIST } from './jyotish-engine.js';
import { t, signName } from './i18n.js';

const SE_SUN = 0, SE_MOON = 1, SE_MARS = 4, SE_MERCURY = 2, SE_JUPITER = 5, SE_VENUS = 3, SE_SATURN = 6, SE_TRUE_NODE = 11;
const SEFLG_SPEED = 256;
const PLANETS_SWE = {
  Sun: SE_SUN, Moon: SE_MOON, Mars: SE_MARS, Mercury: SE_MERCURY,
  Jupiter: SE_JUPITER, Venus: SE_VENUS, Saturn: SE_SATURN, Rahu: SE_TRUE_NODE
};
const ALL_PLANETS = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
const SLOW_PLANETS = ['Saturn','Jupiter','Rahu','Ketu'];
const FAST_PLANETS = ['Sun','Moon','Mars','Mercury','Venus'];
const NAKSPAN = 360 / 27;

// ============================================================================
// 核心: 计算 Transit 行星位置
// ============================================================================
export async function computeTransit(dateStr, timeStr, tz) {
  const swe = await initEngine();
  let year, month, day, hour;

  if (dateStr && timeStr) {
    [year, month, day] = dateStr.split('-').map(Number);
    const [h, m] = timeStr.split(':').map(Number);
    const localHour = h + m / 60.0;
    const tzOffset = tz != null ? parseFloat(tz) : 0;
    hour = localHour - tzOffset; // 转 UT
  } else {
    // 默认用当前 UTC
    const now = new Date();
    year = now.getUTCFullYear();
    month = now.getUTCMonth() + 1;
    day = now.getUTCDate();
    hour = now.getUTCHours() + now.getUTCMinutes() / 60.0;
  }

  const jd = swe.julday(year, month, day, hour);
  swe.set_sid_mode(1); // Lahiri
  const ayanamsa = swe.get_ayanamsa(jd);

  const planets = {};
  for (const [pname, pid] of Object.entries(PLANETS_SWE)) {
    try {
      const pos = swe.calc_ut(jd, pid, SEFLG_SPEED);
      const lonT = pos[0];
      const lonS = ((lonT - ayanamsa) % 360 + 360) % 360;
      const spd = pos[3];
      const si = Math.floor(lonS / 30);
      const dInS = lonS - si * 30;
      const ni = Math.floor(lonS / NAKSPAN);
      const pada = Math.floor((lonS % NAKSPAN) / (NAKSPAN / 4)) + 1;
      planets[pname] = {
        sign: SIGNS[si], sign_cn: SIGNS_CN[SIGNS[si]],
        degree: Math.round(lonS * 1e4) / 1e4,
        degree_in_sign: Math.round(dInS * 1e4) / 1e4,
        retrograde: spd < 0,
        speed: Math.round(spd * 1e4) / 1e4,
        nakshatra: NAKSHATRA_LIST[ni % 27].name,
        nakshatra_lord: NAKSHATRA_LIST[ni % 27].lord,
        nakshatra_pada: pada,
      };
      if (pname === 'Rahu') {
        const klon = (lonS + 180) % 360;
        const ksi = Math.floor(klon / 30);
        const kni = Math.floor(klon / NAKSPAN);
        const kp = Math.floor((klon % NAKSPAN) / (NAKSPAN / 4)) + 1;
        planets['Ketu'] = {
          sign: SIGNS[ksi], sign_cn: SIGNS_CN[SIGNS[ksi]],
          degree: Math.round(klon * 1e4) / 1e4,
          degree_in_sign: Math.round((klon - ksi * 30) * 1e4) / 1e4,
          retrograde: true,
          speed: -Math.abs(spd),
          nakshatra: NAKSHATRA_LIST[kni % 27].name,
          nakshatra_lord: NAKSHATRA_LIST[kni % 27].lord,
          nakshatra_pada: kp,
        };
      }
    } catch (e) { console.error(`[Transit] Error: ${pname}`, e); }
  }

  // 格式化日期显示
  let displayDate, displayTime;
  if (dateStr && timeStr) {
    displayDate = dateStr;
    displayTime = timeStr;
  } else {
    const now = new Date();
    displayDate = `${now.getUTCFullYear()}-${String(now.getUTCMonth()+1).padStart(2,'0')}-${String(now.getUTCDate()).padStart(2,'0')}`;
    displayTime = `${String(now.getUTCHours()).padStart(2,'0')}:${String(now.getUTCMinutes()).padStart(2,'0')}`;
  }

  return {
    date: displayDate,
    time: displayTime,
    is_utc: true,
    julian_day: Math.round(jd * 1e6) / 1e6,
    ayanamsa: Math.round(ayanamsa * 1e4) / 1e4,
    planets,
  };
}

// ============================================================================
// Transit vs 本命盘叠加分析（全行星版）
// ============================================================================
export function computeTransitOverlay(natalPlanets, natalAscSign, transitPlanets) {
  const ai = SIGNS.indexOf(natalAscSign);
  const allPlanets = [];

  for (const pname of ALL_PLANETS) {
    const tp = transitPlanets[pname];
    if (!tp) continue;
    const tSignIdx = SIGNS.indexOf(tp.sign);
    const transitHouse = ((tSignIdx - ai + 12) % 12) + 1;
    const np = natalPlanets[pname];

    // 检测与本命行星同宫
    const conjunctions = [];
    for (const [nn, npi] of Object.entries(natalPlanets)) {
      if (npi.error || npi.sign === undefined) continue;
      if (npi.sign === tp.sign) {
        const degDiff = Math.abs(tp.degree - npi.degree);
        conjunctions.push({ planet: nn, degree_diff: Math.round(degDiff * 100) / 100 });
      }
    }

    // 检测 Transit 行星对本命行星的相位
    const aspects = [];
    const tHouse = transitHouse;
    for (const [nn, npi] of Object.entries(natalPlanets)) {
      if (npi.error || npi.house === undefined) continue;
      const nHouse = npi.house;
      const diff = ((nHouse - tHouse + 12) % 12);
      // Graha Drishti: 所有行星 7宫相位, 火星额外 4,8; 木星 5,9; 土星 3,10
      const planetAspects = PLANET_ASPECTS[pname] || [7];
      for (const offset of planetAspects) {
        if (diff === offset) {
          aspects.push({ to: nn, to_cn: PLANET_CN[nn], type: offset === 7 ? '7宫' : `${offset}宫`, to_house: nHouse });
        }
      }
    }

    allPlanets.push({
      planet: pname,
      planet_cn: PLANET_CN[pname],
      symbol: PLANET_SYMBOLS[pname] || '',
      is_slow: SLOW_PLANETS.includes(pname),
      transit_sign: tp.sign,
      transit_sign_cn: tp.sign_cn,
      transit_degree: tp.degree,
      transit_degree_in_sign: tp.degree_in_sign,
      transit_house: transitHouse,
      transit_nakshatra: tp.nakshatra,
      transit_nakshatra_pada: tp.nakshatra_pada,
      retrograde: tp.retrograde,
      speed: tp.speed,
      natal_sign: np?.sign || null,
      natal_house: np?.house || null,
      sign_changed: np ? (np.sign !== tp.sign) : false,
      conjunctions,
      aspects,
    });
  }

  return {
    all: allPlanets,
    slow: allPlanets.filter(p => p.is_slow),
    fast: allPlanets.filter(p => !p.is_slow),
  };
}

// ============================================================================
// Double Transit 分析（增强版）
// ============================================================================
export function computeDoubleTransit(transitPlanets, natalAscSign) {
  const ai = SIGNS.indexOf(natalAscSign);
  const results = [];

  for (let h = 1; h <= 12; h++) {
    const aspectedBy = [];
    for (const pname of ['Saturn', 'Jupiter']) {
      const tp = transitPlanets[pname];
      if (!tp) continue;
      const tHouse = ((SIGNS.indexOf(tp.sign) - ai + 12) % 12) + 1;
      const aspects = PLANET_ASPECTS[pname] || [7];
      for (const offset of aspects) {
        if (((tHouse - 1 + offset) % 12) + 1 === h) {
          aspectedBy.push({ planet: pname, planet_cn: PLANET_CN[pname], offset, from_house: tHouse });
        }
      }
    }
    if (aspectedBy.length >= 2) {
      results.push({ house: h, aspectedBy, significance: 'double_transit', desc: t('dt.locked').replace('{0}', h) });
    }
  }
  return results;
}

// ============================================================================
// Sade Sati 检测（增强版 — 含阶段详细信息）
// ============================================================================
export function checkSadeSati(natalMoonSign, transitPlanets) {
  const moonIdx = SIGNS.indexOf(natalMoonSign);
  const satIdx = SIGNS.indexOf(transitPlanets.Saturn?.sign || '');
  if (moonIdx < 0 || satIdx < 0) return null;

  const diff = ((satIdx - moonIdx + 12) % 12);
  let active = false, phase = 0, desc = '', detail = '';

  if (diff === 11) {
    active = true; phase = 1;
    desc = t('ss.phase1');
    detail = t('ss.detail1');
  } else if (diff === 0) {
    active = true; phase = 2;
    desc = t('ss.phase2');
    detail = t('ss.detail2');
  } else if (diff === 1) {
    active = true; phase = 3;
    desc = t('ss.phase3');
    detail = t('ss.detail3');
  } else if (diff === 10) {
    active = false; phase = 0;
    desc = t('ss.coming');
    detail = t('ss.detail.soon').replace('{0}', signName(SIGNS[(moonIdx - 1 + 12) % 12]));
  }

  // Saturn 在当前星座的度数（用于估算剩余时间）
  const satDegree = transitPlanets.Saturn?.degree_in_sign || 0;
  const satRetro = transitPlanets.Saturn?.retrograde || false;
  const approxYearsLeft = satRetro
    ? (satDegree / 30 * 2.5)
    : ((30 - satDegree) / 30 * 2.5);

  return {
    active,
    phase,
    desc,
    detail,
    natal_moon_sign: natalMoonSign,
    natal_moon_sign_cn: SIGNS_CN[natalMoonSign],
    saturn_sign: transitPlanets.Saturn?.sign,
    saturn_sign_cn: transitPlanets.Saturn?.sign_cn,
    saturn_degree_in_sign: Math.round(satDegree * 100) / 100,
    saturn_retrograde: satRetro,
    approx_remaining: t('ss.remaining').replace('{0}', (Math.round(approxYearsLeft * 10) / 10)),
  };
}

// ============================================================================
// Ashtakavarga Transit 评分（基于AV数据）
// ============================================================================
export function computeTransitAVScore(transitPlanets, natalAscSign, avData) {
  if (!avData || (!avData.bav && !avData.bav_raw)) return null;
  const ai = SIGNS.indexOf(natalAscSign);
  const scores = [];

  for (const pname of ALL_PLANETS) {
    const tp = transitPlanets[pname];
    if (!tp) continue;
    const tSignIdx = SIGNS.indexOf(tp.sign);
    const transitHouse = ((tSignIdx - ai + 12) % 12) + 1;

    // 从SAV获取该宫位的综合分数
    let savScore = null;
    if (avData.sav) {
      savScore = Array.isArray(avData.sav) ? avData.sav[tSignIdx] : (avData.sav?.scores?.[tSignIdx] ?? null);
    }

    // 从BAV获取各行星对该星座的贡献
    let bavContrib = {};
    const bavData = avData.bav_raw || avData.bav || {};
    if (bavData) {
      for (const [bPlanet, bavArr] of Object.entries(bavData)) {
        if (Array.isArray(bavArr) && bavArr[tSignIdx] !== undefined) {
          bavContrib[bPlanet] = bavArr[tSignIdx];
        }
      }
    }

    scores.push({
      planet: pname,
      planet_cn: PLANET_CN[pname],
      transit_sign: tp.sign,
      transit_sign_cn: tp.sign_cn,
      transit_house: transitHouse,
      sav_score: savScore,
      bav_contributions: bavContrib,
      transit_quality: savScore >= 30 ? 'favorable' : savScore >= 26 ? 'neutral' : 'challenging',
    });
  }
  return scores;
}

// ============================================================================
// Transit 行星对宫位影响摘要
// ============================================================================
export function computeTransitHouseImpact(transitPlanets, natalAscSign) {
  const ai = SIGNS.indexOf(natalAscSign);
  const houseImpacts = {};
  for (let h = 1; h <= 12; h++) {
    houseImpacts[h] = { transiting: [], aspected_by: [] };
  }

  // 记录各行星落在哪个宫
  for (const pname of ALL_PLANETS) {
    const tp = transitPlanets[pname];
    if (!tp) continue;
    const tSignIdx = SIGNS.indexOf(tp.sign);
    const house = ((tSignIdx - ai + 12) % 12) + 1;
    houseImpacts[house].transiting.push({
      planet: pname, planet_cn: PLANET_CN[pname],
      retrograde: tp.retrograde,
    });
  }

  // 记录行星相位对宫的影响
  for (const pname of ['Saturn', 'Jupiter', 'Mars']) {
    const tp = transitPlanets[pname];
    if (!tp) continue;
    const tSignIdx = SIGNS.indexOf(tp.sign);
    const fromHouse = ((tSignIdx - ai + 12) % 12) + 1;
    const aspects = PLANET_ASPECTS[pname] || [7];
    for (const offset of aspects) {
      const targetHouse = ((fromHouse - 1 + offset) % 12) + 1;
      houseImpacts[targetHouse].aspected_by.push({
        planet: pname, planet_cn: PLANET_CN[pname],
        from_house: fromHouse, aspect_type: t('transit.aspect.offset').replace('{0}', offset),
      });
    }
  }

  return houseImpacts;
}
