/**
 * Jyotish Advanced Calculations v1.0
 * 高级计算模块: Karaka, Arudha, Varga, Ashtakavarga, Shadbala, Tithi, Combustion, Dasha-3级
 */

import {
  SIGNS, SIGNS_CN, SIGN_LORDS, PLANET_CN, NAKSHATRA_LIST, DASHA_ORDER, DASHA_YEARS,
  EXALTATION, DEBILITATION, PLANET_RELATIONS
} from './jyotish-engine.js';

// ========== 常量 ==========

export const COMBUSTION_RANGE = { Moon:12, Mars:17, Mercury:14, Jupiter:11, Venus:10, Saturn:15 };

export const SHADBALA_REQUIRED = { Sun:5, Moon:6, Mars:5, Mercury:7, Jupiter:6.5, Venus:5.5, Saturn:5 };

export const VARGA_DEFS = [
  {id:'D1',name:'Rasi',cn:'本命盘',d:1},{id:'D2',name:'Hora',cn:'财富盘',d:2},
  {id:'D3',name:'Drekkana',cn:'兄弟盘',d:3},{id:'D4',name:'Chaturthamsa',cn:'房产盘',d:4},
  {id:'D7',name:'Saptamsa',cn:'子女盘',d:7},{id:'D9',name:'Navamsa',cn:'九分盘',d:9},
  {id:'D10',name:'Dasamsa',cn:'事业盘',d:10},{id:'D12',name:'Dwadasamsa',cn:'父母盘',d:12},
  {id:'D16',name:'Shodasamsa',cn:'车辆盘',d:16},{id:'D20',name:'Vimsamsa',cn:'灵性盘',d:20},
  {id:'D24',name:'Chaturvimsamsa',cn:'教育盘',d:24},{id:'D30',name:'Trimsamsa',cn:'厄运盘',d:30},
  {id:'D40',name:'Khavedamsa',cn:'吉凶盘',d:40},{id:'D45',name:'Akshavedamsa',cn:'总体盘',d:45},
  {id:'D60',name:'Shastyamsa',cn:'业力盘',d:60},
];

export const TITHI_CN = [
  '初一(Pratipat)','初二(Dvitiya)','初三(Tritiya)','初四(Chaturthi)','初五(Panchami)',
  '初六(Shashthi)','初七(Saptami)','初八(Ashtami)','初九(Navami)','初十(Dashami)',
  '十一(Ekadashi)','十二(Dvadashi)','十三(Trayodashi)','十四(Chaturdashi)','满月/新月'
];

export const SUN_MOON_YOGAS = [
  'Vishkambha','Priti','Ayushman','Saubhagya','Shobhana','Atiganda','Sukarma','Dhriti',
  'Shula','Ganda','Vriddhi','Dhruva','Vyaghata','Harshana','Vajra','Siddhi','Vyatipata',
  'Variyan','Parigha','Shiva','Siddha','Sadhya','Shubha','Shukla','Brahma','Indra','Vaidhriti'
];

// ========== Combustion ==========

export function computeCombustion(planets) {
  const sunDeg = planets.Sun?.degree;
  if (!sunDeg) return;
  for (const pn of ['Moon','Mars','Mercury','Jupiter','Venus','Saturn']) {
    const p = planets[pn]; if (!p || p.error) continue;
    const dist = Math.min(Math.abs(p.degree-sunDeg), 360-Math.abs(p.degree-sunDeg));
    if (dist < (COMBUSTION_RANGE[pn]||15)) { p.combust=true; p.combust_degree=Math.round(dist*100)/100; }
  }
}

// ========== Karaka ==========

