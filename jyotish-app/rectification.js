/**
 * 生时校正 UI 渲染层 v2.0
 * 引擎逻辑在 rectification-engine.js
 */
import { SIGNS, PLANET_CN, SIGN_LORDS } from './jyotish-engine.js';
import {
  EVENT_CATEGORIES, VARGA_SENSITIVITY, runRectification,
  getHouseLord, fmtTime, dateToJD
} from './rectification-engine.js';
import { t, getLang, signName, planetName } from './i18n.js';

function fmtOffset(m) { return m === 0 ? t('rect.baseline') : `${m > 0 ? '+' : ''}${m}min`; }

let rectEvents = [];

export function renderRectificationTab(container) {
  const lang = getLang();
  container.innerHTML = `
    <div class="rect-header">
      <h3 class="section-title">${t('rect.title')}</h3>
      <p class="rect-subtitle">${t('rect.subtitle')}</p>
      <div class="rect-method-info">${t('rect.method.info')}</div>
    </div>
    <div class="rect-config card">
      <h4 class="sub-title">${t('rect.config')}</h4>
      <div class="rect-config-row">
        <div class="form-group"><label>${t('rect.range')}</label>
          <select id="rect-range">
            <option value="5">${t('rect.range.5')}</option>
            <option value="10">${t('rect.range.10')}</option>
            <option value="15" selected>${t('rect.range.15')}</option>
            <option value="20">${t('rect.range.20')}</option>
            <option value="30">${t('rect.range.30')}</option>
          </select></div>
        <div class="form-group"><label>${t('rect.step')}</label>
          <select id="rect-step">
            <option value="0.5">${t('rect.step.30s')}</option>
            <option value="1" selected>${t('rect.step.1m')}</option>
            <option value="2">${t('rect.step.2m')}</option>
            <option value="5">${t('rect.step.5m')}</option>
          </select></div>
      </div>
      <details class="rect-sensitivity-details">
        <summary>${t('rect.sensitivity.info')}</summary>
        <table class="rect-table rect-sens-table">
          <thead><tr><th>${t('rect.varga.col')}</th><th>${t('rect.time.window')}</th></tr></thead>
          <tbody>${Object.entries(VARGA_SENSITIVITY).map(([k, v]) =>
            `<tr><td>${k} (${lang === 'en' ? v.en : v.cn})</td><td>~${v.min} ${t('rect.min.unit')}</td></tr>`
          ).join('')}</tbody>
        </table>
      </details>
    </div>
    <div class="rect-events card">
      <h4 class="sub-title">${t('rect.events')} <span class="rect-count" id="rect-event-count">0 ${t('rect.event.count')}</span></h4>
      <p class="rect-hint">${t('rect.events.hint')}</p>
      <div class="rect-add-row">
        <div class="form-group"><label>${t('rect.event.date')}</label><input type="date" id="rect-event-date" required></div>
        <div class="form-group"><label>${t('rect.event.cat')}</label>
          <select id="rect-event-cat">${Object.entries(EVENT_CATEGORIES).map(([k, v]) =>
            `<option value="${k}">${v.icon} ${lang === 'en' ? v.en : v.cn} (${v.varga})</option>`
          ).join('')}</select></div>
        <div class="form-group"><label>${t('rect.event.desc')}</label><input type="text" id="rect-event-desc" placeholder="${t('rect.event.ph')}"></div>
        <button class="btn-primary btn-sm" id="rect-add-btn">${t('rect.event.add')}</button>
      </div>
      <div id="rect-event-list" class="rect-event-list"></div>
    </div>
    <div class="rect-action">
      <button class="btn-primary" id="rect-run-btn">
        <span class="btn-text">${t('rect.run')}</span>
        <span class="btn-loading hidden"><span class="spinner"></span> ${t('rect.computing')}</span>
      </button>
    </div>
    <div id="rect-progress" class="rect-progress hidden">
      <div class="rect-progress-bar"><div class="rect-progress-fill" id="rect-progress-fill"></div></div>
      <p class="rect-progress-text" id="rect-progress-text">${t('rect.preparing')}</p>
    </div>
    <div id="rect-results" class="hidden"></div>`;
  bindEvents(container);
}

