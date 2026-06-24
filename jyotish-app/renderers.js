/**
 * Jyotish App — 高级渲染函数 v1.0
 * Karaka, Arudha, Vargas, Ashtakavarga, Shadbala, Tithi, Dasha三级
 */
import { SIGNS, SIGNS_CN, PLANET_CN, PLANET_SYMBOLS } from './jyotish-engine.js';
import { VARGA_DEFS } from './jyotish-advanced.js';
import { renderSouthIndianChart } from './chart-renderer.js';
import { t, signName, planetName, statusName, houseLabel, yearsLabel } from './i18n.js';
import { DASHA_THEMES, NAKSHATRA_DATA, PLANET_DIGNITY, ASCENDANT_TABLE } from './interpretation.js';
import { escapeHtml, escapeAttr, safeNumber } from './security.js';
const $ = id => document.getElementById(id);

// ========== Varga 分盘星座计算（与 jyotish-advanced.js 同逻辑） ==========
function vargaSignIdx(degInSign, si, d) {
  const sw = 30 / d, pi = Math.floor(degInSign / sw);
  const o = si % 2 === 0;
  switch (d) {
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

// ========== Tithi / Yoga 信息 ==========
export function renderTithiInfo(ty) {
  const el = $('tithi-info-section');
  if (!ty) { el.innerHTML = ''; return; }
  el.innerHTML = `
    <h4 class="sub-title" style="margin-bottom:10px;">${t('panch.title')}</h4>
    <div class="panchanga-grid">
      <div class="tithi-item"><div class="tithi-label">Vara 星期</div><div class="tithi-value">${escapeHtml(ty.vara || '-')}</div></div>
      <div class="tithi-item"><div class="tithi-label">Tithi 月相</div><div class="tithi-value">${escapeHtml(ty.tithi.name)}</div></div>
      <div class="tithi-item"><div class="tithi-label">Paksha 半月</div><div class="tithi-value">${escapeHtml(ty.tithi.paksha)}</div></div>
      <div class="tithi-item"><div class="tithi-label">Karana 半月相</div><div class="tithi-value">${escapeHtml(ty.karana?.name || '-')}</div></div>
      <div class="tithi-item"><div class="tithi-label">Yoga 日月瑜伽</div><div class="tithi-value">${escapeHtml(ty.yoga.name)}</div></div>
    </div>
  `;
}

// ========== Arudha 快速概览（本命盘Tab底部） ==========
export function renderArudhaQuick(arudha) {
  const el = $('arudha-quick-section');
  if (!arudha || Object.keys(arudha).length === 0) { el.innerHTML = ''; return; }
  const items = Object.entries(arudha).map(([k, v]) =>
    `<div class="arudha-quick-item"><div class="ar-label">${escapeHtml(k)}${v.label ? ' ' + escapeHtml(v.label) : ''}</div><div class="ar-sign">${escapeHtml(signName(v.sign))} ${escapeHtml(houseLabel(v.pada_house))}</div></div>`
  ).join('');
  el.innerHTML = `<h4 class="sub-title" style="margin-bottom:10px;">${t('arudha.overview')}</h4><div class="arudha-quick-grid">${items}</div>`;
}

// ========== Karaka ==========
export function renderKaraka(karaka) {
  renderKarakaGrid($('karaka7-grid'), karaka.karaka7);
  renderKarakaGrid($('karaka8-grid'), karaka.karaka8);
}
function renderKarakaGrid(container, data) {
  if (!container || !data) return;
  const labels = { AK:'AK 自我灵魂', AmK:'AmK 事业顾问', BK:'BK 兄弟姐妹', MK:'MK 母亲', PK:'PK 子女', GK:'GK 障碍冲突', DK:'DK 配偶', PiK:'PiK 父亲' };
  container.innerHTML = Object.entries(data).map(([k, v]) => {
    const isDK = k === 'DK';
    return `<div class="karaka-item${isDK ? ' k-dk' : ''}">
      <div class="k-label">${escapeHtml(labels[k] || k)}</div>
      <div class="k-planet">${escapeHtml(PLANET_SYMBOLS[v.planet] || '')} ${escapeHtml(planetName(v.planet))}</div>
      <div class="k-detail">${safeNumber(v.degree).toFixed(2)}° · ${escapeHtml(signName(v.sign))} H${escapeHtml(v.house)}</div>
    </div>`;
  }).join('');
}

// ========== Vargas 分盘 ==========
export function renderVargas(allV, planets, ascendant) {
  const selector = $('varga-selector');
  const order = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  // 渲染选择器
  selector.innerHTML = VARGA_DEFS.map(v =>
    `<button class="varga-btn${v.id === 'D9' ? ' active' : ''}" data-varga="${escapeAttr(v.id)}">${escapeHtml(v.id)} ${escapeHtml(v.cn)}</button>`
  ).join('');
  selector.querySelectorAll('.varga-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      selector.querySelectorAll('.varga-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderSingleVarga(btn.dataset.varga, planets, ascendant);
    });
  });
  renderSingleVarga('D9', planets, ascendant);
}

