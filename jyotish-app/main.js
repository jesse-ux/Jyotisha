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
  DASHA_THEMES, ASCENDANT_TABLE, PLANET_DIGNITY, NEECHA_BHANGA_RULES,
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
  computeDoubleTransitPAC, computeTransitLL7L, computePlanetaryCongregation, computeVivahSaham,
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
  renderFrequency, renderTriangle, renderRamanGrades, renderTrikonaKendra, renderArgala,
} from './analysis-renderers.js';
import {
  computeBhavaBala, computeVimsopaka, computeVaiseshikamsas,
  computePlanetActivity, computePlanetAge, computePlanetAlertness, computePlanetMood,
  computeAVPinda, computeAllExtraDasas,
} from './jyotish-extended.js';
import {
  renderBhavaBala, renderVimsopakaVaiseshikamsa, renderPlanetStates, renderAVPinda, renderExtraDasas,
} from './renderers.js';
import { computeArgala } from './argala.js';
import { computeTajika } from './tajika.js';
import { computeNakshatraAdvanced, computeCharaDasha, computeKarakamsha } from './jyotish-advanced.js';
import { computeValidation, computeAudit, computeActionableContext } from './jyotish-export-modules.js';
import { initTooltip, bindTerms, setGlossaryTerminologyMode } from './glossary.js';
import { initAIChat, aiChatSetChartData } from './ai-chat.js';
import { initAuth } from './auth.js';
import { initSubscription } from './subscription.js';
import { renderRectificationTab, initRectification } from './rectification.js';
import { t, getLang, initI18N, onLangChange, signName, planetName, statusName, houseLabel, houseAreaName, yearsLabel } from './i18n.js';
import { escapeHtml, escapeAttr, safeNumber } from './security.js';
import { renderSkillCoverage } from './skill-map.js';
import { initChartImport } from './import-chart.js';
import { buildMEVGAudit, renderMEVGAudit } from './mevg-audit.js';

// 合并所有 Yoga 定义
const ALL_YOGA_DEFS = [...YOGA_DEFINITIONS, ...YOGA_EXTENDED_A, ...YOGA_EXTENDED_B];
const D9_MALEFICS = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'];
const D9_GREEN_HOUSES = [1, 3, 4, 5, 7, 9, 10];
const D9_HARD_HOUSES = [6, 8, 12];
const NODE_DIGNITY = {
  Rahu: { exaltation: { sign: 'Taurus' }, debilitation: { sign: 'Scorpio' }, ownSigns: [] },
  Ketu: { exaltation: { sign: 'Scorpio' }, debilitation: { sign: 'Taurus' }, ownSigns: [] },
};
const PANCHANGA_ACTIVITIES = [
  ['all', '全部活动'],
  ['marriage', '婚礼'],
  ['business', '开业/签约'],
  ['travel', '出行'],
  ['medical', '医疗'],
  ['education', '学习/入学'],
];
const PANCHANGA_CONDITIONS = [
  ['all', '全部条件'],
  ['has_vrata', 'Vrata/节日标签'],
  ['festival_candidate', '节日候选'],
  ['spiritual_practice', '修行/祈福'],
  ['auspicious_activity', '适合所选活动'],
  ['avoid_new_start', '不宜新开始'],
  ['good_choghadiya', '有吉利 Choghadiya'],
];
const PANCHANGA_CONDITION_GUIDE = {
  all: '显示范围内所有日期。',
  has_vrata: '当天存在 vrata、lunar observance 或节日候选标签。',
  festival_candidate: '节日名称仍需 lunar masa 或传统规则确认，当前只作为候选窗口。',
  spiritual_practice: '适合斋戒、祈福、修行或月相观察的保守标签。',
  auspicious_activity: '所选活动或当日综合质量给出推荐倾向。',
  avoid_new_start: '含不宜新开始、活动避开或质量偏弱的提醒。',
  good_choghadiya: '当天存在吉利 Choghadiya 子时段，可作为日内择时入口。',
};
const PANCHANGA_CONDITION_MODES = [
  ['all', '满足全部'],
  ['any', '满足任一'],
];
const DEMO_BIRTH = {
  year: 1990,
  month: 1,
  day: 1,
  hour: 12,
  minute: 0,
  lat: 39.9,
  lon: 116.4,
  tz: 8,
  city: '北京',
};
const CASE_GROUP_PRESETS = ['全部分组', '家庭', '伴侣', '客户', '研究', '朋友', '未分组'];
const CASE_RELATION_PRESETS = [
  ['all', '全部关系'],
  ['self', '本人'],
  ['partner', '伴侣/婚恋'],
  ['family', '家庭'],
  ['client', '客户'],
  ['research', '研究'],
  ['friend', '朋友'],
  ['unknown', '未标注'],
];

const $ = id => document.getElementById(id);
const PRODUCT_GAP_DOC = '/Users/wuyongnaren/Documents/印度占星/docs/research/product_gap_matrix_2026_06_22.md';
const CHART_LIBRARY_KEY = 'jyotish_chart_library';
const SYNASTRY_PAIR_LIBRARY_KEY = 'jyotish_synastry_pair_library';
const PRASHNA_CASE_LIBRARY_KEY = 'jyotish_prashna_case_library';
const CALCULATION_SETTINGS_KEY = 'jyotish_calculation_settings';
const TERMINOLOGY_MODE_KEY = 'jyotish_terminology_mode';
const TRUST_CENTER_STORAGE_KEYS = [
  CHART_LIBRARY_KEY,
  SYNASTRY_PAIR_LIBRARY_KEY,
  PRASHNA_CASE_LIBRARY_KEY,
  CALCULATION_SETTINGS_KEY,
  TERMINOLOGY_MODE_KEY,
  'jyotish_ai_messages',
  'jyotish_user_profile',
  'jyotish_subscription_state',
];
const DEFAULT_CALCULATION_SETTINGS = {
  ayanamsa: 'lahiri',
  nodeMode: 'mean',
  houseSystem: 'whole_sign',
  sunrisePolicy: 'auto_solar',
  geocoderPolicy: 'local_city_db',
  ephemerisBackend: 'swisseph_local',
  terminologyMode: 'balanced',
  yogaVariant: 'bvr_structured',
  jaiminiKarakaVariant: 'seven_and_eight',
  kpSignificatorVariant: 'abcd_weighted',
  ashtakavargaVariant: 'bphs_pav_sodhita',
  shadbalaVariant: 'relative_internal',
  dashaReference: 'birth_moon',
};
const TERMINOLOGY_MODE_OPTIONS = {
  balanced: {
    label: '平衡模式',
    shortLabel: 'Balanced',
    note: '同时显示中文、Sanskrit、English 和短解释。',
  },
  beginner: {
    label: '入门模式',
    shortLabel: 'Beginner',
    note: '优先现代生活语言，减少缩写负担。',
  },
  professional: {
    label: '专业模式',
    shortLabel: 'Pro',
    note: '保留中文、英文和 Sanskrit 对照。',
  },
};
const CALCULATION_SETTING_OPTIONS = {
  ayanamsa: [
    ['lahiri', 'Lahiri / Chitrapaksha'],
    ['raman', 'Raman'],
    ['kp', 'KP / Krishnamurti'],
  ],
  nodeMode: [
    ['mean', 'Mean node / 平均罗喉'],
    ['true', 'True node / 真罗喉'],
  ],
  houseSystem: [
    ['whole_sign', 'Whole Sign / Rashi'],
    ['sripati', 'Sripati Bhava Chalit（专项接口）'],
    ['equal', 'Equal House（专项接口）'],
    ['placidus', 'Placidus（专项接口）'],
  ],
  sunrisePolicy: [
    ['auto_solar', '按地点计算日出/日落'],
    ['manual_time', '使用面板手填日出/日落'],
  ],
  geocoderPolicy: [
    ['local_city_db', '本地城市库'],
    ['manual_coordinates', '手动经纬度优先'],
  ],
  ephemerisBackend: [
    ['swisseph_local', 'Swiss Ephemeris / 本地 API 主路径'],
    ['swisseph_wasm', 'SwissEph WASM / 浏览器降级'],
    ['xalen_spike', 'xalen-ephemeris Apache-2.0 可行性记录'],
  ],
  terminologyMode: [
    ['balanced', '平衡：术语 + 短解释'],
    ['beginner', '初学：现代生活语言优先'],
    ['professional', '专业：Sanskrit / English / 技法名优先'],
  ],
  yogaVariant: [
    ['bvr_structured', 'B.V. Raman/PyJHora 对齐规则（当前）'],
    ['conservative_classic', '保守经典规则（后续切换）'],
    ['functional_plus_classic', '功能性 + 经典 Yoga（后续切换）'],
  ],
  jaiminiKarakaVariant: [
    ['seven_and_eight', '7/8 Karaka 双口径展示（当前）'],
    ['seven_karaka', '7 Karaka 固定口径（后续切换）'],
    ['eight_karaka_rahu', '8 Karaka 含 Rahu（后续切换）'],
  ],
  kpSignificatorVariant: [
    ['abcd_weighted', 'ABCD Significator 加权（当前）'],
    ['traditional_sub_lord', '传统 Star/Sub/Sub-Sub（后续切换）'],
    ['question_domain_focus', '按问题域重点宫位（后续切换）'],
  ],
  ashtakavargaVariant: [
    ['bphs_pav_sodhita', 'BPHS BAV/SAV + PAV/Sodhita（当前）'],
    ['sav_bav_only', '仅 SAV/BAV 快速层（后续切换）'],
    ['transit_av_weighted', 'Transit AV 加权（后续切换）'],
  ],
  shadbalaVariant: [
    ['relative_internal', '内部相对强弱（当前）'],
    ['absolute_benchmark', '外部绝对值校准（后续切换）'],
    ['ishta_kashta_weighted', 'Ishta/Kashta 加权（后续切换）'],
  ],
  dashaReference: [
    ['birth_moon', '出生月亮星宿起算（当前）'],
    ['query_date_snapshot', '按查询日期快照（后续切换）'],
    ['multi_system_convergence', '多 Dasha 共振（后续切换）'],
  ],
};

// 全局状态
let chartData = null;
let _lastChartSummary = null;
let _lastSynastryPairRecord = null;
let _lastPrashnaCaseRecord = null;
let _caseWorkspaceSelection = new Set();
let _caseWorkspacePreview = null;
let _exportInProgress = false;

