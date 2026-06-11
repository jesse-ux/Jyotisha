/**
 * API Bridge v1.0
 * 连接前端到 Python v6.6.0 精算引擎
 * 
 * 用法: 在 index.html 中加载此脚本后，自动检测并优先使用 Python API
 */
const API_BASE = 'http://localhost:5200';

async function apiFetch(endpoint, body = {}) {
  try {
    const resp = await fetch(`${API_BASE}${endpoint}`, {
      method: body && Object.keys(body).length > 0 ? 'POST' : 'GET',
      headers: { 'Content-Type': 'application/json' },
      body: body && Object.keys(body).length > 0 ? JSON.stringify(body) : undefined,
    });
    return await resp.json();
  } catch (e) {
    return null;
  }
}

async function checkApiAvailable() {
  const r = await apiFetch('/api/health');
  return r && r.status === 'ok';
}

/**
 * 使用 Python API 计算完整星盘
 * 替代原有的 jyotish-engine.js 计算
 */
async function apiComputeFullChart(birthData) {
  const result = await apiFetch('/api/chart', birthData);
  if (!result || !result.success) {
    throw new Error(result?.error || 'API computation failed');
  }
  return result;
}

/**
 * 获取补救建议
 */
async function apiGetRemedies(chartData) {
  const shadbala = {};
  if (chartData.planets) {
    for (const [p, d] of Object.entries(chartData.planets)) {
      shadbala[p] = { total_rupas: 3.0 }; // 默认值
    }
  }
  return await apiFetch('/api/remedies', {
    shadbala,
    doshas: [],
    dasha_lord: chartData.dasha?.current_md || '',
  });
}

/**
 * 获取KP分析
 */
async function apiGetKP(chartData) {
  return await apiFetch('/api/kp', {
    planets: chartData.planets || {},
    asc_sign_idx: chartData.ascendant?.sign_idx || 0,
  });
}

/**
 * 获取合盘分析
 */
async function apiGetSynastry(maleMoonDeg, femaleMoonDeg) {
  return await apiFetch('/api/synastry', {
    male_moon: maleMoonDeg,
    female_moon: femaleMoonDeg,
  });
}

/**
 * 获取Sade Sati分析
 */
async function apiGetSadeSati(chartData) {
  const moon = chartData.planets?.Moon;
  const sun = chartData.planets?.Sun;
  return await apiFetch('/api/sade_sati', {
    moon_degree: moon?.lon || 0,
    asc_degree: chartData.ascendant?.degree || 0,
    saturn_degree: chartData.planets?.Saturn?.lon || 0,
  });
}

/**
 * 获取Pancha Mahapurusha分析
 */
async function apiGetPMC(chartData) {
  return await apiFetch('/api/pancha_mahapurusha', {
    planets: chartData.planets || {},
    sun_degree: chartData.planets?.Sun?.lon || 0,
  });
}

/**
 * 获取事业分析
 */
async function apiGetCareer(chartData) {
  return await apiFetch('/api/career', {
    planets: chartData.planets || {},
    asc_sign: chartData.ascendant?.sign || 'Aries',
  });
}

/**
 * 获取感情分析
 */
async function apiGetRelationship(chartData) {
  return await apiFetch('/api/relationship', {
    planets: chartData.planets || {},
    asc_sign: chartData.ascendant?.sign || 'Aries',
  });
}

/**
 * 获取Prashna卜卦分析
 */
async function apiGetPrashna(chartData, question) {
  return await apiFetch('/api/prashna', {
    planets: chartData.planets || {},
    question: question || 'general',
  });
}

// 导出
window.JyotishAPI = {
  checkAvailable: checkApiAvailable,
  computeChart: apiComputeFullChart,
  getRemedies: apiGetRemedies,
  getKP: apiGetKP,
  getSynastry: apiGetSynastry,
  getSadeSati: apiGetSadeSati,
  getPMC: apiGetPMC,
  getCareer: apiGetCareer,
  getRelationship: apiGetRelationship,
  getPrashna: apiGetPrashna,
  baseUrl: API_BASE,
};
