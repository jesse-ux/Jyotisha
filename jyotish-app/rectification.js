/**
 * 生时校正 UI 渲染层 v2.0
 * 引擎逻辑在 rectification-engine.js
 */
import { SIGNS, PLANET_CN, SIGN_LORDS } from './jyotish-engine.js';
import {
  EVENT_CATEGORIES, EVENT_COLLECTION_GUIDE, VARGA_SENSITIVITY, runRectification,
  buildRectificationInterviewQuestions, buildRecommendedRectificationQuestions, rectificationInterviewAnswersToEvents,
  getHouseLord, fmtTime, dateToJD
} from './rectification-engine.js';
import { t, getLang, signName, planetName } from './i18n.js';
import { escapeHtml, escapeAttr } from './security.js';

function fmtOffset(m) { return m === 0 ? t('rect.baseline') : `${m > 0 ? '+' : ''}${m}min`; }

let rectEvents = [];
let rectInterviewAnswers = {};
let rectRecommendedEvents = [];

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
        <div class="form-group"><label>出生时间区间开始</label><input type="time" id="rect-window-start" step="60"></div>
        <div class="form-group"><label>出生时间区间结束</label><input type="time" id="rect-window-end" step="60"></div>
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
    <div class="rect-interview card">
    <div class="rect-interview-head">
      <div>
        <h4 class="sub-title">快速事件访谈</h4>
        <p>只回答是/否；选“是”时补一个大概日期，系统会自动转成生命事件。</p>
      </div>
      <span>guided_rectification_interview · recommended_events</span>
    </div>
      <div class="rect-interview-list">${renderRectificationInterview(lang)}</div>
      <div class="rect-interview-actions">
        <button type="button" class="rect-secondary-btn" id="rect-import-interview">把回答加入事件并开始校正</button>
        <span id="rect-interview-status" aria-live="polite"></span>
      </div>
    </div>
    <div class="rect-events card">
      <h4 class="sub-title">${t('rect.events')} <span class="rect-count" id="rect-event-count">0 ${t('rect.event.count')}</span></h4>
      <p class="rect-hint">${t('rect.events.hint')}</p>
      <div class="rect-event-guide">${EVENT_COLLECTION_GUIDE.map(group =>
        `<span>${lang === 'en' ? escapeHtml(group.en) : escapeHtml(group.cn)}</span>`
      ).join('')}</div>
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

function pctStyle(value) {
  const num = Number(value);
  const pct = Number.isFinite(num) ? Math.max(0, Math.min(100, Math.round(num))) : 0;
  return `${pct}%`;
}

function bindEvents(container) {
  const q = s => container.querySelector(s);
  bindInterviewEvents(container);
  q('#rect-add-btn').addEventListener('click', () => {
    const dEl = q('#rect-event-date'), cEl = q('#rect-event-cat'), descEl = q('#rect-event-desc');
    if (!dEl.value) { dEl.focus(); return; }
    rectEvents.push({ date: dEl.value, category: cEl.value, desc: descEl.value || EVENT_CATEGORIES[cEl.value].cn });
    dEl.value = ''; descEl.value = '';
    renderEventList(container);
  });
  q('#rect-run-btn').addEventListener('click', function () { handleRun(container, this); });
}

function renderInterviewQuestion(question, lang) {
  const prompt = lang === 'en' ? question.question_en : question.question_cn;
  const label = lang === 'en' ? question.label_en : question.label_cn;
  const examples = (question.examples_cn || []).join(' / ');
  return `<div class="rect-interview-item" data-question-id="${escapeAttr(question.id)}" data-category="${escapeAttr(question.category)}">
    <div class="rect-interview-copy">
      <strong>${escapeHtml(prompt)}</strong>
      <span>${escapeHtml(label)} · ${escapeHtml(question.varga)}${examples ? ` · ${escapeHtml(examples)}` : ''}</span>
    </div>
    <div class="rect-answer-group" role="group" aria-label="${escapeAttr(prompt)}">
      <button type="button" data-rect-answer="yes">是</button>
      <button type="button" data-rect-answer="no">否</button>
      <button type="button" data-rect-answer="other">其他</button>
    </div>
    <div class="rect-answer-detail hidden">
      <input type="date" class="rect-answer-date" aria-label="事件日期">
      <input type="text" class="rect-answer-note" placeholder="补充说明，可选">
    </div>
  </div>`;
}

