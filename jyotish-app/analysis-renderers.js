/**
 * Deep Analysis Renderers v1.0
 * 渲染: Raman功能表 · PACDARES · 宫位互影响 · Vargottama · 频率 · 三角验证 · Raman评级
 */
import { PLANET_CN, PLANET_SYMBOLS, SIGNS_CN, SIGNS } from './jyotish-engine.js';
import { RAMAN_TABLES, HOUSE_DOMAINS } from './analysis-deep.js';
import { t, signName, planetName, houseLabel } from './i18n.js';
import { escapeHtml, safeNumber } from './security.js';

const $ = id => document.getElementById(id);
const ARGALA_TARGETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];

// ============================================================================
// 1. Raman 功能吉凶星表
// ============================================================================
export function renderFunctionalNature(ascSign) {
  const c = $('raman-fn-table'); if (!c) return;
  const t = RAMAN_TABLES[ascSign]; if (!t) { c.innerHTML = '<p>无数据</p>'; return; }
  const FN_LABEL = {
    best_benefic: { text: '最佳吉星', cls: 'fn-best' },
    benefic: { text: '吉星', cls: 'fn-good' },
    yogakaraka: { text: 'Yogakaraka', cls: 'fn-yk' },
    neutral: { text: '中性', cls: 'fn-neutral' },
    malefic: { text: '凶星', cls: 'fn-bad' },
    worst: { text: '最凶', cls: 'fn-worst' },
  };
  const mkBadges = (list, key) => list.map(p =>
    `<span class="fn-badge ${FN_LABEL[key].cls}">${escapeHtml(PLANET_SYMBOLS[p]||'')} ${escapeHtml(PLANET_CN[p])}</span>`
  ).join('');

  let html = `<div class="fn-row fn-best-row"><span class="fn-label">最佳吉星</span><div class="fn-badges">${mkBadges(t.best,'best_benefic')}</div></div>`;
  if (t.yk) html += `<div class="fn-row fn-yk-row"><span class="fn-label">Yogakaraka</span><div class="fn-badges"><span class="fn-badge fn-yk">${escapeHtml(PLANET_SYMBOLS[t.yk]||'')} ${escapeHtml(PLANET_CN[t.yk])}</span></div></div>`;
  html += `<div class="fn-row fn-good-row"><span class="fn-label">吉星</span><div class="fn-badges">${mkBadges(t.good,'benefic')}</div></div>`;
  html += `<div class="fn-row fn-neutral-row"><span class="fn-label">中性</span><div class="fn-badges">${mkBadges(t.neutral,'neutral')}</div></div>`;
  html += `<div class="fn-row fn-bad-row"><span class="fn-label">凶星</span><div class="fn-badges">${mkBadges(t.bad,'malefic')}</div></div>`;
  if (t.worst.length) html += `<div class="fn-row fn-worst-row"><span class="fn-label">最凶</span><div class="fn-badges">${mkBadges(t.worst,'worst')}</div></div>`;
  html += `<div class="fn-row fn-maraka-row"><span class="fn-label">Maraka</span><div class="fn-badges">${mkBadges(t.maraka,'worst')}</div></div>`;
  c.innerHTML = html;
}

// ============================================================================
// 2. PACDARES 八维分析
// ============================================================================
export function renderPACDARES(pac) {
  const c = $('pacdares-grid'); if (!c) return;
  const SECTIONS = [
    { key:'P', title:'P · Position 位置', icon:'P', desc:'行星本位：落宫·星座·状态·功能属性' },
    { key:'A', title:'A · Aspect 相位', icon:'A', desc:'行星接收的相位影响' },
    { key:'C', title:'C · Conjunction 合相', icon:'C', desc:'同宫行星合相关系与能量污染' },
    { key:'D', title:'D · Dhana 财富', icon:'D', desc:'财富Yoga检测' },
    { key:'Ar', title:'Ar · Arishta 凶象', icon:'!', desc:'凶象检测' },
    { key:'R', title:'R · Raja 王者', icon:'R', desc:'Raja Yoga & Yogakaraka' },
    { key:'E', title:'E · Exchange 互换', icon:'E', desc:'Parivartana 宫主星互换' },
    { key:'S', title:'S · Special 特殊', icon:'S', desc:'逆行·燃烧·入旺·落陷' },
  ];
  let html = '';
  for (const s of SECTIONS) {
    const items = pac[s.key] || [];
    const count = items.length;
    html += `<div class="pac-section"><div class="pac-header"><span class="pac-icon">${s.icon}</span><span class="pac-title">${s.title}</span><span class="pac-count">${count}</span></div><div class="pac-desc">${s.desc}</div>`;
    if (count === 0) {
      html += `<div class="pac-empty">未检测到</div>`;
    } else {
      html += `<div class="pac-items">`;
      for (const it of items) html += renderPACItem(s.key, it);
      html += `</div>`;
    }
    html += `</div>`;
  }
  c.innerHTML = html;
}