function renderSingleVarga(vargaId, planets, ascendant) {
  const def = VARGA_DEFS.find(v => v.id === vargaId);
  if (!def) return;
  const d = def.d;

  // 计算分盘上升
  const ascSi = SIGNS.indexOf(ascendant.sign);
  const ascDegRaw = safeNumber(ascendant.degree_in_sign ?? ascendant.degree);
  const ascDegInSign = ascDegRaw >= 30 ? ((ascDegRaw % 30) + 30) % 30 : ascDegRaw;
  const vargaAscIdx = d === 1 ? ascSi : vargaSignIdx(ascDegInSign, ascSi, d);
  const vargaAscSign = SIGNS[vargaAscIdx];

  // 构建分盘星盘数据
  const vPlanets = {};
  for (const [pn, pi] of Object.entries(planets)) {
    if (pi.error) continue;
    if (d === 1) {
      vPlanets[pn] = { ...pi };
      continue;
    }
    const psi = SIGNS.indexOf(pi.sign);
    const vi = vargaSignIdx(pi.degree_in_sign, psi, d);
    const vHouse = ((vi - vargaAscIdx + 12) % 12) + 1;
    vPlanets[pn] = {
      sign: SIGNS[vi], sign_cn: SIGNS_CN[SIGNS[vi]],
      house: vHouse, degree: 0, degree_in_sign: 0,
      status: '中性', retrograde: false, nakshatra: '', nakshatra_pada: 1, combust: false,
    };
  }

  const chartData = { ascendant: { sign: vargaAscSign }, planets: vPlanets };
  renderSouthIndianChart($('varga-chart'), chartData);

  // 表格
  $('varga-table-title').textContent = `${def.id} ${def.cn} — ${t('varga.positions')}`;
  const tbody = $('varga-table').querySelector('tbody');
  const order = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  tbody.innerHTML = order.filter(pn => vPlanets[pn]).map(pn => {
    const vp = vPlanets[pn];
    return `<tr><td><span class="planet-symbol">${escapeHtml(PLANET_SYMBOLS[pn]||'')}</span>${escapeHtml(planetName(pn))}</td><td>${escapeHtml(signName(vp.sign))}</td><td>H${escapeHtml(vp.house)}</td></tr>`;
  }).join('');
}

// ========== Arudha 详细（分盘Tab底部） ==========
export function renderArudha(arudha) {
  const el = $('arudha-section');
  if (!arudha || Object.keys(arudha).length === 0) { el.innerHTML = ''; return; }
  const items = Object.entries(arudha).map(([k, v]) =>
    `<div class="arudha-item"><div class="ar-pada">${escapeHtml(k)}${v.label ? ' · ' + escapeHtml(v.label) : ''}</div><div class="ar-sign">${escapeHtml(signName(v.sign))}</div><div class="ar-house">${escapeHtml(houseLabel(v.pada_house))} · ${t('house.lord')}: ${escapeHtml(planetName(v.lord))}</div></div>`
  ).join('');
  el.innerHTML = `<div class="arudha-title">${t('arudha.title')}</div><div class="arudha-grid">${items}</div>`;
}

