/**
 * Jyotish App — 主入口 v3.0
 * 整合: 排盘、宫位、相位、Yoga、Karaka、分盘、Ashtakavarga、Shadbala、Dasha三级、Transit
 */
import {
  initEngine, computeChart, detectYogas, detectExtendedYogas,
  computeAspects, computeHouseAnalysis, searchCities,
  SIGNS, SIGNS_CN, PLANET_CN, PLANET_SYMBOLS, SIGN_LORDS,
} from './jyotish-engine.js';
import {
  computeCombustion, computeKaraka, computeArudha, computeAllVargas,
  computeAshtakavarga, computeShadbala, computeTithiYoga, computeDashaWithPratyantar,
} from './jyotish-advanced.js';
import { renderSouthIndianChart, renderNorthIndianChart, setChartStyle, getChartStyle } from './chart-renderer.js';
import {
  HOUSE_MEANINGS, PLANET_IN_HOUSE, NAKSHATRA_DATA,
  YOGA_DEFINITIONS, ASPECT_DESC, HOUSE_GROUPS, TRANSIT_EFFECTS,
} from './interpretation.js';
import { YOGA_EXTENDED_A } from './yoga-extended.js';
import { YOGA_EXTENDED_B } from './yoga-extended-b.js';
import { YOGA_DETAILS_A } from './yoga-details-a.js';
import { YOGA_DETAILS_B } from './yoga-details-b.js';
import { PIH_PART1 } from './planet-house-details-a.js';
import { PIH_PART2 } from './planet-house-details-b.js';
import { PIH_PART3 } from './planet-house-details-c.js';

const YOGA_DETAILS = { ...YOGA_DETAILS_A, ...YOGA_DETAILS_B };
const PLANET_HOUSE_DETAIL = { ...PIH_PART1, ...PIH_PART2, ...PIH_PART3 };
import {
  computeTransit, computeTransitOverlay, computeDoubleTransit, checkSadeSati,
  computeTransitAVScore, computeTransitHouseImpact,
} from './transit.js';
import {
  renderTithiInfo, renderArudhaQuick, renderKaraka, renderVargas, renderArudha,
  renderAshtakavarga, renderShadbala, renderDasha3Level, updatePlanetsTable,
} from './renderers.js';
import {
  computePACDARES, computeHouseInfluence, detectVargottama, computeFrequency,
  computeTriangle, computeRamanHouseScore, computeTrikonaKendra,
} from './analysis-deep.js';
import {
  renderFunctionalNature, renderPACDARES, renderHouseInfluence, renderVargottama,
  renderFrequency, renderTriangle, renderRamanGrades, renderTrikonaKendra,
} from './analysis-renderers.js';
import {
  computeBhavaBala, computeVimsopaka, computeVaiseshikamsas,
  computePlanetActivity, computePlanetAge, computePlanetAlertness, computePlanetMood,
  computeAVPinda, computeAllExtraDasas,
} from './jyotish-extended.js';
import {
  renderBhavaBala, renderVimsopakaVaiseshikamsa, renderPlanetStates, renderAVPinda, renderExtraDasas,
} from './renderers.js';
import { exportJSON, exportSVG, exportPNG } from './export.js';
import { computeArgala } from './argala.js';
import { computeTajika } from './tajika.js';
import { computeNakshatraAdvanced, computeCharaDasha, computeKarakamsha } from './jyotish-advanced.js';
import { computeValidation, computeAudit, computeActionableContext } from './jyotish-export-modules.js';
import { initTooltip, bindTerms } from './glossary.js';
import { initAIChat, aiChatSetChartData } from './ai-chat.js';
import { initAuth } from './auth.js';
import { initSubscription } from './subscription.js';
import { renderRectificationTab, initRectification } from './rectification.js';
import { t, getLang, initI18N, onLangChange, signName, planetName, statusName, houseLabel, houseAreaName, yearsLabel } from './i18n.js';

// 合并所有 Yoga 定义
const ALL_YOGA_DEFS = [...YOGA_DEFINITIONS, ...YOGA_EXTENDED_A, ...YOGA_EXTENDED_B];

const $ = id => document.getElementById(id);

// 全局状态
let chartData = null;
let _lastChartSummary = null;

// ============================================================================
// Tab 切换
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  const tabs = $('section-tabs');
  if (!tabs) return;
  tabs.addEventListener('click', e => {
    const btn = e.target.closest('.tab-btn');
    if (!btn) return;
    tabs.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    const panel = $(`tab-${btn.dataset.tab}`);
    if (panel) {
      panel.classList.add('active');
      // Tab 切换后重新绑定术语
      setTimeout(() => bindTerms(panel), 100);
      setTimeout(() => bindTerms(panel), 500);
    }
    // 自动将当前 Tab 滚入视区
    btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
  });

  // Tab 栏滚动提示箭头
  const hint = document.createElement('div');
  hint.className = 'tab-scroll-hint';
  hint.innerHTML = '›';
  hint.title = 'Scroll →';
  tabs.parentNode.style.position = 'relative';
  tabs.parentNode.appendChild(hint);
  function checkScrollHint() {
    const atEnd = tabs.scrollLeft + tabs.clientWidth >= tabs.scrollWidth - 10;
    hint.classList.toggle('visible', !atEnd && tabs.scrollWidth > tabs.clientWidth);
  }
  tabs.addEventListener('scroll', checkScrollHint);
  // 全局可调用，切换页面后触发
  window.__checkTabScrollHint = checkScrollHint;
  window.addEventListener('resize', checkScrollHint);
  hint.addEventListener('click', () => {
    tabs.scrollBy({ left: 200, behavior: 'smooth' });
  });
});

