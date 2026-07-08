/**
 * Jyotish Extended Calculations v1.0
 * Bhava Bala, Vimsopaka, Vaiseshikamsas, Planet States, AV Pinda, 8 Extra Dasas
 */
import { SIGNS, SIGNS_CN, SIGN_LORDS, PLANET_CN, NAKSHATRA_LIST, EXALTATION, DEBILITATION, PLANET_RELATIONS } from './jyotish-engine.js';
import { computeAllVargas } from './jyotish-advanced.js';

const _dignity = (pn, sign) => {
  if (EXALTATION[pn] === sign) return 3;
  if (DEBILITATION[pn] === sign) return 0.5;
  if (SIGN_LORDS[sign] === pn) return 2.5;
  const rel = PLANET_RELATIONS[pn];
  if (rel?.friends?.includes(SIGN_LORDS[sign])) return 2;
  if (rel?.enemies?.includes(SIGN_LORDS[sign])) return 1;
  return 1.5;
};

// BPHS Vimsopaka Bala — Varga Viswa scoring
// Own/Exalted=20, Great Friend=18, Friend=15, Equal=10, Enemy=7, Bitter Enemy=5
// Compound relationship: check both planet→lord AND lord→planet attitudes
const _vargaViswa = (pn, sign) => {
  const lord = SIGN_LORDS[sign];
  if (lord === pn) return 20; // Own sign
  if (EXALTATION[pn] === sign) return 20; // Exalted
  if (DEBILITATION[pn] === sign) return 5; // Debilitated
  const rel = PLANET_RELATIONS[pn];
  if (!rel) return 10;
  const isFriend = rel.friends?.includes(lord);
  const isEnemy = rel.enemies?.includes(lord);
  const lordRel = PLANET_RELATIONS[lord];
  const lordIsFriend = lordRel?.friends?.includes(pn);
  const lordIsEnemy = lordRel?.enemies?.includes(pn);
  if (isFriend && lordIsFriend) return 18; // Great friend
  if (isFriend) return 15; // Friend
  if (!isFriend && !isEnemy) return 10; // Neutral
  if (isEnemy && lordIsEnemy) return 5; // Bitter enemy
  return 7; // Enemy
};

// ===== 1. Bhava Bala =====
export function computeBhavaBala(planets, ascSign, shadbala) {
  const ai = SIGNS.indexOf(ascSign);
  const houses = [];
  for (let h = 1; h <= 12; h++) {
    const si = (ai + h - 1) % 12, sn = SIGNS[si], lord = SIGN_LORDS[sn] || '';
    const lordBala = shadbala[lord]?.raw_virupas?.totalV || 0;
    // Dig Bala
    const digMap = {1:30,4:30,7:0,10:60};
    const dig = digMap[h] ?? Math.max(0, (6 - Math.min(Math.abs(h-10), 12-Math.abs(h-10))) * 10);
    // Drig Bala
    let drig = 0;
    for (const [on, od] of Object.entries(planets)) {
      if (on==='Rahu'||on==='Ketu'||od.error) continue;
      const oSI = SIGNS.indexOf(od.sign);
      const diff = ((si - oSI) + 12) % 12 + 1;
      let has = diff===7;
      if (on==='Mars' && [4,8].includes(diff)) has=true;
      if (on==='Jupiter' && [5,9].includes(diff)) has=true;
      if (on==='Saturn' && [3,10].includes(diff)) has=true;
      if (has) {
        const v = diff===1?30:15;
        if (['Jupiter','Venus','Mercury'].includes(on)) drig+=v;
        else if (['Saturn','Mars','Sun'].includes(on)) drig-=v;
        else drig+=v*0.5;
      }
    }
    drig = Math.max(-60, Math.min(60, drig));
    const total = lordBala + dig + drig;
    houses.push({house:h,sign:sn,sign_cn:SIGNS_CN[sn],lord,
      bala:Math.round(total*100)/100, in_rupas:Math.round(total/60*100)/100,
      lord_bala:Math.round(lordBala*100)/100, dig_bala:dig, drig_bala:Math.round(drig*100)/100});
  }
  const ranked = [...houses].sort((a,b)=>b.bala-a.bala);
  ranked.forEach((b,i)=>b.rank=i+1);
  return {houses, ranked};
}