// ============================================================================
// Tab 切换
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  const tabs = $('section-tabs');
  if (!tabs) return;
  tabs.addEventListener('click', e => {
    const btn = e.target.closest('.tab-btn');
    if (!btn || !btn.dataset.tab) return;
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

function switchToTab(tabName) {
  const tabs = $('section-tabs');
  if (!tabs || !tabName) return;
  const btn = [...tabs.querySelectorAll('.tab-btn')].find(item => item.dataset.tab === tabName);
  if (btn) btn.click();
}

// ============================================================================
// 城市搜索
// ============================================================================
let debounceTimer = null;
function setupCitySearch() {
  const cityInput = $('birth-city'), suggestions = $('city-suggestions');
  const latInput = $('birth-lat'), lonInput = $('birth-lon'), tzSelect = $('birth-tz');
  cityInput.addEventListener('input', () => {
    latInput.value = '';
    lonInput.value = '';
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const q = cityInput.value.trim();
      if (q.length < 1) { suggestions.classList.add('hidden'); return; }
      const results = searchCities(q);
      if (results.length === 0) { suggestions.classList.add('hidden'); return; }
      suggestions.innerHTML = results.map(c => {
        const lat = safeNumber(c.lat);
        const lon = safeNumber(c.lon);
        const tz = safeNumber(c.tz);
        const label = c.en ? `${c.name} (${c.en})` : c.name;
        return `<div class="suggestion-item" data-lat="${escapeAttr(lat)}" data-lon="${escapeAttr(lon)}" data-tz="${escapeAttr(tz)}">${escapeHtml(label)} <small>${lat.toFixed(1)}°, ${lon.toFixed(1)}°</small></div>`;
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

function normalizeCityText(value) {
  return String(value || '').trim().toLowerCase().replace(/\s+/g, ' ');
}

function applyCityToBirthForm(city) {
  if (!city) return false;
  const lat = safeNumber(city.lat);
  const lon = safeNumber(city.lon);
  const tz = safeNumber(city.tz);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return false;
  const label = city.en ? `${city.name} (${city.en})` : city.name;
  $('birth-city').value = city.name || city.en || label;
  $('birth-lat').value = lat;
  $('birth-lon').value = lon;
  if (Number.isFinite(tz)) $('birth-tz').value = String(tz);
  const suggestions = $('city-suggestions');
  if (suggestions) suggestions.classList.add('hidden');
  return true;
}

function resolveTypedBirthCity() {
  const lat = parseFloat($('birth-lat').value);
  const lon = parseFloat($('birth-lon').value);
  if (Number.isFinite(lat) && Number.isFinite(lon)) return true;
  const q = $('birth-city').value.trim();
  if (!q) return false;
  const results = searchCities(q);
  if (!results.length) return false;
  const target = normalizeCityText(q);
  const exact = results.find(city => {
    const names = [city.name, city.en, city.en ? `${city.name} (${city.en})` : city.name];
    return names.some(name => normalizeCityText(name) === target);
  });
  return applyCityToBirthForm(exact || (results.length === 1 ? results[0] : null));
}

function getBrowserTimezoneOffset() {
  const tz = -new Date().getTimezoneOffset() / 60;
  return Number.isFinite(tz) ? tz : 0;
}

function resolveTimezoneValue(value) {
  const raw = String(value ?? '').trim();
  if (!raw || raw === 'auto') return getBrowserTimezoneOffset();
  const utc = raw.match(/^UTC\s*([+-]?\d{1,2})(?::?(\d{2}))?/i);
  if (utc) {
    const hours = Number(utc[1]);
    const minutes = Number(utc[2] || 0);
    if (Number.isFinite(hours) && Number.isFinite(minutes)) {
      return hours + (hours >= 0 ? minutes / 60 : -minutes / 60);
    }
  }
  const tz = Number(raw);
  return Number.isFinite(tz) ? tz : getBrowserTimezoneOffset();
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
async function computeChartForBirth(birth) {
  const { year, month, day, hour, minute, second = 0, lat, lon, tz } = birth;
  const settings = readCalculationSettings();
  const payload = applyCalculationSettingsToPayload({ year, month, day, hour, minute, second, lat, lon, tz });
  if (!payload.ayanamsa) payload.ayanamsa = settings.ayanamsa;
  const apiChart = await window.JyotishAPI?.computeWithPython(payload);
  if (apiChart?.success) {
    console.log('[Jyotish] ✅ 本地 API 服务 —', apiChart.dasha_count, 'Dasha');
    return attachCalculationSettings(apiChart, settings);
  }
  await initEngine();
  const fallbackChart = await computeChart({ year, month, day, hour, minute, second, lat, lon, tz });
  fallbackChart._fallback = true;
  fallbackChart._calculation_boundary = {
    ayanamsa: settings.ayanamsa,
    appliedAyanamsa: 'lahiri',
    note: settings.ayanamsa === 'lahiri'
      ? 'Browser fallback uses Lahiri-compatible SwissEph WASM path.'
      : `Browser fallback cannot apply ${settings.ayanamsa}; start the local API service to calculate this ayanamsa.`,
  };
  attachCalculationSettings(fallbackChart, settings);
  console.log('[Jyotish] ⚠️ JS引擎计算完成');
  return fallbackChart;
}

function buildChartComputeRecoveryMessage(error) {
  const message = error?.message || error || '本地 API 未连接';
  return `计算失败：${message}。请到 Trust Center 运行健康检查；如本地 API 未连接，请按 README 的普通用户启动路径启动网页服务和本地 API 服务后重试。`;
}

function buildInteractiveAPIRecoveryMessage(label, error) {
  const message = error?.message || error || '本地 API 未连接';
  return `${label}：${message}。请到 Trust Center 运行健康检查；如本地 API 未连接，请按 README 的普通用户启动路径启动网页服务和本地 API 服务后重试。`;
}

function renderInlineAPIError(className, label, error) {
  return `<p class="${escapeAttr(className)}">${escapeHtml(buildInteractiveAPIRecoveryMessage(label, error))}</p>`;
}

function setChartComputeStatus(message = '', tone = 'warn') {
  const status = $('chart-compute-status');
  if (!status) return;
  status.textContent = message;
  status.dataset.tone = tone;
  status.classList.toggle('hidden', !message);
}

function setupForm() {
  const form = $('birth-form'), btn = $('btn-calculate');
  const btnText = btn.querySelector('.btn-text'), btnLoading = btn.querySelector('.btn-loading');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const year = parseInt($('birth-year').value);
    const month = parseInt($('birth-month').value);
    const day = parseInt($('birth-day').value);
    const timeVal = $('birth-time').value;
    resolveTypedBirthCity();
    const lat = parseFloat($('birth-lat').value), lon = parseFloat($('birth-lon').value);
    const tz = resolveTimezoneValue($('birth-tz').value);
    if (!year || !month || !day || !timeVal) { alert(t('alert.date')); return; }
    if (isNaN(lat) || isNaN(lon)) { alert(t('alert.city')); return; }
    const [hour, minute, second = 0] = timeVal.split(':').map(Number);
    btnText.classList.add('hidden'); btnLoading.classList.remove('hidden'); btn.disabled = true;
    setChartComputeStatus('正在计算星盘...', 'warn');
    try {
      // v6.9.4: 计算层 — 优先本地 API 服务, 回退JS引擎
      chartData = await computeChartForBirth({ year, month, day, hour, minute, second, lat, lon, tz });
    } catch (e) {
      console.error('[Jyotish] 计算失败:', e);
      setChartComputeStatus(buildChartComputeRecoveryMessage(e), 'error');
      btnText.classList.remove('hidden'); btnLoading.classList.add('hidden'); btn.disabled = false;
      return;
    }
    try {
      window.__jyotishBirth = { year, month, day, hour, minute, second, lat, lon, tz };
      renderAll();
      showPage('chart');
      aiChatSetChartData(chartData);
      // v6.9.4: 触发 AI 解读
      triggerAIReading(chartData);
      setChartComputeStatus(chartData?._fallback ? '已使用浏览器本地引擎生成星盘；如需完整本地 API 服务能力，请到 Trust Center 运行健康检查。' : '星盘已生成。', 'ok');
    } catch (err) {
      console.error('[Jyotish] Error:', err);
      setChartComputeStatus(buildChartComputeRecoveryMessage(err), 'error');
    } finally {
      btnText.classList.remove('hidden'); btnLoading.classList.add('hidden'); btn.disabled = false;
    }
  });
}

function fillBirthFormFromData(birth) {
  const yearEl = $('birth-year');
  const monthEl = $('birth-month');
  const dayEl = $('birth-day');
  const cityEl = $('birth-city');
  yearEl.value = String(birth.year);
  monthEl.value = String(birth.month);
  monthEl.dispatchEvent(new Event('change'));
  dayEl.value = String(birth.day);
  const second = Number.isFinite(Number(birth.second)) ? Number(birth.second) : 0;
  $('birth-time').value = second
    ? `${String(birth.hour).padStart(2, '0')}:${String(birth.minute).padStart(2, '0')}:${String(second).padStart(2, '0')}`
    : `${String(birth.hour).padStart(2, '0')}:${String(birth.minute).padStart(2, '0')}`;
  $('birth-lat').value = birth.lat;
  $('birth-lon').value = birth.lon;
  $('birth-tz').value = String(birth.tz);
  if (cityEl && birth.city) cityEl.value = birth.city;
}

function setFirstUseStatus(message, tone = 'neutral') {
  const status = $('first-use-status');
  if (!status) return;
  status.textContent = message || '';
  status.dataset.tone = tone;
}

function fillDemoBirth() {
  fillBirthFormFromData(DEMO_BIRTH);
  setFirstUseStatus('示例盘已填入。确认信息后点击“生成星盘”进入完整解盘。', 'ok');
  $('btn-calculate')?.focus();
}

async function runFirstUseHealthCheck() {
  setFirstUseStatus('正在检查本地 API 与技法目录...', 'pending');
  try {
    const apiHealth = await window.JyotishAPI?.getAPIHealth?.();
    const audit = await window.JyotishAPI?.getCapabilityAudit?.();
    const apiOnline = Boolean(apiHealth?.success || apiHealth?.status === 'ok' || apiHealth?.ok);
    const techniqueCount = audit?.registry?.technique_count || audit?.registry_count || audit?.technique_count || 0;
    const endpointCount = audit?.surfaces?.api_endpoint_count || audit?.api_endpoint_count || 0;
    window.__jyotishRuntimeHealth = {
      status: apiOnline ? 'ok' : 'warn',
      checkedAt: new Date().toISOString(),
      apiOnline,
      apiBase: apiHealth?.base,
      version: apiHealth?.version,
      latencyMs: apiHealth?.latencyMs,
      techniqueCount,
      endpointCount,
      apiHealth,
      audit,
      details: [
        ['PWA 安装壳', getPWAStatus().label, getPWAStatus().note],
        ['本地 API 服务', apiHealth?.base || (apiOnline ? 'online' : '未连接'), apiOnline ? `health ok · v${apiHealth?.version || '-'} · ${apiHealth?.latencyMs ?? '-'}ms` : '本地 API 未通过 health 检查'],
        ['Technique catalog', `${techniqueCount || 0} techniques`, `${endpointCount || 0} API endpoints 可被前端发现`],
      ],
    };
    if (apiOnline) {
      setFirstUseStatus(`本地 API 可用；技法目录 ${techniqueCount || 0} 项、API ${endpointCount || 0} 个端点已返回。可以继续生成星盘。`, 'ok');
      return;
    }
    setFirstUseStatus('本地 API 未连接；仍可先用浏览器 fallback 生成基础星盘，后端报告/PDF/高级技法需启动本地 API 服务。', 'warn');
  } catch (error) {
    window.__jyotishRuntimeHealth = {
      status: 'warn',
      checkedAt: new Date().toISOString(),
      apiOnline: false,
      error: error?.message || String(error),
      details: [
        ['PWA 安装壳', getPWAStatus().label, getPWAStatus().note],
        ['本地 API 服务', '未连接', error?.message || '请确认本地 API 服务正在 127.0.0.1:5200 运行'],
        ['启动路径', '普通用户启动路径', '按 README 先启动网页服务，再启动本地 API 服务。'],
      ],
    };
    setFirstUseStatus('本地 API 未连接；请按普通用户启动路径启动网页服务和本地 API 服务后再检查。', 'warn');
  }
}

function focusFirstUseImport() {
  const importPanel = $('chart-import-panel');
  const importText = $('chart-import-text');
  if (importPanel) importPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
  if (importText) importText.focus();
  setFirstUseStatus('已定位到星盘导入区。粘贴出生资料或上传文本层 PDF 后点击“识别信息”。', 'neutral');
}

function setupFirstUsePanel() {
  const panel = $('first-use-panel');
  if (!panel || panel.dataset.bound) return;
  panel.dataset.bound = 'true';
  $('first-use-demo')?.addEventListener('click', fillDemoBirth);
  $('first-use-health')?.addEventListener('click', runFirstUseHealthCheck);
  $('first-use-import')?.addEventListener('click', focusFirstUseImport);
}

function getAscendantLord(ascendant = {}) {
  return ascendant.lord || SIGN_LORDS[ascendant.sign] || '';
}

function normalizePlanetRecord(planet = {}) {
  return planet || {};
}

function formatMoonNakshatra(moonP) {
  const moon = normalizePlanetRecord(moonP);
  const nakshatra = moon.nakshatra || moon.nakshatra_name || '';
  const pada = moon.nakshatra_pada || moon.pada || '';
  if (!nakshatra) return '';
  return `${nakshatra}${pada ? ` Pada ${pada}` : ''}`;
}

async function applyRectifiedBirth(birth) {
  if (!birth) return;
  try {
    fillBirthFormFromData(birth);
    chartData = await computeChartForBirth(birth);
    window.__jyotishBirth = birth;
    renderAll();
    showPage('chart');
    aiChatSetChartData(chartData);
    triggerAIReading(chartData);
    const rectPanel = $('rect-panel');
    const rectOverlay = $('rect-overlay');
    if (rectPanel) rectPanel.classList.add('hidden');
    if (rectOverlay) rectOverlay.classList.add('hidden');
    document.body.style.overflow = '';
  } catch (error) {
    console.error('[Rect] apply corrected birth failed:', error);
    setChartComputeStatus(buildInteractiveAPIRecoveryMessage('校正时间应用暂不可用', error), 'error');
  }
}

// ============================================================================
// 全部渲染
// ============================================================================
function renderAll() {
  if (!chartData) return;
  const { ascendant = {}, planets = {}, birth_info = {} } = chartData;
  if (!birth_info.date) birth_info.date = '2000-01-01';
  if (!birth_info.time) birth_info.time = '12:00';
  if (!birth_info.tz) birth_info.tz = 'UTC+8';
  const moonP = normalizePlanetRecord(planets.Moon);
  const ascendantLord = ascendant.lord || getAscendantLord(ascendant);
  const moonNakshatra = formatMoonNakshatra(moonP);

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
  $('asc-degree').textContent = `${((ascendant.degree_in_sign ?? ascendant.degree) ?? 0).toFixed(2)}°  |  ${t('asc.lord')}: ${planetName(ascendantLord) || ascendantLord || '-'}`;
  $('asc-nakshatra').textContent = moonNakshatra ? `${t('asc.nakshatra')}: ${moonNakshatra}` : '';
  $('asc-lord-badge').textContent = ascendantLord ? `${t('asc.lord')}: ${planetName(ascendantLord) || ascendantLord} (${ascendantLord})` : `${t('asc.lord')}: -`;

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
  renderD9MarriageReport(allV, planets, ascendant, karaka);
  renderArudha(arudha);

  // Ashtakavarga Tab
  renderAshtakavarga(av, ascendant.sign);

  // Shadbala Tab
  renderShadbala(sb);

  // Dasha Tab
  renderDashaSystemOverview(chartData);
  if (dashaData) renderDasha3Level(dashaData);

  // Transit Tab（异步）
  renderTransit(planets, ascendant.sign, av, ascendant.degree);

  // 深度分析 Tab
  const pacdares = computePACDARES(planets, ascendant.sign);
  const houseInfluence = computeHouseInfluence(planets, ascendant.sign);
  const vargottama = detectVargottama(planets);
  const frequency = computeFrequency(planets);
  const triangle = computeTriangle(planets);
  const ramanGrades = computeRamanHouseScore(planets, ascendant.sign);
  const argala = computeArgala(buildPlanetSignIndex(planets), SIGNS.indexOf(ascendant.sign));
  renderFunctionalNature(ascendant.sign);
  renderPACDARES(pacdares);
  renderArgala(argala);
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
  const validation = computeValidation(planets, ascendant, av, dashaData);
  const audit = computeAudit(planets, ascendant, av, validation);
  const actionableCtx = computeActionableContext(planets, ascendant);
  const provenance = buildCalculationProvenance(chartData, ty, {
    av,
    shadbala: sb,
    validation,
    audit,
    chartStyle: getChartStyle(),
  });
  chartData._client_audit = { validation, audit, actionableContext: actionableCtx, provenance };
  renderSpecialLagnaReport(arudha, ascendant, birth_info, chartData.special_lagnas);
  renderCompleteReadingTab({ ascendant, moonP, allYogas, dashaData, extraDasas, chartData, validation, audit });
  renderAIPromptPackPanel(chartData);
  renderProvenancePanel({
    chartData,
    panchanga: ty,
    provenance,
    validation,
    audit,
    allYogas,
    dashaData,
    extraDasas,
  });

  // 🔥 v6.7.2: API数据渲染 Recovery & KP tabs
  renderRemediesTab(chartData);
  renderSynastryTab(chartData);
  renderPrashnaTab(chartData);
  renderKPTab(chartData);
  // v6.9.0: 验证 & 过境 Tab
  renderVerifyTab(chartData);
  renderTransitCompareTab(chartData);
  updateSaveChartButton();
  renderSavedChartPanel();

  // 绑定术语 Tooltip（延迟确保所有异步渲染完成）
  setTimeout(() => bindTerms(document.querySelector('#page-chart')), 200);
  setTimeout(() => bindTerms(document.querySelector('#page-chart')), 800);
}

// ============================================================================
// 完整解盘 Tab：承接 Skill 全能力路线
// ============================================================================
function renderCompleteReadingTab({ ascendant, moonP, allYogas, dashaData, extraDasas, chartData, validation, audit }) {
  const extraDashaCount = Object.keys(extraDasas || {}).length;
  const apiDashaCount = chartData?._extended?.dasha_count || chartData?.available_dashas?.length || 0;
  const dashaCount = Math.max(apiDashaCount, extraDashaCount, dashaData ? 1 : 0);
  renderSkillCoverage($('skill-coverage-section'), {
    ascendant: ascendant?.sign ? `${ascendant.sign} · ${signName(ascendant.sign)}` : '-',
    moonNakshatra: formatMoonNakshatra(moonP) || '-',
    yogaCount: allYogas?.length || 0,
    dashaCount,
    chartData,
    birthInfo: chartData?.birth_info || {},
  });
  const mevg = buildMEVGAudit({ ascendant, moonP, allYogas, dashaData, chartData, validation, audit });
  renderMEVGAudit($('mevg-audit-section'), mevg);
}

function renderAIPromptPackPanel(cd) {
  const host = $('ai-prompt-pack-panel');
  if (!host) return;
  const pack = normalizeAIPromptPack(cd);
  const evidence = pack.evidence_snapshot || {};
  const ayanamsa = evidence.ayanamsa || {};
  const core = evidence.core || {};
  const timing = evidence.timing || {};
  const strength = evidence.strength || {};
  const docs = pack.retrieval_plan?.local_reference_docs || [];
  const tags = pack.retrieval_plan?.retrieval_tags || [];
  const ranking = Array.isArray(strength.shadbala_ranking) ? strength.shadbala_ranking : [];
  host.innerHTML = `
    <section class="ai-prompt-pack-panel">
      <div class="ai-prompt-pack-head">
        <div>
          <span>AI Prompt Pack</span>
          <strong>${escapeHtml(pack.mode || 'jyotish_structured_prompt_pack')}</strong>
        </div>
        <em>schema v${escapeHtml(String(pack.schema_version || 1))}</em>
      </div>
      <div class="ai-prompt-pack-grid">
        <div class="ai-prompt-pack-card">
          <span>Ayanamsa</span>
          <strong>${escapeHtml(ayanamsa.display || getCalculationSettingLabel('ayanamsa', readCalculationSettings().ayanamsa))}</strong>
          <small>${escapeHtml(`node=${ayanamsa.node_mode || 'mean'} · value=${ayanamsa.value ?? '-'}`)}</small>
        </div>
        <div class="ai-prompt-pack-card">
          <span>Lagna / Moon</span>
          <strong>${escapeHtml(core.ascendant?.sign || cd?.ascendant?.sign || '-')} / ${escapeHtml(core.Moon?.sign || cd?.planets?.Moon?.sign || '-')}</strong>
          <small>D1 evidence snapshot</small>
        </div>
        <div class="ai-prompt-pack-card">
          <span>Dasha</span>
          <strong>${escapeHtml(timing.current_mahadasha || cd?.dasha?.current_md || '-')}</strong>
          <small>${escapeHtml(timing.current_antardasha ? `AD ${timing.current_antardasha}` : timing.start_date || '')}</small>
        </div>
      </div>
      <div class="ai-prompt-pack-body">
        <div>
          <h4>Prompt</h4>
          <pre>${escapeHtml(pack.prompt_zh || '')}</pre>
        </div>
        <div>
          <h4>Evidence</h4>
          <div class="ai-prompt-pack-evidence">
            ${['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'].map(planet => {
              const pdata = core[planet] || cd?.planets?.[planet] || {};
              return `<span>${escapeHtml(planet)} · ${escapeHtml(pdata.sign || '-')} ${escapeHtml(formatCompactDegree(pdata.degree))}</span>`;
            }).join('')}
          </div>
          ${ranking.length ? `
            <div class="ai-prompt-pack-strength">
              ${ranking.slice(0, 5).map(item => `<span>${escapeHtml(item.planet || '-')} ${escapeHtml(String(item.total_rupas ?? item.rupas ?? '-'))}</span>`).join('')}
            </div>
          ` : ''}
        </div>
      </div>
      <div class="ai-prompt-pack-foot">
        <div>
          <strong>Retrieval</strong>
          ${docs.slice(0, 6).map(doc => `<span>${escapeHtml(doc)}</span>`).join('')}
        </div>
        <div>
          <strong>Boundary</strong>
          ${(tags.length ? tags : ['oracle_boundary_visible', 'confidence_labeled_reading']).map(tag => `<span>${escapeHtml(tag)}</span>`).join('')}
        </div>
      </div>
    </section>
  `;
}

function normalizeAIPromptPack(cd = {}) {
  if (cd?.ai_prompt_pack?.evidence_snapshot) return cd.ai_prompt_pack;
  const settings = normalizeCalculationSettings(cd?._calculation_settings || readCalculationSettings());
  const birth = cd.birth || cd.birth_info || {};
  const planets = cd.planets || {};
  return {
    schema_version: 1,
    mode: 'jyotish_structured_prompt_pack',
    prompt_zh: [
      '你是一个审慎的 AI Native 印度/吠陀占星分析助手。',
      '请只基于 evidence_snapshot 中的计算证据生成解读，不要编造星盘不存在的配置。',
      `本盘使用 ${getCalculationSettingLabel('ayanamsa', settings.ayanamsa)} ayanamsa，节点口径为 ${getCalculationSettingLabel('nodeMode', settings.nodeMode)}。`,
      '不要仅凭单一配置下结论；核心判断至少交叉 D1、D9、Dasha、Shadbala/Ashtakavarga 或 Transit 中的两个证据层。',
    ].join('\n'),
    evidence_snapshot: {
      birth,
      ayanamsa: {
        name: settings.ayanamsa,
        display: getCalculationSettingLabel('ayanamsa', settings.ayanamsa),
        value: birth.ayanamsa ?? cd.ayanamsa,
        node_mode: settings.nodeMode,
      },
      core: {
        ascendant: cd.ascendant || {},
        ...Object.fromEntries(Object.entries(planets).filter(([planet]) => ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'].includes(planet))),
      },
      timing: {
        current_mahadasha: cd.dasha?.current_md,
        remaining_years: cd.dasha?.remaining_years,
        start_date: cd.dasha?.start_date,
      },
      strength: {
        shadbala_ranking: Object.entries(cd.shadbala || {}).map(([planet, pdata]) => ({ planet, rupas: pdata?.rupas, level: pdata?.level })),
      },
    },
    retrieval_plan: {
      local_reference_docs: [
        'references/ai-reading-workflow-prompt.md',
        'references/comprehensive-reading-workflow.md',
        'references/prediction-boundary-protocol.md',
      ],
      retrieval_tags: ['no_single_factor_conclusion', 'oracle_boundary_visible', 'confidence_labeled_reading'],
    },
  };
}

function formatCompactDegree(value) {
  const num = Number(value);
  return Number.isFinite(num) ? `${num.toFixed(2)}°` : '-';
}

function readCalculationSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem(CALCULATION_SETTINGS_KEY) || '{}');
    if (!saved.terminologyMode) saved.terminologyMode = localStorage.getItem(TERMINOLOGY_MODE_KEY);
    return normalizeCalculationSettings(saved);
  } catch {
    return { ...DEFAULT_CALCULATION_SETTINGS };
  }
}

function writeCalculationSettings(settings) {
  const normalized = normalizeCalculationSettings(settings);
  localStorage.setItem(CALCULATION_SETTINGS_KEY, JSON.stringify(normalized));
  localStorage.setItem(TERMINOLOGY_MODE_KEY, normalized.terminologyMode);
  setGlossaryTerminologyMode(normalized.terminologyMode);
  if (chartData) chartData._terminology_mode = normalized.terminologyMode;
  return normalized;
}

function normalizeCalculationSettings(settings = {}) {
  const normalized = { ...DEFAULT_CALCULATION_SETTINGS };
  Object.keys(DEFAULT_CALCULATION_SETTINGS).forEach(key => {
    const allowed = (CALCULATION_SETTING_OPTIONS[key] || []).map(([value]) => value);
    if (allowed.includes(settings[key])) normalized[key] = settings[key];
  });
  return normalized;
}

function getCalculationSettingLabel(key, value) {
  const found = (CALCULATION_SETTING_OPTIONS[key] || []).find(([option]) => option === value);
  return found ? found[1] : value || '-';
}

function applyCalculationSettingsToPayload(payload) {
  const settings = readCalculationSettings();
  return {
    ...payload,
    ayanamsa: settings.ayanamsa,
    node_mode: settings.nodeMode,
    house_system: settings.houseSystem,
    sunrise_policy: settings.sunrisePolicy,
    geocoder_policy: settings.geocoderPolicy,
    ephemeris_backend: settings.ephemerisBackend,
    terminology_mode: settings.terminologyMode,
    yoga_variant: settings.yogaVariant,
    jaimini_karaka_variant: settings.jaiminiKarakaVariant,
    kp_significator_variant: settings.kpSignificatorVariant,
    ashtakavarga_variant: settings.ashtakavargaVariant,
    shadbala_variant: settings.shadbalaVariant,
    dasha_reference: settings.dashaReference,
  };
}

function attachCalculationSettings(chart, settings = readCalculationSettings()) {
  if (!chart) return chart;
  chart._calculation_settings = normalizeCalculationSettings(settings);
  chart._terminology_mode = readTerminologyMode();
  return chart;
}

function buildCalculationProvenance(chartData, panchanga, context = {}) {
  const birth = chartData?.birth_info || chartData?.birth || {};
  const settings = normalizeCalculationSettings(chartData?._calculation_settings || readCalculationSettings());
  const terminologyMode = readTerminologyMode(chartData?._terminology_mode);
  const terminology = getTerminologyModeOption(terminologyMode);
  const ayanamsaValue = birth.ayanamsa ?? chartData?.birth?.ayanamsa ?? chartData?.ayanamsa;
  const ayanamsaLabel = birth.ayanamsa_display || chartData?.birth?.ayanamsa_display || getCalculationSettingLabel('ayanamsa', settings.ayanamsa);
  const ayanamsa = ayanamsaValue != null
    ? `${ayanamsaLabel} (${Number(ayanamsaValue).toFixed(4)} deg)`
    : ayanamsaLabel;
  const hasPython = chartData?.success && !chartData?._fallback;
  return {
    engine: hasPython ? `本地 API 服务 ${chartData?.version || ''}`.trim() : 'Browser SwissEph fallback',
    ephemeris: hasPython ? 'Swiss Ephemeris via local API' : 'SwissEph WASM/browser',
    ephemerisBackend: getCalculationSettingLabel('ephemerisBackend', settings.ephemerisBackend),
    terminologyMode: getCalculationSettingLabel('terminologyMode', settings.terminologyMode),
    ayanamsa,
    nodeMode: `${birth.node_mode || getCalculationSettingLabel('nodeMode', settings.nodeMode)}；Ketu derived 180 deg opposite`,
    houseSystem: `${getCalculationSettingLabel('houseSystem', settings.houseSystem)}；Bhava Chalit 可在专项接口复核`,
    sunrisePolicy: getCalculationSettingLabel('sunrisePolicy', settings.sunrisePolicy),
    geocoderPolicy: getCalculationSettingLabel('geocoderPolicy', settings.geocoderPolicy),
    yogaVariant: getCalculationSettingLabel('yogaVariant', settings.yogaVariant),
    jaiminiKarakaVariant: getCalculationSettingLabel('jaiminiKarakaVariant', settings.jaiminiKarakaVariant),
    kpSignificatorVariant: getCalculationSettingLabel('kpSignificatorVariant', settings.kpSignificatorVariant),
    ashtakavargaVariant: getCalculationSettingLabel('ashtakavargaVariant', settings.ashtakavargaVariant),
    shadbalaVariant: getCalculationSettingLabel('shadbalaVariant', settings.shadbalaVariant),
    dashaReference: getCalculationSettingLabel('dashaReference', settings.dashaReference),
    terminologyMode,
    terminologyLabel: terminology.label,
    terminologyNote: terminology.note,
    calculationSettings: settings,
    ruleVariantStatus: 'Rule variants are saved/exported as interpretive policy; non-current variants are staged until each engine path supports live switching.',
    calculationSettingsStatus: 'Settings are saved and exported; ayanamsa and node mode are live API parameters. Rule variants remain interpretive policy unless the target endpoint returns live variant metadata.',
    chartStyle: context.chartStyle === 'north' ? 'North Indian' : 'South Indian',
    timezone: birth.tz || 'UTC+8',
    coordinates: `${safeNumber(birth.lat ?? 0).toFixed(4)}, ${safeNumber(birth.lon ?? 0).toFixed(4)}`,
    julianDay: birth.julian_day || chartData?.birth?.julian_day || '',
    panchangaSource: panchanga ? 'Birth-time Sun/Moon longitudes in current chart' : 'Unavailable',
    exportStatus: 'HTML/JSON/SVG/PNG export available; backend PDF pipeline is queued in product gap matrix',
    savedChartStatus: readSavedChartStatus(chartData),
  };
}

function readSavedChartStatus(cd) {
  const lib = readChartLibrary();
  const saved = Boolean(findChartLibraryEntry(lib, cd));
  return {
    count: lib.length,
    currentSaved: saved,
    label: saved ? '当前星盘已在本地星盘库' : '当前星盘尚未保存到本地星盘库',
  };
}

function readChartLibrary() {
  try {
    const lib = JSON.parse(localStorage.getItem(CHART_LIBRARY_KEY) || '[]');
    return Array.isArray(lib) ? lib : [];
  } catch {
    return [];
  }
}

function writeChartLibrary(lib) {
  localStorage.setItem(CHART_LIBRARY_KEY, JSON.stringify(Array.isArray(lib) ? lib : []));
}

function readSynastryPairLibrary() {
  try {
    const lib = JSON.parse(localStorage.getItem(SYNASTRY_PAIR_LIBRARY_KEY) || '[]');
    return Array.isArray(lib) ? lib : [];
  } catch {
    return [];
  }
}

function writeSynastryPairLibrary(lib) {
  localStorage.setItem(SYNASTRY_PAIR_LIBRARY_KEY, JSON.stringify(Array.isArray(lib) ? lib : []));
}

function readPrashnaCaseLibrary() {
  try {
    const lib = JSON.parse(localStorage.getItem(PRASHNA_CASE_LIBRARY_KEY) || '[]');
    return Array.isArray(lib) ? lib : [];
  } catch {
    return [];
  }
}

function writePrashnaCaseLibrary(lib) {
  localStorage.setItem(PRASHNA_CASE_LIBRARY_KEY, JSON.stringify(Array.isArray(lib) ? lib : []));
}

function sortChartLibrary(lib) {
  return [...(Array.isArray(lib) ? lib : [])].sort((a, b) => {
    const aTime = Date.parse(a?.updatedAt || a?.savedAt || '') || 0;
    const bTime = Date.parse(b?.updatedAt || b?.savedAt || '') || 0;
    return bTime - aTime;
  });
}

function sortCaseLibrary(lib) {
  return [...(Array.isArray(lib) ? lib : [])].sort((a, b) => {
    const aTime = Date.parse(a?.updatedAt || a?.generatedAt || a?.savedAt || '') || 0;
    const bTime = Date.parse(b?.updatedAt || b?.generatedAt || b?.savedAt || '') || 0;
    return bTime - aTime;
  });
}

function buildWorkspaceChartId(cd) {
  const birth = cd?.birth_info || {};
  if (!birth.date) return '';
  return [
    birth.date,
    normalizeBirthIdPart(birth.time || '00:00'),
    normalizeBirthIdPart(birth.lat),
    normalizeBirthIdPart(birth.lon),
    normalizeBirthIdPart(birth.tz),
  ].join('_');
}

function buildLegacyWorkspaceChartId(cd) {
  const birth = cd?.birth_info || {};
  if (!birth.date) return '';
  return [
    birth.date,
    normalizeBirthIdPart(birth.lat),
    normalizeBirthIdPart(birth.lon),
    normalizeBirthIdPart(birth.tz),
  ].join('_');
}

function normalizeBirthIdPart(value) {
  return String(value ?? '').trim().replace(/\s+/g, '');
}

function findChartLibraryEntry(lib, cd) {
  const id = buildWorkspaceChartId(cd);
  const legacyId = buildLegacyWorkspaceChartId(cd);
  return (Array.isArray(lib) ? lib : []).find(entry => entry?.id === id || entry?.id === legacyId) || null;
}

function buildWorkspaceChartLabel(cd) {
  const birth = cd?.birth_info || {};
  const asc = cd?.ascendant || {};
  const date = birth.date || '-';
  const time = birth.time || '';
  const ascLabel = asc.sign ? `${signName(asc.sign)} rising` : 'chart';
  return `${date} ${time} · ${ascLabel}`;
}

function buildDefaultChartWorkspaceMeta(cd) {
  const birth = cd?.birth_info || cd?.birth || {};
  const named = String(birth.name || birth.person_name || '').trim();
  return {
    group: named ? '家庭' : '未分组',
    relation: 'self',
    tags: ['chart'],
  };
}

function normalizeWorkspaceMeta(record, fallback = {}) {
  const rawTags = Array.isArray(record?.tags)
    ? record.tags
    : String(record?.tags || '').split(',').map(tag => tag.trim()).filter(Boolean);
  return {
    group: record?.group || fallback.group || '未分组',
    relation: record?.relation || fallback.relation || 'unknown',
    tags: rawTags.length ? rawTags : (fallback.tags || []),
  };
}

function getCaseDefaultMeta(kind) {
  if (kind === 'pair') return { group: '伴侣', relation: 'partner', tags: ['synastry', 'relationship'] };
  if (kind === 'prashna') return { group: '研究', relation: 'research', tags: ['prashna'] };
  return { group: '未分组', relation: 'self', tags: ['chart'] };
}

function getCaseGroupLabel(record, kind) {
  return normalizeWorkspaceMeta(record, getCaseDefaultMeta(kind)).group;
}

function getCaseRelationValue(record, kind) {
  return normalizeWorkspaceMeta(record, getCaseDefaultMeta(kind)).relation;
}

function getCaseRelationLabel(record, kind) {
  const value = getCaseRelationValue(record, kind);
  return CASE_RELATION_PRESETS.find(([key]) => key === value)?.[1] || '未标注';
}

function renderCaseMetaLine(record, kind) {
  const meta = normalizeWorkspaceMeta(record, getCaseDefaultMeta(kind));
  return `
    <div class="case-meta-line">
      <span>${escapeHtml(meta.group)}</span>
      <span>${escapeHtml(getCaseRelationLabel(meta, kind))}</span>
      ${meta.tags.slice(0, 3).map(tag => `<em>${escapeHtml(tag)}</em>`).join('')}
    </div>
  `;
}

function formatWorkspaceCaseTitle(record, kind) {
  return `${record?.label || record?.id || '未命名'} · ${getCaseGroupLabel(record, kind)}`;
}

function saveCurrentChartToLibrary() {
  if (!chartData) return false;
  const id = buildWorkspaceChartId(chartData);
  if (!id) return false;
  const now = new Date().toISOString();
  const lib = readChartLibrary();
  const existing = findChartLibraryEntry(lib, chartData);
  if (existing) {
    const meta = normalizeWorkspaceMeta(existing, buildDefaultChartWorkspaceMeta(chartData));
    existing.id = id;
    existing.data = chartData;
    existing.label = existing.label || buildWorkspaceChartLabel(chartData);
    existing.group = meta.group;
    existing.relation = meta.relation;
    existing.tags = meta.tags;
    existing.updatedAt = now;
  } else {
    const meta = buildDefaultChartWorkspaceMeta(chartData);
    lib.push({
      id,
      label: buildWorkspaceChartLabel(chartData),
      data: chartData,
      ...meta,
      savedAt: now,
      updatedAt: now,
    });
  }
  writeChartLibrary(sortChartLibrary(lib).slice(0, 24));
  updateSaveChartButton();
  renderSavedChartPanel();
  return true;
}

function updateSaveChartButton() {
  const btn = $('btn-save-chart');
  if (!btn) return;
  if (!chartData) {
    btn.disabled = true;
    btn.textContent = '保存星盘';
    return;
  }
  const saved = readSavedChartStatus(chartData);
  btn.disabled = false;
  btn.textContent = saved.currentSaved ? '已保存' : '保存星盘';
  btn.classList.toggle('is-saved', Boolean(saved.currentSaved));
}

function setupSavedChartPanel() {
  const saveBtn = $('btn-save-chart');
  if (saveBtn && !saveBtn.dataset.bound) {
    saveBtn.dataset.bound = 'true';
    saveBtn.addEventListener('click', () => {
      if (!saveCurrentChartToLibrary()) return;
      saveBtn.textContent = '已保存';
      setTimeout(updateSaveChartButton, 1200);
      if ($('provenance-panel')) renderAll();
    });
  }
  renderSavedChartPanel();
}

function renderSavedChartPanel() {
  const panel = $('saved-chart-panel');
  if (!panel) return;
  const lib = sortChartLibrary(readChartLibrary());
  if (!lib.length) {
    panel.innerHTML = `
      <div class="saved-chart-empty">
        <strong>本地星盘库</strong>
        <span>先用示例盘、导入资料或手动输入生成星盘，保存后可一键打开。</span>
      </div>
    `;
    return;
  }
  panel.innerHTML = `
    <div class="saved-chart-head">
      <strong>本地星盘库</strong>
      <span>${escapeHtml(String(lib.length))} 个星盘</span>
    </div>
    <div class="saved-chart-list">
      ${lib.slice(0, 5).map(entry => `
        <button type="button" class="saved-chart-item" data-open-saved-chart="${escapeAttr(entry.id || '')}">
          <span>${escapeHtml(entry.label || entry.id || '未命名星盘')}</span>
          <small>${escapeHtml(formatSavedAt(entry.updatedAt || entry.savedAt))}</small>
        </button>
      `).join('')}
    </div>
  `;
  panel.querySelectorAll('[data-open-saved-chart]').forEach(button => {
    button.addEventListener('click', () => openSavedChartFromPanel(button.dataset.openSavedChart));
  });
}

function openSavedChartFromPanel(id) {
  const entry = readChartLibrary().find(item => item?.id === id);
  if (!entry?.data) return;
  chartData = entry.data;
  window.__jyotishBirth = normalizeSavedBirth(entry.data);
  renderAll();
  showPage('chart');
  aiChatSetChartData(chartData);
}

function normalizeSavedBirth(cd) {
  const birth = cd?.birth_info || cd?.birth || {};
  const [year, month, day] = String(birth.date || '').split('-').map(Number);
  const [hour, minute, secondRaw] = String(birth.time || '').split(':').map(Number);
  const second = Number.isFinite(secondRaw) ? secondRaw : Number(birth.second) || 0;
  return {
    year: year || 2000,
    month: month || 1,
    day: day || 1,
    hour: hour || 12,
    minute: minute || 0,
    second,
    lat: Number(birth.lat) || 0,
    lon: Number(birth.lon) || 0,
    tz: resolveTimezoneValue(birth.tz),
  };
}

function renderProvenancePanel({ chartData, panchanga, provenance, validation, audit, allYogas, dashaData, extraDasas }) {
  const container = $('provenance-panel');
  if (!container) return;
  container._panchangaChartData = chartData;
  const birth = chartData?.birth_info || {};
  const dashaCount = Math.max(Object.keys(extraDasas || {}).length, dashaData ? 1 : 0, chartData?.available_dashas?.length || 0);
  const saved = provenance.savedChartStatus || {};
  const chartLibrary = readChartLibrary();
  const pairLibrary = sortCaseLibrary(readSynastryPairLibrary());
  const prashnaLibrary = sortCaseLibrary(readPrashnaCaseLibrary());
  const panchangaRows = buildPanchangaRows(panchanga);
  const tithiLord = chartData?.tithi_lord_analysis || {};
  const auditRows = [
    ['核心能力', '65/65 registry 已产品化', '由 capability audit 与碎片审计持续守门'],
    ['Yoga 数量', `${allYogas?.length || 0} 条`, '后续进入规则搜索/流派变体模式'],
    ['Dasha 覆盖', `${dashaCount} 类/层级入口`, '后续强化事件时间线与候选窗口'],
    ['校验状态', validation?.status || audit?.overall || '已生成', '导出 JSON 会携带 validation/audit 模块'],
  ];
  const roadmap = [
    ['当前完成', 'PWA / Trust Center / 术语模式', '安装入口、本地数据边界、入门/专业/梵文术语偏好已进入产品面'],
    ['下一步 P1', '桌面包装', 'PWA 作为当前交付；Pake 适合快速 URL 壳；Tauri 留给本地 API 服务 sidecar 与签名策略'],
    ['下一步 P1', '星历抽象', '评估 SwissEph、VedAstro、Xalen 等底座替换边界，避免算法假切换'],
    ['守门检查', 'Packaging preflight', '运行 scripts/desktop_packaging_preflight.py 检查 manifest、service worker、loopback API 与 Trust Center'],
  ];

  container.innerHTML = `
    <div class="provenance-grid">
      <section class="provenance-card provenance-card-wide">
        <div class="provenance-head">
          <span>Calculation Provenance</span>
          <strong>${escapeHtml(provenance.engine)}</strong>
        </div>
        <div class="provenance-kv-grid">
          ${renderKV('出生时间', `${birth.date || '-'} ${birth.time || ''} ${birth.tz || ''}`)}
          ${renderKV('坐标', provenance.coordinates)}
          ${renderKV('Ayanamsa', provenance.ayanamsa)}
          ${renderKV('星历', provenance.ephemeris)}
          ${renderKV('星历底座', provenance.ephemerisBackend)}
          ${renderKV('术语模式', provenance.terminologyMode)}
          ${renderKV('宫位策略', provenance.houseSystem)}
          ${renderKV('节点策略', provenance.nodeMode)}
          ${renderKV('日出策略', provenance.sunrisePolicy)}
          ${renderKV('地理策略', provenance.geocoderPolicy)}
          ${renderKV('Yoga 口径', provenance.yogaVariant)}
          ${renderKV('Jaimini 口径', provenance.jaiminiKarakaVariant)}
          ${renderKV('KP 口径', provenance.kpSignificatorVariant)}
          ${renderKV('AV 口径', provenance.ashtakavargaVariant)}
          ${renderKV('Julian Day', provenance.julianDay || '-')}
          ${renderKV('当前盘式', provenance.chartStyle)}
        </div>
        ${renderCalculationSettingsPanel(provenance.calculationSettings)}
      </section>

      <section class="provenance-card">
        <div class="provenance-head">
          <span>Panchanga Preview</span>
          <strong>${escapeHtml(panchanga?.tithi?.paksha || 'Birth-time')}</strong>
        </div>
        <div class="provenance-list">
          ${panchangaRows.map(row => `
            <div class="provenance-list-row">
              <span>${escapeHtml(row[0])}</span>
              <strong>${escapeHtml(row[1])}</strong>
              <small>${escapeHtml(row[2])}</small>
            </div>
          `).join('')}
        </div>
        ${renderTithiLordInsight(tithiLord)}
        <div class="panchanga-range-controls">
          <label>
            <span>开始</span>
            <input type="date" id="panchanga-start" value="${escapeAttr(toDateISO(new Date()))}">
          </label>
          <label>
            <span>结束</span>
            <input type="date" id="panchanga-end" value="${escapeAttr(toDateISO(addDays(new Date(), 6)))}">
          </label>
          <label>
            <span>日出</span>
            <input type="time" id="panchanga-sunrise" value="06:00">
          </label>
          <label>
            <span>日落</span>
            <input type="time" id="panchanga-sunset" value="18:00">
          </label>
          <label>
            <span>活动</span>
            <select id="panchanga-activity">
              ${PANCHANGA_ACTIVITIES.map(([value, label]) => `<option value="${escapeAttr(value)}">${escapeHtml(label)}</option>`).join('')}
            </select>
          </label>
          <div class="panchanga-condition-filter" id="panchanga-condition">
            <div class="panchanga-condition-head">
              <span>条件组合</span>
              <select id="panchanga-condition-mode" aria-label="Panchanga 条件组合模式">
                ${PANCHANGA_CONDITION_MODES.map(([value, label]) => `<option value="${escapeAttr(value)}">${escapeHtml(label)}</option>`).join('')}
              </select>
            </div>
            <div class="panchanga-condition-options">
              ${PANCHANGA_CONDITIONS.filter(([value]) => value !== 'all').map(([value, label]) => `
                <label>
                  <input type="checkbox" name="panchanga-condition-option" value="${escapeAttr(value)}">
                  <small>${escapeHtml(label)}</small>
                </label>
              `).join('')}
            </div>
          </div>
        </div>
        <div class="provenance-actions">
          <button type="button" class="provenance-action" data-action="panchanga-week">本周</button>
          <button type="button" class="provenance-action" data-action="panchanga-month">本月</button>
          <button type="button" class="provenance-action" data-action="panchanga-range">生成日历</button>
          <button type="button" class="provenance-action" data-action="panchanga-csv">导出 CSV</button>
          <button type="button" class="provenance-action" data-action="panchanga-ics">导出 ICS</button>
        </div>
        <div id="panchanga-range-result" class="panchanga-week-status">使用 /api/panchanga_range 生成 Panchanga 日期范围、月历、活动筛选、Rahu Kala、Yamaganda、Gulika。</div>
      </section>

      <section class="provenance-card">
        <div class="provenance-head">
          <span>Workspace</span>
          <strong>${escapeHtml(saved.count ?? 0)} saved</strong>
        </div>
        <div class="workspace-status">
          <strong>${escapeHtml(saved.label || '星盘库状态未知')}</strong>
          <p>本地星盘库与 AI 面板共用同一份数据，可在主界面保存、打开、删除和导出案例。</p>
        </div>
        ${renderChartWorkspaceList(chartLibrary)}
        ${renderCaseWorkspaceSummary(pairLibrary, prashnaLibrary)}
        <div class="provenance-actions">
          <button type="button" class="provenance-action" data-action="workspace-save-current">保存当前盘</button>
          <button type="button" class="provenance-action" data-action="workspace-open-selected">打开所选</button>
          <button type="button" class="provenance-action" data-action="workspace-delete-selected">删除所选</button>
          <button type="button" class="provenance-action" data-action="workspace-export-selected">导出所选</button>
          <button type="button" class="provenance-action" data-action="workspace-export-cases">导出案例库</button>
          <label class="provenance-action file-action">
            <input type="file" id="workspace-case-import-file" accept=".json,application/json">
            导入案例库
          </label>
          <button type="button" class="provenance-action" data-action="export-json">导出 JSON</button>
          <button type="button" class="provenance-action" data-action="export-html">导出 HTML 报告</button>
          <button type="button" class="provenance-action" data-action="open-ai-library">打开 AI 面板</button>
        </div>
        <div id="workspace-case-import-status" class="workspace-import-status" aria-live="polite"></div>
      </section>

      ${renderTrustCenterPanel()}

      <section class="provenance-card provenance-card-wide">
        <div class="provenance-head">
          <span>Audit & Next Work</span>
          <strong>Product parity track</strong>
        </div>
        <div class="provenance-table-wrap">
          <table class="provenance-table">
            <tbody>
              ${auditRows.map(row => `<tr><th>${escapeHtml(row[0])}</th><td>${escapeHtml(row[1])}</td><td>${escapeHtml(row[2])}</td></tr>`).join('')}
            </tbody>
          </table>
        </div>
        <div class="roadmap-grid">
          ${roadmap.map(item => `
            <div class="roadmap-card">
              <span>${escapeHtml(item[0])}</span>
              <strong>${escapeHtml(item[1])}</strong>
              <p>${escapeHtml(item[2])}</p>
            </div>
          `).join('')}
        </div>
        <details class="technique-json">
          <summary>产品差距矩阵路径</summary>
          <pre>${escapeHtml(PRODUCT_GAP_DOC)}</pre>
        </details>
      </section>
    </div>
  `;
  bindProvenanceActions();
}

function renderKV(label, value) {
  return `
    <div class="provenance-kv">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(value || '-'))}</strong>
    </div>
  `;
}

function renderCalculationSettingsPanel(settings = readCalculationSettings()) {
  const current = normalizeCalculationSettings(settings);
  return `
    <div class="calculation-settings-panel">
      <div class="calculation-settings-head">
        <strong>Calculation Settings</strong>
        <span>保存后下一次排盘生效，并随导出报告记录。</span>
      </div>
      <div class="calculation-settings-grid">
        ${renderCalculationSelect('ayanamsa', 'Ayanamsa', current.ayanamsa)}
        ${renderCalculationSelect('nodeMode', 'Node', current.nodeMode)}
        ${renderCalculationSelect('houseSystem', 'House', current.houseSystem)}
        ${renderCalculationSelect('sunrisePolicy', 'Sunrise', current.sunrisePolicy)}
        ${renderCalculationSelect('geocoderPolicy', 'Geocoder', current.geocoderPolicy)}
        ${renderCalculationSelect('ephemerisBackend', 'Ephemeris', current.ephemerisBackend)}
        ${renderCalculationSelect('terminologyMode', 'Terminology', current.terminologyMode)}
      </div>
      ${renderTerminologyModePreview(current.terminologyMode)}
      <div class="rule-variant-panel">
        <div class="calculation-settings-head">
          <strong>Rule Variants</strong>
          <span>当前先记录解释口径，后续逐项接入实时切换。</span>
        </div>
        <div class="calculation-settings-grid rule-variant-grid">
          ${renderCalculationSelect('yogaVariant', 'Yoga', current.yogaVariant)}
          ${renderCalculationSelect('jaiminiKarakaVariant', 'Jaimini', current.jaiminiKarakaVariant)}
          ${renderCalculationSelect('kpSignificatorVariant', 'KP', current.kpSignificatorVariant)}
          ${renderCalculationSelect('ashtakavargaVariant', 'Ashtakavarga', current.ashtakavargaVariant)}
          ${renderCalculationSelect('shadbalaVariant', 'Shadbala', current.shadbalaVariant)}
          ${renderCalculationSelect('dashaReference', 'Dasha', current.dashaReference)}
        </div>
      </div>
      <div class="calculation-settings-note">
        Lahiri / Mean Node / Whole Sign / Swiss Ephemeris 与当前 Rule Variants 是主路径；xalen-ephemeris 先作为 Apache-2.0 可行性记录，不改变当前核心黄经。
      </div>
      <button type="button" class="provenance-action calculation-settings-save" data-action="save-calculation-settings">保存计算设置</button>
    </div>
  `;
}

function renderTerminologyModePreview(mode) {
  const copy = {
    beginner: [
      '初学模式',
      'tooltip 会优先解释成日常生活语言，例如“第10宫=事业角色与公开责任”。',
    ],
    professional: [
      '专业模式',
      'tooltip 会保留 Sanskrit / English / 技法名，适合复盘 DK、UL、SAV、Shadbala 等证据。',
    ],
    balanced: [
      '平衡模式',
      'tooltip 同时显示中文、Sanskrit、English 和短解释，是默认阅读模式。',
    ],
  };
  const [title, note] = copy[mode] || copy.balanced;
  return `
    <div class="terminology-mode-preview" data-terminology-mode="${escapeAttr(mode)}">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(note)}</span>
    </div>
  `;
}

function renderCalculationSelect(key, label, value) {
  const options = CALCULATION_SETTING_OPTIONS[key] || [];
  return `
    <label>
      <span>${escapeHtml(label)}</span>
      <select data-setting-key="${escapeAttr(key)}">
        ${options.map(([option, optionLabel]) => `<option value="${escapeAttr(option)}"${option === value ? ' selected' : ''}>${escapeHtml(optionLabel)}</option>`).join('')}
      </select>
    </label>
  `;
}

function initPWAInstallability() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        window.__jyotishPWAStatus = {
          serviceWorker: 'registered',
          scope: registration.scope,
          controlled: Boolean(navigator.serviceWorker.controller),
        };
        updateTrustCenterPWAStatus();
      })
      .catch(error => {
        window.__jyotishPWAStatus = {
          serviceWorker: 'failed',
          error: error?.message || 'registration failed',
        };
        updateTrustCenterPWAStatus();
      });
  } else {
    window.__jyotishPWAStatus = { serviceWorker: 'unsupported' };
  }

  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    window.__jyotishDeferredInstallPrompt = event;
    window.__jyotishPWAStatus = {
      ...(window.__jyotishPWAStatus || {}),
      installPrompt: 'ready',
    };
    updateTrustCenterPWAStatus();
  });
  window.addEventListener('appinstalled', () => {
    window.__jyotishDeferredInstallPrompt = null;
    window.__jyotishPWAStatus = {
      ...(window.__jyotishPWAStatus || {}),
      installed: true,
      installPrompt: 'installed',
    };
    updateTrustCenterPWAStatus();
  });
}

function renderTrustCenterPanel() {
  const stats = getTrustCenterStats();
  const pwa = getPWAStatus();
  const terminology = getTerminologyModeOption();
  const runtime = getRuntimeHealthStatus();
  const statusMessage = getTrustCenterStatusMessage(pwa, runtime);
  return `
    <section class="provenance-card trust-center-panel">
      <div class="provenance-head">
        <span>Trust Center</span>
        <strong>Local-first</strong>
      </div>
      <div class="trust-status-grid">
        ${renderTrustStatus('PWA', pwa.label, pwa.note)}
        ${renderTrustStatus('本地星盘', `${stats.charts} charts`, '存储在浏览器 localStorage')}
        ${renderTrustStatus('配对/问事', `${stats.pairs} pairs · ${stats.prashnas} prashna`, '可单独或整库导出')}
        ${renderTrustStatus('术语', terminology.shortLabel, terminology.note)}
        ${renderTrustStatus('API', '127.0.0.1:5200', '本地 API 服务；不需要外部账号')}
        ${renderTrustStatus('运行体检', runtime.label, runtime.note)}
      </div>
      ${renderRuntimeHealthPanel(runtime)}
      ${renderValidationTransparencyPanel()}
      ${renderDashaShadbalaCalibrationPanel()}
      ${renderRealCaseRevalidationPanel()}
      ${renderTerminologyModePanel()}
      <div class="trust-center-copy">
        <p>出生资料、保存星盘、配对记录、问事记录和计算设置默认保存在本机浏览器。导出报告会写入你主动下载的文件；PDF 后端工件仅由本地 API 生成。</p>
        <p>术语模式只改变解释层和导出记录，不改变底层排盘；AI 聊天、订阅登录或外部接口只在你配置并主动使用对应功能时发生。</p>
      </div>
      <div class="provenance-actions">
        <button type="button" class="provenance-action" data-action="trust-run-health">运行健康检查</button>
        <button type="button" class="provenance-action" data-action="trust-run-real-cases">复验真实案例</button>
        <button type="button" class="provenance-action" data-action="pwa-install">安装为应用</button>
        <button type="button" class="provenance-action" data-action="trust-export-local">导出本地资料</button>
        <button type="button" class="provenance-action danger" data-action="trust-clear-local">清空本地资料</button>
      </div>
      <div id="trust-center-status" class="workspace-import-status" aria-live="polite">${escapeHtml(statusMessage)}</div>
    </section>
  `;
}

const DASHA_SHADBALA_CALIBRATION_STATUS = {
  title: 'Dasha/Shadbala Calibration Status',
  collection: 'external_oracle_collection_queue',
  validator: 'external_oracle_evidence_validation',
  totalTasks: '5 template cases',
  readyForCalibration: 'ready_for_calibration: 0',
  validPackets: 'valid_packets: 0',
  productionTuning: 'production_tuning_allowed: false',
  highConfidence: 'D1/D9/SAV 高可信',
  boundary: '大运起点和 Shadbala 绝对值仍在外部 evidence validator 校准中',
  nextAction: '继续采集 JHora/PyJHora 黑盒截图与分量值；未达标前不得把大运起点或 Shadbala 绝对值说成已完成外部校准。',
};

function renderDashaShadbalaCalibrationPanel() {
  return `
    <div class="dasha-shadbala-calibration-panel">
      <div class="calculation-settings-head">
        <strong>${escapeHtml(DASHA_SHADBALA_CALIBRATION_STATUS.title)}</strong>
        <span>${escapeHtml(DASHA_SHADBALA_CALIBRATION_STATUS.highConfidence)} · ${escapeHtml(DASHA_SHADBALA_CALIBRATION_STATUS.boundary)}</span>
      </div>
      <div class="dasha-shadbala-calibration-grid">
        ${renderValidationTransparencyMetric('Queue', DASHA_SHADBALA_CALIBRATION_STATUS.totalTasks, DASHA_SHADBALA_CALIBRATION_STATUS.collection)}
        ${renderValidationTransparencyMetric('Calibration', DASHA_SHADBALA_CALIBRATION_STATUS.readyForCalibration, '可用于生产调参的外部证据包数量。')}
        ${renderValidationTransparencyMetric('Evidence', DASHA_SHADBALA_CALIBRATION_STATUS.validPackets, DASHA_SHADBALA_CALIBRATION_STATUS.validator)}
        ${renderValidationTransparencyMetric('Tuning', DASHA_SHADBALA_CALIBRATION_STATUS.productionTuning, '禁止用单份 PDF、本地输出或全局缩放调生产常数。')}
      </div>
      <div class="dasha-shadbala-calibration-boundary">
        <strong>边界</strong>
        <span>${escapeHtml(DASHA_SHADBALA_CALIBRATION_STATUS.nextAction)}</span>
      </div>
    </div>
  `;
}

const VALIDATION_TRANSPARENCY = {
  source: 'Yoga logic benchmark',
  charts: '60 charts',
  comparableRules: '82 comparable rules',
  precision: 'Precision 96.48%',
  recall: 'Recall 93.99%',
  f1: 'F1 95.22%',
  unmappedPyjhora: 'unmapped_pyjhora: 718',
  gates: ['golden cases', 'BPHS invariants', 'release-quality-gate'],
};

function renderValidationTransparencyPanel() {
  return `
    <div class="validation-transparency-panel">
      <div class="calculation-settings-head">
        <strong>Validation Transparency</strong>
        <span>${escapeHtml(VALIDATION_TRANSPARENCY.source)} · ${escapeHtml(VALIDATION_TRANSPARENCY.charts)} · ${escapeHtml(VALIDATION_TRANSPARENCY.comparableRules)}</span>
      </div>
      <div class="validation-transparency-grid">
        ${renderValidationTransparencyMetric('Precision', VALIDATION_TRANSPARENCY.precision, '命中的规则中，与参考比较一致的比例。')}
        ${renderValidationTransparencyMetric('Recall', VALIDATION_TRANSPARENCY.recall, '参考可比较规则中，被当前引擎找回的比例。')}
        ${renderValidationTransparencyMetric('F1', VALIDATION_TRANSPARENCY.f1, 'Precision 与 Recall 的综合分。')}
        ${renderValidationTransparencyMetric('Coverage gap', VALIDATION_TRANSPARENCY.unmappedPyjhora, '仍未映射的 PyJHora/B.V. Raman 规则保持可见。')}
      </div>
      <div class="validation-transparency-boundary">
        <strong>边界</strong>
        <span>这些数字来自 references/validation_logic_report.json 的 Yoga 规则对照，不是个人事件预测准确率；出生时间、地点、星历、流派选择和现实事件记录仍会影响解读。</span>
      </div>
      <div class="capability-command-tags">
        ${VALIDATION_TRANSPARENCY.gates.map(gate => `<span>${escapeHtml(gate)}</span>`).join('')}
      </div>
    </div>
  `;
}

function renderValidationTransparencyMetric(label, value, note) {
  return `
    <div class="validation-transparency-metric">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
      <small>${escapeHtml(note)}</small>
    </div>
  `;
}

const REAL_CASE_REVALIDATION_BASELINE = {
  status: 'baseline',
  publicReference: { label: '公开人物星座级一致率', passed: 66, total: 66, passRate: 1, display: '66/66' },
  allChecks: { passed: 87, total: 99, display: '87/99' },
  controversialReference: { caseCount: 5, note: 'controversial_reference 样本保留展示，不计入发布阻断口径。' },
  boundary: '公开人物星座级一致率，不是人生事件预测准确率。',
};

function renderRealCaseRevalidationPanel() {
  const state = window.__jyotishRealCaseRevalidation || REAL_CASE_REVALIDATION_BASELINE;
  const publicRef = state.publicReference || REAL_CASE_REVALIDATION_BASELINE.publicReference;
  const allChecks = state.allChecks || REAL_CASE_REVALIDATION_BASELINE.allChecks;
  const controversial = state.controversialReference || REAL_CASE_REVALIDATION_BASELINE.controversialReference;
  const checkedLabel = state.checkedAt ? `已复验 · ${formatDateTime(state.checkedAt)}` : 'release gate baseline';
  const tone = state.status === 'warn' ? 'warn' : state.status === 'checking' ? 'pending' : 'ok';
  const publicValue = publicRef.display || `${publicRef.passed ?? 66}/${publicRef.total ?? 66}`;
  const allValue = allChecks.display || `${allChecks.passed ?? 87}/${allChecks.total ?? 99}`;
  return `
    <div class="real-case-revalidation-panel real-case-revalidation-${escapeAttr(tone)}">
      <div class="calculation-settings-head">
        <strong>真实案例复验</strong>
        <span>${escapeHtml(checkedLabel)}</span>
      </div>
      <div class="real-case-revalidation-grid">
        ${renderRealCaseMetric('公开人物星座级一致率', publicValue, '发布阻断口径，只统计非争议公开样本的 Lagna/Sun/Moon 星座。')}
        ${renderRealCaseMetric('全量诊断', allValue, '包含争议来源和度数诊断，保留差异供审计。')}
        ${renderRealCaseMetric('controversial_reference', `${controversial.caseCount ?? 5} cases`, controversial.note || '来源矛盾、时区争议或边界度数样本。')}
      </div>
      <div class="real-case-revalidation-boundary">
        <strong>边界</strong>
        <span>${escapeHtml(state.boundary || REAL_CASE_REVALIDATION_BASELINE.boundary)}</span>
      </div>
    </div>
  `;
}

function renderRealCaseMetric(label, value, note) {
  return `
    <div class="real-case-revalidation-metric">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
      <small>${escapeHtml(note)}</small>
    </div>
  `;
}

function getTrustCenterStatusMessage(pwa, runtime = getRuntimeHealthStatus()) {
  const health = window.__jyotishRuntimeHealth || {};
  if (health.status === 'checking') return '正在运行健康检查...';
  if (health.status === 'ok') return '健康检查通过：本地 API 服务、能力目录和 PWA 安装壳状态已记录。';
  if (health.status === 'warn') return `健康检查未通过：${health.error || runtime.note || '本地 API 或能力目录未通过健康检查。'}`;
  return pwa.note;
}

function renderTrustStatus(label, value, note) {
  return `
    <div class="trust-status-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
      <small>${escapeHtml(note)}</small>
    </div>
  `;
}