// ============================================================================
// 城市搜索
// ============================================================================
let debounceTimer = null;
function setupCitySearch() {
  const cityInput = $('birth-city'), suggestions = $('city-suggestions');
  const latInput = $('birth-lat'), lonInput = $('birth-lon'), tzSelect = $('birth-tz');
  cityInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const q = cityInput.value.trim();
      if (q.length < 1) { suggestions.classList.add('hidden'); return; }
      const results = searchCities(q);
      if (results.length === 0) { suggestions.classList.add('hidden'); return; }
      suggestions.innerHTML = results.map(c => {
        const label = c.en ? `${c.name} (${c.en})` : c.name;
        return `<div class="suggestion-item" data-lat="${c.lat}" data-lon="${c.lon}" data-tz="${c.tz}">${label} <small>${c.lat.toFixed(1)}°, ${c.lon.toFixed(1)}°</small></div>`;
      }).join('');
      suggestions.classList.remove('hidden');
      suggestions.querySelectorAll('.suggestion-item').forEach(el => {
        el.addEventListener('click', () => {
          const text = el.textContent.trim();
          cityInput.value = text.split(/\s+\(/)[0]; // 取中文名部分
          latInput.value = el.dataset.lat; lonInput.value = el.dataset.lon; tzSelect.value = el.dataset.tz;
          suggestions.classList.add('hidden');
        });
      });
    }, 200);
  });
  document.addEventListener('click', e => {
    if (!cityInput.contains(e.target) && !suggestions.contains(e.target)) suggestions.classList.add('hidden');
  });
}

// ============================================================================
// 日期下拉框初始化
// ============================================================================
function initDateSelects() {
  const yearEl = $('birth-year'), monthEl = $('birth-month'), dayEl = $('birth-day');
  if (!yearEl) return;
  const thisYear = new Date().getFullYear();
  for (let y = thisYear; y >= 1940; y--) {
    const opt = document.createElement('option');
    opt.value = y; opt.textContent = y;
    yearEl.appendChild(opt);
  }
  yearEl.value = '1997';
  for (let m = 1; m <= 12; m++) {
    const opt = document.createElement('option');
    opt.value = m; opt.textContent = m;
    monthEl.appendChild(opt);
  }
  function updateDays() {
    const y = parseInt(yearEl.value) || 2000;
    const m = parseInt(monthEl.value) || 1;
    const maxDay = new Date(y, m, 0).getDate();
    const curDay = parseInt(dayEl.value) || 0;
    dayEl.innerHTML = '';
    const ph = document.createElement('option');
    ph.value = ''; ph.disabled = true; ph.textContent = t('date.day');
    dayEl.appendChild(ph);
    for (let d = 1; d <= maxDay; d++) {
      const opt = document.createElement('option');
      opt.value = d; opt.textContent = d;
      dayEl.appendChild(opt);
    }
    if (curDay >= 1 && curDay <= maxDay) dayEl.value = curDay;
  }
  yearEl.addEventListener('change', updateDays);
  monthEl.addEventListener('change', updateDays);
  updateDays();
  // 更新 placeholder option 文本
  function updatePlaceholders() {
    yearEl.options[0].textContent = t('date.year');
    monthEl.options[0].textContent = t('date.month');
    if (dayEl.options[0]) dayEl.options[0].textContent = t('date.day');
  }
  updatePlaceholders();
  onLangChange(updatePlaceholders);
}

// ============================================================================
// 表单提交
// ============================================================================
function setupForm() {
  const form = $('birth-form'), btn = $('btn-calculate');
  const btnText = btn.querySelector('.btn-text'), btnLoading = btn.querySelector('.btn-loading');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const year = parseInt($('birth-year').value);
    const month = parseInt($('birth-month').value);
    const day = parseInt($('birth-day').value);
    const timeVal = $('birth-time').value;
    const lat = parseFloat($('birth-lat').value), lon = parseFloat($('birth-lon').value);
    const tz = parseFloat($('birth-tz').value);
    if (!year || !month || !day || !timeVal) { alert(t('alert.date')); return; }
    if (isNaN(lat) || isNaN(lon)) { alert(t('alert.city')); return; }
    const [hour, minute] = timeVal.split(':').map(Number);
    btnText.classList.add('hidden'); btnLoading.classList.remove('hidden'); btn.disabled = true;
    try {
      await initEngine();
      chartData = await computeChart({ year, month, day, hour, minute, lat, lon, tz });
      // 保存出生数据供生时校正使用
      window.__jyotishBirth = { year, month, day, hour, minute, lat, lon, tz };
      renderAll();
      showPage('chart');
      // 将当前星盘数据传给 AI 聊天
      aiChatSetChartData(chartData);
    } catch (err) {
      console.error('[Jyotish] Error:', err);
      alert(t('alert.error') + err.message);
    } finally {
      btnText.classList.remove('hidden'); btnLoading.classList.add('hidden'); btn.disabled = false;
    }
  });
}