// ========== Ashtakavarga ==========
export function renderAshtakavarga(av, ascSign) {
  // 概览
  $('av-summary').innerHTML = `<div class="av-total-badge">${t('av.savtotal')}: ${av.sav_total} / 337</div>`;

  // SAV 图表（南印度风格格子）
  renderSAVChart(av, ascSign);

  // 详细卡片
  const details = $('av-details');
  const pOrder = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'];
  details.innerHTML = '';
  for (let h = 1; h <= 12; h++) {
    const sh = av.sav_by_house[h];
    if (!sh) continue;
    const score = safeNumber(sh.score);
    const pct = Math.max(0, Math.min(100, Math.round(score / 56 * 100)));
    const bavRow = pOrder.map(pn => {
      const has = av.bav_by_house[h]?.[pn] ? 'contrib' : '';
      return `<span class="av-bav-dot ${has}" title="${escapeAttr(planetName(pn))}: ${escapeAttr(av.bav_by_house[h]?.[pn] || 0)}"></span>`;
    }).join('');
    details.innerHTML += `<div class="av-house-card">
      <div class="av-house-num">${escapeHtml(houseLabel(h))} · ${escapeHtml(sh.sign)}</div>
      <div class="av-score">${score}</div>
      <div class="av-score-bar"><div class="av-score-fill" style="width:${pct}%"></div></div>
      <div class="av-bav-row">${bavRow}</div>
    </div>`;
  }
}

function renderSAVChart(av, ascSign) {
  const container = $('av-chart');
  const ai = SIGNS.indexOf(ascSign);
  // 南印度布局位置
  const layout = [
    [0,0],[0,1],[0,2],[0,3],[1,3],[2,3],[3,3],[3,2],[3,1],[3,0],[2,0],[1,0]
  ];
  const size = 400, cell = size / 4;
  let svg = `<svg viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">`;
  // 画格子
  for (let i = 0; i < 12; i++) {
    const [r, c] = layout[i];
    const signIdx = i; // South Indian: Pisces=0, Aries=1, ...
    const house = ((signIdx - ai + 12) % 12) + 1;
    const score = safeNumber(av.sav_by_house[house]?.score);
    const color = score >= 30 ? 'rgba(22,163,74,0.15)' : score >= 25 ? 'rgba(109,40,217,0.08)' : score < 20 ? 'rgba(220,38,38,0.1)' : '#fff';
    const x = c * cell, y = r * cell;
    svg += `<rect x="${x}" y="${y}" width="${cell}" height="${cell}" fill="${color}" stroke="#c9c8c8" stroke-width="1"/>`;
    svg += `<text x="${x+cell/2}" y="${y+16}" text-anchor="middle" fill="#8c8c8c" font-size="10">${SIGNS[signIdx].slice(0,3)}</text>`;
    svg += `<text x="${x+cell/2}" y="${y+cell/2+8}" text-anchor="middle" fill="${score>=30?'#16a34a':score<20?'#dc2626':'#2e2e2e'}" font-size="22" font-weight="700">${score}</text>`;
    svg += `<text x="${x+cell/2}" y="${y+cell-8}" text-anchor="middle" fill="#6b6b6b" font-size="9">H${house}</text>`;
  }
  svg += '</svg>';
  container.innerHTML = svg;
}

// ========== Shadbala ==========
export function renderShadbala(sb) {
  const tbody = $('shadbala-table').querySelector('tbody');
  tbody.innerHTML = '';
  for (const pn of ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']) {
    const s = sb[pn]; if (!s) continue;
    const pct = safeNumber(s.percentage);
    const barClass = pct >= 100 ? 'strong' : pct >= 75 ? 'medium' : 'weak';
    tbody.innerHTML += `<tr>
      <td><span class="planet-symbol">${escapeHtml(PLANET_SYMBOLS[pn]||'')}</span>${escapeHtml(planetName(pn))}</td>
      <td>${escapeHtml(s.total)} R</td>
      <td>${escapeHtml(s.required)} R</td>
      <td>
        <div style="display:flex;align-items:center;gap:8px;">
          <span>${pct}%</span>
          <div class="shadbala-bar" style="flex:1"><div class="shadbala-bar-fill ${barClass}" style="width:${Math.min(pct,120)}%"></div></div>
        </div>
      </td>
      <td class="${pct>=100?'status-exalted':pct>=75?'status-own':'status-debilitated'}">${escapeHtml(s.status)}</td>
    </tr>`;
  }
}

