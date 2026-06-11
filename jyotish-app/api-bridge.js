/**
 * API Bridge v2.0
 * 连接前端到 Python v6.7.0 精算引擎
 * 
 * 部署: API_KEY 在生产环境通过服务端环境变量注入
 *       此处为前端调用凭证，实际部署时建议配置环境变量
 */
const API_BASE = 'https://copse.top';
const API_KEY = 'sk-828a787bd2bb69d2d4707e8c05ae5cfe81b13de7be1db7f85932d49ed72e4c6a';

const API_CACHE = {};
const CACHE_TTL = 300000; // 5分钟缓存

async function apiFetch(endpoint, body = {}) {
  const cacheKey = endpoint + JSON.stringify(body);
  if (API_CACHE[cacheKey] && Date.now() - API_CACHE[cacheKey].ts < CACHE_TTL) {
    return API_CACHE[cacheKey].data;
  }
  try {
    const resp = await fetch(`${API_BASE}${endpoint}`, {
      method: body && Object.keys(body).length > 0 ? 'POST' : 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
      },
      body: body && Object.keys(body).length > 0 ? JSON.stringify(body) : undefined,
    });
    const data = await resp.json();
    API_CACHE[cacheKey] = { data, ts: Date.now() };
    return data;
  } catch (e) {
    console.warn('[API] fetch failed:', e.message);
    return null;
  }
}

async function checkApiAvailable() {
  const r = await apiFetch('/api/health');
  if (r && r.status === 'ok') {
    console.log(`[API] ✅ Connected to Jyotish API v${r.version} (${r.modules})`);
    return true;
  }
  return false;
}

async function apiComputeFullChart(birthData) {
  const result = await apiFetch('/api/chart', birthData);
  if (!result || !result.success) {
    throw new Error(result?.error || '计算失败，请检查输入信息');
  }
  return result;
}

async function apiGetRemedies(chartData) {
  return await apiFetch('/api/remedies', {
    shadbala: chartData.planets || {},
    doshas: [],
    dasha_lord: chartData.dasha?.current_md || '',
  });
}

async function apiGetKP(chartData) {
  return await apiFetch('/api/kp', {
    planets: chartData.planets || {},
    asc_sign_idx: chartData.ascendant?.sign_idx || 0,
  });
}

async function apiGetSynastry(maleMoonDeg, femaleMoonDeg) {
  return await apiFetch('/api/synastry', { male_moon: maleMoonDeg, female_moon: femaleMoonDeg });
}

async function apiGetSadeSati(chartData) {
  return await apiFetch('/api/sade_sati', {
    moon_degree: chartData.planets?.Moon?.lon || 0,
    asc_degree: chartData.ascendant?.degree || 0,
    saturn_degree: chartData.planets?.Saturn?.lon || 0,
  });
}

async function apiGetPMC(chartData) {
  return await apiFetch('/api/pancha_mahapurusha', {
    planets: chartData.planets || {},
    sun_degree: chartData.planets?.Sun?.lon || 0,
  });
}

async function apiGetCareer(chartData) {
  return await apiFetch('/api/career', {
    planets: chartData.planets || {},
    asc_sign: chartData.ascendant?.sign || 'Aries',
  });
}

async function apiGetRelationship(chartData) {
  return await apiFetch('/api/relationship', {
    planets: chartData.planets || {},
    asc_sign: chartData.ascendant?.sign || 'Aries',
  });
}

async function apiGetPrashna(chartData, question) {
  return await apiFetch('/api/prashna', {
    planets: chartData.planets || {},
    question: question || 'general',
  });
}

// 🔥 一键全功能计算
async function apiComputeAll(birthData) {
  const chart = await apiComputeFullChart(birthData);
  if (!chart || !chart.success) return chart;
  
  // 并行请求所有分析
  const [remedies, kp, sade_sati, pmc, career, relationship] = await Promise.all([
    apiGetRemedies(chart),
    apiGetKP(chart),
    apiGetSadeSati(chart),
    apiGetPMC(chart),
    apiGetCareer(chart),
    apiGetRelationship(chart),
  ]);
  
  chart._extended = { remedies, kp, sade_sati, pmc, career, relationship };
  return chart;
}

window.JyotishAPI = {
  checkAvailable: checkApiAvailable,
  computeChart: apiComputeFullChart,
  computeAll: apiComputeAll,
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
