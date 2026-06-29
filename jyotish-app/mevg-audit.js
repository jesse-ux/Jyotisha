import { PLANET_CN, SIGN_LORDS } from './jyotish-engine.js';
import { escapeHtml, escapeAttr, safeNumber } from './security.js';

const SOURCE_TIERS = [
  ['classic', '经典文本/学院', 'BPHS、B.V. Raman、K.N. Rao、Sanjay Rath、ICAS/BVRI'],
  ['expert', '知名占星师', 'Marc Boney、Hart de Fouw、传统师承文章或讲座'],
  ['specialist', '专业占星网站', 'AstroSage、AstroVed、Cosmic Insights、Vedic Astrology Journal'],
  ['case', '案例库', '本地真实案例库、名人验证案例、历史事件对照'],
];

const BOUNDARIES = [
  '每条预测必须先拆成“承诺 Promise”与“激活 Activation”，不能只看 Dasha 或 Transit 单点下结论。',
  '没有外部来源支持的 Yoga、Dasha、Transit、补救措施，只能作为待验证假设。',
  '出生时间不确定时，D9、D10、特殊 Lagna、Pratyantar 级别判断必须降级。',
  '占星输出的是结构模式、主题强弱与时间窗口，不保证具体事件形式或结果。',
];

function planetName(name) {
  return PLANET_CN[name] ? `${PLANET_CN[name]} ${name}` : name || '-';
}

function signName(sign) {
  return sign ? `${sign}` : '-';
}

function currentDashaLords(dashaData) {
  const md = dashaData?.current_dasha;
  const ad = md?.antardasha?.find(item => item.is_current);
  const pd = ad?.pratyantardasha?.find(item => item.is_current);
  return [md?.lord, ad?.lord, pd?.lord].filter(Boolean);
}

function buildClaims({ ascendant, moonP, allYogas, dashaData, chartData }) {
  const claims = [];
  if (ascendant?.sign) {
    claims.push({
      area: '本命身份',
      claim: `${signName(ascendant.sign)} 上升，命主星为 ${planetName(ascendant.lord || SIGN_LORDS[ascendant.sign])}`,
      evidence: ['D1 上升点', '宫主星表'],
      query: `"${ascendant.sign} ascendant lord ${ascendant.lord || SIGN_LORDS[ascendant.sign]}" Vedic astrology interpretation`,
      status: 'internal',
    });
  }
  if (moonP?.nakshatra) {
    claims.push({
      area: '月亮星宿',
      claim: `Moon 位于 ${moonP.nakshatra} Pada ${moonP.nakshatra_pada || '-'}，用于 Dasha 起点与心理主题`,
      evidence: ['Moon 黄经', 'Nakshatra 切分'],
      query: `"${moonP.nakshatra}" nakshatra pada ${moonP.nakshatra_pada || ''} Vedic astrology traits`,
      status: 'internal',
    });
  }
  const topYogas = (allYogas || []).slice(0, 3);
  topYogas.forEach(yoga => {
    claims.push({
      area: 'Yoga',
      claim: `${yoga.name_cn || yoga.name}：${yoga.combination || yoga.effects || '需要确认形成条件'}`,
      evidence: ['Yoga 规则引擎', yoga.category || '未分类'],
      query: `"${yoga.name}" Vedic astrology formation conditions effects case study`,
      status: 'external_required',
    });
  });
  currentDashaLords(dashaData).slice(0, 2).forEach((lord, index) => {
    claims.push({
      area: index === 0 ? 'Mahadasha' : 'Antardasha',
      claim: `当前 ${index === 0 ? '大运' : '小运'}主星 ${planetName(lord)} 需要结合其落宫、宫主与分盘确认兑现方式`,
      evidence: ['Vimshottari 时间线', 'Moon Nakshatra 起算'],
      query: `"${lord}" "${index === 0 ? 'Mahadasha' : 'Antardasha'}" effects Vedic astrology case study`,
      status: 'external_required',
    });
  });
  const special = chartData?.special_lagnas;
  if (special?.precision) {
    claims.push({
      area: '特殊 Lagna',
      claim: `HL/GL/VL 精度：${special.precision}；用于辅助财富、行动与身份定位`,
      evidence: ['Python API', special.sunrise_local_time ? `日出 ${special.sunrise_local_time}` : '日出校正字段'],
      query: `"Hora Lagna" "Ghati Lagna" interpretation Jaimini Vedic astrology`,
      status: special.precision === 'sunrise_correct' ? 'internal' : 'limited',
    });
  }
  return claims;
}