// ============================================================================
// 全部渲染
// ============================================================================
function renderAll() {
  if (!chartData) return;
  const { ascendant, planets, birth_info } = chartData;
  const moonP = planets.Moon;

  // 高级计算
  computeCombustion(planets);
  const karaka = computeKaraka(planets);
  const arudha = computeArudha(planets, ascendant.sign);
  const allV = computeAllVargas(planets);
  const av = computeAshtakavarga(planets, ascendant.sign);
  const sb = computeShadbala(planets, ascendant.sign, birth_info, allV);
  const ty = computeTithiYoga(planets, birth_info);
  let dashaData = null;
  if (moonP) dashaData = computeDashaWithPratyantar(moonP.degree, birth_info.date);

  // Banner
  $('asc-sign').textContent = `${ascendant.sign} · ${signName(ascendant.sign)}`;
  $('asc-degree').textContent = `${(ascendant.degree_in_sign != null ? ascendant.degree_in_sign : ascendant.degree).toFixed(2)}°  |  ${t('asc.lord')}: ${planetName(ascendant.lord)}`;
  if (moonP) $('asc-nakshatra').textContent = `${t('asc.nakshatra')}: ${moonP.nakshatra} Pada ${moonP.nakshatra_pada}`;
  $('asc-lord-badge').textContent = `${t('asc.lord')}: ${planetName(ascendant.lord)} (${ascendant.lord})`;

  // 生时校正引导卡片：显示/绑定
  const rectPrompt = $('rect-prompt');
  const rectPanel = $('rect-panel');
  const rectOverlay = $('rect-overlay');
  if (rectPrompt && rectPanel) {
    rectPrompt.classList.remove('hidden');
    if (!rectPrompt.dataset.bound) {
      rectPrompt.dataset.bound = 'true';
      $('rect-prompt-btn').addEventListener('click', () => {
        rectPanel.classList.remove('hidden');
        if (rectOverlay) rectOverlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        initRectification();
        renderRectificationTab($('rect-content'));
      });
      $('rect-panel-close').addEventListener('click', () => {
        rectPanel.classList.add('hidden');
        if (rectOverlay) rectOverlay.classList.add('hidden');
        document.body.style.overflow = '';
      });
      if (rectOverlay) rectOverlay.addEventListener('click', () => {
        rectPanel.classList.add('hidden');
        rectOverlay.classList.add('hidden');
        document.body.style.overflow = '';
      });
    }
  }

  // 提前计算 Yogas（供星盘中心区域和 Yoga Tab 共用）
  const baseYogas = detectYogas(planets, ascendant.sign);
  let allYogas = [...baseYogas.yogas];
  for (const yd of ALL_YOGA_DEFS) {
    try {
      const combo = yd.check(planets, ascendant.sign);
      if (combo) allYogas.push({ id: yd.id, name: yd.name, name_cn: yd.name_cn, combination: combo, effects: yd.effects, strength: yd.strength, negative: yd.negative || false, category: yd.category });
    } catch (e) {}
  }

  // 构建星盘中心摘要
  const chartSummary = buildChartSummary(ascendant, moonP, dashaData, karaka, allYogas);
  _lastChartSummary = chartSummary;

  // 本命盘 Tab
  const renderFn = getChartStyle() === 'north' ? renderNorthIndianChart : renderSouthIndianChart;
  renderFn($('rasi-chart'), chartData, { summary: chartSummary });
  updatePlanetsTable(planets, allV.D9);
  renderTithiInfo(ty);
  renderArudhaQuick(arudha);

  // Karaka Tab
  renderKaraka(karaka);

  // 宫位分析 Tab
  renderHouseAnalysis(planets, ascendant.sign);

  // 相位 Tab
  renderAspects(planets);

  // Yoga Tab（使用预计算结果）
  renderYogasWith(allYogas);

  // 分盘 Tab
  renderVargas(allV, planets, ascendant);
  renderArudha(arudha);

  // Ashtakavarga Tab
  renderAshtakavarga(av, ascendant.sign);

  // Shadbala Tab
  renderShadbala(sb);

  // Dasha Tab
  if (dashaData) renderDasha3Level(dashaData);

  // Transit Tab（异步）
  renderTransit(planets, ascendant.sign, av);

  // 深度分析 Tab
  const pacdares = computePACDARES(planets, ascendant.sign);
  const houseInfluence = computeHouseInfluence(planets, ascendant.sign);
  const vargottama = detectVargottama(planets);
  const frequency = computeFrequency(planets);
  const triangle = computeTriangle(planets);
  const ramanGrades = computeRamanHouseScore(planets, ascendant.sign);
  renderFunctionalNature(ascendant.sign);
  renderPACDARES(pacdares);
  renderRamanGrades(ramanGrades);
  renderHouseInfluence(houseInfluence);
  renderVargottama(vargottama);
  renderTriangle(triangle);
  renderFrequency(frequency);

  // 三方四正映射分析
  const tkData = computeTrikonaKendra(planets, ascendant.sign);
  renderTrikonaKendra(tkData);

  // 扩展分析 Tab
  const bb = computeBhavaBala(planets, ascendant.sign, sb);
  const vim = computeVimsopaka(planets);
  const vais = computeVaiseshikamsas(vim);
  const activity = computePlanetActivity(planets);
  const pAge = computePlanetAge(planets);
  const alertness = computePlanetAlertness(planets);
  const mood = computePlanetMood(planets);
  const pinda = computeAVPinda(av);
  const extraDasas = computeAllExtraDasas(planets, ascendant.sign, birth_info.date);
  renderBhavaBala(bb);
  renderVimsopakaVaiseshikamsa(vim, vais);
  renderPlanetStates(activity, pAge, alertness, mood);
  renderAVPinda(pinda);
  renderExtraDasas(extraDasas);

  // 绑定术语 Tooltip（延迟确保所有异步渲染完成）
  setTimeout(() => bindTerms(document.querySelector('#page-chart')), 200);
  setTimeout(() => bindTerms(document.querySelector('#page-chart')), 800);
}

