/**
 * AI Chat Module — 星盘咨询 · AI 对话
 * 浮动按钮 + 星盘库(LocalStorage) + AI 对话面板
 */
import { SIGNS_CN, PLANET_CN, SIGNS } from './jyotish-engine.js';
import { t, getLang, signName, planetName } from './i18n.js';

const STORAGE_KEY = 'jyotish_chart_library';
const CHAT_CTX_KEY = 'jyotish_chat_context';
const DASHA_SHADBALA_AI_CALIBRATION_BOUNDARY = [
  '【Dasha/Shadbala Calibration Status】',
  'ready_for_calibration: 0',
  'external_oracle_evidence_validation: valid_packets: 0',
  'D1/D9/SAV 高可信；大运起点和 Shadbala 绝对值仍在外部 evidence validator 校准中。',
  '不得把大运起点或 Shadbala 绝对值说成已完成外部校准；涉及具体日期/绝对力量值时必须说明当前只可作参考标定。',
].join('\n');

let _currentChartData = null;
let _selectedChartId = null;
let _panelEl = null;
let _fabEl = null;
let _authToken = null;
let _authUser = null;
let _guidedTopicContext = null;

// ============================================================================
// 初始化
// ============================================================================
export function initAIChat() {
  createFAB();
  createPanel();
}

// ============================================================================
// 设置当前 chartData（排盘后调用）
// ============================================================================
export function aiChatSetChartData(cd) {
  _currentChartData = cd;
  if (cd) {
    _selectedChartId = buildChartId(cd);
    refreshChartSelect();
  }
}

export function openAIChatWithPrompt(prompt, guidedTopicContext = null) {
  const text = String(prompt || '').trim();
  if (!text) return;
  _guidedTopicContext = guidedTopicContext && typeof guidedTopicContext === 'object'
    ? guidedTopicContext
    : null;
  if (_panelEl && !_panelEl.classList.contains('open')) {
    _panelEl.classList.add('open');
  }
  const input = _panelEl?.querySelector('#ai-input');
  if (!input) return;
  input.value = text;
  input.focus();
}

// ============================================================================
// 认证状态同步（由 auth.js 调用）
// ============================================================================
export function aiChatSetAuth(token, user) {
  _authToken = token;
  _authUser = user;
}

// ============================================================================
// 浮动按钮
// ============================================================================
function createFAB() {
  _fabEl = document.createElement('button');
  _fabEl.className = 'ai-fab';
  _fabEl.innerHTML = `<span class="ai-fab-icon">✦</span><span class="ai-fab-text">${t('ai.fab.text')}</span>`;
  _fabEl.title = t('ai.fab.title');
  _fabEl.addEventListener('click', togglePanel);
  document.body.appendChild(_fabEl);

  // 首次使用：脉冲动画 + 引导气泡
  if (!localStorage.getItem('jyotish_fab_seen')) {
    _fabEl.classList.add('ai-fab-pulse');
    const tip = document.createElement('div');
    tip.className = 'ai-fab-tip';
    tip.textContent = t('ai.fab.tip');
    document.body.appendChild(tip);
    // 点击后消失
    const dismiss = () => {
      localStorage.setItem('jyotish_fab_seen', '1');
      _fabEl.classList.remove('ai-fab-pulse');
      tip.style.opacity = '0';
      setTimeout(() => tip.remove(), 300);
    };
    _fabEl.addEventListener('click', dismiss, {once: true});
    // 8秒后自动消失
    setTimeout(dismiss, 8000);
  }
}