// ===== 2. Vimsopaka Bala =====
// BPHS Dasa Varga (10): D1(3) + D2(1.5) + D3(1.5) + D7(1.5) + D9(1.5) + D10(1.5) + D12(1.5) + D16(1.5) + D30(1.5) + D60(5) = 20
// BPHS Shodasa Varga (16): above + D4(1) + D20(1) + D24(1) + D40(1) + D45(1) + D60 stays 5
// Score = Σ(weight × Varga_Viswa) / 20, max = 20
const DASA_W = [{id:'D1',w:3},{id:'D2',w:1.5},{id:'D3',w:1.5},{id:'D7',w:1.5},{id:'D9',w:1.5},{id:'D10',w:1.5},{id:'D12',w:1.5},{id:'D16',w:1.5},{id:'D30',w:1.5},{id:'D60',w:5}];
const SHODASA_W = [{id:'D1',w:3},{id:'D2',w:1.5},{id:'D3',w:1.5},{id:'D4',w:1},{id:'D7',w:1.5},{id:'D9',w:1.5},{id:'D10',w:1.5},{id:'D12',w:1.5},{id:'D16',w:1.5},{id:'D20',w:1},{id:'D24',w:1},{id:'D30',w:1.5},{id:'D40',w:1},{id:'D45',w:1},{id:'D60',w:5}];

export function computeVimsopaka(planets) {
  const av = computeAllVargas(planets);
  const PL = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  const dasa={}, shodasa={};
  for (const pn of PL) {
    const d1 = planets[pn]?.sign; if (!d1) continue;
    let ds=0;
    for (const{id,w}of DASA_W) ds += w * _vargaViswa(pn, av[id]?.planets?.[pn]?.sign||d1) / 20;
    dasa[pn]={score:Math.round(ds*100)/100, max:20, pct:Math.round(ds/20*10000)/100};
    let ss=0;
    for (const{id,w}of SHODASA_W) ss += w * _vargaViswa(pn, av[id]?.planets?.[pn]?.sign||d1) / 20;
    shodasa[pn]={score:Math.round(ss*100)/100, max:20, pct:Math.round(ss/20*10000)/100};
  }
  return {dasa, shodasa};
}

// ===== 3. Vaiseshikamsas =====
const V_DASA = [{min:0,max:2,l:1,n:'Kim'},{min:2,max:3,l:2,n:'Paarijaata'},{min:3,max:4,l:3,n:'Uttama'},{min:4,max:5,l:4,n:'Gopura'},{min:5,max:6,l:5,n:'Simhasana/Kanduka'},{min:6,max:7,l:6,n:'Kerala'},{min:7,max:8,l:7,n:'Kalpavriksha'},{min:8,max:99,l:8,n:'Csynthetic_north_chinaaVana'}];
const V_SHO = [{min:0,max:4,l:1,n:'Kim'},{min:4,max:6,l:2,n:'Paarijaata'},{min:6,max:8,l:3,n:'Uttama'},{min:8,max:10,l:4,n:'Gopura'},{min:10,max:12,l:5,n:'Kanduka'},{min:12,max:14,l:6,n:'Kerala'},{min:14,max:16,l:7,n:'Kalpavriksha'},{min:16,max:99,l:8,n:'Csynthetic_north_chinaaVana'}];

export function computeVaiseshikamsas(vim) {
  const PL = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  const r = {};
  for (const pn of PL) {
    const ds = vim.dasa[pn]?.score||0, ss = vim.shodasa[pn]?.score||0;
    let dl = V_DASA[V_DASA.length-1]; for (const t of V_DASA) if (ds>=t.min&&ds<t.max){dl=t;break;}
    let sl = V_SHO[V_SHO.length-1]; for (const t of V_SHO) if (ss>=t.min&&ss<t.max){sl=t;break;}
    r[pn] = {planet_cn:PLANET_CN[pn], dasa:{score:ds,level:dl.l,name:dl.n}, shodasa:{score:ss,level:sl.l,name:sl.n}};
  }
  return r;
}

