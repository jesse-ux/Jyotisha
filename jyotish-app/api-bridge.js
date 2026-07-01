/**
 * API Bridge v4.0
 *
 * 架构:
 *   计算 → 纯本地 (SwissEph WASM 或 localhost:5200 本地 API 服务)
 *   AI解读 → 登录后的服务端 /api/chat；浏览器不保存模型 API key
 */
let activeApiBase = '';
const AI_DISABLED_MESSAGE = 'AI_BROWSER_KEY_DISABLED: AI 解读需通过服务端 /api/chat 或后端代理；不要把 OpenAI API key 放进浏览器。';

function getApiBases(preferActive = false) {
  const configured = window.YINDUZHANXING_API_BASE || localStorage.getItem('YINDUZHANXING_API_BASE') || '';
  const bases = [
    preferActive ? activeApiBase : '',
    configured,
    'http://localhost:5200',
    'http://127.0.0.1:5200',
    'http://localhost:5201',
    'http://127.0.0.1:5201',
  ].filter(Boolean);
  return [...new Set(bases.map(base => base.replace(/\/$/, '')))];
}

async function postJson(path, payload, { requireModernChart = false } = {}) {
  let firstSuccessful = null;
  let lastError = null;
  let lastAttempt = null;
  for (const base of getApiBases(true)) {
    try {
      const resp = await fetch(`${base}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await parseApiResponse(resp);
      lastAttempt = `${base}${path}`;
      if (!resp.ok) {
        lastError = new Error(buildAPIRecoveryMessage(path, data?.error || data?.message || `API请求失败: ${path}`, lastAttempt));
        continue;
      }
      if (data?.success === false) {
        lastError = new Error(buildAPIRecoveryMessage(path, data?.error || data?.message || `API返回失败: ${path}`, lastAttempt));
        continue;
      }
      if (requireModernChart && data?.success && data?.special_lagnas?.precision !== 'sunrise_correct') {
        firstSuccessful ||= { base, data };
        continue;
      }
      activeApiBase = base;
      return data;
    } catch (error) {
      lastAttempt = `${base}${path}`;
      lastError = new Error(buildAPIRecoveryMessage(path, error, lastAttempt));
    }
  }
  if (firstSuccessful) {
    activeApiBase = firstSuccessful.base;
    return firstSuccessful.data;
  }
  throw lastError || new Error(buildAPIRecoveryMessage(path, '本地 API 未连接', lastAttempt));
}

async function fetchJson(path) {
  let lastError = null;
  let lastAttempt = null;
  for (const base of getApiBases(true)) {
    try {
      const resp = await fetch(`${base}${path}`);
      const data = await parseApiResponse(resp);
      lastAttempt = `${base}${path}`;
      if (!resp.ok || data?.success === false) {
        lastError = new Error(buildAPIRecoveryMessage(path, data?.error || data?.message || `API请求失败: ${path}`, lastAttempt));
        continue;
      }
      activeApiBase = base;
      return data;
    } catch (error) {
      lastAttempt = `${base}${path}`;
      lastError = new Error(buildAPIRecoveryMessage(path, error, lastAttempt));
    }
  }
  throw lastError || new Error(buildAPIRecoveryMessage(path, '本地 API 未连接', lastAttempt));
}

async function parseApiResponse(resp) {
  const raw = await resp.text();
  try {
    return raw ? JSON.parse(raw) : {};
  } catch {
    return { message: raw?.slice(0, 180) || '' };
  }
}

function buildAPIRecoveryMessage(path, error, lastAttempt = '') {
  const message = typeof error === 'string' ? error : (error?.message || '本地 API 未连接');
  return `${message}。请到 Trust Center 运行健康检查；如未连接，请按 README 的普通用户启动路径启动网页服务和本地 API 服务后重试。${lastAttempt ? ` lastAttempt=${lastAttempt}` : ''}`;
}

function normalizeChartData(data) {
  if (data.birth && !data.birth_info) data.birth_info = data.birth;
  if (data.ascendant?.degree != null && data.ascendant.degree_in_sign == null) {
    data.ascendant.degree_in_sign = data.ascendant.degree;
  }
  if (data.planets) {
    for (const [, v] of Object.entries(data.planets)) {
      if (v?.degree != null && v.degree_in_sign == null) {
        v.degree_in_sign = v.degree % 30;
      }
    }
  }
  return data;
}

// ═══════════════════════════════════════════════════════════════
// 计算层 — 纯本地，不需要服务器
// ═══════════════════════════════════════════════════════════════

async function computeWithPython(birthData) {
  try {
    const data = await postJson('/api/chart', birthData, { requireModernChart: true });
    if (data.success) {
      console.log('[Compute] ✅ 本地 API 服务 v' + data.version + ' @ ' + activeApiBase);
      return normalizeChartData(data);
    }
  } catch(e) {
    console.log('[Compute] 本地 API 服务不可用, 回退JS引擎');
  }
  return null;
}

async function computeConsultationWorkflow(payload) {
  return postJson('/api/consultation_workflow', payload);
}

async function computeSynastry(payload) {
  return postJson('/api/synastry', payload);
}

async function computePrashna(payload) {
  return postJson('/api/prashna', payload);
}

async function computeKP(payload) {
  return postJson('/api/kp', payload);
}

async function computeDashaSystem(payload) {
  return postJson('/api/dasha', payload);
}

async function computeCharaDasha(payload) {
  return postJson('/api/dasha/chara', payload);
}

async function computeRemedies(payload) {
  return postJson('/api/remedies', payload);
}

async function computeSadeSati(payload) {
  return postJson('/api/sade_sati', payload);
}

async function computePanchaMahapurusha(payload) {
  return postJson('/api/pancha_mahapurusha', payload);
}

async function computeCareer(payload) {
  return postJson('/api/career', payload);
}

async function computeRelationship(payload) {
  return postJson('/api/relationship', payload);
}

async function importChart(payload) {
  return postJson('/api/import_chart', payload);
}

async function generateReportArtifact(payload) {
  return postJson('/api/report_artifact', payload);
}

async function validateOracleEvidence(payload) {
  return postJson('/api/oracle_evidence', payload);
}

async function computeThematicReport(payload) {
  return postJson('/api/thematic_report', payload);
}

async function getAPIHealth() {
  let lastError = null;
  for (const base of getApiBases(true)) {
    try {
      const startedAt = Date.now();
      const resp = await fetch(`${base}/api/health`);
      const data = await parseApiResponse(resp);
      if (!resp.ok || data?.status !== 'ok') {
        lastError = new Error(buildAPIRecoveryMessage('/api/health', data?.error || data?.message || '本地 API 健康检查失败', `${base}/api/health`));
        continue;
      }
      activeApiBase = base;
      return {
        success: true,
        base,
        latencyMs: Date.now() - startedAt,
        ...data,
      };
    } catch (error) {
      lastError = new Error(buildAPIRecoveryMessage('/api/health', error, `${base}/api/health`));
    }
  }
  throw lastError || new Error(buildAPIRecoveryMessage('/api/health', '本地 API 健康检查不可用'));
}

async function getCapabilityAudit() {
  let lastError = null;
  for (const base of getApiBases(true)) {
    try {
      const resp = await fetch(`${base}/api/capability_audit`);
      const data = await parseApiResponse(resp);
      if (!resp.ok || data?.success === false) {
        lastError = new Error(buildAPIRecoveryMessage('/api/capability_audit', data?.error || data?.message || '能力审计接口不可用', `${base}/api/capability_audit`));
        continue;
      }
      activeApiBase = base;
      return data;
    } catch (error) {
      lastError = new Error(buildAPIRecoveryMessage('/api/capability_audit', error, `${base}/api/capability_audit`));
    }
  }
  throw lastError || new Error(buildAPIRecoveryMessage('/api/capability_audit', '能力审计接口不可用'));
}

async function getVedAstroStatus() {
  return fetchJson('/api/vedastro/status');
}

async function runVedAstroRangeScan(payload) {
  return postJson('/api/vedastro/range_scan', payload);
}

async function getTechniqueCatalog() {
  let lastError = null;
  for (const base of getApiBases(true)) {
    try {
      const resp = await fetch(`${base}/api/technique_catalog`);
      const data = await parseApiResponse(resp);
      if (!resp.ok || data?.success === false) {
        lastError = new Error(buildAPIRecoveryMessage('/api/technique_catalog', data?.error || data?.message || '技法目录接口不可用', `${base}/api/technique_catalog`));
        continue;
      }
      activeApiBase = base;
      return data;
    } catch (error) {
      lastError = new Error(buildAPIRecoveryMessage('/api/technique_catalog', error, `${base}/api/technique_catalog`));
    }
  }
  throw lastError || new Error(buildAPIRecoveryMessage('/api/technique_catalog', '技法目录接口不可用'));
}

async function runTechniqueExample(payload) {
  return postJson('/api/technique_example', payload);
}

async function computeAnnual(payload) {
  return postJson('/api/annual', payload);
}

async function computeMuhurta(payload) {
  return postJson('/api/muhurta', payload);
}

async function computePanchangaRange(payload) {
  return postJson('/api/panchanga_range', payload);
}

async function computeBhavaChalit(payload) {
  return postJson('/api/bhava_chalit', payload);
}

async function computeSudarshana(payload) {
  return postJson('/api/sudarshana', payload);
}

async function computeNakshatraFull(payload) {
  return postJson('/api/nakshatra_full', payload);
}

async function computeVargaFull(payload) {
  return postJson('/api/varga_full', payload);
}

async function computeJaimini(payload) {
  return postJson('/api/jaimini', payload);
}

async function computeAshtakavarga(payload) {
  return postJson('/api/ashtakavarga', payload);
}

async function computeShadbala(payload) {
  return postJson('/api/shadbala', payload);
}

async function computeYogas(payload) {
  return postJson('/api/yogas', payload);
}

async function computeAspects(payload) {
  return postJson('/api/aspects', payload);
}

async function computeRectificationGate(payload) {
  return postJson('/api/rectification_gate', payload);
}

async function computeCaseValidation(payload) {
  return postJson('/api/case_validation', payload);
}

async function getRealCaseRevalidation() {
  return fetchJson('/api/real_case_revalidation');
}

async function computeDivisionalYoga(payload) {
  return postJson('/api/divisional_yoga', payload);
}

async function computeKakshya(payload) {
  return postJson('/api/kakshya', payload);
}

async function computeBhavaBala(payload) {
  return postJson('/api/bhava_bala', payload);
}

async function computeTransitTriggers(payload) {
  return postJson('/api/transit', payload);
}

// ═══════════════════════════════════════════════════════════════
// AI 解读层 — 浏览器端禁用密钥直连；由 ai-chat.js 走服务端 /api/chat
// ═══════════════════════════════════════════════════════════════

async function aiReading(chartData, options = {}) {
  const { style = 'deep', focus = '全部' } = options;
  return {
    success: false,
    error: AI_DISABLED_MESSAGE,
    style,
    focus,
    chartDataPresent: Boolean(chartData),
    prompt_context: buildReadingPrompt(chartData || {}, style, focus),
    promptPackUsed: Boolean(chartData?.ai_prompt_pack?.prompt_zh),
  };
}

const SYSTEM_PROMPT = `你是印度占星(Jyotish/Vedic Astrology)专业解盘师。
基于提供的精确星盘数据，给出个性化、严谨、有深度的解读。
规则：
- 每次判断必须引用星盘中的具体配置（行星-星座-宫位-Dasha）
- 避免刻板教条（"土星落陷=不好"），必须结合多配置综合判断
- 语气专业但不冷漠，像面对面交谈
- 给出具体的时间窗口，不要说"未来几年"
- 如果某个配置有多种可能性，列出2-3种最可能的走向
- Dasha/Shadbala Calibration Status: ready_for_calibration: 0；external_oracle_evidence_validation valid_packets: 0；不得把大运起点或 Shadbala 绝对值说成已完成外部校准`;

const DASHA_SHADBALA_PROMPT_BOUNDARY = [
  '【Dasha/Shadbala Calibration Status】',
  'ready_for_calibration: 0',
  'external_oracle_evidence_validation: valid_packets: 0',
  'D1/D9/SAV 高可信；大运起点和 Shadbala 绝对值仍在外部 evidence validator 校准中。',
  '不得把大运起点或 Shadbala 绝对值说成已完成外部校准；涉及具体日期/绝对力量值时必须说明当前只可作参考标定。',
].join('\n');

function buildReadingPrompt(chartData, style, focus) {
  if (chartData?.ai_prompt_pack?.prompt_zh && chartData?.ai_prompt_pack?.evidence_snapshot) {
    return [
      chartData.ai_prompt_pack.prompt_zh,
      '',
      DASHA_SHADBALA_PROMPT_BOUNDARY,
      '',
      '【evidence_snapshot】',
      JSON.stringify(chartData.ai_prompt_pack.evidence_snapshot, null, 2),
      '',
      '【retrieval_plan】',
      JSON.stringify(chartData.ai_prompt_pack.retrieval_plan || {}, null, 2),
    ].join('\n');
  }
  const asc = chartData.ascendant?.sign || '?';
  const planets = chartData.planets || {};
  const yogas = (chartData.yogas || []).slice(0, 15);
  const dasha = chartData.dasha || {};

  let prompt = `请基于以下星盘数据给出${style === 'quick' ? '简明' : '深度'}解读。\n\n`;
  prompt += `【焦点领域】${focus}\n\n`;
  prompt += `【上升星座】${asc}\n\n`;
  prompt += `【行星落位】\n`;
  for (const [name, data] of Object.entries(planets)) {
    const sign = typeof data === 'object' ? (data.sign || '?') : data;
    const house = typeof data === 'object' ? (data.house || '?') : '?';
    prompt += `  ${name}: ${sign} ${house}宫\n`;
  }

  if (yogas.length > 0) {
    prompt += `\n【主要Yoga】\n`;
    for (const y of yogas) {
      prompt += `  ${y.name || ''}: ${(y.combination || y.desc || '').slice(0, 60)}\n`;
    }
  }

  if (dasha.current_md) {
    prompt += `\n【当前大运】${dasha.current_md} (${dasha.current_ad || ''})\n`;
  }

  prompt += `\n请分析：`;
  if (focus === '事业' || focus === '全部') prompt += `\n1) 事业方向与关键时间节点`;
  if (focus === '感情' || focus === '全部') prompt += `\n2) 感情婚姻特征与时机`;
  if (focus === '健康' || focus === '全部') prompt += `\n3) 需注意的健康周期`;
  if (focus === '全部') prompt += `\n4) 当前大运的核心主题`;

  return `${prompt}\n\n${DASHA_SHADBALA_PROMPT_BOUNDARY}`;
}

// ═══════════════════════════════════════════════════════════════
// 一键入口
// ═══════════════════════════════════════════════════════════════

async function aiFullReading(chartData) {
  const reading = await aiReading(chartData, { style: 'deep', focus: '全部' });
  return reading;
}

async function aiQuickInsight(chartData) {
  const reading = await aiReading(chartData, { style: 'quick', focus: '全部' });
  return reading;
}

// ═══════════════════════════════════════════════════════════════
// 对外接口
// ═══════════════════════════════════════════════════════════════

window.JyotishAPI = {
  get apiBase() { return activeApiBase || getApiBases()[0] || ''; },
  aiKeyPolicy: 'server_side_only',
  // 计算
  computeWithPython,
  computeConsultationWorkflow,
  computeSynastry,
  computePrashna,
  computeKP,
  computeDashaSystem,
  computeCharaDasha,
  computeRemedies,
  computeSadeSati,
  computePanchaMahapurusha,
  computeCareer,
  computeRelationship,
  importChart,
  generateReportArtifact,
  validateOracleEvidence,
  computeThematicReport,
  getAPIHealth,
  getCapabilityAudit,
  getVedAstroStatus,
  runVedAstroRangeScan,
  getTechniqueCatalog,
  runTechniqueExample,
  computeAnnual,
  computeMuhurta,
  computePanchangaRange,
  computeBhavaChalit,
  computeSudarshana,
  computeNakshatraFull,
  computeVargaFull,
  computeJaimini,
  computeAshtakavarga,
  computeShadbala,
  computeYogas,
  computeAspects,
  computeRectificationGate,
  computeCaseValidation,
  getRealCaseRevalidation,
  computeDivisionalYoga,
  computeKakshya,
  computeBhavaBala,
  computeTransitTriggers,
  // AI 解读
  aiReading,
  aiFullReading,
  aiQuickInsight,
};