function renderPACItem(key, it) {
  switch(key) {
    case 'P': return `<div class="pac-item pac-pos"><span class="pi-planet">${escapeHtml(PLANET_SYMBOLS[it.planet]||'')} ${escapeHtml(it.pcn)}</span><span class="pi-detail">${escapeHtml(it.scn)} H${escapeHtml(it.house)} ${escapeHtml(it.status||'')} ${it.retro?'℞':''} ${it.combust?'[燃]':''}</span><span class="pi-fn fn-${fnCls(it.fn)}">${fnLabel(it.fn)}</span><span class="pi-hr">主管H${escapeHtml((it.hr || []).join('/'))}</span></div>`;
    case 'A': return `<div class="pac-item pac-asp"><span class="pi-planet">${escapeHtml(PLANET_SYMBOLS[it.planet]||'')} ${escapeHtml(it.pcn)} (H${escapeHtml(it.house)})</span>${(it.received || []).map(r=>`<span class="pi-recv ${r.impact==='吉'?'recv-good':r.impact==='凶'?'recv-bad':'recv-neut'}">${escapeHtml(PLANET_CN[r.from])} ${escapeHtml(r.type)} → ${escapeHtml(r.impact)}</span>`).join('')}</div>`;
    case 'C': return `<div class="pac-item pac-conj${it.pollution?' pac-poll':''}"><span class="pi-planets">${escapeHtml(it.p1cn)} + ${escapeHtml(it.p2cn)}</span><span class="pi-house">H${escapeHtml(it.house)}</span>${it.pollution?'<span class="pi-poll-badge">[!] 能量污染</span>':''}<span class="pi-fn fn-${fnCls(it.f1)}">${fnLabel(it.f1)}</span><span class="pi-fn fn-${fnCls(it.f2)}">${fnLabel(it.f2)}</span></div>`;
    case 'D': return `<div class="pac-item pac-dhana"><span class="pi-type">${escapeHtml(it.type)}</span><span class="pi-lords">${escapeHtml(it.lcn)}</span><span class="pi-house">H${escapeHtml(it.house)}</span><span class="pi-str">${escapeHtml(it.str)}</span></div>`;
    case 'Ar': return `<div class="pac-item pac-arishta"><span class="pi-type">${escapeHtml(it.type)}</span><span class="pi-desc">${escapeHtml(it.desc)}</span></div>`;
    case 'R': return `<div class="pac-item pac-raja"><span class="pi-type">${escapeHtml(it.type)}</span><span class="pi-lords">${escapeHtml(it.lcn)}</span><span class="pi-house">H${escapeHtml(it.house)}</span><span class="pi-str">${escapeHtml(it.str)}</span></div>`;
    case 'E': return `<div class="pac-item pac-exchg"><span class="pi-type">${escapeHtml(it.type)} (${escapeHtml(it.nature)})</span><span class="pi-desc">${escapeHtml(it.desc)}</span></div>`;
    case 'S': return `<div class="pac-item pac-special"><span class="pi-type">${escapeHtml(it.type)}</span><span class="pi-desc">${escapeHtml(it.desc)}</span></div>`;
    default: return '';
  }
}

function fnCls(fn) { return fn==='yogakaraka'?'yk':fn==='best_benefic'?'best':fn==='benefic'?'good':fn==='malefic'?'bad':fn==='worst'?'worst':'neut'; }
function fnLabel(fn) { return fn==='yogakaraka'?'YK':fn==='best_benefic'?'大吉':fn==='benefic'?'吉':fn==='malefic'?'凶':fn==='worst'?'大凶':'中'; }

