/**
 * API Bridge v4.0
 *
 * 架构:
 *   计算 → 纯本地 (SwissEph WASM 或 localhost:5200 Python API)
 *   AI解读 → copse.top (GPT API 中转)
 */
const AI_BASE = 'https://copse.top';
const AI_KEY = 'sk-828a787bd2bb69d2d4707e8c05ae5cfe81b13de7be1db7f85932d49ed72e4c6a';

// ═══════════════════════════════════════════════════════════════
// 计算层 — 纯本地，不需要服务器
// ═══════════════════════════════════════════════════════════════

async function computeWithPython(birthData) {
  try {
    const resp = await fetch('http://localhost:5200/api/chart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(birthData),
    });
    const data = await resp.json();
    if (data.success) {
      console.log('[Compute] ✅ Python API v' + data.version);
      // Python API返回 'birth'，统一转为JS引擎的 'birth_info' 格式
      if (data.birth && !data.birth_info) {
        data.birth_info = data.birth;
      }
      return data;
    }
  } catch(e) {
    console.log('[Compute] Python API 不可用, 回退JS引擎');
  }
  return null;
}

// ═══════════════════════════════════════════════════════════════
// AI 解读层 — 通过 copse.top 调用 GPT
// ═══════════════════════════════════════════════════════════════

async function aiReading(chartData, options = {}) {
  const { style = 'deep', focus = '全部' } = options;

  const prompt = buildReadingPrompt(chartData, style, focus);

  try {
    const resp = await fetch(AI_BASE + '/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + AI_KEY,
      },
      body: JSON.stringify({
        model: 'gpt-4',
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: prompt },
        ],
        temperature: 0.7,
        max_tokens: 2000,
      }),
    });
    const data = await resp.json();
    const text = data?.choices?.[0]?.message?.content || '';
    return { success: true, reading: text, style, focus };
  } catch(e) {
    console.warn('[AI] 解读失败:', e.message);
    return { success: false, error: e.message };
  }
}

const SYSTEM_PROMPT = `你是印度占星(Jyotish/Vedic Astrology)专业解盘师。
基于提供的精确星盘数据，给出个性化、严谨、有深度的解读。
规则：
- 每次判断必须引用星盘中的具体配置（行星-星座-宫位-Dasha）
- 避免刻板教条（"土星落陷=不好"），必须结合多配置综合判断
- 语气专业但不冷漠，像面对面交谈
- 给出具体的时间窗口，不要说"未来几年"
- 如果某个配置有多种可能性，列出2-3种最可能的走向`;

function buildReadingPrompt(chartData, style, focus) {
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

  return prompt;
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
  // 计算
  computeWithPython,
  // AI 解读
  aiReading,
  aiFullReading,
  aiQuickInsight,
};