// ============================================================================
// 星盘中心摘要构建
// ============================================================================
function buildChartSummary(ascendant, moonP, dashaData, karaka, allYogas) {
  // 当前 Dasha 信息
  let dasha = null;
  if (dashaData?.current_dasha) {
    const md = dashaData.current_dasha;
    const ad = md.antardasha?.find(a => a.is_current);
    dasha = {
      maha: md.lord_cn || md.lord,
      antar: ad ? (ad.lord_cn || ad.lord) : '',
      period: ad ? `${ad.start} — ${ad.end}` : `${md.start || ''} — ${md.end || ''}`,
    };
  }

  // AK / DK
  let karakaSummary = null;
  if (karaka) {
    const k7 = karaka.karaka7 || {};
    karakaSummary = {
      AK: k7.AK?.planet_cn || k7.AK?.planet || null,
      DK: k7.DK?.planet_cn || k7.DK?.planet || null,
    };
  }

  // 关键 Yogas（按强度排序取前4）
  const strengthOrder = { '极强': 5, '强': 4, '中强': 3, '中': 2, '中负': 1, '负面': 0 };
  const topYogas = allYogas
    .filter(y => !y.negative)
    .sort((a, b) => (strengthOrder[b.strength] || 2) - (strengthOrder[a.strength] || 2))
    .slice(0, 4)
    .map(y => ({ name_cn: y.name_cn, negative: y.negative }));

  return {
    moonNakshatra: moonP ? `${moonP.nakshatra} P${moonP.nakshatra_pada}` : null,
    dasha,
    karaka: karakaSummary,
    topYogas,
  };
}

// ============================================================================
// 宫位分析
// ============================================================================
function renderHouseAnalysis(planets, ascSign) {
  const container = $('house-grid');
  container.innerHTML = '';
  const houses = computeHouseAnalysis(planets, ascSign);
  for (const h of houses) {
    const meaning = HOUSE_MEANINGS[h.house];
    const card = document.createElement('div');
    card.className = 'house-card';
    const occHTML = h.occupants.map(o => {
      const reading = PLANET_IN_HOUSE[o.name]?.[h.house] || '';
      const detail = PLANET_HOUSE_DETAIL[o.name]?.[h.house];
      return `<div class="occ-item" data-planet="${o.name}" data-house="${h.house}">
        <span class="occupant-badge">${PLANET_SYMBOLS[o.name]||''} ${planetName(o.name)}</span>
        ${detail ? '<span class="occ-expand-hint">▼</span>' : ''}
        ${detail ? `<div class="occ-detail" style="display:none;">
          <div class="occ-line"><span class="occ-tag occ-pos">${t('detail.pos')}</span><span class="occ-text">${detail.p}</span></div>
          <div class="occ-line"><span class="occ-tag occ-neg">${t('detail.neg')}</span><span class="occ-text">${detail.n}</span></div>
          <div class="occ-line"><span class="occ-tag occ-adv">${t('detail.adv')}</span><span class="occ-text">${detail.a}</span></div>
          <div class="occ-line"><span class="occ-tag occ-special">${t('detail.special')}</span><span class="occ-text">${detail.s}</span></div>
        </div>` : ''}
      </div>`;
    }).join('');
    let lordReading = '';
    if (h.lordHouse && meaning?.lordInHouse) lordReading = meaning.lordInHouse[h.lordHouse] || '';
    card.innerHTML = `
      <div class="house-card-header"><span class="house-card-num">${houseLabel(h.house)}</span><span class="house-card-sign">${signName(h.sign)} ${h.sign}</span></div>
      <div class="house-card-lord">${t('house.lord')}: ${planetName(h.lord)}（${houseLabel(h.lordHouse||'?')}）</div>
      ${occHTML ? `<div class="house-card-occupants">${occHTML}</div>` : ''}
      <div class="house-card-reading">${meaning ? `【${meaning.name}】${meaning.themes}` : ''}${lordReading ? `<br/>${t('house.inHouse')}: ${lordReading}` : ''}</div>
    `;
    // Bind expand/collapse for occupant details
    card.querySelectorAll('.occ-item').forEach(item => {
      const badge = item.querySelector('.occupant-badge');
      const detail = item.querySelector('.occ-detail');
      const hint = item.querySelector('.occ-expand-hint');
      if (badge && detail) {
        badge.style.cursor = 'pointer';
        badge.addEventListener('click', () => {
          const open = detail.style.display !== 'none';
          detail.style.display = open ? 'none' : 'block';
          if (hint) hint.textContent = open ? '▼' : '▲';
        });
      }
    });
    container.appendChild(card);
  }
}

// ============================================================================
// 相位
// ============================================================================
function renderAspects(planets) {
  const container = $('aspects-grid');
  container.innerHTML = '';
  const aspects = computeAspects(planets);
  if (aspects.length === 0) { container.innerHTML = `<p style="color:var(--text-muted);">${t('aspect.none')}</p>`; return; }
  for (const a of aspects) {
    const friendlyClass = a.friendly === 'friendly' ? 'aspect-friendly' : a.friendly === 'hostile' ? 'aspect-hostile' : '';
    const row = document.createElement('div');
    row.className = `aspect-row ${friendlyClass}`;
    const aspType = a.type === 'opposition' ? t('aspect.opposition') : a.type === 'trine' ? t('aspect.trine') : t('aspect.special');
    row.innerHTML = `
      <span class="aspect-from">${PLANET_SYMBOLS[a.from]||''} ${planetName(a.from)}</span>
      <span class="aspect-arrow">→ ${houseLabel(a.toHouse)} →</span>
      <span class="aspect-to">${PLANET_SYMBOLS[a.to]||''} ${planetName(a.to)}</span>
      <span class="aspect-type ${a.type}">${aspType}</span>
    `;
    container.appendChild(row);
  }
}