function bindEvents(container) {
  const q = s => container.querySelector(s);
  q('#rect-add-btn').addEventListener('click', () => {
    const dEl = q('#rect-event-date'), cEl = q('#rect-event-cat'), descEl = q('#rect-event-desc');
    if (!dEl.value) { dEl.focus(); return; }
    rectEvents.push({ date: dEl.value, category: cEl.value, desc: descEl.value || EVENT_CATEGORIES[cEl.value].cn });
    dEl.value = ''; descEl.value = '';
    renderEventList(container);
  });
  q('#rect-run-btn').addEventListener('click', function () { handleRun(container, this); });
}

function renderEventList(container) {
  const listEl = container.querySelector('#rect-event-list');
  const countEl = container.querySelector('#rect-event-count');
  const lang = getLang();
  countEl.textContent = `${rectEvents.length} ${t('rect.event.count')}`;
  if (!rectEvents.length) { listEl.innerHTML = `<p class="rect-empty">${t('rect.no.events')}</p>`; return; }
  listEl.innerHTML = rectEvents.map((evt, i) => {
    const cat = EVENT_CATEGORIES[evt.category];
    return `<div class="rect-event-item">
      <span class="rect-evt-icon">${cat.icon}</span>
      <span class="rect-evt-date">${evt.date}</span>
      <span class="rect-evt-cat">${lang === 'en' ? cat.en : cat.cn} (${cat.varga})</span>
      <span class="rect-evt-desc">${evt.desc}</span>
      <button class="rect-evt-del" data-idx="${i}">✕</button></div>`;
  }).join('');
  listEl.querySelectorAll('.rect-evt-del').forEach(b => {
    b.addEventListener('click', () => { rectEvents.splice(+b.dataset.idx, 1); renderEventList(container); });
  });
}

async function handleRun(container, runBtn) {
  if (!rectEvents.length) { alert(t('rect.alert.no.events')); return; }
  if (!window.__jyotishBirth) { alert(t('rect.alert.no.chart')); return; }
  const q = s => container.querySelector(s);
  const progressEl = q('#rect-progress'), fillEl = q('#rect-progress-fill');
  const textEl = q('#rect-progress-text'), resultsEl = q('#rect-results');
  const rangeMin = +q('#rect-range').value, stepMin = +q('#rect-step').value;
  progressEl.classList.remove('hidden'); resultsEl.classList.add('hidden');
  runBtn.querySelector('.btn-text').classList.add('hidden');
  runBtn.querySelector('.btn-loading').classList.remove('hidden'); runBtn.disabled = true;
  try {
    const result = await runRectification(window.__jyotishBirth, rectEvents, {
      rangeMin, stepMin,
      onProgress(cur, total) {
        const pct = Math.round(cur / total * 100);
        fillEl.style.width = pct + '%';
        textEl.textContent = `${t('rect.calculating')} ${cur}/${total} (${pct}%)`;
      },
    });
    if (result.error) { textEl.textContent = result.error; return; }
    renderResults(container, result);
  } catch (e) { textEl.textContent = `Error: ${e.message}`; console.error('[Rect]', e);
  } finally {
    runBtn.querySelector('.btn-text').classList.remove('hidden');
    runBtn.querySelector('.btn-loading').classList.add('hidden');
    runBtn.disabled = false;
    setTimeout(() => progressEl.classList.add('hidden'), 2000);
  }
}