function buildInternalChecks({ validation, chartData, allYogas, dashaData }) {
  const checks = [];
  const validationPassed = safeNumber(validation?.passed, 0);
  const validationTotal = safeNumber(validation?.total_checks || validation?.checked, 0);
  checks.push({
    name: 'R1-R10 数据完整性',
    status: validation?.valid ? 'pass' : 'warn',
    detail: validationTotal ? `${validationPassed}/${validationTotal} 项通过` : '未取得完整校验表',
  });
  checks.push({
    name: 'Rahu/Ketu 轴线',
    status: (validation?.results || []).find(r => r.rule === 'R5')?.passed ? 'pass' : 'warn',
    detail: (validation?.results || []).find(r => r.rule === 'R5')?.detail || '未找到 R5 结果',
  });
  checks.push({
    name: 'Dasha 时间线',
    status: dashaData?.current_dasha ? 'pass' : 'warn',
    detail: dashaData?.current_dasha ? `当前 ${planetName(dashaData.current_dasha.lord)}` : '未取得当前大运',
  });
  checks.push({
    name: 'Yoga 规则命中',
    status: allYogas?.length ? 'pass' : 'warn',
    detail: `${allYogas?.length || 0} 条规则命中；解释仍需 MEVG 外部来源`,
  });
  checks.push({
    name: '特殊 Lagna 精度',
    status: chartData?.special_lagnas?.precision === 'sunrise_correct' ? 'pass' : 'warn',
    detail: chartData?.special_lagnas?.precision === 'sunrise_correct' ? '日出校正版' : '缺少日出校正或后端字段',
  });
  return checks;
}

function confidenceProfile({ validation, allYogas, dashaData, chartData }) {
  let score = 52;
  if (validation?.valid) score += 14;
  if ((allYogas || []).length) score += 8;
  if (dashaData?.current_dasha) score += 10;
  if (chartData?.special_lagnas?.precision === 'sunrise_correct') score += 8;
  const externalRequired = Math.min(18, Math.max(8, (allYogas || []).slice(0, 3).length * 5 + 8));
  score -= externalRequired;
  const bounded = Math.max(25, Math.min(86, Math.round(score)));
  const level = bounded >= 75 ? '中高' : bounded >= 58 ? '中' : '谨慎';
  return {
    score: bounded,
    level,
    cap: '未执行实时外部检索时，预测/补救/具体事件判断最高只建议给到中等置信度。',
  };
}

function buildVedAstroOverviewHighlights(chartData = {}) {
  const overview = chartData?.ai_prompt_pack?.evidence_snapshot?.vedastro_overview
    || chartData?.modules?.vedastro_range_scan_result
    || chartData?.vedastro_overview
    || null;
  if (!overview || typeof overview !== 'object' || overview.status !== 'ok') return [];

  const topEvents = overview.top_events_by_domain || {};
  const highlights = [];
  const career = topEvents.career || null;
  const wealth = topEvents.wealth || topEvents.finance || null;

  if (career) {
    highlights.push({
      label: 'Career VedAstro overview',
      detail: `${career.signal_label || career.event_id || 'career window'} · ${career.start || overview.reference_date || '-'} · single_day_overview`,
    });
  }
  if (wealth) {
    highlights.push({
      label: 'Wealth VedAstro overview',
      detail: `${wealth.signal_label || wealth.event_id || 'wealth window'} · ${wealth.start || overview.reference_date || '-'} · single_day_overview`,
    });
  }
  if (!highlights.length && overview.reference_date) {
    highlights.push({
      label: 'VedAstro main_entry_overview',
      detail: `${overview.reference_date} · single_day_overview · vedastro_overview`,
    });
  }
  return highlights;
}

