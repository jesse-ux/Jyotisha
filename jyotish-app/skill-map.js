import { escapeAttr, escapeHtml } from './security.js';

const STAGES = [
  ['入口路由', '出生信息 / PDF星盘 / 生时不明三路径'],
  ['静态十步', '宫位、Yoga、Argala、逆行燃烧、Nakshatra、Shadbala、AV、Ketu、分盘'],
  ['动态七步', 'Dasha、收敛、Transit、Double Transit、Jaimini、KP、Varshaphala'],
  ['应期输出', '时间窗口、行动类型、置信度、案例检索'],
  ['补救措施', '宝石、咒语、捐赠、斋戒、Dosha专项'],
  ['现代措辞', '把传统术语映射为普通用户能理解的生活语言'],
  ['验证门控', 'Technique Audit、预测边界、外部验证状态'],
  ['报告交付', '结构化摘要、专题章节、PDF/打印导出'],
];

const MODULES = [
  { id: 'd1', name: 'D1基础星盘', tab: '本命盘', status: 'app', detail: '行星位置、宫位、尊严、星宿、上升信息' },
  { id: 'lagna', name: '特殊Lagna', tab: '完整解盘', status: 'app', detail: 'AL/UL/A10 与日出校正版 HL/GL/VL 已在完整解盘展示' },
  { id: 'karaka', name: 'Jaimini Karaka', tab: 'Karaka', status: 'app', detail: '7/8 Karaka 已展示，并已声明两套体系差异与固定口径要求' },
  { id: 'shadbala', name: 'Shadbala六维力量', tab: 'Shadbala', status: 'app', detail: '相对强弱已展示，外部绝对值校准仍需标注边界' },
  { id: 'avastha', name: 'Avastha状态', tab: '扩展分析', status: 'partial', detail: '行星年龄/警觉/情绪状态已部分展示' },
  { id: 'bhava', name: 'Bhava Bala', tab: '扩展分析', status: 'app', detail: '宫位力量、宫主、Drig/Dig 维度' },
  { id: 'vimsopaka', name: 'Vimsopaka', tab: '扩展分析', status: 'app', detail: 'Dasa/Shodasa 分盘综合评分' },
  { id: 'varga', name: '分盘与频率', tab: '分盘 / 综合深度', status: 'app', detail: 'D9、D10、Vargottama、频率与三角验证' },
  { id: 'ashtakavarga', name: 'Ashtakavarga', tab: 'Ashtakavarga', status: 'app', detail: 'SAV/BAV、PAV、Sodhita 与 Yoga Pinda 贡献追溯' },
  { id: 'dasha', name: '多Dasha收敛', tab: 'Dasha', status: 'app', detail: 'Vimshottari 三级、35类Dasha总览、单系统时间线、当前/下一周期已在用户端展示' },
  { id: 'navamsa', name: 'Navamsa婚姻', tab: '分盘 / 完整解盘', status: 'app', detail: 'D9婚姻专题报告、八步旗标、Vargottama/Pushkara 与边界说明已展示' },
  { id: 'synthesis', name: '综合结论', tab: '完整解盘', status: 'app', detail: '把所有模块汇总为用户可读报告与审计表' },
];

const TECHNIQUES = [
  ['D1 / Rashi', '已接入', '本命盘、行星表、宫位分析'],
  ['D9 / D10 / 分盘', '已接入', '分盘 Tab、三角验证、Vargottama'],
  ['D9婚姻八步旗标', '已接入', 'D9上升、DK、Venus、D9七宫、Vargottama、Pushkara专题报告'],
  ['特殊Lagna / AL / UL / HL / GL', '已接入', '完整解盘已展示 AL/UL/A10/HL/GL/VL；本地 API 服务可返回日出校正版 HL/GL/VL，离线时保留本地简化兜底'],
  ['Vimshottari Dasha', '已接入', 'Mahadasha / Antardasha / Pratyantar'],
  ['35种Dasha', '已接入', '用户端已接入 Dasha 系统总览、分类筛选、单系统主周期时间线、当前/下一周期与精度说明'],
  ['Jaimini Karaka / Arudha', '已接入', 'Karaka、Arudha概览，A10/UL需专题化'],
  ['Functional Benefic/Malefic / 功能吉凶星', '已接入', '按 Lagna 输出功能吉星、功能凶星、Yogakaraka 与中性星，并进入 Technique Audit Table'],
  ['Argala', '已接入', '综合深度 Tab 已展示 Argala/Virodhargala 支持、阻挡和净分'],
  ['Shadbala', '已接入', '六维力量表；保留绝对值校准边界'],
  ['Ashtakavarga', '已接入', 'SAV/BAV、Transit AV'],
  ['KP / Sub-lord', '已接入', 'KP页已支持问题域筛选、重点宫位 ABCD significator、高权重证据解释、Sublord 表格与使用边界'],
  ['Synastry / Ashtakoot', '已接入', '合盘页已支持对方完整出生资料排盘、36分Ashtakoot、D9专题、Kuja Dosha平衡与Dasha同步；保留月亮黄经快算'],
  ['Prashna', '已接入', '问事页已展示 Prashna Lagna、KP三层判定、Arudha镜像、Nadi侧写、时机评分与下一步行动；Sphuta/Sahams/失物仍保留为进阶路线'],
  ['Remedies', '已接入', 'API自动返回补救建议；用户端已加入免责声明、低风险优先与7日执行计划'],
  ['生时矫正', '已接入', '事件输入、候选时间评分、证据闭环、摘要复制与推荐时间重新排盘已闭环'],
  ['MEVG外部验证', '已接入', '完整解盘已展示内部校验、外部检索项、置信度上限与预测边界'],
  ['PDF星盘输入', '已接入', '用户端已支持纯文本/文本层PDF上传、抽取、质量门控与自动填表'],
];

let capabilityAuditPromise = null;

const TECHNIQUE_API_ENDPOINTS = {
  chart: '/api/chart',
  kp: '/api/kp',
  prashna: '/api/prashna',
  synastry: '/api/synastry',
  ashtakoot: '/api/synastry',
  dasha: '/api/dasha',
  'chara-dasha': '/api/dasha/chara',
  remedies: '/api/remedies',
  sade_sati: '/api/sade_sati',
  pancha_mahapurusha: '/api/pancha_mahapurusha',
  career: '/api/career',
  relationship: '/api/relationship',
  'full-reading': '/api/chart',
  tajika: '/api/tajika',
  'solar-return': '/api/annual',
  muhurta: '/api/muhurta',
  'bhava-chalit': '/api/bhava_chalit',
  sudarshana: '/api/sudarshana',
  'nakshatra-full': '/api/nakshatra_full',
  'varga-full': '/api/varga_full',
  jaimini: '/api/jaimini',
  ashtakavarga: '/api/ashtakavarga',
  shadbala: '/api/shadbala',
  yoga: '/api/yogas',
  yogas: '/api/yogas',
  aspects: '/api/aspects',
  rectification: '/api/rectification_gate',
  'case-validation': '/api/case_validation',
  'divisional-yoga': '/api/divisional_yoga',
  'deep-varga-avastha': '/api/deep_varga_avastha',
  kakshya: '/api/kakshya',
  'bhava-bala': '/api/bhava_bala',
  'transit-trigger': '/api/transit',
  'thematic-report': '/api/thematic_report',
  'report-artifact': '/api/report_artifact',
};

const TECHNIQUE_COMMAND_ACTIONS = {
  'varga-full': 'varga',
  'solar-return': 'annual',
  tajika: 'annual',
  varshaphala: 'annual',
  muhurta: 'muhurta',
  muhurtha: 'muhurta',
  'bhava-chalit': 'bhava',
  sudarshana: 'sudarshana',
  'nakshatra-full': 'nakshatra',
  jaimini: 'jaimini',
  'chara-dasha': 'charaDasha',
  ashtakavarga: 'ashtakavarga',
  shadbala: 'shadbala',
  yoga: 'yogas',
  yogas: 'yogas',
  aspects: 'aspects',
  rectification: 'rectification',
  'case-validation': 'caseValidation',
  'divisional-yoga': 'divisionalYoga',
  'deep-varga-avastha': 'deepVargaAvastha',
  kakshya: 'kakshya',
  'bhava-bala': 'bhavaBala',
  'transit-trigger': 'transitTrigger',
  transit: 'transitTrigger',
  'thematic-report': 'thematicReport',
  career: 'career',
  relationship: 'relationship',
  kp: 'kpQuick',
  prashna: 'prashnaQuick',
  synastry: 'synastryQuick',
  ashtakoot: 'synastryQuick',
  dasha: 'dasha',
  remedies: 'remedies',
  sade_sati: 'sadeSati',
  'pancha_mahapurusha': 'panchaMahapurusha',
};

const TECHNIQUE_ID_ACTIONS = {
  vimshottari_dasha: 'dasha',
  remedies: 'remedies',
  sade_sati: 'sadeSati',
  pancha_mahapurusha: 'panchaMahapurusha',
  kp_system: 'kpQuick',
  prashna: 'prashnaQuick',
  prashna_integration: 'prashnaQuick',
  synastry_16factor: 'synastryQuick',
  full_reading_strict: 'thematicReport',
};

const TECHNIQUE_EXPLORER_PRIORITY = [
  'varga',
  'annual',
  'muhurta',
  'bhava',
  'sudarshana',
  'nakshatra',
  'jaimini',
  'ashtakavarga',
  'shadbala',
  'yogas',
  'aspects',
  'dasha',
  'remedies',
  'sadeSati',
  'panchaMahapurusha',
  'rectification',
  'caseValidation',
  'divisionalYoga',
  'kakshya',
  'bhavaBala',
  'transitTrigger',
  'thematicReport',
  'career',
  'relationship',
  'kpQuick',
  'prashnaQuick',
  'synastryQuick',
];

function statusClass(status) {
  if (status === 'app' || status === '已接入') return 'skill-status-ready';
  if (status === 'partial' || status === '部分接入') return 'skill-status-partial';
  return 'skill-status-pending';
}

function statusText(status) {
  return {
    app: '已在用户端承载',
    partial: '部分承载',
    engine: '引擎/Skill已覆盖',
  }[status] || status;
}

export function renderSkillCoverage(container, context = {}) {
  if (!container) return;
  const yogaCount = context.yogaCount ?? 0;
  const dashaCount = context.dashaCount ?? 1;
  const ready = MODULES.filter(m => m.status === 'app').length;
  const partial = MODULES.filter(m => m.status === 'partial').length;
  const engine = MODULES.filter(m => m.status === 'engine').length;

  const stageHtml = STAGES.map(([name, detail], index) => `
    <div class="skill-stage">
      <span class="skill-stage-index">${index + 1}</span>
      <div><strong>${escapeHtml(name)}</strong><p>${escapeHtml(detail)}</p></div>
    </div>
  `).join('');

  const moduleHtml = MODULES.map(m => `
    <div class="skill-module ${statusClass(m.status)}">
      <div class="skill-module-head">
        <strong>${escapeHtml(m.name)}</strong>
        <span>${escapeHtml(statusText(m.status))}</span>
      </div>
      <p>${escapeHtml(m.detail)}</p>
      <small>${escapeHtml(m.tab)}</small>
    </div>
  `).join('');

  const techniqueRows = TECHNIQUES.map(([name, status, note]) => `
    <tr>
      <td>${escapeHtml(name)}</td>
      <td><span class="skill-status ${statusClass(status)}">${escapeHtml(status)}</span></td>
      <td>${escapeHtml(note)}</td>
    </tr>
  `).join('');

  container.innerHTML = `
    <div class="skill-dashboard">
      <div class="skill-hero">
        <div>
          <h4>专业完整解盘</h4>
          <p>当前报告把核心星盘、分盘、Dasha、Yoga、力量评估、过境、补救与验证边界放在同一条解盘链路中，便于从总览继续进入各专题。</p>
        </div>
        <div class="skill-metrics">
          <span><b>${ready}</b>已承载</span>
          <span><b>${partial}</b>部分</span>
          <span><b>${engine}</b>待接入</span>
        </div>
      </div>

      <div class="skill-summary-grid">
        <div><strong>${escapeHtml(context.ascendant || '-')}</strong><span>上升</span></div>
        <div><strong>${escapeHtml(context.moonNakshatra || '-')}</strong><span>月亮星宿</span></div>
        <div><strong>${yogaCount}</strong><span>Yoga识别</span></div>
        <div><strong>${dashaCount}</strong><span>Dasha层级</span></div>
      </div>

      <section class="skill-section">
        <h4>完整工作流</h4>
        <div class="skill-stage-grid">${stageHtml}</div>
      </section>

      <section class="skill-section">
        <h4>12模块深度报告</h4>
        <div class="skill-module-grid">${moduleHtml}</div>
      </section>

      <section class="skill-section">
        <h4>Technique Audit Table</h4>
        <div class="skill-table-wrap">
          <table class="skill-audit-table">
            <thead><tr><th>技法</th><th>用户端状态</th><th>说明</th></tr></thead>
            <tbody>${techniqueRows}</tbody>
          </table>
        </div>
      </section>
    </div>
  `;
  renderTechniqueWorkbench(container, context);
  hydrateCapabilityAudit(container, context);
}