export function computeKaraka(planets) {
  const seven = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'];
  // Fix: sort by degree_in_sign (0-30°), NOT absolute longitude (0-360°)
  const sorted = seven.filter(p=>planets[p]&&!planets[p].error).map(p=>({name:p,degree:planets[p].degree_in_sign})).sort((a,b)=>b.degree-a.degree);
  const L7=['AK','AmK','BK','MK','PK','GK','DK'];
  const CN7={AK:'Atmakaraka 自我灵魂',AmK:'Amatyakaraka 事业顾问',BK:'Bhratrikaraka 兄弟姐妹',MK:'Matrikaraka 母亲',PK:'Putrakaraka 子女',GK:'Gnatikaraka 障碍冲突',DK:'Darakaraka 配偶'};
  const k7={};
  for(let i=0;i<Math.min(sorted.length,7);i++){
    k7[L7[i]]={planet:sorted[i].name,planet_cn:PLANET_CN[sorted[i].name],degree:sorted[i].degree,label_cn:CN7[L7[i]],sign:planets[sorted[i].name]?.sign,sign_cn:planets[sorted[i].name]?.sign_cn,house:planets[sorted[i].name]?.house};
  }
  // 8-Karaka — Rahu uses reverse degree_in_sign: 30 - degree_in_sign
  const rahuK=planets.Rahu&&!planets.Rahu.error?[{name:'Rahu',degree:(30-planets.Rahu.degree_in_sign)%30}]:[];
  const s8=seven.filter(p=>planets[p]&&!planets[p].error).map(p=>({name:p,degree:planets[p].degree_in_sign})).concat(rahuK).sort((a,b)=>b.degree-a.degree);
  const L8=['AK','AmK','BK','MK','PK','GK','DK','PiK'];
  const CN8={...CN7,PiK:'Pitrukaraka 父亲'};
  const k8={};
  for(let i=0;i<Math.min(s8.length,8);i++){
    k8[L8[i]]={planet:s8[i].name,planet_cn:PLANET_CN[s8[i].name],degree:s8[i].degree,label_cn:CN8[L8[i]],sign:planets[s8[i].name]?.sign,sign_cn:planets[s8[i].name]?.sign_cn,house:planets[s8[i].name]?.house};
  }
  return {karaka7:k7,karaka8:k8};
}

// ========== Arudha ==========

export function computeArudha(planets, ascSign) {
  const ai=SIGNS.indexOf(ascSign); const padas={};
  function calc(h){
    const si=(ai+h-1)%12; const s=SIGNS[si]; const lord=SIGN_LORDS[s];
    const lp=planets[lord]; if(!lp||lp.error)return null;
    const li=SIGNS.indexOf(lp.sign); let cnt=((li-si+12)%12)+1;
    if(cnt===h)cnt=((cnt+9)%12)+1; else if(cnt===((h+6-1)%12+1))cnt=((cnt+9)%12)+1;
    const pi=(si+cnt-1)%12;
    return{house:h,sign:SIGNS[pi],sign_cn:SIGNS_CN[SIGNS[pi]],pada_house:((pi-ai+12)%12)+1,lord,lord_cn:PLANET_CN[lord]};
  }
  const al=calc(1); if(al){al.label='Arudha Lagna 社会形象'; padas.AL=al;}
  for(let h=2;h<=12;h++){const p=calc(h);if(p)padas[`A${h}`]=p;}
  if(padas.A12)padas.UL={...padas.A12,label:'Upapada Lagna 配偶征象'};
  return padas;
}

// ========== Varga ==========

// BPHS 分盘映射：星座索引 si 的第 pi 份 → 目标星座索引
// 奇数星座(si%2==0): Aries,Gemini,Leo,Libra,Sagittarius,Aquarius
// 偶数星座(si%2==1): Taurus,Cancer,Virgo,Scorpio,Capricorn,Pisces
function _vargaMap(si, pi, d) {
  const o = si % 2 === 0; // 奇数星座: Aries(0),Gemini(2)...
  switch(d) {
    case 2: return pi === 0 ? (o ? 4 : 3) : (o ? 3 : 4);
    case 3: return o ? (si + pi * 4) % 12 : (si + 8 + pi * 4) % 12;
    case 4: return o ? (si + pi) % 12 : (si + 8 + pi) % 12;
    case 7: return o ? (si + pi) % 12 : (si + 6 + pi) % 12;
    case 9: { const el = [0,9,6,3]; return (el[si % 4] + pi) % 12; }
    case 10: return o ? (si + pi) % 12 : (si + 8 + pi) % 12;
    case 12: return (si + pi) % 12;
    case 16: return ((o ? 0 : 1) + pi) % 12;
    case 20: return ((o ? 0 : 8) + pi) % 12;
    case 24: return ((o ? 4 : 3) + pi) % 12;
    case 27: return ((o ? 0 : 6) + pi) % 12;
    case 30: {
      if (o) { return pi<5?0:pi<10?10:pi<18?8:pi<25?2:6; }
      else { return pi<5?1:pi<12?5:pi<20?9:pi<25?7:11; }
    }
    case 40: return ((o ? 0 : 6) + pi) % 12;
    case 45: return ((o ? 0 : 6) + pi) % 12;
    case 60: return o ? (si + pi) % 12 : (si + 1 + pi) % 12;
    default: return (si + pi) % 12;
  }
}