export function buildMEVGAudit(input) {
  const claims = buildClaims(input);
  const internalChecks = buildInternalChecks(input);
  const profile = confidenceProfile(input);
  const vedastroHighlights = buildVedAstroOverviewHighlights(input.chartData);
  return {
    profile,
    internalChecks,
    claims,
    vedastroHighlights,
    sourceTiers: SOURCE_TIERS,
    boundaries: BOUNDARIES,
    stats: {
      claims: claims.length,
      externalRequired: claims.filter(c => c.status === 'external_required').length,
      internalPassed: internalChecks.filter(c => c.status === 'pass').length,
      internalTotal: internalChecks.length,
    },
  };
}

export function renderMEVGAudit(container, audit) {
  if (!container || !audit) return;
  const statusLabel = {
    internal: '内部已校验',
    external_required: '需外部验证',
    limited: '精度受限',
  };
  const checkHtml = audit.internalChecks.map(check => `
    <div class="mevg-check mevg-${escapeAttr(check.status)}">
      <span>${escapeHtml(check.status === 'pass' ? '通过' : '注意')}</span>
      <strong>${escapeHtml(check.name)}</strong>
      <p>${escapeHtml(check.detail)}</p>
    </div>
  `).join('');
  const claimHtml = audit.claims.map(claim => `
    <div class="mevg-claim mevg-claim-${escapeAttr(claim.status)}">
      <div class="mevg-claim-head">
        <strong>${escapeHtml(claim.area)}</strong>
        <span>${escapeHtml(statusLabel[claim.status] || claim.status)}</span>
      </div>
      <p>${escapeHtml(claim.claim)}</p>
      <div class="mevg-evidence">${claim.evidence.map(item => `<span>${escapeHtml(item)}</span>`).join('')}</div>
      <code>${escapeHtml(claim.query)}</code>
    </div>
  `).join('');
  const sourceHtml = audit.sourceTiers.map(([, label, detail]) => `
    <div class="mevg-source">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(detail)}</span>
    </div>
  `).join('');
  const vedastroHtml = (audit.vedastroHighlights || []).map(item => `
    <div class="mevg-source">
      <strong>${escapeHtml(item.label)}</strong>
      <span>${escapeHtml(item.detail)}</span>
    </div>
  `).join('');
  container.innerHTML = `
    <section class="mevg-panel">
      <div class="mevg-head">
        <div>
          <h4>MEVG 外部验证门控</h4>
          <p>把当前星盘的主要判断拆成证据、外部检索项、置信度上限和边界声明。</p>
        </div>
        <div class="mevg-score">
          <span>${escapeHtml(audit.profile.level)}置信</span>
          <strong>${escapeHtml(audit.profile.score)}</strong>
        </div>
      </div>

      <div class="mevg-summary">
        <div><strong>${escapeHtml(audit.stats.claims)}</strong><span>待审计声明</span></div>
        <div><strong>${escapeHtml(audit.stats.externalRequired)}</strong><span>需外部来源</span></div>
        <div><strong>${escapeHtml(`${audit.stats.internalPassed}/${audit.stats.internalTotal}`)}</strong><span>内部校验</span></div>
      </div>

      <div class="mevg-cap">${escapeHtml(audit.profile.cap)}</div>
      <div class="mevg-check-grid">${checkHtml}</div>

      <div class="mevg-section">
        <h4>声明与建议检索词</h4>
        <div class="mevg-claims">${claimHtml}</div>
      </div>

      <div class="mevg-section">
        <h4>来源优先级</h4>
        <div class="mevg-sources">${sourceHtml}</div>
      </div>

      ${vedastroHtml ? `
        <div class="mevg-section">
          <h4>VedAstro 概览提示</h4>
          <div class="mevg-sources">${vedastroHtml}</div>
          <p class="mevg-cap">这些提示来自 main_entry_overview / single_day_overview；用于事业/财富外部补证，不替代长周期精扫。</p>
        </div>
      ` : ''}

      <div class="mevg-section">
        <h4>预测边界</h4>
        <ul class="mevg-boundaries">
          ${audit.boundaries.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </div>
    </section>
  `;
}