function renderTechniqueWorkbench(container, context = {}) {
  const host = container.querySelector('.skill-dashboard');
  if (!host || host.querySelector('.technique-workbench')) return;
  const chartData = context.chartData || {};
  const planets = chartData.planets || {};
  const hasChart = Object.keys(planets).length > 0;
  const actions = [
    ['varga', 'D81/D108/D144', '精微分盘'],
    ['annual', 'Varshaphala', '年运/Tajika'],
    ['muhurta', 'Muhurta', '今日择日'],
    ['bhava', 'Bhava Chalit', '宫位漂移'],
    ['sudarshana', 'Sudarshana', '三重Lagna'],
    ['nakshatra', 'Nakshatra+', '星宿深层'],
    ['jaimini', 'Jaimini', 'Karaka/Arudha'],
    ['charaDasha', 'Chara Dasha', 'Jaimini 应期'],
    ['ashtakavarga', 'Ashtakavarga', 'SAV/BAV'],
    ['shadbala', 'Shadbala', '六重力量'],
    ['yogas', 'Yogas', '格局检测'],
    ['aspects', 'Aspects', '精确相位'],
    ['rectification', '生时门控', '精度/分盘'],
    ['caseValidation', '案例验证', 'MEVG证据'],
    ['divisionalYoga', '分盘Yoga', 'D9/D10/D12'],
    ['deepVargaAvastha', '深层状态', 'Sayanadi/Shayanadi · D24/D30/D60'],
    ['kakshya', 'Kakshya', '度数触发'],
    ['bhavaBala', 'Bhava Bala', '宫位力量'],
    ['transitTrigger', '过境触发', '时间窗口'],
    ['thematicReport', '主题报告', '叙事/裁决'],
    ['career', '事业引擎', 'D10/10宫'],
    ['relationship', '感情引擎', '7宫/D9'],
    ['kpQuick', 'KP快读', 'Sublord'],
    ['prashnaQuick', '问事快读', '当下问题'],
    ['synastryQuick', '合盘快读', 'Ashtakoot'],
  ];
  const buttons = actions.map(([id, label, note], index) => `
    <button type="button" class="technique-action" data-action="${escapeAttr(id)}" ${hasChart ? '' : 'disabled'}>
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(note)}</span>
      <small>${index + 1}</small>
    </button>
  `).join('');
  const section = document.createElement('section');
  section.className = 'skill-section technique-workbench';
  section.innerHTML = `
    <div class="technique-workbench-head">
      <h4>高级技法工作台</h4>
      <span>${hasChart ? '本地 API 服务' : '等待星盘'}</span>
    </div>
    <div class="technique-action-grid">${buttons}</div>
    <div class="technique-result" aria-live="polite">
      <p>${hasChart ? '选择一个高级技法读取后端完整计算结果。' : '完成排盘后显示高级技法入口。'}</p>
    </div>
  `;
  host.appendChild(section);
  if (hasChart) bindTechniqueWorkbench(section, context);
}

function bindTechniqueWorkbench(section, context) {
  const resultHost = section.querySelector('.technique-result');
  const buttons = [...section.querySelectorAll('[data-action]')];
  for (const button of buttons) {
    button.addEventListener('click', async () => {
      if (!window.JyotishAPI) {
        resultHost.innerHTML = renderWorkbenchError('本地 API 服务未连接');
        return;
      }
      const action = button.dataset.action;
      buttons.forEach(btn => btn.classList.toggle('active', btn === button));
      button.classList.add('loading');
      resultHost.innerHTML = `<p>正在计算 ${escapeHtml(button.querySelector('strong')?.textContent || action)}...</p>`;
      try {
        const data = await runTechniqueAction(action, context);
        resultHost.innerHTML = renderTechniqueResult(action, data);
      } catch (error) {
        resultHost.innerHTML = renderWorkbenchError(error?.message || '高级技法计算失败');
      } finally {
        button.classList.remove('loading');
      }
    });
  }
}

async function runTechniqueAction(action, context) {
  const chartData = context.chartData || {};
  const base = {
    planets: chartData.planets || {},
    ascendant: chartData.ascendant || {},
  };
  if (action === 'varga') {
    return window.JyotishAPI.computeVargaFull({
      ...base,
      divisions: ['D81', 'D108', 'D144'],
    });
  }
  if (action === 'annual') {
    return window.JyotishAPI.computeAnnual({
      ...base,
      ...buildBirthPayload(context),
      target_year: new Date().getFullYear(),
    });
  }
  if (action === 'muhurta') {
    return window.JyotishAPI.computeMuhurta({
      ...base,
      date: new Date().toISOString().slice(0, 10),
    });
  }
  if (action === 'bhava') {
    return window.JyotishAPI.computeBhavaChalit({
      ...base,
      ...buildBirthPayload(context),
      mode: 'compare',
      house_system: resolveBhavaHouseSystem(context),
    });
  }
  if (action === 'sudarshana') {
    return window.JyotishAPI.computeSudarshana(base);
  }
  if (action === 'nakshatra') {
    return window.JyotishAPI.computeNakshatraFull({
      ...base,
      age: estimateAge(context),
    });
  }
  if (action === 'jaimini') {
    return window.JyotishAPI.computeJaimini({
      ...base,
      ...buildBirthPayload(context),
      mode: 'all',
    });
  }
  if (action === 'charaDasha') {
    return window.JyotishAPI.computeCharaDasha({
      ...base,
      ...buildBirthPayload(context),
      antardasha: true,
    });
  }
  if (action === 'ashtakavarga') {
    return window.JyotishAPI.computeAshtakavarga(base);
  }
  if (action === 'shadbala') {
    return window.JyotishAPI.computeShadbala({
      ...base,
      ...buildBirthPayload(context),
    });
  }
  if (action === 'yogas') {
    return window.JyotishAPI.computeYogas(base);
  }
  if (action === 'aspects') {
    return window.JyotishAPI.computeAspects(base);
  }
  if (action === 'dasha') {
    return window.JyotishAPI.computeDashaSystem({
      ...base,
      ...buildBirthPayload(context),
      dasha: 'vimshottari',
    });
  }
  if (action === 'remedies') {
    return window.JyotishAPI.computeRemedies({
      ...base,
      dasha: chartData.dasha || {},
      sade_sati: chartData.sade_sati || {},
    });
  }
  if (action === 'sadeSati') {
    return window.JyotishAPI.computeSadeSati({
      moon_degree: chartData.planets?.Moon?.lon ?? chartData.planets?.Moon?.degree ?? 0,
      asc_degree: chartData.ascendant?.lon ?? chartData.ascendant?.degree ?? 0,
      saturn_degree: chartData.transit?.Saturn?.lon ?? chartData.planets?.Saturn?.lon ?? chartData.planets?.Saturn?.degree ?? 0,
    });
  }
  if (action === 'panchaMahapurusha') {
    return window.JyotishAPI.computePanchaMahapurusha({
      planets: chartData.planets || {},
      sun_degree: chartData.planets?.Sun?.lon ?? chartData.planets?.Sun?.degree,
    });
  }
  if (action === 'rectification') {
    return window.JyotishAPI.computeRectificationGate({
      ...base,
      declared_accuracy: 'minute',
      time_source: 'family_clear',
    });
  }
  if (action === 'caseValidation') {
    return window.JyotishAPI.computeCaseValidation({
      ...base,
      current_md: chartData?.dasha?.current_md || chartData?.dasha?.current_dasha?.lord || '',
      predicted_events: inferValidationEvents(chartData),
      transit_desc: inferTransitDescription(chartData),
    });
  }
  if (action === 'divisionalYoga') {
    return window.JyotishAPI.computeDivisionalYoga({
      ...base,
      divisions: ['D9', 'D10', 'D12'],
    });
  }
  if (action === 'deepVargaAvastha') {
    return callTechniqueEndpoint('/api/deep_varga_avastha', base);
  }
  if (action === 'kakshya') {
    return window.JyotishAPI.computeKakshya(base);
  }
  if (action === 'bhavaBala') {
    return window.JyotishAPI.computeBhavaBala(base);
  }
  if (action === 'transitTrigger') {
    return window.JyotishAPI.computeTransitTriggers({
      natal_planets: chartData.planets || {},
      ascendant: chartData.ascendant || {},
      start: new Date().toISOString().slice(0, 10),
      end: new Date(Date.now() + 90 * 86400000).toISOString().slice(0, 10),
      planets_to_check: ['Saturn', 'Jupiter', 'Rahu', 'Ketu'],
    });
  }
  if (action === 'thematicReport') {
    return window.JyotishAPI.computeThematicReport({
      chart_data: chartData,
      themes: ['marriage', 'career', 'wealth', 'health', 'spirituality'],
    });
  }
  if (action === 'career') {
    return window.JyotishAPI.computeCareer({
      planets: chartData.planets || {},
      asc_sign: chartData.ascendant?.sign || 'Aries',
    });
  }
  if (action === 'relationship') {
    return window.JyotishAPI.computeRelationship({
      planets: chartData.planets || {},
      asc_sign: chartData.ascendant?.sign || 'Aries',
    });
  }
  if (action === 'kpQuick') {
    return window.JyotishAPI.computeKP({
      planets: chartData.planets || {},
      asc_sign_idx: chartData.ascendant?.sign_idx ?? signIndex(chartData.ascendant?.sign),
    });
  }
  if (action === 'prashnaQuick') {
    return window.JyotishAPI.computePrashna({
      planets: chartData.planets || {},
      question: 'general',
    });
  }
  if (action === 'synastryQuick') {
    const moon = chartData.planets?.Moon?.lon ?? chartData.planets?.Moon?.degree ?? 0;
    return window.JyotishAPI.computeSynastry({
      male_moon: moon,
      female_moon: (Number(moon) + 120) % 360,
    });
  }
  throw new Error(`未知技法: ${action}`);
}

function signIndex(sign) {
  const signs = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'];
  const index = signs.indexOf(sign);
  return index >= 0 ? index : 0;
}

function inferValidationEvents(chartData = {}) {
  const dasha = chartData.dasha || {};
  const events = [];
  const current = dasha.current_md || dasha.current_dasha?.lord;
  if (current === 'Jupiter') events.push('事业巅峰', '教育/法律成就', '全球影响力');
  if (current === 'Saturn') events.push('结构化成', '长期社会地位', '压力');
  if (current === 'Mars') events.push('行动力爆发', '竞争成就', '冲突');
  if (current === 'Venus') events.push('艺术创作', '关系发展', '美学/奢侈品');
  if (!events.length) events.push('事业巅峰', '关系发展');
  return events;
}

function inferTransitDescription(chartData = {}) {
  const asc = chartData.ascendant?.sign || '';
  if (asc) return `Double Jupiter Saturn activation around ${asc} ascendant`;
  return 'Double Jupiter Saturn';
}

function buildBirthPayload(context) {
  const birth = window.__jyotishBirth || {};
  const birthInfo = context.birthInfo || context.chartData?.birth_info || {};
  const dateParts = String(birthInfo.date || '').split('-').map(Number);
  const timeParts = String(birthInfo.time || '').split(':').map(Number);
  return {
    year: pickNumber(birth.year, dateParts[0], 1990),
    month: pickNumber(birth.month, dateParts[1], 1),
    day: pickNumber(birth.day, dateParts[2], 1),
    hour: pickNumber(birth.hour, timeParts[0], 12),
    minute: pickNumber(birth.minute, timeParts[1], 0),
    lat: pickNumber(birth.lat, birthInfo.lat, 0),
    lon: pickNumber(birth.lon, birthInfo.lon, 0),
    tz: pickNumber(birth.tz, parseTimezone(birthInfo.tz), 0),
  };
}

function pickNumber(...values) {
  for (const value of values) {
    if (value == null || value === '') continue;
    const number = Number(value);
    if (Number.isFinite(number)) return number;
  }
  const fallback = Number(values[values.length - 1]);
  return Number.isFinite(fallback) ? fallback : 0;
}

function parseTimezone(value) {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  const match = String(value || '').match(/UTC\s*([+-]\d+(?:\.\d+)?)(?::(\d+))?/i);
  if (!match) return 0;
  const hours = Number(match[1]);
  const minutes = Number(match[2] || 0) / 60;
  const sign = match[1].trim().startsWith('-') ? -1 : 1;
  return hours + sign * minutes;
}

function estimateAge(context) {
  const birth = window.__jyotishBirth || {};
  const birthInfo = context.birthInfo || context.chartData?.birth_info || {};
  const birthYear = Number(birth.year || String(birthInfo.date || '').slice(0, 4));
  if (!Number.isFinite(birthYear) || birthYear < 1800) return undefined;
  return Math.max(0, new Date().getFullYear() - birthYear);
}