function getRuntimeHealthStatus() {
  const health = window.__jyotishRuntimeHealth;
  if (!health) {
    return {
      label: '未运行',
      note: '点击运行健康检查，确认本地 API 服务、能力目录和 PWA 安装壳状态。',
      tone: 'pending',
      details: [],
    };
  }
  if (health.status === 'checking') {
    return {
      label: '检查中',
      note: '正在探测 /api/health、/api/capability_audit 与 PWA 状态。',
      tone: 'pending',
      details: health.details || [],
    };
  }
  if (health.status === 'ok') {
    return {
      label: '可用',
      note: `${health.apiBase || '本地 API'} · v${health.version || '-'} · ${health.latencyMs ?? '-'}ms`,
      tone: 'ok',
      details: health.details || [],
    };
  }
  return {
    label: '需处理',
    note: health.error || '本地 API 或能力目录未通过健康检查。',
    tone: 'warn',
    details: health.details || [],
  };
}

function renderRuntimeHealthPanel(runtime = getRuntimeHealthStatus()) {
  const details = runtime.details?.length ? runtime.details : [
    ['PWA 安装壳', getPWAStatus().label, getPWAStatus().note],
    ['本地 API 服务', '待检查', '默认探测 http://127.0.0.1:5200/api/health'],
    ['Desktop path', 'PWA now', 'Pake shell 短期可用；Tauri sidecar 留给一键启动本地 API 服务。'],
  ];
  return `
    <div class="runtime-health-panel runtime-health-${escapeAttr(runtime.tone || 'pending')}">
      <div class="calculation-settings-head">
        <strong>Runtime Health</strong>
        <span>${escapeHtml(runtime.note)}</span>
      </div>
      <div class="runtime-health-grid">
        ${details.map(([label, value, note]) => `
          <div class="runtime-health-item">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(String(value || '-'))}</strong>
            <small>${escapeHtml(note || '')}</small>
          </div>
        `).join('')}
      </div>
      ${renderStaticDemoBoundary()}
      <p class="runtime-health-note">Packaging preflight: python3 scripts/desktop_packaging_preflight.py。Pake 适合快速 URL 壳；Tauri shell with sidecar 适合后续一键启动本地 API 服务。</p>
    </div>
  `;
}

function renderStaticDemoBoundary() {
  return `
    <div class="static-demo-boundary static-demo-boundary-compact" data-static-demo-boundary>
      <div class="static-demo-boundary-head">
        <strong>静态演示模式</strong>
        <span>公开静态站点只承载网页壳；完整计算需要用户自己启动本地 API。</span>
      </div>
      <div class="static-demo-boundary-grid">
        <div>
          <span>浏览器 fallback</span>
          <p>可直接体验：出生资料输入、基础 D1/D9 星盘、术语模式、Trust Center</p>
        </div>
        <div>
          <span>需要本地 API 服务</span>
          <p>需要本地 API：PDF/HTML 报告、高级技法、真实案例复验、AI 解读代理</p>
        </div>
        <div>
          <span>Deploy</span>
          <p>Vercel / Netlify / GitHub Pages 适合静态壳；Docker Compose 适合完整本机版本。</p>
        </div>
      </div>
    </div>
  `;
}

function getPWAStatus() {
  const status = window.__jyotishPWAStatus || {};
  if (status.installed || status.installPrompt === 'installed') {
    return { label: '已安装', note: '浏览器已把 Jyotish 加入应用环境。' };
  }
  if (status.installPrompt === 'ready') {
    return { label: '可安装', note: '可以通过按钮安装为桌面/移动应用。' };
  }
  if (status.serviceWorker === 'registered') {
    return { label: '离线壳已注册', note: '静态页面可缓存；高级计算仍需本地 API 服务在线。' };
  }
  if (status.serviceWorker === 'failed') {
    return { label: '注册失败', note: status.error || 'Service worker 注册失败。' };
  }
  if (status.serviceWorker === 'unsupported') {
    return { label: '不支持', note: '当前浏览器不支持 service worker。' };
  }
  return { label: '检测中', note: '正在检查 manifest 与 service worker。' };
}

function updateTrustCenterPWAStatus() {
  const host = $('trust-center-status');
  if (!host) return;
  host.textContent = getPWAStatus().note;
}

function getTrustCenterStats() {
  return {
    charts: readChartLibrary().length,
    pairs: readSynastryPairLibrary().length,
    prashnas: readPrashnaCaseLibrary().length,
    keys: TRUST_CENTER_STORAGE_KEYS.filter(key => localStorage.getItem(key) !== null).length,
  };
}

function exportTrustCenterLocalData() {
  const payload = {
    exportedAt: new Date().toISOString(),
    terminologyMode: readTerminologyMode(),
    storage: Object.fromEntries(TRUST_CENTER_STORAGE_KEYS.map(key => [key, readTrustStorageValue(key)])),
  };
  downloadText(JSON.stringify(payload, null, 2), `jyotish-local-data-${toDateISO(new Date())}.json`, 'application/json;charset=utf-8');
  const status = $('trust-center-status');
  if (status) status.textContent = '已导出本地资料 JSON。';
}

function readTrustStorageValue(key) {
  const raw = localStorage.getItem(key);
  if (raw == null) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function clearTrustCenterLocalData() {
  if (!window.confirm('清空本地星盘、配对、问事、计算设置和相关本地状态？此操作不可撤销。')) return;
  TRUST_CENTER_STORAGE_KEYS.forEach(key => localStorage.removeItem(key));
  _caseWorkspaceSelection.clear();
  _caseWorkspacePreview = null;
  setGlossaryTerminologyMode(DEFAULT_CALCULATION_SETTINGS.terminologyMode);
  if (chartData) chartData._terminology_mode = DEFAULT_CALCULATION_SETTINGS.terminologyMode;
  const status = $('trust-center-status');
  if (status) status.textContent = '本地资料已清空。';
  renderAll();
  setupSavedChartPanel();
}

async function runTrustCenterHealthCheck() {
  const status = $('trust-center-status');
  const checkedAt = new Date().toISOString();
  window.__jyotishRuntimeHealth = {
    status: 'checking',
    checkedAt,
    details: [
      ['PWA 安装壳', getPWAStatus().label, getPWAStatus().note],
      ['本地 API 服务', '检查中', '正在请求 /api/health'],
      ['Technique catalog', '等待中', 'API 在线后检查能力目录'],
    ],
  };
  if (status) status.textContent = '正在运行健康检查...';
  renderAll();
  try {
    const api = await window.JyotishAPI.getAPIHealth();
    const audit = await window.JyotishAPI.getCapabilityAudit();
    const surfaces = audit?.surfaces || {};
    const registry = audit?.registry || {};
    window.__jyotishRuntimeHealth = {
      status: 'ok',
      checkedAt,
      apiBase: api.base,
      version: api.version,
      latencyMs: api.latencyMs,
      details: [
        ['PWA 安装壳', getPWAStatus().label, getPWAStatus().note],
        ['本地 API 服务', api.base || 'online', `health ok · v${api.version || '-'} · ${api.latencyMs}ms`],
        ['Technique catalog', `${registry.technique_count || 0} techniques`, `${surfaces.api_endpoint_count || 0} API endpoints 可被前端发现`],
        ['Desktop path', 'PWA now', 'Pake shell 可快速包 URL；Tauri sidecar 等 API 生命周期和签名策略确定后再落地。'],
      ],
    };
    if (status) status.textContent = '健康检查通过：本地 API 服务、能力目录和 PWA 安装壳状态已记录。';
  } catch (error) {
    window.__jyotishRuntimeHealth = {
      status: 'warn',
      checkedAt,
      error: error?.message || '运行健康检查失败',
      details: [
        ['PWA 安装壳', getPWAStatus().label, getPWAStatus().note],
        ['本地 API 服务', '未连接', error?.message || '请确认本地 API 服务正在 127.0.0.1:5200 运行'],
        ['启动路径', '普通用户启动路径', '按 README 先启动网页服务，再启动本地 API 服务。'],
        ['Packaging preflight', '待检查', '运行 python3 scripts/desktop_packaging_preflight.py 获取桌面包装前置结果。'],
      ],
    };
    if (status) status.textContent = `健康检查未通过：${window.__jyotishRuntimeHealth.error}`;
  }
  renderAll();
}

async function runTrustCenterRealCaseRevalidation() {
  const status = $('trust-center-status');
  window.__jyotishRealCaseRevalidation = {
    status: 'checking',
    checkedAt: new Date().toISOString(),
    publicReference: REAL_CASE_REVALIDATION_BASELINE.publicReference,
    allChecks: REAL_CASE_REVALIDATION_BASELINE.allChecks,
    controversialReference: REAL_CASE_REVALIDATION_BASELINE.controversialReference,
    boundary: REAL_CASE_REVALIDATION_BASELINE.boundary,
  };
  if (status) status.textContent = '正在复验真实案例...';
  renderAll();
  try {
    const result = await window.JyotishAPI.getRealCaseRevalidation();
    window.__jyotishRealCaseRevalidation = {
      status: result.success ? 'ok' : 'warn',
      checkedAt: new Date().toISOString(),
      publicReference: {
        label: result.public_reference?.label || '公开人物星座级一致率',
        passed: result.public_reference?.passed,
        total: result.public_reference?.total,
        passRate: result.public_reference?.pass_rate,
      },
      allChecks: {
        passed: result.all_checks?.passed,
        total: result.all_checks?.total,
      },
      controversialReference: {
        caseCount: result.controversial_reference?.case_count,
        note: result.controversial_reference?.note,
      },
      boundary: result.accuracy_boundary || REAL_CASE_REVALIDATION_BASELINE.boundary,
    };
    if (status) {
      const ref = window.__jyotishRealCaseRevalidation.publicReference;
      status.textContent = `真实案例复验完成：公开人物星座级一致率 ${ref.passed}/${ref.total}。`;
    }
  } catch (error) {
    window.__jyotishRealCaseRevalidation = {
      status: 'warn',
      checkedAt: new Date().toISOString(),
      publicReference: REAL_CASE_REVALIDATION_BASELINE.publicReference,
      allChecks: REAL_CASE_REVALIDATION_BASELINE.allChecks,
      controversialReference: REAL_CASE_REVALIDATION_BASELINE.controversialReference,
      boundary: `真实案例复验需要本地 API 服务：${error?.message || '请先启动本地 API。'} 这不是人生事件预测准确率。`,
    };
    if (status) status.textContent = `真实案例复验未完成：${error?.message || '本地 API 未连接'}`;
  }
  renderAll();
}

async function promptPWAInstall() {
  const status = $('trust-center-status');
  const prompt = window.__jyotishDeferredInstallPrompt;
  if (!prompt) {
    if (status) status.textContent = getPWAStatus().note || '当前浏览器尚未提供安装提示，可使用浏览器菜单添加到主屏幕。';
    return;
  }
  prompt.prompt();
  const result = await prompt.userChoice.catch(() => null);
  window.__jyotishDeferredInstallPrompt = null;
  if (status) status.textContent = result?.outcome === 'accepted' ? '已接受安装。' : '已取消安装。';
}

function saveCalculationSettingsFromPanel(panel) {
  const settings = {};
  panel.querySelectorAll('[data-setting-key]').forEach(input => {
    settings[input.dataset.settingKey] = input.value;
  });
  const normalized = writeCalculationSettings(settings);
  if (chartData) attachCalculationSettings(chartData, normalized);
  renderAll();
}

function readTerminologyMode(value = readCalculationSettings().terminologyMode) {
  return Object.prototype.hasOwnProperty.call(TERMINOLOGY_MODE_OPTIONS, value) ? value : DEFAULT_CALCULATION_SETTINGS.terminologyMode;
}

function writeTerminologyMode(mode) {
  const normalized = readTerminologyMode(mode);
  const settings = { ...readCalculationSettings(), terminologyMode: normalized };
  writeCalculationSettings(settings);
  localStorage.setItem(TERMINOLOGY_MODE_KEY, normalized);
  setGlossaryTerminologyMode(normalized);
  if (chartData) chartData._terminology_mode = normalized;
  return normalized;
}

function getTerminologyModeOption(mode = readTerminologyMode()) {
  const normalized = readTerminologyMode(mode);
  return TERMINOLOGY_MODE_OPTIONS[normalized] || TERMINOLOGY_MODE_OPTIONS.beginner;
}

function renderTerminologyModePanel() {
  const current = readTerminologyMode();
  return `
    <div class="terminology-mode-panel">
      <div class="calculation-settings-head">
        <strong>Terminology Mode</strong>
        <span>${escapeHtml(getTerminologyModeOption(current).note)}</span>
      </div>
      <div class="terminology-mode-options" role="radiogroup" aria-label="术语模式">
        ${Object.entries(TERMINOLOGY_MODE_OPTIONS).map(([value, option]) => `
          <label class="terminology-mode-option${value === current ? ' active' : ''}">
            <input type="radio" name="terminology-mode" value="${escapeAttr(value)}"${value === current ? ' checked' : ''}>
            <strong>${escapeHtml(option.label)}</strong>
            <span>${escapeHtml(option.shortLabel)}</span>
            <small>${escapeHtml(option.note)}</small>
          </label>
        `).join('')}
      </div>
      <button type="button" class="provenance-action terminology-mode-save" data-action="save-terminology-mode">保存术语模式</button>
    </div>
  `;
}

function saveTerminologyModeFromPanel(panel) {
  const selected = panel.querySelector('input[name="terminology-mode"]:checked')?.value;
  writeTerminologyMode(selected);
  renderAll();
}

function buildPanchangaRows(panchanga) {
  if (!panchanga) return [['状态', '不可用', '当前星盘缺少太阳/月亮经度']];
  return [
    ['Vara', panchanga.vara || '-', '星期/日主'],
    ['Tithi', `${panchanga.tithi?.number || '-'} · ${panchanga.tithi?.name || '-'}`, panchanga.tithi?.paksha || ''],
    ['Karana', panchanga.karana?.name || panchanga.karana || '-', '半 Tithi'],
    ['Yoga', `${panchanga.yoga?.number || '-'} · ${panchanga.yoga?.name || '-'}`, '日月合经'],
  ];
}

function renderTithiLordInsight(analysis) {
  if (!analysis || !analysis.tithi_lord) return '';
  const doshaCount = Array.isArray(analysis.doshas) ? analysis.doshas.length : 0;
  return `
    <div class="tithi-lord-insight">
      <div class="provenance-head">
        <span>Tithi Lord</span>
        <strong>${escapeHtml(analysis.tithi_lord)} · ${escapeHtml(String(Math.round((analysis.tithi_score || 0) * 100)))}%</strong>
      </div>
      <p>${escapeHtml(analysis.relationship_style || analysis.emotional_pattern || '已接入 Tithi 主星分析。')}</p>
      <div class="tithi-chip-row">
        <span>${escapeHtml(analysis.tithi_type_cn || analysis.tithi_type || 'Tithi')}</span>
        <span>${escapeHtml(analysis.lord_sign || '-')} H${escapeHtml(String(analysis.lord_house || '-'))}</span>
        <span>${doshaCount ? `${doshaCount} dosha` : 'no dosha'}</span>
      </div>
    </div>
  `;
}

function renderChartWorkspaceList(lib) {
  if (!Array.isArray(lib) || !lib.length) {
    return '<div class="workspace-library empty">暂无保存星盘。保存当前盘后可从这里直接打开。</div>';
  }
  return `
    <div class="workspace-library">
      <label>
        <span>本地星盘库</span>
        <select id="workspace-chart-select">
          ${lib.map(entry => `<option value="${escapeAttr(entry.id)}">${escapeHtml(formatWorkspaceCaseTitle(entry, 'chart'))}</option>`).join('')}
        </select>
      </label>
      <div class="workspace-chart-list">
        ${lib.slice(0, 4).map(entry => `
          <div class="workspace-chart-row">
            <strong>${escapeHtml(entry.label || entry.id || '未命名星盘')}</strong>
            ${renderCaseMetaLine(entry, 'chart')}
            <span>${escapeHtml(formatSavedAt(entry.savedAt || entry.updatedAt))}</span>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

function renderCaseWorkspaceSummary(pairs, prashnas) {
  const filter = readCaseWorkspaceFilter();
  const chartLibrary = sortChartLibrary(readChartLibrary());
  const filteredCharts = filterCaseRecords(chartLibrary, filter, 'chart');
  const filteredPairs = filterCaseRecords(pairs || [], filter, 'pair');
  const filteredPrashnas = filterCaseRecords(prashnas || [], filter, 'prashna');
  pruneCaseWorkspaceSelection(chartLibrary, pairs || [], prashnas || []);
  return `
    <div id="case-workspace-summary" class="workspace-library case-workspace-summary">
      <div id="case-workspace-counts" class="case-workspace-counts">
        ${renderCaseWorkspaceCounts(chartLibrary, pairs || [], prashnas || [], filteredCharts, filteredPairs, filteredPrashnas)}
      </div>
      <div class="case-workspace-controls">
        <input type="search" id="workspace-case-search" placeholder="搜索问题、对象或结论" value="${escapeAttr(filter.query)}">
        <select id="workspace-case-type">
          <option value="all"${filter.type === 'all' ? ' selected' : ''}>全部案例</option>
          <option value="chart"${filter.type === 'chart' ? ' selected' : ''}>只看星盘</option>
          <option value="pair"${filter.type === 'pair' ? ' selected' : ''}>只看配对</option>
          <option value="prashna"${filter.type === 'prashna' ? ' selected' : ''}>只看问事</option>
        </select>
        <select id="workspace-case-group">
          ${CASE_GROUP_PRESETS.map(group => `<option value="${escapeAttr(group)}"${filter.group === group ? ' selected' : ''}>${escapeHtml(group)}</option>`).join('')}
        </select>
        <select id="workspace-case-relation">
          ${CASE_RELATION_PRESETS.map(([value, label]) => `<option value="${escapeAttr(value)}"${filter.relation === value ? ' selected' : ''}>${escapeHtml(label)}</option>`).join('')}
        </select>
      </div>
      <div class="case-bulk-actions">
        <button type="button" class="mini-action" data-action="workspace-select-visible">全选当前</button>
        <button type="button" class="mini-action" data-action="workspace-clear-selection">清空选择</button>
        <button type="button" class="mini-action" data-action="workspace-export-selected-cases">导出已选</button>
        <button type="button" class="mini-action danger" data-action="workspace-delete-selected-cases">删除已选</button>
      </div>
      <div id="workspace-case-list" class="workspace-chart-list">
        ${renderCaseWorkspaceRows(filteredCharts, filteredPairs, filteredPrashnas, filter)}
      </div>
      <div id="workspace-case-preview" class="case-preview-panel">
        ${renderWorkspaceCasePreview()}
      </div>
    </div>
  `;
}

function renderCaseWorkspaceCounts(charts, pairs, prashnas, filteredCharts, filteredPairs, filteredPrashnas) {
  return `
    <span>星盘 ${escapeHtml(String((charts || []).length))}</span>
    <span>配对 ${escapeHtml(String((pairs || []).length))}</span>
    <span>问事 ${escapeHtml(String((prashnas || []).length))}</span>
    <span>显示 ${escapeHtml(String((filteredCharts || []).length + (filteredPairs || []).length + (filteredPrashnas || []).length))}</span>
    <span>已选 ${escapeHtml(String(_caseWorkspaceSelection.size))}</span>
  `;
}

function renderCaseWorkspaceRows(filteredCharts, filteredPairs, filteredPrashnas, filter) {
  const chartRows = filteredCharts.slice(0, 4).map(record => `
    <div class="workspace-chart-row workspace-case-row">
      ${renderCaseSelectControl('chart', record.id || '', '星盘')}
      <div>
        <strong>${escapeHtml(record.label || record.id || '未命名星盘')}</strong>
        ${renderCaseMetaLine(record, 'chart')}
        <span>${escapeHtml(formatSavedAt(record.updatedAt || record.savedAt))}</span>
      </div>
      <div class="case-row-actions">
        <button type="button" class="mini-action" data-action="workspace-preview-case" data-case-kind="chart" data-case-id="${escapeAttr(record.id || '')}">预览</button>
        <button type="button" class="mini-action" data-action="workspace-edit-case" data-case-kind="chart" data-case-id="${escapeAttr(record.id || '')}">编辑</button>
        <button type="button" class="mini-action" data-action="workspace-open-chart" data-case-id="${escapeAttr(record.id || '')}">打开</button>
      </div>
    </div>
  `).join('');
  const pairRows = filteredPairs.slice(0, 4).map(record => `
    <div class="workspace-chart-row workspace-case-row">
      ${renderCaseSelectControl('pair', record.id || '', '配对')}
      <div>
        <strong>${escapeHtml(record.label || record.id || '未命名配对')}</strong>
        ${renderCaseMetaLine(record, 'pair')}
        <span>${escapeHtml(record.score?.total ?? 0)} / ${escapeHtml(record.score?.max ?? 36)} · ${escapeHtml(record.verdict || '-')}</span>
      </div>
      <div class="case-row-actions">
        <button type="button" class="mini-action" data-action="workspace-preview-case" data-case-kind="pair" data-case-id="${escapeAttr(record.id || '')}">预览</button>
        <button type="button" class="mini-action" data-action="workspace-edit-case" data-case-kind="pair" data-case-id="${escapeAttr(record.id || '')}">编辑</button>
        <button type="button" class="mini-action" data-action="workspace-open-pair" data-case-id="${escapeAttr(record.id || '')}">打开</button>
        <button type="button" class="mini-action danger" data-action="workspace-delete-pair" data-case-id="${escapeAttr(record.id || '')}">删除</button>
      </div>
    </div>
  `).join('');
  const prashnaRows = filteredPrashnas.slice(0, 4).map(record => `
    <div class="workspace-chart-row workspace-case-row">
      ${renderCaseSelectControl('prashna', record.id || '', '问事')}
      <div>
        <strong>${escapeHtml(record.label || record.id || '未命名问事')}</strong>
        ${renderCaseMetaLine(record, 'prashna')}
        <span>${escapeHtml(record.conclusion || '-')} · ${escapeHtml(formatSavedAt(record.updatedAt || record.generatedAt))}</span>
      </div>
      <div class="case-row-actions">
        <button type="button" class="mini-action" data-action="workspace-preview-case" data-case-kind="prashna" data-case-id="${escapeAttr(record.id || '')}">预览</button>
        <button type="button" class="mini-action" data-action="workspace-edit-case" data-case-kind="prashna" data-case-id="${escapeAttr(record.id || '')}">编辑</button>
        <button type="button" class="mini-action" data-action="workspace-open-prashna" data-case-id="${escapeAttr(record.id || '')}">打开</button>
        <button type="button" class="mini-action danger" data-action="workspace-delete-prashna" data-case-id="${escapeAttr(record.id || '')}">删除</button>
      </div>
    </div>
  `).join('');
  return `
    ${filter.type !== 'pair' && filter.type !== 'prashna' ? chartRows : ''}
    ${filter.type !== 'prashna' ? pairRows : ''}
    ${filter.type !== 'pair' ? prashnaRows : ''}
    ${!chartRows && !pairRows && !prashnaRows ? '<div class="workspace-library empty">暂无匹配案例。</div>' : ''}
  `;
}

function refreshCaseWorkspaceList() {
  const countContainer = $('case-workspace-counts');
  const listContainer = $('workspace-case-list');
  if (!countContainer || !listContainer) return;
  const charts = sortChartLibrary(readChartLibrary());
  const pairs = sortCaseLibrary(readSynastryPairLibrary());
  const prashnas = sortCaseLibrary(readPrashnaCaseLibrary());
  pruneCaseWorkspaceSelection(charts, pairs, prashnas);
  const filter = readCaseWorkspaceFilter();
  const filteredCharts = filterCaseRecords(charts, filter, 'chart');
  const filteredPairs = filterCaseRecords(pairs, filter, 'pair');
  const filteredPrashnas = filterCaseRecords(prashnas, filter, 'prashna');
  countContainer.innerHTML = renderCaseWorkspaceCounts(charts, pairs, prashnas, filteredCharts, filteredPairs, filteredPrashnas);
  listContainer.innerHTML = renderCaseWorkspaceRows(filteredCharts, filteredPairs, filteredPrashnas, filter);
  renderWorkspaceCasePreviewPanel();
}

function readCaseWorkspaceFilter() {
  return {
    query: $('workspace-case-search')?.value?.trim() || '',
    type: $('workspace-case-type')?.value || 'all',
    group: $('workspace-case-group')?.value || '全部分组',
    relation: $('workspace-case-relation')?.value || 'all',
  };
}

function filterCaseRecords(records, filter, kind) {
  if (filter.type !== 'all' && filter.type !== kind) return [];
  let filtered = Array.isArray(records) ? records : [];
  if (filter.group && filter.group !== '全部分组') {
    filtered = filtered.filter(record => getCaseGroupLabel(record, kind) === filter.group);
  }
  if (filter.relation && filter.relation !== 'all') {
    filtered = filtered.filter(record => getCaseRelationValue(record, kind) === filter.relation);
  }
  const query = normalizeCaseSearchText(filter.query);
  if (!query) return filtered;
  return filtered.filter(record => normalizeCaseSearchText([
    record?.label,
    record?.group,
    getCaseRelationLabel(record, kind),
    ...(Array.isArray(record?.tags) ? record.tags : []),
    record?.question_text,
    record?.question_type,
    record?.conclusion,
    record?.verdict,
    record?.self?.ascendant,
    record?.partner?.ascendant,
    record?.chartLabel,
    record?.id,
  ].filter(Boolean).join(' ')).includes(query));
}

function normalizeCaseSearchText(value) {
  return String(value || '').trim().toLowerCase();
}

function buildCaseSelectionKey(kind, id) {
  return `${kind}:${id}`;
}

function renderCaseSelectControl(kind, id, label) {
  const key = buildCaseSelectionKey(kind, id || '');
  return `
    <label class="case-select-control" title="选择案例">
      <input type="checkbox" data-action="workspace-toggle-case" data-case-key="${escapeAttr(key)}" ${_caseWorkspaceSelection.has(key) ? 'checked' : ''}>
      <span>${escapeHtml(label)}</span>
    </label>
  `;
}

function pruneCaseWorkspaceSelection(charts, pairs, prashnas) {
  const valid = new Set([
    ...(charts || []).filter(item => item?.id).map(item => buildCaseSelectionKey('chart', item.id)),
    ...(pairs || []).filter(item => item?.id).map(item => buildCaseSelectionKey('pair', item.id)),
    ...(prashnas || []).filter(item => item?.id).map(item => buildCaseSelectionKey('prashna', item.id)),
  ]);
  _caseWorkspaceSelection = new Set([..._caseWorkspaceSelection].filter(key => valid.has(key)));
}

function getVisibleCaseSelectionKeys() {
  return [...document.querySelectorAll('#workspace-case-list [data-case-key]')]
    .map(input => input.dataset.caseKey)
    .filter(Boolean);
}

function resolveSelectedCaseRecords() {
  const charts = readChartLibrary();
  const pairs = readSynastryPairLibrary();
  const prashnas = readPrashnaCaseLibrary();
  const selected = [..._caseWorkspaceSelection];
  return {
    chartRecords: selected
      .filter(key => key.startsWith('chart:'))
      .map(key => charts.find(record => record?.id === key.slice(6)))
      .filter(Boolean),
    pairRecords: selected
      .filter(key => key.startsWith('pair:'))
      .map(key => pairs.find(record => record?.id === key.slice(5)))
      .filter(Boolean),
    prashnaRecords: selected
      .filter(key => key.startsWith('prashna:'))
      .map(key => prashnas.find(record => record?.id === key.slice(8)))
      .filter(Boolean),
  };
}

function previewWorkspaceCase(kind, id) {
  const record = findWorkspaceCaseRecord(kind, id);
  if (!record) return;
  _caseWorkspacePreview = { kind, id };
  renderWorkspaceCasePreviewPanel();
}

function findWorkspaceCaseRecord(kind, id) {
  if (!id) return null;
  if (kind === 'pair') return readSynastryPairLibrary().find(record => record?.id === id) || null;
  if (kind === 'prashna') return readPrashnaCaseLibrary().find(record => record?.id === id) || null;
  return readChartLibrary().find(record => record?.id === id) || null;
}

function renderWorkspaceCasePreviewPanel() {
  const panel = $('workspace-case-preview');
  if (!panel) return;
  panel.innerHTML = renderWorkspaceCasePreview();
}

function renderWorkspaceCasePreview() {
  if (!_caseWorkspacePreview) {
    return '<div class="case-preview-empty">选择一条案例后，可在这里快速查看摘要。</div>';
  }
  const { kind, id } = _caseWorkspacePreview;
  const record = findWorkspaceCaseRecord(kind, id);
  if (!record) {
    _caseWorkspacePreview = null;
    return '<div class="case-preview-empty">所选案例已不存在。</div>';
  }
  const meta = normalizeWorkspaceMeta(record, getCaseDefaultMeta(kind));
  const title = record.label || record.question_text || record.id || '未命名案例';
  return `
    <div class="case-preview-head">
      <div>
        <span>${escapeHtml(getCaseKindLabel(kind))}</span>
        <strong>${escapeHtml(title)}</strong>
      </div>
      <button type="button" class="mini-action" data-action="workspace-clear-preview">收起</button>
    </div>
    ${renderCaseMetaLine(record, kind)}
    <div class="case-preview-grid">
      ${renderWorkspaceCasePreviewCards(record, kind)}
    </div>
    <div class="case-preview-footer">
      <span>${escapeHtml(meta.group)} · ${escapeHtml(getCaseRelationLabel(record, kind))}</span>
      <span>${escapeHtml(formatSavedAt(record.updatedAt || record.generatedAt || record.savedAt))}</span>
    </div>
  `;
}

function renderWorkspaceCasePreviewCards(record, kind) {
  if (kind === 'pair') return renderSynastryCasePreviewCards(record);
  if (kind === 'prashna') return renderPrashnaCasePreviewCards(record);
  return renderChartCasePreviewCards(record);
}

function renderChartCasePreviewCards(record) {
  const data = record.data || {};
  const birth = data.birth_info || {};
  const asc = data.ascendant || {};
  const moon = data.planets?.Moon || {};
  return [
    ['出生', `${birth.date || '-'} ${birth.time || ''}`.trim() || '-'],
    ['上升', asc.sign ? signName(asc.sign) : '-'],
    ['月亮', moon.sign ? `${signName(moon.sign)} ${moon.nakshatra || ''}`.trim() : '-'],
    ['坐标', birth.lat != null && birth.lon != null ? `${safeNumber(birth.lat).toFixed(3)}, ${safeNumber(birth.lon).toFixed(3)}` : '-'],
  ].map(renderCasePreviewCard).join('');
}

function renderSynastryCasePreviewCards(record) {
  const score = record.score || {};
  const deep = record.deep || {};
  return [
    ['合盘分', `${score.total ?? 0} / ${score.max ?? 36}${score.percentage != null ? ` · ${score.percentage}%` : ''}`],
    ['判断', record.verdict || '-'],
    ['对方', record.partner?.moon || record.partner?.ascendant || '-'],
    ['节奏', deep.dasha?.note || deep.dasha?.label || '-'],
  ].map(renderCasePreviewCard).join('');
}

function renderPrashnaCasePreviewCards(record) {
  return [
    ['问题', record.question_text || record.question_type || '-'],
    ['结论', record.conclusion || '-'],
    ['置信度', record.confidence || '-'],
    ['下一步', record.next_action || '-'],
  ].map(renderCasePreviewCard).join('');
}

function renderCasePreviewCard([label, value]) {
  return `<div class="case-preview-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value || '-')}</strong></div>`;
}

function getCaseKindLabel(kind) {
  if (kind === 'pair') return '配对';
  if (kind === 'prashna') return '问事';
  return '星盘';
}

function editWorkspaceCaseMetadata(kind, id) {
  if (!id) return;
  const store = getWorkspaceCaseStore(kind);
  const records = store.read();
  const record = records.find(item => item?.id === id);
  if (!record) return;
  const fallback = getCaseDefaultMeta(kind);
  const currentMeta = normalizeWorkspaceMeta(record, fallback);
  const label = window.prompt('案例标题', record.label || record.id || '');
  if (label === null) return;
  const group = window.prompt(`分组（${CASE_GROUP_PRESETS.slice(1).join(' / ')}）`, currentMeta.group || fallback.group);
  if (group === null) return;
  const relation = window.prompt(`关系类型（${CASE_RELATION_PRESETS.filter(([key]) => key !== 'all').map(([key]) => key).join(' / ')}）`, currentMeta.relation || fallback.relation);
  if (relation === null) return;
  const tags = window.prompt('标签（逗号分隔）', currentMeta.tags.join(', '));
  if (tags === null) return;
  const updated = applyWorkspaceCaseMetadata(record, { label, group, relation, tags }, fallback);
  store.write(records.map(item => item?.id === id ? updated : item));
  renderSynastryPairWorkspace();
  renderPrashnaCaseWorkspace();
  refreshCaseWorkspaceList();
}

function getWorkspaceCaseStore(kind) {
  if (kind === 'pair') {
    return { read: readSynastryPairLibrary, write: value => writeSynastryPairLibrary(sortCaseLibrary(value).slice(0, 80)) };
  }
  if (kind === 'prashna') {
    return { read: readPrashnaCaseLibrary, write: value => writePrashnaCaseLibrary(sortCaseLibrary(value).slice(0, 80)) };
  }
  return { read: readChartLibrary, write: value => writeChartLibrary(sortChartLibrary(value).slice(0, 24)) };
}

function applyWorkspaceCaseMetadata(record, input, fallback = {}) {
  const tags = String(input.tags || '')
    .split(',')
    .map(tag => tag.trim())
    .filter(Boolean);
  const relationKeys = new Set(CASE_RELATION_PRESETS.map(([key]) => key));
  const relation = relationKeys.has(input.relation) && input.relation !== 'all'
    ? input.relation
    : (fallback.relation || 'unknown');
  return {
    ...record,
    label: String(input.label || record.label || record.id || '').trim() || record.label || record.id,
    group: String(input.group || '').trim() || fallback.group || '未分组',
    relation,
    tags: tags.length ? tags : (fallback.tags || []),
    updatedAt: new Date().toISOString(),
  };
}

function formatSavedAt(value) {
  if (!value) return '未记录保存时间';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

function bindProvenanceActions() {
  const panel = $('provenance-panel');
  if (!panel || panel.dataset.bound === 'true') return;
  panel.dataset.bound = 'true';
  panel.addEventListener('click', event => {
    const btn = event.target.closest('.provenance-action, .mini-action');
    if (!btn) return;
    if (btn.dataset.action === 'export-json') {
      const item = document.querySelector('.export-item[data-format="json"]');
      if (item) item.click();
    }
    if (btn.dataset.action === 'export-html') {
      const item = document.querySelector('.export-item[data-format="html"]');
      if (item) item.click();
    }
    if (btn.dataset.action === 'save-calculation-settings') {
      saveCalculationSettingsFromPanel(panel);
    }
    if (btn.dataset.action === 'save-terminology-mode') {
      saveTerminologyModeFromPanel(panel);
    }
    if (btn.dataset.action === 'panchanga-week') {
      setPanchangaRangePreset('week');
      renderPanchangaRange(panel);
    }
    if (btn.dataset.action === 'panchanga-month') {
      setPanchangaRangePreset('month');
      renderPanchangaRange(panel);
    }
    if (btn.dataset.action === 'panchanga-range') {
      renderPanchangaRange(panel);
    }
    if (btn.dataset.action === 'panchanga-csv') {
      exportPanchangaRangeCSV(panel);
    }
    if (btn.dataset.action === 'panchanga-ics') {
      exportPanchangaRangeICS(panel);
    }
    if (btn.dataset.action === 'workspace-save-current') {
      saveCurrentChartToWorkspace(panel);
    }
    if (btn.dataset.action === 'workspace-open-selected') {
      openSelectedWorkspaceChart(panel);
    }
    if (btn.dataset.action === 'workspace-delete-selected') {
      deleteSelectedWorkspaceChart();
    }
    if (btn.dataset.action === 'trust-run-health') {
      runTrustCenterHealthCheck();
    }
    if (btn.dataset.action === 'pwa-install') {
      promptPWAInstall();
    }
    if (btn.dataset.action === 'trust-export-local') {
      exportTrustCenterLocalData();
    }
    if (btn.dataset.action === 'trust-clear-local') {
      clearTrustCenterLocalData();
    }
    if (btn.dataset.action === 'workspace-export-selected') {
      exportSelectedWorkspaceChart();
    }
    if (btn.dataset.action === 'workspace-export-cases') {
      exportWorkspaceCaseLibrary();
    }
    if (btn.dataset.action === 'workspace-select-visible') {
      selectVisibleWorkspaceCases();
    }
    if (btn.dataset.action === 'workspace-clear-selection') {
      _caseWorkspaceSelection.clear();
      refreshCaseWorkspaceList();
    }
    if (btn.dataset.action === 'workspace-export-selected-cases') {
      exportSelectedWorkspaceCases();
    }
    if (btn.dataset.action === 'workspace-delete-selected-cases') {
      deleteSelectedWorkspaceCases();
    }
    if (btn.dataset.action === 'workspace-edit-case') {
      editWorkspaceCaseMetadata(btn.dataset.caseKind || 'chart', btn.dataset.caseId || '');
    }
    if (btn.dataset.action === 'workspace-preview-case') {
      previewWorkspaceCase(btn.dataset.caseKind || 'chart', btn.dataset.caseId || '');
    }
    if (btn.dataset.action === 'workspace-clear-preview') {
      _caseWorkspacePreview = null;
      renderWorkspaceCasePreviewPanel();
    }
    if (btn.dataset.action === 'workspace-open-pair') {
      openSavedSynastryPair(btn.dataset.caseId || '');
    }
    if (btn.dataset.action === 'workspace-open-chart') {
      openSavedChartFromPanel(btn.dataset.caseId || '');
    }
    if (btn.dataset.action === 'workspace-delete-pair') {
      deleteSavedSynastryPair(btn.dataset.caseId || '');
    }
    if (btn.dataset.action === 'workspace-open-prashna') {
      openSavedPrashnaCase(btn.dataset.caseId || '');
    }
    if (btn.dataset.action === 'workspace-delete-prashna') {
      deleteSavedPrashnaCase(btn.dataset.caseId || '');
    }
    if (btn.dataset.action === 'open-ai-library') {
      const fab = document.querySelector('.ai-fab');
      if (fab) fab.click();
    }
  });
  panel.addEventListener('change', event => {
    const input = event.target.closest('#workspace-case-import-file');
    if (input) {
      importWorkspaceCaseLibrary(input.files?.[0]);
      input.value = '';
      return;
    }
    const caseToggle = event.target.closest('[data-action="workspace-toggle-case"]');
    if (caseToggle) {
      if (caseToggle.checked) {
        _caseWorkspaceSelection.add(caseToggle.dataset.caseKey || '');
      } else {
        _caseWorkspaceSelection.delete(caseToggle.dataset.caseKey || '');
      }
      _caseWorkspaceSelection.delete('');
      refreshCaseWorkspaceList();
      return;
    }
    if (event.target.matches('input[name="terminology-mode"]')) {
      panel.querySelectorAll('.terminology-mode-option').forEach(option => option.classList.remove('active'));
      event.target.closest('.terminology-mode-option')?.classList.add('active');
      setGlossaryTerminologyMode(readTerminologyMode(event.target.value));
      return;
    }
    if (event.target.closest('#workspace-case-type')) {
      refreshCaseWorkspaceList();
    }
    if (event.target.closest('#workspace-case-group')) {
      refreshCaseWorkspaceList();
    }
    if (event.target.closest('#workspace-case-relation')) {
      refreshCaseWorkspaceList();
    }
  });
  panel.addEventListener('input', event => {
    if (event.target.closest('#workspace-case-search')) {
      refreshCaseWorkspaceList();
    }
  });
}

function getSelectedWorkspaceEntry() {
  const select = $('workspace-chart-select');
  const id = select?.value;
  if (!id) return null;
  return sortChartLibrary(readChartLibrary()).find(entry => entry?.id === id) || null;
}

function saveCurrentChartToWorkspace(panel) {
  const source = panel?._panchangaChartData || chartData;
  if (!source) return;
  const id = buildWorkspaceChartId(source);
  if (!id) return;
  const lib = readChartLibrary();
  const existing = findChartLibraryEntry(lib, source);
  if (existing) {
    const meta = normalizeWorkspaceMeta(existing, buildDefaultChartWorkspaceMeta(source));
    existing.id = id;
    existing.data = source;
    existing.label = existing.label || buildWorkspaceChartLabel(source);
    existing.group = meta.group;
    existing.relation = meta.relation;
    existing.tags = meta.tags;
    existing.updatedAt = new Date().toISOString();
  } else {
    const meta = buildDefaultChartWorkspaceMeta(source);
    lib.push({
      id,
      label: buildWorkspaceChartLabel(source),
      data: source,
      ...meta,
      savedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });
  }
  writeChartLibrary(sortChartLibrary(lib).slice(0, 24));
  renderAll();
}

function openSelectedWorkspaceChart(panel) {
  const entry = getSelectedWorkspaceEntry();
  if (!entry?.data) return;
  chartData = entry.data;
  panel._panchangaChartData = chartData;
  renderAll();
  showPage('chart');
  aiChatSetChartData(chartData);
}

function deleteSelectedWorkspaceChart() {
  const entry = getSelectedWorkspaceEntry();
  if (!entry) return;
  if (!window.confirm(`删除「${entry.label || entry.id}」？`)) return;
  writeChartLibrary(readChartLibrary().filter(item => item?.id !== entry.id));
  renderAll();
}

function exportSelectedWorkspaceChart() {
  const entry = getSelectedWorkspaceEntry();
  if (!entry) return;
  downloadText(JSON.stringify(entry, null, 2), `jyotish-chart-${entry.id || 'saved'}.json`, 'application/json;charset=utf-8');
}

function exportWorkspaceCaseLibrary() {
  const payload = {
    exportedAt: new Date().toISOString(),
    charts: sortChartLibrary(readChartLibrary()).map(({ data, ...entry }) => ({
      ...entry,
      meta: normalizeWorkspaceMeta(entry, buildDefaultChartWorkspaceMeta(data)),
    })),
    synastry_pairs: sortCaseLibrary(readSynastryPairLibrary()),
    prashna_cases: sortCaseLibrary(readPrashnaCaseLibrary()),
  };
  downloadText(JSON.stringify(payload, null, 2), `jyotish-case-library-${toDateISO(new Date())}.json`, 'application/json;charset=utf-8');
}

function selectVisibleWorkspaceCases() {
  getVisibleCaseSelectionKeys().forEach(key => _caseWorkspaceSelection.add(key));
  refreshCaseWorkspaceList();
}

function exportSelectedWorkspaceCases() {
  const { chartRecords, pairRecords, prashnaRecords } = resolveSelectedCaseRecords();
  if (!chartRecords.length && !pairRecords.length && !prashnaRecords.length) return;
  const payload = {
    exportedAt: new Date().toISOString(),
    charts: chartRecords.map(({ data, ...entry }) => entry),
    synastry_pairs: pairRecords,
    prashna_cases: prashnaRecords,
  };
  downloadText(JSON.stringify(payload, null, 2), `jyotish-selected-cases-${toDateISO(new Date())}.json`, 'application/json;charset=utf-8');
}

function deleteSelectedWorkspaceCases() {
  const { chartRecords, pairRecords, prashnaRecords } = resolveSelectedCaseRecords();
  const count = chartRecords.length + pairRecords.length + prashnaRecords.length;
  if (!count) return;
  if (!window.confirm(`删除已选 ${count} 条案例？此操作只会删除本地案例库记录。`)) return;
  const chartIds = new Set(chartRecords.map(record => record.id));
  const pairIds = new Set(pairRecords.map(record => record.id));
  const prashnaIds = new Set(prashnaRecords.map(record => record.id));
  writeChartLibrary(readChartLibrary().filter(record => !chartIds.has(record?.id)));
  writeSynastryPairLibrary(readSynastryPairLibrary().filter(record => !pairIds.has(record?.id)));
  writePrashnaCaseLibrary(readPrashnaCaseLibrary().filter(record => !prashnaIds.has(record?.id)));
  _caseWorkspaceSelection.clear();
  _caseWorkspacePreview = null;
  renderSynastryPairWorkspace();
  renderPrashnaCaseWorkspace();
  renderAll();
}

async function importWorkspaceCaseLibrary(file) {
  const status = $('workspace-case-import-status');
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.json') && file.type !== 'application/json') {
    if (status) status.textContent = '请选择 JSON 案例库文件。';
    return;
  }
  try {
    const payload = JSON.parse(await readWorkspaceFileAsText(file));
    const imported = mergeWorkspaceCaseLibrary(payload);
    if (status) {
      status.textContent = `已导入：星盘 ${imported.charts}、配对 ${imported.pairs}、问事 ${imported.prashnas}。`;
    }
    renderAll();
  } catch (error) {
    if (status) status.textContent = `导入失败：${error?.message || 'JSON 格式不正确'}`;
  }
}

function readWorkspaceFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(reader.error || new Error('文件读取失败'));
    reader.readAsText(file);
  });
}