// ============================================================================
// Yoga（扩展版 — 接受预计算结果）
// ============================================================================
function renderYogasWith(allYogas) {
  const container = $('yoga-cards'), summary = $('yoga-summary');
  container.innerHTML = ''; summary.innerHTML = '';
  const positive = allYogas.filter(y => !y.negative).length;
  const negative = allYogas.filter(y => y.negative).length;
  summary.innerHTML = `<div class="yoga-stat"><strong>${allYogas.length}</strong> ${t('yoga.count')}</div><div class="yoga-stat"><strong>${positive}</strong> ${t('yoga.bene')}</div>${negative > 0 ? `<div class="yoga-stat"><strong>${negative}</strong> ${t('yoga.male')}</div>` : ''}`;
  if (allYogas.length === 0) { container.innerHTML = `<p style="color:var(--text-muted);">${t('yoga.none')}</p>`; return; }
  for (const y of allYogas) {
    const card = document.createElement('div');
    card.className = 'yoga-card';
    if (y.negative) card.style.borderLeft = '3px solid #f87171';
    const detail = YOGA_DETAILS[y.id];
    let detailHTML = '';
    if (detail) {
      const eff = detail.e || {};
      detailHTML = `<div class="yoga-detail" style="display:none;">
        <div class="yd-section"><span class="yd-label">${t('yoga.formation')}</span><span class="yd-text">${detail.f}</span></div>
        ${eff.c ? `<div class="yd-section"><span class="yd-label">${t('detail.career')}</span><span class="yd-text">${eff.c}</span></div>` : ''}
        ${eff.w ? `<div class="yd-section"><span class="yd-label">${t('detail.wealth')}</span><span class="yd-text">${eff.w}</span></div>` : ''}
        ${eff.m ? `<div class="yd-section"><span class="yd-label">${t('detail.marriage')}</span><span class="yd-text">${eff.m}</span></div>` : ''}
        ${eff.h ? `<div class="yd-section"><span class="yd-label">${t('detail.health')}</span><span class="yd-text">${eff.h}</span></div>` : ''}
        ${detail.x ? `<div class="yd-section"><span class="yd-label">${t('yoga.cancel')}</span><span class="yd-text">${detail.x}</span></div>` : ''}
        ${detail.t?.length ? `<div class="yd-tags">${detail.t.map(tag=>`<span class="yd-tag">${tag}</span>`).join('')}</div>` : ''}
      </div>`;
    }
    card.innerHTML = `
      <div class="yoga-header" style="cursor:pointer;">
        <div class="yoga-name">${y.name}</div><div class="yoga-name-cn">${y.name_cn}${y.category ? ` <small style="color:var(--text-muted);font-size:10px;">[${y.category}]</small>` : ''}</div>
        <div class="yoga-combo">${y.combination}</div>
        <div style="font-size:11px;color:var(--text-secondary);margin:4px 0;">${y.effects||''}</div>
        <span class="yoga-strength">${y.strength}</span>
        ${detail ? `<span class="yoga-expand-hint">${t('yoga.expand')}</span>` : ''}
      </div>
      ${detailHTML}
    `;
    if (detail) {
      const header = card.querySelector('.yoga-header');
      const detailEl = card.querySelector('.yoga-detail');
      const hint = card.querySelector('.yoga-expand-hint');
      header.addEventListener('click', () => {
        const open = detailEl.style.display !== 'none';
        detailEl.style.display = open ? 'none' : 'block';
        if (hint) hint.textContent = open ? t('yoga.expand') : t('yoga.collapse');
      });
    }
    container.appendChild(card);
  }
}

// ============================================================================
// Yoga（原版 — 兼容保留）
// ============================================================================
function renderYogas(planets, ascSign) {
  const container = $('yoga-cards'), summary = $('yoga-summary');
  container.innerHTML = ''; summary.innerHTML = '';
  const baseYogas = detectYogas(planets, ascSign);
  let allYogas = [...baseYogas.yogas];
  for (const yd of ALL_YOGA_DEFS) {
    try {
      const combo = yd.check(planets, ascSign);
      if (combo) allYogas.push({ name: yd.name, name_cn: yd.name_cn, combination: combo, effects: yd.effects, strength: yd.strength, negative: yd.negative || false });
    } catch (e) {}
  }
  const positive = allYogas.filter(y => !y.negative).length;
  const negative = allYogas.filter(y => y.negative).length;
  summary.innerHTML = `<div class="yoga-stat"><strong>${allYogas.length}</strong> ${t('yoga.count')}</div><div class="yoga-stat"><strong>${positive}</strong> ${t('yoga.bene')}</div>${negative > 0 ? `<div class="yoga-stat"><strong>${negative}</strong> ${t('yoga.male')}</div>` : ''}`;
  if (allYogas.length === 0) { container.innerHTML = `<p style="color:var(--text-muted);">${t('yoga.none')}</p>`; return; }
  for (const y of allYogas) {
    const card = document.createElement('div');
    card.className = 'yoga-card';
    if (y.negative) card.style.borderLeft = '3px solid #f87171';
    card.innerHTML = `
      <div class="yoga-name">${y.name}</div><div class="yoga-name-cn">${y.name_cn}${y.category ? ` <small style="color:var(--text-muted);font-size:10px;">[${y.category}]</small>` : ''}</div>
      <div class="yoga-combo">${y.combination}</div>
      <div style="font-size:11px;color:var(--text-secondary);margin:4px 0;">${y.effects||''}</div>
      <span class="yoga-strength">${y.strength}</span>
    `;
    container.appendChild(card);
  }
}

// ============================================================================
// Transit 推运（v2.0 增强）
// ============================================================================
let _lastTransitData = null;