// ===== 4. Planet States =====
export function computePlanetActivity(planets) {
  const PL = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  const r = {};
  for (const pn of PL) {
    const p = planets[pn]; if (!p||p.error) continue;
    let a;
    if (p.retrograde) a='Gamana (on the move)';
    else {
      const sp = Math.abs(p.speed||0);
      if (sp<0.2) a='Sayana (lying down)';
      else if (sp<0.5) a='Aagamana (coming)';
      else a='Prakasana (glowing)';
    }
    if (pn==='Rahu'||pn==='Ketu') a='Prakasana (glowing)';
    if (pn==='Sun') a='Aagamana (coming)';
    r[pn]={planet_cn:PLANET_CN[pn],activity:a};
  }
  return r;
}

export function computePlanetAge(planets) {
  const AGE = [{max:6,n:'Baala (infant)'},{max:12,n:'Kumara (adolescent)'},{max:18,n:'Yuva (young)'},{max:24,n:'Vriddha (old)'},{max:30,n:'Mrita (dead)'}];
  const PL = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  const r = {};
  for (const pn of PL) {
    const p = planets[pn]; if (!p||p.error) continue;
    const d = p.degree_in_sign;
    let age = AGE[AGE.length-1].n;
    for (const a of AGE) if (d<a.max){age=a.n;break;}
    r[pn]={planet_cn:PLANET_CN[pn],age,degree:d};
  }
  return r;
}

export function computePlanetAlertness(planets) {
  const PL = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  const r = {};
  for (const pn of PL) {
    const p = planets[pn]; if (!p||p.error) continue;
    const h = p.house;
    let s;
    if ([1,4,7,10].includes(h)) s='Jaagrita (awake)';
    else if ([2,5,8,11].includes(h)) s='Swapna (dreaming)';
    else s='Sushupta (asleep)';
    r[pn]={planet_cn:PLANET_CN[pn],alertness:s,house:h};
  }
  return r;
}

export function computePlanetMood(planets) {
  const PL = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  const r = {};
  for (const pn of PL) {
    const p = planets[pn]; if (!p||p.error) continue;
    const ml = [];
    if (EXALTATION[pn]===p.sign) ml.push('Deepta (glowing)');
    if (DEBILITATION[pn]===p.sign) ml.push('Duhkhita (distressed)');
    if (SIGN_LORDS[p.sign]===pn) ml.push('Swastha (comfortable)');
    if (p.retrograde) ml.push('Garvita (proud)');
    const mySI = SIGNS.indexOf(p.sign);
    for (const [on,od] of Object.entries(planets)) {
      if (on===pn||on==='Rahu'||on==='Ketu'||od.error) continue;
      const oSI = SIGNS.indexOf(od.sign), diff = ((mySI-oSI)+12)%12+1;
      let has = diff===7;
      if (on==='Mars'&&[4,8].includes(diff)) has=true;
      if (on==='Jupiter'&&[5,9].includes(diff)) has=true;
      if (on==='Saturn'&&[3,10].includes(diff)) has=true;
      if (has) {
        if (['Jupiter','Venus','Mercury'].includes(on)&&!ml.includes('Mudita (delighted)')) ml.push('Mudita (delighted)');
        if (['Saturn','Mars','Sun'].includes(on)&&!ml.includes('Khala (mischievous)')) ml.push('Khala (mischievous)');
      }
    }
    if (!ml.length) ml.push('Deena (sad)');
    r[pn]={planet_cn:PLANET_CN[pn],moods:ml};
  }
  return r;
}

// ===== 5. Ashtakavarga Pinda =====
const RASI_GUNAKAR = [7,10,8,4,10,5,7,8,9,5,11,12]; // Aries..Pisces
const GRAHA_GUNAKAR = {Sun:5,Moon:5,Mars:8,Mercury:5,Jupiter:10,Venus:7,Saturn:5};

export function computeAVPinda(avResult) {
  const pOrder = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'];
  const bavRaw = avResult.bav_raw || {};
  const r = {};
  for (const src of [...pOrder, 'Lagna']) {
    const bav = bavRaw[src]; if (!bav) continue;
    const totalBindus = bav.reduce((a,b)=>a+b,0);
    // Rasi Pinda = sum of (bindus[i] × rasiGunakar[i])
    let rasiPinda = 0;
    for (let i = 0; i < 12; i++) rasiPinda += bav[i] * RASI_GUNAKAR[i];
    // Graha Pinda = totalBindus × grahaGunakar (Lagna has no graha gunakar)
    const gG = GRAHA_GUNAKAR[src] || 0;
    const grahaPinda = totalBindus * gG;
    r[src] = {
      sodhya_pinda: totalBindus,
      rasi_pinda: rasiPinda,
      graha_pinda: grahaPinda,
      total_bindus: totalBindus
    };
  }
  return r;
}