// ============================================================================
// 3. Argala / Virodhargala 干预分析
// ============================================================================
export function renderArgala(argala) {
  const c = $('argala-section'); if (!c) return;
  if (!argala || Object.keys(argala).length === 0) {
    c.innerHTML = '<div class="argala-empty">未取得 Argala 数据</div>';
    return;
  }
  const entries = ARGALA_TARGETS
    .map(pn => ({ planet: pn, ...(argala[pn] || {}) }))
    .filter(item => item.argala_on_this || item.virodha_on_this)
    .sort((a, b) => Math.abs(safeNumber(b.net_score)) - Math.abs(safeNumber(a.net_score)));
  const supported = entries.filter(item => item.net_assessment === 'supported' || item.net_assessment === 'strongly_supported').length;
  const blocked = entries.filter(item => item.net_assessment === 'blocked').length;
  const neutral = entries.length - supported - blocked;
  const cards = entries.slice(0, 9).map(item => renderArgalaCard(item)).join('');
  c.innerHTML = `
    <div class="argala-dashboard">
      <div class="argala-summary">
        <div><strong>${supported}</strong><span>被支持</span></div>
        <div><strong>${blocked}</strong><span>被阻挡</span></div>
        <div><strong>${neutral}</strong><span>中性</span></div>
      </div>
      <div class="argala-note">
        <strong>读法</strong>
        <p>Argala 看“结果能否被打开”：2/4/11 宫形成资源、基础、收益干预；12/10/3 宫形成 Virodhargala 阻挡。这里按行星主题展示净支持或净阻碍。</p>
      </div>
      <div class="argala-grid">${cards}</div>
    </div>
  `;
}

function renderArgalaCard(item) {
  const cls = item.net_assessment === 'strongly_supported' ? 'argala-strong'
    : item.net_assessment === 'supported' ? 'argala-supported'
    : item.net_assessment === 'blocked' ? 'argala-blocked' : 'argala-neutral';
  const support = (item.argala_on_this || []).slice(0, 3).map(a =>
    `<span>${escapeHtml(planetName(a.source))} · ${escapeHtml(a.house_from)}宫 · ${escapeHtml(a.effect)}</span>`
  ).join('');
  const blockers = (item.virodha_on_this || []).slice(0, 3).map(v =>
    `<span>${escapeHtml(planetName(v.source))} 阻挡${escapeHtml(v.blocks_argala_from)}宫Argala</span>`
  ).join('');
  const label = {
    strongly_supported: '强支持',
    supported: '支持',
    blocked: '受阻',
    neutral: '中性',
  }[item.net_assessment] || '中性';
  return `
    <div class="argala-card ${cls}">
      <div class="argala-card-head">
        <strong>${escapeHtml(PLANET_SYMBOLS[item.planet] || '')} ${escapeHtml(planetName(item.planet))}</strong>
        <span>${escapeHtml(label)} ${safeNumber(item.net_score) >= 0 ? '+' : ''}${escapeHtml(item.net_score ?? 0)}</span>
      </div>
      <div class="argala-card-body">
        <div><b>Argala</b>${support || '<span>无主要干预</span>'}</div>
        <div><b>Virodha</b>${blockers || '<span>无明显阻挡</span>'}</div>
      </div>
    </div>
  `;
}

// ============================================================================
// 4. 宫位互影响矩阵
// ============================================================================
export function renderHouseInfluence(matrix) {
  const c = $('house-influence-grid'); if (!c) return;
  let html = '';
  for (const h of matrix) {
    const vd = h.verdict;
    const vc = vd==='强力'?'vd-strong':vd==='吉'?'vd-good':vd==='中'?'vd-neut':vd==='弱'?'vd-weak':'vd-afflicted';
    html += `<div class="hi-card ${vc}"><div class="hi-header"><span class="hi-num">H${escapeHtml(h.house)}</span><span class="hi-sign">${escapeHtml(h.scn)}</span><span class="hi-lord">主: ${escapeHtml(h.lcn)}</span></div><div class="hi-score ${vc}">${safeNumber(h.total)>0?'+':''}${escapeHtml(h.total)}</div><div class="hi-verdict ${vc}">${escapeHtml(h.verdict)}</div><div class="hi-items">`;
    for (const it of h.items) {
      const ic = it.sc > 0 ? 'hi-pos' : it.sc < 0 ? 'hi-neg' : 'hi-zero';
      html += `<div class="hi-influence ${ic}"><span class="hi-src">${escapeHtml(it.src)}</span><span class="hi-sc">${safeNumber(it.sc)>0?'+':''}${escapeHtml(it.sc)}</span></div>`;
    }
    html += `</div></div>`;
  }
  c.innerHTML = html;
}

// ============================================================================
// 4. Vargottama 检测
// ============================================================================
export function renderVargottama(vgList) {
  const c = $('vargottama-section'); if (!c) return;
  if (!vgList.length) { c.innerHTML = '<div class="vg-empty">未检测到 Vargottama 行星</div>'; return; }
  let html = '<div class="vg-grid">';
  for (const v of vgList) {
    html += `<div class="vg-card"><span class="vg-planet">${escapeHtml(PLANET_SYMBOLS[v.planet]||'')} ${escapeHtml(v.pcn)}</span><span class="vg-badge">Vargottama</span><span class="vg-sign">${escapeHtml(v.d1)}</span></div>`;
  }
  html += '</div>';
  html += '<div class="vg-note">Vargottama：行星在本命盘(D1)和九分盘(D9)落入同一星座，能量倍增。无论吉凶，该行星能量都会被放大。</div>';
  c.innerHTML = html;
}