// ============================================================================
// 聊天面板
// ============================================================================
function createPanel() {
  _panelEl = document.createElement('div');
  _panelEl.className = 'ai-panel';
  _panelEl.innerHTML = `
    <div class="ai-panel-header">
      <div class="ai-panel-title">${t('ai.panel.title')}</div>
      <button class="ai-panel-close">&times;</button>
    </div>
    <div class="ai-chart-select">
      <label>${t('ai.select.chart')}</label>
      <select id="ai-chart-selector"></select>
      <div class="ai-chart-actions">
        <button class="ai-chart-btn" id="ai-save-chart">${t('ai.save.chart')}</button>
        <button class="ai-chart-btn" id="ai-del-chart">${t('ai.delete')}</button>
      </div>
    </div>
    <div class="ai-messages" id="ai-messages">
      <div class="ai-msg system">${t('ai.welcome')}</div>
    </div>
    <div class="ai-input-area">
      <input class="ai-input" id="ai-input" placeholder="${t('ai.placeholder')}" />
      <button class="ai-send" id="ai-send">${t('ai.send')}</button>
    </div>
  `;
  document.body.appendChild(_panelEl);

  // 事件
  _panelEl.querySelector('.ai-panel-close').addEventListener('click', closePanel);
  _panelEl.querySelector('#ai-save-chart').addEventListener('click', saveCurrentChart);
  _panelEl.querySelector('#ai-del-chart').addEventListener('click', deleteSelectedChart);
  _panelEl.querySelector('#ai-send').addEventListener('click', sendMessage);
  _panelEl.querySelector('#ai-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  _panelEl.querySelector('#ai-chart-selector').addEventListener('change', e => {
    _selectedChartId = e.target.value;
  });

  refreshChartSelect();
}

function togglePanel() {
  _panelEl.classList.toggle('open');
}
function closePanel() {
  _panelEl.classList.remove('open');
}

// ============================================================================
// 星盘库管理（LocalStorage）
// ============================================================================
function getLibrary() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
  catch { return []; }
}
function saveLibrary(lib) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(lib));
}

function buildChartId(cd) {
  if (!cd?.birth_info) return 'unknown';
  const bi = cd.birth_info;
  return `${bi.date}_${bi.lat}_${bi.lon}_${bi.tz}`;
}

function chartLabel(cd) {
  if (!cd?.birth_info) return t('ai.unknown.chart');
  const bi = cd.birth_info;
  const asc = cd.ascendant;
  return `${bi.date} ${asc ? signName(asc.sign) : ''} ↑ (${bi.lat}°,${bi.lon}°)`;
}

function refreshChartSelect() {
  const sel = _panelEl?.querySelector('#ai-chart-selector');
  if (!sel) return;
  const lib = getLibrary();
  sel.innerHTML = `<option value="">-- ${t('ai.select.saved')} --</option>`;
  for (const entry of lib) {
    const opt = document.createElement('option');
    opt.value = entry.id;
    opt.textContent = entry.label;
    if (entry.id === _selectedChartId) opt.selected = true;
    sel.appendChild(opt);
  }
  // 如果有当前星盘但未保存，添加临时选项
  if (_currentChartData && !lib.find(e => e.id === _selectedChartId)) {
    const opt = document.createElement('option');
    opt.value = _selectedChartId || 'current';
    opt.textContent = chartLabel(_currentChartData) + ` ${t('ai.current')}`;
    opt.selected = true;
    sel.appendChild(opt);
  }
}

function saveCurrentChart() {
  if (!_currentChartData) { addSystemMsg(t('ai.no.chart.gen')); return; }
  const id = buildChartId(_currentChartData);
  const lib = getLibrary();
  if (lib.find(e => e.id === id)) { addSystemMsg(t('ai.chart.exists')); return; }
  lib.push({
    id,
    label: chartLabel(_currentChartData),
    data: _currentChartData,
    savedAt: new Date().toISOString(),
  });
  saveLibrary(lib);
  refreshChartSelect();
  addSystemMsg(t('ai.chart.saved'));
}

function deleteSelectedChart() {
  const sel = _panelEl?.querySelector('#ai-chart-selector');
  if (!sel || !sel.value) { addSystemMsg(t('ai.select.first')); return; }
  let lib = getLibrary();
  lib = lib.filter(e => e.id !== sel.value);
  saveLibrary(lib);
  refreshChartSelect();
  addSystemMsg(t('ai.chart.deleted'));
}

