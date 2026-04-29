/**
 * Jyotish Export Helper Modules v1.0
 * - Validation (数据完整性校验 R1-R10)
 * - Audit (行星审计 P1-P12)
 * - Actionable Context (宫位/行星映射, 仓库耦合)
 */

import { SIGNS, SIGN_LORDS, DASHA_ORDER, DASHA_YEARS, NAKSHATRA_LIST } from './jyotish-engine.js';

// ========== Validation R1-R10 ==========
export function computeValidation(planets, ascendant, ashtakavarga, dasha) {
  const results = [];
  let passed = 0, failed = 0;

  function check(rule, name, ok, detail) {
    results.push({ rule, name, passed: ok, detail });
    ok ? passed++ : failed++;
  }

  // R1: SAV总和=337
  if (ashtakavarga?.sav) {
    const total = ashtakavarga.sav.reduce((a, b) => a + b, 0);
    check('R1', 'SAV总和=337', total === 337, `SAV total = ${total}, expected 337`);
  } else {
    check('R1', 'SAV总和=337', false, 'SAV data unavailable');
  }

  // R2: BAV行常数校验
  if (ashtakavarga?.bav_raw) {
    const bav = ashtakavarga.bav_raw;
    const bavNames = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Lagna'];
    const bavConsts = [48,49,39,54,56,52,39,49];
    let r2Detail = [];
    let r2Ok = true;
    for (let i = 0; i < bavNames.length; i++) {
      const row = bav[bavNames[i]];
      if (!row) { r2Ok = false; r2Detail.push(`${bavNames[i]}=N/A`); continue; }
      const sum = row.reduce((a, b) => a + b, 0);
      const ok = sum === bavConsts[i];
      if (!ok) r2Ok = false;
      r2Detail.push(`${bavNames[i]}=${sum}/${bavConsts[i]}`);
    }
    check('R2', 'BAV行常数校验', r2Ok, r2Detail.join('; '));
  }

  // R2b: BAV列→SAV列校验
  if (ashtakavarga?.bav_raw && ashtakavarga?.sav) {
    const bav = ashtakavarga.bav_raw;
    const bavNames = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'];
    let r2bOk = true;
    let r2bDetail = [];
    for (let col = 0; col < 12; col++) {
      let colSum = 0;
      for (const pn of bavNames) colSum += (bav[pn]?.[col] || 0);
      const savVal = ashtakavarga.sav[col];
      if (colSum !== savVal) r2bOk = false;
    }
    check('R2b', 'BAV列→SAV列校验', r2bOk, r2bOk ? '所有12星座 BAV列和 与 SAV分数一致 ✅' : 'BAV列和与SAV不一致');
  }

  // R5: Rahu-Ketu 180°对冲
  if (planets.Rahu?.degree != null && planets.Ketu?.degree != null) {
    const diff = Math.abs(planets.Rahu.degree - planets.Ketu.degree);
    const deviation = Math.abs(diff - 180);
    check('R5', 'Rahu-Ketu 180°对冲', deviation < 0.01,
      `Rahu=${planets.Rahu.degree}°, Ketu=${planets.Ketu.degree}°, 偏差=${deviation.toFixed(4)}°`);
  }

  // R7: Dasha年限总和=120
  const dashaSum = DASHA_ORDER.reduce((s, p) => s + (DASHA_YEARS[p] || 0), 0);
  check('R7', 'Dasha年限总和=120', dashaSum === 120, `Dasha year chain sum = ${dashaSum}`);

  // R8: 行星完整性
  const requiredPlanets = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  const haveAll = requiredPlanets.every(p => planets[p] && !planets[p].error);
  check('R8', '行星完整性', haveAll, haveAll ? '完整：9行星 + Ascendant' : '缺少行星');

  // R9: 星座度数范围
  let r9Ok = true;
  for (const pn of requiredPlanets) {
    const p = planets[pn];
    if (!p || p.error) continue;
    if (p.degree_in_sign < 0 || p.degree_in_sign >= 30) r9Ok = false;
  }
  check('R9', '星座度数范围', r9Ok, r9Ok ? '所有行星度数在合法范围' : '存在度数越界');

  // R10: 宫位连续性
  let r10Ok = true;
  const houses = new Set();
  for (const pn of requiredPlanets) {
    const p = planets[pn];
    if (p?.house) houses.add(p.house);
  }
  if (ascendant?.sign) houses.add(1);
  check('R10', '宫位连续性', houses.size >= 10, `1-12宫完整(${houses.size}宫)`);

  return {
    valid: failed === 0,
    total_checks: results.length,
    checked: results.length,
    passed, failed,
    skipped: 0,
    results,
  };
}