function mergeWorkspaceCaseLibrary(payload) {
  const charts = Array.isArray(payload?.charts) ? payload.charts : [];
  const pairs = Array.isArray(payload?.synastry_pairs) ? payload.synastry_pairs : [];
  const prashnas = Array.isArray(payload?.prashna_cases) ? payload.prashna_cases : [];
  if (!charts.length && !pairs.length && !prashnas.length) {
    throw new Error('未找到 charts、synastry_pairs 或 prashna_cases。');
  }
  const validCharts = charts.filter(item => item?.id);
  const validPairs = pairs.filter(item => item?.id);
  const validPrashnas = prashnas.filter(item => item?.id);
  if (!validCharts.length && !validPairs.length && !validPrashnas.length) {
    throw new Error('案例库记录缺少 id，无法导入。');
  }
  const chartLib = mergeLibraryById(readChartLibrary(), validCharts, getCaseDefaultMeta('chart'));
  const pairLib = mergeLibraryById(readSynastryPairLibrary(), validPairs, getCaseDefaultMeta('pair'));
  const prashnaLib = mergeLibraryById(readPrashnaCaseLibrary(), validPrashnas, getCaseDefaultMeta('prashna'));
  writeChartLibrary(sortChartLibrary(chartLib).slice(0, 24));
  writeSynastryPairLibrary(sortCaseLibrary(pairLib).slice(0, 80));
  writePrashnaCaseLibrary(sortCaseLibrary(prashnaLib).slice(0, 80));
  return { charts: validCharts.length, pairs: validPairs.length, prashnas: validPrashnas.length };
}

function mergeLibraryById(current, incoming, defaultMeta = {}) {
  const byId = new Map((Array.isArray(current) ? current : []).filter(item => item?.id).map(item => [item.id, item]));
  for (const item of incoming) {
    const merged = { ...(byId.get(item.id) || {}), ...item, importedAt: new Date().toISOString() };
    const meta = normalizeWorkspaceMeta(merged, merged.meta || defaultMeta);
    byId.set(item.id, { ...merged, ...meta });
  }
  return [...byId.values()];
}

function openSavedSynastryPair(caseId) {
  const record = readSynastryPairLibrary().find(item => item?.id === caseId);
  if (!record) return;
  _lastSynastryPairRecord = record;
  const result = $('synastry-result');
  if (result) {
    result.innerHTML = renderSavedSynastryPair(record);
    bindTerms(result);
  }
  showPage('chart');
  switchToTab('synastry');
}

function deleteSavedSynastryPair(caseId) {
  const record = readSynastryPairLibrary().find(item => item?.id === caseId);
  if (!record) return;
  if (!window.confirm(`删除配对「${record.label || record.id}」？`)) return;
  writeSynastryPairLibrary(readSynastryPairLibrary().filter(item => item?.id !== caseId));
  if (_caseWorkspacePreview?.kind === 'pair' && _caseWorkspacePreview.id === caseId) _caseWorkspacePreview = null;
  renderSynastryPairWorkspace();
  renderAll();
}

function openSavedPrashnaCase(caseId) {
  const record = readPrashnaCaseLibrary().find(item => item?.id === caseId);
  if (!record) return;
  _lastPrashnaCaseRecord = record;
  recordPrashnaWorkflow(record.data || {}, record.question_text || '', record.question_type || 'general');
  const result = $('prashna-result');
  if (result) {
    result.innerHTML = renderPrashnaResult(record.data || {}, record.question_text || '');
    bindTerms(result);
  }
  showPage('chart');
  switchToTab('prashna');
}

function deleteSavedPrashnaCase(caseId) {
  const record = readPrashnaCaseLibrary().find(item => item?.id === caseId);
  if (!record) return;
  if (!window.confirm(`删除问事「${record.question_text || record.label || record.id}」？`)) return;
  writePrashnaCaseLibrary(readPrashnaCaseLibrary().filter(item => item?.id !== caseId));
  if (_caseWorkspacePreview?.kind === 'prashna' && _caseWorkspacePreview.id === caseId) _caseWorkspacePreview = null;
  renderPrashnaCaseWorkspace();
  renderAll();
}

function setPanchangaRangePreset(mode) {
  const startEl = $('panchanga-start');
  const endEl = $('panchanga-end');
  if (!startEl || !endEl) return;
  const base = parseDateISO(startEl.value || toDateISO(new Date()));
  if (mode === 'month') {
    const first = new Date(base.getFullYear(), base.getMonth(), 1);
    const last = new Date(base.getFullYear(), base.getMonth() + 1, 0);
    startEl.value = toDateISO(first);
    endEl.value = toDateISO(last);
    return;
  }
  startEl.value = toDateISO(base);
  endEl.value = toDateISO(addDays(base, 6));
}

async function renderPanchangaRange(panel) {
  const output = $('panchanga-range-result');
  const source = panel?._panchangaChartData || chartData;
  if (!output) return;
  if (!source) {
    output.innerHTML = '<div class="panchanga-week-error">请先生成星盘。</div>';
    return;
  }
  if (!window.JyotishAPI?.computePanchangaRange) {
    output.innerHTML = '<div class="panchanga-week-error">当前 API bridge 未提供 /api/panchanga_range。</div>';
    return;
  }

  output.innerHTML = '<div class="panchanga-week-loading">正在生成 Panchanga 日历...</div>';
  try {
    const payload = readPanchangaRangeInputs();
    const result = await window.JyotishAPI.computePanchangaRange(payload);
    const report = result?.report || {};
    const allRows = normalizePanchangaRangeRows(report.days || []);
    const selectedConditions = normalizePanchangaConditions(payload.conditions || payload.condition || []);
    const conditionMode = normalizePanchangaConditionMode(payload.condition_mode || payload.conditionMode);
    const rows = filterPanchangaRowsByCondition(allRows, selectedConditions, conditionMode);
    const activityLabel = getPanchangaActivityLabel(payload.activity || 'all');
    const conditionLabel = getPanchangaConditionSelectionLabel(selectedConditions, conditionMode);
    panel._lastPanchangaRange = { report, rows, allRows, activity: payload.activity || 'all', condition: selectedConditions[0] || 'all', conditions: selectedConditions, conditionMode };
    output.innerHTML = `
      <div class="panchanga-range-summary">
        <strong>${escapeHtml(report.start_date || payload.start_date)} → ${escapeHtml(report.end_date || payload.end_date)}</strong>
        <span>${escapeHtml(String(rows.length))}/${escapeHtml(String(report.day_count || allRows.length))} 天 · ${escapeHtml(activityLabel)} · ${escapeHtml(conditionLabel)} · ${escapeHtml(report.calculation_policy?.sunrise_sunset || report.calculation_policy?.inauspicious_periods || 'daytime eight-segment rule')}</span>
        ${renderPanchangaLocationSummary(report.location, source)}
      </div>
      ${renderPanchangaConditionGuide(selectedConditions, conditionMode, report.search_summary)}
      ${renderPanchangaFestivalDetails(rows)}
      ${renderPanchangaMonthGrid(report.month_grid || [])}
      <div class="panchanga-week-table-wrap">
        <table class="panchanga-week-table">
          <thead>
            <tr><th>日期</th><th>质量</th><th>活动</th><th>条件</th><th>标签</th><th>吉时窗口</th><th>Tithi</th><th>Nakshatra</th><th>Yoga</th><th>结束时间</th><th>日出/日落</th><th>Rahu Kala</th><th>Yamaganda</th><th>Gulika</th></tr>
          </thead>
          <tbody>
            ${rows.length ? rows.map(row => `
              <tr>
                <td>${escapeHtml(row.date)}</td>
                <td><strong>${escapeHtml(row.quality)}</strong><span>${formatPercent(row.score)}</span></td>
                <td><span class="${escapeAttr(getPanchangaActivityClass(row.activityVerdict))}">${escapeHtml(row.activityVerdict)}</span></td>
                <td>${renderPanchangaConditionBadges(row.conditionTags)}</td>
                <td>${renderVrataTagBadges(row.vrataTags)}</td>
                <td>${escapeHtml(row.subDaySummary)}</td>
                <td>${escapeHtml(row.tithi)}</td>
                <td>${escapeHtml(row.nakshatra)}</td>
                <td>${escapeHtml(row.yoga)}</td>
                <td>${escapeHtml(row.endSummary)}</td>
                <td>${escapeHtml(row.sunrise)}-${escapeHtml(row.sunset)}</td>
                <td>${escapeHtml(row.rahuKala)}</td>
                <td>${escapeHtml(row.yamaganda)}</td>
                <td>${escapeHtml(row.gulika)}</td>
              </tr>
            `).join('') : '<tr><td colspan="14">当前范围内没有匹配条件的日期。</td></tr>'}
          </tbody>
        </table>
      </div>
    `;
  } catch (error) {
    output.innerHTML = `<div class="panchanga-week-error">Panchanga 日历生成失败：${escapeHtml(error?.message || 'unknown error')}</div>`;
  }
}

function readPanchangaRangeInputs() {
  const today = new Date();
  const start = $('panchanga-start')?.value || toDateISO(today);
  const end = $('panchanga-end')?.value || toDateISO(addDays(today, 6));
  const payload = {
    start_date: start,
    end_date: end,
    sunrise: $('panchanga-sunrise')?.value || '06:00',
    sunset: $('panchanga-sunset')?.value || '18:00',
    hour_from_sunrise: 6,
  };
  const activity = $('panchanga-activity')?.value || 'all';
  if (activity !== 'all') payload.activity = activity;
  const conditions = getSelectedPanchangaConditions();
  payload.conditions = conditions;
  payload.condition = conditions[0] || 'all';
  payload.condition_mode = $('panchanga-condition-mode')?.value || 'all';
  const birth = chartData?.birth_info || chartData?.birth || {};
  const lat = Number(birth.lat);
  const lon = Number(birth.lon);
  const tz = Number(birth.tz);
  if (Number.isFinite(lat) && Number.isFinite(lon) && Number.isFinite(tz)) {
    payload.lat = lat;
    payload.lon = lon;
    payload.tz = tz;
  }
  return payload;
}

function normalizePanchangaRangeRows(days) {
  return days.map(day => {
    const p = day.panchanga || {};
    const summary = day.summary || {};
    const periods = day.inauspicious_periods || {};
    const solar = day.solar_times || {};
    const checks = day.activity_checks || {};
    const primaryCheck = Object.values(checks)[0] || null;
    const endTimes = day.end_times || {};
    const vrataTags = Array.isArray(day.vrata_tags) ? day.vrata_tags : [];
    const festivalDetails = Array.isArray(day.festival_details) ? day.festival_details : [];
    const conditionTags = Array.isArray(day.condition_tags) ? day.condition_tags : [];
    const choghadiya = day.choghadiya || {};
    const horaWindows = day.hora_windows || {};
    return {
      date: day.query_date || '-',
      quality: summary.overall_quality || p.overall_quality || '-',
      score: summary.overall_score ?? p.overall_score,
      tithi: p.tithi?.full_name || p.tithi?.name || '-',
      nakshatra: p.nakshatra?.nakshatra || p.nakshatra?.name || '-',
      yoga: p.yoga?.yoga || p.yoga?.name || '-',
      vara: p.vara?.vara || p.vara?.name || '-',
      sunrise: solar.sunrise || periods.sunrise || '-',
      sunset: solar.sunset || periods.sunset || '-',
      solarPolicy: solar.policy || '',
      endTimes,
      tithiEndsAt: endTimes.tithi?.ends_at || '',
      nakshatraEndsAt: endTimes.nakshatra?.ends_at || '',
      yogaEndsAt: endTimes.yoga?.ends_at || '',
      endSummary: formatEndTimeSummary(endTimes),
      vrataTags,
      festivalDetails,
      vrataLabels: vrataTags.map(tag => tag.label || tag.key).filter(Boolean).join(' / '),
      conditionTags,
      conditionLabels: conditionTags.map(tag => tag.label || tag.key).filter(Boolean).join(' / '),
      subDaySummary: formatSubDaySummary(choghadiya, horaWindows),
      choghadiya,
      horaWindows,
      activityVerdict: primaryCheck?.verdict || summarizeActivities(summary),
      activityNotes: Array.isArray(primaryCheck?.notes) ? primaryCheck.notes.join('; ') : '',
      rahuKala: formatWindow(periods.rahu_kala),
      yamaganda: formatWindow(periods.yamaganda),
      gulika: formatWindow(periods.gulika),
    };
  });
}

function renderPanchangaMonthGrid(grid) {
  if (!Array.isArray(grid) || !grid.length) return '';
  const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  return `
    <div class="panchanga-month-grid" aria-label="Panchanga month grid">
      ${weekdays.map(day => `<div class="panchanga-month-head">${escapeHtml(day)}</div>`).join('')}
      ${grid.flatMap(week => week.map(cell => {
        if (!cell) return '<div class="panchanga-month-cell is-empty"></div>';
        const best = Array.isArray(cell.best_activities) ? cell.best_activities.slice(0, 2).map(getPanchangaActivityLabel).join(' / ') : '';
        const tagLabels = Array.isArray(cell.vrata_tags) ? cell.vrata_tags.slice(0, 2).map(tag => tag.label || tag.key).filter(Boolean) : [];
        const bestChoghadiya = Array.isArray(cell.best_choghadiya) ? cell.best_choghadiya.slice(0, 2).map(item => `${item.name} ${item.start}`).join(' / ') : '';
        return `
          <div class="panchanga-month-cell">
            <div class="panchanga-month-date">
              <strong>${escapeHtml(String(cell.day || ''))}</strong>
              <span>${escapeHtml(formatPercent(cell.score))}</span>
            </div>
            <p>${escapeHtml(cell.tithi || '-')}</p>
            <small>${escapeHtml(cell.nakshatra || '-')}</small>
            ${cell.tithi_ends_at ? `<small>${escapeHtml(shortLocalDateTime(cell.tithi_ends_at))}</small>` : ''}
            ${tagLabels.length ? `<div class="panchanga-tag-row">${tagLabels.map(label => `<span>${escapeHtml(label)}</span>`).join('')}</div>` : ''}
            ${bestChoghadiya ? `<small>${escapeHtml(bestChoghadiya)}</small>` : ''}
            ${best ? `<em>${escapeHtml(best)}</em>` : ''}
          </div>
        `;
      })).join('')}
    </div>
  `;
}

function getPanchangaActivityLabel(value) {
  const found = PANCHANGA_ACTIVITIES.find(([key]) => key === value);
  return found ? found[1] : value || '全部活动';
}

function getPanchangaConditionLabel(value) {
  const found = PANCHANGA_CONDITIONS.find(([key]) => key === value);
  return found ? found[1] : value || '全部条件';
}

function getSelectedPanchangaConditions() {
  return Array.from(document.querySelectorAll('input[name="panchanga-condition-option"]:checked'))
    .map(input => input.value)
    .filter(Boolean);
}

function normalizePanchangaConditions(conditions) {
  const list = Array.isArray(conditions) ? conditions : [conditions];
  return [...new Set(list.filter(condition => condition && condition !== 'all'))];
}

function normalizePanchangaConditionMode(mode) {
  return mode === 'any' ? 'any' : 'all';
}

function getPanchangaConditionModeLabel(mode) {
  const normalized = normalizePanchangaConditionMode(mode);
  const found = PANCHANGA_CONDITION_MODES.find(([key]) => key === normalized);
  return found ? found[1] : '满足全部';
}

function getPanchangaConditionSelectionLabel(conditions, mode = 'all') {
  const selected = normalizePanchangaConditions(conditions);
  if (!selected.length) return getPanchangaConditionLabel('all');
  const joiner = normalizePanchangaConditionMode(mode) === 'any' ? ' / ' : ' + ';
  return `${getPanchangaConditionModeLabel(mode)}：${selected.map(getPanchangaConditionLabel).join(joiner)}`;
}

function renderPanchangaLocationSummary(location, sourceChart) {
  const birth = sourceChart?.birth_info || sourceChart?.birth || {};
  if (location?.lat != null && location?.lon != null) {
    const city = birth.city || birth.place || '';
    return `<small>地点：${escapeHtml(city ? `${city} · ` : '')}${escapeHtml(Number(location.lat).toFixed(3))}, ${escapeHtml(Number(location.lon).toFixed(3))} · TZ ${escapeHtml(location.tz)}</small>`;
  }
  return '<small>地点：手动日出/日落；未使用出生地坐标。</small>';
}

function renderPanchangaConditionGuide(conditions, mode = 'all', searchSummary = null) {
  const selected = normalizePanchangaConditions(conditions);
  const items = selected.length ? selected : ['all'];
  const counts = searchSummary?.condition_counts || {};
  return `
    <div class="panchanga-condition-guide">
      <div>
        <strong>${escapeHtml(getPanchangaConditionModeLabel(mode))}</strong>
        <span>${escapeHtml(selected.length ? `当前组合 ${selected.length} 个条件；同类 /panchanga/search 可按 tithi+nākṣatra+yoga+vara 或标签组合检索。` : '未选择条件，显示全部日期。')}</span>
      </div>
      ${items.map(key => `
        <div>
          <strong>${escapeHtml(getPanchangaConditionLabel(key))}${counts[key] ? ` · ${escapeHtml(String(counts[key]))}` : ''}</strong>
          <span>${escapeHtml(PANCHANGA_CONDITION_GUIDE[key] || '按当前 Panchanga 标签筛选。')}</span>
        </div>
      `).join('')}
    </div>
  `;
}

function renderPanchangaFestivalDetails(rows) {
  const details = [];
  rows.forEach(row => {
    (row.festivalDetails || []).forEach(detail => {
      details.push({ ...detail, date: row.date });
    });
  });
  if (!details.length) return '';
  return `
    <div class="panchanga-festival-details">
      ${details.slice(0, 6).map(detail => `
        <div class="panchanga-festival-card ${detail.requires_confirmation ? 'is-candidate' : ''}">
          <strong>${escapeHtml(detail.label || detail.key || '-')}</strong>
          <span>${escapeHtml(detail.date || '')} · ${escapeHtml(detail.type || 'observance')}</span>
          <p>${escapeHtml(detail.guidance || detail.confirmation_note || '')}</p>
          <small>${escapeHtml((detail.basis || []).join(' · '))}</small>
        </div>
      `).join('')}
    </div>
  `;
}

function filterPanchangaRowsByCondition(rows, condition, mode = 'all') {
  const selected = normalizePanchangaConditions(condition);
  if (!selected.length) return rows;
  const matcher = normalizePanchangaConditionMode(mode) === 'any'
    ? selected.some.bind(selected)
    : selected.every.bind(selected);
  return rows.filter(row => matcher(item => rowMatchesPanchangaCondition(row, item)));
}

function rowMatchesPanchangaCondition(row, condition) {
  const tags = Array.isArray(row?.conditionTags) ? row.conditionTags : [];
  if (tags.some(tag => tag.key === condition)) return true;
  if (condition === 'festival_candidate') {
    return (row?.vrataTags || []).some(tag => tag.type === 'festival_candidate');
  }
  if (condition === 'has_vrata') return Boolean((row?.vrataTags || []).length);
  if (condition === 'auspicious_activity') return /推荐|大吉|吉|Excellent|Good/.test(String(row?.activityVerdict || ''));
  if (condition === 'avoid_new_start') return /避开|不宜|Avoid|Poor/.test(String(row?.activityVerdict || ''));
  if (condition === 'good_choghadiya') {
    return ['day', 'night'].some(part => (row?.choghadiya?.[part] || []).some(item => item.quality === 'auspicious'));
  }
  if (condition === 'spiritual_practice') {
    return (row?.vrataTags || []).some(tag => ['fasting', 'observance', 'lunar', 'vrata'].includes(tag.type));
  }
  return false;
}

function summarizeActivities(summary) {
  const best = Array.isArray(summary?.best_activities) ? summary.best_activities : [];
  const avoid = Array.isArray(summary?.avoid_activities) ? summary.avoid_activities : [];
  if (avoid.length) return `避开 ${avoid.map(getPanchangaActivityLabel).slice(0, 2).join('/')}`;
  if (best.length) return `推荐 ${best.map(getPanchangaActivityLabel).slice(0, 2).join('/')}`;
  return '中性';
}

function getPanchangaActivityClass(verdict) {
  const text = String(verdict || '');
  if (/避开|不宜|Avoid|Poor/.test(text)) return 'panchanga-activity-badge is-bad';
  if (/推荐|大吉|吉|Excellent|Good/.test(text)) return 'panchanga-activity-badge is-good';
  return 'panchanga-activity-badge';
}

function formatEndTimeSummary(endTimes) {
  const parts = [];
  if (endTimes?.tithi?.ends_at) parts.push(`T ${shortLocalDateTime(endTimes.tithi.ends_at)}`);
  if (endTimes?.nakshatra?.ends_at) parts.push(`N ${shortLocalDateTime(endTimes.nakshatra.ends_at)}`);
  if (endTimes?.yoga?.ends_at) parts.push(`Y ${shortLocalDateTime(endTimes.yoga.ends_at)}`);
  return parts.join(' · ') || '-';
}

function shortLocalDateTime(value) {
  const text = String(value || '');
  return text.length >= 16 ? text.slice(5, 16) : text || '-';
}

function renderVrataTagBadges(tags) {
  if (!Array.isArray(tags) || !tags.length) return '-';
  return `<div class="panchanga-tag-row">${tags.slice(0, 3).map(tag => `<span>${escapeHtml(tag.label || tag.key || '-')}</span>`).join('')}</div>`;
}

function renderPanchangaConditionBadges(tags) {
  if (!Array.isArray(tags) || !tags.length) return '-';
  return `<div class="panchanga-condition-chip">${tags.slice(0, 3).map(tag => `<span>${escapeHtml(tag.label || tag.key || '-')}</span>`).join('')}</div>`;
}

function formatSubDaySummary(choghadiya, horaWindows) {
  const good = [
    ...(Array.isArray(choghadiya?.day) ? choghadiya.day : []),
    ...(Array.isArray(choghadiya?.night) ? choghadiya.night : []),
  ].filter(item => item.quality === 'auspicious').slice(0, 2);
  const hora = Array.isArray(horaWindows?.day) ? horaWindows.day[0] : null;
  const goodText = good.map(item => `${item.name} ${item.start}-${item.end}`).join(' · ');
  const horaText = hora ? `Hora ${hora.lord} ${hora.start}-${hora.end}` : '';
  return [goodText, horaText].filter(Boolean).join(' · ') || '-';
}

function formatWindow(period) {
  if (!period) return '-';
  return `${period.start || '-'}-${period.end || '-'}`;
}

function exportPanchangaRangeCSV(panel) {
  const rows = panel?._lastPanchangaRange?.rows || [];
  if (!rows.length) {
    renderPanchangaRange(panel);
    return;
  }
  const header = ['date', 'quality', 'score', 'activity_verdict', 'activity_notes', 'condition_tags', 'vrata_tags', 'sub_day_windows', 'tithi', 'tithi_ends_at', 'nakshatra', 'nakshatra_ends_at', 'yoga', 'yoga_ends_at', 'vara', 'sunrise', 'sunset', 'rahu_kala', 'yamaganda', 'gulika'];
  const csvRows = [header, ...rows.map(row => [
    row.date,
    row.quality,
    formatPercent(row.score),
    row.activityVerdict,
    row.activityNotes,
    row.conditionLabels,
    row.vrataLabels,
    row.subDaySummary,
    row.tithi,
    row.tithiEndsAt,
    row.nakshatra,
    row.nakshatraEndsAt,
    row.yoga,
    row.yogaEndsAt,
    row.vara,
    row.sunrise,
    row.sunset,
    row.rahuKala,
    row.yamaganda,
    row.gulika,
  ])];
  const csv = csvRows.map(cols => cols.map(escapeCsv).join(',')).join('\n');
  downloadText(csv, `panchanga-${rows[0].date || 'range'}-${rows[rows.length - 1].date || 'range'}.csv`, 'text/csv;charset=utf-8');
}

function exportPanchangaRangeICS(panel) {
  const rows = panel?._lastPanchangaRange?.rows || [];
  if (!rows.length) {
    renderPanchangaRange(panel);
    return;
  }
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Jyotish Web App//Panchanga//CN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
  ];
  rows.forEach((row, index) => {
    const uid = `panchanga-${row.date}-${index}@jyotish-web-app`;
    const start = row.date.replace(/-/g, '');
    const end = toDateISO(addDays(parseDateISO(row.date), 1)).replace(/-/g, '');
    const summary = `Panchanga ${row.quality}`;
    const description = [
      `Tithi: ${row.tithi}`,
      `Nakshatra: ${row.nakshatra}`,
      `Yoga: ${row.yoga}`,
      `Vara: ${row.vara}`,
      `Activity: ${row.activityVerdict}`,
      `Condition tags: ${row.conditionLabels || '-'}`,
      `Vrata tags: ${row.vrataLabels || '-'}`,
      `Sub-day windows: ${row.subDaySummary}`,
      `End times: ${row.endSummary}`,
      `Sunrise/Sunset: ${row.sunrise}-${row.sunset}`,
      `Rahu Kala: ${row.rahuKala}`,
      `Yamaganda: ${row.yamaganda}`,
      `Gulika: ${row.gulika}`,
    ].join('\\n');
    lines.push(
      'BEGIN:VEVENT',
      `UID:${escapeIcs(uid)}`,
      `DTSTAMP:${formatIcsTimestamp(new Date())}`,
      `DTSTART;VALUE=DATE:${start}`,
      `DTEND;VALUE=DATE:${end}`,
      `SUMMARY:${escapeIcs(summary)}`,
      `DESCRIPTION:${escapeIcs(description)}`,
      'END:VEVENT',
    );
  });
  lines.push('END:VCALENDAR');
  downloadText(lines.join('\r\n'), `panchanga-${rows[0].date || 'range'}-${rows[rows.length - 1].date || 'range'}.ics`, 'text/calendar;charset=utf-8');
}

function escapeIcs(value) {
  return String(value ?? '')
    .replace(/\\/g, '\\\\')
    .replace(/\n/g, '\\n')
    .replace(/,/g, '\\,')
    .replace(/;/g, '\\;');
}

function formatIcsTimestamp(date) {
  return date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
}