function getSelectedChartData() {
  const sel = _panelEl?.querySelector('#ai-chart-selector');
  if (!sel || !sel.value) return _currentChartData;
  // 如果选的是当前星盘
  if (_currentChartData && buildChartId(_currentChartData) === sel.value) return _currentChartData;
  // 从库中查找
  const lib = getLibrary();
  const entry = lib.find(e => e.id === sel.value);
  return entry?.data || _currentChartData;
}

// ============================================================================
// 对话系统
// ============================================================================
function addSystemMsg(text) {
  const box = _panelEl?.querySelector('#ai-messages');
  if (!box) return;
  const div = document.createElement('div');
  div.className = 'ai-msg system';
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function addUserMsg(text) {
  const box = _panelEl?.querySelector('#ai-messages');
  if (!box) return;
  const div = document.createElement('div');
  div.className = 'ai-msg user';
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function addAssistantMsg(text) {
  const box = _panelEl?.querySelector('#ai-messages');
  if (!box) return;
  const div = document.createElement('div');
  div.className = 'ai-msg assistant';
  div.innerHTML = formatMsg(text);
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function formatMsg(text) {
  // 简单 markdown: **bold**, \n -> <br>
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}

async function sendMessage() {
  const input = _panelEl?.querySelector('#ai-input');
  const sendBtn = _panelEl?.querySelector('#ai-send');
  if (!input || !sendBtn) return;
  const text = input.value.trim();
  if (!text) return;

  addUserMsg(text);
  input.value = '';
  sendBtn.disabled = true;

  const cd = getSelectedChartData();
  if (!cd) {
    addAssistantMsg(t('ai.no.chart.or.saved'));
    sendBtn.disabled = false;
    return;
  }

  // 构建星盘摘要上下文
  const context = buildChartContext(cd, _guidedTopicContext);

  // 调用 AI 对话
  try {
    const reply = await callAI(text, context);
    addAssistantMsg(reply);
  } catch (err) {
    addAssistantMsg(t('ai.error.prefix') + err.message);
  }
  sendBtn.disabled = false;
}

function buildChartContext(cd, guidedTopicContext = null) {
  if (!cd?.planets || !cd?.ascendant) return t('ai.no.data');
  const professionalReadingContext = buildProfessionalReadingContext(cd);
  if (cd.ai_prompt_pack?.prompt_zh && cd.ai_prompt_pack?.evidence_snapshot) {
    const workflow = cd._consultationWorkflow || {};
    const runtimePlanner = workflow.runtime_planner || {};
    const officialSnapshot = cd.ai_prompt_pack.evidence_snapshot.vedastro_official_full_snapshot || {};
    const vedastroOverview = cd.ai_prompt_pack.evidence_snapshot.vedastro_overview || {};
    const strictContracts = officialSnapshot.strict_workflow_contracts || {};
    const primaryRoute = officialSnapshot.strict_workflow_primary_route || Object.keys(strictContracts)[0] || '';
    const topReaderContract = primaryRoute ? (strictContracts[primaryRoute] || {}) : {};
    const adjudicationStages = topReaderContract.adjudication_stages || {};
    const predictionBoundaryContract = topReaderContract.prediction_boundary_contract || cd.ai_prompt_pack.evidence_snapshot.prediction_boundary_contract || {};
    const multiReferenceSummary = topReaderContract.multi_reference_reading_summary || {};
    const techniqueAuditSummary = topReaderContract.technique_audit_summary || {};
    const runtimePlannerBoundary = runtimePlanner && typeof runtimePlanner === 'object' && Object.keys(runtimePlanner).length
      ? [
          '【Runtime Planner】',
          `planner=${runtimePlanner.planner_name || 'UnifiedConsultationRuntimePlanner'} · entry=${runtimePlanner.entry_mode || workflow.entry_mode || '-'} · route=${runtimePlanner.route?.question_type || workflow.routing?.question_type || '-'}`,
          `sync_steps=${(runtimePlanner.sync_steps || []).join(' -> ') || '-'}`,
          `async_candidates=${(runtimePlanner.async_candidates || []).join(' / ') || '-'}`,
        ].join('\n')
      : '';
    const officialBoundary = officialSnapshot && typeof officialSnapshot === 'object'
      ? [
          '【VedAstro Official Snapshot Boundary】',
          `status=${officialSnapshot.status || 'blocked'} · source=${officialSnapshot.primary_source || 'vedastro_official'} · official_python_path=${officialSnapshot.official_python_path || '-'}`,
          `bundle=${officialSnapshot.official_bundle_status || 'blocked'} · chart_available=${officialSnapshot.official_chart_available ? 'yes' : 'no'}`,
          `full_catalog=${officialSnapshot.official_full_capability_catalog_status || 'blocked'} · executed=${officialSnapshot.official_full_capability_catalog_summary?.executed_method_count || 0}/${officialSnapshot.official_full_capability_catalog_summary?.catalog_method_count || 0} · sample_limit=${officialSnapshot.official_full_capability_catalog_summary?.sample_limit || 0}`,
        ].join('\n')
      : '';
    const topReaderBoundary = topReaderContract && typeof topReaderContract === 'object' && Object.keys(topReaderContract).length
      ? [
          '【Top Reader Contract】',
          `route=${primaryRoute || '-'} · verdict=${topReaderContract.verdict || '-'} · dominant_label=${topReaderContract.dominant_label || '-'}`,
          `adjudication_stages.promise=${adjudicationStages.promise?.status || 'missing'} · activation=${adjudicationStages.activation?.status || 'missing'} · manifestation=${adjudicationStages.manifestation?.status || 'missing'} · label=${adjudicationStages.label?.value || topReaderContract.dominant_label || '-'}`,
          `technique_audit_summary.functional=${techniqueAuditSummary.functional_benefic_malefic?.gate || 'none'}/${techniqueAuditSummary.functional_benefic_malefic?.used ? 'used' : 'blocked'} · vargas=${(techniqueAuditSummary.relevant_vargas?.present_keys || []).join('/') || 'none'} · dual_dasha=${techniqueAuditSummary.vimshottari_narayana_crosscheck?.used ? 'used' : 'blocked'}`,
          `multi_reference_reading_summary.root_frame=${Object.keys(multiReferenceSummary.root_frame || {}).join('/') || 'none'} · modifier_frame=${Object.keys(multiReferenceSummary.modifier_frame || {}).join('/') || 'none'}`,
          `main_conflicts=${(topReaderContract.main_conflicts || []).map(item => item?.type).filter(Boolean).join('/') || 'none'}`,
        ].join('\n')
      : '';
    const predictionBoundary = predictionBoundaryContract && typeof predictionBoundaryContract === 'object' && Object.keys(predictionBoundaryContract).length
      ? [
          '【Prediction Boundary Contract】',
          `source_refs=${(predictionBoundaryContract.source_refs || []).join(' / ') || '-'}`,
          `promise=${predictionBoundaryContract.promise?.status || adjudicationStages.promise?.status || 'missing'} · activation=${predictionBoundaryContract.activation?.status || adjudicationStages.activation?.status || 'missing'} · manifestation=${predictionBoundaryContract.manifestation?.status || adjudicationStages.manifestation?.status || 'missing'} · label=${predictionBoundaryContract.label?.value || topReaderContract.dominant_label || '-'}`,
          `mevg=${predictionBoundaryContract.confidence_boundary?.mevg_status || 'blocked'} · real_case=${predictionBoundaryContract.confidence_boundary?.real_case_calibration_status || 'blocked'} · policy=${predictionBoundaryContract.confidence_boundary?.unverified_claim_policy || 'downgrade_or_block'}`,
        ].join('\n')
      : '';
    const vedastroBoundary = vedastroOverview && typeof vedastroOverview === 'object'
      ? [
          '【VedAstro Overview Boundary】',
          `status=${vedastroOverview.status || 'blocked'} · scope=${vedastroOverview.search_scope || 'single_day_overview'} · source=${vedastroOverview.source || 'vedastro_service_adapter_candidate'}`,
          'overview only，不替代长周期精扫。',
        ].join('\n')
      : '';
    const guidedTopicBoundary = guidedTopicContext && typeof guidedTopicContext === 'object'
      ? [
          '【Guided Topic Context】',
          `topic_id=${guidedTopicContext.id || '-'} · title=${guidedTopicContext.title || '-'} · confidence=${guidedTopicContext.confidence || '-'}`,
          `guided_topic_context.functional=${(guidedTopicContext.strict_adjudication_bundle?.strict_audit_gate || guidedTopicContext.strict_audit_gate)?.functional_benefic_malefic?.gate || 'none'}/${(guidedTopicContext.strict_adjudication_bundle?.strict_audit_gate || guidedTopicContext.strict_audit_gate)?.functional_benefic_malefic?.used ? 'used' : 'blocked'} · vargas=${((guidedTopicContext.strict_adjudication_bundle?.strict_audit_gate || guidedTopicContext.strict_audit_gate)?.relevant_vargas?.present_keys || []).join('/') || 'none'} · dual_dasha=${(guidedTopicContext.strict_adjudication_bundle?.strict_audit_gate || guidedTopicContext.strict_audit_gate)?.vimshottari_narayana_crosscheck?.used ? 'used' : 'blocked'}`,
          `monthly_adjudication_summary=${(guidedTopicContext.strict_adjudication_bundle?.monthly_adjudication_summary || guidedTopicContext.monthly_adjudication_summary)?.primary_state?.value ? `${(guidedTopicContext.strict_adjudication_bundle?.monthly_adjudication_summary || guidedTopicContext.monthly_adjudication_summary).primary_state.value} / ${(guidedTopicContext.strict_adjudication_bundle?.monthly_adjudication_summary || guidedTopicContext.monthly_adjudication_summary).manifestation_mode?.value || '-'} / ${(guidedTopicContext.strict_adjudication_bundle?.monthly_adjudication_summary || guidedTopicContext.monthly_adjudication_summary).friction_source?.value || '-'} / ${(guidedTopicContext.strict_adjudication_bundle?.monthly_adjudication_summary || guidedTopicContext.monthly_adjudication_summary).time_confidence?.value || '-'}` : 'none'}`,
          `official_day_signal_summary=${(guidedTopicContext.strict_adjudication_bundle?.official_day_signal_summary || guidedTopicContext.official_day_signal_summary)?.top_day ? `${(guidedTopicContext.strict_adjudication_bundle?.official_day_signal_summary || guidedTopicContext.official_day_signal_summary).top_day.date || '-'} / ${(guidedTopicContext.strict_adjudication_bundle?.official_day_signal_summary || guidedTopicContext.official_day_signal_summary).top_day.summary || '-'} / ${(guidedTopicContext.strict_adjudication_bundle?.official_day_signal_summary || guidedTopicContext.official_day_signal_summary).top_day.confidence || '-'}` : 'none'}`,
          `why=${guidedTopicContext.why_worth_exploring || '-'}`,
        ].join('\n')
      : '';
    return [
      professionalReadingContext,
      '',
      '【AI Prompt Pack】',
      cd.ai_prompt_pack.prompt_zh,
      '',
      DASHA_SHADBALA_AI_CALIBRATION_BOUNDARY,
      '',
      runtimePlannerBoundary,
      '',
      officialBoundary,
      '',
      topReaderBoundary,
      '',
      predictionBoundary,
      '',
      guidedTopicBoundary,
      '',
      vedastroBoundary,
      '',
      '【evidence_snapshot】',
      JSON.stringify(cd.ai_prompt_pack.evidence_snapshot, null, 2),
      '',
      '【retrieval_plan】',
      JSON.stringify(cd.ai_prompt_pack.retrieval_plan || {}, null, 2),
    ].join('\n');
  }
  const asc = cd.ascendant;
  const bi = cd.birth_info;
  let ctx = `【${t('ai.no.data').replace(t('ai.no.data'), 'Chart Info')}】\n${t('label.date')}: ${bi?.date || '?'}\nAscendant: ${signName(asc.sign)} (${asc.sign}) ${asc.degree?.toFixed(2) || ''}°\n\n[Planets]\n`;
  const order = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  for (const pn of order) {
    const p = cd.planets[pn];
    if (!p || p.error) continue;
    ctx += `${planetName(pn)}: ${signName(p.sign)} ${p.degree_in_sign?.toFixed(2) || ''}° H${p.house} ${p.status || ''} ${p.retrograde ? 'R' : ''} ${p.nakshatra || ''}\n`;
  }
  return `${professionalReadingContext}\n\n${ctx}\n${DASHA_SHADBALA_AI_CALIBRATION_BOUNDARY}`;
}

function buildProfessionalReadingContext(cd) {
  const packet = cd?.professional_reading || window.__jyotishProfessionalReading?.professional_reading || null;
  if (!packet || typeof packet !== 'object') {
    return [
      '【Professional Reading Packet】',
      'status=not_loaded',
      'professional_reading: absent',
      'VedAstro Gateway Boundary: not_loaded',
      'user_led_calibration_controls: absent',
    ].join('\n');
  }
  const gateway = packet.vedastro_gateway || {};
  const controls = packet.user_led_calibration_controls || {};
  const requiredRows = packet.technique_audit_table_required_rows || [];
  return [
    '【Professional Reading Packet】',
    `status=${gateway.status || 'unknown'} · professional_reading=loaded`,
    `VedAstro Gateway Boundary: ${gateway.user_visibility?.boundary || gateway.gateway_status?.boundary || 'blocked_or_not_reported'}`,
    `user_led_calibration_controls: blind_mode=${Boolean(controls.blind_mode)} · disable_life_event_feedback=${Boolean(controls.disable_life_event_feedback)}`,
    `required_audit_rows=${requiredRows.join(' / ') || 'Functional Benefic/Malefic / MEVG / Real Case Calibration / VedAstro Gateway Boundary'}`,
  ].join('\n');
}

function buildAISetupGuidance() {
  const lang = getLang();
  if (lang === 'en') {
    return `💡 **${t('ai.setup.title')}**\n${t('ai.setup.server')}\n${t('ai.setup.secret')}\n${t('ai.setup.trust')}`;
  }
  return `💡 **${t('ai.setup.title')}**\n${t('ai.setup.server')}\n${t('ai.setup.secret')}\n${t('ai.setup.trust')}`;
}

// ============================================================================
// AI API 调用（对接后端 Jyotish Server）
// ============================================================================
function getApiBase() {
  if (window.JYOTISH_API_BASE) return window.JYOTISH_API_BASE;
  if (import.meta.env?.VITE_JYOTISH_API_BASE) return import.meta.env.VITE_JYOTISH_API_BASE;
  return '';  // 同域部署
}

async function callAI(userMessage, chartContext) {
  const apiBase = getApiBase();

  // 优先使用后端 API（需要登录）
  if (_authToken && apiBase !== undefined) {
    try {
      const cd = getSelectedChartData();
      const resp = await fetch(`${apiBase}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${_authToken}`,
        },
        body: JSON.stringify({
          message: userMessage,
          chart_context: chartContext,
          chart_data: cd,
          guided_topic_context: _guidedTopicContext,
        }),
      });
      const data = await parseAIResponse(resp);
      if (!resp.ok) {
        // 401 = token 过期
        if (resp.status === 401) {
          return '**登录已过期，请重新登录后继续对话。**\n\n点击页面右上角头像，退出后重新登录即可。';
        }
        // 429 = 超出限额
        if (resp.status === 429) {
          const todayUsage = data.todayUsage ?? '?';
          const limit = data.limit ?? 3;
          return `**今日对话次数已用完 (${todayUsage}/${limit})**\n\n免费用户每日 3 次 AI 对话。升级高级会员可享无限对话。\n\n点击右上角头像 → 升级高级会员。`;
        }
        throw new Error(data.error || data.message || `服务器错误 (${resp.status})`);
      }
      // 更新用量显示
      if (data.todayUsage !== undefined && _authUser) {
        _authUser.subscription = _authUser.subscription || {};
        _authUser.subscription.todayUsage = data.todayUsage;
        _authUser.subscription.limit = data.limit;
        // 通知 auth 刷新 UI
        localStorage.setItem('jyotish_auth_user', JSON.stringify(_authUser));
        document.querySelectorAll('[data-auth-header]').forEach(el => {
          // 触发 auth UI 更新（通过自定义事件）
          el.dispatchEvent(new CustomEvent('jyotish:usage-update'));
        });
      }
      return data.reply || data.message || data.content || t('ai.no.reply');
    } catch (err) {
      if (err.message.includes('登录已过期') || err.message.includes('次数已用完') || err.message.includes('expired') || err.message.includes('limit')) {
        return err.message;
      }
      console.warn('[AI Chat] Backend API failed, falling back:', err);
      return `${buildAIRecoveryMessage(err)}\n\n${generateLocalReply(userMessage, chartContext)}`;
    }
  }

  // 未登录提示
  if (!_authToken) {
    return `**请先登录以使用 AI 占星师对话**\n\n登录后每日可免费对话 3 次。\n\n点击页面右上角「登录」按钮即可注册/登录。\n\n${buildAISetupGuidance()}`;
  }

  // 兜底：本地回复
  return generateLocalReply(userMessage, chartContext);
}

async function parseAIResponse(resp) {
  const raw = await resp.text();
  try {
    return raw ? JSON.parse(raw) : {};
  } catch {
    return { message: raw?.slice(0, 180) || '' };
  }
}

function buildAIRecoveryMessage(error) {
  const message = error?.message || error || '本地 API 未连接';
  return `**服务端 AI 对话暂不可用**\n\n${message}\n\n请到 Trust Center 运行健康检查；如本地 API 未连接，请按 README 的普通用户启动路径启动网页服务和本地 API 服务后重试。\n\n${buildAISetupGuidance()}`;
}

function generateLocalReply(message, ctx) {
  const cd = getSelectedChartData();
  const asc = cd?.ascendant;
  const promptPack = cd?.ai_prompt_pack;
  const packAyanamsa = promptPack?.evidence_snapshot?.ayanamsa;
  const parameterBoundary = packAyanamsa
    ? `\n\n参数：${packAyanamsa.display || packAyanamsa.name || 'Lahiri'} Ayanamsa；节点口径 ${packAyanamsa.node_mode || 'mean'}。AI Prompt Pack 已作为上下文入口；完整生成式解读需要服务端 /api/chat。`
    : '';
  const calibrationBoundary = `\n\n${DASHA_SHADBALA_AI_CALIBRATION_BOUNDARY}`;
  const contextBoundary = `${parameterBoundary}${calibrationBoundary}`;
  const lower = message.toLowerCase();
  const lang = getLang();

  if (lower.includes('事业') || lower.includes('工作') || lower.includes('职业') || lower.includes('career') || lower.includes('job')) {
    const h10 = cd?.planets ? Object.entries(cd.planets).filter(([,p]) => p.house === 10).map(([pn]) => planetName(pn)) : [];
    return lang === 'en'
      ? `**Career Analysis (D1 Rasi)**\n\nAscendant ${signName(asc?.sign)} — 10th House:\n${h10.length > 0 ? '- Planets in H10: ' + h10.join(', ') : '- No planets in H10'}\n\n⚠️ Full career analysis requires D10, Dasha cycles, and Transit.\n\n💡 Configure AI backend for deeper insights.`
      : `**事业分析（基于 D1 本命盘）**\n\n上升 ${signName(asc?.sign)} 的第10宫：\n${h10.length > 0 ? '- 10宫内行星: ' + h10.join('、') : '- 10宫无行星落入'}\n\n⚠️ 完整职业分析需 D10、Dasha 大运、Transit 等。${contextBoundary}\n\n💡 建议配置 AI 后端获取更深入的分析。`;
  }

  if (lower.includes('婚姻') || lower.includes('感情') || lower.includes('配偶') || lower.includes('恋爱') || lower.includes('marriage') || lower.includes('love') || lower.includes('spouse')) {
    const h7 = cd?.planets ? Object.entries(cd.planets).filter(([,p]) => p.house === 7).map(([pn]) => planetName(pn)) : [];
    return lang === 'en'
      ? `**Marriage & Relationship (D1 Rasi)**\n\nAscendant ${signName(asc?.sign)} — 7th House:\n${h7.length > 0 ? '- Planets in H7: ' + h7.join(', ') : '- No planets in H7'}\n\n⚠️ Full analysis needs DK, D9, Vimshottari Venus periods.\n\n💡 Configure AI backend for complete reading.`
      : `**婚姻感情分析（基于 D1 本命盘）**\n\n上升 ${signName(asc?.sign)} 的第7宫：\n${h7.length > 0 ? '- 7宫内行星: ' + h7.join('、') : '- 7宫无行星落入'}\n\n⚠️ 完整婚姻分析需 DK、D9、Dasha 等。${contextBoundary}\n\n💡 配置 AI 后端获取完整解读。`;
  }

  if (lower.includes('财运') || lower.includes('财富') || lower.includes('收入') || lower.includes('wealth') || lower.includes('money') || lower.includes('finance')) {
    return lang === 'en'
      ? `**Wealth Analysis (D1 Rasi)**\n\nAscendant ${signName(asc?.sign)}:\n- H2 (earned income) and H11 (gains) are key houses\n- Jupiter and Venus status directly affects wealth potential\n\n⚠️ Full analysis needs D2, Dasha, and Transit.\n\n💡 Configure AI backend for deeper wealth reading.`
      : `**财运分析（基于 D1 本命盘）**\n\n上升 ${signName(asc?.sign)}:\n- 第2宫(正财)和第11宫(收入)是关键宫位\n- Jupiter 和 Venus 的状态直接影响财富潜力\n\n⚠️ 完整分析需 D2、Dasha 和 Transit。${contextBoundary}\n\n💡 配置 AI 后端获取深度财运解读。`;
  }

  if (lower.includes('健康') || lower.includes('身体') || lower.includes('health')) {
    return lang === 'en'
      ? `**Health Analysis (D1 Rasi)**\n\nAscendant ${signName(asc?.sign)}:\n- H1 represents body and vitality\n- H6 represents disease\n- H8 represents chronic health issues\n\n⚠️ Full analysis requires D6 (Shashtamsa).\n\n💡 Configure AI backend for deeper health reading.`
      : `**健康分析（基于 D1 本命盘）**\n\n上升 ${signName(asc?.sign)}:\n- 第1宫代表身体和生命力\n- 第6宫代表疾病\n- 第8宫代表慢性健康问题\n\n⚠️ 完整分析需 D6。${contextBoundary}\n\n💡 配置 AI 后端获取深度健康解读。`;
  }

  return lang === 'en'
    ? `**Chart Overview**\n\nAscendant: ${signName(asc?.sign)} ${asc?.degree?.toFixed(2) || ''}°\n\nYou can ask about:\n- Career\n- Marriage & relationships\n- Wealth\n- Health\n- Dasha analysis\n- Transit impacts\n\n${buildAISetupGuidance()}`
    : `**星盘概览**\n\n上升: ${signName(asc?.sign)} ${asc?.degree?.toFixed(2) || ''}°${contextBoundary}\n\n你可以询问以下话题：\n- 事业运 / 工作方向\n- 婚姻感情\n- 财运分析\n- 健康运势\n- Dasha 大运分析\n- Transit 过境影响\n\n${buildAISetupGuidance()}`;
}