function renderResults(container, result) {
  const el = container.querySelector('#rect-results'); el.classList.remove('hidden');
  const lang = getLang();
  const { bestMatch: bm, confidence: conf, baseChartInfo: base, results: all } = result;
  const confClr = { '高': '#22c55e', '中': '#f59e0b', '低': '#ef4444', '不确定': '#9ca3af' };

  // 分盘变化
  const vcHtml = bm.vargaChanges.length > 0
    ? bm.vargaChanges.map(c => `<tr><td>${c.varga}</td><td>${signName(c.from)}</td><td>${signName(c.to)}</td></tr>`).join('')
    : `<tr><td colspan="3" style="text-align:center">${t('rect.no.change')}</td></tr>`;

  // 评分条
  const weights = { dasha:'40%', varga:'35%', house:'15%', nak:'10%' };
  const scoreBars = Object.keys(weights).map(k => {
    const s = bm.scores[k];
    return `<div class="rect-score-row">
      <span class="rect-score-label">${t('rect.scoring.'+k)} (${weights[k]})</span>
      <div class="rect-score-bar"><div class="rect-score-fill" style="width:${s.pct}%"></div></div>
      <span class="rect-score-val">${s.pct}%</span></div>`;
  }).join('');

  // 事件详情
  const evtRows = bm.eventScores.map(es => {
    const cat = EVENT_CATEGORIES[es.event.category];
    const rel = getRelevanceText(es.dasha, es.event.category, bm.ascSign);
    return `<tr>
      <td>${cat.icon} ${lang==='en'?cat.en:cat.cn} <small>(${cat.varga})</small></td>
      <td>${es.event.date}</td>
      <td>${es.dasha ? planetName(es.dasha.mahadasha) : '—'}</td>
      <td>${es.dasha?.antardasha ? planetName(es.dasha.antardasha) : '—'}</td>
      <td class="${es.dashaScore>0?'rect-score-pos':'rect-score-neg'}">${es.dashaScore.toFixed(1)}</td>
      <td class="${es.vargaScore>0?'rect-score-pos':'rect-score-neg'}">${es.vargaScore.toFixed(1)}</td>
      <td class="rect-relevance">${rel}</td></tr>`;
  }).join('');

  el.innerHTML = `
    <div class="rect-result-summary card">
      <h4 class="sub-title">${t('rect.result')}</h4>
      <div class="rect-summary-grid">
        <div class="rect-summary-item"><span class="rect-label">${t('rect.original.time')}</span><span class="rect-value">${base.time}</span></div>
        <div class="rect-summary-item"><span class="rect-label">${t('rect.rec.time')}</span><span class="rect-value rect-best">${bm.time} (${fmtOffset(bm.offsetMin)})</span></div>
        <div class="rect-summary-item"><span class="rect-label">${t('rect.confidence')}</span><span class="rect-value" style="color:${confClr[conf.level]||'#9ca3af'}">${conf.level} (${conf.bestPct}%)</span></div>
      </div>
      <div class="rect-recommendations">${conf.recommendation.map(r => `<p class="rect-rec-line">${r}</p>`).join('')}</div>
    </div>
    <div class="rect-scoring-detail card">
      <h4 class="sub-title">${t('rect.scoring.title')}</h4>
      ${scoreBars}
      <div class="rect-score-total">${t('rect.total.score')} ${bm.totalScore}%</div>
    </div>
    <div class="rect-varga-changes card">
      <h4 class="sub-title">${t('rect.varga.changes')}</h4>
      <table class="rect-table"><thead><tr><th>${t('rect.varga.col')}</th><th>${t('rect.from.col')}</th><th>${t('rect.to.col')}</th></tr></thead>
      <tbody>${vcHtml}</tbody></table>
    </div>
    <div class="rect-top-results card">
      <h4 class="sub-title">${t('rect.top.candidates')}</h4>
      <div class="rect-table-wrap"><table class="rect-table">
        <thead><tr><th>#</th><th>${t('rect.time')}</th><th>${t('rect.offset')}</th><th>${t('rect.asc')}</th><th>D9</th><th>D10</th><th>${t('rect.score')}</th><th>${t('rect.match')}</th></tr></thead>
        <tbody>${all.slice(0,10).map((r,i) => {
          const d9=r.vargaLagnas?.D9?.sign||r.ascSign, d10=r.vargaLagnas?.D10?.sign||r.ascSign;
          const d9chg=r.vargaChanges?.some(v=>v.varga==='D9')?' ⚠️':'';
          const d10chg=r.vargaChanges?.some(v=>v.varga==='D10')?' ⚠️':'';
          return `<tr class="${r.isBest?'rect-best-row':''}" data-offset="${r.offsetMin}">
            <td>${i+1}</td><td>${r.time}</td><td>${fmtOffset(r.offsetMin)}</td>
            <td>${signName(r.ascSign)}</td><td>${signName(d9)}${d9chg}</td><td>${signName(d10)}${d10chg}</td>
            <td>${r.totalScore}%</td>
            <td><div class="rect-match-bar"><div class="rect-match-fill" style="width:${r.totalScore}%"></div><span class="rect-match-pct">${r.totalScore}%</span></div></td></tr>`;
        }).join('')}</tbody>
      </table></div>
    </div>
    <div class="rect-event-detail card">
      <h4 class="sub-title">${t('rect.event.detail')}</h4>
      <div class="rect-table-wrap"><table class="rect-table rect-detail-table">
        <thead><tr><th>${t('rect.event.col')}</th><th>${t('rect.date.col')}</th><th>${t('rect.maha.col')}</th><th>${t('rect.antar.col')}</th><th>${t('rect.score.dasha')}</th><th>${t('rect.score.varga')}</th><th>${t('rect.rel.col')}</th></tr></thead>
        <tbody>${evtRows}</tbody>
      </table></div>
    </div>`;

  el.querySelectorAll('.rect-top-results tr[data-offset]').forEach(tr => {
    tr.style.cursor = 'pointer';
    tr.addEventListener('click', () => {
      const off = parseFloat(tr.dataset.offset);
      const r = all.find(x => x.offsetMin === off);
      if (r) showOffsetDetail(el, r, base);
    });
  });
}