async function renderTransit(natalPlanets, ascSign, avData) {
  $('transit-date').textContent = t('transit.computing');
  try {
    // 读取用户选择的日期（如果有）
    const dateInput = $('transit-date-input');
    const timeInput = $('transit-time-input');
    const dateStr = dateInput?.value || null;
    const timeStr = timeInput?.value || null;
    const tz = chartData?.birth_info?.tz || 0;

    const transit = await computeTransit(dateStr, timeStr, tz);
    _lastTransitData = { transit, natalPlanets, ascSign };

    $('transit-date').textContent = `${transit.date} ${transit.time} UT · Ayanamsa: ${transit.ayanamsa}°`;

    // Transit 星盘渲染
    const tChartData = { ascendant: { sign: ascSign }, planets: {} };
    for (const [pn, pi] of Object.entries(transit.planets)) {
      tChartData.planets[pn] = { ...pi, status: '中性', house: 1 };
    }
    renderSouthIndianChart($('transit-chart'), tChartData);

    // 全行星 Transit 表格
    const overlay = computeTransitOverlay(natalPlanets, ascSign, transit.planets);
    const tableContainer = $('transit-all-table');
    if (tableContainer) {
      let html = `<table class="planets-table transit-planets-table">
        <thead><tr><th>行星</th><th>Transit星座</th><th>度数</th><th>本命宫位</th><th>逆行</th><th>星宿</th><th>本命星座</th><th>换座</th></tr></thead><tbody>`;
      for (const p of overlay.all) {
        const changeClass = p.sign_changed ? 'style="color:var(--red);font-weight:600"' : '';
        html += `<tr>
          <td><span class="planet-symbol">${p.symbol}</span> ${planetName(p.planet)}</td>
          <td>${signName(p.transit_sign)}</td>
          <td>${p.transit_degree_in_sign.toFixed(2)}°</td>
          <td><span class="transit-house-badge">H${p.transit_house}</span></td>
          <td>${p.retrograde ? '<span style="color:var(--red)">℞</span>' : ''}</td>
          <td>${p.transit_nakshatra} P${p.transit_nakshatra_pada}</td>
          <td>${p.natal_sign ? signName(p.natal_sign) : '-'}</td>
          <td ${changeClass}>${p.sign_changed ? '⚡' + t('col.change') : ''}</td>
        </tr>`;
      }
      html += '</tbody></table>';
      tableContainer.innerHTML = html;
    }

    // 慢星详细分析
    const slowContainer = $('transit-overlay');
    slowContainer.innerHTML = '';
    for (const item of overlay.slow) {
      const effect = TRANSIT_EFFECTS[item.planet]?.[item.transit_house] || '';
      const cjStr = item.conjunctions.length > 0
        ? `<div class="transit-conj">${t('transit.conj')}: ${item.conjunctions.map(c => `${planetName(c.planet)}(${c.degree_diff}°)`).join(', ')}</div>` : '';
      const aspStr = item.aspects.length > 0
        ? `<div class="transit-asp">${t('transit.asp')}: ${item.aspects.map(a => `${planetName(a.to)}[H${a.to_house}](${a.type})`).join(', ')}</div>` : '';
      const div = document.createElement('div');
      div.className = 'transit-overlay-item';
      div.innerHTML = `<span class="planet-symbol">${item.symbol}</span>
        <div class="transit-planet-info">
          <div class="transit-planet-name">${planetName(item.planet)} ${item.retrograde ? '℞' : ''} → ${houseLabel(item.transit_house)}</div>
          <div class="transit-planet-detail">${signName(item.transit_sign)} ${item.transit_degree_in_sign.toFixed(2)}° ${item.retrograde ? t('ss.retro') : ''}</div>
          ${effect ? `<div class="transit-effect">${effect}</div>` : ''}
          ${cjStr}${aspStr}
        </div>`;
      slowContainer.appendChild(div);
    }

    // Double Transit
    const doubleTransits = computeDoubleTransit(transit.planets, ascSign);
    const dtSection = $('double-transit-section');
    dtSection.innerHTML = '';
    if (doubleTransits.length > 0) {
      dtSection.innerHTML = `<h4 class="sub-title">${t('dt.title')}</h4>`;
      for (const dt of doubleTransits) {
        const detail = dt.aspectedBy.map(a => `${planetName(a.planet)}(H${a.from_house}→H${a.offset})`).join(' + ');
        dtSection.innerHTML += `<div class="dt-card"><div class="dt-house">${dt.desc}</div><div class="dt-detail">${detail}</div></div>`;
      }
    }

    // Sade Sati（增强版）
    const ss = checkSadeSati(natalPlanets.Moon?.sign || '', transit.planets);
    const ssSection = $('sade-sati-section');
    ssSection.innerHTML = '';
    if (ss) {
      ssSection.innerHTML = `<h4 class="sub-title">${t('ss.detect')}</h4>
        <div class="sade-sati-badge ${ss.active ? 'active' : 'inactive'}">${ss.active ? `[!] ${ss.desc}` : (ss.phase === 0 ? `[~] ${ss.desc}` : `[OK] ${t('ss.active')}`)}</div>
        ${ss.detail ? `<div class="sade-sati-detail">${ss.detail}</div>` : ''}
        <div class="sade-sati-info">${t('ss.moon')}: ${signName(ss.natal_moon_sign)} · ${t('ss.saturn')}: ${signName(ss.saturn_sign)} ${ss.saturn_degree_in_sign.toFixed(2)}° ${ss.saturn_retrograde ? t('ss.retro') : ''}</div>`;
    }

    // Ashtakavarga Transit 评分
    if (avData) {
      const avScores = computeTransitAVScore(transit.planets, ascSign, avData);
      const avSection = $('transit-av-section');
      if (avSection && avScores) {
        let avHTML = `<h4 class="sub-title">${t('tav.title')}</h4><div class="transit-av-grid">`;
        for (const s of avScores) {
          const qClass = s.transit_quality === 'favorable' ? 'av-fav' : s.transit_quality === 'challenging' ? 'av-chal' : 'av-neu';
          avHTML += `<div class="transit-av-item ${qClass}">
            <span class="av-planet">${planetName(s.planet)}</span>
            <span class="av-sign">${signName(s.transit_sign)}</span>
            <span class="av-score">SAV: ${s.sav_score ?? '-'}</span>
            <span class="av-quality">${s.transit_quality === 'favorable' ? t('quality.fav') : s.transit_quality === 'challenging' ? t('quality.chal') : t('quality.neu')}</span>
          </div>`;
        }
        avHTML += '</div>';
        avSection.innerHTML = avHTML;
      }
    }

    // 宫位影响摘要
    const houseImpact = computeTransitHouseImpact(transit.planets, ascSign);
    const hiSection = $('transit-house-impact');
    if (hiSection) {
      let hiHTML = `<h4 class="sub-title">${t('thi.title')}</h4><div class="house-impact-grid">`;
      for (let h = 1; h <= 12; h++) {
        const hi = houseImpact[h];
        const total = hi.transiting.length + hi.aspected_by.length;
        const intensity = total >= 3 ? 'intense' : total >= 2 ? 'moderate' : 'light';
        hiHTML += `<div class="hi-card hi-${intensity}">
          <div class="hi-house">H${h} <small>${houseAreaName(h)}</small></div>
          <div class="hi-planets">${hi.transiting.map(t => `<span class="hi-transit">${planetName(t.planet)}${t.retrograde?'℞':''}</span>`).join('')}</div>
          <div class="hi-aspects">${hi.aspected_by.map(a => `<span class="hi-asp">${planetName(a.planet)}(${a.aspect_type})</span>`).join('')}</div>
        </div>`;
      }
      hiHTML += '</div>';
      hiSection.innerHTML = hiHTML;
    }
  } catch (err) {
    console.error('[Transit] Error:', err);
    $('transit-date').textContent = 'Transit 计算失败: ' + err.message;
  }
}