export function computeVarga(planets, vargaId) {
  const def=VARGA_DEFS.find(v=>v.id===vargaId); if(!def)return null;
  const{id,name,cn,d}=def;
  if(d===1){const r={};for(const[pn,pi]of Object.entries(planets)){if(pi.error)continue;r[pn]={sign:pi.sign,sign_cn:pi.sign_cn,house:pi.house};}return{id,name,name_cn:cn,planets:r};}
  const varga={};
  for(const[pn,pi]of Object.entries(planets)){
    if(pi.error)continue;
    const deg=pi.degree_in_sign; const si=SIGNS.indexOf(pi.sign);
    const sw=30/d; const seg=Math.floor(deg/sw);
    const vi=_vargaMap(si, seg, d);
    varga[pn]={sign:SIGNS[vi],sign_cn:SIGNS_CN[SIGNS[vi]],house:pi.house};
  }
  return{id,name,name_cn:cn,planets:varga};
}

export function computeAllVargas(planets){const r={};for(const v of VARGA_DEFS)r[v.id]=computeVarga(planets,v.id);return r;}

// ========== Ashtakavarga (BPHS Standard v2.0) ==========
// BAV_TABLE[planet][source] = favorable house numbers counted from source's sign
// SAV total = 337 (cosmic constant): 48+49+39+54+56+52+39

const BAV_TABLE = {
  Sun: {
    Sun:[1,2,4,7,8,9,10,11], Moon:[3,6,10,11], Mars:[1,2,4,7,8,9,10,11],
    Mercury:[3,5,6,9,10,11,12], Jupiter:[5,6,9,11], Venus:[6,7,12],
    Saturn:[1,2,4,7,8,9,10,11], Lagna:[3,4,6,10,11,12]
  },
  Moon: {
    Sun:[3,6,7,8,10,11], Moon:[1,3,6,7,10,11], Mars:[2,3,5,6,9,10,11],
    Mercury:[1,3,4,5,7,8,10,11], Jupiter:[1,4,7,8,10,11],
    Venus:[3,4,5,7,9,10,11], Saturn:[3,5,6,11], Lagna:[3,6,10,11,12]
  },
  Mars: {
    Sun:[3,5,6,10,11], Moon:[3,6,11], Mars:[1,2,4,7,8,10,11],
    Mercury:[3,5,6,11], Jupiter:[6,10,11,12], Venus:[6,8,11,12],
    Saturn:[1,4,7,8,9,10,11], Lagna:[1,3,6,10,11]
  },
  Mercury: {
    Sun:[5,6,9,11,12], Moon:[2,4,6,8,10,11], Mars:[1,2,4,7,8,9,10,11],
    Mercury:[1,3,5,6,9,10,11,12], Jupiter:[6,8,11,12],
    Venus:[1,2,3,4,5,8,9,11], Saturn:[1,2,4,7,8,9,10,11], Lagna:[1,2,4,6,8,10,11]
  },
  Jupiter: {
    Sun:[1,2,3,4,7,8,9,10,11], Moon:[2,5,7,9,11], Mars:[1,2,4,7,8,10,11],
    Mercury:[1,2,4,5,6,9,10,11], Jupiter:[1,2,3,4,7,8,10,11],
    Venus:[2,5,6,9,10,11], Saturn:[3,5,6,12], Lagna:[1,2,4,5,6,7,9,10,11]
  },
  Venus: {
    Sun:[8,11,12], Moon:[1,2,3,4,5,8,9,11,12], Mars:[3,5,6,9,11,12],
    Mercury:[3,5,6,9,11,12], Jupiter:[5,8,9,10,11],
    Venus:[1,2,3,4,5,8,9,10,11], Saturn:[3,4,5,8,9,10,11], Lagna:[1,2,3,4,5,8,9]
  },
  Saturn: {
    Sun:[1,2,4,7,8,10,11], Moon:[3,6,11], Mars:[3,5,6,10,11,12],
    Mercury:[6,8,9,10,11,12], Jupiter:[5,6,11,12], Venus:[6,11,12],
    Saturn:[3,5,6,11], Lagna:[1,3,4,6,10,11]
  },
  Lagna: {
    Sun:[3,4,6,10,11,12], Moon:[3,6,10,11,12], Mars:[1,3,6,10,11],
    Mercury:[1,2,4,6,8,10,11], Jupiter:[1,2,4,5,6,7,9,10,11],
    Venus:[1,2,3,4,5,8,9], Saturn:[1,3,4,6,10,11], Lagna:[3,6,10,11]
  }
};