function getRelevanceText(di, category, ascSign) {
  if (!di) return '—';
  const cat = EVENT_CATEGORIES[category]; if (!cat) return '—';
  const ai = SIGNS.indexOf(ascSign), hl = cat.houses.map(h => getHouseLord(ai, h));
  const mdR = cat.planets.includes(di.mahadasha) || hl.includes(di.mahadasha);
  const adR = di.antardasha && (cat.planets.includes(di.antardasha) || hl.includes(di.antardasha));
  if (mdR && adR) return t('rect.strong.match');
  if (mdR) return t('rect.maha.match');
  if (adR) return t('rect.antar.match');
  return t('rect.no.match');
}

function showOffsetDetail(container, r, base) {
  let det = container.querySelector('.rect-offset-detail');
  if (!det) { det = document.createElement('div'); det.className = 'rect-offset-detail card'; container.appendChild(det); }
  const vlHtml = Object.entries(r.vargaLagnas || {}).map(([k, v]) =>
    `<span class="rect-change-tag">${k}: ${v ? signName(v.sign) : '—'}</span>`
  ).join('');
  const hcHtml = r.houseChanges.length > 0
    ? r.houseChanges.map(c => `<span class="rect-change-tag">${planetName(c.planet)}: H${c.from}→H${c.to}</span>`).join('')
    : t('rect.no.change');
  det.innerHTML = `
    <h4 class="sub-title">${t('rect.offset.detail').replace('{0}',fmtOffset(r.offsetMin)).replace('{1}',r.time)}</h4>
    <div class="rect-detail-grid">
      <div><strong>${t('rect.asc.label')}</strong>${signName(r.ascSign)} ${r.ascDeg?.toFixed(2)}°</div>
      <div><strong>${t('rect.moon.nak')}</strong>${r.moonNak?.nakName||'—'} Pada ${r.moonNak?.pada||'?'}</div>
      <div><strong>${t('rect.total.score')}</strong>${r.totalScore}%</div>
    </div>
    <h5 class="rect-sub">${t('rect.varga.changes')}</h5>
    <div class="rect-changes">${vlHtml}</div>
    <h5 class="rect-sub">${t('rect.house.changes')}</h5>
    <div class="rect-changes">${hcHtml}</div>`;
  det.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

export function initRectification() { rectEvents = []; }
