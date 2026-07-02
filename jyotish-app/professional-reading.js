import { escapeHtml } from './security.js';

const DEFAULT_QUESTION = '请按高严谨流程做盲推解盘，先列 Technique Audit Table，再给结论。';
const DEFAULT_THEMES = ['career', 'relationship', 'finance', 'health', 'timing'];

export function renderProfessionalReadingPanel(state = {}) {
  const status = state.gatewayStatus || {};
  const result = state.result?.professional_reading || null;
  return `
    <section class="provenance-card professional-reading-panel">
      <div class="provenance-head">
        <span>Web Professional Reading v1</span>
        <strong>${escapeHtml(status.active_backend || 'gateway-ready')}</strong>
      </div>
      <div class="trust-status-grid">
        ${renderMetric('Technique Audit Table', 'required', '必须显示 Functional Benefic/Malefic、MEVG、Real Case Calibration。')}
        ${renderMetric('MEVG / Global Web Evidence', 'queued-or-blocked', '外部资料采集必须进入队列或说明 blocked。')}
        ${renderMetric('Real Case Calibration', 'required', '找不到相似案例时必须降级，不得静默跳过。')}
        ${renderMetric('VedAstro Gateway Boundary', status.mode || 'local_first', '普通中国大陆用户不需要浏览器直连 VedAstro。')}
      </div>
      <div class="professional-reading-actions">
        <button type="button" class="provenance-action" data-action="professional-reading-run">运行专业解盘</button>
        <button type="button" class="provenance-action" data-action="professional-reading-gateway">刷新网关状态</button>
      </div>
      <div id="professional-reading-status" class="workspace-import-status" aria-live="polite">
        ${escapeHtml(state.message || '等待运行。')}
      </div>
      ${result ? renderProfessionalReadingResult(result) : ''}
    </section>
  `;
}

export function buildProfessionalReadingPayload(chartData = {}, overrides = {}) {
  const birth = window.__jyotishBirth || chartData.birth_info || chartData.birth || {};
  return {
    year: Number(birth.year || birth.date?.slice?.(0, 4) || overrides.year || REDACTED_YEAR),
    month: Number(birth.month || birth.date?.slice?.(5, 7) || overrides.month || 1),
    day: Number(birth.day || birth.date?.slice?.(8, 10) || overrides.day || 1),
    hour: Number(birth.hour ?? overrides.hour ?? 12),
    minute: Number(birth.minute ?? overrides.minute ?? 0),
    second: Number(birth.second ?? overrides.second ?? 0),
    lat: Number(birth.lat ?? overrides.lat ?? 0),
    lon: Number(birth.lon ?? overrides.lon ?? 0),
    tz: Number(birth.tz ?? overrides.tz ?? 8),
    question: overrides.question || DEFAULT_QUESTION,
    themes: overrides.themes || DEFAULT_THEMES,
    reference_date: overrides.reference_date || new Date().toISOString().slice(0, 10),
    blind_mode: overrides.blind_mode ?? true,
    disable_life_event_feedback: overrides.disable_life_event_feedback ?? true,
  };
}

export function bindProfessionalReadingPanel(container, chartData = null, setState = () => {}) {
  container?.querySelector('[data-action="professional-reading-gateway"]')?.addEventListener('click', async () => {
    setState({ message: '正在刷新 VedAstro Gateway...' });
    const gatewayStatus = await window.JyotishAPI.getVedAstroGatewayStatus();
    setState({ gatewayStatus, message: 'VedAstro Gateway 状态已刷新。' });
  });
  container?.querySelector('[data-action="professional-reading-run"]')?.addEventListener('click', async () => {
    setState({ message: '正在运行专业解盘代理...' });
    const payload = buildProfessionalReadingPayload(chartData);
    const result = await window.JyotishAPI.runProfessionalReading(payload);
    setState({ result, gatewayStatus: result?.professional_reading?.vedastro_gateway?.gateway_status || {}, message: '专业解盘包已生成。' });
  });
}

function renderMetric(label, value, note) {
  return `
    <div class="trust-status-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
      <p>${escapeHtml(note)}</p>
    </div>
  `;
}

function renderProfessionalReadingResult(result) {
  const gateway = result.vedastro_gateway || {};
  const controls = result.user_led_calibration_controls || {};
  const requiredRows = result.technique_audit_table_required_rows || [];
  return `
    <div class="professional-reading-result">
      <h3>Professional Reading Packet</h3>
      <p>status: ${escapeHtml(gateway.status || 'unknown')}</p>
      <p>blind_mode: ${escapeHtml(String(Boolean(controls.blind_mode)))}</p>
      <ul>
        ${requiredRows.map(row => `<li>${escapeHtml(row)}</li>`).join('')}
      </ul>
    </div>
  `;
}