export function computeAshtakavarga(planets, ascSign) {
  const ai = SIGNS.indexOf(ascSign);
  const pOrder = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'];
  const allSrc = [...pOrder, 'Lagna'];

  // Sign index for each source (7 planets + Lagna)
  const srcSI = {};
  for (const pn of pOrder) {
    if (planets[pn] && !planets[pn].error) srcSI[pn] = SIGNS.indexOf(planets[pn].sign);
  }
  srcSI.Lagna = ai;

  // Compute BAV for each of 8 bodies
  const bav = {};
  const sav = new Array(12).fill(0);

  for (const planet of allSrc) {
    const rules = BAV_TABLE[planet];
    if (!rules) continue;
    const scores = new Array(12).fill(0);

    for (const source of allSrc) {
      if (!(source in srcSI)) continue;
      const favHouses = rules[source] || [];
      const si = srcSI[source];
      for (const h of favHouses) {
        scores[(si + h - 1) % 12] += 1;
      }
    }

    bav[planet] = scores;
    // Only 7 planets contribute to SAV (Lagna BAV shown separately)
    if (planet !== 'Lagna') {
      for (let i = 0; i < 12; i++) sav[i] += scores[i];
    }
  }

  // Map to houses
  const savH = {}, bavH = {};
  for (let h = 1; h <= 12; h++) {
    const si = (ai + h - 1) % 12;
    savH[h] = { sign: SIGNS[si], score: sav[si] };
    bavH[h] = {};
    for (const pn of pOrder) bavH[h][pn] = bav[pn]?.[si] || 0;
  }

  return {
    sav_total: sav.reduce((a, b) => a + b, 0),
    sav, sav_by_house: savH, bav_by_house: bavH,
    bav_raw: bav,
    lagna_bav: bav.Lagna || new Array(12).fill(0)
  };
}

// ========== Shadbala (Parashara 6-dimension) ==========
// 60 Virupas = 1 Rupa; All internal calculations in Virupas

const EXALT_DEG = { Sun:10, Moon:33, Mars:298, Mercury:165, Jupiter:95, Venus:357, Saturn:200 };
const DEBIL_DEG = {};
for (const [p,d] of Object.entries(EXALT_DEG)) DEBIL_DEG[p] = (d+180)%360;

const DIG_BEST = { Sun:10, Mars:10, Moon:4, Venus:4, Jupiter:1, Mercury:1, Saturn:7 };
const NAIS_V = { Sun:60, Moon:60, Venus:52.5, Jupiter:45, Mercury:37.5, Mars:30, Saturn:22.5 };
const MIN_RUPA = { Sun:5, Moon:6, Mars:5, Mercury:7, Jupiter:6.5, Venus:5.5, Saturn:5 };
const DIURNAL_S = ['Sun','Jupiter','Venus'];
const NOCTURNAL_S = ['Moon','Mars','Saturn'];
const BENEFS = ['Jupiter','Venus','Mercury'];
const MALEFS = ['Saturn','Mars','Sun'];
const SPEC_ASP = { Mars:[4,8], Jupiter:[5,9], Saturn:[3,10] };

// Saptavargaja dignity score (compound relationship, BPHS)
// Own=30, Great Friend=22.5, Friend=15, Equal=7.5, Enemy=3.75, Bitter Enemy=1.875
function _saptaScore(pn, sign) {
  const lord = SIGN_LORDS[sign];
  if (lord === pn) return 30; // Own sign
  const rel = PLANET_RELATIONS[pn];
  if (!rel) return 7.5; // Neutral
  const isFriend = rel.friends?.includes(lord);
  const isEnemy = rel.enemies?.includes(lord);
  const lordRel = PLANET_RELATIONS[lord];
  const lordIsFriend = lordRel?.friends?.includes(pn);
  const lordIsEnemy = lordRel?.enemies?.includes(pn);
  if (isFriend && lordIsFriend) return 22.5; // Great Friend
  if (isFriend) return 15; // Friend
  if (!isFriend && !isEnemy) return 7.5; // Equal/Neutral
  if (isEnemy && lordIsEnemy) return 1.875; // Bitter Enemy
  return 3.75; // Enemy
}