function escapeCsv(value) {
  const s = String(value ?? '');
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function downloadText(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function addDays(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

function parseDateISO(value) {
  const [year, month, day] = String(value).split('-').map(Number);
  return new Date(year, (month || 1) - 1, day || 1);
}

function toDateISO(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function formatPercent(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return '-';
  return `${Math.round(n * 100)}%`;
}

function buildPlanetSignIndex(planets) {
  const result = {};
  for (const [pn, p] of Object.entries(planets || {})) {
    if (!p || p.error) continue;
    const signIdx = SIGNS.indexOf(p.sign);
    if (signIdx >= 0) result[pn] = signIdx;
  }
  return result;
}

function renderSpecialLagnaReport(arudha, ascendant, birthInfo, specialLagnas) {
  const container = $('special-lagna-section');
  if (!container) return;
  if (!ascendant?.sign) {
    container.innerHTML = '';
    return;
  }
  const special = buildSpecialLagnaReport(arudha, ascendant, birthInfo, specialLagnas);
  const cards = special.cards.map(card => `
    <div class="special-lagna-card ${card.kind}">
      <span>${escapeHtml(card.code)}</span>
      <strong>${escapeHtml(card.title)}</strong>
      <div>${escapeHtml(card.sign)}</div>
      <p>${escapeHtml(card.meaning)}</p>
    </div>
  `).join('');
  container.innerHTML = `
    <section class="special-lagna-panel">
      <div class="special-lagna-head">
        <div>
          <h4>特殊 Lagna 专题</h4>
          <p>把 AL/UL/A10 的外显影像与 HL/GL/VL 的时间敏感辅助点放在同一张卡片里，作为完整解盘的身份、婚姻、事业、财富与权力观察入口。</p>
        </div>
        <span>${escapeHtml(special.ghatiLabel)}</span>
      </div>
      ${special.meta.length ? `<div class="special-lagna-meta">${special.meta.map(item => `<span>${escapeHtml(item)}</span>`).join('')}</div>` : ''}
      <div class="special-lagna-grid">${cards}</div>
      <p class="special-lagna-note">${escapeHtml(special.note)}</p>
    </section>
  `;
}

function buildSpecialLagnaReport(arudha, ascendant, birthInfo, specialLagnas) {
  const apiSpecial = normalizeSpecialLagnas(specialLagnas);
  if (apiSpecial) {
    const card = (code, title, sign, lord, meaning, kind = 'derived') => ({
      code,
      title,
      sign: sign ? `${signName(sign)} · 主星 ${planetName(lord || SIGN_LORDS[sign])}` : '暂缺',
      meaning,
      kind,
    });
    return {
      ghatiLabel: `Ghati ${apiSpecial.ghatis.toFixed(2)}`,
      meta: [
        apiSpecial.precision === 'sunrise_correct' ? '日出校正' : '后端计算',
        apiSpecial.sunriseLocal ? `日出 ${apiSpecial.sunriseLocal}` : '',
      ].filter(Boolean),
      note: apiSpecial.note || 'HL/GL 已按出生地日出起算；若出生时间不确定，请结合生时校正模块共同判断。',
      cards: [
        card('AL', 'Arudha Lagna 社会形象', arudha?.AL?.sign, arudha?.AL?.lord, '别人最容易看到的外在形象、名声与社会投射。', 'core'),
        card('UL', 'Upapada Lagna 婚姻外显', arudha?.UL?.sign, arudha?.UL?.lord, '伴侣关系在外界呈现出的样子，也用于观察婚姻持续性。', 'core'),
        card('A10', 'Karma Pada 事业形象', arudha?.A10?.sign, arudha?.A10?.lord, '职业名声、公众认可方式，以及事业成果如何被看见。', 'core'),
        card('HL', 'Hora Lagna 财富驱动', apiSpecial.HL?.sign, apiSpecial.HL?.lord, '财富获取方式、资源动机和物质层面的行动入口。'),
        card('GL', 'Ghati Lagna 权力行动', apiSpecial.GL?.sign, apiSpecial.GL?.lord, '行动效率、权力表达、竞争与事件触发敏感点。'),
        card('VL', 'Varnada Lagna 身份来源', apiSpecial.VL?.sign, apiSpecial.VL?.lord, '身份阶层、外在定位和人生舞台的来源感。'),
      ],
    };
  }

  const birth = window.__jyotishBirth || {};
  const time = birthInfo?.time || `${String(birth.hour ?? 12).padStart(2, '0')}:${String(birth.minute ?? 0).padStart(2, '0')}`;
  const [hourRaw, minuteRaw, secondRaw] = String(time).split(':');
  const hour = Number.isFinite(Number(hourRaw)) ? Number(hourRaw) : safeNumber(birth.hour, 12);
  const minute = Number.isFinite(Number(minuteRaw)) ? Number(minuteRaw) : safeNumber(birth.minute, 0);
  const second = Number.isFinite(Number(secondRaw)) ? Number(secondRaw) : safeNumber(birth.second, 0);
  const ascIdx = SIGNS.indexOf(ascendant.sign);
  const ghatis = ((hour + minute / 60 + second / 3600) / 24) * 60;
  const ghatiFloor = Math.floor(ghatis);
  const hlIdx = ghatiFloor % 2 ? ghatiFloor % 12 : (7 - ghatiFloor + 120) % 12;
  const glIdx = ghatiFloor % 12;
  const vlIdx = (ascIdx * 3) % 12;
  const card = (code, title, sign, lord, meaning, kind = 'derived') => ({
    code,
    title,
    sign: sign ? `${signName(sign)} · 主星 ${planetName(lord || SIGN_LORDS[sign])}` : '暂缺',
    meaning,
    kind,
  });
  return {
    ghatiLabel: `Ghati ${ghatis.toFixed(2)}`,
    meta: ['本地简化值'],
    note: '边界：HL/GL/VL 当前使用本地简化算法，按午夜起算 ghati；传统精算应使用出生地日出时间。因此它们作为辅助观察，不用于单独定论。',
    cards: [
      card('AL', 'Arudha Lagna 社会形象', arudha?.AL?.sign, arudha?.AL?.lord, '别人最容易看到的外在形象、名声与社会投射。', 'core'),
      card('UL', 'Upapada Lagna 婚姻外显', arudha?.UL?.sign, arudha?.UL?.lord, '伴侣关系在外界呈现出的样子，也用于观察婚姻持续性。', 'core'),
      card('A10', 'Karma Pada 事业形象', arudha?.A10?.sign, arudha?.A10?.lord, '职业名声、公众认可方式，以及事业成果如何被看见。', 'core'),
      card('HL', 'Hora Lagna 财富驱动', SIGNS[hlIdx], SIGN_LORDS[SIGNS[hlIdx]], '财富获取方式、资源动机和物质层面的行动入口。'),
      card('GL', 'Ghati Lagna 权力行动', SIGNS[glIdx], SIGN_LORDS[SIGNS[glIdx]], '行动效率、权力表达、竞争与事件触发敏感点。'),
      card('VL', 'Varnada Lagna 身份来源', SIGNS[vlIdx], SIGN_LORDS[SIGNS[vlIdx]], '身份阶层、外在定位和人生舞台的来源感。'),
    ],
  };
}

function normalizeSpecialLagnas(specialLagnas) {
  if (!specialLagnas || !specialLagnas.HL || !specialLagnas.GL || !specialLagnas.VL) return null;
  const ghatis = safeNumber(
    specialLagnas.ghatis_elapsed_from_sunrise ?? specialLagnas.HL?.ghatis_elapsed,
    NaN,
  );
  if (!Number.isFinite(ghatis)) return null;
  return {
    precision: specialLagnas.precision || specialLagnas.capability_status || '',
    sunriseLocal: specialLagnas.sunrise_local_time || '',
    ghatis,
    note: specialLagnas.note || '',
    HL: normalizeSpecialPoint(specialLagnas.HL),
    GL: normalizeSpecialPoint(specialLagnas.GL),
    VL: normalizeSpecialPoint(specialLagnas.VL),
  };
}

function normalizeSpecialPoint(point) {
  if (!point) return null;
  const sign = point.sign || SIGNS[point.sign_idx];
  return {
    sign,
    lord: point.lord || SIGN_LORDS[sign],
    degree: point.degree_in_sign ?? point.longitude,
  };
}

// ============================================================================
// D9 Navamsa 婚姻专题
// ============================================================================
function renderD9MarriageReport(allV, planets, ascendant, karaka) {
  const container = $('d9-marriage-section');
  if (!container) return;
  const report = buildD9MarriageReport(allV, planets, ascendant, karaka);
  if (!report) {
    container.innerHTML = `
      <div class="d9-panel">
        <div class="d9-empty">D9 婚姻专题需要完整出生时间和行星度数。请先生成可计算分盘的星盘。</div>
      </div>
    `;
    return;
  }

  const coreHtml = report.core.map(item => `
    <div class="d9-core-card">
      <span>${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(item.value)}</strong>
      <p>${escapeHtml(item.note)}</p>
    </div>
  `).join('');

  const flagHtml = report.flags.map(flag => `
    <div class="d9-flag d9-flag-${escapeAttr(flag.level)}">
      <div class="d9-flag-head">
        <strong>${escapeHtml(flag.name)}</strong>
        <span>${escapeHtml(flag.label)}</span>
      </div>
      <p>${escapeHtml(flag.detail)}</p>
    </div>
  `).join('');

  const evidenceHtml = report.evidence.map(item => `
    <li><strong>${escapeHtml(item.label)}：</strong>${escapeHtml(item.value)}</li>
  `).join('');

  container.innerHTML = `
    <div class="d9-panel">
      <div class="d9-panel-head">
        <div>
          <h4>D9 Navamsa 婚姻专题</h4>
          <p>基于 D9 上升、Darakaraka、Venus、D9 七宫、Vargottama 与 Pushkara 的八步旗标。</p>
        </div>
        <div class="d9-score d9-score-${escapeAttr(report.zone.key)}">
          <span>${escapeHtml(report.zone.name)}</span>
          <strong>${escapeHtml(report.score)} / 8</strong>
        </div>
      </div>
      <div class="d9-core-grid">${coreHtml}</div>
      <div class="d9-flags">${flagHtml}</div>
      <div class="d9-evidence">
        <div>
          <strong>关键证据</strong>
          <ul>${evidenceHtml}</ul>
        </div>
        <p>边界：D9 需要准确出生时间，且应与 D1、Dasha、Transit、现实关系模式一起判断；这里展示的是婚恋专题信号，不替代个人选择或专业咨询。</p>
      </div>
    </div>
  `;
}

function buildD9MarriageReport(allV, planets, ascendant, karaka) {
  if (!allV?.D9?.planets || !planets || !ascendant?.sign) return null;
  const ascSign = getD9AscSign(ascendant);
  if (!ascSign) return null;
  const ascIdx = SIGNS.indexOf(ascSign);
  const d9Planets = buildD9PlanetPositions(allV.D9.planets, planets, ascIdx);
  const d9AscLord = SIGN_LORDS[ascSign];
  const d9AscLordPos = d9Planets[d9AscLord];
  const dkPlanet = karaka?.karaka7?.DK?.planet || karaka?.karaka8?.DK?.planet;
  const dkPos = dkPlanet ? d9Planets[dkPlanet] : null;
  const venusPos = d9Planets.Venus;
  const seventhSign = SIGNS[(ascIdx + 6) % 12];
  const seventhLord = SIGN_LORDS[seventhSign];
  const seventhLordPos = d9Planets[seventhLord];
  const seventhPlanets = Object.entries(d9Planets).filter(([, p]) => p.house === 7).map(([pn]) => pn);
  const vargottama = Object.entries(d9Planets)
    .filter(([pn, p]) => planets[pn]?.sign && planets[pn].sign === p.sign)
    .map(([pn]) => pn);
  const pushkara = Object.entries(planets)
    .filter(([pn, p]) => d9Planets[pn] && isPushkaraNavamsa(p))
    .map(([pn]) => pn);

  const flags = [
    evaluateAscLordFlag(d9AscLord, d9AscLordPos),
    evaluateDKFlag(dkPlanet, dkPos),
    evaluatePlanetDignityFlag('Venus', venusPos, 'Venus在D9尊严'),
    evaluateSeventhLordFlag(seventhLord, seventhLordPos),
    evaluateDKVenusFlag(dkPlanet, dkPos, venusPos),
    evaluateSeventhMaleficsFlag(seventhPlanets),
    evaluateVargottamaFlag(vargottama, dkPlanet),
    evaluatePushkaraFlag(pushkara, dkPlanet, seventhLord),
  ];
  const score = flags.reduce((sum, flag) => sum + flag.score, 0);
  const positiveCount = flags.filter(flag => flag.score > 0).length;
  const zone = d9Zone(score);

  return {
    score: `${score >= 0 ? '+' : ''}${score}`,
    zone,
    flags,
    core: [
      { label: 'D9上升', value: signName(ascSign), note: `${planetName(d9AscLord)}主导婚姻成熟后的运作气质` },
      { label: 'DK配偶征象', value: dkPlanet ? `${planetName(dkPlanet)} · ${formatD9Pos(dkPos)}` : '未取得DK', note: 'Darakaraka 描述配偶/亲密关系触发点' },
      { label: 'Venus关系品质', value: venusPos ? formatD9Pos(venusPos) : '缺少Venus', note: 'Venus 代表关系审美、亲密体验与和合力' },
      { label: 'D9七宫', value: `${signName(seventhSign)} · 主星 ${planetName(seventhLord)}`, note: seventhPlanets.length ? `七宫行星：${seventhPlanets.map(planetName).join('、')}` : '七宫无行星，重点看七宫主' },
    ],
    evidence: [
      { label: 'D9上升主星', value: `${planetName(d9AscLord)} ${formatD9Pos(d9AscLordPos)}` },
      { label: 'D9七宫主', value: `${planetName(seventhLord)} ${formatD9Pos(seventhLordPos)}` },
      { label: 'D9七宫行星', value: seventhPlanets.length ? seventhPlanets.map(planetName).join('、') : '无' },
      { label: 'Vargottama', value: vargottama.length ? vargottama.map(planetName).join('、') : '无' },
      { label: 'Pushkara Navamsa', value: pushkara.length ? pushkara.map(planetName).join('、') : '无' },
      { label: '旗标概览', value: `${positiveCount} 个绿旗，${flags.filter(flag => flag.score < 0).length} 个红旗` },
    ],
  };
}

function buildD9PlanetPositions(d9Planets, natalPlanets, ascIdx) {
  const result = {};
  for (const [pn, p] of Object.entries(d9Planets || {})) {
    if (!p?.sign) continue;
    const signIdx = SIGNS.indexOf(p.sign);
    if (signIdx < 0) continue;
    result[pn] = {
      sign: p.sign,
      house: ((signIdx - ascIdx + 12) % 12) + 1,
      dignity: planetDignity(pn, p.sign),
      natal: natalPlanets[pn] || {},
    };
  }
  return result;
}

function getD9AscSign(ascendant) {
  const si = SIGNS.indexOf(ascendant?.sign);
  if (si < 0) return null;
  const raw = safeNumber(ascendant.degree_in_sign ?? ascendant.degree);
  const degInSign = raw >= 30 ? ((raw % 30) + 30) % 30 : raw;
  const seg = Math.min(8, Math.floor(degInSign / (30 / 9)));
  const elementStart = [0, 9, 6, 3];
  return SIGNS[(elementStart[si % 4] + seg) % 12];
}

function planetDignity(planet, sign) {
  const data = PLANET_DIGNITY[planet] || NODE_DIGNITY[planet];
  if (!data || !sign) return { key: 'neutral', label: '中性' };
  if (data.debilitation?.sign === sign) return { key: 'debilitated', label: '落陷' };
  if (data.exaltation?.sign === sign) return { key: 'exalted', label: '旺相' };
  if (data.ownSigns?.includes(sign)) return { key: 'own', label: '入庙' };
  if (data.friends?.some(friend => SIGN_LORDS[sign] === friend)) return { key: 'friend', label: '友星座' };
  if (data.enemies?.some(enemy => SIGN_LORDS[sign] === enemy)) return { key: 'enemy', label: '敌星座' };
  return { key: 'neutral', label: '中性' };
}

function d9Flag(level, name, detail) {
  return {
    level,
    name,
    detail,
    score: level === 'green' ? 1 : level === 'red' ? -1 : 0,
    label: level === 'green' ? '绿旗' : level === 'red' ? '红旗' : '黄旗',
  };
}

function evaluateAscLordFlag(planet, pos) {
  if (!planet || !pos) return d9Flag('yellow', 'D9上升主星状态', '缺少上升主星位置，暂按中性处理。');
  if (['exalted', 'own', 'friend'].includes(pos.dignity.key) || D9_GREEN_HOUSES.includes(pos.house)) {
    return d9Flag('green', 'D9上升主星状态', `${planetName(planet)}在${formatD9Pos(pos)}，婚姻成熟后的自我调适力较好。`);
  }
  if (pos.dignity.key === 'debilitated' || pos.dignity.key === 'enemy' || D9_HARD_HOUSES.includes(pos.house)) {
    return d9Flag('red', 'D9上升主星状态', `${planetName(planet)}在${formatD9Pos(pos)}，亲密关系中需要更有意识地修复自我防御。`);
  }
  return d9Flag('yellow', 'D9上升主星状态', `${planetName(planet)}在${formatD9Pos(pos)}，信号中性，需结合D1与Dasha。`);
}

function evaluateDKFlag(planet, pos) {
  if (!planet || !pos) return d9Flag('yellow', 'DK在D9位置', '缺少DK位置，暂按中性处理。');
  if ([1, 3, 4, 5, 7, 9, 10].includes(pos.house)) {
    return d9Flag('green', 'DK在D9位置', `${planetName(planet)}落${formatD9Pos(pos)}，配偶征象容易进入关系主轴。`);
  }
  if ([8, 12].includes(pos.house)) {
    return d9Flag('red', 'DK在D9位置', `${planetName(planet)}落${formatD9Pos(pos)}，关系可能触发深层转化、距离感或隐性议题。`);
  }
  if ([6, 11].includes(pos.house)) {
    return d9Flag('yellow', 'DK在D9位置', `${planetName(planet)}落${formatD9Pos(pos)}，关系议题偏现实协作或期待管理。`);
  }
  return d9Flag('yellow', 'DK在D9位置', `${planetName(planet)}落${formatD9Pos(pos)}，需与Venus和七宫主交叉判断。`);
}

function evaluatePlanetDignityFlag(planet, pos, name) {
  if (!pos) return d9Flag('yellow', name, `缺少${planetName(planet)}位置，暂按中性处理。`);
  if (['exalted', 'own', 'friend'].includes(pos.dignity.key)) {
    return d9Flag('green', name, `${planetName(planet)}在${formatD9Pos(pos)}，关系品质有稳定支撑。`);
  }
  if (['debilitated', 'enemy'].includes(pos.dignity.key)) {
    return d9Flag('red', name, `${planetName(planet)}在${formatD9Pos(pos)}，亲密表达和价值交换需要主动经营。`);
  }
  return d9Flag('yellow', name, `${planetName(planet)}在${formatD9Pos(pos)}，关系品质信号中性。`);
}

function evaluateSeventhLordFlag(planet, pos) {
  if (!planet || !pos) return d9Flag('yellow', 'D9七宫主位置', '缺少D9七宫主位置，暂按中性处理。');
  if (['exalted', 'own', 'friend'].includes(pos.dignity.key) || [1, 4, 5, 7, 9, 10].includes(pos.house)) {
    return d9Flag('green', 'D9七宫主位置', `${planetName(planet)}在${formatD9Pos(pos)}，婚姻运作模式较容易成形。`);
  }
  if (pos.dignity.key === 'debilitated' || [8, 12].includes(pos.house)) {
    return d9Flag('red', 'D9七宫主位置', `${planetName(planet)}在${formatD9Pos(pos)}，伴侣协作与长期承诺需要更清晰规则。`);
  }
  return d9Flag('yellow', 'D9七宫主位置', `${planetName(planet)}在${formatD9Pos(pos)}，婚姻运作信号中等。`);
}

function evaluateDKVenusFlag(dkPlanet, dkPos, venusPos) {
  if (!dkPlanet || !dkPos || !venusPos) return d9Flag('yellow', 'DK-Venus关系', '缺少DK或Venus，暂按中性处理。');
  const distance = signDistance(dkPos.sign, venusPos.sign);
  if (distance === 1 || distance === 5 || distance === 7 || distance === 9 || dkPos.sign === venusPos.sign) {
    return d9Flag('green', 'DK-Venus关系', `DK ${planetName(dkPlanet)}与Venus形成同宫/吉性距离，配偶征象与关系品质较能互相接住。`);
  }
  if ([6, 8, 12].includes(distance)) {
    return d9Flag('red', 'DK-Venus关系', `DK ${planetName(dkPlanet)}与Venus呈${distance}位关系，吸引力与相处方式可能需要磨合。`);
  }
  return d9Flag('yellow', 'DK-Venus关系', `DK ${planetName(dkPlanet)}与Venus无明显强连接，需看Dasha触发。`);
}

function evaluateSeventhMaleficsFlag(seventhPlanets) {
  const malefics = seventhPlanets.filter(pn => D9_MALEFICS.includes(pn));
  if (malefics.length === 0) return d9Flag('green', 'D9七宫凶星压力', 'D9七宫无自然凶星占据，关系场域压力较轻。');
  if (malefics.length === 1) return d9Flag('yellow', 'D9七宫凶星压力', `D9七宫有${planetName(malefics[0])}，关系需要管理节奏和边界。`);
  return d9Flag('red', 'D9七宫凶星压力', `D9七宫有${malefics.map(planetName).join('、')}，冲突/压力信号较集中。`);
}

function evaluateVargottamaFlag(vargottama, dkPlanet) {
  if (dkPlanet && vargottama.includes(dkPlanet)) return d9Flag('green', 'Vargottama检查', `DK ${planetName(dkPlanet)}为Vargottama，配偶征象跨D1/D9一致。`);
  if (vargottama.includes('Venus')) return d9Flag('green', 'Vargottama检查', 'Venus为Vargottama，关系品质主题较稳定。');
  if (vargottama.length) return d9Flag('yellow', 'Vargottama检查', `${vargottama.map(planetName).join('、')}为Vargottama，可作为辅助稳定信号。`);
  return d9Flag('red', 'Vargottama检查', '未见Vargottama行星，D1/D9之间需要更多交叉验证。');
}

function evaluatePushkaraFlag(pushkara, dkPlanet, seventhLord) {
  if ((dkPlanet && pushkara.includes(dkPlanet)) || pushkara.includes('Venus')) {
    const hits = pushkara.filter(pn => pn === dkPlanet || pn === 'Venus').map(planetName).join('、');
    return d9Flag('green', 'Pushkara检查', `${hits}落Pushkara Navamsa，婚恋主题有额外缓冲与祝福信号。`);
  }
  if (seventhLord && pushkara.includes(seventhLord)) {
    return d9Flag('yellow', 'Pushkara检查', `D9七宫主${planetName(seventhLord)}落Pushkara，可缓和婚姻运作压力。`);
  }
  return d9Flag('red', 'Pushkara检查', 'DK、Venus、D9七宫主未落Pushkara，需要依赖其他强项补足。');
}

function isPushkaraNavamsa(planet) {
  const sign = planet?.sign;
  const deg = safeNumber(planet?.degree_in_sign ?? planet?.degree, NaN);
  if (!sign || !Number.isFinite(deg)) return false;
  const si = SIGNS.indexOf(sign);
  const element = si % 4;
  if (element === 0) return deg >= 20 && deg < 23 + (20 / 60);
  if (element === 1) return deg >= 13 + (20 / 60) && deg < 16 + (40 / 60);
  if (element === 2) return deg >= 6 + (40 / 60) && deg < 10;
  return deg >= 26 + (40 / 60) && deg < 30;
}

function signDistance(fromSign, toSign) {
  const from = SIGNS.indexOf(fromSign);
  const to = SIGNS.indexOf(toSign);
  if (from < 0 || to < 0) return 0;
  return ((to - from + 12) % 12) + 1;
}

function formatD9Pos(pos) {
  if (!pos) return '-';
  return `${signName(pos.sign)} · ${houseLabel(pos.house)} · ${pos.dignity.label}`;
}

function d9Zone(score) {
  if (score >= 5) return { key: 'green', name: 'Green Zone' };
  if (score >= 3) return { key: 'yellow', name: 'Yellow Zone' };
  if (score >= 1) return { key: 'orange', name: 'Orange Zone' };
  return { key: 'red', name: 'Red Zone' };
}

// ============================================================================
// Dasha 系统总览
// ============================================================================
function parseDashaDate(value) {
  if (!value) return null;
  const text = String(value).slice(0, 10);
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (match) return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatDashaDate(value) {
  const date = parseDashaDate(value);
  if (!date) return value || '-';
  return dashaDateToString(date);
}

function dashaDateToString(date) {
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${date.getFullYear()}-${mm}-${dd}`;
}

function formatDashaLord(lord) {
  const value = String(lord || '').trim();
  if (!value) return '-';
  const houseMatch = value.match(/^House\s+(\d+)\s+\(([^)]+)\)$/i);
  if (houseMatch) return `${houseMatch[1]}宫 (${signName(houseMatch[2])})`;
  if (PLANET_CN[value] || PLANET_SYMBOLS[value]) return planetName(value);
  if (SIGNS.includes(value)) return signName(value);
  return value;
}

function formatDashaYears(value) {
  if (value == null || value === '') return '-';
  const num = Number(value);
  return Number.isFinite(num) ? `${num}年` : `${value}年`;
}

function dashaPrecisionLabel(precision) {
  if (precision === 'calculator') return '专用算法';
  if (precision === 'generic') return '通用序列';
  return 'API时间线';
}

function dashaPrecisionNote(precision) {
  if (precision === 'generic') return '当前使用通用序列展开，适合趋势参考；古典细则仍需继续校准。';
  if (precision === 'calculator') return '当前系统已调用专用计算器，适合与本命、Transit、分盘交叉验证。';
  return '当前系统由本地 API 服务返回时间线。';
}

function addDashaDays(date, days) {
  return new Date(date.getTime() + days * 86400000);
}

function getDashaPeriodDays(period) {
  const start = parseDashaDate(period.start);
  const end = parseDashaDate(period.end);
  if (start && end && end > start) return (end.getTime() - start.getTime()) / 86400000;
  const years = Number(period.years);
  return Number.isFinite(years) && years > 0 ? years * 365.25636 : 0;
}

function extendDashaPeriodsForToday(rawPeriods) {
  const base = (Array.isArray(rawPeriods) ? rawPeriods : [])
    .filter(period => period && period.start && period.end)
    .map(period => ({ ...period, cycle_index: period.cycle_index || 0 }));
  if (!base.length) return Array.isArray(rawPeriods) ? rawPeriods : [];

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const lastEnd = parseDashaDate(base[base.length - 1].end);
  if (!lastEnd || today < lastEnd) return base;

  const extended = [...base];
  let cursor = lastEnd;
  let cycleIndex = 1;
  let includeOneAfterCurrent = false;

  while (cursor && cycleIndex <= 5) {
    for (const period of base) {
      const days = getDashaPeriodDays(period);
      if (!days) return extended;
      const start = cursor;
      const end = addDashaDays(start, days);
      extended.push({
        ...period,
        start: dashaDateToString(start),
        end: dashaDateToString(end),
        cycle_index: cycleIndex,
        repeated_cycle: true,
      });
      cursor = end;
      if (includeOneAfterCurrent) return extended;
      if (today >= start && today < end) includeOneAfterCurrent = true;
    }
    cycleIndex += 1;
  }

  return extended;
}

function getDashaTimelineState(periods) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const enriched = periods.map((period, index) => ({
    ...period,
    _index: index,
    _startDate: parseDashaDate(period.start),
    _endDate: parseDashaDate(period.end),
  }));
  const current = enriched.find(period => (
    period._startDate && period._endDate && today >= period._startDate && today < period._endDate
  ));
  const next = current
    ? enriched.find(period => period._index > current._index && period._startDate)
    : enriched.find(period => period._startDate && today < period._startDate);
  let progress = 0;
  if (current?._startDate && current?._endDate) {
    const total = current._endDate.getTime() - current._startDate.getTime();
    const elapsed = today.getTime() - current._startDate.getTime();
    progress = total > 0 ? Math.max(0, Math.min(100, Math.round((elapsed / total) * 100))) : 0;
  }
  return { periods: enriched, current, next, progress };
}

function renderDashaSystemOverview(chartData) {
  const container = $('dasha-system-section');
  if (!container) return;
  const dashas = chartData?.available_dashas || chartData?._extended?.available_dashas || [];
  if (!dashas.length) {
    container.innerHTML = `
      <div class="dasha-system-panel">
        <div class="dasha-system-empty">
          <strong>当前为本地 JS 计算模式</strong>
          <p>已展示 Vimshottari 三级大运。启动本地 API 服务后可查看完整 Dasha 系统清单。</p>
        </div>
      </div>
    `;
    return;
  }

  const grouped = dashas.reduce((acc, d) => {
    const type = d.type || 'other';
    if (!acc[type]) acc[type] = [];
    acc[type].push(d);
    return acc;
  }, {});
  const typeLabels = {
    nakshatra: 'Nakshatra',
    rasi: 'Rashi',
    conditional: '条件',
    varga: 'Varga',
    bhav: 'Bhava',
    special: 'Special',
    other: 'Other',
  };
  const typeButtons = `
    <button class="dasha-type-btn active" data-dasha-type="all">
      全部 <span>${dashas.length}</span>
    </button>
  ` + Object.entries(grouped).map(([type, items]) => `
    <button class="dasha-type-btn" data-dasha-type="${escapeAttr(type)}">
      ${escapeHtml(typeLabels[type] || type)} <span>${items.length}</span>
    </button>
  `).join('');
  const cards = dashas.map((d, index) => `
    <button class="dasha-system-card${index === 0 ? ' selected' : ''}" data-dasha-type="${escapeAttr(d.type || 'other')}" data-dasha-key="${escapeAttr(d.key || d.name || '')}">
      <strong>${escapeHtml(d.name || d.key || 'Dasha')}</strong>
      <span>${escapeHtml(typeLabels[d.type] || d.type || 'Other')} · ${escapeHtml(d.years ?? '-')}年</span>
    </button>
  `).join('');
  container.innerHTML = `
    <div class="dasha-system-panel">
      <div class="dasha-system-head">
        <div>
          <h4>多 Dasha 系统</h4>
          <p>当前 API 返回 ${dashas.length} 种 Dasha。选择任一系统即可查看主周期时间线、当前周期、下一周期与计算精度提示。</p>
        </div>
        <div class="dasha-system-count">${dashas.length}</div>
      </div>
      <div class="dasha-type-filter">${typeButtons}</div>
      <div class="dasha-system-layout">
        <div class="dasha-system-list">${cards}</div>
        <div class="dasha-system-detail" id="dasha-system-detail"></div>
      </div>
    </div>
  `;
  bindDashaSystemOverview(dashas, typeLabels, chartData);
}

function bindDashaSystemOverview(dashas, typeLabels, sourceChart) {
  const detail = $('dasha-system-detail');
  const list = document.querySelector('.dasha-system-list');
  const filters = document.querySelectorAll('.dasha-type-btn');
  if (!detail || !list) return;

  let requestSeq = 0;
  const birth = window.__jyotishBirth || {};

  const renderTimeline = (result) => {
    const rawPeriods = extendDashaPeriodsForToday(result?.periods);
    const timeline = getDashaTimelineState(rawPeriods);
    const periods = timeline.periods;
    const precisionLabel = dashaPrecisionLabel(result?.precision);
    const current = timeline.current;
    const next = timeline.next;
    const analysisHtml = renderVimshottariAnalysisBlock(result?.vimshottari_analysis);
    const summaryHtml = `
      <div class="dasha-system-summary">
        <div class="dasha-system-now${current ? '' : ' muted'}">
          <div class="dasha-system-kicker">当前周期</div>
          <strong>${escapeHtml(current ? formatDashaLord(current.lord) : '未落入已返回周期')}</strong>
          <p>${escapeHtml(current ? `${formatDashaDate(current.start)} ~ ${formatDashaDate(current.end)} · ${formatDashaYears(current.years)}` : '当前日期不在该系统已返回的时间线内。')}</p>
          ${current ? `<div class="dasha-system-progress" aria-label="当前周期进度 ${timeline.progress}%"><i style="width:${escapeAttr(timeline.progress)}%"></i></div>` : ''}
        </div>
        <div class="dasha-system-next${next ? '' : ' muted'}">
          <div class="dasha-system-kicker">下一周期</div>
          <strong>${escapeHtml(next ? formatDashaLord(next.lord) : '暂无后续周期')}</strong>
          <p>${escapeHtml(next ? `${formatDashaDate(next.start)} ~ ${formatDashaDate(next.end)} · ${formatDashaYears(next.years)}` : 'API 当前没有返回更靠后的周期。')}</p>
        </div>
      </div>
    `;
    const periodRows = periods.map(period => `
      <div class="dasha-system-period${current?._index === period._index ? ' current' : ''}${next?._index === period._index ? ' upcoming' : ''}">
        <strong>${escapeHtml(formatDashaLord(period.lord))}${current?._index === period._index ? '<small>当前</small>' : ''}${next?._index === period._index ? '<small>下一段</small>' : ''}${period.cycle_index ? `<small>第${escapeHtml(period.cycle_index + 1)}轮</small>` : ''}</strong>
        <span>${escapeHtml(formatDashaDate(period.start))} ~ ${escapeHtml(formatDashaDate(period.end))}</span>
        <em>${escapeHtml(formatDashaYears(period.years))}</em>
      </div>
    `).join('');
    detail.innerHTML = `
      <div class="dasha-system-detail-card">
        <div class="dasha-system-meta">${escapeHtml(typeLabels[result?.type] || result?.type || 'Other')} · ${escapeHtml(precisionLabel)}</div>
        <strong>${escapeHtml(result?.name || result?.key || 'Dasha')}</strong>
        <p>周期：${escapeHtml(result?.cycle_years ?? '-')} 年。${escapeHtml(dashaPrecisionNote(result?.precision))}</p>
        ${summaryHtml}
        ${analysisHtml}
        <div class="dasha-system-periods">${periodRows || '<p>暂无可显示周期。</p>'}</div>
      </div>
    `;
  };

  const showDetail = async (key) => {
    const item = dashas.find(d => (d.key || d.name) === key) || dashas[0];
    if (!item) return;
    const activeSeq = ++requestSeq;
    detail.innerHTML = `
      <div class="dasha-system-detail-card">
        <div class="dasha-system-meta">${escapeHtml(typeLabels[item.type] || item.type || 'Other')}</div>
        <strong>${escapeHtml(item.name || item.key || 'Dasha')}</strong>
        <p>正在从本地 API 服务读取该 Dasha 的时间线...</p>
      </div>
    `;
    try {
      const result = await window.JyotishAPI?.computeDashaSystem?.({
        ...birth,
        dasha: item.key,
        planets: sourceChart?.planets || {},
        ascendant: sourceChart?.ascendant || {},
      });
      if (!result || result.success === false) {
        throw new Error(result?.error || 'Dasha API 未返回有效时间线');
      }
      if (activeSeq !== requestSeq) return;
      renderTimeline(result);
    } catch (err) {
      if (activeSeq !== requestSeq) return;
      detail.innerHTML = `
        <div class="dasha-system-detail-card">
          <div class="dasha-system-meta">${escapeHtml(typeLabels[item.type] || item.type || 'Other')}</div>
          <strong>${escapeHtml(item.name || item.key || 'Dasha')}</strong>
          <p>周期：${escapeHtml(item.years ?? '-')} 年。当前未能连接单系统时间线接口：${escapeHtml(err?.message || '本地 API 服务不可用')}。</p>
        </div>
      `;
    }
  };

  list.querySelectorAll('.dasha-system-card').forEach(card => {
    card.addEventListener('click', () => {
      list.querySelectorAll('.dasha-system-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      showDetail(card.dataset.dashaKey);
    });
  });
  filters.forEach(btn => {
    btn.addEventListener('click', () => {
      filters.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const type = btn.dataset.dashaType;
      let firstVisible = null;
      list.querySelectorAll('.dasha-system-card').forEach(card => {
        const visible = type === 'all' || card.dataset.dashaType === type;
        card.hidden = !visible;
        card.classList.remove('selected');
        if (visible && !firstVisible) firstVisible = card;
      });
      if (firstVisible) {
        firstVisible.classList.add('selected');
        showDetail(firstVisible.dataset.dashaKey);
      }
    });
  });
  const first = list.querySelector('.dasha-system-card');
  if (first) showDetail(first.dataset.dashaKey);
}

function renderVimshottariAnalysisBlock(analysis) {
  if (!analysis || !analysis.current) return '';
  const md = analysis.current.mahadasha || {};
  const ad = analysis.current.antardasha || {};
  const levels = analysis.five_levels || {};
  const levelLine = ['mahadasha', 'bhukti', 'pratyantar', 'sookshma', 'prana']
    .map(key => levels[key]?.lord)
    .filter(Boolean)
    .join(' / ');
  const keywords = (analysis.current.keywords || []).slice(0, 4);
  return `
    <div class="dasha-analysis-block">
      <div class="dasha-analysis-head">
        <span>${escapeHtml(analysis.nakshatra?.name || 'Vimshottari')}</span>
        <strong>${escapeHtml(analysis.summary?.headline || `${md.lord || '-'} / ${ad.lord || '-'}`)}</strong>
      </div>
      <div class="dasha-analysis-grid">
        <div><span>Mahadasha</span><strong>${escapeHtml(formatDashaLord(md.lord || '-'))}</strong><p>${escapeHtml(formatDashaDate(md.start))} ~ ${escapeHtml(formatDashaDate(md.end))}</p></div>
        <div><span>Antardasha</span><strong>${escapeHtml(formatDashaLord(ad.lord || '-'))}</strong><p>剩余约 ${escapeHtml(analysis.current.remaining_days ?? '-')} 天</p></div>
        <div><span>五级层级</span><strong>${escapeHtml(levelLine || '-')}</strong><p>${escapeHtml(analysis.current.theme || '以运限作为时间主轴')}</p></div>
      </div>
      <div class="dasha-analysis-tags">
        ${keywords.map(item => `<span>${escapeHtml(item)}</span>`).join('')}
        <span>${escapeHtml(analysis.source || 'dasha_analyzer.py')}</span>
      </div>
    </div>
  `;
}

// ============================================================================
// Remedies Tab 渲染
// ============================================================================
function renderRemediesTab(chartData) {
  const sec = document.getElementById('remedies-section');
  if (!sec) return;
  const remedies = chartData?.remedies || chartData?._extended?.remedies;
  if (!remedies) {
    sec.innerHTML = `
      <div class="remedies-empty">
        <strong>补救建议暂不可用</strong>
        <p>启动本地 API 服务并重新排盘后，可根据 Shadbala、当前 Dasha 与 Dosha 自动生成补救计划。</p>
      </div>
    `;
    return;
  }
  const recommendations = remedies.recommendations || {};
  const gems = recommendations.gems || [];
  const mantras = recommendations.mantras || [];
  const donations = recommendations.donations || [];
  const fasting = recommendations.fasting || [];
  const lifestyle = recommendations.lifestyle || [];
  const doshaRemedies = recommendations.dosha_remedies || [];
  const weakPlanets = remedies.weak_planets || [];
  const moderatePlanets = remedies.moderate_planets || [];
  const primaryMantra = mantras[0];
  const primaryDonation = donations[0];
  const primaryLifestyle = lifestyle[0];
  const totalActions = gems.length + mantras.length + donations.length + fasting.length + lifestyle.length + doshaRemedies.length;

  const renderActionCards = (items, mapper) => items.map(item => {
    const mapped = mapper(item);
    return `
      <div class="remedy-action-card remedy-${escapeAttr(mapped.kind)}">
        <span>${escapeHtml(mapped.label)}</span>
        <strong>${escapeHtml(mapped.title)}</strong>
        <p>${escapeHtml(mapped.body)}</p>
        ${mapped.meta ? `<small>${escapeHtml(mapped.meta)}</small>` : ''}
      </div>
    `;
  }).join('');

  const gemstoneCards = renderActionCards(gems.slice(0, 3), g => ({
    kind: 'gem',
    label: '谨慎',
    title: `${g.planet || ''} · ${g.gem || ''}`,
    body: g.note || '宝石类补救需要结合完整星盘、体质和预算复核。',
    meta: [g.metal, g.finger, g.day].filter(Boolean).join(' · '),
  }));
  const mantraCards = renderActionCards(mantras.slice(0, 4), m => ({
    kind: 'mantra',
    label: '低风险',
    title: m.mantra || m.planet || 'Mantra',
    body: m.note || `每日念诵 ${m.repetitions || 27} 遍`,
    meta: m.priority === 'dasha_lord' ? '当前 Dasha 主星优先' : `${m.repetitions || '-'} 遍`,
  }));
  const donationCards = renderActionCards(donations.slice(0, 3), d => ({
    kind: 'donation',
    label: '行动',
    title: d.planet || 'Dana 捐赠',
    body: d.note || '选择能力范围内的小额、持续、真实善行。',
    meta: Array.isArray(d.items) ? d.items.slice(0, 3).join(' · ') : '',
  }));
  const fastingCards = renderActionCards(fasting.slice(0, 2), f => ({
    kind: 'fasting',
    label: '需评估',
    title: `${f.planet || ''} 斋戒`,
    body: f.note || '有低血糖、慢病、孕期或饮食限制者不要自行断食。',
    meta: f.day || '',
  }));
  const doshaCards = renderActionCards(doshaRemedies.slice(0, 3), d => ({
    kind: 'dosha',
    label: '专项',
    title: d.dosha || 'Dosha',
    body: d.note || '专项补救需结合完整星盘和现实背景判断。',
    meta: Array.isArray(d.actions) ? d.actions.slice(0, 2).join(' · ') : '',
  }));

  const firstWeek = [
    primaryMantra ? `每天固定一个安静时段，念诵 ${primaryMantra.mantra || primaryMantra.planet} ${primaryMantra.repetitions || 27} 遍。` : '每天记录一次情绪、睡眠与精力变化，先观察一周。',
    primaryDonation ? `选择一天做一次小额捐赠或服务：${primaryDonation.note || primaryDonation.planet || '按能力行善'}。` : '做一件可验证的小善行，保持简单、可持续。',
    primaryLifestyle ? primaryLifestyle.note : '避免一次性购买高价宝石，先执行低风险补救。',
  ];
  const evidenceCards = (remedies.evidence_chain || []).slice(0, 6).map(item => `
    <div class="remedies-evidence-card">
      <span>${escapeHtml(item.source || 'evidence')}</span>
      <strong>${escapeHtml(item.planet || item.dosha || '规则命中')}</strong>
      <p>${escapeHtml(item.reason || '补救建议的来源依据')}</p>
      ${item.value !== undefined ? `<small>value ${escapeHtml(item.value)} / threshold ${escapeHtml(item.threshold || '-')}</small>` : ''}
    </div>
  `).join('');

  sec.innerHTML = `
    <div class="remedies-dashboard">
      <div class="remedies-hero">
        <div>
          <h4>Upaya 补救计划</h4>
          <p>${escapeHtml(remedies.summary || '根据当前星盘生成补救建议。')}</p>
        </div>
        <div class="remedies-metrics">
          <span><b>${escapeHtml(totalActions)}</b>条建议</span>
          <span><b>${escapeHtml(weakPlanets.length)}</b>极弱行星</span>
          <span><b>${escapeHtml(moderatePlanets.length)}</b>偏弱行星</span>
        </div>
      </div>

      <div class="remedies-boundary">
        <strong>使用边界</strong>
        <p>补救建议只能作为传统文化与自我管理参考，不能替代医疗、法律、投资或心理咨询。宝石、斋戒、仪式类建议请先做现实风险评估。</p>
      </div>

      <div class="remedies-section">
        <h4>建议依据</h4>
        <div class="remedies-evidence-grid">${evidenceCards || '<p>暂无明确弱项证据，当前建议以低风险观察为主。</p>'}</div>
        <p class="remedies-next-action">${escapeHtml(remedies.next_action || '先执行低风险补救，再根据现实反馈复核。')}</p>
      </div>

      <div class="remedies-plan">
        <h4>前 7 天执行计划</h4>
        <ol>${firstWeek.map(step => `<li>${escapeHtml(step)}</li>`).join('')}</ol>
      </div>

      <div class="remedies-section">
        <h4>低风险优先</h4>
        <div class="remedies-grid">${mantraCards || '<p>暂无咒语建议。</p>'}${donationCards}${lifestyle.length ? renderActionCards(lifestyle.slice(0, 2), l => ({ kind: 'lifestyle', label: '生活', title: l.type || 'Lifestyle', body: l.note || '', meta: '' })) : ''}</div>
      </div>

      <div class="remedies-section">
        <h4>需要谨慎确认</h4>
        <div class="remedies-grid">${gemstoneCards || '<p>暂无宝石建议。</p>'}${fastingCards}${doshaCards}</div>
      </div>

      <details class="technique-json remedies-json">
        <summary>JSON</summary>
        <pre>${escapeHtml(JSON.stringify(remedies, null, 2).slice(0, 6000))}</pre>
      </details>
    </div>
  `;
}

// ============================================================================
// 合盘 Tab 渲染
// ============================================================================
function renderSynastryTab(chartData) {
  const selfMoon = $('synastry-self-moon');
  const partnerMoon = $('synastry-partner-moon');
  const result = $('synastry-result');
  const runBtn = $('btn-run-synastry');
  const runFullBtn = $('btn-run-synastry-full');
  const runLibraryBtn = $('btn-run-synastry-library');
  if (!result) return;

  const moonLon = getChartMoonLongitude(chartData);
  if (selfMoon && Number.isFinite(Number(moonLon))) {
    selfMoon.value = Number(moonLon).toFixed(2);
  }

  renderSynastryPartnerLibrary();
  renderSynastryPairWorkspace();
  setupSynastryPairActions();
  setupSynastryPartnerCitySearch();

  if (runLibraryBtn && !runLibraryBtn.dataset.bound) {
    runLibraryBtn.dataset.bound = 'true';
    runLibraryBtn.addEventListener('click', async () => {
      try {
        const entry = getSelectedSynastryLibraryEntry();
        if (!entry?.data) {
          result.innerHTML = '<p class="synastry-error">请先在本地星盘库中选择一个对方星盘。</p>';
          return;
        }
        await runSynastryWithPartnerChart(getActiveChartData(), entry.data, result, {
          partnerBirth: entry.data?.birth_info || {},
          partnerLabel: entry.label || entry.id,
          loading: `正在使用「${entry.label || entry.id}」计算完整合盘...`,
        });
      } catch (e) {
        result.innerHTML = renderInlineAPIError('synastry-error', '合盘计算暂不可用', e);
      }
    });
  }

  if (runFullBtn && !runFullBtn.dataset.bound) {
    runFullBtn.dataset.bound = 'true';
    runFullBtn.addEventListener('click', async () => {
      try {
        const partnerBirth = readSynastryPartnerBirth();
        result.innerHTML = '<p>正在为对方排盘并计算完整合盘...</p>';
        const partnerChart = await computeChartForBirth(partnerBirth);
        await runSynastryWithPartnerChart(getActiveChartData(), partnerChart, result, { partnerBirth });
      } catch (e) {
        result.innerHTML = renderInlineAPIError('synastry-error', '合盘计算暂不可用', e);
      }
    });
  }

  if (runBtn && partnerMoon && selfMoon && !runBtn.dataset.bound) {
    runBtn.dataset.bound = 'true';
    runBtn.addEventListener('click', async () => {
      const maleMoon = Number(selfMoon.value);
      const femaleMoon = Number(partnerMoon.value);
      if (!Number.isFinite(maleMoon) || !Number.isFinite(femaleMoon)) {
        result.innerHTML = '<p class="synastry-error">请输入 0-360 之间的月亮黄经。</p>';
        return;
      }
      if (maleMoon < 0 || maleMoon > 360 || femaleMoon < 0 || femaleMoon > 360) {
        result.innerHTML = '<p class="synastry-error">月亮黄经必须在 0-360 度之间。</p>';
        return;
      }
      result.innerHTML = '<p>正在计算 Ashtakoot 合盘...</p>';
      try {
        const data = await window.JyotishAPI?.computeSynastry?.({ male_moon: maleMoon, female_moon: femaleMoon });
        if (!data) throw new Error('本地 API 未返回结果');
        recordSynastryWorkflow(data, null, { mode: 'moon_longitude_quick' });
        result.innerHTML = renderSynastryResult(data);
        bindTerms(result);
      } catch (e) {
        result.innerHTML = renderInlineAPIError('synastry-error', '合盘计算暂不可用', e);
      }
    });
  }
}

function getActiveChartData() {
  return chartData;
}

function renderSynastryPartnerLibrary() {
  const select = $('synastry-partner-library');
  if (!select) return;
  const previous = select.value;
  const currentId = buildWorkspaceChartId(chartData);
  const legacyCurrentId = buildLegacyWorkspaceChartId(chartData);
  const lib = sortChartLibrary(readChartLibrary()).filter(entry => entry?.id && ![currentId, legacyCurrentId].includes(entry.id) && entry?.data);
  select.innerHTML = lib.length
    ? `<option value="">选择保存星盘...</option>${lib.map(entry => `<option value="${escapeAttr(entry.id)}">${escapeHtml(entry.label || entry.id)}</option>`).join('')}`
    : '<option value="">暂无可用保存星盘</option>';
  if (previous && lib.some(entry => entry.id === previous)) {
    select.value = previous;
  }
}

function getSelectedSynastryLibraryEntry() {
  const id = $('synastry-partner-library')?.value || '';
  if (!id) return null;
  return readChartLibrary().find(entry => entry?.id === id) || null;
}

async function runSynastryWithPartnerChart(selfChart, partnerChart, result, options = {}) {
  const maleMoon = getChartMoonLongitude(selfChart);
  if (!Number.isFinite(maleMoon)) {
    result.innerHTML = '<p class="synastry-error">本人星盘缺少月亮黄经，请先重新排盘。</p>';
    return;
  }
  const femaleMoon = getChartMoonLongitude(partnerChart);
  if (!Number.isFinite(femaleMoon)) throw new Error('对方星盘缺少月亮黄经，无法计算 Ashtakoot');
  if (options.loading) {
    result.innerHTML = `<p>${escapeHtml(options.loading)}</p>`;
  }
  const data = await window.JyotishAPI?.computeSynastry?.({ male_moon: maleMoon, female_moon: femaleMoon });
  if (!data) throw new Error('本地 API 未返回结果');
  const deep = buildSynastryDeepContext(selfChart, partnerChart, options.partnerBirth || partnerChart?.birth_info || {});
  recordSynastryWorkflow(data, deep, { mode: options.partnerBirth ? 'full_birth_chart' : 'saved_partner_chart' });
  _lastSynastryPairRecord = buildSynastryPairRecord(selfChart, partnerChart, data, deep, options);
  result.innerHTML = renderSynastryResult(data, deep);
  renderSynastryPairWorkspace();
  bindTerms(result);
}

function getChartMoonLongitude(chart) {
  const moon = chart?.planets?.Moon || {};
  const value = moon.lon ?? moon.longitude ?? moon.degree;
  const n = Number(value);
  return Number.isFinite(n) ? ((n % 360) + 360) % 360 : NaN;
}

function setupSynastryPartnerCitySearch() {
  const cityInput = $('synastry-partner-city');
  const suggestions = $('synastry-city-suggestions');
  const latInput = $('synastry-partner-lat');
  const lonInput = $('synastry-partner-lon');
  const tzInput = $('synastry-partner-tz');
  if (!cityInput || !suggestions || !latInput || !lonInput || !tzInput || cityInput.dataset.bound) return;
  cityInput.dataset.bound = 'true';
  let timer = null;
  cityInput.addEventListener('input', () => {
    latInput.value = '';
    lonInput.value = '';
    clearTimeout(timer);
    timer = setTimeout(() => {
      const q = cityInput.value.trim();
      if (q.length < 1) { suggestions.classList.add('hidden'); return; }
      const results = searchCities(q);
      if (!results.length) { suggestions.classList.add('hidden'); return; }
      suggestions.innerHTML = results.map(c => {
        const lat = safeNumber(c.lat);
        const lon = safeNumber(c.lon);
        const tz = safeNumber(c.tz);
        const label = c.en ? `${c.name} (${c.en})` : c.name;
        return `<div class="suggestion-item" data-lat="${escapeAttr(lat)}" data-lon="${escapeAttr(lon)}" data-tz="${escapeAttr(tz)}">${escapeHtml(label)} <small>${lat.toFixed(1)}°, ${lon.toFixed(1)}°</small></div>`;
      }).join('');
      suggestions.classList.remove('hidden');
      suggestions.querySelectorAll('.suggestion-item').forEach(el => {
        el.addEventListener('click', () => {
          cityInput.value = el.textContent.trim().split(/\s+\(/)[0];
          latInput.value = el.dataset.lat;
          lonInput.value = el.dataset.lon;
          tzInput.value = el.dataset.tz;
          suggestions.classList.add('hidden');
        });
      });
    }, 200);
  });
  document.addEventListener('click', e => {
    if (!cityInput.contains(e.target) && !suggestions.contains(e.target)) suggestions.classList.add('hidden');
  });
}

function readSynastryPartnerBirth() {
  const dateValue = $('synastry-partner-date')?.value || '';
  const timeValue = $('synastry-partner-time')?.value || '';
  const lat = Number($('synastry-partner-lat')?.value);
  const lon = Number($('synastry-partner-lon')?.value);
  const tz = Number($('synastry-partner-tz')?.value);
  if (!dateValue || !timeValue) throw new Error('请填写对方出生日期和时间。');
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) throw new Error('请选择对方出生城市，或通过城市搜索填入经纬度。');
  if (!Number.isFinite(tz)) throw new Error('请填写对方出生地时区，例如印度为 5.5，中国为 8。');
  const [year, month, day] = dateValue.split('-').map(Number);
  const [hour, minute, second = 0] = timeValue.split(':').map(Number);
  if (![year, month, day, hour, minute].every(Number.isFinite)) throw new Error('对方出生日期或时间格式不正确。');
  return { year, month, day, hour, minute, second, lat, lon, tz };
}

function buildSynastryDeepContext(selfChart, partnerChart, partnerBirth) {
  return {
    partnerBirth,
    partnerSummary: buildSynastryChartSummary(partnerChart),
    comparison: buildBiWheelComparisonData(selfChart, partnerChart),
    spouseStatus: buildSynastrySpouseStatusContext(selfChart, partnerChart),
    ulDkTiming: buildULDKTimingContext(selfChart, partnerChart),
    selfD9: buildChartD9MarriageSnapshot(selfChart),
    partnerD9: buildChartD9MarriageSnapshot(partnerChart),
    kuja: buildKujaComparison(selfChart, partnerChart),
    dasha: buildDashaSync(selfChart, partnerChart),
  };
}

function buildSynastryChartSummary(chart) {
  const asc = chart?.ascendant || {};
  const moon = chart?.planets?.Moon || {};
  const current = getCurrentDashaSnapshot(chart);
  return {
    ascendant: asc.sign ? signName(asc.sign) : '-',
    moon: moon.sign ? `${signName(moon.sign)} ${formatDegreeInSign(moon.degree_in_sign ?? moon.degree)}` : '-',
    nakshatra: moon.nakshatra ? `${moon.nakshatra}${moon.nakshatra_pada ? ` P${moon.nakshatra_pada}` : ''}` : '-',
    dasha: current.label,
  };
}

function buildSynastrySpouseStatusContext(selfChart, partnerChart) {
  return {
    self: buildSpouseStatusSnapshot(selfChart),
    partner: buildSpouseStatusSnapshot(partnerChart),
  };
}

function buildULDKTimingContext(selfChart, partnerChart) {
  return {
    self: buildULDKTimingSnapshot(selfChart),
    partner: buildULDKTimingSnapshot(partnerChart),
  };
}

function buildULDKTimingSnapshot(chart) {
  if (!chart?.planets || !chart?.ascendant?.sign) return null;
  const karaka = computeKaraka(chart.planets);
  const arudha = computeArudha(chart.planets, chart.ascendant.sign);
  const dk7 = normalizeDKPoint(karaka?.karaka7?.DK, chart);
  const dk8 = normalizeDKPoint(karaka?.karaka8?.DK, chart);
  const ul = normalizeULPoint(arudha?.UL);
  const dasha = getCurrentDashaSnapshot(chart);
  const seventhSign = SIGNS[(SIGNS.indexOf(chart.ascendant.sign) + 6 + 12) % 12] || '';
  const seventhLord = SIGN_LORDS[seventhSign] || '';
  const triggers = [];
  const dashaLords = [dasha.maha, dasha.antar, dasha.pratyantar].filter(Boolean);
  const addTrigger = text => {
    if (text && !triggers.includes(text)) triggers.push(text);
  };
  dashaLords.forEach(lord => {
    if (lord === dk7?.planet) addTrigger(`${planetName(lord)} 运触发 7星制 DK`);
    if (lord === dk8?.planet && lord !== dk7?.planet) addTrigger(`${planetName(lord)} 运触发 8星制 DK`);
    if (lord === seventhLord) addTrigger(`${planetName(lord)} 运触发 7宫主`);
    if (['Venus', 'Jupiter', 'Moon', 'Mars'].includes(lord)) addTrigger(`${planetName(lord)} 运触发关系自然征象星`);
    if (lord === ul?.lord) addTrigger(`${planetName(lord)} 运触发 UL 主星`);
  });
  const ulMatchesDK = Boolean(ul?.sign && [dk7?.sign, dk8?.sign].includes(ul.sign));
  if (ulMatchesDK) addTrigger(`UL 与 DK 同落 ${signName(ul.sign)}，配偶征象更集中`);
  const level = triggers.length >= 3 ? 'strong' : triggers.length >= 1 ? 'moderate' : 'low';
  const summary = level === 'strong'
    ? 'DK/UL 与当前运限多点交叉'
    : level === 'moderate'
      ? 'DK/UL 或关系星有单点触发'
      : '当前运限未明显触发 DK/UL';
  return {
    dk7,
    dk8,
    ul,
    dasha,
    triggers,
    level,
    summary,
    evidence: [
      dk7 ? `7星制 DK：${formatDKPoint(dk7)}` : '7星制 DK 待补充',
      dk8 ? `8星制 DK：${formatDKPoint(dk8)}` : '8星制 DK 待补充',
      ul ? `UL：${formatULPoint(ul)}` : 'UL 待补充',
      `当前 Dasha：${dasha.label || '-'}`,
    ],
  };
}

function normalizeDKPoint(point, chart) {
  if (!point?.planet) return null;
  const planet = chart?.planets?.[point.planet] || {};
  return {
    planet: point.planet,
    sign: point.sign || planet.sign || '',
    house: point.house || planet.house || '',
    degree: point.degree,
  };
}

function normalizeULPoint(point) {
  if (!point?.sign) return null;
  return {
    sign: point.sign,
    pada_house: point.pada_house,
    lord: point.lord,
  };
}

function buildSpouseStatusSnapshot(chart) {
  const ascSign = chart?.ascendant?.sign || '';
  if (!ascSign || !chart?.planets) return null;
  const seventhSign = SIGNS[(SIGNS.indexOf(ascSign) + 6 + 12) % 12] || '';
  const seventhLord = SIGN_LORDS[seventhSign] || '';
  const lagnaLord = SIGN_LORDS[ascSign] || '';
  const seventhLordPlanet = chart.planets[seventhLord] || {};
  const lagnaLordPlanet = chart.planets[lagnaLord] || {};
  const seventhOccupants = Object.entries(chart.planets)
    .filter(([, planet]) => Number(planet?.house) === 7)
    .map(([name]) => name);
  const upachayaFromSeventh = [9, 12, 4, 5];
  const growthHouses = Object.entries(chart.planets)
    .filter(([, planet]) => upachayaFromSeventh.includes(Number(planet?.house)))
    .map(([name, planet]) => `${planetName(name)} H${planet.house}`);
  const score = [
    ['exalted', 'own'].includes(seventhLordPlanet.dignity) ? 2 : ['friendly'].includes(seventhLordPlanet.dignity) ? 1 : 0,
    [1, 4, 5, 7, 9, 10].includes(Number(seventhLordPlanet.house)) ? 1 : 0,
    [3, 6, 10, 11].includes(Number(seventhLordPlanet.house)) ? 1 : 0,
    growthHouses.length ? 1 : 0,
  ].reduce((sum, value) => sum + value, 0);
  return {
    ascSign,
    seventhSign,
    seventhLord,
    lagnaLord,
    score,
    level: score >= 4 ? 'strong' : score >= 2 ? 'moderate' : 'low',
    verdict: score >= 4 ? '婚后成长/伴侣资源信号强' : score >= 2 ? '有婚后成长或伴侣资源信号' : '未见明显高地位配偶 Yoga',
    evidence: [
      `7宫 ${signName(seventhSign)}，7主 ${planetName(seventhLord)} 位于 H${seventhLordPlanet.house || '-'} ${seventhLordPlanet.dignity || 'unknown'}`,
      `Lagna 主 ${planetName(lagnaLord)} 位于 H${lagnaLordPlanet.house || '-'} ${lagnaLordPlanet.dignity || 'unknown'}`,
      seventhOccupants.length ? `7宫内行星：${seventhOccupants.map(planetName).join('、')}` : '7宫无主要行星占据',
      growthHouses.length ? `从7宫起算成长宫被占据：${growthHouses.join('、')}` : '从7宫起算成长宫暂无明显占据',
    ],
  };
}

function buildChartD9MarriageSnapshot(chart) {
  if (!chart?.planets || !chart?.ascendant) return null;
  const allV = computeAllVargas(chart.planets);
  const karaka = computeKaraka(chart.planets);
  const report = buildD9MarriageReport(allV, chart.planets, chart.ascendant, karaka);
  if (!report) return null;
  return {
    score: report.score,
    zone: report.zone,
    core: report.core,
    positives: report.flags.filter(flag => flag.score > 0).slice(0, 3),
    risks: report.flags.filter(flag => flag.score < 0).slice(0, 3),
  };
}

function buildKujaComparison(selfChart, partnerChart) {
  const self = analyzeKujaDosha(selfChart);
  const partner = analyzeKujaDosha(partnerChart);
  const diff = Math.abs(self.score - partner.score);
  let verdict = 'balanced';
  let label = '火星煞压力相近';
  let note = '双方 Kuja/Manglik 压力相近，可继续综合看 D9 与 Dasha。';
  if (diff >= 3) {
    verdict = 'hard';
    label = '火星煞不平衡';
    note = '双方火星煞压力差距较大，关系冲突、节奏和安全感议题需要额外复核。';
  } else if (diff >= 2) {
    verdict = 'watch';
    label = '火星煞需观察';
    note = '双方火星煞压力有差异，建议结合现实互动和婚姻宫受克情况判断。';
  }
  return { self, partner, diff, verdict, label, note };
}

function analyzeKujaDosha(chart) {
  const planets = chart?.planets || {};
  const mars = planets.Mars || {};
  const moon = planets.Moon || {};
  const venus = planets.Venus || {};
  const lagnaHouse = Number(mars.house);
  const moonHouse = houseFromSign(moon.sign, mars.sign);
  const venusHouse = houseFromSign(venus.sign, mars.sign);
  const refs = [
    { from: 'Lagna', house: lagnaHouse },
    { from: 'Moon', house: moonHouse },
    { from: 'Venus', house: venusHouse },
  ].filter(item => Number.isFinite(item.house));
  const doshaHouses = new Set([1, 2, 4, 7, 8, 12]);
  const severeHouses = new Set([7, 8]);
  const hits = refs.filter(item => doshaHouses.has(item.house));
  const mitigations = [];
  if (['Aries', 'Scorpio', 'Capricorn'].includes(mars.sign)) mitigations.push('Mars 入庙/旺相缓解');
  if (planets.Jupiter?.house === mars.house) mitigations.push('Jupiter 同宫保护');
  let score = hits.reduce((sum, item) => sum + (severeHouses.has(item.house) ? 2 : 1), 0);
  if (mitigations.length) score = Math.max(0, score - 1);
  const level = score >= 4 ? 'high' : score >= 2 ? 'medium' : score >= 1 ? 'low' : 'none';
  const levelLabel = { high: '偏强', medium: '中等', low: '轻微', none: '未见明显' }[level];
  return {
    score,
    level,
    levelLabel,
    marsSign: mars.sign || '-',
    marsHouse: Number.isFinite(lagnaHouse) ? lagnaHouse : '-',
    hits,
    mitigations,
  };
}

function houseFromSign(fromSign, toSign) {
  const fromIdx = SIGNS.indexOf(fromSign);
  const toIdx = SIGNS.indexOf(toSign);
  if (fromIdx < 0 || toIdx < 0) return NaN;
  return ((toIdx - fromIdx + 12) % 12) + 1;
}

function buildDashaSync(selfChart, partnerChart) {
  const self = getCurrentDashaSnapshot(selfChart);
  const partner = getCurrentDashaSnapshot(partnerChart);
  const shared = [self.maha, self.antar, self.pratyantar].filter(Boolean)
    .filter(lord => [partner.maha, partner.antar, partner.pratyantar].includes(lord));
  const relationshipLords = new Set(['Venus', 'Jupiter', 'Moon', 'Mars']);
  const selfRelationship = [self.maha, self.antar].some(lord => relationshipLords.has(lord));
  const partnerRelationship = [partner.maha, partner.antar].some(lord => relationshipLords.has(lord));
  let level = 'neutral';
  let label = '节奏中性';
  let note = '当前大运/小运没有明显同步，适合继续看行运触发与现实互动。';
  if (shared.length) {
    level = 'strong';
    label = 'Dasha 同步强';
    note = `双方当前运限共享 ${shared.map(planetName).join('、')}，关系议题更容易被同一类事件激活。`;
  } else if (selfRelationship && partnerRelationship) {
    level = 'supportive';
    label = '关系主题同时被激活';
    note = '双方当前运限都触及 Venus/Jupiter/Moon/Mars，亲密关系议题的可见度较高。';
  }
  return { self, partner, shared, level, label, note };
}

function getCurrentDashaSnapshot(chart) {
  const moonLon = getChartMoonLongitude(chart);
  const date = chart?.birth_info?.date;
  if (!Number.isFinite(moonLon) || !date) return { label: '-', maha: '', antar: '', pratyantar: '' };
  const dasha = computeDashaWithPratyantar(moonLon, date, new Date().toISOString().split('T')[0]);
  const current = dasha?.current || dasha?.current_dasha || {};
  const maha = current.maha_lord || current.maha || current.md || current.lord || '';
  const antar = current.antar_lord || current.antar || current.ad || '';
  const pratyantar = current.pratyantar_lord || current.pratyantar || current.pd || '';
  const label = [maha, antar, pratyantar].filter(Boolean).map(planetName).join(' / ') || '-';
  return { label, maha, antar, pratyantar };
}

function formatDegreeInSign(value) {
  const n = Number(value);
  return Number.isFinite(n) ? `${n.toFixed(2)}°` : '';
}

function buildBiWheelComparisonData(selfChart, partnerChart) {
  const axes = [
    buildBiWheelAxisRow('上升轴', buildChartAxisPoint(selfChart), buildChartAxisPoint(partnerChart), '身体节奏、第一印象与共同生活入口'),
    buildBiWheelAxisRow('月亮轴', buildSynastryPlanetPoint(selfChart, 'Moon'), buildSynastryPlanetPoint(partnerChart, 'Moon'), '情绪安全感、日常照料和亲密反应'),
    buildBiWheelAxisRow('金星轴', buildSynastryPlanetPoint(selfChart, 'Venus'), buildSynastryPlanetPoint(partnerChart, 'Venus'), '吸引力、价值交换和关系愉悦感'),
    buildBiWheelAxisRow('火星轴', buildSynastryPlanetPoint(selfChart, 'Mars'), buildSynastryPlanetPoint(partnerChart, 'Mars'), '行动节奏、冲突方式和欲望表达'),
  ].filter(row => row.self?.sign || row.partner?.sign);
  const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
  const rows = planets.map(planet => {
    const self = buildSynastryPlanetPoint(selfChart, planet);
    const partner = buildSynastryPlanetPoint(partnerChart, planet);
    if (!self.sign && !partner.sign) return null;
    return {
      planet,
      label: planetName(planet),
      self,
      partner,
      relation: buildSignRelationship(self.sign, partner.sign),
      partnerOverlayHouse: overlayHouseFromChart(selfChart, partner.sign),
      selfOverlayHouse: overlayHouseFromChart(partnerChart, self.sign),
      theme: relationshipPlanetTheme(planet),
    };
  }).filter(Boolean);
  return {
    axes,
    rows,
    compositeStyle: buildCompositeStyleMidpoints(selfChart, partnerChart),
  };
}

function buildBiWheelAxisRow(label, self, partner, theme) {
  return {
    label,
    self,
    partner,
    relation: buildSignRelationship(self?.sign, partner?.sign),
    theme,
  };
}

function buildChartAxisPoint(chart) {
  const asc = chart?.ascendant || {};
  return {
    sign: asc.sign || '',
    degree: Number.isFinite(Number(asc.degree_in_sign ?? asc.degree)) ? Number(asc.degree_in_sign ?? asc.degree) : null,
    house: 1,
    label: asc.sign ? `${signName(asc.sign)} ${formatDegreeInSign(asc.degree_in_sign ?? asc.degree)}` : '-',
  };
}

function buildSynastryPlanetPoint(chart, planet) {
  const raw = chart?.planets?.[planet] || {};
  const lon = normalizeLongitude(raw.lon ?? raw.longitude ?? raw.absolute_degree ?? raw.degree);
  const sign = raw.sign || signFromLongitude(lon) || '';
  const degree = Number.isFinite(Number(raw.degree_in_sign))
    ? Number(raw.degree_in_sign)
    : Number.isFinite(lon)
      ? lon % 30
      : Number.isFinite(Number(raw.degree))
        ? Number(raw.degree)
        : null;
  return {
    planet,
    sign,
    degree,
    lon: Number.isFinite(lon) ? lon : null,
    house: Number.isFinite(Number(raw.house)) ? Number(raw.house) : null,
    nakshatra: raw.nakshatra || '',
    label: sign ? `${signName(sign)} ${formatDegreeInSign(degree)}` : '-',
  };
}

function normalizeLongitude(value) {
  const n = Number(value);
  return Number.isFinite(n) ? ((n % 360) + 360) % 360 : NaN;
}

function signFromLongitude(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return '';
  return SIGNS[Math.floor(normalizeLongitude(n) / 30) % 12] || '';
}

function buildSignRelationship(selfSign, partnerSign) {
  const selfIdx = SIGNS.indexOf(selfSign);
  const partnerIdx = SIGNS.indexOf(partnerSign);
  if (selfIdx < 0 || partnerIdx < 0) {
    return { houseDistance: '-', label: '待补充', tone: 'neutral' };
  }
  const houseDistance = ((partnerIdx - selfIdx + 12) % 12) + 1;
  const labels = {
    1: '同星座共振',
    2: '资源磨合',
    3: '沟通学习',
    4: '家庭/安全感张力',
    5: '三方支持',
    6: '调适与服务',
    7: '对宫吸引',
    8: '深层转化',
    9: '三方支持',
    10: '目标/责任张力',
    11: '社群与愿景支持',
    12: '隐性议题',
  };
  const tone = [1, 5, 9, 11].includes(houseDistance)
    ? 'support'
    : [4, 7, 10].includes(houseDistance)
      ? 'tension'
      : [2, 6, 8, 12].includes(houseDistance)
        ? 'work'
        : 'neutral';
  return { houseDistance, label: labels[houseDistance] || '中性', tone };
}

function overlayHouseFromChart(chart, sign) {
  const house = houseFromSign(chart?.ascendant?.sign, sign);
  return Number.isFinite(house) ? house : null;
}

function buildCompositeStyleMidpoints(selfChart, partnerChart) {
  return ['Sun', 'Moon', 'Venus', 'Mars'].map(planet => {
    const self = buildSynastryPlanetPoint(selfChart, planet);
    const partner = buildSynastryPlanetPoint(partnerChart, planet);
    if (!Number.isFinite(self.lon) || !Number.isFinite(partner.lon)) return null;
    const lon = midpointLongitude(self.lon, partner.lon);
    const sign = signFromLongitude(lon);
    return {
      planet,
      label: planetName(planet),
      sign,
      degree: lon % 30,
      note: `${planetName(planet)} midpoint 指向共同关系场的${relationshipPlanetTheme(planet)}`,
    };
  }).filter(Boolean);
}

function midpointLongitude(a, b) {
  const start = normalizeLongitude(a);
  const delta = ((normalizeLongitude(b) - start + 540) % 360) - 180;
  return normalizeLongitude(start + delta / 2);
}

function relationshipPlanetTheme(planet) {
  return {
    Sun: '身份认同与长期方向',
    Moon: '情绪安全感',
    Mars: '行动、冲突与欲望',
    Mercury: '沟通和日常协商',
    Jupiter: '信念、承诺和成长',
    Venus: '吸引力、价值和愉悦',
    Saturn: '责任、边界和时间压力',
    Rahu: '新奇、执念和突破常规',
    Ketu: '疏离、灵性和旧模式',
  }[planet] || '关系互动';
}

function buildRelationshipReportTemplate(data = {}, deep = null) {
  const total = Number(data.total_score ?? data.score?.total ?? 0);
  const max = Number(data.max_score ?? data.score?.max ?? 36) || 36;
  const percentage = max ? Number(((total / max) * 100).toFixed(1)) : 0;
  const scores = data.scores || {};
  const kutaDetails = Object.entries(scores).map(([name, score]) => {
    const maxScore = Number(kutaMax(name));
    const value = Number(score);
    const ratio = Number.isFinite(value) && Number.isFinite(maxScore) && maxScore > 0 ? value / maxScore : 0;
    return { name, score: Number.isFinite(value) ? value : score, max: Number.isFinite(maxScore) ? maxScore : '-', ratio };
  });
  const strongestKutas = kutaDetails.filter(item => item.ratio >= 0.75).sort((a, b) => b.ratio - a.ratio).slice(0, 3);
  const weakKutas = kutaDetails.filter(item => item.ratio <= 0.35).sort((a, b) => a.ratio - b.ratio).slice(0, 3);
  const d9Scores = [deep?.selfD9?.score, deep?.partnerD9?.score].map(Number).filter(Number.isFinite);
  const d9Average = d9Scores.length ? Number((d9Scores.reduce((sum, value) => sum + value, 0) / d9Scores.length).toFixed(1)) : null;
  const kuja = deep?.kuja || null;
  const dasha = deep?.dasha || null;
  const hasDeep = Boolean(deep?.selfD9 || deep?.partnerD9 || kuja || dasha);
  const spouseStatus = deep?.spouseStatus || null;
  const ulDkTiming = deep?.ulDkTiming || null;
  const approvedFlag = data.is_match_approved ?? data.is_approved;
  const status = percentage >= 78 && approvedFlag !== false
    ? 'strong'
    : percentage >= 58 && approvedFlag !== false
      ? 'workable'
      : 'needs_context';
  const statusLabel = {
    strong: '高兼容，仍需完整复核',
    workable: '可推进观察',
    needs_context: '需谨慎综合判断',
  }[status];
  const headline = status === 'strong'
    ? 'Ashtakoot 基础匹配较强，适合进入 D9、Kuja 与现实互动复核。'
    : status === 'workable'
      ? '基础匹配有可用支撑，但关键风险位需要逐项确认。'
      : '当前匹配不能只按总分推进，需要把红旗与时机证据放在前面。';
  const strengths = strongestKutas.map(item => `${item.name} ${item.score}/${item.max}：此项支持关系中的${relationshipKutaMeaning(item.name)}。`);
  if (d9Average !== null && d9Average >= 3) strengths.push(`D9 平均 ${d9Average}/8：双方婚姻分盘至少有可用支撑。`);
  if (dasha?.level === 'strong' || dasha?.level === 'supportive') strengths.push(dasha.note || dasha.label);
  collectULDKTimingStrengths(ulDkTiming).forEach(item => strengths.push(item));
  collectSpouseStatusStrengths(spouseStatus).forEach(item => strengths.push(item));
  if (!strengths.length) strengths.push('尚未出现足够稳定的强项，建议先补完整出生盘与 D9 复核。');
  const risks = weakKutas.map(item => `${item.name} ${item.score}/${item.max}：需重点观察${relationshipKutaMeaning(item.name)}。`);
  if (kuja?.verdict === 'hard' || kuja?.verdict === 'watch') risks.push(kuja.note || kuja.label);
  if (d9Average !== null && d9Average < 2) risks.push(`D9 平均 ${d9Average}/8：婚姻分盘质量偏弱，不能只依赖合盘总分。`);
  if ((data.exceptions || []).length) risks.push(`存在缓解条件：${(data.exceptions || []).join('；')}`);
  collectULDKTimingRisks(ulDkTiming).forEach(item => risks.push(item));
  collectSpouseStatusRisks(spouseStatus).forEach(item => risks.push(item));
  if (!hasDeep) risks.push('当前只完成基础 Ashtakoot，缺少 D9、Kuja Dosha 与 Dasha 同步证据。');
  if (!risks.length) risks.push('未见明显红旗，但仍需结合双方完整星盘与现实互动。');
  const evidence = [
    { label: 'Ashtakoot', value: `${formatReportNumber(total)} / ${formatReportNumber(max)}`, note: `${percentage}% · ${data.assessment || statusLabel}` },
    { label: 'D9 质量', value: d9Average === null ? '待补充' : `${d9Average} / 8`, note: d9Scores.length ? '取双方 D9 婚姻快照平均值' : '需要双方准确出生时间' },
    { label: 'Kuja Dosha', value: kuja?.label || '待补充', note: kuja?.note || '完整出生盘后可判断冲突压力是否平衡' },
    { label: 'Dasha 时机', value: dasha?.label || '待补充', note: dasha?.note || '需要双方 Moon 与出生日期计算当前运限' },
    { label: 'UL/DK 时机', value: formatULDKTimingEvidence(ulDkTiming), note: 'Jaimini 配偶征象与当前运限触发的交叉检查' },
    { label: '配偶/婚后成长', value: formatSpouseStatusEvidence(spouseStatus), note: '来自 7宫/7主/成长宫的个人关系体质快照' },
  ];
  return {
    status,
    statusLabel,
    headline,
    percentage,
    evidence,
    strongestKutas,
    weakKutas,
    strengths: strengths.slice(0, 5),
    risks: risks.slice(0, 5),
    nextSteps: [
      '先确认双方出生时间精度，再复核 D9 与 7宫/7主。',
      '把低分 Kuta 对应到现实互动议题，不用单一分数替代沟通。',
      '若 Kuja 或 Dasha 出现压力，优先安排边界、节奏和冲突处理观察期。',
    ],
    boundaries: [
      '合盘报告只提供传统 Jyotish 证据，不替代个人选择。',
      '总分通过不等于关系必然稳定；总分偏低也不等于关系不可经营。',
    ],
  };
}

function collectSpouseStatusStrengths(spouseStatus) {
  return ['self', 'partner'].map(key => {
    const item = spouseStatus?.[key];
    if (!item || item.level === 'low') return '';
    return `${key === 'self' ? '本人' : '对方'}：${item.verdict}，可作为关系长期资源/成长证据。`;
  }).filter(Boolean);
}

function collectSpouseStatusRisks(spouseStatus) {
  return ['self', 'partner'].map(key => {
    const item = spouseStatus?.[key];
    if (!item || item.level !== 'low') return '';
    return `${key === 'self' ? '本人' : '对方'}：${item.verdict}，需结合 D9 与现实承诺复核。`;
  }).filter(Boolean);
}

function collectULDKTimingStrengths(ulDkTiming) {
  return ['self', 'partner'].map(key => {
    const item = ulDkTiming?.[key];
    if (!item || item.level === 'low') return '';
    return `${key === 'self' ? '本人' : '对方'}：${item.summary}，关系时机有可读触发。`;
  }).filter(Boolean);
}

function collectULDKTimingRisks(ulDkTiming) {
  return ['self', 'partner'].map(key => {
    const item = ulDkTiming?.[key];
    if (!item || item.level !== 'low') return '';
    return `${key === 'self' ? '本人' : '对方'}：${item.summary}，当前运限未明显触发 DK/UL。`;
  }).filter(Boolean);
}

function formatSpouseStatusEvidence(spouseStatus) {
  const self = spouseStatus?.self?.verdict || '待补充';
  const partner = spouseStatus?.partner?.verdict || '待补充';
  return `本人：${self} / 对方：${partner}`;
}

function formatULDKTimingEvidence(ulDkTiming) {
  const self = ulDkTiming?.self?.summary || '待补充';
  const partner = ulDkTiming?.partner?.summary || '待补充';
  return `本人：${self} / 对方：${partner}`;
}

function relationshipKutaMeaning(name) {
  return {
    Varna: '精神追求与价值层级',
    Vashya: '影响力与相处主导权',
    Tara: '生活阶段与支持感',
    Yoni: '性格/身体语言兼容',
    GrahaMaitri: '思维方式与情感理解',
    Gana: '气质类型和社交风格',
    Bhakoot: '情绪频率与整体关系节奏',
    Nadi: '体质、习惯和深层相似性',
  }[name] || '关系互动';
}

function formatReportNumber(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return value ?? '-';
  return Number.isInteger(n) ? String(n) : n.toFixed(1).replace(/\.0$/, '');
}

function renderSynastryResult(data, deep = null) {
  const scores = data.scores || {};
  const male = data.male_details || data.male || {};
  const female = data.female_details || data.female || {};
  const approvedFlag = data.is_match_approved ?? data.is_approved;
  const percentage = data.match_percentage ?? ((Number(data.total_score || 0) / Number(data.max_score || 36)) * 100).toFixed(1);
  const relationshipReport = deep?.relationshipReport || data.relationshipReport || data.relationship_report || buildRelationshipReportTemplate(data, deep);
  const rows = Object.entries(scores).map(([name, score]) => `
    <tr><td>${escapeHtml(name)}</td><td>${escapeHtml(score)} / ${escapeHtml(kutaMax(name))}</td></tr>
  `).join('');
  const approved = approvedFlag ? '匹配通过' : '需要谨慎综合判断';
  const approvedClass = approvedFlag ? 'synastry-ok' : 'synastry-warn';
  const exceptionHtml = (data.exceptions || []).length
    ? `<div class="synastry-note"><strong>缓解条件</strong><p>${(data.exceptions || []).map(escapeHtml).join('<br>')}</p></div>`
    : '';
  return `
    <div class="synastry-score ${approvedClass}">
      <strong>${escapeHtml(data.total_score ?? 0)} / ${escapeHtml(data.max_score ?? 36)}</strong>
      <span>${escapeHtml(percentage)}% · ${approved}</span>
    </div>
    <div class="synastry-details">
      ${renderPartnerDetails('本人', male)}
      ${renderPartnerDetails('对方', female)}
    </div>
    <div class="synastry-table-wrap">
      <table class="synastry-table">
        <thead><tr><th>Kuta</th><th>得分</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    ${exceptionHtml}
    ${renderRelationshipReport(relationshipReport)}
    ${deep ? renderSynastryDeepResult(deep) : ''}
    ${deep ? renderSynastryPairActions() : ''}
    <p class="synastry-boundary">合盘分数不能单独决定关系。正式关系判断还需结合双方完整星盘、7宫/7主、D9、Kuja Dosha、Dasha 同步、现实互动与自主选择。</p>
  `;
}

function buildSynastryPairRecord(selfChart, partnerChart, data, deep, options = {}) {
  const now = new Date().toISOString();
  const selfId = buildWorkspaceChartId(selfChart) || 'current-chart';
  const partnerId = buildWorkspaceChartId(partnerChart) || `partner-${now}`;
  const total = Number(data.total_score ?? 0);
  const max = Number(data.max_score ?? 36);
  const partnerLabel = options.partnerLabel || buildWorkspaceChartLabel(partnerChart);
  const relationshipReport = buildRelationshipReportTemplate(data, deep);
  return {
    id: `${selfId}__${partnerId}`,
    label: `${buildWorkspaceChartLabel(selfChart)} ↔ ${partnerLabel}`,
    group: '伴侣',
    relation: 'partner',
    tags: ['synastry', 'relationship', 'ashtakoot'],
    generatedAt: now,
    updatedAt: now,
    selfChartId: selfId,
    partnerChartId: partnerId,
    self: buildSynastryChartSummary(selfChart),
    partner: buildSynastryChartSummary(partnerChart),
    score: {
      total,
      max,
      percentage: max ? Number(((total / max) * 100).toFixed(1)) : 0,
    },
    verdict: data.assessment || (data.is_approved ? '匹配通过' : '需要谨慎综合判断'),
    scores: data.scores || {},
    exceptions: data.exceptions || [],
    relationshipReport,
    deep: deep ? normalizeSynastryDeepForExport({ ...deep, relationshipReport }) : null,
    source: options.partnerLabel ? 'saved_partner_chart' : 'full_birth_chart',
    data: {
      total_score: data.total_score ?? 0,
      max_score: data.max_score ?? 36,
      match_percentage: data.match_percentage ?? (max ? Number(((total / max) * 100).toFixed(1)) : 0),
      is_match_approved: data.is_match_approved ?? data.is_approved ?? false,
      scores: data.scores || {},
      exceptions: data.exceptions || [],
      male_details: data.male_details || data.male || {},
      female_details: data.female_details || data.female || {},
      assessment: data.assessment || '',
      relationship_report: relationshipReport,
    },
  };
}

function renderSynastryPairActions() {
  return `
    <div class="synastry-pair-actions">
      <button type="button" class="btn-secondary" data-action="save-synastry-pair">保存配对记录</button>
      <button type="button" class="btn-secondary" data-action="export-synastry-pair">导出当前配对</button>
      <button type="button" class="btn-secondary" data-action="export-synastry-html">导出 HTML 报告</button>
    </div>
  `;
}

function setupSynastryPairActions() {
  const result = $('synastry-result');
  if (result && result.dataset.pairActionsBound !== 'true') {
    result.dataset.pairActionsBound = 'true';
    result.addEventListener('click', event => {
      const btn = event.target.closest('[data-action="save-synastry-pair"], [data-action="export-synastry-pair"], [data-action="export-synastry-html"]');
      if (!btn) return;
      if (btn.dataset.action === 'save-synastry-pair') {
        saveCurrentSynastryPair();
      }
      if (btn.dataset.action === 'export-synastry-pair') {
        exportCurrentSynastryPair();
      }
      if (btn.dataset.action === 'export-synastry-html') {
        exportCurrentSynastryHTMLReport();
      }
    });
  }
  const workspace = $('synastry-pair-workspace');
  if (!workspace || workspace.dataset.pairWorkspaceBound === 'true') return;
  workspace.dataset.pairWorkspaceBound = 'true';
  workspace.addEventListener('click', event => {
    const btn = event.target.closest('[data-action="save-synastry-pair"], [data-action="export-synastry-pair"]');
    const actionBtn = btn || event.target.closest('.mini-action');
    if (!actionBtn) return;
    if (actionBtn.dataset.action === 'workspace-open-pair') openSavedSynastryPair(actionBtn.dataset.caseId || '');
    if (actionBtn.dataset.action === 'workspace-delete-pair') deleteSavedSynastryPair(actionBtn.dataset.caseId || '');
    if (!btn) return;
    if (btn.dataset.action === 'save-synastry-pair') {
      saveCurrentSynastryPair();
    }
    if (btn.dataset.action === 'export-synastry-pair') {
      exportCurrentSynastryPair();
    }
  });
}

function sortSynastryPairLibrary(lib) {
  return [...(Array.isArray(lib) ? lib : [])].sort((a, b) => {
    const aTime = Date.parse(a?.updatedAt || a?.generatedAt || '') || 0;
    const bTime = Date.parse(b?.updatedAt || b?.generatedAt || '') || 0;
    return bTime - aTime;
  });
}

function saveCurrentSynastryPair() {
  if (!_lastSynastryPairRecord) return;
  const now = new Date().toISOString();
  const lib = readSynastryPairLibrary();
  const existing = lib.find(record => record?.id === _lastSynastryPairRecord.id);
  if (existing) {
    Object.assign(existing, _lastSynastryPairRecord, { updatedAt: now, generatedAt: existing.generatedAt || now });
  } else {
    lib.push({ ..._lastSynastryPairRecord, generatedAt: now, updatedAt: now });
  }
  writeSynastryPairLibrary(sortSynastryPairLibrary(lib).slice(0, 50));
  renderSynastryPairWorkspace();
}

function exportCurrentSynastryPair() {
  if (!_lastSynastryPairRecord) return;
  const safeId = String(_lastSynastryPairRecord.id || 'pair').replace(/[^a-z0-9_-]+/gi, '-');
  downloadText(JSON.stringify(_lastSynastryPairRecord, null, 2), `jyotish-synastry-${safeId}.json`, 'application/json;charset=utf-8');
}

async function exportCurrentSynastryHTMLReport() {
  if (!chartData || !_lastSynastryPairRecord) return;
  const workflows = ensureClientWorkflows();
  if (workflows) {
    workflows.synastry = buildSynastryWorkflowFromPair(_lastSynastryPairRecord);
  }
  const { exportHTMLReport } = await loadExportModule();
  exportHTMLReport(chartData, buildExportExtras(chartData));
}

function buildSynastryWorkflowFromPair(record) {
  const replayDeep = buildSynastryReplayDeep(record);
  const report = record.relationshipReport || record.data?.relationship_report || record.deep?.relationshipReport || buildRelationshipReportTemplate(record.data || record, replayDeep);
  return {
    mode: record.source || 'saved_pair',
    generatedAt: record.generatedAt || record.updatedAt || new Date().toISOString(),
    total_score: record.score?.total ?? 0,
    max_score: record.score?.max ?? 36,
    match_percentage: record.score?.percentage ?? 0,
    is_match_approved: String(record.verdict || '').includes('通过'),
    scores: record.scores || {},
    exceptions: record.exceptions || [],
    male_details: record.data?.male_details || record.data?.male || {},
    female_details: record.data?.female_details || record.data?.female || {},
    assessment: record.verdict || record.data?.assessment || '',
    relationship_report: report,
    deep: record.deep || null,
  };
}

function renderSavedSynastryPair(record) {
  const data = record?.data || {
    total_score: record?.score?.total ?? 0,
    max_score: record?.score?.max ?? 36,
    match_percentage: record?.score?.percentage ?? 0,
    scores: record?.scores || {},
    exceptions: record?.exceptions || [],
    assessment: record?.verdict || '',
  };
  return `
    <div class="case-replay-banner">
      <strong>已打开保存配对</strong>
      <span>${escapeHtml(record?.label || record?.id || '未命名配对')} · ${escapeHtml(formatSavedAt(record?.updatedAt || record?.generatedAt))}</span>
    </div>
    ${renderSynastryResult(data, buildSynastryReplayDeep(record))}
  `;
}

function buildSynastryReplayDeep(record) {
  const deep = record?.deep || {};
  const report = deep.relationshipReport || record?.relationshipReport || record?.data?.relationship_report || null;
  if (!deep.partnerSummary && !record?.partner) {
    return report ? { relationshipReport: report } : null;
  }
  const dasha = deep.dasha ? {
    level: deep.dasha.level || 'saved',
    label: deep.dasha.label || 'Dasha 同步',
    note: deep.dasha.note || '-',
    self: typeof deep.dasha.self === 'object' ? deep.dasha.self : { label: deep.dasha.self || '-' },
    partner: typeof deep.dasha.partner === 'object' ? deep.dasha.partner : { label: deep.dasha.partner || '-' },
  } : null;
  const kuja = deep.kuja ? {
    verdict: deep.kuja.verdict || 'balanced',
    label: deep.kuja.label || 'Kuja Dosha',
    note: deep.kuja.note || '-',
    self: typeof deep.kuja.self === 'object' ? deep.kuja.self : { levelLabel: deep.kuja.self || '-', marsHouse: '-', marsSign: '-' },
    partner: typeof deep.kuja.partner === 'object' ? deep.kuja.partner : { levelLabel: deep.kuja.partner || '-', marsHouse: '-', marsSign: '-' },
  } : null;
  return {
    partnerSummary: deep.partnerSummary || record.partner || {},
    dasha,
    kuja,
    comparison: normalizeReplayComparison(deep.comparison || record.comparison),
    spouseStatus: normalizeReplaySpouseStatus(deep.spouseStatus || record.spouseStatus),
    ulDkTiming: normalizeReplayULDKTiming(deep.ulDkTiming || record.ulDkTiming),
    selfD9: normalizeReplayD9(deep.selfD9 || deep.d9?.self),
    partnerD9: normalizeReplayD9(deep.partnerD9 || deep.d9?.partner),
    relationshipReport: report,
  };
}

function normalizeReplayComparison(comparison) {
  if (!comparison) return null;
  return {
    axes: Array.isArray(comparison.axes) ? comparison.axes : [],
    rows: Array.isArray(comparison.rows) ? comparison.rows : [],
    compositeStyle: Array.isArray(comparison.compositeStyle) ? comparison.compositeStyle : [],
  };
}

function normalizeReplaySpouseStatus(spouseStatus) {
  if (!spouseStatus) return null;
  const normalize = item => item ? {
    ascSign: item.ascSign || '',
    seventhSign: item.seventhSign || '',
    seventhLord: item.seventhLord || '',
    lagnaLord: item.lagnaLord || '',
    score: item.score ?? 0,
    level: item.level || 'low',
    verdict: item.verdict || '未见明显高地位配偶 Yoga',
    evidence: Array.isArray(item.evidence) ? item.evidence : [],
  } : null;
  return {
    self: normalize(spouseStatus.self),
    partner: normalize(spouseStatus.partner),
  };
}

function normalizeReplayULDKTiming(ulDkTiming) {
  if (!ulDkTiming) return null;
  const normalize = item => item ? {
    dk7: item.dk7 || null,
    dk8: item.dk8 || null,
    ul: item.ul || null,
    dasha: item.dasha || null,
    triggers: Array.isArray(item.triggers) ? item.triggers : [],
    level: item.level || 'low',
    summary: item.summary || 'UL/DK 时机待补充',
    evidence: Array.isArray(item.evidence) ? item.evidence : [],
  } : null;
  return {
    self: normalize(ulDkTiming.self),
    partner: normalize(ulDkTiming.partner),
  };
}

function normalizeReplayD9(snapshot) {
  if (!snapshot) return null;
  return {
    score: snapshot.score ?? '-',
    zone: typeof snapshot.zone === 'object' ? snapshot.zone : { name: snapshot.zone || '保存摘要' },
    core: snapshot.core || [],
    positives: snapshot.positives || [],
    risks: snapshot.risks || [],
  };
}

function renderSynastryPairWorkspace() {
  const container = $('synastry-pair-workspace');
  if (!container) return;
  const lib = sortSynastryPairLibrary(readSynastryPairLibrary());
  if (!lib.length) {
    container.innerHTML = '<div class="synastry-pair-empty">暂无保存配对记录。完成一次完整合盘后可保存当前结果。</div>';
    return;
  }
  container.innerHTML = `
    <div class="synastry-pair-head">
      <strong>保存配对记录</strong>
      <span>${lib.length} 组</span>
    </div>
    <div class="synastry-pair-list">
      ${lib.slice(0, 3).map(record => `
        <div class="synastry-pair-row">
          <div>
            <strong>${escapeHtml(record.label || record.id || '未命名配对')}</strong>
            <span>${escapeHtml(record.score?.total ?? 0)} / ${escapeHtml(record.score?.max ?? 36)} · ${escapeHtml(record.verdict || '-')}</span>
            <small>${escapeHtml(formatSavedAt(record.updatedAt || record.generatedAt))}</small>
          </div>
          <div class="case-row-actions">
            <button type="button" class="mini-action" data-action="workspace-open-pair" data-case-id="${escapeAttr(record.id || '')}">打开</button>
            <button type="button" class="mini-action danger" data-action="workspace-delete-pair" data-case-id="${escapeAttr(record.id || '')}">删除</button>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

function renderSynastryDeepResult(deep) {
  const cards = [
    deep.partnerSummary ? renderSynastryPartnerSummary(deep.partnerSummary) : '',
    deep.dasha ? renderSynastryDashaCard(deep.dasha) : '',
    deep.kuja ? renderSynastryKujaCard(deep.kuja) : '',
  ].filter(Boolean).join('');
  const d9Cards = [
    deep.selfD9 ? renderSynastryD9Card('本人 D9', deep.selfD9) : '',
    deep.partnerD9 ? renderSynastryD9Card('对方 D9', deep.partnerD9) : '',
  ].filter(Boolean).join('');
  return `
    ${renderBiWheelComparisonView(deep.comparison)}
    ${renderULDKTimingComparison(deep.ulDkTiming)}
    ${renderSpouseStatusComparison(deep.spouseStatus)}
    ${cards ? `<div class="synastry-deep-grid">${cards}</div>` : ''}
    ${d9Cards ? `<div class="synastry-d9-compare">${d9Cards}</div>` : ''}
  `;
}

function renderULDKTimingComparison(ulDkTiming) {
  if (!ulDkTiming?.self && !ulDkTiming?.partner) return '';
  return `
    <div class="uldk-timing-comparison">
      <div class="uldk-timing-head">
        <strong>UL/DK 与关系时机</strong>
        <span>Jaimini · Dasha trigger</span>
      </div>
      <div class="uldk-timing-grid">
        ${renderULDKTimingCard('本人', ulDkTiming.self)}
        ${renderULDKTimingCard('对方', ulDkTiming.partner)}
      </div>
    </div>
  `;
}

function renderULDKTimingCard(label, item) {
  if (!item) {
    return `
      <div class="uldk-timing-card uldk-timing-low">
        <strong>${escapeHtml(label)}</strong>
        <p>缺少 Jaimini/运限数据，暂无法判断。</p>
      </div>
    `;
  }
  const triggers = (item.triggers || []).slice(0, 4);
  return `
    <div class="uldk-timing-card uldk-timing-${escapeAttr(item.level || 'low')}">
      <strong>${escapeHtml(label)} · ${escapeHtml(item.summary || 'UL/DK 时机待补充')}</strong>
      <p>DK7 ${escapeHtml(formatDKPoint(item.dk7))} · DK8 ${escapeHtml(formatDKPoint(item.dk8))}</p>
      <p>UL ${escapeHtml(formatULPoint(item.ul))} · 当前 ${escapeHtml(item.dasha?.label || '-')}</p>
      <ul>
        ${(triggers.length ? triggers : ['当前运限未明显触发 DK/UL，需要结合行运和现实进展。']).map(text => `<li>${escapeHtml(text)}</li>`).join('')}
      </ul>
    </div>
  `;
}

function formatDKPoint(point) {
  if (!point) return '待补充';
  return `${planetName(point.planet || '')}${point.sign ? ` ${signName(point.sign)}` : ''}${point.house ? ` H${point.house}` : ''}`;
}

function formatULPoint(point) {
  if (!point) return '待补充';
  return `${signName(point.sign || '')}${point.pada_house ? ` H${point.pada_house}` : ''}${point.lord ? ` · 主 ${planetName(point.lord)}` : ''}`;
}

function renderSpouseStatusComparison(spouseStatus) {
  if (!spouseStatus?.self && !spouseStatus?.partner) return '';
  return `
    <div class="spouse-status-comparison">
      <div class="spouse-status-head">
        <strong>配偶/婚后成长 Yoga</strong>
        <span>spouse_status_yoga.py</span>
      </div>
      <div class="spouse-status-grid">
        ${renderSpouseStatusCard('本人', spouseStatus.self)}
        ${renderSpouseStatusCard('对方', spouseStatus.partner)}
      </div>
    </div>
  `;
}

function renderSpouseStatusCard(label, item) {
  if (!item) {
    return `
      <div class="spouse-status-card spouse-status-low">
        <strong>${escapeHtml(label)}</strong>
        <p>缺少出生盘数据，暂无法判断。</p>
      </div>
    `;
  }
  return `
    <div class="spouse-status-card spouse-status-${escapeAttr(item.level || 'low')}">
      <strong>${escapeHtml(label)} · ${escapeHtml(item.verdict || '-')}</strong>
      <p>7宫 ${escapeHtml(signName(item.seventhSign || ''))} · 7主 ${escapeHtml(planetName(item.seventhLord || ''))} · ${escapeHtml(item.score ?? 0)} / 5</p>
      <ul>
        ${(item.evidence || []).slice(0, 4).map(text => `<li>${escapeHtml(text)}</li>`).join('')}
      </ul>
    </div>
  `;
}

function renderRelationshipReport(report = {}) {
  const evidence = Array.isArray(report.evidence) ? report.evidence : [];
  return `
    <div class="relationship-report-template relationship-report-${escapeAttr(report.status || 'needs_context')}">
      <div class="relationship-report-head">
        <div>
          <strong>关系报告模板</strong>
          <p>${escapeHtml(report.headline || '合盘报告需要结合完整星盘、D9、Kuja 与 Dasha 复核。')}</p>
        </div>
        <span class="relationship-report-status">${escapeHtml(report.statusLabel || '需谨慎综合判断')}</span>
      </div>
      <div class="relationship-report-grid">
        ${evidence.map(item => `
          <div class="relationship-evidence-card">
            <span>${escapeHtml(item.label || '-')}</span>
            <strong>${escapeHtml(item.value || '-')}</strong>
            <small>${escapeHtml(item.note || '-')}</small>
          </div>
        `).join('')}
      </div>
      <div class="relationship-report-sections">
        ${renderRelationshipReportList('支持证据', report.strengths)}
        ${renderRelationshipReportList('需要观察', report.risks)}
        ${renderRelationshipReportList('下一步', report.nextSteps)}
      </div>
      <div class="relationship-report-boundary">
        ${(report.boundaries || []).map(item => `<span>${escapeHtml(item)}</span>`).join('')}
      </div>
    </div>
  `;
}

function renderRelationshipReportList(label, items = []) {
  const list = Array.isArray(items) && items.length ? items : ['暂无可展示条目。'];
  return `
    <div class="relationship-report-section">
      <strong>${escapeHtml(label)}</strong>
      <ul class="relationship-report-list">
        ${list.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
      </ul>
    </div>
  `;
}

function renderBiWheelComparisonView(comparison) {
  if (!comparison || (!comparison.axes?.length && !comparison.rows?.length)) return '';
  return `
    <div class="biwheel-comparison-view">
      <div class="biwheel-comparison-head">
        <strong>双人比较视图</strong>
        <span>bi-wheel / composite-style</span>
      </div>
      <div class="biwheel-axis-grid">
        ${(comparison.axes || []).map(row => `
          <div class="biwheel-axis-card biwheel-tone-${escapeAttr(row.relation?.tone || 'neutral')}">
            <span>${escapeHtml(row.label || '-')}</span>
            <strong>${escapeHtml(row.relation?.label || '-')}</strong>
            <p>本人 ${escapeHtml(row.self?.label || '-')} · 对方 ${escapeHtml(row.partner?.label || '-')}</p>
            <small>${escapeHtml(row.theme || '-')}</small>
          </div>
        `).join('')}
      </div>
      <div class="biwheel-table-wrap">
        <table class="biwheel-comparison-table">
          <thead><tr><th>行星</th><th>本人</th><th>对方</th><th>互动</th><th>Overlay</th></tr></thead>
          <tbody>
            ${(comparison.rows || []).map(row => `
              <tr>
                <td>${escapeHtml(row.label || row.planet || '-')}</td>
                <td>${escapeHtml(row.self?.label || '-')}</td>
                <td>${escapeHtml(row.partner?.label || '-')}</td>
                <td>${escapeHtml(row.relation?.label || '-')}</td>
                <td>对方落本人${escapeHtml(row.partnerOverlayHouse || '-')}宫 / 本人落对方${escapeHtml(row.selfOverlayHouse || '-')}宫</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
      ${renderCompositeStyleStrip(comparison.compositeStyle)}
    </div>
  `;
}

function renderCompositeStyleStrip(items = []) {
  if (!Array.isArray(items) || !items.length) return '';
  return `
    <div class="composite-style-strip">
      ${items.map(item => `
        <div>
          <span>${escapeHtml(item.label || '-')} midpoint</span>
          <strong>${escapeHtml(signName(item.sign || ''))} ${escapeHtml(formatDegreeInSign(item.degree))}</strong>
          <small>${escapeHtml(item.note || '-')}</small>
        </div>
      `).join('')}
    </div>
  `;
}

function renderSynastryPartnerSummary(summary = {}) {
  return `
    <div class="synastry-deep-card">
      <strong>对方星盘摘要</strong>
      <p>上升：${escapeHtml(summary.ascendant || '-')}</p>
      <p>月亮：${escapeHtml(summary.moon || '-')} · ${escapeHtml(summary.nakshatra || '-')}</p>
      <p>当前运限：${escapeHtml(summary.dasha || '-')}</p>
    </div>
  `;
}

function renderSynastryDashaCard(dasha) {
  return `
    <div class="synastry-deep-card synastry-dasha-${escapeAttr(dasha.level)}">
      <strong>${escapeHtml(dasha.label)}</strong>
      <p>本人：${escapeHtml(dasha.self.label)}</p>
      <p>对方：${escapeHtml(dasha.partner.label)}</p>
      <small>${escapeHtml(dasha.note)}</small>
    </div>
  `;
}

function renderSynastryKujaCard(kuja) {
  return `
    <div class="synastry-deep-card synastry-kuja-${escapeAttr(kuja.verdict)}">
      <strong>${escapeHtml(kuja.label)}</strong>
      <p>本人：${escapeHtml(kuja.self.levelLabel)} · Mars ${escapeHtml(kuja.self.marsHouse)}宫 ${escapeHtml(signName(kuja.self.marsSign))}</p>
      <p>对方：${escapeHtml(kuja.partner.levelLabel)} · Mars ${escapeHtml(kuja.partner.marsHouse)}宫 ${escapeHtml(signName(kuja.partner.marsSign))}</p>
      <small>${escapeHtml(kuja.note)}</small>
    </div>
  `;
}

function renderSynastryD9Card(label, report) {
  if (!report) {
    return `
      <div class="synastry-deep-card">
        <strong>${escapeHtml(label)}</strong>
        <p>D9 信息不足，请确认出生时间精度。</p>
      </div>
    `;
  }
  const core = (report.core || []).slice(0, 2).map(item => `<p>${escapeHtml(item.label)}：${escapeHtml(item.value)}</p>`).join('');
  const risks = (report.risks || []).map(flag => escapeHtml(flag.name)).join('、') || '无明显红旗';
  const positives = (report.positives || []).map(flag => escapeHtml(flag.name)).join('、') || '暂无突出绿旗';
  return `
    <div class="synastry-deep-card synastry-d9-card">
      <div class="synastry-d9-head">
        <strong>${escapeHtml(label)}</strong>
        <span>${escapeHtml(report.zone.name)} · ${escapeHtml(report.score)} / 8</span>
      </div>
      ${core}
      <small>绿旗：${positives}</small>
      <small>风险：${risks}</small>
    </div>
  `;
}

function renderPartnerDetails(label, details = {}) {
  return `
    <div class="synastry-person">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(details.moon_sign || '-')} · ${escapeHtml(details.nakshatra || '-')}${details.nakshatra_pada ? ` P${escapeHtml(details.nakshatra_pada)}` : ''}</span>
      <small>Gana ${escapeHtml(details.gana || '-')} · Nadi ${escapeHtml(details.nadi || '-')} · Yoni ${escapeHtml(details.yoni || '-')}</small>
    </div>
  `;
}

function kutaMax(name) {
  return {
    Varna: 1,
    Vashya: 2,
    Tara: 3,
    Yoni: 4,
    GrahaMaitri: 5,
    Gana: 6,
    Bhakoot: 7,
    Nadi: 8,
  }[name] ?? '-';
}

// ============================================================================
// Prashna 问事 Tab 渲染
// ============================================================================
function renderPrashnaTab(chartData) {
  const category = $('prashna-category');
  const question = $('prashna-question');
  const result = $('prashna-result');
  const runBtn = $('btn-run-prashna');
  if (!category || !question || !result || !runBtn) return;
  renderPrashnaCaseWorkspace();
  setupPrashnaCaseActions();

  if (!runBtn.dataset.bound) {
    runBtn.dataset.bound = 'true';
    runBtn.addEventListener('click', async () => {
      const questionText = question.value.trim();
      const questionType = category.value || 'general';
      if (questionText.length > 120) {
        result.innerHTML = '<p class="prashna-error">问题请控制在 120 字以内。</p>';
        return;
      }
      result.innerHTML = '<p>正在铸造 Prashna 问事盘...</p>';
      try {
        const data = await window.JyotishAPI?.computePrashna?.({
          question: questionType,
          question_text: questionText,
          planets: chartData?.planets || {},
          asc_degree: chartData?.ascendant?.lon ?? chartData?.ascendant?.degree ?? 15.5,
          horary_number: chartData?.kp_horary?.horary_number || '',
        });
        if (!data) throw new Error('本地 API 未返回结果');
        recordPrashnaWorkflow(data, questionText, questionType);
        _lastPrashnaCaseRecord = buildPrashnaCaseRecord(data, questionText, questionType);
        result.innerHTML = renderPrashnaResult(data, questionText);
        renderPrashnaCaseWorkspace();
        bindTerms(result);
      } catch (e) {
        result.innerHTML = renderInlineAPIError('prashna-error', '问事计算暂不可用', e);
      }
    });
  }
}

function ensureClientWorkflows() {
  const active = getActiveChartData();
  if (!active) return null;
  if (!active._client_workflows || typeof active._client_workflows !== 'object') {
    active._client_workflows = {};
  }
  return active._client_workflows;
}

function recordSynastryWorkflow(data, deep = null, options = {}) {
  const workflows = ensureClientWorkflows();
  if (!workflows) return;
  const relationshipReport = deep?.relationshipReport || data.relationship_report || buildRelationshipReportTemplate(data, deep);
  workflows.synastry = {
    mode: options.mode || 'synastry',
    generatedAt: new Date().toISOString(),
    total_score: data.total_score ?? 0,
    max_score: data.max_score ?? 36,
    match_percentage: data.match_percentage ?? ((Number(data.total_score || 0) / Number(data.max_score || 36)) * 100),
    is_match_approved: data.is_match_approved ?? data.is_approved ?? false,
    scores: data.scores || {},
    exceptions: data.exceptions || [],
    male_details: data.male_details || data.male || {},
    female_details: data.female_details || data.female || {},
    relationship_report: relationshipReport,
    deep: deep ? normalizeSynastryDeepForExport({ ...deep, relationshipReport }) : null,
  };
}

function normalizeSynastryDeepForExport(deep) {
  return {
    partnerSummary: deep.partnerSummary || {},
    relationshipReport: deep.relationshipReport || null,
    comparison: deep.comparison ? normalizeReplayComparison(deep.comparison) : null,
    spouseStatus: deep.spouseStatus ? normalizeReplaySpouseStatus(deep.spouseStatus) : null,
    dasha: deep.dasha ? {
      label: deep.dasha.label,
      note: deep.dasha.note,
      self: deep.dasha.self?.label || '-',
      partner: deep.dasha.partner?.label || '-',
    } : null,
    kuja: deep.kuja ? {
      label: deep.kuja.label,
      note: deep.kuja.note,
      self: deep.kuja.self?.levelLabel || '-',
      partner: deep.kuja.partner?.levelLabel || '-',
    } : null,
    d9: {
      self: deep.selfD9 ? { score: deep.selfD9.score, zone: deep.selfD9.zone?.name || '' } : null,
      partner: deep.partnerD9 ? { score: deep.partnerD9.score, zone: deep.partnerD9.zone?.name || '' } : null,
    },
  };
}

function recordPrashnaWorkflow(data, questionText, questionType) {
  const workflows = ensureClientWorkflows();
  if (!workflows) return;
  workflows.prashna = {
    generatedAt: new Date().toISOString(),
    question_text: questionText || '',
    question_type: questionType || 'general',
    summary: data.summary || {},
    prashna_chart: data.prashna_chart || {},
    kp_horary: data.kp_horary || {},
    kp_answer_v2: data.kp_answer_v2 || data.kp_answer || {},
    kp_answer: data.kp_answer || {},
    arudha: data.arudha || {},
    nadi: data.nadi || {},
    timing: data.timing || {},
    sphutas: data.sphutas || {},
    life_sphutas: data.life_sphutas || {},
    sahams: data.sahams || {},
    lost_item: data.lost_item || {},
    kunda: data.kunda || {},
  };
}

function buildPrashnaCaseRecord(data, questionText, questionType) {
  const now = new Date().toISOString();
  const summary = data.summary || {};
  const answer = data.kp_answer_v2 || data.kp_answer || {};
  const chart = data.prashna_chart || {};
  const conclusion = summary.conclusion || answer.kp_answer || 'MAYBE — 需要更多信息确认';
  const questionLabel = questionText || questionType || 'Prashna';
  return {
    id: `${buildWorkspaceChartId(getActiveChartData()) || 'chart'}__prashna__${now.replace(/[:.]/g, '-')}`,
    label: `${questionLabel.slice(0, 42)} · ${conclusion}`,
    group: '研究',
    relation: 'research',
    tags: ['prashna', questionType || 'general'],
    generatedAt: now,
    updatedAt: now,
    chartId: buildWorkspaceChartId(getActiveChartData()),
    chartLabel: buildWorkspaceChartLabel(getActiveChartData()),
    question_text: questionText || '',
    question_type: questionType || 'general',
    conclusion,
    confidence: summary.confidence || answer.confidence || '中',
    primary_house: answer.primary_house || summary.primary_house || '',
    kp_horary: data.kp_horary || {},
    horary_number: data.kp_horary?.horary_number || '',
    sub_lord: answer.kp_sub_lord || '',
    asc: chart.asc_sign ? `${chart.asc_sign} ${chart.asc_degree ?? ''}`.trim() : '',
    next_action: summary.next_action || data.timing?.recommendation || '',
    data,
  };
}

function renderPrashnaCaseActions() {
  return `
    <div class="prashna-case-actions">
      <button type="button" class="btn-secondary" data-action="save-prashna-case">保存问事案例</button>
      <button type="button" class="btn-secondary" data-action="export-prashna-case">导出当前问事</button>
    </div>
  `;
}

function setupPrashnaCaseActions() {
  const result = $('prashna-result');
  if (result && result.dataset.caseActionsBound !== 'true') {
    result.dataset.caseActionsBound = 'true';
    result.addEventListener('click', event => {
      const btn = event.target.closest('[data-action="save-prashna-case"], [data-action="export-prashna-case"]');
      if (!btn) return;
      if (btn.dataset.action === 'save-prashna-case') saveCurrentPrashnaCase();
      if (btn.dataset.action === 'export-prashna-case') exportCurrentPrashnaCase();
    });
  }
  const workspace = $('prashna-case-workspace');
  if (!workspace || workspace.dataset.caseWorkspaceBound === 'true') return;
  workspace.dataset.caseWorkspaceBound = 'true';
  workspace.addEventListener('click', event => {
    const btn = event.target.closest('.mini-action');
    if (!btn) return;
    if (btn.dataset.action === 'workspace-open-prashna') openSavedPrashnaCase(btn.dataset.caseId || '');
    if (btn.dataset.action === 'workspace-delete-prashna') deleteSavedPrashnaCase(btn.dataset.caseId || '');
  });
}

function saveCurrentPrashnaCase() {
  if (!_lastPrashnaCaseRecord) return;
  const now = new Date().toISOString();
  const lib = readPrashnaCaseLibrary();
  const existing = lib.find(record => record?.id === _lastPrashnaCaseRecord.id);
  if (existing) {
    Object.assign(existing, _lastPrashnaCaseRecord, { updatedAt: now, generatedAt: existing.generatedAt || now });
  } else {
    lib.push({ ..._lastPrashnaCaseRecord, generatedAt: now, updatedAt: now });
  }
  writePrashnaCaseLibrary(sortCaseLibrary(lib).slice(0, 80));
  renderPrashnaCaseWorkspace();
}

function exportCurrentPrashnaCase() {
  if (!_lastPrashnaCaseRecord) return;
  const safeId = String(_lastPrashnaCaseRecord.id || 'prashna').replace(/[^a-z0-9_-]+/gi, '-');
  downloadText(JSON.stringify(_lastPrashnaCaseRecord, null, 2), `jyotish-prashna-${safeId}.json`, 'application/json;charset=utf-8');
}

function renderPrashnaCaseWorkspace() {
  const container = $('prashna-case-workspace');
  if (!container) return;
  const lib = sortCaseLibrary(readPrashnaCaseLibrary());
  if (!lib.length) {
    container.innerHTML = '<div class="prashna-case-empty">暂无保存问事案例。完成一次问事分析后可保存当前结果。</div>';
    return;
  }
  container.innerHTML = `
    <div class="prashna-case-head">
      <strong>保存问事案例</strong>
      <span>${lib.length} 条</span>
    </div>
    <div class="prashna-case-list">
      ${lib.slice(0, 4).map(record => `
        <div class="prashna-case-row">
          <div>
            <strong>${escapeHtml(record.question_text || record.question_type || '未命名问事')}</strong>
            <span>${escapeHtml(record.conclusion || '-')} · ${escapeHtml(record.confidence || '-')}</span>
            <small>${escapeHtml(formatSavedAt(record.updatedAt || record.generatedAt))}</small>
          </div>
          <div class="case-row-actions">
            <button type="button" class="mini-action" data-action="workspace-open-prashna" data-case-id="${escapeAttr(record.id || '')}">打开</button>
            <button type="button" class="mini-action danger" data-action="workspace-delete-prashna" data-case-id="${escapeAttr(record.id || '')}">删除</button>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

function renderPrashnaResult(data, questionText) {
  const chart = data.prashna_chart || {};
  const answer = data.kp_answer_v2 || data.kp_answer || {};
  const oldAnswer = data.kp_answer || {};
  const arudha = data.arudha || {};
  const nadi = data.nadi || {};
  const timing = data.timing || {};
  const summary = data.summary || {};
  const answerText = summary.conclusion || answer.kp_answer || oldAnswer.kp_answer || 'MAYBE — 需要更多信息确认';
  const tone = answerText.includes('YES') ? 'prashna-yes' : answerText.includes('NO') ? 'prashna-no' : 'prashna-maybe';
  const planetRows = Object.entries(chart.planet_houses || {}).map(([planet, house]) => `
    <tr><td>${escapeHtml(planet)}</td><td>${escapeHtml(house)}宫</td></tr>
  `).join('');
  const factors = (timing.factors || []).slice(0, 5).map(item => `<li>${escapeHtml(item)}</li>`).join('');
  return `
    <div class="prashna-answer ${tone}">
      <strong>${escapeHtml(answerText)}</strong>
      <span>置信度：${escapeHtml(summary.confidence || answer.confidence || oldAnswer.confidence || '中')}</span>
    </div>
    ${questionText ? `<p class="prashna-question-readout">${escapeHtml(questionText)}</p>` : ''}
    <div class="prashna-grid">
      <div><span>问事上升</span><strong>${escapeHtml(chart.asc_sign || '-')} ${escapeHtml(chart.asc_degree ?? '-')}°</strong></div>
      <div><span>上升主星</span><strong>${escapeHtml(chart.prashna_lagna_lord || '-')}</strong></div>
      <div><span>问题宫</span><strong>${escapeHtml(answer.primary_house || oldAnswer.primary_house || summary.primary_house || '-')}宫</strong></div>
      <div><span>问题宫主</span><strong>${escapeHtml(answer.question_lord || oldAnswer.question_lord || summary.question_lord || '-')}</strong></div>
      <div><span>Sub Lord</span><strong>${escapeHtml(answer.kp_sub_lord || '-')}</strong></div>
      <div><span>Karaka</span><strong>${escapeHtml(answer.karaka || oldAnswer.karaka || '-')}</strong></div>
    </div>
    <div class="prashna-insight-grid">
      <div class="prashna-note">
        <strong>KP 三层判定</strong>
        <p>${escapeHtml(answer.reason || oldAnswer.note || '基于问题宫、宫主与 KP Prashna 信号综合判断。')}</p>
        ${answer.timing_note ? `<small>${escapeHtml(answer.timing_note)}</small>` : ''}
      </div>
      <div class="prashna-note">
        <strong>Arudha 镜像</strong>
        <p>问题宫 ${escapeHtml(arudha.question_house || '-')}，宫主 ${escapeHtml(arudha.lord || '-')} 落 ${escapeHtml(arudha.lord_house || '-')}宫，镜像点在 ${escapeHtml(arudha.arudha_house || '-')}宫。</p>
        <small>${escapeHtml(arudha.note || 'Arudha 用于观察问题背后的真实关注点。')}</small>
      </div>
      <div class="prashna-note">
        <strong>Nadi 侧写</strong>
        <p>${escapeHtml(nadi.moon_jupiter_relation || '-')}</p>
        <small>${escapeHtml(nadi.nadi_interpretation || '').replace(/\n/g, ' / ')}</small>
      </div>
      <div class="prashna-note">
        <strong>时机评分</strong>
        <p>${escapeHtml(timing.score ?? '-')} / 100 · ${escapeHtml(timing.rating || '-')}</p>
        ${factors ? `<ul>${factors}</ul>` : ''}
      </div>
    </div>
    ${planetRows ? `<div class="prashna-table-wrap"><table class="prashna-table"><thead><tr><th>行星</th><th>问事宫位</th></tr></thead><tbody>${planetRows}</tbody></table></div>` : ''}
    ${renderKPHoraryEvidence(data.kp_horary || {})}
    ${renderPrashnaAdvancedEvidence(data)}
    ${renderPrashnaCaseActions()}
    <div class="prashna-next-action">${escapeHtml(summary.next_action || timing.recommendation || '把这个结论与现实证据交叉验证后再行动。')}</div>
    <p class="prashna-boundary">Prashna 适合回答具体、单一、当下的问题。重大决定仍需结合出生盘、大运、过境和现实信息，不应只凭单次问事结论行动。</p>
  `;
}

function renderKPHoraryEvidence(kpHorary = {}) {
  const ruling = kpHorary.ruling_planets || {};
  const cusp = kpHorary.cuspal_sub_lord || {};
  const question = kpHorary.question_houses || {};
  const significators = kpHorary.house_significators || {};
  const judgement = kpHorary.judgement_matrix || [];
  const sigRows = Object.entries(significators).map(([house, sig]) => `
    <tr>
      <td>H${escapeHtml(house)}</td>
      <td>${escapeHtml(formatKPList(sig.A))}</td>
      <td>${escapeHtml(formatKPList(sig.B))}</td>
      <td>${escapeHtml(formatKPList(sig.C))}</td>
      <td>${escapeHtml(formatKPList(sig.D))}</td>
    </tr>
  `).join('');
  const judgementCards = judgement.map(row => `
    <div>
      <span>H${escapeHtml(row.house)} · ${escapeHtml(row.role || '-')}</span>
      <strong>${escapeHtml(row.signal || '-')}</strong>
      <small>score ${escapeHtml(row.score ?? '-')}</small>
    </div>
  `).join('');
  if (!kpHorary.method && !sigRows && !judgementCards) return '';
  return `
    <details class="prashna-advanced kp-horary-evidence" open>
      <summary>KP Horary：Ruling Planets / Sub Lord / Significators</summary>
      <div class="prashna-advanced-grid">
        <div class="prashna-advanced-card">
          <strong>Ruling Planets</strong>
          <p>Asc ${escapeHtml(ruling.ascendant_lord || '-')} · Moon Star ${escapeHtml(ruling.moon_star_lord || '-')}</p>
          <small>Moon Sub ${escapeHtml(ruling.moon_sub_lord || '-')} · Horary ${escapeHtml(kpHorary.horary_number || '-')}</small>
        </div>
        <div class="prashna-advanced-card">
          <strong>Cuspal Sub Lord</strong>
          <p>H${escapeHtml(cusp.house || question.primary || '-')} · ${escapeHtml(cusp.kp_lords?.sub_lord || '-')}</p>
          <small>Star ${escapeHtml(cusp.kp_lords?.nakshatra_lord || '-')} · Sub-Sub ${escapeHtml(cusp.kp_lords?.sub_sub_lord || '-')}</small>
        </div>
        <div class="prashna-advanced-card">
          <strong>Question Houses</strong>
          <p>Primary H${escapeHtml(question.primary || '-')} · ${escapeHtml(formatKPList(question.secondary))}</p>
          <small>Karaka ${escapeHtml(question.karaka || '-')}</small>
        </div>
        <div class="prashna-advanced-card">
          <strong>Judgement Matrix</strong>
          <div class="prashna-mini-grid">${judgementCards || '<p>暂无 judgement_matrix。</p>'}</div>
        </div>
      </div>
      ${sigRows ? `<div class="prashna-table-wrap"><table class="prashna-table"><thead><tr><th>宫</th><th>A</th><th>B</th><th>C</th><th>D</th></tr></thead><tbody>${sigRows}</tbody></table></div>` : ''}
      <p class="prashna-boundary">${escapeHtml(kpHorary.next_action || '用 KP Horary 证据复核结论，不单独替代出生盘和现实信息。')}</p>
    </details>
  `;
}

function renderPrashnaAdvancedEvidence(data = {}) {
  const sphutas = data.sphutas || {};
  const life = data.life_sphutas || {};
  const sahams = data.sahams || {};
  const lost = data.lost_item || {};
  const kunda = data.kunda || {};
  const points = ['trisphuta', 'catusphuta', 'pancasphuta']
    .map(key => sphutas[key])
    .filter(Boolean)
    .map(point => `<div><span>${escapeHtml(point.name)}</span><strong>${escapeHtml(point.sign)} · ${escapeHtml(point.house)}宫</strong><small>${escapeHtml(point.longitude)}°</small></div>`)
    .join('');
  const sahamCards = (sahams.points || []).slice(0, 6)
    .map(point => `<div><span>${escapeHtml(point.note || point.name)}</span><strong>${escapeHtml(point.sign)} · ${escapeHtml(point.house)}宫</strong><small>${escapeHtml(point.name)} ${escapeHtml(point.longitude)}°</small></div>`)
    .join('');
  return `
    <details class="prashna-advanced">
      <summary>进阶证据：Sphuta / Saham / 失物 / Kunda</summary>
      <div class="prashna-advanced-grid">
        <div class="prashna-advanced-card">
          <strong>Sphuta 组合</strong>
          <div class="prashna-mini-grid">${points || '<p>暂无 Sphuta 数据。</p>'}</div>
        </div>
        <div class="prashna-advanced-card">
          <strong>Prana / Deha / Mrityu</strong>
          <p>${escapeHtml(life.signal || '-')}</p>
          <small>${escapeHtml(life.note || '生命点仅作压力提示。')}</small>
        </div>
        <div class="prashna-advanced-card">
          <strong>失物线索</strong>
          <p>${escapeHtml(lost.summary || '-')}</p>
          <small>${escapeHtml(lost.likely_direction || '-')}</small>
        </div>
        <div class="prashna-advanced-card">
          <strong>Kunda 验证</strong>
          <p>${escapeHtml(kunda.nakshatra || '-')} P${escapeHtml(kunda.pada || '-')} · ${escapeHtml(kunda.strength || '-')}</p>
          <small>${escapeHtml(kunda.note || '')}</small>
        </div>
      </div>
      <div class="prashna-saham-strip">${sahamCards || '<p>暂无 Saham 数据。</p>'}</div>
    </details>
  `;
}

// ============================================================================
// KP Tab 渲染  
// ============================================================================
function renderKPTab(chartData) {
  const sec = document.getElementById('kp-section');
  if (!sec) return;
  const ext = chartData._extended;
  if (!ext?.kp?.houses) {
    sec.innerHTML = '<p style="text-align:center;color:#999;padding:40px">KP分析将在API返回后展示</p>';
    return;
  }

  const focus = window.__kpFocus || 'career';
  const domains = kpDomains();
  const domain = domains[focus] || domains.career;
  const focusRows = domain.houses.map(h => renderKPHouseCard(h, ext.kp.houses[h], true)).join('');
  const otherRows = Array.from({ length: 12 }, (_, i) => i + 1)
    .filter(h => !domain.houses.includes(h))
    .map(h => renderKPHouseCard(h, ext.kp.houses[h], false))
    .join('');
  const planets = ext.kp.planets || {};
  const planetRows = Object.entries(planets).slice(0, 9).map(([pn, pd]) => {
    const kl = pd.kp_lords || {};
    const sig = pd.significators || {};
    return `
      <tr>
        <td>${escapeHtml(planetName(pn))}</td>
        <td>${escapeHtml(kl.nakshatra || '-')}</td>
        <td>${escapeHtml(kl.sub_lord || '-')}</td>
        <td>${escapeHtml(kl.sub_sub_lord || '-')}</td>
        <td>${escapeHtml(formatKPList(sig.A))}</td>
        <td>${escapeHtml(formatKPList(sig.B))}</td>
      </tr>
    `;
  }).join('');

  sec.innerHTML = `
    <div class="kp-dashboard">
      <div class="kp-head">
        <div>
          <h4>KP Sublord 事件判断</h4>
          <p>用 ABCD significator 看具体问题是否容易兑现：A/B 权重更高，C/D 作背景补充。</p>
        </div>
        <select id="kp-focus-select" class="kp-focus-select">
          ${Object.entries(domains).map(([key, item]) => `<option value="${escapeAttr(key)}" ${key === focus ? 'selected' : ''}>${escapeHtml(item.label)}</option>`).join('')}
        </select>
      </div>
      <div class="kp-verdict">
        <strong>${escapeHtml(domain.label)}</strong>
        <p>${escapeHtml(domain.note)}</p>
        <small>重点宫位：${domain.houses.map(h => `${h}宫`).join(' / ')}</small>
      </div>
      <div class="kp-house-grid kp-focus-grid">${focusRows}</div>
      <details class="kp-all-houses">
        <summary>查看全部 12 宫 KP Significator</summary>
        <div class="kp-house-grid">${otherRows}</div>
      </details>
      <div class="kp-table-wrap">
        <table class="kp-table">
          <thead><tr><th>行星</th><th>Nakshatra</th><th>Sub</th><th>Sub-Sub</th><th>A</th><th>B</th></tr></thead>
          <tbody>${planetRows}</tbody>
        </table>
      </div>
      <p class="kp-boundary">KP 适合回答边界清楚的事件问题。先选问题域，再看对应宫位的强 significator；不要把全盘 KP 表当作泛性格解读。</p>
    </div>
  `;

  const select = document.getElementById('kp-focus-select');
  if (select && !select.dataset.bound) {
    select.dataset.bound = 'true';
    select.addEventListener('change', () => {
      window.__kpFocus = select.value;
      renderKPTab(chartData);
    });
  }
}

function renderKPHouseCard(house, data = {}, focused = false) {
  const sig = data.significators || {};
  const kp = data.kp_lords || {};
  return `
    <div class="kp-house-card ${focused ? 'kp-house-focus' : ''}">
      <div class="kp-house-title">
        <strong>${escapeHtml(house)}宫 · ${escapeHtml(signName(data.sign || '-'))}</strong>
        <span>${escapeHtml(planetName(kp.sub_lord || ''))}</span>
      </div>
      <p>A ${escapeHtml(formatKPList(sig.A))}</p>
      <p>B ${escapeHtml(formatKPList(sig.B))}</p>
      <small>C ${escapeHtml(formatKPList(sig.C))} · D ${escapeHtml(formatKPList(sig.D))}</small>
    </div>
  `;
}

function formatKPList(value) {
  if (Array.isArray(value)) return value.length ? value.map(item => typeof item === 'number' ? `${item}宫` : planetName(item)).join('、') : '-';
  if (value === null || value === undefined || value === '') return '-';
  return typeof value === 'number' ? `${value}宫` : planetName(value);
}

function kpDomains() {
  return {
    career: { label: '事业/工作', houses: [10, 6, 2, 11], note: '10宫看职位与社会结果，6宫看劳动/竞争，2与11宫看收入和兑现。' },
    relationship: { label: '关系/婚姻', houses: [7, 2, 5, 11], note: '7宫看伴侣与契约，2宫看家庭延续，5宫看恋爱，11宫看愿望兑现。' },
    finance: { label: '财务/收益', houses: [2, 11, 5, 9], note: '2宫现金与储蓄，11宫收益，5宫投机，9宫机会与贵人。' },
    health: { label: '健康/恢复', houses: [1, 6, 8, 12], note: '1宫身体状态，6宫疾病，8宫风险，12宫消耗和住院。' },
    property: { label: '房产/家宅', houses: [4, 2, 11, 12], note: '4宫房产家宅，2/11宫付款与收益，12宫支出和迁移成本。' },
    travel: { label: '旅行/迁移', houses: [3, 9, 12, 4], note: '3宫短途，9宫远行，12宫海外/离开，4宫原居所。' },
    general: { label: '一般问题', houses: [1, 10, 11, 12], note: '一般问题先看问事者、事件结果、愿望兑现与损耗。' },
  };
}

// ============================================================================
// 🔍 验证Tab渲染 (v6.9.0)
// ============================================================================
function renderVerifyTab(chartData) {
  const pastSec = document.getElementById('past-events-result');
  if (pastSec && chartData._extended?.past_events) {
    const pe = chartData._extended.past_events;
    pastSec.innerHTML = `<p style="color:#666;margin-bottom:8px">${escapeHtml(pe.summary || '基于Dasha/Transit反推')}</p>
      ${(pe.events || []).map(e => `<div style="background:#e8f5e9;padding:8px 12px;border-radius:6px;margin:4px 0;font-size:13px">
        <strong>${escapeHtml(e.period || '')}</strong>: ${escapeHtml(e.description || '')} <span style="color:#888">(${escapeHtml(e.confidence || '')})</span></div>`).join('')}`;
  }

  const caseSec = document.getElementById('case-match-result');
  if (caseSec && chartData._extended?.case_matches) {
    const cm = chartData._extended.case_matches;
    caseSec.innerHTML = `<p style="color:#666;margin-bottom:8px">匹配到${cm.length || 0}个相似案例</p>
      ${(cm || []).slice(0,5).map(c => `<div style="background:#e3f2fd;padding:8px 12px;border-radius:6px;margin:4px 0;font-size:13px">
        <strong>${escapeHtml(c.name || '')}</strong>: ${escapeHtml(c.match || '')} <span style="color:#666">吻合度:${escapeHtml(c.accuracy || '?')}</span></div>`).join('')}`;
  }

  const fallSec = document.getElementById('fallacy-warn-result');
  if (fallSec) {
    let warnings = [];
    const interps = chartData._extended?.interpretations || {};
    for (const [k, v] of Object.entries(interps)) {
      if (typeof v === 'string' && (v.includes('毁灭') || v.includes('落陷') || v.includes('必坏'))) {
        warnings.push({text: v.slice(0, 60), fix: '需多配置综合判断'});
      }
    }
    if (warnings.length === 0) warnings.push({text: '未检测到常见误区', fix: ''});
    fallSec.innerHTML = warnings.map(w => `<div style="background:#fff3e0;padding:6px 12px;border-radius:6px;margin:4px 0;font-size:12px">
      ⚠️ ${escapeHtml(w.text)}${w.fix ? ' → '+escapeHtml(w.fix) : ''}</div>`).join('');
  }
}

// ============================================================================
// 🪐 过境对比 Tab渲染 (v6.9.0)
// ============================================================================
async function parseTransitCompareResponse(resp) {
  const raw = await resp.text();
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch (_error) {
    return { error: raw.slice(0, 240) };
  }
}

function buildTransitCompareRecoveryMessage(error) {
  const message = error?.message || String(error || '本地 API 未连接');
  return `过境数据需本地 API 服务：${message}。请到 Trust Center 运行健康检查；如本地 API 未连接，请按 README 的普通用户启动路径启动网页服务和本地 API 服务后重试。`;
}

function buildTransitRenderRecoveryMessage(error) {
  const message = error?.message || String(error || '本地计算异常');
  return `Transit 计算暂不可用：${message}。请到 Trust Center 运行健康检查；如本地 API 或高级计算服务未连接，请按 README 的普通用户启动路径启动网页服务和本地 API 服务后重试。`;
}

function renderTransitCompareTab(chartData) {
  const transitBtn = document.getElementById('btn-run-transit');
  if (!transitBtn) return;
  transitBtn.onclick = async () => {
    const start = document.getElementById('transit-start').value;
    const end = document.getElementById('transit-end').value;
    if (!start || !end) return;
    const rd = document.getElementById('transit-result');
    rd.innerHTML = '<p style="text-align:center;color:#999;padding:20px">搜索过境触发点...</p>';
    try {
      const base = window.JyotishAPI?.apiBase || '';
      const resp = await fetch(`${base}/api/transit`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({start, end, planets: Object.keys(chartData.planets || {}).slice(0, 9)})
      });
      const data = await parseTransitCompareResponse(resp);
      if (!resp.ok || data.success === false) {
        throw new Error(data.error || data.message || `Transit API HTTP ${resp.status}`);
      }
      if (data.triggers?.length) {
        rd.innerHTML = `<p style="color:#666">发现${data.triggers.length}个触发点</p>
          ${data.triggers.slice(0, 20).map(t => `<div style="background:#f9f9f9;padding:6px 12px;border-radius:6px;margin:3px 0;font-size:12px">
            <strong>${escapeHtml(t.planet || '')}</strong> → ${escapeHtml(t.event || t.description || '')} · ${escapeHtml(t.start_date || t.date || '')}</div>`).join('')}`;
      } else {
        rd.innerHTML = '<p style="text-align:center;color:#999;padding:20px">无显著过境触发点</p>';
      }
    } catch(e) {
      rd.innerHTML = `<p style="text-align:center;color:#7a4b00;padding:20px">${escapeHtml(buildTransitCompareRecoveryMessage(e))}</p>`;
    }
  };
}

// ============================================================================
// AI 解读触发 (v6.9.4)
// ============================================================================
async function triggerAIReading(chartData) {
  if (!window.JyotishAPI?.aiFullReading) return;
  const summaryEl = document.getElementById('chart-summary');
  if (summaryEl) summaryEl.innerHTML += '<p style="color:#1565c0;font-size:13px">🤖 AI 正在生成个性化解读...</p>';
  try {
    const result = await window.JyotishAPI.aiFullReading(chartData);
    if (result.success) {
      if (summaryEl) {
        summaryEl.innerHTML = '<div style="background:#e3f2fd;padding:14px;border-radius:10px;margin-top:10px;font-size:14px;line-height:1.7">'
          + escapeHtml(result.reading).replace(/\n/g, '<br>') + '</div>';
      }
      console.log('[AI] ✅ 解读生成成功');
    }
  } catch(e) {
    console.warn('[AI] 解读失败:', e.message);
    if (summaryEl) summaryEl.innerHTML += '<p style="color:#999;font-size:12px">AI解读不可用，请查看结构化数据</p>';
  }
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
    moonNakshatra: formatMoonNakshatra(moonP) || null,
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

async function renderTransit(natalPlanets, ascSign, avData, ascDegree = 0) {
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

    // ── 新功能: Double Transit PAC + D9 ──
    const dtpac = computeDoubleTransitPAC(transit.planets, natalPlanets, ascSign, ascDegree, 7);
    const dtpacSection = $('double-transit-pac-section');
    if (dtpacSection) {
      dtpacSection.innerHTML = '';
      const summaryIcon = dtpac.summary.startsWith('✅') ? '✅' : dtpac.summary.startsWith('⚠️') ? '⚠️' : '❌';
      let html = `<h4 class="sub-title">KN Rao Double Transit PAC + D9</h4>`;
      html += `<div class="dt-pac-summary">${summaryIcon} ${dtpac.summary.replace(/[✅⚠️❌]/g, '')}</div>`;
      // D1 层
      const d1j = Object.keys(dtpac.d1.jupiter);
      const d1s = Object.keys(dtpac.d1.saturn);
      if (d1j.length || d1s.length) {
        html += `<div class="dt-pac-layer"><b>D1层</b> | Jupiter→[${d1j.join(', ')}] Saturn→[${d1s.join(', ')}]</div>`;
      }
      // D9 层
      const d9j = Object.keys(dtpac.d9.jupiter);
      const d9s = Object.keys(dtpac.d9.saturn);
      if (d9j.length || d9s.length) {
        html += `<div class="dt-pac-layer"><b>D9层</b> | Jupiter→[${d9j.join(', ')}] Saturn→[${d9s.join(', ')}]</div>`;
      }
      // Double Transit 命中
      if (dtpac.double_transit.length > 0) {
        html += '<div class="dt-pac-hits">';
        for (const dt of dtpac.double_transit) {
          html += `<div class="dt-pac-hit">[${dt.layer}] ${dt.target} (${dt.strength})</div>`;
        }
        html += '</div>';
      }
      dtpacSection.innerHTML = html;
    }

    // ── 新功能: Transit LL/7L ──
    const ll7l = computeTransitLL7L(transit.planets, natalPlanets, ascSign);
    const ll7lSection = $('transit-ll7l-section');
    if (ll7lSection) {
      ll7lSection.innerHTML = '';
      let html = `<h4 class="sub-title">Transit LL/7L 连接</h4>`;
      html += `<div class="ll7l-info">LL: ${planetName(ll7l.lagna_lord)} | 7L: ${planetName(ll7l.seventh_lord)}</div>`;
      if (ll7l.p5.hit) {
        html += `<div class="ll7l-badge badge-hit">P5(98%): ${ll7l.p5.details.map(d => `${d.direction} → ${d.connections.map(c => c.type).join('+')}`).join(' | ')}</div>`;
      } else {
        html += `<div class="ll7l-badge badge-miss">P5(98%): 未触发</div>`;
      }
      if (ll7l.p8.hit) {
        html += `<div class="ll7l-badge badge-hit">P8: ${ll7l.p8.details.join(' | ')}</div>`;
      }
      if (ll7l.parivartana.hit) {
        html += `<div class="ll7l-badge badge-hit">互换: ${ll7l.parivartana.details.join(' | ')}</div>`;
      }
      ll7lSection.innerHTML = html;
    }

    // ── 新功能: 行星聚集 ──
    const cong = computePlanetaryCongregation(natalPlanets, ascSign, transit.planets, 7);
    const congSection = $('planetary-congregation-section');
    if (congSection) {
      congSection.innerHTML = '';
      let html = `<h4 class="sub-title">行星聚集检测</h4>`;
      html += `<div class="cong-natal">本命 Lagna: [${cong.natal.lagna.map(planetName).join(', ')}] (${cong.natal.lagna.length}) | 7H: [${cong.natal.house_7.map(planetName).join(', ')}] (${cong.natal.house_7.length})</div>`;
      if (cong.transit) {
        const t7 = cong.transit[7] || [];
        html += `<div class="cong-transit">Transit 7H: [${t7.map(planetName).join(', ')}] (${t7.length})</div>`;
      }
      html += `<div class="cong-summary">${cong.summary}</div>`;
      congSection.innerHTML = html;
    }

    // ── 新功能: Vivah Saham ──
    const vs = computeVivahSaham(natalPlanets, ascDegree, transit.planets);
    const vsSection = $('vivah-saham-section');
    if (vsSection) {
      vsSection.innerHTML = '';
      let html = `<h4 class="sub-title">Vivah Saham 婚姻敏感点</h4>`;
      html += `<div class="vs-position">${vs.vivah_saham.sign_cn} ${vs.vivah_saham.degree_in_sign.toFixed(2)}°`;
      if (vs.vivah_saham.nakshatra) html += ` | ${vs.vivah_saham.nakshatra} P${vs.vivah_saham.pada}`;
      html += '</div>';
      if (vs.transit_activation) {
        const ta = vs.transit_activation;
        html += `<div class="vs-activation">Jupiter PAC: [${ta.jupiter.map(c => c.type).join(', ') || '-'}] | Saturn PAC: [${ta.saturn.map(c => c.type).join(', ') || '-'}]</div>`;
        html += `<div class="vs-double ${ta.double_activation ? 'badge-hit' : 'badge-miss'}">双星激活: ${ta.double_activation ? '✅ 是' : '❌ 否'}</div>`;
        if (ta.venus_in_saham_sign) html += `<div class="vs-venus">Venus 在 Saham 星座 ✅</div>`;
      }
      vsSection.innerHTML = html;
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
    $('transit-date').textContent = buildTransitRenderRecoveryMessage(err);
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
  initPWAInstallability();
  // 初始化 i18n
  initI18N();
  // 语言变化时重新渲染
  onLangChange(() => {
    if (chartData) renderAll();
  });

  initDateSelects();
  initChartImport();
  setupCitySearch();
  setupForm();
  setupFirstUsePanel();
  setupSavedChartPanel();
  $('btn-back').addEventListener('click', () => showPage('input'));
  // 初始化术语 Tooltip
  initTooltip();
  setGlossaryTerminologyMode(readTerminologyMode());
  // 初始化认证系统
  initAuth();
  // 初始化订阅系统
  initSubscription();
  // 初始化 AI 聊天
  initAIChat();
  document.addEventListener('jyotish:apply-rectified-birth', event => {
    applyRectifiedBirth(event.detail?.birth);
  });
  // Transit 更新按钮
  const transitBtn = $('btn-transit-update');
  if (transitBtn) {
    transitBtn.addEventListener('click', async () => {
      if (!chartData) return;
      const { planets, ascendant, birth_info } = chartData;
      const allV = computeAllVargas(planets);
      const av = computeAshtakavarga(planets, ascendant.sign);
      await renderTransit(planets, ascendant.sign, av, ascendant.degree);
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
  const moonLon = planets.Moon?.lon ?? planets.Moon?.longitude ?? planets.Moon?.degree ?? 0;
  return Math.floor(moonLon / (360 / 27)) % 27;
}

async function loadExportModule() {
  return import('./export.js');
}

function buildExportExtras(sourceChart) {
  const { planets, ascendant, birth_info } = sourceChart;
  const vargas = computeAllVargas(planets);
  const karaka = computeKaraka(planets);
  const av = computeAshtakavarga(planets, ascendant.sign);
  const sb = computeShadbala(planets, ascendant.sign, birth_info, vargas);
  const moonLon = planets.Moon?.lon ?? planets.Moon?.longitude ?? planets.Moon?.degree ?? 0;
  const dasha = computeDashaWithPratyantar(moonLon, birth_info.date, new Date().toISOString().split('T')[0]);
  const baseYogas = detectYogas(planets, ascendant.sign);
  const yogas = [...(baseYogas?.yogas || [])];
  try { yogas.push(...detectExtendedYogas(planets, ascendant.sign)); } catch(e) {}
  const aspects = _buildAspectsModule(planets);
  const panchanga = computeTithiYoga(planets, birth_info);
  const nakshatraAdvanced = computeNakshatraAdvanced(planets, _getBirthNakIdx(planets));
  const charaDasha = computeCharaDasha(planets, ascendant.sign);
  const karakamsha = computeKarakamsha(planets);
  const ascIdx = SIGNS.indexOf(ascendant.sign);
  const planetSignIdx = buildPlanetSignIndex(planets);
  const argala = computeArgala(planetSignIdx, ascIdx);
  const birthYear = parseInt((birth_info.date || '').split('-')[0]) || 1990;
  const birthMonth = parseInt((birth_info.date || '').split('-')[1]) || 1;
  const tajika = computeTajika(planets, ascendant.sign, birthYear, birthMonth);
  const validation = computeValidation(planets, ascendant, av, dasha);
  const audit = computeAudit(planets, ascendant, av, validation);
  const actionableContext = computeActionableContext(planets, ascendant);
  const jaimini = _buildJaiminiModule(karaka, charaDasha, karakamsha);

  return {
    dasha, yogas, vargas, aspects, jaimini,
    nakshatraAdvanced, argala, tajika,
    shadbala: sb, ashtakavarga: _buildAVModule(av),
    panchanga, validation, audit, actionableContext,
    provenance: sourceChart._client_audit?.provenance,
    workflows: buildWorkflowExportExtras(sourceChart),
  };
}

function buildWorkflowExportExtras(sourceChart) {
  const workflows = { ...(sourceChart?._client_workflows || {}) };
  if (sourceChart?._extended?.kp) {
    workflows.kp = buildKPReportSummary(sourceChart._extended.kp, window.__kpFocus || 'career');
  }
  workflows.case_library = {
    synastry_pairs: sortCaseLibrary(readSynastryPairLibrary()).slice(0, 12),
    prashna_cases: sortCaseLibrary(readPrashnaCaseLibrary()).slice(0, 12),
  };
  return workflows;
}

function buildKPReportSummary(kp, focus = 'career') {
  const domains = kpDomains();
  const domain = domains[focus] || domains.career;
  const houses = {};
  domain.houses.forEach(house => {
    houses[house] = kp?.houses?.[house] || {};
  });
  return {
    focus,
    label: domain.label,
    note: domain.note,
    focus_houses: domain.houses,
    houses,
    planets: kp?.planets || {},
  };
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
function getExportFormatLabel(format) {
  return {
    json: 'JSON 数据',
    html: 'HTML 报告',
    pdf: 'PDF 报告',
    svg: '星盘 SVG',
    png: '星盘 PNG',
  }[format] || '报告';
}

function setExportStatus(message, tone = 'working') {
  const status = $('export-status');
  if (!status) return;
  status.textContent = message || '';
  status.classList.toggle('hidden', !message);
  status.classList.toggle('is-working', tone === 'working');
  status.classList.toggle('is-success', tone === 'success');
  status.classList.toggle('is-error', tone === 'error');
}

function getPDFExportRecoveryMessage(error = null) {
  const reason = error?.message || 'PDF 渲染器不可用';
  return `PDF 渲染器不可用：${reason}。已改为导出 HTML 报告；也可先导出 HTML 报告并用浏览器打印为 PDF。请先到 Trust Center 运行健康检查。若本地 API 未连接，启动网页服务和本地 API 服务后重试 PDF。`;
}

function getGenericExportRecoveryMessage(format, error = null) {
  const label = getExportFormatLabel(format);
  const reason = error?.message || '导出模块加载失败';
  return `导出失败：${label} 未完成。${reason}。请刷新页面后重试；若仍失败，先导出 JSON 保存数据，再检查浏览器下载权限。`;
}

function buildExportRecoveryMessage(format, error) {
  return format === 'pdf'
    ? getPDFExportRecoveryMessage(error)
    : getGenericExportRecoveryMessage(format, error);
}

function clearExportStatusSoon(delay = 4200) {
  window.setTimeout(() => {
    if (!_exportInProgress) setExportStatus('');
  }, delay);
}

function setExportBusy(isBusy, activeItem = null) {
  _exportInProgress = Boolean(isBusy);
  const btnExport = $('btn-export');
  const items = document.querySelectorAll('.export-item');
  if (btnExport) {
    btnExport.disabled = _exportInProgress;
    btnExport.classList.toggle('is-exporting', _exportInProgress);
    btnExport.setAttribute('aria-busy', String(_exportInProgress));
  }
  items.forEach(item => {
    item.disabled = _exportInProgress;
    item.classList.toggle('is-exporting', _exportInProgress && item === activeItem);
    item.setAttribute('aria-busy', String(_exportInProgress && item === activeItem));
  });
}

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
    item.addEventListener('click', async () => {
      menu.classList.add('hidden');
      if (!chartData) { alert(t('alert.chart')); return; }
      if (_exportInProgress) return;
      const format = item.dataset.format;
      const label = getExportFormatLabel(format);
      try {
        setExportBusy(true, item);
        setExportStatus(`正在准备${label}...`, 'working');
        const exportModule = await loadExportModule();
        if (format === 'json' || format === 'html' || format === 'pdf') {
          const extras = buildExportExtras(chartData);
          if (format === 'json') {
            exportModule.exportJSON(chartData, extras);
            setExportStatus('JSON 数据已开始下载。', 'success');
          } else if (format === 'html') {
            exportModule.exportHTMLReport(chartData, extras);
            setExportStatus('HTML 报告已开始下载，可直接打开或打印。', 'success');
          } else {
            const result = await exportModule.exportPDFReport(chartData, extras);
            if (result?.fallback === 'html') {
              const artifactStatus = exportModule.formatReportArtifactStatus?.(result);
              setExportStatus(artifactStatus || getPDFExportRecoveryMessage(result?.error ? new Error(result.error) : null), 'error');
            } else {
              setExportStatus(exportModule.formatReportArtifactStatus?.(result) || 'PDF 报告已生成并开始下载。', 'success');
            }
          }
        } else if (format === 'svg') {
          const chartEl = $('rasi-chart');
          exportModule.exportSVG(chartEl, `jyotish-${chartData.birth_info?.date || 'chart'}`);
          setExportStatus('星盘 SVG 已开始下载。', 'success');
        } else if (format === 'png') {
          const chartEl = $('rasi-chart');
          await exportModule.exportPNG(chartEl, `jyotish-${chartData.birth_info?.date || 'chart'}`);
          setExportStatus('星盘 PNG 已开始下载。', 'success');
        }
      } catch (error) {
        setExportStatus(buildExportRecoveryMessage(format, error), 'error');
      } finally {
        setExportBusy(false);
        clearExportStatusSoon();
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
