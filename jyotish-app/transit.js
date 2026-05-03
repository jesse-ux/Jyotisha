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
// Navamsa (D9) 星座计算工具
// ============================================================================
function navamsaSignIdx(lon) {
  const l = ((lon % 360) + 360) % 360;
  const si = Math.floor(l / 30);
  const d = l - si * 30;
  const ni = Math.floor(d / (30 / 9));
  const elStarts = [0, 9, 6, 3]; // Aries/Fire=0, Taurus/Earth=9, Gemini/Air=6, Cancer/Water=3
  return (elStarts[si % 4] + ni) % 12;
}

// ============================================================================
// PAC 检查: Position(同宫) / Aspect(相位) / Conjunction(合相≤10°)
// KN Rao Double Transit 核心: Saturn/Jupiter 通过 PAC 关联目标
// ============================================================================
function checkPAC(planetName, planetLon, targetLon, ascSignIdx) {
  const results = [];
  const pSignIdx = Math.floor((((planetLon % 360) + 360) % 360) / 30);
  const tSignIdx = Math.floor((((targetLon % 360) + 360) % 360) / 30);
  const pHouse = ((pSignIdx - ascSignIdx + 12) % 12) + 1;
  const tHouse = ((tSignIdx - ascSignIdx + 12) % 12) + 1;

  // P: Position — 同宫
  if (pHouse === tHouse) {
    results.push({ type: 'Position', desc: `同宫(${tHouse}宫)` });
  }

  // C: Conjunction — 合相 ≤10°
  let diff = Math.abs(planetLon - targetLon) % 360;
  if (diff > 180) diff = 360 - diff;
  if (diff <= 10) {
    results.push({ type: 'Conjunction', desc: `合相(${diff.toFixed(2)}°)` });
  }

  // A: Aspect — Graha Drishti
  const aspects = PLANET_ASPECTS[planetName] || [7];
  for (const offset of aspects) {
    if (((tHouse - pHouse + 12) % 12) === offset) {
      results.push({ type: 'Aspect', offset, desc: `${offset}宫相位` });
    }
  }

  return results;
}