function _sthanaBala(pn, lon, sign, house, allV) {
  // A. Uchcha Bala (0-60 Virupas)
  const debDeg = DEBIL_DEG[pn] || 0;
  let offset = (lon - debDeg + 360) % 360;
  if (offset > 180) offset = 360 - offset;
  const ucha = offset / 180 * 60;

  // B. Saptavargaja Bala (7 vargas: D1/D2/D3/D7/D9/D12/D30)
  // Sum dignity scores from 7 vargas, max = 7*30 = 210 Shashtiamsas
  const SAPTA_IDS = ['D1','D2','D3','D7','D9','D12','D30'];
  let sapta = 0;
  for (const vid of SAPTA_IDS) {
    const vSign = vid === 'D1' ? sign : (allV?.[vid]?.planets?.[pn]?.sign || sign);
    sapta += _saptaScore(pn, vSign);
  }

  // C. Ojayugma Bala (15 Virupas for sign + 15 for Navamsa = max 30)
  let oja = 0;
  // Sign-based: benefics in even signs, malefics in odd signs
  const signIdx = SIGNS.indexOf(sign);
  const signOdd = signIdx % 2 === 0; // Aries=0(odd), Taurus=1(even), ...
  if (pn === 'Mercury' || pn === 'Venus') { if (!signOdd) oja += 15; }
  else { if (signOdd) oja += 15; }
  // Navamsa-based: same rule for D9 sign
  const d9Sign = allV?.D9?.planets?.[pn]?.sign;
  if (d9Sign) {
    const d9Odd = SIGNS.indexOf(d9Sign) % 2 === 0;
    if (pn === 'Mercury' || pn === 'Venus') { if (!d9Odd) oja += 15; }
    else { if (d9Odd) oja += 15; }
  }

  // D. Kendra Bala (BPHS: Kendra=60, Panaphara=30, Apoklima=15)
  let kendra;
  if ([1,4,7,10].includes(house)) kendra = 60;
  else if ([2,5,8,11].includes(house)) kendra = 30;
  else kendra = 15;

  // E. Drekkana Bala (15 Virupas)
  const degInSign = lon % 30;
  let drekkana = 0;
  if (['Sun','Mars','Jupiter'].includes(pn)) drekkana = degInSign < 10 ? 15 : 0;
  else if (['Moon','Venus'].includes(pn)) drekkana = (degInSign >= 10 && degInSign < 20) ? 15 : 0;
  else drekkana = degInSign >= 20 ? 15 : 0;

  return { ucha: Math.round(ucha*100)/100, sapta: Math.round(sapta*100)/100, oja, kendra, drekkana,
    total: Math.round((ucha+sapta+oja+kendra+drekkana)*100)/100 };
}

function _digBala(pn, house) {
  const best = DIG_BEST[pn] || 1;
  let diff = Math.abs(house - best);
  if (diff > 6) diff = 12 - diff;
  return Math.max(0, (6 - diff) * 10);
}

function _kalaBala(pn, isNight, sunNorth, sunLon, moonLon) {
  // A. Nathonnata Bala (60 or 0)
  let nathon = 0;
  if (pn === 'Mercury') nathon = 60;
  else if (isNight && NOCTURNAL_S.includes(pn)) nathon = 60;
  else if (!isNight && DIURNAL_S.includes(pn)) nathon = 60;

  // B. Paksha Bala (0-30)
  const moonSunDiff = (moonLon - sunLon + 360) % 360;
  let paksha = 0;
  if (['Jupiter','Venus','Moon'].includes(pn)) {
    paksha = moonSunDiff / 180 * 30;
  } else {
    paksha = moonSunDiff <= 180
      ? (180 - moonSunDiff) / 180 * 30
      : (moonSunDiff - 180) / 180 * 30;
  }

  // C. Tribhaga Bala (45 or 0)
  const tribhaga = ['Jupiter','Venus','Saturn'].includes(pn) ? 45 : 0;

  // D. Ayana Bala (30 or 15)
  let ayana = 15;
  if (pn === 'Mercury') ayana = 30;
  else if (sunNorth && ['Sun','Mars','Moon'].includes(pn)) ayana = 30;
  else if (!sunNorth && ['Jupiter','Venus','Saturn'].includes(pn)) ayana = 30;

  const total = nathon + paksha + tribhaga + ayana;
  return { nathon, paksha: Math.round(paksha*100)/100, tribhaga, ayana, total: Math.round(total*100)/100 };
}

function _chestaBala(pn, retro, speed, sunLon, moonLon) {
  if (pn === 'Sun') return 60;
  if (pn === 'Moon') {
    const diff = (moonLon - sunLon + 360) % 360;
    return diff / 180 * 60;
  }
  if (retro) return 60;
  const absSpd = Math.abs(speed);
  if (absSpd > 1.0) return 50;
  if (absSpd > 0.5) return 35;
  if (absSpd > 0.1) return 20;
  return 10;
}