// ============================================================================
// 5. 行星频率分析
// ============================================================================
export function renderFrequency(freq) {
  const c = $('frequency-grid'); if (!c) return;
  let html = '';
  for (const [pn, f] of Object.entries(freq)) {
    const lc = f.pct>=50?'freq-vhigh':f.pct>=40?'freq-high':f.pct>=30?'freq-mid':'freq-low';
    const pct = Math.max(0, Math.min(100, safeNumber(f.pct)));
    html += `<div class="freq-card"><div class="freq-header"><span class="freq-planet">${escapeHtml(PLANET_SYMBOLS[pn]||'')} ${escapeHtml(f.pcn)}</span><span class="freq-pct ${lc}">${pct}%</span></div><div class="freq-top">${escapeHtml(f.topScn)} (${escapeHtml(f.count)}/${16})</div><div class="freq-level ${lc}">${escapeHtml(f.level)}</div><div class="freq-bar-wrap"><div class="freq-bar" style="width:${pct}%"></div></div><div class="freq-dist">${(f.dist || []).map(d=>`${escapeHtml(d.scn)} ${escapeHtml(d.p)}%`).join(' · ')}</div></div>`;
  }
  c.innerHTML = html;
}

// ============================================================================
// 6. D1 × D9 × D10 三角验证
// ============================================================================
export function renderTriangle(tri) {
  const c = $('triangle-table'); if (!c) return;
  let html = `<table class="tri-table"><thead><tr><th>行星</th><th>D1</th><th>D1状态</th><th>D9</th><th>D9状态</th><th>D10</th><th>D10状态</th><th>Vg</th><th>判定</th></tr></thead><tbody>`;
  for (const t of tri) {
    const vc = t.verdict.includes('双重强势')?'tri-best':t.verdict.includes('未兑现')?'tri-break':t.verdict.includes('反击')?'tri-comeback':t.verdict.includes('双重弱势')?'tri-worst':'tri-ok';
    html += `<tr><td>${escapeHtml(PLANET_SYMBOLS[t.planet]||'')} ${escapeHtml(t.pcn)}</td><td>${escapeHtml(t.d1sign)}</td><td class="${stCls(t.d1st)}">${escapeHtml(t.d1st)}</td><td>${escapeHtml(t.d9sign)}</td><td class="${stCls(t.d9st)}">${escapeHtml(t.d9st)}</td><td>${escapeHtml(t.d10sign)}</td><td class="${stCls(t.d10st)}">${escapeHtml(t.d10st)}</td><td>${t.vargottama?'✓':'—'}</td><td class="${vc}">${escapeHtml(t.verdict)}</td></tr>`;
  }
  html += '</tbody></table>';
  c.innerHTML = html;
}

function stCls(st) { return st==='入旺'||st==='入庙'?'st-good':st==='落陷'?'st-bad':'st-neut'; }

// ============================================================================
// 7. Raman 宫位评级（六步法）
// ============================================================================
function sanitizeRamanDetail(detail) {
  return String(detail || '')
    .replace(/\(undefined\)/g, '(缺星座)')
    .replace(/\bundefined\b/g, '缺资料');
}

export function renderRamanGrades(scores) {
  const c = $('raman-grades-grid'); if (!c) return;
  let html = '';
  for (const s of scores) {
    const gc = s.grade==='A'?'grade-a':s.grade==='B'?'grade-b':s.grade==='C'?'grade-c':s.grade==='D'?'grade-d':'grade-f';
    const domain = HOUSE_DOMAINS[s.house];
    html += `<div class="rg-card ${gc}"><div class="rg-top"><span class="rg-num">H${escapeHtml(s.house)}</span><span class="rg-sign">${escapeHtml(s.scn)}</span><span class="rg-grade ${gc}">${escapeHtml(s.grade)}</span></div><div class="rg-domain">${escapeHtml(domain?domain.name:'')}</div><div class="rg-scores"><span class="rg-pos">+${escapeHtml(s.pos)}</span> / <span class="rg-neg">-${escapeHtml(s.neg)}</span> = <span class="rg-net">${safeNumber(s.net)>0?'+':''}${escapeHtml(s.net)}</span></div><div class="rg-lord">宫主: ${escapeHtml(s.lcn)}</div><div class="rg-details">`;
    for (const d of s.details) html += `<div class="rg-detail ${d.startsWith('✓')?'rd-pos':d.startsWith('✗')?'rd-neg':'rd-neut'}">${escapeHtml(sanitizeRamanDetail(d))}</div>`;
    html += '</div></div>';
  }
  c.innerHTML = html;
}