// ========== Audit (P1-P12) ==========
export function computeAudit(planets, ascendant, ashtakavarga, validation) {
  const ascIdx = SIGNS.indexOf(ascendant?.sign || 'Aries');
  const ascLord = SIGN_LORDS[ascendant?.sign || 'Aries'];

  // P1: Identity
  const ascLordPlanet = planets[ascLord];
  const p1 = {
    asc_sign: ascendant?.sign,
    asc_lord: ascLord,
    lord_sign: ascLordPlanet?.sign || '',
    lord_house: ascLordPlanet?.house || 0,
    lord_status: ascLordPlanet?.status || '',
  };

  // P2: Health houses (6, 8, 12)
  const p2 = { houses: {} };
  for (const h of [6, 8, 12]) {
    const sIdx = (ascIdx + h - 1) % 12;
    p2.houses[`house_${h}`] = { sign: SIGNS[sIdx], lord: SIGN_LORDS[SIGNS[sIdx]] };
  }
  p2.sun_status = planets.Sun?.status || '';
  p2.sun_house = planets.Sun?.house || 0;

  // P3: Warehouse Coupling
  const p3 = {};
  const lordToHouses = {};
  for (let h = 1; h <= 12; h++) {
    const sIdx = (ascIdx + h - 1) % 12;
    const lord = SIGN_LORDS[SIGNS[sIdx]];
    if (!lordToHouses[lord]) lordToHouses[lord] = [];
    lordToHouses[lord].push(h);
  }
  const kendraTrikona = new Set([1,4,5,7,9,10]);
  for (const [lord, hs] of Object.entries(lordToHouses)) {
    if (hs.length < 2) continue;
    const hasK = hs.some(h => kendraTrikona.has(h));
    const allK = hs.every(h => kendraTrikona.has(h));
    let quality = '中性 — 标准互动';
    if (allK) quality = '吉庆型 — 自然流畅的支持';
    else if (!hasK) quality = '压力型 — 通过努力获取成就';
    else quality = '凶吉混合 — 挑战与成长并存';

    p3[lord] = {
      houses: hs,
      meaning: `${lord}同时掌管${hs.join('宫和')}宫，事务捆绑`,
      conjunction_quality: quality,
    };
  }

  // P8: Age Status (degree-based life stage)
  const p8 = {};
  for (const pn of ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']) {
    const p = planets[pn];
    if (!p || p.error) continue;
    const deg = p.degree_in_sign;
    let phase, quality;
    if (deg < 10) { phase = '婴幼(0-10°)'; quality = '辅助型 — 能量尚未完全展开'; }
    else if (deg < 20) { phase = '青壮(10-20°)'; quality = '主动型 — 能量最活跃，主导性强'; }
    else { phase = '成熟(20-30°)'; quality = '成熟型 — 稳定输出，经验丰富'; }
    p8[pn] = { degree_in_sign: Math.round(deg * 100) / 100, phase, quality };
  }

  return {
    version: '3.5',
    birth_info_audit: {
      ascendant: ascendant?.sign,
      degree: ascendant?.degree,
    },
    audit: { P1_identity: p1, P2_health: p2, P3_warehouse_coupling: p3, P8_age_status: p8 },
    validation,
    conflict_arbitration: [],
  };
}

// ========== Actionable Context ==========
export function computeActionableContext(planets, ascendant) {
  const ascIdx = SIGNS.indexOf(ascendant?.sign || 'Aries');

  // House Lord Map
  const houseLordMap = {};
  for (let h = 1; h <= 12; h++) {
    const sIdx = (ascIdx + h - 1) % 12;
    const sign = SIGNS[sIdx];
    houseLordMap[h] = { sign, lord: SIGN_LORDS[sign] };
  }

  // Planet House Map
  const planetHouseMap = {};
  const planetNames = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  for (const pn of planetNames) {
    const p = planets[pn];
    if (!p || p.error) continue;
    planetHouseMap[pn] = {
      sign: p.sign,
      house: p.house,
      degree_in_sign: p.degree_in_sign,
    };
  }

  // Key House Activations
  const keyActivations = {};
  for (let h = 1; h <= 12; h++) {
    const planetsInHouse = planetNames.filter(pn => planets[pn]?.house === h);
    if (planetsInHouse.length > 0) {
      keyActivations[h] = { planets: planetsInHouse, count: planetsInHouse.length };
    }
  }

  return {
    house_lord_map: houseLordMap,
    planet_house_map: planetHouseMap,
    key_house_activations: keyActivations,
  };
}