// ========== Dasha 三级 ==========
export function renderDasha3Level(data) {
  const container = $('dasha-timeline');
  const currentEl = $('dasha-current');
  container.innerHTML = '';

  if (data.current_dasha) {
    const cd = data.current_dasha;
    const curSub = cd.antardasha?.find(a => a.is_current);
    const curPraty = curSub?.pratyantardasha?.find(p => p.is_current);
    const theme = DASHA_THEMES[cd.lord];
    const themeHtml = theme ? `<div class="dasha-theme">${escapeHtml(theme.theme)}</div><div class="dasha-detail"><span class="dasha-pos">✦ ${escapeHtml(theme.positive)}</span><span class="dasha-neg">⚠ ${escapeHtml(theme.negative)}</span></div>` : '';
    currentEl.innerHTML = `
      <div><div class="dasha-current-label">${t('dasha.maha')}</div><div class="dasha-current-planet">${escapeHtml(planetName(cd.lord))}</div></div>
      <div><div class="dasha-current-label">${t('dasha.antar')}</div><div class="dasha-current-sub">${curSub ? escapeHtml(planetName(curSub.lord)) : '-'}</div></div>
      <div><div class="dasha-current-label">${t('dasha.praty')}</div><div class="dasha-current-sub">${curPraty ? escapeHtml(planetName(curPraty.lord)) : '-'}</div></div>
      <div class="dasha-current-date">${escapeHtml(cd.start)} ~ ${escapeHtml(cd.end)}</div>
      ${themeHtml}
    `;
  }

  for (const d of data.timeline) {
    const isCur = data.current_dasha && data.current_dasha.lord === d.lord;
    const bar = document.createElement('div');
    bar.className = `dasha-bar${isCur ? ' active' : ''}`;
    bar.innerHTML = `<div class="dasha-planet">${escapeHtml(planetName(d.lord))}</div><div class="dasha-years">${escapeHtml(yearsLabel(d.years))}</div><div class="dasha-date">${escapeHtml(String(d.start || '').slice(2))}</div>`;
    bar.addEventListener('click', () => {
      container.querySelectorAll('.dasha-bar').forEach(b => b.classList.remove('selected'));
      bar.classList.add('selected');
      renderAntardashaPanel(d.antardasha || []);
    });
    container.appendChild(bar);
  }

  if (data.current_dasha?.antardasha) {
    renderAntardashaPanel(data.current_dasha.antardasha);
  }
}

function renderAntardashaPanel(subs) {
  const panel = $('antardasha-panel');
  panel.innerHTML = '';
  for (const ad of subs) {
    const div = document.createElement('div');
    div.className = `antardasha-item${ad.is_current ? ' current' : ''}`;
    div.innerHTML = `<div class="ad-planet">${escapeHtml(planetName(ad.lord))}${ad.is_current ? ' ◀' : ''}</div><div class="ad-date">${escapeHtml(String(ad.start || '').slice(5))}~${escapeHtml(String(ad.end || '').slice(5))}</div>`;
    div.addEventListener('click', () => {
      panel.querySelectorAll('.antardasha-item').forEach(i => i.classList.remove('selected'));
      div.classList.add('selected');
      renderPratyantardasha(ad.pratyantardasha || []);
    });
    panel.appendChild(div);
  }
  // 自动展开当前次运的三运
  const cur = subs.find(s => s.is_current);
  if (cur?.pratyantardasha) renderPratyantardasha(cur.pratyantardasha);
}

function renderPratyantardasha(pratyList) {
  const panel = $('pratyantardasha-panel');
  panel.innerHTML = `<h4>${t('dasha.praty')}</h4><div class="praty-grid"></div>`;
  const grid = panel.querySelector('.praty-grid');
  for (const p of pratyList) {
    grid.innerHTML += `<div class="praty-item${p.is_current ? ' current' : ''}">
      <div class="praty-planet">${escapeHtml(planetName(p.lord))}${p.is_current ? ' ◀' : ''}</div>
      <div class="praty-date">${escapeHtml(String(p.start || '').slice(5))}~${escapeHtml(String(p.end || '').slice(5))}</div>
    </div>`;
  }
}