// ===== 6. Extra Dasa Systems =====
const TY = 365.24219;
const _jd = (y,m,d) => { if(m<=2){y--;m+=12;} const A=Math.floor(y/100),B=2-A+Math.floor(A/4); return Math.floor(365.25*(y+4716))+Math.floor(30.6001*(m+1))+d+B-1524.5; };
const _jds = (jd) => { let Z=Math.floor(jd+0.5),F=jd+0.5-Z,A; if(Z<2299161)A=Z;else{const a=Math.floor((Z-1867216.25)/36524.25);A=Z+1+a-Math.floor(a/4);} const B=A+1524,C=Math.floor((B-122.1)/365.25),D=Math.floor(365.25*C),E=Math.floor((B-D)/30.6001); const dy=Math.floor(B-D-Math.floor(30.6001*E)+F),mo=E<14?E-1:E-13,yr=mo>2?C-4716:C-4715; return `${yr}-${String(mo).padStart(2,'0')}-${String(dy).padStart(2,'0')}`; };

const ASHT_ORD = ['Sun','Moon','Mars','Mercury','Saturn','Jupiter','Venus','Rahu'];
const ASHT_YR = {Sun:6,Moon:15,Mars:8,Mercury:17,Saturn:10,Jupiter:19,Venus:21,Rahu:12};
const YOG_ORD = ['Moon','Sun','Jupiter','Mars','Mercury','Saturn','Venus','Rahu'];
const YOG_NM = ['Mangala','Pingala','Dhanya','Bhramari','Bhadrika','Ulka','Siddha','Sankata'];
const YOG_YR = {Moon:1,Sun:2,Jupiter:3,Mars:4,Mercury:5,Saturn:6,Venus:7,Rahu:8};
const S_ABBR = ['Ar','Ta','Ge','Cn','Le','Vi','Li','Sc','Sg','Cp','Aq','Pi'];
const S_YRS = [7,10,7,8,6,10,7,8,9,10,7,12];

function _buildSubs(sJD, totalDays, order, yrMap, refJD) {
  const totY = order.reduce((s,l)=>s+(yrMap[l]||0),0);
  const subs=[]; let c=sJD;
  for (const lord of order) {
    const d=totalDays*(yrMap[lord]||0)/totY, e=c+d;
    subs.push({lord,lord_cn:PLANET_CN[lord],start:_jds(c),end:_jds(e),is_current:c<=refJD&&refJD<e});
    c=e;
  }
  return subs;
}

export function computeAshtottari(moonLon, bDate, rDate) {
  const bJD=_jd(...bDate.split('-').map(Number));
  const rJD=rDate?_jd(...rDate.split('-').map(Number)):_jd(new Date().getFullYear(),new Date().getMonth()+1,new Date().getDate());
  const nk=NAKSHATRA_LIST[Math.floor(moonLon/(360/27))%27];
  const prog=(moonLon%(360/27))/(360/27);
  let si=ASHT_ORD.indexOf(nk.lord); if(si<0)si=0;
  const sJD=bJD-prog*(ASHT_YR[nk.lord]||6)*TY;
  const tl=[]; let c=sJD;
  for(let i=0;i<8;i++){
    const lord=ASHT_ORD[(si+i)%8], yrs=ASHT_YR[lord], e=c+yrs*TY;
    const d={lord,lord_cn:PLANET_CN[lord],start:_jds(c),end:_jds(e),years:yrs,antardasha:null};
    if(c<=rJD&&rJD<e){d.antardasha=_buildSubs(c,e-c,ASHT_ORD,ASHT_YR,rJD);d.is_current=true;}
    tl.push(d); c=e;
  }
  return{system:'Ashtottari Dasa (108年)',timeline:tl,current:tl.find(d=>d.is_current)||null};
}