// ============================================================================
// 页面切换 + 初始化
// ============================================================================
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  if (name === 'input') $('page-input').classList.add('active');
  else if (name === 'chart') {
    $('page-chart').classList.add('active');
    // 延迟触发 Tab 滚动提示检查（需等 DOM 渲染完毕）
    setTimeout(() => { if (window.__checkTabScrollHint) window.__checkTabScrollHint(); }, 100);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // 初始化 i18n
  initI18N();
  // 语言变化时重新渲染
  onLangChange(() => {
    if (chartData) renderAll();
  });

  initDateSelects();
  setupCitySearch();
  setupForm();
  $('btn-back').addEventListener('click', () => showPage('input'));
  // 初始化术语 Tooltip
  initTooltip();
  // 初始化认证系统
  initAuth();
  // 初始化订阅系统
  initSubscription();
  // 初始化 AI 聊天
  initAIChat();
  // Transit 更新按钮
  const transitBtn = $('btn-transit-update');
  if (transitBtn) {
    transitBtn.addEventListener('click', async () => {
      if (!chartData) return;
      const { planets, ascendant, birth_info } = chartData;
      const allV = computeAllVargas(planets);
      const av = computeAshtakavarga(planets, ascendant.sign);
      await renderTransit(planets, ascendant.sign, av);
    });
  }
  // 导出功能
  setupExport();
  // 星盘风格切换
  setupChartStyle();
});

// ============================================================================
// 导出辅助函数
// ============================================================================
function _getBirthNakIdx(planets) {
  const moonLon = planets.Moon?.degree || 0;
  return Math.floor(moonLon / (360 / 27)) % 27;
}

function _buildAspectsModule(planets) {
  const rawAspects = computeAspects(planets);
  const aspects = (rawAspects || []).map(a => ({
    planet1: a.from, planet2: a.to,
    type: a.offset === 7 ? 'opposition' : (a.offset === 5 || a.offset === 9) ? 'trine' : `aspect_${a.offset}`,
    aspect_degree: a.offset * 30,
    actual_diff: Math.abs((planets[a.from]?.degree || 0) - (planets[a.to]?.degree || 0)),
    orb: 0, orb_category: 'standard',
    applying: false, strength: 0,
    description: `${a.from}→${a.to}(${a.offset}宫相位)`,
    friendly: a.friendly,
  }));
  // Conjunctions
  const names = Object.keys(planets).filter(p => !planets[p].error);
  const conjunctions = [];
  for (let i = 0; i < names.length; i++) {
    for (let j = i + 1; j < names.length; j++) {
      const d1 = planets[names[i]].degree, d2 = planets[names[j]].degree;
      const diff = Math.min(Math.abs(d1 - d2), 360 - Math.abs(d1 - d2));
      if (diff < 10) conjunctions.push({ planet1: names[i], planet2: names[j], orb: Math.round(diff * 100) / 100 });
    }
  }
  return { aspects, conjunctions, summary: `${aspects.length} aspects, ${conjunctions.length} conjunctions` };
}

function _buildAVModule(av) {
  if (!av) return null;
  return {
    method: 'Parashara BPHS',
    bav: av.bav_raw,
    sav: { scores: av.sav },
    sav_total: av.sav_total,
    sav_by_house: av.sav_by_house,
    bav_by_house: av.bav_by_house,
  };
}