// ========== 行星表更新（含D9列） ==========
export function updatePlanetsTable(planets, d9Varga) {
  const tbody = $('planets-table').querySelector('tbody');
  tbody.innerHTML = '';
  const order = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  for (const pn of order) {
    const p = planets[pn]; if (!p || p.error) continue;
    let sc = '';
    if (p.status === '入旺') sc = 'status-exalted';
    else if (p.status === '落陷') sc = 'status-debilitated';
    else if (p.status === '入庙') sc = 'status-own';
    const retro = p.retrograde ? ' ℞' : '';
    const combust = p.combust ? ' [燃]' : '';
    // D9 sign
    let d9sign = '-';
    if (d9Varga?.planets?.[pn]) {
      d9sign = signName(d9Varga.planets[pn].sign) || '-';
    }
    tbody.innerHTML += `<tr>
      <td><span class="planet-symbol">${escapeHtml(PLANET_SYMBOLS[pn]||'')}</span>${escapeHtml(pn)}${retro}${combust}</td>
      <td>${escapeHtml(signName(p.sign))}</td>
      <td>${safeNumber(p.degree_in_sign).toFixed(2)}°</td>
      <td>H${escapeHtml(p.house)}</td>
      <td class="${sc}">${statusName(p.status)}</td>
      <td>${escapeHtml(p.nakshatra)} P${escapeHtml(p.nakshatra_pada)}</td>
      <td>${escapeHtml(d9sign)}</td>
    </tr>`;
  }
}

// ========== Extended: Bhava Bala / Vimsopaka / Vaiseshikamsas / Planet States / AV Pinda / Extra Dasas ==========

export function renderBhavaBala(bb) {
  const el = $('bhava-bala-section'); if (!el || !bb) return;
  const rows = bb.houses.map(h => {
    const bar = Math.min(100, safeNumber(h.in_rupas) / 12 * 100);
    return `<tr><td>${escapeHtml(h.house)}</td><td>${escapeHtml(signName(h.sign))}</td><td>${escapeHtml(planetName(h.lord)||h.lord)}</td>
      <td>${escapeHtml(h.in_rupas)}</td><td>${escapeHtml(h.lord_bala)}</td><td>${escapeHtml(h.dig_bala)}</td><td>${escapeHtml(h.drig_bala)}</td>
      <td><div style="background:#222;height:8px;border-radius:4px;width:${bar}%;max-width:120px;"></div></td></tr>`;
  }).join('');
  el.innerHTML = `<h4 class="sub-title">${t('ext.bhava')}</h4>
    <div class="shadbala-note" style="margin-bottom:12px"><p>${t('bb.note')}</p></div>
    <table class="planets-table"><tr><th>${t('col.house')}</th><th>${t('col.sign')}</th><th>${t('col.lord')}</th><th>Rupas</th><th>${t('col.lordbala')}</th><th>${t('col.dig')}</th><th>${t('col.drig')}</th><th>${t('col.strength')}</th></tr>${rows}</table>
    <p style="margin-top:8px;font-size:12px;color:#666;">${t('bb.strongest')}: ${signName(bb.ranked[0].sign)}(${bb.ranked[0].in_rupas}) | ${t('bb.weakest')}: ${signName(bb.ranked[bb.ranked.length-1].sign)}(${bb.ranked[bb.ranked.length-1].in_rupas})</p>`;
}