function renderTechniqueResult(action, data) {
  if (action === 'varga') return renderVargaTechniqueResult(data);
  if (action === 'annual') return renderAnnualTechniqueResult(data);
  if (action === 'muhurta') return renderMuhurtaTechniqueResult(data);
  if (action === 'ashtakavarga') return renderAshtakavargaTechniqueResult(data);
  if (action === 'shadbala') return renderShadbalaTechniqueResult(data);
  if (action === 'yogas') return renderYogaTechniqueResult(data);
  if (action === 'dasha') return renderDashaTechniqueResult(data);
  if (action === 'remedies') return renderRemediesExplorerResult(data);
  if (action === 'sadeSati') return renderDomainEngineResult('Sade Sati 土星周期', data, '只把 Sade Sati 作为土星主题窗口，仍需结合本命承诺与 Dasha。');
  if (action === 'panchaMahapurusha') return renderDomainEngineResult('Pancha Mahapurusha 五王瑜伽', data, '确认行星尊严、宫位和实际强度后再写成优势主题。');
  if (action === 'rectification') return renderRectificationGateResult(data);
  if (action === 'caseValidation') return renderCaseValidationResult(data);
  if (action === 'divisionalYoga') return renderDivisionalYogaResult(data);
  if (action === 'deepVargaAvastha') return renderDeepVargaAvasthaResult(data);
  if (action === 'kakshya') return renderKakshyaResult(data);
  if (action === 'bhava') return renderBhavaChalitResult(data);
  if (action === 'bhavaBala') return renderBhavaBalaResult(data);
  if (action === 'transitTrigger') return renderTransitTriggerResult(data);
  if (action === 'thematicReport') return renderThematicReportResult(data);
  if (action === 'career') return renderDomainEngineResult('事业引擎', data, '优先把强项领域和当前 Dasha/Transit 对齐，避免只按10宫单点下结论。');
  if (action === 'relationship') return renderDomainEngineResult('感情引擎', data, '把7宫、Venus、DK、UL、D9 与双方现实关系状态一起判断。');
  if (action === 'kpQuick') return renderKPQuickResult(data);
  if (action === 'prashnaQuick') return renderPrashnaQuickResult(data);
  if (action === 'synastryQuick') return renderSynastryQuickResult(data);
  const payload = data?.report || data?.result || data || {};
  const rows = Object.entries(payload).slice(0, 8).map(([key, value]) => `
    <div class="technique-result-row">
      <span>${escapeHtml(formatKey(key))}</span>
      <strong>${escapeHtml(formatMiniValue(value))}</strong>
    </div>
  `).join('');
  return `
    <div class="technique-result-head">
      <strong>${escapeHtml(resultTitle(action))}</strong>
      <span>${escapeHtml(data?.mode || data?.endpoint || 'complete')}</span>
    </div>
    <div class="technique-result-grid">${rows || '<p>后端已返回结果。</p>'}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(payload, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderVargaTechniqueResult(data) {
  const charts = Object.entries(data?.result || {});
  const cards = charts.map(([key, chart]) => {
    const asc = chart?.ascendant || {};
    const moon = chart?.planets?.Moon || {};
    return `
      <div class="technique-varga-card">
        <span>${escapeHtml(key.replace(/^D(\d+)_/, 'D$1 · '))}</span>
        <strong>${escapeHtml(asc.sign || '-')} ${escapeHtml(formatDegree(asc.degree))}</strong>
        <small>Moon: ${escapeHtml(moon.sign || '-')} ${escapeHtml(formatDegree(moon.degree))} · H${escapeHtml(moon.house || '-')}</small>
      </div>
    `;
  }).join('');
  return `
    <div class="technique-result-head">
      <strong>D81/D108/D144 精微分盘</strong>
      <span>${escapeHtml(data?.source || 'varga')}</span>
    </div>
    <div class="technique-varga-grid">${cards}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data?.result || {}, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderWorkbenchError(message) {
  return `
    <div class="technique-error">
      <strong>计算失败</strong>
      <p>${escapeHtml(message)}</p>
      <small>先到 Trust Center 运行健康检查；若本地 API 未连接，请按 README 的普通用户启动路径启动网页服务和本地 API 服务后重试。</small>
    </div>
  `;
}

function resultTitle(action) {
  return {
    annual: 'Varshaphala / Tajika',
    muhurta: 'Muhurta',
    bhava: 'Bhava Chalit',
    sudarshana: 'Sudarshana Chakra',
    nakshatra: 'Nakshatra 深层报告',
    jaimini: 'Jaimini 系统',
    ashtakavarga: 'Ashtakavarga',
    shadbala: 'Shadbala 六重力量',
    yogas: 'Yoga 格局检测',
    aspects: '精确相位',
    rectification: '生时精度门控',
    caseValidation: '案例验证 / MEVG',
    divisionalYoga: '分盘 Yoga',
    kakshya: 'Kakshya 度数触发',
    bhavaBala: 'Bhava Bala 宫位力量',
    transitTrigger: 'Transit Trigger',
    thematicReport: '主题化报告',
    career: '事业专题',
    relationship: '感情专题',
    kpQuick: 'KP Sublord',
    prashnaQuick: 'Prashna 问事',
    synastryQuick: 'Ashtakoot 合盘',
  }[action] || action;
}

function renderAnnualTechniqueResult(data) {
  const report = data?.report || {};
  const muntha = report.muntha || {};
  const yearLord = report.year_lord || report.varshesha || {};
  const tajikaYogas = report.tajika_yogas || {};
  const tajikaStrength = report.tajika_strength || {};
  const strengthSummary = tajikaStrength.summary || {};
  const strongestPlanet = strengthSummary.strongest_planets?.[0];
  const weakestPlanet = strengthSummary.weakest_planets?.[0];
  const yogaCount = Array.isArray(tajikaYogas) ? tajikaYogas.length : (tajikaYogas.yogas?.length || tajikaYogas.count || 0);
  const cards = [
    ['年度主题', annualTheme(report, muntha), 'Muntha / Solar Return'],
    ['Muntha', formatMuntha(muntha), muntha.formula || '年度上升点每年前进一宫'],
    ['年度主星', yearLord.year_lord || yearLord.lord || yearLord.planet || '-', yearLord.year_theme || yearLord.reason || '用于判断年度主导行星'],
    ['Tajika Yoga', `${yogaCount} 项`, '作为年度事件触发与强弱判断的证据层'],
    ['年度强度', formatTajikaStrengthPlanet(strongestPlanet), 'Harsha Bala / Panchavargiya Bala 最强行星'],
    ['年度风险', formatTajikaStrengthPlanet(weakestPlanet), '综合强度较低，需用 Dasha/Transit 复核'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  return `
    <div class="technique-result-head">
      <strong>Varshaphala / Tajika 年运</strong>
      <span>${escapeHtml(report.target_year || report.report_year || data?.endpoint || 'annual')}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    ${renderTajikaStrengthCards(tajikaStrength)}
    <div class="technique-next-action">下一步：结合当前 Dasha 与 Transit，只把年度盘作为“今年主题和触发方向”，不要单独当作事件承诺。</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(report, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderTajikaStrengthCards(tajikaStrength = {}) {
  if (!tajikaStrength?.method || tajikaStrength.error) {
    return '';
  }
  const summary = tajikaStrength.summary || {};
  const strongest = summary.strongest_planets || [];
  const weakest = summary.weakest_planets || [];
  const combinedStrength = tajikaStrength.combined_strength || {};
  const rows = Object.entries(combinedStrength)
    .sort(([, a], [, b]) => (b?.score || 0) - (a?.score || 0))
    .slice(0, 7)
    .map(([planet, item]) => {
      const components = item.components || {};
      return `
        <div class="technique-evidence-row">
          <strong>${escapeHtml(planet)}</strong>
          <span>${escapeHtml(item.grade || '-')} · ${escapeHtml(item.score ?? '-')} / ${escapeHtml(item.max_score ?? '-')}</span>
          <small>Harsha Bala ${escapeHtml(components.harsha_bala ?? '-')} · Panchavargiya Bala ${escapeHtml(components.panchavargiya_bala ?? '-')}</small>
        </div>
      `;
    }).join('');
  const evidence = [
    strongest[0] ? `最强：${formatTajikaStrengthPlanet(strongest[0])}` : null,
    weakest[0] ? `需复核：${formatTajikaStrengthPlanet(weakest[0])}` : null,
    summary.headline,
  ].filter(Boolean);
  return `
    <div class="technique-evidence-strip">${evidence.map(item => `<span>${escapeHtml(item)}</span>`).join('')}</div>
    <details class="technique-json" open>
      <summary>Harsha Bala / Panchavargiya Bala</summary>
      <div>${rows || '<div class="technique-muted">暂无年度强度数据</div>'}</div>
    </details>
  `;
}

function formatTajikaStrengthPlanet(item) {
  if (!item) return '待计算';
  const score = item.score == null ? '-' : item.score;
  const maxScore = item.max_score == null ? '-' : item.max_score;
  return `${item.planet || '-'} · ${item.grade || '-'} · ${score}/${maxScore}`;
}

function renderMuhurtaTechniqueResult(data) {
  const report = data?.report || {};
  const rangeSearch = data?.range_search || report.range_search || {};
  const summary = report.summary || {};
  const panchanga = report.panchanga || {};
  const best = summary.best_activities || [];
  const avoid = summary.avoid_activities || [];
  const cards = [
    ['整体质量', `${summary.overall_quality || '-'} · ${formatPercent(summary.overall_score)}`, `${summary.auspicious_elements ?? 0}/${panchanga.total_elements || 6} 个 Panchanga 要素偏吉`],
    ['适合活动', best.length ? best.join(' / ') : '暂无明显优先项', '按 Tithi、Nakshatra、Vara 等规则筛选'],
    ['谨慎活动', avoid.length ? avoid.join(' / ') : '暂无硬性避开项', '若有 Dosha 或不吉 Yoga，应降级处理'],
    ['Abhijit', report.abhijit_muhurta?.time_range || '约 48 分钟窗口', report.abhijit_muhurta?.warning || '仍需结合当地日出日落精算'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  const evidence = [
    panchanga.tithi?.full_name || panchanga.tithi?.name,
    panchanga.nakshatra?.nakshatra,
    panchanga.yoga?.yoga,
    panchanga.vara?.vara,
  ].filter(Boolean);
  return `
    <div class="technique-result-head">
      <strong>Muhurta 择日</strong>
      <span>${escapeHtml(report.query_date || data?.endpoint || 'today')}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-evidence-strip">${evidence.map(item => `<span>${escapeHtml(item)}</span>`).join('')}</div>
    ${renderMuhurtaRangeSolver(rangeSearch)}
    <div class="technique-next-action">下一步：若用于婚礼、手术、签约等高风险活动，继续输入具体活动和当地日出后的小时，避免只看“今日整体”。</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(report, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderMuhurtaRangeSolver(rangeSearch = {}) {
  if (rangeSearch.mode !== 'muhurta_date_range_solver') return '';
  const bestWindows = rangeSearch.best_windows || [];
  const rejectedDates = rangeSearch.rejected_dates || [];
  const candidates = bestWindows.slice(0, 5).map(item => {
    const windows = (item.recommended_windows || []).slice(0, 3)
      .map(win => `${win.name || win.type} ${win.start || ''}-${win.end || ''}`)
      .join(' / ');
    const panchanga = item.evidence?.panchanga || {};
    return `
      <div class="technique-evidence-row">
        <strong>${escapeHtml(item.date || '-')} · ${escapeHtml(item.quality || '-')} · ${escapeHtml(item.score ?? '-')}</strong>
        <span>${escapeHtml(item.activity_verdict || '活动结论待确认')}</span>
        <small>${escapeHtml(windows || '暂无干净窗口')} · ${escapeHtml(panchanga.tithi || '-')} · ${escapeHtml(panchanga.nakshatra || '-')}</small>
      </div>
    `;
  }).join('');
  const rejected = rejectedDates.slice(0, 4)
    .map(item => `${item.date}: ${item.reason}`)
    .join('；');
  return `
    <details class="technique-json" open>
      <summary>范围择日 · 择日候选</summary>
      <div class="technique-evidence-strip">
        <span>${escapeHtml(rangeSearch.activity_label || rangeSearch.activity || '-')}</span>
        <span>${escapeHtml(rangeSearch.date_range?.start || '-')} - ${escapeHtml(rangeSearch.date_range?.end || '-')}</span>
        <span>${escapeHtml(rangeSearch.candidate_count ?? 0)} / ${escapeHtml(rangeSearch.scanned_days ?? 0)} 个候选</span>
      </div>
      <div>${candidates || '<div class="technique-muted">暂无可推荐候选</div>'}</div>
      ${rejected ? `<small class="technique-method-boundary">已过滤：${escapeHtml(rejected)}</small>` : ''}
    </details>
  `;
}

function renderAshtakavargaTechniqueResult(data) {
  const summary = data?.summary || {};
  const pavSummary = data?.pav_summary || summary.pav_summary || {};
  const sodhitaSummary = data?.sodhita_summary || summary.sodhita_summary || {};
  const yogaPindaSummary = data?.yoga_pinda_summary || summary.yoga_pinda_summary || {};
  const strongest = summary.strongest_houses || [];
  const weakest = summary.weakest_houses || [];
  const topPav = pavSummary.top_planets || [];
  const topSodhita = sodhitaSummary.top_signs || [];
  const topYogaPinda = yogaPindaSummary.top_planets || [];
  const cards = [
    ['SAV结论', summary.headline || '-', `总分 ${summary.sav_total ?? '-'} · 校验 ${summary.sav_valid === false ? '需复核' : '通过'}`],
    ['最强宫位', strongest.map(item => `H${item.house}:${item.sign} ${item.score}`).join(' / ') || '-', '优先承载事件和结果的领域'],
    ['谨慎宫位', weakest.map(item => `H${item.house}:${item.sign} ${item.score}`).join(' / ') || '-', '需要Dasha/Transit确认后再判断'],
    ['Sodhita', sodhitaSummary.headline || '-', topSodhita.map(item => `${item.sign}:${item.score}`).join(' / ') || '净化分未返回'],
    ['Yoga Pinda', yogaPindaSummary.headline || '-', topYogaPinda.map(item => `${item.planet}:${item.yoga_pinda}`).join(' / ') || 'Pinda未返回'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  const evidence = [
    pavSummary.validation_passed === false ? 'PAV校验需复核' : 'PAV校验通过',
    yogaPindaSummary.validation_passed === false ? 'Yoga Pinda需复核' : 'Yoga Pinda校验通过',
    ...topPav.map(item => `${item.planet}:${item.total}`),
    `扣减:${sodhitaSummary.reduction_total ?? 0}`,
  ].filter(Boolean);
  return `
    <div class="technique-result-head">
      <strong>Ashtakavarga / PAV / Sodhita / Yoga Pinda</strong>
      <span>${escapeHtml(data?.endpoint || 'ashtakavarga')}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-evidence-strip">${evidence.map(item => `<span>${escapeHtml(item)}</span>`).join('')}</div>
    <div class="technique-next-action">${escapeHtml(summary.next_action || '先看SAV领域强弱，再用PAV、Sodhita和Yoga Pinda追溯证据。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderShadbalaTechniqueResult(data) {
  const result = data?.result || {};
  const planets = result.planets || {};
  const advanced = data?.advanced_layer || {};
  const strongest = result.strongest || result.ranking?.[0] || '-';
  const weakest = result.weakest || result.ranking?.[result.ranking.length - 1] || '-';
  const yuddha = advanced.active_yuddha || {};
  const topKala = advanced.top_kala_support || [];
  const drik = advanced.sputa_drik_bala || {};
  const cards = [
    ['最强/最弱', `${strongest} / ${weakest}`, `排名 ${formatMiniValue(result.ranking || [])}`],
    ['主算法', result.method || 'Shadbala六重力量', '保留原总分和排名，不被增强层覆盖'],
    ['Kala增强', topKala.map(item => `${item.planet}:${item.virupas}`).join(' / ') || '无额外时间力量', 'Varsha/Maasa/Dina/Hora 子项证据'],
    ['Yuddha/Sputa', Object.keys(yuddha).length ? formatMiniValue(yuddha) : strongestScore(drik), '交战力量与连续相位力量作为复核证据'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  const evidence = [
    ...(data?.rule_variants?.selected || []),
    ...Object.entries(planets).slice(0, 4).map(([planet, item]) => `${planet}:${item.strength_level || item.total_rupas}`),
  ].filter(Boolean);
  return `
    <div class="technique-result-head">
      <strong>Shadbala 六重力量</strong>
      <span>${escapeHtml(advanced.source ? 'advanced layer' : data?.endpoint || 'shadbala')}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-evidence-strip">${evidence.map(item => `<span>${escapeHtml(item)}</span>`).join('')}</div>
    <div class="technique-next-action">${escapeHtml(advanced.next_action || data?.rule_variants?.boundary || '先看主排名，再用高级层解释冲突。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderYogaTechniqueResult(data) {
  const result = data?.result || data || {};
  const summary = result.summary || {};
  const curse = result.curse_yogas || {};
  const curses = curse.curses_detected || [];
  const firstCurse = curses[0] || {};
  const selectedVariants = data?.rule_variants?.selected || result.rule_variants?.selected || ['extended_algorithm', 'json_rule_engine', 'curse_conjunctions'];
  const cards = [
    ['扩展算法', `${summary.extended_count ?? (result.extended_yogas || []).length ?? 0} 项`, 'scripts/yoga_expansion.py'],
    ['JSON规则', `${summary.rule_engine_count ?? (result.rule_engine_yogas || []).length ?? 0} 项`, 'references/yoga_rules.json'],
    ['凶星合相', `${summary.curse_count ?? curses.length} 项 · ${curse.overall_risk || 'low'}`, firstCurse.name_cn || firstCurse.name || '未发现高风险合相'],
    ['规则口径', formatMiniValue(selectedVariants), data?.rule_variants?.boundary || result.rule_variants?.boundary || '多套规则并行展示'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  const evidence = curses.slice(0, 5).map(item => `${item.name_cn || item.name}:${item.severity_label || item.severity}`);
  return `
    <div class="technique-result-head">
      <strong>Yoga 格局检测</strong>
      <span>${escapeHtml(data?.ascendant || data?.endpoint || 'yogas')}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-evidence-strip">${evidence.map(item => `<span>${escapeHtml(item)}</span>`).join('')}</div>
    <div class="technique-next-action">${escapeHtml(curse.narrative ? '凶星合相仅作为风险提示层，必须与 Dasha、Transit、现实事件共同验证。' : '继续用 Dasha/Transit 验证 Yoga 是否有时间窗口。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(result, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderDashaTechniqueResult(data) {
  const periods = data?.periods || [];
  const current = periods[0] || {};
  const next = periods[1] || {};
  const analysis = data?.vimshottari_analysis || {};
  const active = analysis.current || {};
  const md = active.mahadasha || {};
  const ad = active.antardasha || {};
  const levels = analysis.five_levels || {};
  const cards = [
    ['系统', data?.name || data?.key || 'Dasha', `${data?.precision || '-'} · ${data?.cycle_years || '-'}年循环`],
    ['当前MD/AD', md.lord ? `${md.lord} / ${ad.lord || '-'}` : (current.lord || current.name || '-'), md.start ? `${md.start} → ${md.end}` : `${current.start || current.start_date || '-'} → ${current.end || current.end_date || '-'}`],
    ['五级层级', renderDashaLevelLine(levels), active.remaining_days != null ? `当前小运剩余约 ${active.remaining_days} 天` : `${next.lord || next.name || '-'} 下一周期`],
    ['返回周期', `${periods.length}段`, analysis.source || '用于时间线，不单独代表事件承诺'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  const evidence = [
    analysis.nakshatra?.name ? `Moon:${analysis.nakshatra.name} P${analysis.nakshatra.pada}` : '',
    ...(active.keywords || []).slice(0, 4),
    ...(data?.fragment_sources || []),
  ].filter(Boolean);
  return `
    <div class="technique-result-head">
      <strong>Dasha API Explorer</strong>
      <span>${escapeHtml(data?.key || 'vimshottari')}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-evidence-strip">${evidence.map(item => `<span>${escapeHtml(item)}</span>`).join('')}</div>
    <div class="technique-next-action">${escapeHtml(analysis.summary?.next_action || '下一步：把 Dasha 只作为时间主轴，再用本命承诺、Transit 与案例验证收敛。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderDashaLevelLine(levels = {}) {
  const ordered = ['mahadasha', 'bhukti', 'pratyantar', 'sookshma', 'prana'];
  const labels = ordered.map(key => levels[key]?.lord).filter(Boolean);
  return labels.length ? labels.join(' / ') : '-';
}

function renderRemediesExplorerResult(data) {
  const source = data?.remedies || data?.result || data || {};
  const gemstone = source.gemstone || source.gemstones || {};
  const mantra = source.mantra || source.mantras || {};
  const actions = source.actions || source.behavioral_remedies || source.low_risk_actions || [];
  const evidence = source.evidence_chain || source.evidence || [];
  const cards = [
    ['原则', source.priority || source.policy || '低风险优先', '补救建议不能替代医疗、法律、投资或心理咨询'],
    ['宝石', formatMiniValue(gemstone), '高成本/身体接触类建议必须二次确认'],
    ['Mantra', formatMiniValue(mantra), '优先选择低风险、可停止的练习'],
    ['执行项', formatMiniValue(actions), `${Array.isArray(evidence) ? evidence.length : 0} 条证据链`],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  return `
    <div class="technique-result-head">
      <strong>Remedies API Explorer</strong>
      <span>${escapeHtml(data?.endpoint || 'remedies')}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-next-action">${escapeHtml(source.next_action || '先执行低风险行动，观察7天后再升级。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(source, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderThematicReportResult(data) {
  const themes = data?.themes || {};
  const entries = Object.entries(themes);
  const workflow = data?.workflow_orchestration || {};
  const evidenceSource = data?.evidence_source || {};
  const moduleStatus = evidenceSource.module_status || {};
  const fragmentSources = data?.fragment_sources || ['report_orchestrator.py', 'reading_orchestrator.py', 'orchestrator_bridge.py'];
  const fullReadingBadge = evidenceSource.full_reading_used
    ? `full-reading:${evidenceSource.full_reading_module_count || 0} modules`
    : '';
  const themeLabels = {
    marriage: '婚姻',
    career: '事业',
    wealth: '财富',
    health: '健康',
    spirituality: '灵性',
  };
  const cards = entries.map(([key, report]) => {
    const timing = report?.timing || {};
    const evidence = Array.isArray(report?.evidence) ? report.evidence : [];
    const recommendations = Array.isArray(report?.recommendations) ? report.recommendations : [];
    return `
      <article class="thematic-report-card">
        <div class="thematic-report-card-head">
          <strong>${escapeHtml(themeLabels[key] || key)}</strong>
          <span>${escapeHtml(report?.strength || '-')}</span>
        </div>
        <p>${escapeHtml(report?.summary || '-')}</p>
        <small>${escapeHtml(timing.dasha_period ? `${timing.dasha_period} · ${timing.start_year}-${timing.end_year}` : '未返回明确时间锚点')}</small>
        <div class="thematic-report-evidence">
          ${evidence.slice(0, 3).map(item => `<span>${escapeHtml(item.technique || item.chart || 'evidence')}</span>`).join('')}
        </div>
        <ul>
          ${recommendations.slice(0, 2).map(item => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </article>
    `;
  }).join('');
  return `
    <div class="technique-result-head">
      <strong>主题化报告 / 冲突裁决</strong>
      <span>${escapeHtml(data?.mode || data?.endpoint || 'thematic')}</span>
    </div>
    <div class="technique-evidence-strip">${[
      evidenceSource.source,
      fullReadingBadge,
      evidenceSource.sample_fallback ? 'sample fallback' : 'real evidence path',
      evidenceSource.warning_count ? `${evidenceSource.warning_count} warnings` : '',
      ...Object.entries(moduleStatus).slice(0, 6).map(([key, value]) => `${key}:${value}`),
    ].filter(Boolean).map(item => `<span>${escapeHtml(item)}</span>`).join('')}</div>
    <div class="thematic-report-grid">${cards || '<p>后端已返回主题化报告。</p>'}</div>
    <div class="technique-evidence-strip">${[
      ...fragmentSources,
      workflow.bridge?.class,
      workflow.stage,
    ].filter(Boolean).map(item => `<span>${escapeHtml(item)}</span>`).join('')}</div>
    <div class="technique-next-action">${escapeHtml(data?.boundary || '主题报告负责组织证据与叙事，仍需 Dasha、Transit、案例验证共同收敛。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderRectificationGateResult(data) {
  const summary = data?.summary || {};
  const lagna = data?.lagna_boundary || {};
  const asc = data?.ascendant || {};
  const cards = [
    ['结论', summary.headline || '-', lagna.note || `${asc.sign || '-'} ${formatDegree(asc.degree_in_sign)}`],
    ['有效精度', data?.effective_accuracy || '-', `声明：${data?.declared_accuracy || '-'}；来源：${data?.time_source || '-'}`],
    ['可用分盘', (summary.enabled || []).join(' / ') || '-', '这些分盘可正常进入解释层'],
    ['需谨慎/禁用', [...(summary.warned || []), ...(summary.disabled || [])].join(' / ') || '无', summary.confidence_floor || '按出生时间可信度降级'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  const events = summary.recommended_events || [];
  return `
    <div class="technique-result-head">
      <strong>生时精度门控</strong>
      <span>${lagna.is_sensitive ? 'sensitive' : 'stable'}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-evidence-strip">${events.map(item => `<span>${escapeHtml(formatEventType(item))}</span>`).join('')}</div>
    <div class="technique-next-action">${escapeHtml(summary.next_action || '补充事件后再做高敏分盘判断。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderCaseValidationResult(data) {
  const summary = data?.summary || {};
  const result = data?.result || {};
  const gate = data?.mevg_gate || {};
  const fragmentSources = data?.fragment_sources || ['case_validator.py', 'mevg_automation.py'];
  const cards = [
    ['验证结论', summary.headline || '-', `${summary.overall_confidence ?? 0}% overall confidence`],
    ['通过/待证', `${summary.validated_count ?? 0} / ${summary.unvalidated_count ?? 0}`, summary.case_base || result.case_base || '本地案例库'],
    ['MEVG门控', gate.gate_status || summary.gate_status || '-', `失败率 ${gate.fail_rate ?? 0} · 阈值 ${gate.threshold ?? '-'}`],
    ['下一步', summary.next_action || '-', '未验证项不得写成确定预测'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  const validations = result.validations || [];
  const evidence = [
    ...validations.slice(0, 5).map(item => `${item.type || 'rule'}:${item.validated ? 'ok' : 'wait'}`),
    ...fragmentSources,
  ];
  return `
    <div class="technique-result-head">
      <strong>案例验证 / MEVG</strong>
      <span>${escapeHtml(data?.endpoint || 'case')}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-evidence-strip">${evidence.map(item => `<span>${escapeHtml(item)}</span>`).join('')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderDivisionalYogaResult(data) {
  const summary = data?.summary || {};
  const result = data?.result || {};
  const divisionCards = Object.entries(result).map(([division, item]) => {
    const first = (item.yogas || [])[0];
    const note = first ? `${first.name || '-'} · ${first.description || ''}` : '暂无强 Yoga 命中';
    return renderInsightCard(division, `${item.yoga_count || 0} 项`, note);
  }).join('');
  return `
    <div class="technique-result-head">
      <strong>分盘 Yoga 检测</strong>
      <span>${escapeHtml(data?.ascendant || 'varga')}</span>
    </div>
    <div class="technique-insight-grid">
      ${renderInsightCard('结论', summary.headline || '-', `${summary.total_yogas ?? 0} 个 D9/D10/D12 命中`)}
      ${divisionCards}
    </div>
    <div class="technique-next-action">${escapeHtml(summary.next_action || '分盘 Yoga 只作为对应领域的辅助证据。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderDeepVargaAvasthaResult(data) {
  const report = data?.report || data || {};
  const summary = report.summary || {};
  const avasthaSummary = report.avastha_summary || {};
  const deepVargaTemplates = report.deep_varga_templates || {};
  const dominantStates = avasthaSummary.dominant_states || [];
  const priorityCards = summary.priority_cards || [];
  const cards = [
    ['结论', summary.headline || '-', 'Sayanadi/Shayanadi 与 D24/D30/D60 综合'],
    ['主导状态', dominantStates.map(item => `${item.state}:${item.count}`).join(' / ') || '-', 'dominant_states'],
    ['弱状态行星', (avasthaSummary.weak_planets || []).map(item => `${item.planet}:${item.state}`).join(' / ') || '暂无', 'Avastha 低活跃或 Bala 偏弱'],
    ['深分盘', Object.keys(deepVargaTemplates).join(' / ') || 'D24/D30/D60', 'D24/D30/D60 deep_varga_templates'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  const templateRows = Object.entries(deepVargaTemplates).map(([division, item]) => {
    const templateCards = item.template_cards || [];
    const riskFlags = item.risk_flags || [];
    const firstCards = templateCards.slice(0, 3).map(card => `${card.planet} H${card.house} ${card.sign}`).join(' / ');
    return `
      <div class="technique-evidence-row">
        <strong>${escapeHtml(division)} · ${escapeHtml(item.title || item.theme || '-')}</strong>
        <span>${escapeHtml(firstCards || '暂无关键行星')}</span>
        <small>${escapeHtml(riskFlags.length)} 个 risk_flags · ${escapeHtml(item.next_action || '')}</small>
      </div>
    `;
  }).join('');
  const priority = priorityCards.map(card => `<span>${escapeHtml(card.title || '-')}：${escapeHtml(card.value || '-')}</span>`).join('');
  return `
    <div class="technique-result-head">
      <strong>Sayanadi/Shayanadi · D24/D30/D60</strong>
      <span>${escapeHtml(data?.endpoint || report.method || 'deep_varga_avastha')}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-evidence-strip">${priority || '<span>深层状态解释层</span>'}</div>
    <details class="technique-json" open>
      <summary>D24/D30/D60 模板</summary>
      <div>${templateRows || '<div class="technique-muted">暂无深分盘模板数据</div>'}</div>
    </details>
    <div class="technique-next-action">${escapeHtml(summary.next_action || '深分盘和 Avastha 只作为侧证，需要与 D1、Dasha、Transit 同读。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(report, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderKakshyaResult(data) {
  const summary = data?.summary || {};
  const strongest = summary.strongest || [];
  const weakest = summary.weakest || [];
  const cards = [
    ['结论', summary.headline || '-', `平均强度 ${summary.average_strength ?? '-'}`],
    ['最强触发', strongest.map(item => `${item.planet}:${item.kakshya_lord}`).join(' / ') || '-', '这些行星所在度数区间支持度较高'],
    ['需谨慎', weakest.map(item => `${item.planet}:${item.kakshya_lord}`).join(' / ') || '-', '行运触发时不宜放大单点结论'],
    ['区间单位', `${data?.result?.kakshya_span || 3.75}°`, '每个星座分为 8 个 Kakshya 区间'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  return `
    <div class="technique-result-head">
      <strong>Kakshya 度数触发</strong>
      <span>${escapeHtml(data?.ascendant || 'ashtakavarga')}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-next-action">${escapeHtml(summary.next_action || '只在已有主题承诺时用 Kakshya 细化触发窗口。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderBhavaChalitResult(data) {
  const result = data?.result || {};
  const summary = result.summary || {};
  const selected = data?.selected_house_system || result.selected_house_system || result.house_system || '-';
  const requested = data?.requested_house_system || result.requested_house_system || selected;
  const available = data?.available_house_systems || result.available_house_systems || [];
  const systemLabels = {
    sripati: 'Sripati',
    placidus: 'Placidus',
    equal: 'Equal House',
    whole_sign: 'Whole Sign',
    porphyry: 'Porphyry',
    koch: 'Koch',
  };
  const shifts = result.shifts || [];
  const firstHouse = result.boundaries?.houses?.[0];
  const cards = [
    ['宫位制', systemLabels[selected] || selected, requested === selected ? '使用用户选择的 houseSystem' : `请求 ${requested}，实际 ${selected}`],
    ['可选系统', available.map(item => systemLabels[item] || item).join(' / ') || '-', 'Sripati 与 Placidus 可从 Calculation Settings 切换'],
    ['迁移行星', `${summary.shifted_count ?? result.shifted_count ?? shifts.length} / ${summary.total_planets ?? Object.keys(result.rashi_chart || {}).length}`, shifts.slice(0, 3).map(item => `${item.planet}:H${item.rashi_house}->H${item.bhava_house}`).join(' · ') || '暂无迁移'],
    ['第一宫边界', firstHouse ? `${firstHouse.sandhi_start_lon}° → ${firstHouse.sandhi_end_lon}°` : '-', result.calculation_note || data?.calculation_note || 'Bhava Madhya / Sandhi 边界'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  return `
    <div class="technique-result-head">
      <strong>Bhava Chalit 宫位漂移</strong>
      <span>${escapeHtml(systemLabels[selected] || selected)}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-next-action">${escapeHtml(result.fallback_reason || data?.fallback_reason || '用 Bhava Chalit 复核行星是否跨越宫位边界，再与 Rashi chart 一起解释。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderBhavaBalaResult(data) {
  const summary = data?.summary || {};
  const strongest = summary.strongest || [];
  const weakest = summary.weakest || [];
  const cards = [
    ['结论', summary.headline || '-', data?.ascendant || 'Ascendant'],
    ['最强宫位', strongest.map(item => `H${item.house}:${item.level}`).join(' / ') || '-', '优先作为人生主题与承载领域'],
    ['最弱宫位', weakest.map(item => `H${item.house}:${item.level}`).join(' / ') || '-', '需要 Dasha/Transit 确认后再定风险'],
    ['方法', data?.result?.method || 'Bhava Bala', 'Adhipathi + Dig + Drik 三元力量'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  return `
    <div class="technique-result-head">
      <strong>Bhava Bala 宫位力量</strong>
      <span>${escapeHtml(data?.ascendant || 'bhava')}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-next-action">${escapeHtml(summary.next_action || '把宫位力量作为领域权重，不单独代表事件结果。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderTransitTriggerResult(data) {
  const summary = data?.summary || {};
  const triggers = summary.top_triggers || [];
  const cards = [
    ['结论', summary.headline || '-', `${summary.total_triggers ?? 0} 个触发点`],
    ['区间', `${summary.period?.start || '-'} → ${summary.period?.end || '-'}`, '默认扫描未来90天慢行星触发'],
    ['首要触发', triggers[0] ? `${triggers[0].planet || '-'} → ${triggers[0].sensitive_point || '-'} ${triggers[0].start_date || ''}` : '暂无', '仅代表时间窗口'],
    ['证据类型', triggers[0]?.source || data?.result?.summary || '-', '优先 Swiss Ephemeris，缺失时回退均速模型'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  return `
    <div class="technique-result-head">
      <strong>过境精确触发</strong>
      <span>${escapeHtml(data?.endpoint || 'transit')}</span>
    </div>
    <div class="technique-insight-grid">${cards}</div>
    <div class="technique-next-action">${escapeHtml(summary.next_action || '过境只用于细化时间窗口。')}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderDomainEngineResult(title, data, nextAction) {
  const cards = summarizeDomainObject(data).slice(0, 4).map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  return `
    <div class="technique-result-head">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(data?.endpoint || 'analysis')}</span>
    </div>
    <div class="technique-insight-grid">${cards || renderInsightCard('结果', '已返回', '展开 JSON 查看完整结构')}</div>
    <div class="technique-next-action">${escapeHtml(nextAction)}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function summarizeDomainObject(data) {
  const source = data?.summary && typeof data.summary === 'object' ? data.summary : data;
  const rows = [];
  for (const [key, value] of Object.entries(source || {})) {
    if (rows.length >= 4) break;
    if (value == null || typeof value === 'function') continue;
    rows.push([formatKey(key), formatMiniValue(value), Array.isArray(value) ? `${value.length} 项证据` : '结构化分析字段']);
  }
  return rows;
}

function renderKPQuickResult(data) {
  const houses = data?.houses || {};
  const planets = data?.planets || {};
  const firstHouse = houses[1] || Object.values(houses)[0] || {};
  const firstPlanet = Object.entries(planets)[0] || [];
  const kp = firstPlanet[1]?.kp_lords || {};
  const cards = [
    ['结论', Object.keys(houses).length ? 'KP 宫位 Significator 已返回' : '等待 KP 数据', 'ABCD Significator 用于事件兑现判断'],
    ['1宫证据', firstHouse.sign || '-', `A/B/C/D: ${formatMiniValue(firstHouse.significators || {})}`],
    ['首颗行星', firstPlanet[0] || '-', `${kp.sub_lord || '-'} / ${kp.sub_sub_lord || '-'}`],
    ['下一步', '用具体问题限定宫位', 'KP 不适合无问题泛读'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  return `
    <div class="technique-result-head"><strong>KP Sublord 快读</strong><span>kp</span></div>
    <div class="technique-insight-grid">${cards}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderPrashnaQuickResult(data) {
  const chart = data?.prashna_chart || {};
  const answer = data?.kp_answer || {};
  const cards = [
    ['答案', answer.kp_answer || 'MAYBE', `置信度 ${answer.confidence || '-'}`],
    ['问题宫', `${answer.primary_house || '-'}宫`, `宫主 ${answer.question_lord || '-'}`],
    ['问事上升', `${chart.asc_sign || '-'} ${formatDegree(chart.asc_degree)}`, `Lagna lord ${chart.prashna_lagna_lord || '-'}`],
    ['边界', '一次只问一个具体问题', '重大决定需结合出生盘'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  return `
    <div class="technique-result-head"><strong>Prashna 问事快读</strong><span>horary</span></div>
    <div class="technique-insight-grid">${cards}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function renderSynastryQuickResult(data) {
  const percentage = data?.match_percentage ?? ((Number(data?.total_score || 0) / Number(data?.max_score || 36)) * 100).toFixed(1);
  const scores = data?.scores || {};
  const cards = [
    ['总分', `${data?.total_score ?? 0}/${data?.max_score ?? 36}`, `${percentage}%`],
    ['结论', data?.is_match_approved ? '匹配通过' : '需谨慎综合判断', '月亮星宿体系结果'],
    ['强项', strongestScore(scores), '从 Kuta 分项中读取'],
    ['边界', '还需完整双方星盘', '7宫/D9/Kuja/Dasha 同步不可省略'],
  ].map(([label, value, note]) => renderInsightCard(label, value, note)).join('');
  return `
    <div class="technique-result-head"><strong>Ashtakoot 合盘快读</strong><span>synastry</span></div>
    <div class="technique-insight-grid">${cards}</div>
    <details class="technique-json"><summary>JSON</summary><pre>${escapeHtml(JSON.stringify(data, null, 2).slice(0, 6000))}</pre></details>
  `;
}

function strongestScore(scores = {}) {
  const entries = Object.entries(scores);
  if (!entries.length) return '-';
  const [name, score] = entries.sort((a, b) => Number(b[1]) - Number(a[1]))[0];
  return `${name}: ${score}`;
}

function renderInsightCard(label, value, note) {
  return `
    <div class="technique-insight-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
      <p>${escapeHtml(note || '')}</p>
    </div>
  `;
}

function annualTheme(report, muntha) {
  const note = report.note || muntha.interpretation || '';
  if (note) return String(note).slice(0, 90);
  const year = report.target_year || report.report_year || new Date().getFullYear();
  return `${year} 年的太阳返照主题`;
}

function formatMuntha(muntha = {}) {
  const sign = muntha.muntha_sign || muntha.sign || '-';
  const lord = muntha.muntha_lord || muntha.lord || '';
  const house = muntha.house ? ` H${muntha.house}` : '';
  return `${sign}${house}${lord ? ` · ${lord}` : ''}`;
}

function formatPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '-';
  return number <= 1 ? `${Math.round(number * 100)}%` : `${Math.round(number)}%`;
}

function formatEventType(value) {
  return {
    marriage: '婚姻',
    child_birth: '子女',
    career_start: '入职',
    career_change: '事业转折',
    promotion: '晋升',
    relocation: '迁移',
    education_end: '学业完成',
    father_death: '父亲事件',
    mother_death: '母亲事件',
    accident: '事故',
    health_crisis: '健康危机',
    windfall: '意外收入',
    financial_loss: '财务损失',
    spiritual_awakening: '灵性转折',
  }[value] || value;
}

function formatKey(key) {
  return String(key).replace(/_/g, ' ');
}

function formatMiniValue(value) {
  if (value == null || value === '') return '-';
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(3);
  if (typeof value === 'string' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) {
    if (value.length === 0) return '0项';
    if (value.every(item => ['string', 'number', 'boolean'].includes(typeof item))) return value.slice(0, 4).join(' / ');
    return `${value.length}项`;
  }
  if (typeof value === 'object') {
    if (value.sign) return `${value.sign} ${formatDegree(value.degree ?? value.degree_in_sign)}`;
    if (value.name) return value.name;
    if (value.summary) return value.summary;
    return Object.keys(value).slice(0, 5).join(' / ');
  }
  return String(value);
}

function formatDegree(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '';
  return `${number.toFixed(2)}°`;
}

function hydrateCapabilityAudit(container, context = {}) {
  if (!window.JyotishAPI?.getCapabilityAudit && !window.JyotishAPI?.getTechniqueCatalog) {
    renderCapabilityFallback(container, '本地 API 服务未启动，当前显示前端静态能力兜底。');
    return;
  }
  const host = container.querySelector('.skill-dashboard');
  if (!host || host.querySelector('.capability-audit-panel')) return;
  const placeholder = document.createElement('section');
  placeholder.className = 'skill-section capability-audit-panel capability-loading';
  placeholder.innerHTML = '<h4>地毯式能力审计</h4><p>正在读取 technique registry、引擎子命令、API、前端入口与本地开源源码碎片...</p>';
  host.appendChild(placeholder);
  capabilityAuditPromise ||= getTechniqueCatalogOrAudit();
  capabilityAuditPromise
    .then(audit => {
      if (audit?.api_docs) window.__jyotishTechniqueCatalog = audit;
      placeholder.classList.remove('capability-loading');
      placeholder.innerHTML = renderCapabilityAudit(audit, context);
      bindTechniqueDirectory(placeholder, audit, context);
    })
    .catch(error => {
      capabilityAuditPromise = null;
      placeholder.classList.remove('capability-loading');
      placeholder.innerHTML = renderCapabilityFallbackHtml(error?.message || '能力审计接口不可用');
    });
}

async function getTechniqueCatalogOrAudit() {
  if (window.JyotishAPI?.getTechniqueCatalog) {
    try {
      return await window.JyotishAPI.getTechniqueCatalog();
    } catch (error) {
      if (!window.JyotishAPI?.getCapabilityAudit) throw error;
    }
  }
  return window.JyotishAPI.getCapabilityAudit();
}

function renderCapabilityFallback(container, message) {
  const host = container.querySelector('.skill-dashboard');
  if (!host || host.querySelector('.capability-audit-panel')) return;
  const section = document.createElement('section');
  section.className = 'skill-section capability-audit-panel';
  section.innerHTML = renderCapabilityFallbackHtml(message);
  host.appendChild(section);
}

function renderCapabilityFallbackHtml(message) {
  return `
    <h4>地毯式能力审计</h4>
    <div class="capability-error">
      <strong>未取得后端审计结果</strong>
      <p>${escapeHtml(message)}</p>
      <small>按 README 的普通用户启动路径启动网页服务和本地 API 服务，然后重新排盘。</small>
    </div>
  `;
}

function renderCapabilityAudit(audit, context = {}) {
  const registry = audit?.registry || {};
  const surfaces = audit?.surfaces || {};
  const local = audit?.local_open_source || {};
  const research = audit?.external_research || [];
  const gaps = audit?.priority_gaps || [];
  const productization = audit?.productization || {};
  const uxProductization = audit?.ux_productization || {};
  const productSummary = productization.summary || {};
  const productQueue = productization.next_queue || [];
  const uxSummary = uxProductization.summary || {};
  const uxQueue = uxProductization.next_queue || [];
  const directSources = (local.sources || []).filter(s => s.reuse === 'direct');
  const cautionSources = (local.sources || []).filter(s => s.reuse !== 'direct');
  const statusBadges = Object.entries(registry.status_counts || {}).map(([status, count]) => (
    `<span><b>${escapeHtml(count)}</b>${escapeHtml(status)}</span>`
  )).join('');
  const commandTags = (surfaces.engine_not_api || []).slice(0, 18).map(command => (
    `<span>${escapeHtml(command)}</span>`
  )).join('');
  const sourceCards = (local.sources || []).map(source => renderSourceCard(source)).join('');
  const researchRows = research.map(item => `
    <tr>
      <td><a href="${escapeAttr(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.name)}</a></td>
      <td>${escapeHtml(item.license)}</td>
      <td><span class="reuse-pill reuse-${escapeAttr(item.reuse)}">${escapeHtml(reuseLabel(item.reuse))}</span></td>
      <td>${escapeHtml((item.best_for || []).join(' / '))}</td>
    </tr>
  `).join('');
  const gapCards = gaps.map(gap => `
    <div class="capability-gap-card capability-${escapeAttr(gap.priority || 'medium')}">
      <span>${escapeHtml(gap.kind || 'gap')}</span>
      <strong>${escapeHtml(gap.command || gap.topic || '待补能力')}</strong>
      <p>${escapeHtml(gap.reason || '')}</p>
      ${(gap.related_techniques || []).length ? `<small>${gap.related_techniques.map(escapeHtml).join(' · ')}</small>` : ''}
    </div>
  `).join('');
  const productQueueCards = productQueue.slice(0, 8).map(row => `
    <div class="product-queue-card product-${escapeAttr(row.level)}">
      <span>${escapeHtml(productLevelLabel(row.level))}</span>
      <strong>${escapeHtml(row.name)}</strong>
      <p>${escapeHtml(row.next_action || row.reason || '')}</p>
      ${(row.commands || []).length ? `<small>${row.commands.slice(0, 4).map(escapeHtml).join(' · ')}</small>` : ''}
    </div>
  `).join('');
  const uxQueueCards = uxQueue.slice(0, 8).map(row => `
    <div class="ux-queue-card ux-${escapeAttr(row.ux_level)}">
      <span>${escapeHtml(uxLevelLabel(row.ux_level))} · ${escapeHtml(row.ux_score ?? 0)}/6</span>
      <strong>${escapeHtml(row.name)}</strong>
      <p>${escapeHtml(row.ux_next_action || '')}</p>
      ${(row.missing_ux || []).length ? `<small>缺：${row.missing_ux.slice(0, 4).map(uxCriterionLabel).map(escapeHtml).join(' / ')}</small>` : ''}
    </div>
  `).join('');

  return `
    <h4>地毯式能力审计</h4>
    <div class="capability-metrics">
      <div><strong>${escapeHtml(registry.technique_count ?? 0)}</strong><span>注册技法</span></div>
      <div><strong>${escapeHtml(surfaces.engine_command_count ?? 0)}</strong><span>引擎子命令</span></div>
      <div><strong>${escapeHtml(surfaces.api_endpoint_count ?? 0)}</strong><span>Web API</span></div>
      <div><strong>${escapeHtml(surfaces.app_tab_count ?? 0)}</strong><span>前端入口</span></div>
      <div><strong>${escapeHtml(local.source_count ?? 0)}</strong><span>本地开源碎片</span></div>
    </div>
    <div class="capability-status-row">${statusBadges}</div>

    <div class="capability-section productization-section">
      <h5>Skill 产品化覆盖</h5>
      <div class="productization-metrics">
        <div><strong>${escapeHtml(productSummary.productized ?? 0)}</strong><span>已产品化</span></div>
        <div><strong>${escapeHtml(productSummary.api_backed ?? 0)}</strong><span>API 已承载</span></div>
        <div><strong>${escapeHtml(productSummary.engine_or_full_reading ?? 0)}</strong><span>引擎/完整解盘</span></div>
        <div><strong>${escapeHtml(productSummary.registry_only ?? 0)}</strong><span>待确认</span></div>
      </div>
      <div class="product-queue-grid">${productQueueCards || '<p>当前没有自动识别出的下一步队列。</p>'}</div>
      <p class="capability-note">这里衡量用户能否在页面中真正用到该 skill，而不只是代码里存在算法。</p>
    </div>

    <div class="capability-section ux-productization-section">
      <h5>UX 验收</h5>
      <div class="ux-productization-metrics">
        <div><strong>${escapeHtml(uxSummary.excellent ?? 0)}</strong><span>优秀</span></div>
        <div><strong>${escapeHtml(uxSummary.usable ?? 0)}</strong><span>可用</span></div>
        <div><strong>${escapeHtml(uxSummary.thin ?? 0)}</strong><span>偏薄</span></div>
        <div><strong>${escapeHtml(uxSummary.not_user_ready ?? 0)}</strong><span>未就绪</span></div>
      </div>
      <div class="ux-queue-grid">${uxQueueCards || '<p>当前没有 UX 队列。</p>'}</div>
      <p class="capability-note">UX 分数按入口、可读结论、证据链、下一步建议、JSON隐藏、移动端可读六项评估。</p>
    </div>

    ${renderTechniqueDirectory(audit, context)}

    <div class="capability-split">
      <div class="capability-box">
        <h5>引擎已有但 API/应用未完整暴露</h5>
        <div class="capability-command-tags">${commandTags || '<span>暂无明显缺口</span>'}</div>
      </div>
      <div class="capability-box">
        <h5>开源复用库存</h5>
        <p>可直接复用：${escapeHtml(directSources.length)} 个；需许可证谨慎或人工确认：${escapeHtml(cautionSources.length)} 个。</p>
        <div class="capability-source-grid">${sourceCards}</div>
      </div>
    </div>

    <div class="capability-section">
      <h5>优先补洞项</h5>
      <div class="capability-gap-grid">${gapCards || '<p>未发现高优先级暴露缺口。</p>'}</div>
    </div>

    <div class="capability-section">
      <h5>全网对标与许可证边界</h5>
      <div class="skill-table-wrap">
        <table class="skill-audit-table">
          <thead><tr><th>项目</th><th>许可证</th><th>复用策略</th><th>最适合对标</th></tr></thead>
          <tbody>${researchRows}</tbody>
        </table>
      </div>
      <p class="capability-note">AGPL/GPL 项目只用于 benchmark 和算法口径校准；MIT/Apache 项目优先直接复用，避免重复造轮子。</p>
    </div>
  `;
}

function renderSourceCard(source) {
  return `
    <div class="capability-source-card reuse-${escapeAttr(source.reuse || 'unknown')}">
      <div>
        <strong>${escapeHtml(source.name)}</strong>
        <span>${escapeHtml(source.license || 'unknown')} · ${escapeHtml(reuseLabel(source.reuse))}</span>
      </div>
      <p>${escapeHtml((source.modules || []).slice(0, 8).join(' / ') || '未自动识别模块')}</p>
      <small>${escapeHtml(source.file_count || 0)} files · ${escapeHtml(source.path || '')}</small>
    </div>
  `;
}

function renderTechniqueDirectory(audit, context = {}) {
  const rows = buildTechniqueDirectoryRows(audit);
  const hasChart = Boolean(Object.keys(context?.chartData?.planets || {}).length);
  const domains = uniqueSorted(rows.flatMap(row => row.domains));
  const statuses = uniqueSorted(rows.map(row => row.status).filter(Boolean));
  const surfaceOptions = [
    ['all', '全部承载'],
    ['productized', '已产品化'],
    ['api_backed', 'API 已承载'],
    ['engine_or_full_reading', '引擎/完整解盘'],
    ['registry_only', '待确认'],
  ];
  const domainOptions = ['<option value="all">全部领域</option>', ...domains.map(domain => (
    `<option value="${escapeAttr(domain)}">${escapeHtml(domain)}</option>`
  ))].join('');
  const statusOptions = ['<option value="all">全部状态</option>', ...statuses.map(status => (
    `<option value="${escapeAttr(status)}">${escapeHtml(status)}</option>`
  ))].join('');
  const surfaceOptionHtml = surfaceOptions.map(([value, label]) => (
    `<option value="${escapeAttr(value)}">${escapeHtml(label)}</option>`
  )).join('');

  return `
    <div class="capability-section technique-directory" data-technique-directory>
      <div class="technique-directory-head">
        <div>
          <h5>技法与 API 目录</h5>
          <p>按关键词、领域、注册状态和承载层筛选，直接看到每项能力是否已经进入用户端，并可用当前星盘试算白名单 API。</p>
        </div>
        <span>${escapeHtml(rows.length)} 项</span>
      </div>
      <div class="technique-directory-controls">
        <label>
          <span>搜索</span>
          <input id="technique-directory-search" type="search" placeholder="婚姻 / Dasha / KP / API" autocomplete="off" data-technique-filter="search">
        </label>
        <label>
          <span>领域</span>
          <select id="technique-directory-domain" data-technique-filter="domain">${domainOptions}</select>
        </label>
        <label>
          <span>状态</span>
          <select id="technique-directory-status" data-technique-filter="status">${statusOptions}</select>
        </label>
        <label>
          <span>承载</span>
          <select id="technique-directory-surface" data-technique-filter="surface">${surfaceOptionHtml}</select>
        </label>
      </div>
      <div class="technique-directory-summary" data-technique-directory-summary>${escapeHtml(rows.length)} 项匹配</div>
      <div class="technique-directory-grid" data-technique-directory-results>
        ${renderTechniqueDirectoryRows(rows, { hasChart })}
      </div>
    </div>
  `;
}

function buildTechniqueDirectoryRows(audit) {
  if (Array.isArray(audit?.techniques) && audit.techniques.some(row => row.api_endpoints || row.example_endpoint)) {
    return audit.techniques.map(row => {
      const commands = uniqueSorted(row.commands || []);
      const endpoints = uniqueSorted(row.api_endpoints || []);
      const explorerAction = resolveTechniqueExplorerAction(row.id, commands, row.example_endpoint);
      const domains = uniqueSorted(row.domains || []);
      const visibleMarkers = uniqueSorted(row.visible_markers || []);
      const outputPaths = uniqueSorted(row.output_paths || []);
      const searchText = [
        row.id,
        row.name,
        row.audit_label,
        row.status,
        row.level,
        row.reason,
        row.next_action,
        row.method_docs?.summary,
        row.method_docs?.boundary,
        row.method_docs?.primary_endpoint,
        row.ux_level,
        ...domains,
        ...commands,
        ...endpoints,
        ...outputPaths,
        ...visibleMarkers,
      ].filter(Boolean).join(' ').toLowerCase();
      return {
        id: row.id,
        name: row.name || row.id,
        auditLabel: row.audit_label || row.name || row.id,
        status: row.status || 'unknown',
        domains,
        commands,
        apiCommands: uniqueSorted(row.api_commands || []),
        endpoints,
        outputPaths,
        visibleMarkers,
        explorerAction,
        exampleEndpoint: row.example_endpoint || endpointForAction(explorerAction),
        level: row.level || 'registry_only',
        reason: row.reason || '',
        nextAction: row.next_action || '保持监控。',
        methodDocs: row.method_docs || {},
        uxScore: row.ux_score ?? 0,
        uxLevel: row.ux_level || 'not_user_ready',
        missingUx: row.missing_ux || [],
        searchText,
      };
    }).sort(sortTechniqueRows);
  }
  const techniques = audit?.techniques || [];
  const productRows = new Map((audit?.productization?.rows || []).map(row => [row.id, row]));
  const uxRows = new Map((audit?.ux_productization?.rows || []).map(row => [row.id, row]));
  const availableEndpoints = new Set(audit?.surfaces?.api_endpoints || []);
  return techniques.map(technique => {
    const product = productRows.get(technique.id) || {};
    const ux = uxRows.get(technique.id) || {};
    const commands = uniqueSorted([...(product.commands || []), ...(technique.commands || [])]);
    const apiCommands = uniqueSorted(product.api_commands || []);
    const endpoints = uniqueSorted([
      ...apiCommands.map(command => TECHNIQUE_API_ENDPOINTS[command]).filter(Boolean),
      ...commands.map(command => TECHNIQUE_API_ENDPOINTS[command]).filter(endpoint => endpoint && availableEndpoints.has(endpoint)),
    ]);
    const explorerAction = resolveTechniqueExplorerAction(technique.id, commands);
    const domains = uniqueSorted([...(product.domains || []), ...(technique.domains || [])]);
    const outputPaths = uniqueSorted([...(product.output_paths || []), ...(technique.output_paths || [])]);
    const visibleMarkers = uniqueSorted(product.visible_markers || []);
    const searchText = [
      technique.id,
      technique.name,
      technique.audit_label,
      technique.status,
      technique.limitation,
      technique.missing_impact,
      product.level,
      product.reason,
      product.next_action,
      product.method_docs?.summary,
      product.method_docs?.boundary,
      ux.ux_level,
      ux.ux_next_action,
      ...domains,
      ...commands,
      ...apiCommands,
      ...endpoints,
      ...outputPaths,
      ...visibleMarkers,
    ].filter(Boolean).join(' ').toLowerCase();

    return {
      id: technique.id,
      name: technique.name || product.name || technique.id,
      auditLabel: technique.audit_label || technique.name || technique.id,
      status: technique.status || product.status || 'unknown',
      domains,
      commands,
      apiCommands,
      endpoints,
      outputPaths,
      visibleMarkers,
      explorerAction,
      exampleEndpoint: endpointForAction(explorerAction),
      level: product.level || 'registry_only',
      reason: product.reason || technique.limitation || '',
      nextAction: product.next_action || ux.ux_next_action || technique.missing_impact || '保持监控。',
      methodDocs: product.method_docs || {},
      uxScore: ux.ux_score ?? 0,
      uxLevel: ux.ux_level || 'not_user_ready',
      missingUx: ux.missing_ux || [],
      searchText,
    };
  }).sort(sortTechniqueRows);
}

function sortTechniqueRows(a, b) {
  const levelOrder = { registry_only: 0, engine_or_full_reading: 1, api_backed: 2, productized: 3 };
  return (levelOrder[a.level] ?? 0) - (levelOrder[b.level] ?? 0)
    || String(a.name).localeCompare(String(b.name), 'zh-Hans-CN');
}

function renderTechniqueDirectoryRows(rows, options = {}) {
  if (!rows.length) {
    return '<p class="technique-directory-empty">没有匹配的技法，换一个关键词或筛选条件。</p>';
  }
  const hasChart = Boolean(options.hasChart);
  return rows.map(row => {
    const domainTags = row.domains.slice(0, 4).map(domain => `<span>${escapeHtml(domain)}</span>`).join('');
    const commandTags = row.commands.slice(0, 4).map(command => `<span>${escapeHtml(command)}</span>`).join('');
    const endpointTags = row.endpoints.slice(0, 3).map(endpoint => `<code>${escapeHtml(endpoint)}</code>`).join('');
    const markerText = row.visibleMarkers.length ? row.visibleMarkers.slice(0, 3).join(' / ') : '未识别独立入口';
    const missingText = row.missingUx.length
      ? `缺：${row.missingUx.slice(0, 3).map(uxCriterionLabel).join(' / ')}`
      : 'UX 验收完整';
    const methodSummary = row.methodDocs?.summary || row.reason || '已进入能力注册表。';
    const methodBoundary = row.methodDocs?.boundary || row.nextAction;
    const apiDocKey = row.methodDocs?.api_doc_key || row.exampleEndpoint;
    const explorerButton = row.explorerAction
      ? `<button type="button" class="technique-explorer-run" data-technique-run="${escapeAttr(row.explorerAction)}" data-technique-endpoint="${escapeAttr(row.exampleEndpoint || endpointForAction(row.explorerAction))}">${hasChart ? '试算' : '样例'}</button>`
      : '<span class="technique-explorer-static">完整解盘承载</span>';
    return `
      <article class="technique-directory-card technique-${escapeAttr(row.level)}" data-technique-id="${escapeAttr(row.id)}">
        <div class="technique-directory-card-head">
          <div>
            <strong>${escapeHtml(row.name)}</strong>
            <small>${escapeHtml(row.id)}</small>
          </div>
          <span class="technique-directory-pill">${escapeHtml(productLevelLabel(row.level))}</span>
        </div>
        <div class="technique-directory-meta">
          <span>${escapeHtml(row.status)}</span>
          <span>${escapeHtml(uxLevelLabel(row.uxLevel))} · ${escapeHtml(row.uxScore)}/6</span>
          <span>${escapeHtml(markerText)}</span>
        </div>
        <p>${escapeHtml(methodSummary)}</p>
        ${methodBoundary ? `<small class="technique-method-boundary">${escapeHtml(methodBoundary)}</small>` : ''}
        <div class="technique-directory-tags">${domainTags || '<span>未标领域</span>'}</div>
        <div class="technique-directory-tags">${commandTags || '<span>无命令</span>'}</div>
        <div class="technique-directory-endpoints">${endpointTags || '<em>待 API 暴露</em>'}</div>
        ${apiDocKey ? `<div class="technique-explorer-call"><span>API docs</span><code>${escapeHtml(apiDocKey)}</code></div>` : ''}
        <small>${escapeHtml(missingText)}</small>
        <b>${escapeHtml(row.nextAction)}</b>
        <div class="technique-explorer-actions">
          ${explorerButton}
          ${row.explorerAction ? `<code>${escapeHtml(resultTitle(row.explorerAction))}</code>` : '<code>full-reading</code>'}
        </div>
        <div class="technique-explorer-result" data-technique-result aria-live="polite"></div>
      </article>
    `;
  }).join('');
}

function bindTechniqueDirectory(root, audit, context = {}) {
  const directory = root?.querySelector('[data-technique-directory]');
  if (!directory) return;
  const rows = buildTechniqueDirectoryRows(audit);
  const hasChart = Boolean(Object.keys(context?.chartData?.planets || {}).length);
  const resultHost = directory.querySelector('[data-technique-directory-results]');
  const summary = directory.querySelector('[data-technique-directory-summary]');
  const filters = [...directory.querySelectorAll('[data-technique-filter]')];
  const render = () => {
    const criteria = readTechniqueDirectoryFilters(directory);
    const filtered = filterTechniqueDirectoryRows(rows, criteria);
    if (summary) summary.textContent = `${filtered.length} / ${rows.length} 项匹配`;
    if (resultHost) resultHost.innerHTML = renderTechniqueDirectoryRows(filtered, { hasChart });
    bindTechniqueExplorerActions(resultHost, context);
  };
  filters.forEach(control => {
    control.addEventListener(control.tagName === 'INPUT' ? 'input' : 'change', render);
  });
  bindTechniqueExplorerActions(resultHost, context);
}

function readTechniqueDirectoryFilters(directory) {
  return {
    search: normalizeDirectoryText(directory.querySelector('[data-technique-filter="search"]')?.value),
    domain: directory.querySelector('[data-technique-filter="domain"]')?.value || 'all',
    status: directory.querySelector('[data-technique-filter="status"]')?.value || 'all',
    surface: directory.querySelector('[data-technique-filter="surface"]')?.value || 'all',
  };
}

function filterTechniqueDirectoryRows(rows, filters = {}) {
  const search = normalizeDirectoryText(filters.search);
  return rows.filter(row => {
    if (search && !row.searchText.includes(search)) return false;
    if (filters.domain && filters.domain !== 'all' && !row.domains.includes(filters.domain)) return false;
    if (filters.status && filters.status !== 'all' && row.status !== filters.status) return false;
    if (filters.surface && filters.surface !== 'all' && row.level !== filters.surface) return false;
    return true;
  });
}

function bindTechniqueExplorerActions(host, context = {}) {
  if (!host) return;
  const buttons = [...host.querySelectorAll('[data-technique-run]')];
  for (const button of buttons) {
    button.addEventListener('click', async () => {
      const action = button.dataset.techniqueRun;
      const card = button.closest('.technique-directory-card');
      const resultHost = card?.querySelector('[data-technique-result]');
      if (!resultHost || !action) return;
      if (!window.JyotishAPI) {
        resultHost.innerHTML = renderWorkbenchError('本地 API 服务未连接');
        return;
      }
      button.disabled = true;
      button.classList.add('loading');
      resultHost.innerHTML = renderTechniqueExplorerLoading(action, context);
      try {
        const data = await runTechniqueExplorerAction(action, context, button.dataset.techniqueEndpoint || '');
        resultHost.innerHTML = renderTechniqueExplorerResult(action, data);
      } catch (error) {
        resultHost.innerHTML = renderWorkbenchError(error?.message || 'API Explorer 试算失败');
      } finally {
        button.disabled = false;
        button.classList.remove('loading');
      }
    });
  }
}

async function runTechniqueExplorerAction(action, context = {}, endpoint = '') {
  const payload = buildTechniqueExplorerPayload(action, context);
  const targetEndpoint = endpoint || endpointForAction(action);
  if (window.JyotishAPI?.runTechniqueExample && targetEndpoint) {
    return window.JyotishAPI.runTechniqueExample({ endpoint: targetEndpoint, payload });
  }
  return runTechniqueAction(action, context);
}

function renderTechniqueExplorerResult(action, data) {
  if (data?.endpoint === 'technique_example') {
    const apiDoc = getTechniqueApiDoc(data.target_endpoint);
    return `
      <div class="technique-example-badge">
        <span>样例 API</span>
        <code>${escapeHtml(data.target_endpoint || '')}</code>
      </div>
      ${apiDoc ? renderTechniqueApiDocs(apiDoc) : ''}
      ${renderTechniqueResult(action, data.result || data)}
      <details class="technique-json"><summary>Sample payload</summary><pre>${escapeHtml(JSON.stringify(data.sample_payload || {}, null, 2).slice(0, 3000))}</pre></details>
    `;
  }
  return renderTechniqueResult(action, data);
}

function renderTechniqueExplorerLoading(action, context = {}) {
  const payload = buildTechniqueExplorerPayload(action, context);
  return `
    <div class="technique-explorer-loading">
      <strong>正在试算 ${escapeHtml(resultTitle(action))}...</strong>
      <details open><summary>请求预览</summary><pre>${escapeHtml(JSON.stringify(payload, null, 2).slice(0, 1200))}</pre></details>
    </div>
  `;
}

function buildTechniqueExplorerPayload(action, context = {}) {
  const chartData = context.chartData || {};
  const base = {
    planets: chartData.planets || {},
    ascendant: chartData.ascendant || {},
  };
  if (action === 'annual') return { ...base, ...buildBirthPayload(context), target_year: new Date().getFullYear() };
  if (action === 'muhurta') return { date: new Date().toISOString().slice(0, 10), activity: 'business', hour_from_sunrise: 6.0 };
  if (action === 'bhava') return { ...base, ...buildBirthPayload(context), mode: 'compare', house_system: resolveBhavaHouseSystem(context) };
  if (action === 'nakshatra') return { ...base, age: estimateAge(context) };
  if (action === 'jaimini') return { ...base, ...buildBirthPayload(context), mode: 'all' };
  if (action === 'charaDasha') return { ...base, ...buildBirthPayload(context), antardasha: true };
  if (action === 'shadbala') return { ...base, ...buildBirthPayload(context) };
  if (action === 'yogas') return { ...base, current_dasha: chartData.dasha?.current_md || chartData.dasha_lord || '' };
  if (action === 'dasha') return { ...base, ...buildBirthPayload(context), dasha: 'vimshottari' };
  if (action === 'remedies') return { shadbala: chartData.shadbala || {}, doshas: chartData.doshas || [], dasha_lord: chartData.dasha?.current_md || '' };
  if (action === 'sadeSati') return { moon_degree: chartData.planets?.Moon?.lon ?? 0, asc_degree: chartData.ascendant?.lon ?? 0, saturn_degree: chartData.planets?.Saturn?.lon ?? 0 };
  if (action === 'panchaMahapurusha') return { planets: chartData.planets || {}, sun_degree: chartData.planets?.Sun?.lon ?? chartData.planets?.Sun?.degree };
  if (action === 'rectification') return { ...base, declared_accuracy: 'minute', time_source: 'family_clear' };
  if (action === 'caseValidation') return { ...base, current_md: chartData?.dasha?.current_md || '', predicted_events: inferValidationEvents(chartData), transit_desc: inferTransitDescription(chartData) };
  if (action === 'divisionalYoga') return { ...base, divisions: ['D9', 'D10', 'D12'] };
  if (action === 'deepVargaAvastha') return base;
  if (action === 'transitTrigger') return { natal_planets: chartData.planets || {}, ascendant: chartData.ascendant || {}, start: new Date().toISOString().slice(0, 10), end: new Date(Date.now() + 90 * 86400000).toISOString().slice(0, 10), planets_to_check: ['Saturn', 'Jupiter', 'Rahu', 'Ketu'] };
  if (action === 'thematicReport') return { chart_data: chartData, theme: 'marriage' };
  if (action === 'career') return { planets: chartData.planets || {}, asc_sign: chartData.ascendant?.sign || 'Aries' };
  if (action === 'relationship') return { planets: chartData.planets || {}, asc_sign: chartData.ascendant?.sign || 'Aries', dasha_info: { maha_dasha: chartData.dasha?.current_md || 'Venus' } };
  if (action === 'kpQuick') return { planets: chartData.planets || {}, asc_sign_idx: chartData.ascendant?.sign_idx ?? signIndex(chartData.ascendant?.sign) };
  if (action === 'prashnaQuick') return { planets: chartData.planets || {}, question: 'general' };
  if (action === 'synastryQuick') {
    const moon = chartData.planets?.Moon?.lon ?? chartData.planets?.Moon?.degree ?? 0;
    return { male_moon: moon, female_moon: (Number(moon) + 120) % 360 };
  }
  if (action === 'varga') return { ...base, divisions: ['D9', 'D10'] };
  return base;
}

function resolveBhavaHouseSystem(context = {}) {
  const selected = context.calculationSettings?.houseSystem || context.chartData?.provenance?.calculationSettings?.houseSystem || context.chartData?.calculationSettings?.houseSystem;
  const allowed = ['sripati', 'placidus', 'equal', 'whole_sign', 'porphyry', 'koch'];
  return allowed.includes(selected) ? selected : 'sripati';
}

function buildExplorerPayloadPreview(action, context = {}) {
  return buildTechniqueExplorerPayload(action, context);
}

function resolveTechniqueExplorerAction(id, commands = [], endpoint = '') {
  if (TECHNIQUE_ID_ACTIONS[id]) return TECHNIQUE_ID_ACTIONS[id];
  const endpointAction = actionForEndpoint(endpoint);
  if (endpointAction) return endpointAction;
  const available = commands
    .map(command => TECHNIQUE_COMMAND_ACTIONS[command])
    .filter(Boolean);
  if (!available.length) return '';
  return available.sort((a, b) => (
    TECHNIQUE_EXPLORER_PRIORITY.indexOf(a) - TECHNIQUE_EXPLORER_PRIORITY.indexOf(b)
  ))[0];
}

function actionForEndpoint(endpoint) {
  return {
    '/api/varga_full': 'varga',
    '/api/annual': 'annual',
    '/api/tajika': 'annual',
    '/api/muhurta': 'muhurta',
    '/api/bhava_chalit': 'bhava',
    '/api/sudarshana': 'sudarshana',
    '/api/nakshatra_full': 'nakshatra',
    '/api/jaimini': 'jaimini',
    '/api/dasha/chara': 'charaDasha',
    '/api/ashtakavarga': 'ashtakavarga',
    '/api/shadbala': 'shadbala',
    '/api/yogas': 'yogas',
    '/api/aspects': 'aspects',
    '/api/dasha': 'dasha',
    '/api/remedies': 'remedies',
    '/api/sade_sati': 'sadeSati',
    '/api/pancha_mahapurusha': 'panchaMahapurusha',
    '/api/rectification_gate': 'rectification',
    '/api/case_validation': 'caseValidation',
    '/api/divisional_yoga': 'divisionalYoga',
    '/api/kakshya': 'kakshya',
    '/api/bhava_bala': 'bhavaBala',
    '/api/transit': 'transitTrigger',
    '/api/thematic_report': 'thematicReport',
    '/api/career': 'career',
    '/api/relationship': 'relationship',
    '/api/kp': 'kpQuick',
    '/api/prashna': 'prashnaQuick',
    '/api/synastry': 'synastryQuick',
  }[endpoint] || '';
}

function endpointForAction(action) {
  return {
    varga: '/api/varga_full',
    annual: '/api/annual',
    tajika: '/api/tajika',
    muhurta: '/api/muhurta',
    bhava: '/api/bhava_chalit',
    sudarshana: '/api/sudarshana',
    nakshatra: '/api/nakshatra_full',
    jaimini: '/api/jaimini',
    charaDasha: '/api/dasha/chara',
    ashtakavarga: '/api/ashtakavarga',
    shadbala: '/api/shadbala',
    yogas: '/api/yogas',
    aspects: '/api/aspects',
    dasha: '/api/dasha',
    remedies: '/api/remedies',
    sadeSati: '/api/sade_sati',
    panchaMahapurusha: '/api/pancha_mahapurusha',
    rectification: '/api/rectification_gate',
    caseValidation: '/api/case_validation',
    divisionalYoga: '/api/divisional_yoga',
    deepVargaAvastha: '/api/deep_varga_avastha',
    kakshya: '/api/kakshya',
    bhavaBala: '/api/bhava_bala',
    transitTrigger: '/api/transit',
    thematicReport: '/api/thematic_report',
    career: '/api/career',
    relationship: '/api/relationship',
    kpQuick: '/api/kp',
    prashnaQuick: '/api/prashna',
    synastryQuick: '/api/synastry',
  }[action] || '';
}

function getTechniqueApiDoc(endpoint) {
  const catalog = window.__jyotishTechniqueCatalog || {};
  return catalog.api_docs?.[endpoint] || null;
}

function renderTechniqueApiDocs(apiDoc) {
  const openapi = apiDoc.openapi || {};
  return `
    <details class="technique-api-docs">
      <summary>cURL / OpenAPI</summary>
      <div class="technique-api-doc-grid">
        <div>
          <strong>cURL</strong>
          <pre>${escapeHtml(apiDoc.curl || '')}</pre>
        </div>
        <div>
          <strong>OpenAPI</strong>
          <pre>${escapeHtml(JSON.stringify(openapi, null, 2).slice(0, 5000))}</pre>
        </div>
      </div>
      <p>${escapeHtml(apiDoc.notes || '样例 payload 可复制到本地 API。')}</p>
    </details>
  `;
}

function normalizeDirectoryText(value) {
  return String(value || '').trim().toLowerCase();
}

function uniqueSorted(values) {
  return [...new Set((values || []).filter(value => value !== null && value !== undefined && value !== ''))]
    .sort((a, b) => String(a).localeCompare(String(b), 'zh-Hans-CN'));
}

function reuseLabel(reuse) {
  return {
    direct: '可直接复用',
    caution: '仅借鉴/需隔离',
    unknown: '需确认许可',
    benchmark_only: '仅benchmark',
    review_before_copy: '复制前确认',
    direct_or_port: '可复用/可移植',
  }[reuse] || reuse || '未知';
}

function productLevelLabel(level) {
  return {
    productized: '已产品化',
    api_backed: 'API承载',
    engine_or_full_reading: '引擎/完整解盘',
    registry_only: '待确认',
  }[level] || level || '未知';
}

function uxLevelLabel(level) {
  return {
    excellent: '优秀',
    usable: '可用',
    thin: '偏薄',
    not_user_ready: '未就绪',
  }[level] || level || '未知';
}

function uxCriterionLabel(key) {
  return {
    clear_entry: '入口',
    human_readable_conclusion: '结论',
    evidence_chain: '证据链',
    next_action: '下一步',
    json_hidden: '隐藏JSON',
    mobile_scannable: '移动端',
  }[key] || key;
}