// ============================================================================
// Double Transit PAC + D9 层（KN Rao 完整实现）
// 
// 核心逻辑:
// 1. D1 层: Saturn/Jupiter 通过 PAC 关联事件宫/宫主/LL/7L
// 2. D9 层: Saturn/Jupiter 通过 PAC 关联 D9 宫主/D9 Asc
// 3. 两者必须同时激活同一目标 → Double Transit 确认
//
// 精度: KN Rao 体系 110-115 星盘测试 97% 准确率（使用 D9 Navamsa）
// ============================================================================
export function computeDoubleTransitPAC(transitPlanets, natalPlanets, natalAscSign, natalAscDegree, eventHouse = 7) {
  const ai = SIGNS.indexOf(natalAscSign);
  const results = {
    event_house: eventHouse,
    d1: { jupiter: {}, saturn: {} },
    d9: { jupiter: {}, saturn: {} },
    double_transit: [],
    summary: '',
  };

  // --- 计算 D1 层敏感点 ---
  const eventSignIdx = (ai + eventHouse - 1) % 12;
  const eventSign = SIGNS[eventSignIdx];
  const eventLord = SIGN_LORDS[eventSign];
  const llName = SIGN_LORDS[natalAscSign]; // Lagna Lord
  const eventLordReverseIdx = (ai + 6) % 12; // 对宫 = (7宫-1)
  const oppositeLord = SIGN_LORDS[SIGNS[eventLordReverseIdx]]; // 7L (for marriage, eventHouse=7 → 7L)

  // 事件宫经度中点
  const eventHouseLon = (ai * 30 + eventHouse - 1) * 30 + 15;
  // LL 经度
  const llLon = natalPlanets[llName]?.degree ?? natalPlanets[llName]?.lon ?? 0;
  // 事件宫主经度
  const eventLordLon = natalPlanets[eventLord]?.degree ?? natalPlanets[eventLord]?.lon ?? 0;
  // 对宫主经度 (7L for marriage)
  const oppLordLon = natalPlanets[oppositeLord]?.degree ?? natalPlanets[oppositeLord]?.lon ?? 0;

  const d1Targets = {
    [`${eventHouse}宫`]: eventHouseLon,
    [`${eventLord}(宫主)`]: eventLordLon,
    [`${llName}(LL)`]: llLon,
    [`${oppositeLord}(对宫主)`]: oppLordLon,
  };

  // --- 计算 D9 层敏感点 ---
  const d9AscSignIdx = navamsaSignIdx(natalAscDegree);
  const d9AscSign = SIGNS[d9AscSignIdx];
  // D9 事件宫主: D9盘的 eventHouse 宫的星座主星
  const d9EventSignIdx = (d9AscSignIdx + eventHouse - 1) % 12;
  const d9EventSign = SIGNS[d9EventSignIdx];
  const d9EventLord = SIGN_LORDS[d9EventSign];
  // 宫主的 D9 星座（KN Rao 关键: 宫主 D9 星座是第三个目标）
  const eventLordD9SignIdx = navamsaSignIdx(eventLordLon);
  const eventLordD9Sign = SIGNS[eventLordD9SignIdx];
  // LL 的 D9 星座
  const llD9SignIdx = navamsaSignIdx(llLon);
  const llD9Sign = SIGNS[llD9SignIdx];

  // D9 层用 D9 Asc 作为参考点
  const d9EventHouseLon = (d9AscSignIdx * 30 + eventHouse - 1) * 30 + 15;
  const d9EventLordLon = natalPlanets[d9EventLord]?.degree ?? natalPlanets[d9EventLord]?.lon ?? 0;

  const d9Targets = {
    [`D9_${eventHouse}宫`]: d9EventHouseLon,
    [`D9_${eventLord}(宫主)`]: d9EventLordLon,
    [`${eventLord}_D9(${eventLordD9Sign})`]: eventLordD9SignIdx * 30 + 15,
    [`${llName}_D9(${llD9Sign})`]: llD9SignIdx * 30 + 15,
  };

  // --- 计算 Chandra Lagna 层敏感点（强制规范 v1.9.0） ---
  const moonLon = natalPlanets.Moon?.degree ?? 0;
  const moonSignIdx = Math.floor((moonLon % 360) / 30);
  const moonEventSignIdx = (moonSignIdx + eventHouse - 1) % 12;
  const moonEventSign = SIGNS[moonEventSignIdx];
  const moonEventLord = SIGN_LORDS[moonEventSign];
  const moonEventHouseLon = (moonSignIdx * 30 + eventHouse - 1) * 30 + 15;
  const moonEventLordLon = natalPlanets[moonEventLord]?.degree ?? 0;

  const clTargets = {
    [`CL_${eventHouse}宫(${moonEventSign})`]: moonEventHouseLon,
    [`CL_${moonEventLord}(宫主)`]: moonEventLordLon,
  };

  // --- 检查 Jupiter 和 Saturn 的 PAC ---
  results.cl = { jupiter: {}, saturn: {} }; // Chandra Lagna 层
  for (const transitPlanet of ['Jupiter', 'Saturn']) {
    const tp = transitPlanets[transitPlanet];
    if (!tp) continue;
    const tpLon = tp.degree;
    const layer = transitPlanet === 'Jupiter' ? 'jupiter' : 'saturn';

    // D1 层 PAC 检查
    for (const [tName, tLon] of Object.entries(d1Targets)) {
      const pac = checkPAC(transitPlanet, tpLon, tLon, ai);
      if (pac.length > 0) {
        results.d1[layer][tName] = pac;
      }
    }

    // D9 层 PAC 检查 (用 D9 Asc 作为参考点)
    for (const [tName, tLon] of Object.entries(d9Targets)) {
      const pac = checkPAC(transitPlanet, tpLon, tLon, d9AscSignIdx);
      if (pac.length > 0) {
        results.d9[layer][tName] = pac;
      }
    }

    // Chandra Lagna 层 PAC 检查（强制规范：必须从月亮看过境）
    for (const [tName, tLon] of Object.entries(clTargets)) {
      const pac = checkPAC(transitPlanet, tpLon, tLon, moonSignIdx);
      if (pac.length > 0) {
        results.cl[layer][tName] = pac;
      }
    }
  }

  // --- Double Transit 判定 ---
  const jupD1Targets = new Set(Object.keys(results.d1.jupiter));
  const satD1Targets = new Set(Object.keys(results.d1.saturn));
  const jupD9Targets = new Set(Object.keys(results.d9.jupiter));
  const satD9Targets = new Set(Object.keys(results.d9.saturn));
  const jupCLTargets = new Set(Object.keys(results.cl.jupiter));
  const satCLTargets = new Set(Object.keys(results.cl.saturn));

  // D1 层 Double Transit
  const d1Overlap = [...jupD1Targets].filter(t => satD1Targets.has(t));
  for (const t of d1Overlap) {
    results.double_transit.push({
      layer: 'D1', target: t,
      jupiter_pac: results.d1.jupiter[t],
      saturn_pac: results.d1.saturn[t],
      strength: 'strong',
    });
  }

  // D9 层 Double Transit
  const d9Overlap = [...jupD9Targets].filter(t => satD9Targets.has(t));
  for (const t of d9Overlap) {
    results.double_transit.push({
      layer: 'D9', target: t,
      jupiter_pac: results.d9.jupiter[t],
      saturn_pac: results.d9.saturn[t],
      strength: 'strong',
    });
  }

  // Chandra Lagna 层 Double Transit
  const clOverlap = [...jupCLTargets].filter(t => satCLTargets.has(t));
  for (const t of clOverlap) {
    results.double_transit.push({
      layer: 'CL', target: t,
      jupiter_pac: results.cl.jupiter[t],
      saturn_pac: results.cl.saturn[t],
      strength: 'strong',
    });
  }

  // 跨层 Double Transit (Jupiter D1 + Saturn D9 或反之，激活同一主题)
  // 例如 Jupiter PAC D1 7宫 + Saturn PAC D9 7宫 = 间接 Double Transit
  for (const d1t of jupD1Targets) {
    for (const d9t of satD9Targets) {
      if (d1t.replace(/[^\d]/g, '') === d9t.replace(/[^\d]/g, '') || 
          d1t.includes(eventLord) && d9t.includes(eventLord)) {
        results.double_transit.push({
          layer: 'D1+D9', target: `Jupiter(D1)${d1t} + Saturn(D9)${d9t}`,
          jupiter_pac: results.d1.jupiter[d1t],
          saturn_pac: results.d9.saturn[d9t],
          strength: 'moderate',
        });
      }
    }
  }
  for (const d1t of satD1Targets) {
    for (const d9t of jupD9Targets) {
      if (d1t.replace(/[^\d]/g, '') === d9t.replace(/[^\d]/g, '') || 
          d1t.includes(eventLord) && d9t.includes(eventLord)) {
        results.double_transit.push({
          layer: 'D1+D9', target: `Saturn(D1)${d1t} + Jupiter(D9)${d9t}`,
          jupiter_pac: results.d9.jupiter[d9t],
          saturn_pac: results.d1.saturn[d1t],
          strength: 'moderate',
        });
      }
    }
  }

  // --- Summary ---
  const d1Active = d1Overlap.length > 0;
  const d9Active = d9Overlap.length > 0;
  const clActive = clOverlap.length > 0;
  const crossActive = results.double_transit.filter(d => d.layer === 'D1+D9').length > 0;

  const activeLayers = [d1Active && 'D1', d9Active && 'D9', clActive && 'CL'].filter(Boolean);
  if (activeLayers.length >= 2) {
    results.summary = `✅ Double Transit PAC 确认: ${activeLayers.join('+')} 多层激活${eventHouse}宫主题`;
  } else if (d1Active) {
    results.summary = `⚠️ D1 层 Double Transit 激活，D9/CL 层未确认`;
  } else if (d9Active) {
    results.summary = `⚠️ D9 层 Double Transit 激活，D1/CL 层未确认`;
  } else if (clActive) {
    results.summary = `⚠️ Chandra Lagna 层 Double Transit 激活，D1/D9 未确认`;
  } else if (crossActive) {
    results.summary = `⚠️ 跨层间接 Double Transit (D1+D9)，需结合 Dasha 确认`;
  } else {
    results.summary = `❌ 无 Double Transit PAC 激活`;
  }

  results.stats = {
    d1_jupiter_targets: [...jupD1Targets],
    d1_saturn_targets: [...satD1Targets],
    d9_jupiter_targets: [...jupD9Targets],
    d9_saturn_targets: [...satD9Targets],
    cl_jupiter_targets: [...jupCLTargets],
    cl_saturn_targets: [...satCLTargets],
    d1_overlap: d1Overlap,
    d9_overlap: d9Overlap,
    cl_overlap: clOverlap,
    chandra_lagna: SIGNS[moonSignIdx],
  };

  return results;
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

// ============================================================================
// Transit LL/7L 连接 + 互换（Parivartana）
//
// P5: Transit LL PAC natal 7L / Transit 7L PAC natal LL (98%命中率)
// P8: Transit LL 过 7H 或 Transit 7L 过 Lagna (59%命中率)
// + Parivartana 互换检测: Transit LL 在 7L 星座 且 Transit 7L 在 LL 星座
// ============================================================================
export function computeTransitLL7L(transitPlanets, natalPlanets, natalAscSign) {
  const ai = SIGNS.indexOf(natalAscSign);
  const llName = SIGN_LORDS[natalAscSign]; // Lagna Lord
  const sevenSign = SIGNS[(ai + 6) % 12]; // 7宫星座
  const sevenLord = SIGN_LORDS[sevenSign]; // 7L

  const result = {
    lagna_lord: llName,
    seventh_lord: sevenLord,
    p5: { hit: false, details: [] },
    p8: { hit: false, details: [] },
    parivartana: { hit: false, details: [] },
  };

  // Transit LL/7L 位置
  const tLL = transitPlanets[llName];
  const t7L = transitPlanets[sevenLord];
  if (!tLL || !t7L) return result;

  const nLLLon = natalPlanets[llName]?.degree ?? 0;
  const n7LLon = natalPlanets[sevenLord]?.degree ?? 0;

  // --- P5: Transit LL PAC natal 7L / Transit 7L PAC natal LL ---
  const pac1 = checkPAC(llName, tLL.degree, n7LLon, ai);
  if (pac1.length > 0) {
    result.p5.hit = true;
    result.p5.details.push({
      direction: `Transit ${llName} → natal ${sevenLord}`,
      connections: pac1,
    });
  }

  const pac2 = checkPAC(sevenLord, t7L.degree, nLLLon, ai);
  if (pac2.length > 0) {
    result.p5.hit = true;
    result.p5.details.push({
      direction: `Transit ${sevenLord} → natal ${llName}`,
      connections: pac2,
    });
  }

  // --- P8: Transit LL 过 7H 或 Transit 7L 过 Lagna ---
  const tLLHouse = ((SIGNS.indexOf(tLL.sign) - ai + 12) % 12) + 1;
  const t7LHouse = ((SIGNS.indexOf(t7L.sign) - ai + 12) % 12) + 1;

  if (tLLHouse === 7) {
    result.p8.hit = true;
    result.p8.details.push(`Transit ${llName}(${tLL.sign})在7H`);
  }
  if (t7LHouse === 1) {
    result.p8.hit = true;
    result.p8.details.push(`Transit ${sevenLord}(${t7L.sign})在Lagna`);
  }

  // --- Parivartana 互换: Transit LL 在 natal 7L 星座 且 Transit 7L 在 natal LL 星座 ---
  const nLLSign = SIGNS[Math.floor((nLLLon % 360) / 30)];
  const n7LSign = SIGNS[Math.floor((n7LLon % 360) / 30)];
  const tLLIn7LSign = tLL.sign === n7LSign;
  const t7LInLLSign = t7L.sign === nLLSign;

  if (tLLIn7LSign && t7LInLLSign) {
    result.parivartana.hit = true;
    result.parivartana.details.push(
      `完整互换: Transit ${llName}在${n7LSign}(natal ${sevenLord}) + Transit ${sevenLord}在${nLLSign}(natal ${llName})`
    );
  } else if (tLLIn7LSign) {
    result.parivartana.details.push(`部分: Transit ${llName}在${n7LSign}(natal ${sevenLord}座)`);
  } else if (t7LInLLSign) {
    result.parivartana.details.push(`部分: Transit ${sevenLord}在${nLLSign}(natal ${llName}座)`);
  }

  return result;
}

// ============================================================================
// 行星聚集检测（Lagna/7H 聚集 + Transit 聚集）
//
// P7: 本命盘行星聚集 Lagna/7H (70%命中率)
// + Transit 时行星聚集事件宫 (扩展)
// ============================================================================
export function computePlanetaryCongregation(natalPlanets, natalAscSign, transitPlanets = null, eventHouse = 7) {
  const ai = SIGNS.indexOf(natalAscSign);
  const result = {
    natal: { lagna: [], house_7: [], [`${eventHouse}宫`]: [] },
    transit: null,
    summary: '',
  };

  // --- 本命盘聚集 ---
  for (const [pname, pdata] of Object.entries(natalPlanets)) {
    if (pdata.error || pdata.sign === undefined) continue;
    const pSignIdx = SIGNS.indexOf(pdata.sign);
    const house = ((pSignIdx - ai + 12) % 12) + 1;
    if (house === 1) result.natal.lagna.push(pname);
    if (house === 7) result.natal.house_7.push(pname);
    if (house === eventHouse) result.natal[`${eventHouse}宫`].push(pname);
  }

  // --- Transit 聚集 ---
  if (transitPlanets) {
    result.transit = {};
    for (let h = 1; h <= 12; h++) result.transit[h] = [];
    for (const pname of ALL_PLANETS) {
      const tp = transitPlanets[pname];
      if (!tp) continue;
      const tSignIdx = SIGNS.indexOf(tp.sign);
      const house = ((tSignIdx - ai + 12) % 12) + 1;
      result.transit[house].push(pname);
    }
  }

  // --- 判定 ---
  const lagnaCount = result.natal.lagna.length;
  const h7Count = result.natal.house_7.length;
  const eventCount = result.natal[`${eventHouse}宫`].length;

  const flags = [];
  // Sun 在 Lagna 或 ≥3 颗行星在 Lagna
  if (result.natal.lagna.includes('Sun') || lagnaCount >= 3) {
    flags.push(`Lagna聚集: ${result.natal.lagna.join(',')}(${lagnaCount})`);
  }
  // Sun 在 7H 或 ≥3 颗行星在 7H
  if (result.natal.house_7.includes('Sun') || h7Count >= 3) {
    flags.push(`7H聚集: ${result.natal.house_7.join(',')}(${h7Count})`);
  }
  // Transit 聚集事件宫 ≥2 颗慢行星
  if (result.transit) {
    const tEventPlanets = result.transit[eventHouse] || [];
    const tSlowInEvent = tEventPlanets.filter(p => SLOW_PLANETS.includes(p));
    if (tSlowInEvent.length >= 2) {
      flags.push(`Transit ${eventHouse}宫慢行星聚集: ${tSlowInEvent.join(',')}`);
    }
  }

  result.summary = flags.length > 0 ? flags.join(' | ') : '无显著聚集';
  result.flags = flags;
  result.hit = flags.length > 0;

  return result;
}

// ============================================================================
// Vivah Saham 计算 + Transit 激活检测
//
// Vivah Saham = norm(Venus - Saturn + Asc) — 度数级精确计算
// Transit 激活: Jupiter/Saturn PAC 到 Vivah Saham 经度
// ============================================================================
export function computeVivahSaham(natalPlanets, natalAscDegree, transitPlanets = null) {
  const venusLon = natalPlanets.Venus?.degree ?? 0;
  const saturnLon = natalPlanets.Saturn?.degree ?? 0;
  const ascLon = natalAscDegree;

  // Vivah Saham = norm(Venus - Saturn + Asc)
  let sahamsLon = ((venusLon - saturnLon + ascLon) % 360 + 360) % 360;
  const sahamsSignIdx = Math.floor(sahamsLon / 30);
  const sahamsSign = SIGNS[sahamsSignIdx];
  const sahamsDegInSign = sahamsLon - sahamsSignIdx * 30;
  const sahamsNakIdx = Math.floor(sahamsLon / NAKSPAN);
  const sahamsPada = Math.floor((sahamsLon % NAKSPAN) / (NAKSPAN / 4)) + 1;

  const result = {
    vivah_saham: {
      longitude: Math.round(sahamsLon * 10000) / 10000,
      sign: sahamsSign,
      sign_cn: SIGNS_CN[sahamsSign],
      degree_in_sign: Math.round(sahamsDegInSign * 10000) / 10000,
      nakshatra: NAKSHATRA_LIST[sahamsNakIdx % 27]?.name,
      pada: sahamsPada,
    },
    formula: `norm(${venusLon.toFixed(2)}° Venus - ${saturnLon.toFixed(2)}° Saturn + ${ascLon.toFixed(2)}° Asc)`,
    transit_activation: null,
  };

  // --- Transit 激活检测 ---
  if (transitPlanets) {
    const ascSignIdx = Math.floor((ascLon % 360) / 30);
    result.transit_activation = {
      jupiter: [],
      saturn: [],
      double_activation: false,
    };

    // Jupiter PAC 到 Vivah Saham
    if (transitPlanets.Jupiter) {
      const jupPAC = checkPAC('Jupiter', transitPlanets.Jupiter.degree, sahamsLon, ascSignIdx);
      if (jupPAC.length > 0) {
        result.transit_activation.jupiter = jupPAC;
      }
    }

    // Saturn PAC 到 Vivah Saham
    if (transitPlanets.Saturn) {
      const satPAC = checkPAC('Saturn', transitPlanets.Saturn.degree, sahamsLon, ascSignIdx);
      if (satPAC.length > 0) {
        result.transit_activation.saturn = satPAC;
      }
    }

    // 双星激活
    if (result.transit_activation.jupiter.length > 0 && result.transit_activation.saturn.length > 0) {
      result.transit_activation.double_activation = true;
    }

    // Venus transit 过 Saham 星座（辅助信号）
    if (transitPlanets.Venus) {
      const tVenusSign = transitPlanets.Venus.sign;
      if (tVenusSign === sahamsSign) {
        result.transit_activation.venus_in_saham_sign = true;
      }
    }
  }

  return result;
}