export function renderVimsopakaVaiseshikamsa(vim, vais) {
  const el = $('vimsopaka-section'); if (!el || !vim) return;
  const PL = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  const rows = PL.map(pn => {
    const d = vim.dasa[pn], s = vim.shodasa[pn], v = vais?.[pn];
    return `<tr><td>${escapeHtml(planetName(pn))}</td>
      <td>${escapeHtml(d?d.score:'-')}</td><td>${escapeHtml(d?d.pct+'%':'-')}</td>
      <td>${escapeHtml(v?v.dasa.name:'-')}</td><td>${escapeHtml(v?v.dasa.level:'-')}</td>
      <td>${escapeHtml(s?s.score:'-')}</td><td>${escapeHtml(s?s.pct+'%':'-')}</td>
      <td>${escapeHtml(v?v.shodasa.name:'-')}</td><td>${escapeHtml(v?v.shodasa.level:'-')}</td></tr>`;
  }).join('');
  el.innerHTML = `<h4 class="sub-title">${t('ext.vim')}</h4>
    <table class="planets-table"><tr><th>${t('col.planet')}</th>
      <th>${t('col.dasa10')}</th><th>%</th><th>${t('col.level')}</th><th>${t('col.level')}</th>
      <th>${t('col.shodasa')}</th><th>%</th><th>${t('col.level')}</th><th>${t('col.level')}</th></tr>${rows}</table>`;
}

export function renderPlanetStates(activity, age, alertness, mood) {
  const el = $('planet-states-section'); if (!el || !activity) return;
  const PL = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  const rows = PL.map(pn => {
    const a=activity[pn], ag=age?.[pn], al=alertness?.[pn], m=mood?.[pn];
    return `<tr><td>${escapeHtml(planetName(pn))}</td>
      <td>${escapeHtml(a?.activity||'-')}</td><td>${escapeHtml(ag?.age||'-')}</td>
      <td>${escapeHtml(al?.alertness||'-')}</td><td>${escapeHtml(m?.moods?.join(', ')||'-')}</td></tr>`;
  }).join('');
  el.innerHTML = `<h4 class="sub-title">${t('ext.states')}</h4>
    <table class="planets-table"><tr><th>${t('col.planet')}</th><th>${t('col.activity')}</th><th>${t('col.age')}</th><th>${t('col.alertness')}</th><th>${t('col.mood')}</th></tr>${rows}</table>`;
}

export function renderAVPinda(pinda) {
  const el = $('av-pinda-section'); if (!el || !pinda) return;
  const PL = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Lagna'];
  const rows = PL.map(pn => {
    const p = pinda[pn];
    return `<tr><td>${escapeHtml(pn==='Lagna'?'Lagna':planetName(pn))}</td>
      <td>${escapeHtml(p?p.sodhya_pinda:'-')}</td><td>${escapeHtml(p?p.rasi_pinda:'-')}</td><td>${escapeHtml(p?p.graha_pinda:'-')}</td></tr>`;
  }).join('');
  el.innerHTML = `<h4 class="sub-title">${t('ext.pinda')}</h4>
    <table class="planets-table"><tr><th>${t('col.planet')}</th><th>Sodhya Pinda</th><th>Rasi Pinda</th><th>Graha Pinda</th></tr>${rows}</table>`;
}

export function renderExtraDasas(dasas) {
  const el = $('extra-dasa-section'); if (!el || !dasas) return;
  const systems = Object.entries(dasas);
  let html = `<h4 class="sub-title">${t('ext.dasa')}</h4>`;
  for (const [key, dasa] of systems) {
    if (!dasa) continue;
    const cur = dasa.current;
    html += `<div class="dasa-system"><h5>${escapeHtml(dasa.system)}${cur?' — 当前: '+escapeHtml(cur.lord_cn||cur.lord)+' ('+escapeHtml(cur.start)+' ~ '+escapeHtml(cur.end)+')':''}</h5>`;
    // Antardasha
    if (cur?.antardasha) {
      html += '<div class="dasha-subs">';
      for (const s of cur.antardasha) {
        const cls = s.is_current ? 'style="font-weight:bold;color:#222;"' : 'style="color:#888;"';
        html += `<span ${cls}>${escapeHtml(s.lord_cn||s.lord)} ${escapeHtml(s.start)}~${escapeHtml(s.end)}</span> `;
      }
      html += '</div>';
    }
    // Timeline
    html += '<div class="dasha-timeline-row">';
    for (const d of dasa.timeline) {
      const cls = d.is_current ? 'dasha-active' : '';
      html += `<span class="dasha-period ${cls}" title="${escapeAttr(d.start)}~${escapeAttr(d.end)}">${escapeHtml(d.lord_cn||d.lord)}</span>`;
    }
    html += '</div></div>';
  }
  el.innerHTML = html;
}