export function computeYogini(moonLon, bDate, rDate) {
  const bJD=_jd(...bDate.split('-').map(Number));
  const rJD=rDate?_jd(...rDate.split('-').map(Number)):_jd(new Date().getFullYear(),new Date().getMonth()+1,new Date().getDate());
  const nk=NAKSHATRA_LIST[Math.floor(moonLon/(360/27))%27];
  const prog=(moonLon%(360/27))/(360/27);
  let si=YOG_ORD.indexOf(nk.lord); if(si<0)si=0;
  const sJD=bJD-prog*YOG_YR[YOG_ORD[si]]*TY;
  const tl=[]; let c=sJD;
  for(let i=0;i<8;i++){
    const idx=(si+i)%8, lord=YOG_ORD[idx], yrs=YOG_YR[lord], e=c+yrs*TY;
    const d={lord,lord_cn:PLANET_CN[lord],yogini_name:YOG_NM[idx],start:_jds(c),end:_jds(e),years:yrs,antardasha:null};
    if(c<=rJD&&rJD<e){d.antardasha=_buildSubs(c,e-c,YOG_ORD,YOG_YR,rJD);d.is_current=true;}
    tl.push(d); c=e;
  }
  return{system:'Yogini Dasa (36年)',timeline:tl,current:tl.find(d=>d.is_current)||null};
}

function _signDasa(name, startSign, bDate, rDate, fwd) {
  const bJD=_jd(...bDate.split('-').map(Number));
  const rJD=rDate?_jd(...rDate.split('-').map(Number)):_jd(new Date().getFullYear(),new Date().getMonth()+1,new Date().getDate());
  const si=SIGNS.indexOf(startSign);
  const tl=[]; let c=bJD;
  for(let i=0;i<12;i++){
    const idx=fwd?(si+i)%12:((si-i)+12)%12;
    const sn=SIGNS[idx], yrs=S_YRS[idx], e=c+yrs*TY;
    const d={lord:S_ABBR[idx],lord_cn:SIGNS_CN[sn],sign:sn,start:_jds(c),end:_jds(e),years:yrs,antardasha:null};
    if(c<=rJD&&rJD<e){
      d.is_current=true;
      const td=e-c, subs=[]; let sc=c;
      for(let j=0;j<12;j++){
        const sidx=fwd?(idx+j)%12:((idx-j)+12)%12;
        const ssn=SIGNS[sidx], sd=td*S_YRS[sidx]/84, se=sc+sd;
        subs.push({lord:S_ABBR[sidx],lord_cn:SIGNS_CN[ssn],sign:ssn,start:_jds(sc),end:_jds(se),is_current:sc<=rJD&&rJD<se});
        sc=se;
      }
      d.antardasha=subs;
    }
    tl.push(d); c=e;
  }
  return{system:name,timeline:tl,current:tl.find(d=>d.is_current)||null};
}

export const computeNarayana = (moonSign,bD,rD) => _signDasa('Narayana Dasa (那罗延大运)', moonSign, bD, rD, SIGNS.indexOf(moonSign)%2===0);
export const computeShoola = (ascSign,bD,rD) => { const ni=(SIGNS.indexOf(ascSign)+8)%12; return _signDasa('Shoola Dasa (死亡大运)', SIGNS[ni], bD, rD, false); };
export const computeSudasa = (ascSign,bD,rD) => _signDasa('Sudasa (财富大运)', ascSign, bD, rD, true);
export const computeDrigdasa = (moonSign,bD,rD) => { const ni=(SIGNS.indexOf(moonSign)+8)%12; return _signDasa('Drigdasa (灵性大运)', SIGNS[ni], bD, rD, false); };
export const computeMoola = (ascSign,bD,rD) => _signDasa('Moola Dasa (业力根源)', ascSign, bD, rD, true);
export const computeKalachakra = (moonLon,bD,rD) => _signDasa('Kalachakra Dasa (时轮大运)', SIGNS[Math.floor(moonLon/30)], bD, rD, false);

export function computeAllExtraDasas(planets, ascSign, bDate, rDate) {
  const ms=planets.Moon?.sign, ml=planets.Moon?.degree||0;
  return {
    ashtottari:computeAshtottari(ml,bDate,rDate),
    kalachakra:computeKalachakra(ml,bDate,rDate),
    moola:computeMoola(ascSign,bDate,rDate),
    narayana:computeNarayana(ms,ascSign,bDate,rDate),
    sudasa:computeSudasa(ascSign,bDate,rDate),
    drigdasa:computeDrigdasa(ms,bDate,rDate),
    shoola:computeShoola(ascSign,bDate,rDate),
    yogini:computeYogini(ml,bDate,rDate),
  };
}