function _drikBala(pn, planets) {
  let drik = 0;
  const mySI = SIGNS.indexOf(planets[pn]?.sign || 'Aries');
  if (mySI < 0) return 0;

  for (const [on, od] of Object.entries(planets)) {
    if (on === pn || on === 'Rahu' || on === 'Ketu' || od.error) continue;
    const oSI = SIGNS.indexOf(od.sign);
    if (oSI < 0) continue;

    // House difference from other to me (1=conjunction, 7=opposition)
    const hDiff = (mySI - oSI + 12) % 12 + 1;

    let hasAspect = hDiff === 7 || hDiff === 1;
    if (SPEC_ASP[on]) {
      if (SPEC_ASP[on].includes(hDiff)) hasAspect = true;
    }

    if (hasAspect) {
      let val = hDiff === 1 ? 30 : 15;
      if (BENEFS.includes(on)) drik += val;
      else if (MALEFS.includes(on)) drik -= val;
      else drik += val * 0.5;
    }
  }
  return Math.max(-60, Math.min(60, drik));
}

export function computeShadbala(planets, ascSign, birth, allVargas) {
  // Parse birth hour from birth.time string (e.g. "14:45")
  const hour = birth.time ? parseInt(birth.time.split(':')[0]) : (birth.hour || 12);
  const isNight = hour < 6 || hour >= 18;
  const sunLon = planets.Sun?.degree || 0;
  const moonLon = planets.Moon?.degree || 0;
  const sunNorth = sunLon >= 270 || sunLon < 90;

  const r = {};
  for (const pn of ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']) {
    const p = planets[pn]; if (!p || p.error) continue;

    const sthana = _sthanaBala(pn, p.degree, p.sign, p.house, allVargas);
    const dig = _digBala(pn, p.house);
    const kala = _kalaBala(pn, isNight, sunNorth, sunLon, moonLon);
    const chesta = _chestaBala(pn, p.retrograde, p.speed || 1, sunLon, moonLon);
    const nais = NAIS_V[pn] || 30;
    const drik = _drikBala(pn, planets);

    const totalV = sthana.total + dig + kala.total + chesta + nais + drik;
    const totalR = totalV / 60;
    const req = MIN_RUPA[pn] || 5;
    const pct = Math.round(totalR / req * 100);

    r[pn] = {
      planet_cn: PLANET_CN[pn],
      total: Math.round(totalR * 100) / 100,
      required: req,
      percentage: pct,
      status: pct >= 150 ? '极强' : pct >= 125 ? '强' : pct >= 100 ? '充足' : pct >= 75 ? '略弱' : pct >= 50 ? '弱' : '极弱',
      details: {
        sthana: Math.round(sthana.total / 60 * 100) / 100,
        dig: Math.round(dig / 60 * 100) / 100,
        kala: Math.round(kala.total / 60 * 100) / 100,
        chesta: Math.round(chesta / 60 * 100) / 100,
        naisargika: Math.round(nais / 60 * 100) / 100,
        drik: Math.round(drik / 60 * 100) / 100
      },
      raw_virupas: { sthana, dig, kala, chesta, nais, drik, totalV }
    };
  }
  return r;
}

// ========== Tithi / Yoga / Karana ==========

export function computeTithiYoga(planets, birthInfo) {
  const s=planets.Sun?.degree,m=planets.Moon?.degree;
  if(s==null||m==null)return null;
  let diff=((m-s)%360+360)%360;
  const tithi=Math.floor(diff/12)+1;
  const tInP=((tithi-1)%15)+1;
  const isShukla=tithi<=15;
  let sum=(m+s)%360;
  const yoga=Math.floor(sum/(800/60))+1;

  // Karana（半月相）
  const KARANAS = [
    'Bava','Balava','Kaulava','Taitila','Gara','Vanija','Vishti',
    'Shakuni','Chatushpada','Naga','Kimstughna'
  ];
  const karanaIdx = ((tithi - 1) * 2) % 11;
  const karana = KARANAS[karanaIdx];

  // Vara（星期几）
  let varDay = null;
  const DAYS = ['周日(Ravi)','周一(Soma)','周二(Mangala)','周三(Budha)','周四(Guru)','周五(Shukra)','周六(Shani)'];
  if (birthInfo && birthInfo.date) {
    const d = new Date(birthInfo.date);
    varDay = DAYS[d.getDay()];
  }

  return{
    tithi:{number:tithi,name:TITHI_CN[tInP-1]||`Tithi ${tithi}`,paksha:isShukla?'Shukla Paksha 亮半月':'Krishna Paksha 暗半月',isShukla},
    yoga:{number:yoga,name:SUN_MOON_YOGAS[(yoga-1)%27]||`Yoga ${yoga}`},
    karana: { name: karana },
    vara: varDay,
  };
}

// ========== Dasha 三级 ==========

// Vimshottari Dasha 使用热带年（tropical year）= 365.24219 天
const TROPICAL_YEAR = 365.24219;