// ============================================================================
// 8. Trikona-Kendra 三方四正映射渲染
// ============================================================================
export function renderTrikonaKendra(data) {
  const c = document.getElementById('trikona-kendra-grid');
  if (!c || !data) return;
  const { houseLords, trikonaConnections, kendraConnections, crossConnections, overallRating, hasRaja } = data;

  let html = `<div class="tk-rating">${overallRating}</div>`;

  // 关键宫位宫主星一览
  html += `<div class="tk-section"><h5 class="tk-subtitle">关键宫位宫主星</h5><div class="tk-lords-grid">`;
  const keyHouses = [1, 4, 5, 7, 9, 10];
  const houseTag = { 1: '命宫', 4: '家庭', 5: '创意', 7: '婚姻', 9: '命运', 10: '事业' };
  const groupTag = h => [1,5,9].includes(h) ? '三方' : '四正';
  for (const h of keyHouses) {
    const hl = houseLords[h];
    const tag = houseTag[h] || '';
    const grp = groupTag(h);
    html += `<div class="tk-lord-card">
      <div class="tk-lord-house">H${h} <small>${tag}</small> <span class="tk-badge tk-badge-${grp === '三方' ? 'trikona' : 'kendra'}">${grp}</span></div>
      <div class="tk-lord-name">${escapeHtml(hl.lord_cn)} (${escapeHtml(hl.lord)})</div>
      <div class="tk-lord-in">→ H${escapeHtml(hl.lordInHouse || '?')} ${escapeHtml(hl.lordStatus || '')} ${hl.lordRetro ? '℞' : ''}</div>
    </div>`;
  }
  html += '</div></div>';

  // 三方连接
  if (trikonaConnections.length > 0) {
    html += `<div class="tk-section"><h5 class="tk-subtitle">Trikona 三方连接 (1-5-9)</h5><div class="tk-connections">`;
    for (const conn of trikonaConnections) {
      const qClass = conn.quality === 'excellent' ? 'tk-exc' : conn.quality === 'strong' ? 'tk-str' : 'tk-good';
      html += `<div class="tk-conn ${qClass}"><span class="tk-conn-icon">${conn.quality === 'excellent' ? '★' : conn.quality === 'strong' ? '◆' : '→'}</span> ${escapeHtml(conn.desc)}</div>`;
    }
    html += '</div></div>';
  } else {
    html += `<div class="tk-section"><h5 class="tk-subtitle">Trikona 三方连接 (1-5-9)</h5><div class="tk-empty">三方宫主星之间无直接连接</div></div>`;
  }

  // 四正连接
  if (kendraConnections.length > 0) {
    html += `<div class="tk-section"><h5 class="tk-subtitle">Kendra 四正连接 (1-4-7-10)</h5><div class="tk-connections">`;
    for (const conn of kendraConnections) {
      const qClass = conn.quality === 'excellent' ? 'tk-exc' : conn.quality === 'strong' ? 'tk-str' : 'tk-good';
      html += `<div class="tk-conn ${qClass}"><span class="tk-conn-icon">${conn.quality === 'excellent' ? '★' : conn.quality === 'strong' ? '◆' : '→'}</span> ${escapeHtml(conn.desc)}</div>`;
    }
    html += '</div></div>';
  } else {
    html += `<div class="tk-section"><h5 class="tk-subtitle">Kendra 四正连接 (1-4-7-10)</h5><div class="tk-empty">四正宫主星之间无直接连接</div></div>`;
  }

  // 三方×四正交叉
  if (crossConnections.length > 0) {
    html += `<div class="tk-section"><h5 class="tk-subtitle">Trikona × Kendra 交叉连接 (Raja Yoga)</h5><div class="tk-connections">`;
    for (const conn of crossConnections) {
      const qClass = conn.quality === 'maha-raja' ? 'tk-maha' : 'tk-raja';
      html += `<div class="tk-conn ${qClass}"><span class="tk-conn-icon">${conn.quality === 'maha-raja' ? '★★' : '★'}</span> ${escapeHtml(conn.desc)}</div>`;
    }
    html += '</div></div>';
  } else {
    html += `<div class="tk-section"><h5 class="tk-subtitle">Trikona × Kendra 交叉连接</h5><div class="tk-empty">三方与四正之间无交叉 Raja Yoga 连接</div></div>`;
  }

  c.innerHTML = html;
}