function _buildJaiminiModule(karaka, charaDasha, karakamsha) {
  const k7 = karaka?.karaka7 || {};
  const k8 = karaka?.karaka8 || {};
  const DOMAIN = {
    AK: '灵魂使命、核心自我、人生最高目标', AmK: '事业方向、主要谋士、权力代理',
    BK: '兄弟姐妹、勇气、冒险精神', MK: '母亲、家庭根基、情感安全感',
    PK: '子女、创造力、学生、智能成果', GK: '竞争对手、疾病、障碍、转化力量',
    DK: '配偶特质、伴侣关系、婚姻质量', PiK: '父亲、祖先、遗产',
  };
  const CN = {
    AK: '灵魂星AK', AmK: '事业星AmK', BK: '兄弟星BK', MK: '母亲星MK',
    PK: '子女星PK', GK: '障碍星GK', DK: '配偶星DK', PiK: '父亲星PiK',
  };
  const kt7 = {}, kt8 = {};
  let rank = 1;
  for (const [k, v] of Object.entries(k7)) {
    kt7[k] = { ...v, rank: rank++, domain: DOMAIN[k] || '', cn_name: CN[k] || '' };
  }
  rank = 1;
  for (const [k, v] of Object.entries(k8)) {
    kt8[k] = { ...v, rank: rank++, domain: DOMAIN[k] || '', cn_name: CN[k] || '' };
  }
  return {
    chara_karaka_7: {
      karaka_table: kt7,
      summary: {
        AK: k7.AK ? `${k7.AK.planet} (${k7.AK.degree}°)` : '',
        DK: k7.DK ? `${k7.DK.planet} (${k7.DK.degree}°)` : '',
        AK_domain: DOMAIN.AK, DK_domain: DOMAIN.DK,
      },
    },
    chara_karaka_8: { karaka_table_8: kt8 },
    chara_dasha: charaDasha,
    karakamsha,
  };
}

// ============================================================================
// 导出功能
// ============================================================================
function setupExport() {
  const btnExport = $('btn-export');
  const menu = $('export-menu');
  if (!btnExport || !menu) return;

  btnExport.addEventListener('click', (e) => {
    e.stopPropagation();
    menu.classList.toggle('hidden');
  });
  document.addEventListener('click', () => menu.classList.add('hidden'));

  menu.querySelectorAll('.export-item').forEach(item => {
    item.addEventListener('click', () => {
      menu.classList.add('hidden');
      if (!chartData) { alert(t('alert.chart')); return; }
      const format = item.dataset.format;
      if (format === 'json') {
        const { planets, ascendant, birth_info } = chartData;
        // ── 收集全部13模块 ──
        const vargas = computeAllVargas(planets);
        const karaka = computeKaraka(planets);
        const av = computeAshtakavarga(planets, ascendant.sign);
        const sb = computeShadbala(planets, ascendant.sign, birth_info, vargas);
        const dasha = computeDashaWithPratyantar(planets.Moon?.degree || 0, birth_info.date, new Date().toISOString().split('T')[0]);
        const yogas = [...detectYogas(planets, ascendant.sign)];
        // Extended yogas
        try { yogas.push(...detectExtendedYogas(planets, ascendant.sign)); } catch(e) {}
        const aspects = _buildAspectsModule(planets);
        const panchanga = computeTithiYoga(planets, birth_info);
        const nakshatraAdvanced = computeNakshatraAdvanced(planets, _getBirthNakIdx(planets));
        const charaDasha = computeCharaDasha(planets, ascendant.sign);
        const karakamsha = computeKarakamsha(planets);
        const ascIdx = SIGNS.indexOf(ascendant.sign);
        const planetSignIdx = {};
        for (const [pn, p] of Object.entries(planets)) { if (!p.error) planetSignIdx[pn] = Math.floor(p.degree / 30); }
        const argala = computeArgala(planetSignIdx, ascIdx);
        const birthYear = parseInt((birth_info.date || '').split('-')[0]) || 1990;
        const birthMonth = parseInt((birth_info.date || '').split('-')[1]) || 1;
        const tajika = computeTajika(planets, ascendant.sign, birthYear, birthMonth);
        const validation = computeValidation(planets, ascendant, av, dasha);
        const audit = computeAudit(planets, ascendant, av, validation);
        const actionableCtx = computeActionableContext(planets, ascendant);
        const jaimini = _buildJaiminiModule(karaka, charaDasha, karakamsha);

        exportJSON(chartData, {
          dasha, yogas, vargas, aspects, jaimini,
          nakshatraAdvanced, argala, tajika,
          shadbala: sb, ashtakavarga: _buildAVModule(av),
          panchanga, validation, audit, actionableContext,
        });
      } else if (format === 'svg') {
        const chartEl = $('rasi-chart');
        exportSVG(chartEl, `jyotish-${chartData.birth_info?.date || 'chart'}`);
      } else if (format === 'png') {
        const chartEl = $('rasi-chart');
        exportPNG(chartEl, `jyotish-${chartData.birth_info?.date || 'chart'}`);
      }
    });
  });
}

// ============================================================================
// 星盘风格切换
// ============================================================================
function setupChartStyle() {
  const btns = document.querySelectorAll('.style-btn');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      const style = btn.dataset.style;
      setChartStyle(style);
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      // 重新渲染本命盘
      if (chartData) {
        const fn = style === 'north' ? renderNorthIndianChart : renderSouthIndianChart;
        fn($('rasi-chart'), chartData, { summary: _lastChartSummary });
      }
    });
  });
}