// Julian Day 日期转换（标准天文公式，避免 JS Date 浮点精度损失）
function _dateToJD(y, m, d) {
  if (m <= 2) { y--; m += 12; }
  const A = Math.floor(y / 100);
  const B = 2 - A + Math.floor(A / 4);
  return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + d + B - 1524.5;
}

function _jdToDateStr(jd) {
  let Z = Math.floor(jd + 0.5), F = jd + 0.5 - Z, A;
  if (Z < 2299161) A = Z;
  else { const a = Math.floor((Z - 1867216.25) / 36524.25); A = Z + 1 + a - Math.floor(a / 4); }
  const B = A + 1524, C = Math.floor((B - 122.1) / 365.25), D = Math.floor(365.25 * C), E = Math.floor((B - D) / 30.6001);
  const day = Math.floor(B - D - Math.floor(30.6001 * E) + F);
  const month = E < 14 ? E - 1 : E - 13;
  const year = month > 2 ? C - 4716 : C - 4715;
  return `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
}

export function computeDashaWithPratyantar(moonLon, birthDate, referenceDate) {
  const nakSpan=360/27, ni=Math.floor(moonLon/nakSpan), prog=(moonLon%nakSpan)/nakSpan;
  const nak=NAKSHATRA_LIST[ni%27];
  const [by,bm,bd]=birthDate.split('-').map(Number);
  const birthJD=_dateToJD(by,bm,bd);
  const elapsed=prog*nak.years;
  const startJD=birthJD-elapsed*TROPICAL_YEAR;
  const sIdx=DASHA_ORDER.indexOf(nak.lord);
  const timeline=[];let curJD=startJD;

  for(let i=0;i<9;i++){
    const lord=DASHA_ORDER[(sIdx+i)%9],yrs=DASHA_YEARS[lord];
    const endJD=curJD+yrs*TROPICAL_YEAR;
    timeline.push({lord,lord_cn:PLANET_CN[lord],start:_jdToDateStr(curJD),end:_jdToDateStr(endJD),years:yrs,antardasha:null});
    curJD=endJD;
  }

  // reference date → JD
  let refJD;
  if(referenceDate){const[ry,rm,rd]=referenceDate.split('-').map(Number);refJD=_dateToJD(ry,rm,rd);}
  else{const t=new Date();refJD=_dateToJD(t.getFullYear(),t.getMonth()+1,t.getDate());}

  let current=null;
  for(const d of timeline){
    const dsJ=_dateToJD(...d.start.split('-').map(Number)),deJ=_dateToJD(...d.end.split('-').map(Number));
    if(dsJ<=refJD&&refJD<deJ){
      const tDays=deJ-dsJ;const li=DASHA_ORDER.indexOf(d.lord);
      const sub=[];let sJD=dsJ;
      for(let j=0;j<9;j++){
        const sl=DASHA_ORDER[(li+j)%9],sd=tDays*DASHA_YEARS[sl]/120;
        const seJD=sJD+sd;
        const isCur=sJD<=refJD&&refJD<seJD;
        // Pratyantardasha
        const praty=[];let pJD=sJD;
        const pDays=seJD-sJD;
        for(let k=0;k<9;k++){
          const pl=DASHA_ORDER[(DASHA_ORDER.indexOf(sl)+k)%9];
          const pDur=pDays*DASHA_YEARS[pl]/120;
          const peJD=pJD+pDur;
          praty.push({lord:pl,lord_cn:PLANET_CN[pl],start:_jdToDateStr(pJD),end:_jdToDateStr(peJD),is_current:pJD<=refJD&&refJD<peJD});
          pJD=peJD;
        }
        sub.push({lord:sl,lord_cn:PLANET_CN[sl],start:_jdToDateStr(sJD),end:_jdToDateStr(seJD),is_current:isCur,pratyantardasha:praty});
        sJD=seJD;
      }
      d.antardasha=sub;d.pratyantardasha_available=true;current=d;break;
    }
  }
  return{moon_nakshatra:nak.name,birth_date:birthDate,reference_date:_jdToDateStr(refJD),timeline,current_dasha:current};
}

// ========== Nakshatra Advanced ==========
// Gana & Element per Nakshatra
const NAK_GANA = [
  'Dev','Rakshasa','Rakshasa','Manushya','Dev','Manushya','Dev','Dev','Rakshasa',
  'Rakshasa','Manushya','Manushya','Dev','Rakshasa','Rakshasa','Manushya','Dev',
  'Rakshasa','Rakshasa','Manushya','Dev','Dev','Rakshasa','Rakshasa','Manushya',
  'Manushya','Dev'
];
const NAK_ELEMENT = [
  '火','土','火','土','土','风','风','水','水','火','火','土','土','风','风',
  '水','水','火','火','土','土','风','风','水','水','火','火'
];

export function computeNakshatraAdvanced(planets, birthNakIdx) {
  const nakSpan = 360 / 27;
  const results = {};
  const planetNames = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];

  for (const pn of planetNames) {
    const p = planets[pn];
    if (!p || p.error || p.degree == null) continue;
    const lon = p.degree;
    const nakIdx = Math.floor(lon / nakSpan) % 27;
    const degInNak = lon - nakIdx * nakSpan;
    const pada = Math.floor(degInNak / (nakSpan / 4)) + 1;
    const nak = NAKSHATRA_LIST[nakIdx];

    // Tara Bala: distance from birth nakshatra
    const taraDist = ((nakIdx - birthNakIdx) % 27 + 27) % 27 % 9;
    const taraNames = ['Janma','Sampat','Vipat','Kshema','Pratyak','Sadhana','Vadha','Mitra','Atma Mitra'];

    // Sub-lord: each nakshatra divided into 9 sub-sections (Vimshottari order)
    const subSpan = nakSpan / 9;
    const subIdx = Math.floor(degInNak / subSpan) % 9;
    const subLord = DASHA_ORDER[subIdx];

    results[pn] = {
      nakshatra: nak.name,
      nakshatra_idx: nakIdx,
      nakshatra_lord: nak.lord,
      dasha_years: nak.years,
      pada,
      degree_in_nakshatra: Math.round(degInNak * 1e4) / 1e4,
      degree_in_pada: Math.round((degInNak - (pada - 1) * nakSpan / 4) * 1e4) / 1e4,
      gana: NAK_GANA[nakIdx],
      element: NAK_ELEMENT[nakIdx],
      tara_bala: { tara: taraNames[taraDist], index: taraDist },
      sub_lord: subLord,
      sub_index: subIdx,
    };
  }

  return { planets: results };
}

// ========== Chara Dasha ==========
export function computeCharaDasha(planets, ascSign) {
  const SEVEN = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'];
  const ascIdx = SIGNS.indexOf(ascSign);
  // Determine direction: signs 0-5 (Aries-Virgo) = forward, 6-11 (Libra-Pisces) = backward
  const forward = ascIdx < 6;

  // Build sequence starting from ascendant
  const sequence = [];
  for (let i = 0; i < 12; i++) {
    const signIdx = forward ? (ascIdx + i) % 12 : (ascIdx - i + 12) % 12;
    const sign = SIGNS[signIdx];
    const lord = SIGN_LORDS[sign];

    // Find karaka planet with lowest degree in that lord's sign
    // Duration = (360 - planet's navamsa progression) * 120 / 360 simplified
    // Standard: 10 years per sign, adjusted by planet position
    let years = 10; // default
    if (lord && planets[lord] && !planets[lord].error) {
      // Duration based on degree in sign: (30 - deg_in_sign) / 30 * 10 + some base
      years = Math.round(((30 - (planets[lord].degree_in_sign || 0)) / 30 * 9 + 1) * 10) / 10;
    }

    sequence.push({ sign, sign_idx: signIdx, lord, years, order: i + 1 });
  }

  const totalYears = sequence.reduce((s, d) => s + d.years, 0);
  return {
    ascendant: ascSign,
    direction: forward ? 'forward' : 'backward',
    dasha_sequence: sequence,
    total_years: Math.round(totalYears * 10) / 10,
  };
}

// ========== Karakamsha ==========
export function computeKarakamsha(planets) {
  // Karakamsha = Navamsa sign of Atmakaraka
  const karaka = computeKaraka(planets);
  const ak = karaka.karaka7?.AK;
  if (!ak) return null;

  // Get Navamsa sign of AK planet
  const akPlanet = planets[ak.planet];
  if (!akPlanet || akPlanet.error) return null;

  const lon = akPlanet.degree;
  const navamsaSpan = 30 / 9;
  const navamsaIdx = Math.floor(akPlanet.degree_in_sign / navamsaSpan);
  const signIdx = (SIGNS.indexOf(akPlanet.sign) * 9 + navamsaIdx) % 12;
  const karakamshaSign = SIGNS[signIdx];

  return {
    atmakaraka: ak.planet,
    atmakaraka_degree: ak.degree,
    karakamsha_sign: karakamshaSign,
    karakamsha_lord: SIGN_LORDS[karakamshaSign],
  };
}