function bindInterviewEvents(container) {
  container.querySelectorAll('.rect-interview-item').forEach(item => {
    item.querySelectorAll('[data-rect-answer]').forEach(btn => {
      btn.addEventListener('click', () => {
        const answer = btn.dataset.rectAnswer;
        item.querySelectorAll('[data-rect-answer]').forEach(other => other.classList.toggle('active', other === btn));
        item.querySelector('.rect-answer-detail')?.classList.toggle('hidden', answer !== 'yes' && answer !== 'other');
        rectInterviewAnswers[item.dataset.questionId] = {
          answer,
          category: item.dataset.category,
        };
      });
    });
  });
  container.querySelector('#rect-import-interview')?.addEventListener('click', () => {
    const events = collectInterviewEvents(container);
    if (!events.length) {
      const status = container.querySelector('#rect-interview-status');
      if (status) status.textContent = '还没有可导入的“是”回答。';
      return;
    }
    rectEvents = [...rectEvents, ...events];
    renderEventList(container);
    const status = container.querySelector('#rect-interview-status');
    if (status) status.textContent = `已加入 ${events.length} 个事件，正在准备校正。`;
    container.querySelector('#rect-run-btn')?.click();
  });
}

function collectInterviewEvents(container) {
  const answers = [...container.querySelectorAll('.rect-interview-item')].map(item => {
    const saved = rectInterviewAnswers[item.dataset.questionId] || {};
    return {
      ...saved,
      category: saved.category || item.dataset.category,
      date: item.querySelector('.rect-answer-date')?.value || '',
      note: item.querySelector('.rect-answer-note')?.value || '',
    };
  });
  return rectificationInterviewAnswersToEvents(answers);
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
      <span class="rect-evt-date">${escapeHtml(evt.date)}</span>
      <span class="rect-evt-cat">${escapeHtml(lang === 'en' ? cat.en : cat.cn)} (${escapeHtml(cat.varga)})</span>
      <span class="rect-evt-desc">${escapeHtml(evt.desc)}</span>
      <button class="rect-evt-del" data-idx="${escapeAttr(i)}">✕</button></div>`;
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
  const audit = result.audit || {};
  const decisionPlan = result.decisionPlan || {};
  const confClr = { '高': '#22c55e', '中': '#f59e0b', '低': '#ef4444', '不确定': '#9ca3af' };
  const correctedBirth = buildCorrectedBirth(result.birth, bm.offsetMin);
  const reportText = buildRectificationReportText(result, correctedBirth);

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
      <div class="rect-score-bar"><div class="rect-score-fill" style="width:${pctStyle(s.pct)}"></div></div>
      <span class="rect-score-val">${escapeHtml(s.pct)}%</span></div>`;
  }).join('');

  const auditCards = renderAuditCards(audit, conf, lang);
  const warningHtml = (audit.warnings || []).length
    ? `<div class="rect-audit-warnings">${audit.warnings.map(w => `<p>${escapeHtml(w)}</p>`).join('')}</div>`
    : '';

  // 事件详情
  const evtRows = bm.eventScores.map(es => {
    const cat = EVENT_CATEGORIES[es.event.category];
    const rel = getRelevanceText(es.dasha, es.event.category, bm.ascSign);
    return `<tr>
      <td>${cat.icon} ${escapeHtml(lang==='en'?cat.en:cat.cn)} <small>(${escapeHtml(cat.varga)})</small></td>
      <td>${escapeHtml(es.event.date)}</td>
      <td>${escapeHtml(es.dasha ? planetName(es.dasha.mahadasha) : '—')}</td>
      <td>${escapeHtml(es.dasha?.antardasha ? planetName(es.dasha.antardasha) : '—')}</td>
      <td class="${es.dashaScore>0?'rect-score-pos':'rect-score-neg'}">${escapeHtml(es.dashaScore.toFixed(1))}</td>
      <td class="${es.vargaScore>0?'rect-score-pos':'rect-score-neg'}">${escapeHtml(es.vargaScore.toFixed(1))}</td>
      <td class="rect-relevance">${escapeHtml(rel)}</td></tr>`;
  }).join('');

  el.innerHTML = `
    <div class="rect-result-summary card">
      <h4 class="sub-title">${t('rect.result')}</h4>
      <div class="rect-summary-grid">
        <div class="rect-summary-item"><span class="rect-label">${t('rect.original.time')}</span><span class="rect-value">${escapeHtml(base.time)}</span></div>
        <div class="rect-summary-item"><span class="rect-label">${t('rect.rec.time')}</span><span class="rect-value rect-best">${escapeHtml(bm.time)} (${escapeHtml(fmtOffset(bm.offsetMin))})</span></div>
        <div class="rect-summary-item"><span class="rect-label">${t('rect.confidence')}</span><span class="rect-value" style="color:${confClr[conf.level]||'#9ca3af'}">${conf.level} (${conf.bestPct}%)</span></div>
      </div>
      <div class="rect-recommendations">${conf.recommendation.map(r => `<p class="rect-rec-line">${escapeHtml(r)}</p>`).join('')}</div>
      ${warningHtml}
      <div class="rect-result-actions">
        <button type="button" class="rect-secondary-btn" id="rect-copy-report">复制校正摘要</button>
        <button type="button" class="rect-apply-btn" id="rect-apply-time">应用推荐时间重新排盘</button>
      </div>
    </div>
    <div class="rect-audit card">
      <h4 class="sub-title">证据闭环</h4>
      <div class="rect-audit-grid">${auditCards}</div>
    </div>
    <div class="rect-plan card">
      <h4 class="sub-title">分盘调用顺序</h4>
      <p class="rect-plan-principle">${escapeHtml(decisionPlan.principle || 'Dasha 定框，核心分盘先行，专项分盘后置。')}</p>
      <ol class="rect-plan-list">${(decisionPlan.ordered_layers || []).map(layer => `
        <li>
          <div class="rect-plan-row">
            <strong>${escapeHtml(layer.label)}</strong>
            <span>${escapeHtml(layer.role)}</span>
          </div>
          <p>${escapeHtml(layer.reason)}</p>
        </li>
      `).join('')}</ol>
      ${(decisionPlan.selected_theme_vargas || []).length ? `<p class="rect-plan-focus">本轮优先专项分盘：${escapeHtml(decisionPlan.selected_theme_vargas.join(' / '))}</p>` : ''}
      ${(decisionPlan.warnings || []).length ? `<div class="rect-audit-warnings">${decisionPlan.warnings.map(w => `<p>${escapeHtml(w)}</p>`).join('')}</div>` : ''}
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
          return `<tr class="${r.isBest?'rect-best-row':''}" data-offset="${escapeAttr(r.offsetMin)}">
            <td>${i+1}</td><td>${escapeHtml(r.time)}</td><td>${escapeHtml(fmtOffset(r.offsetMin))}</td>
            <td>${escapeHtml(signName(r.ascSign))}</td><td>${escapeHtml(signName(d9))}${d9chg}</td><td>${escapeHtml(signName(d10))}${d10chg}</td>
            <td>${escapeHtml(r.totalScore)}%</td>
            <td><div class="rect-match-bar"><div class="rect-match-fill" style="width:${pctStyle(r.totalScore)}"></div><span class="rect-match-pct">${escapeHtml(r.totalScore)}%</span></div></td></tr>`;
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

  el.querySelector('#rect-apply-time')?.addEventListener('click', () => {
    document.dispatchEvent(new CustomEvent('jyotish:apply-rectified-birth', {
      detail: { birth: correctedBirth, rectification: result },
    }));
  });
  el.querySelector('#rect-copy-report')?.addEventListener('click', async () => {
    await copyRectificationReport(reportText);
    const btn = el.querySelector('#rect-copy-report');
    if (btn) {
      const oldText = btn.textContent;
      btn.textContent = '已复制';
      setTimeout(() => { btn.textContent = oldText; }, 1200);
    }
  });

  el.querySelectorAll('.rect-top-results tr[data-offset]').forEach(tr => {
    tr.style.cursor = 'pointer';
    tr.addEventListener('click', () => {
      const off = parseFloat(tr.dataset.offset);
      const r = all.find(x => x.offsetMin === off);
      if (r) showOffsetDetail(el, r, base);
    });
  });
}

function buildCorrectedBirth(birth, offsetMin) {
  const date = new Date(birth.year, birth.month - 1, birth.day, birth.hour, birth.minute || 0, 0);
  date.setMinutes(date.getMinutes() + offsetMin);
  return {
    year: date.getFullYear(),
    month: date.getMonth() + 1,
    day: date.getDate(),
    hour: date.getHours(),
    minute: date.getMinutes(),
    lat: birth.lat,
    lon: birth.lon,
    tz: birth.tz,
  };
}

function buildRectificationReportText(result, correctedBirth) {
  const bm = result.bestMatch || {};
  const conf = result.confidence || {};
  const audit = result.audit || {};
  const lines = [
    'Janma Samaya Shuddhi 生时校正摘要',
    `原始时间：${result.baseChartInfo?.time || '-'}`,
    `推荐时间：${fmtTime(correctedBirth.hour, correctedBirth.minute)} (${fmtOffset(bm.offsetMin || 0)})`,
    `推荐日期：${correctedBirth.year}-${String(correctedBirth.month).padStart(2, '0')}-${String(correctedBirth.day).padStart(2, '0')}`,
    `置信度：${conf.level || '不确定'} / ${conf.bestPct || 0}%`,
    `事件覆盖：${audit.coverage?.event_count || 0} 个事件，${audit.coverage?.group_count || 0} 类主题，跨度 ${audit.coverage?.year_span || 0} 年`,
    `候选差距：领先 ${audit.score_gap ?? 0} 分；同分簇 ${audit.top_cluster?.count || 0} 个`,
    `使用边界：${conf.recommendation?.join('；') || '建议补充事件后复核。'}`,
  ];
  if (audit.warnings?.length) {
    lines.push(`警告：${audit.warnings.join('；')}`);
  }
  return lines.join('\n');
}

async function copyRectificationReport(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.left = '-9999px';
  document.body.appendChild(ta);
  ta.select();
  document.execCommand('copy');
  ta.remove();
}

function renderAuditCards(audit, conf, lang) {
  const coverage = audit.coverage || {};
  const evidence = audit.evidence || {};
  const cluster = audit.top_cluster || {};
  const missing = coverage.missing_groups?.length ? coverage.missing_groups.join('、') : '暂不需要';
  const runner = audit.runner_up ? `${audit.runner_up.time} (${fmtOffset(audit.runner_up.offsetMin)}, ${audit.runner_up.totalScore}%)` : '无';
  const confidenceMeaning = {
    '高': '可把推荐时间作为主候选，但仍建议保留原始记录。',
    '中': '可用于D1/D9/D10观察，高敏感分盘需谨慎。',
    '低': '只能作为探索候选，不建议覆盖出生证明/家人记录。',
    '不确定': '证据不足，应继续收集事件。',
  }[conf?.level] || '证据不足，应继续收集事件。';
  const cards = [
    ['事件覆盖', `${coverage.event_count || 0}个事件 · ${coverage.group_count || 0}类主题`, `质量 ${coverage.quality_score || 0}%；年份跨度 ${coverage.year_span || 0} 年。`],
    ['命中证据', `${evidence.matched_events || 0}个匹配 · ${evidence.match_rate || 0}%`, `强证据 ${evidence.strong_events || 0} 个；敏感分盘 ${evidence.sensitive_vargas?.join('/') || '无变化'}。`],
    ['候选差距', `领先 ${audit.score_gap ?? 0} 分`, `第二名：${runner}；同分簇 ${cluster.count || 0} 个，范围 ${fmtOffset(cluster.min || 0)} 到 ${fmtOffset(cluster.max || 0)}。`],
    ['使用边界', conf?.level || '不确定', confidenceMeaning],
    ['补充建议', missing, '优先补充不同年龄段、不同主题、日期明确的事件。'],
  ];
  return cards.map(([label, value, note]) => `
    <div class="rect-audit-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
      <p>${escapeHtml(note)}</p>
    </div>
  `).join('');
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
    `<span class="rect-change-tag">${escapeHtml(k)}: ${escapeHtml(v ? signName(v.sign) : '—')}</span>`
  ).join('');
  const hcHtml = r.houseChanges.length > 0
    ? r.houseChanges.map(c => `<span class="rect-change-tag">${escapeHtml(planetName(c.planet))}: H${escapeHtml(c.from)}→H${escapeHtml(c.to)}</span>`).join('')
    : escapeHtml(t('rect.no.change'));
  det.innerHTML = `
    <h4 class="sub-title">${escapeHtml(t('rect.offset.detail').replace('{0}',fmtOffset(r.offsetMin)).replace('{1}',r.time))}</h4>
    <div class="rect-detail-grid">
      <div><strong>${t('rect.asc.label')}</strong>${escapeHtml(signName(r.ascSign))} ${escapeHtml(r.ascDeg?.toFixed(2) || '-')}°</div>
      <div><strong>${t('rect.moon.nak')}</strong>${escapeHtml(r.moonNak?.nakName||'—')} Pada ${escapeHtml(r.moonNak?.pada||'?')}</div>
      <div><strong>${t('rect.total.score')}</strong>${escapeHtml(r.totalScore)}%</div>
    </div>
    <h5 class="rect-sub">${t('rect.varga.changes')}</h5>
    <div class="rect-changes">${vlHtml}</div>
    <h5 class="rect-sub">${t('rect.house.changes')}</h5>
    <div class="rect-changes">${hcHtml}</div>`;
  det.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

export function initRectification() { rectEvents = []; rectInterviewAnswers = {}; }

export function setRectificationRecommendedEvents(recommendedEvents = []) {
  rectRecommendedEvents = Array.isArray(recommendedEvents) ? recommendedEvents : [];
}

function renderRectificationInterview(lang) {
  const recommended = buildRecommendedRectificationQuestions(rectRecommendedEvents);
  const fallback = recommended.length ? [] : buildRectificationInterviewQuestions();
  return [...recommended, ...fallback].slice(0, recommended.length ? recommended.length : 3)
    .map(question => renderInterviewQuestion(question, lang))
    .join('');
}
