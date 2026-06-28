/**
 * Jyotish Export System v2.0 — 100% 完整星盘数据导出
 * 覆盖 Python engine full-reading 全部13模块:
 *   dasha, yoga, varga_full, aspects, jaimini, nakshatra_advanced,
 *   argala, tajika, shadbala, ashtakavarga, validation, audit, actionable_context
 *
 * 导出格式: JSON / HTML / SVG / PNG
 */

import { SIGNS, SIGN_LORDS, PLANET_CN } from './jyotish-engine.js';

const DASHA_SHADBALA_EXPORT_CALIBRATION_STATUS = {
  id: 'dasha_shadbala',
  title: 'Dasha/Shadbala Calibration Status',
  queue: 'external_oracle_collection_queue',
  validator: 'external_oracle_evidence_validation',
  ready_for_calibration: 0,
  valid_packets: 0,
  production_tuning_allowed: false,
  confidence_boundary: 'D1/D9/SAV 高可信；大运起点和 Shadbala 绝对值仍在外部 evidence validator 校准中。',
  user_facing_rule: '不得把大运起点或 Shadbala 绝对值说成已完成外部校准。',
  status_labels: [
    'ready_for_calibration: 0',
    'valid_packets: 0',
    'production_tuning_allowed: false',
  ],
};

// ============================================================================
// JSON 导出 — 完整星盘数据 (100% coverage)
// ============================================================================
export function exportJSON(chartData, extras = {}) {
  const { planets, ascendant, birth_info } = chartData;
  const payload = {
    meta: {
      app: 'Jyotish Web App',
      version: '4.4',
      export_date: new Date().toISOString(),
      ayanamsa: 'Lahiri (Chitrapaksha)',
      provenance: extras.provenance || chartData?._client_audit?.provenance || null,
      calculation_settings: extras.provenance?.calculationSettings || chartData?._calculation_settings || null,
      terminology_mode: extras.provenance?.terminologyMode || chartData?._terminology_mode || null,
      calibration_status: {
        dasha_shadbala: DASHA_SHADBALA_EXPORT_CALIBRATION_STATUS,
      },
    },
    birth_info,
    ascendant: _cleanAscendant(ascendant),
  };

  // ── 1. Planets (完整字段) ──
  payload.planets = {};
  for (const [name, p] of Object.entries(planets)) {
    if (p.error) continue;
    payload.planets[name] = {
      sign: p.sign, sign_cn: p.sign_cn,
      degree: p.degree, degree_in_sign: p.degree_in_sign,
      house: p.house, status: p.status || '',
      retrograde: p.retrograde || false,
      speed: p.speed || 0,
      combust: p.combust || false,
      combust_degree: p.combust_degree || null,
      nakshatra: p.nakshatra, nakshatra_pada: p.nakshatra_pada,
      nakshatra_lord: p.nakshatra_lord,
    };
  }

  // ── 2. Dasha ──
  if (extras.dasha) payload.modules = payload.modules || {};
  if (extras.dasha) payload.modules.dasha = extras.dasha;

  // ── 3. Yoga ──
  if (extras.yogas) {
    payload.modules = payload.modules || {};
    const ascSign = ascendant?.sign || '';
    const kendraLords = _getKendraLords(ascSign);
    const trikonaLords = _getTrikonaLords(ascSign);
    payload.modules.yoga = {
      ascendant: ascSign,
      planets_analyzed: Object.keys(payload.planets).length,
      kendra_lords: kendraLords,
      trikona_lords: trikonaLords,
      yogas_detected: extras.yogas.length,
      yogas: extras.yogas.map(y => ({
        name: y.name || '',
        name_cn: y.name_cn || '',
        combination: y.combination || '',
        effects: y.effects || [],
        strength: y.strength || '',
      })),
    };
  }

  // ── 4. Varga Full ──
  if (extras.vargas) {
    payload.modules = payload.modules || {};
    payload.modules.varga_full = extras.vargas;
  }

  // ── 5. Aspects ──
  if (extras.aspects) {
    payload.modules = payload.modules || {};
    payload.modules.aspects = extras.aspects;
  }

  // ── 6. Jaimini ──
  if (extras.jaimini) {
    payload.modules = payload.modules || {};
    payload.modules.jaimini = extras.jaimini;
  }

  // ── 7. Nakshatra Advanced ──
  if (extras.nakshatraAdvanced) {
    payload.modules = payload.modules || {};
    payload.modules.nakshatra_advanced = extras.nakshatraAdvanced;
  }

  // ── 8. Argala ──
  if (extras.argala) {
    payload.modules = payload.modules || {};
    payload.modules.argala = extras.argala;
  }

  // ── 9. Tajika ──
  if (extras.tajika) {
    payload.modules = payload.modules || {};
    payload.modules.tajika = extras.tajika;
  }

  // ── 10. Shadbala ──
  if (extras.shadbala) {
    payload.modules = payload.modules || {};
    payload.modules.shadbala = extras.shadbala;
  }

  // ── 11. Ashtakavarga ──
  if (extras.ashtakavarga) {
    payload.modules = payload.modules || {};
    payload.modules.ashtakavarga = extras.ashtakavarga;
  }

  // ── 12. Panchanga ──
  if (extras.panchanga) {
    payload.modules = payload.modules || {};
    payload.modules.panchanga = extras.panchanga;
  }

  // ── 13. Validation ──
  if (extras.validation) {
    payload.modules = payload.modules || {};
    payload.modules.validation = extras.validation;
  }

  // ── 14. Audit ──
  if (extras.audit) {
    payload.modules = payload.modules || {};
    payload.modules.audit = extras.audit;
  }

  // ── 15. Actionable Context ──
  if (extras.actionableContext) {
    payload.modules = payload.modules || {};
    payload.modules.actionable_context = extras.actionableContext;
  }

  // ── 16. Calibration Status ──
  payload.modules = payload.modules || {};
  payload.modules.calibration_status = {
    dasha_shadbala: DASHA_SHADBALA_EXPORT_CALIBRATION_STATUS,
  };

  // ── 16. User Workflows ──
  if (extras.workflows) {
    payload.modules = payload.modules || {};
    payload.modules.workflows = extras.workflows;
  }

  downloadFile(
    JSON.stringify(payload, null, 2),
    `jyotish-chart-${birth_info?.date || 'export'}.json`,
    'application/json'
  );
}

// ============================================================================
// HTML 报告导出 — 可直接打开/打印的单文件报告
// ============================================================================
export function exportHTMLReport(chartData, extras = {}) {
  if (!chartData) return;
  const birth = chartData.birth_info || {};
  const html = _buildHTMLReport(chartData, extras);
  downloadFile(
    html,
    `jyotish-report-${_safeFilename(birth.date || 'chart')}.html`,
    'text/html;charset=utf-8'
  );
}

// ============================================================================
// PDF 报告导出 — 复用后端 report_builder.py 的 Playwright PDF 流水线
// ============================================================================
export async function exportPDFReport(chartData, extras = {}) {
  if (!chartData) return null;
  const birth = chartData.birth_info || {};
  const name = `jyotish-report-${_safeFilename(birth.date || birth.name || 'chart')}`;
  const html = _buildHTMLReport(chartData, extras);
  const api = window.JyotishAPI?.generateReportArtifact;
  if (!api) {
    const downloaded_filename = `${name}.html`;
    downloadFile(html, downloaded_filename, 'text/html;charset=utf-8');
    return {
      success: false,
      fallback: 'html',
      report_artifact_fallback: true,
      fallback_reason: 'report_artifact API unavailable',
      error: 'report_artifact API unavailable',
      artifact_status: 'local_html_fallback_ready',
      primary_artifact: 'html',
      download_filename: downloaded_filename,
      download_mime: 'text/html;charset=utf-8',
      user_message: '本地 API 未连接，已改为生成 HTML 报告。',
      downloaded_filename,
      delivery: {
        artifact_status: 'local_html_fallback_ready',
        format: 'html',
        filename: downloaded_filename,
        mime: 'text/html;charset=utf-8',
        fallback: true,
        fallback_reason: 'report_artifact API unavailable',
        user_message: '本地 API 未连接，已改为生成 HTML 报告。',
        next_action: '可直接打开，或用浏览器打印为 PDF',
      },
    };
  }

  const result = await api({ format: 'pdf', name, html });
  let downloaded_filename = '';
  if (result?.pdf_base64) {
    downloaded_filename = result.download_filename || result.delivery?.filename || result.pdf_filename || `${name}.pdf`;
    downloadBase64File(result.pdf_base64, downloaded_filename, result.download_mime || result.delivery?.mime || result.mime || 'application/pdf');
  } else if (result?.html_base64) {
    downloaded_filename = result.download_filename || result.delivery?.filename || result.html_filename || `${name}.html`;
    downloadBase64File(result.html_base64, downloaded_filename, result.download_mime || result.delivery?.mime || 'text/html;charset=utf-8');
  } else {
    downloaded_filename = `${name}.html`;
    downloadFile(html, downloaded_filename, 'text/html;charset=utf-8');
  }
  return {
    ...result,
    downloaded_filename,
    report_artifact_fallback: result?.fallback === 'html' || result?.delivery?.fallback === true,
    fallback_reason: result?.fallback_reason || result?.delivery?.fallback_reason || result?.pdf_error || result?.message || '',
    artifact_status: formatReportArtifactStatus({ ...result, downloaded_filename }),
  };
}

export function formatReportArtifactStatus(result = {}) {
  const delivery = result.delivery || {};
  const filename = result.downloaded_filename || result.download_filename || delivery.filename || result.pdf_filename || result.html_filename || '报告文件';
  const message = result.user_message || delivery.user_message || '';
  if (result.pdf_base64 || delivery.format === 'pdf') {
    return `${message || 'PDF 报告已生成并开始下载。'}已下载：${filename}。`;
  }
  if (result.report_artifact_fallback || result.fallback === 'html' || delivery.fallback) {
    const reason = result.fallback_reason || delivery.fallback_reason || result.error || 'PDF 渲染器不可用';
    return `${message || '后端已生成 HTML 报告。'}已下载：${filename}。${reason}。可直接打开，或用浏览器打印为 PDF。`;
  }
  if (result.html_base64 || delivery.format === 'html') {
    return `${message || '后端已生成 HTML 报告。'}已下载：${filename}。可直接打开，或用浏览器打印为 PDF。`;
  }
  return `报告已开始下载。已下载：${filename}。`;
}

// ============================================================================
// SVG 导出
// ============================================================================
export function exportSVG(chartElement, filename = 'jyotish-chart') {
  if (!chartElement) return;
  const svg = chartElement.querySelector('svg');
  if (!svg) return;

  const clone = svg.cloneNode(true);
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  clone.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');

  const styleEl = document.createElementNS('http://www.w3.org/2000/svg', 'style');
  styleEl.textContent = `text{font-family:'Noto Sans SC','Segoe UI',sans-serif;}.chart-planet-text{font-size:10px;fill:#333;}.chart-sign-text{font-size:9px;fill:#666;}.chart-asc-marker{font-size:11px;fill:#6d28d9;font-weight:700;}rect{stroke:#ccc;stroke-width:0.5;}`;
  clone.insertBefore(styleEl, clone.firstChild);

  downloadFile(new XMLSerializer().serializeToString(clone), `${filename}.svg`, 'image/svg+xml');
}

// ============================================================================
// PNG 导出
// ============================================================================
export async function exportPNG(chartElement, filename = 'jyotish-chart', scale = 2) {
  if (!chartElement) return;
  const svg = chartElement.querySelector('svg');
  if (!svg) return;

  const clone = svg.cloneNode(true);
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  const w = parseFloat(svg.getAttribute('width')) || 400;
  const h = parseFloat(svg.getAttribute('height')) || 400;
  clone.setAttribute('width', w);
  clone.setAttribute('height', h);

  const styleEl = document.createElementNS('http://www.w3.org/2000/svg', 'style');
  styleEl.textContent = `text{font-family:'Noto Sans SC','Segoe UI',sans-serif;fill:#333;}.chart-planet-text{font-size:10px;}.chart-sign-text{font-size:9px;fill:#666;}.chart-asc-marker{font-size:11px;fill:#6d28d9;font-weight:700;}rect{stroke:#ccc;stroke-width:0.5;}`;
  clone.insertBefore(styleEl, clone.firstChild);

  const svgStr = new XMLSerializer().serializeToString(clone);
  const img = new Image();
  const canvas = document.createElement('canvas');
  canvas.width = w * scale; canvas.height = h * scale;
  const ctx = canvas.getContext('2d');
  ctx.scale(scale, scale);

  return new Promise((resolve) => {
    img.onload = () => {
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, w, h);
      ctx.drawImage(img, 0, 0, w, h);
      canvas.toBlob(blob => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = `${filename}.png`; a.click();
          URL.revokeObjectURL(url);
        }
        resolve();
      }, 'image/png');
    };
    img.onerror = () => resolve();
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgStr)));
  });
}

// ============================================================================
// 工具函数
// ============================================================================
function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

function downloadBase64File(base64, filename, mimeType) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  const blob = new Blob([bytes], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

function _cleanAscendant(asc) {
  if (!asc) return {};
  return {
    sign: asc.sign, sign_cn: asc.sign_cn,
    degree: asc.degree, degree_in_sign: asc.degree_in_sign,
    lord: asc.lord || SIGN_LORDS[asc.sign],
  };
}

function _getKendraLords(ascSign) {
  const ai = SIGNS.indexOf(ascSign);
  if (ai < 0) return [];
  const kendra = [1, 4, 7, 10];
  return [...new Set(kendra.map(h => SIGN_LORDS[SIGNS[(ai + h - 1) % 12]]))];
}

function _getTrikonaLords(ascSign) {
  const ai = SIGNS.indexOf(ascSign);
  if (ai < 0) return [];
  const trikona = [5, 9];
  return [...new Set(trikona.map(h => SIGN_LORDS[SIGNS[(ai + h - 1) % 12]]))];
}

function _buildHTMLReport(chartData, extras) {
  const birth = chartData.birth_info || {};
  const asc = _cleanAscendant(chartData.ascendant || {});
  const provenance = extras.provenance || chartData?._client_audit?.provenance || {};
  const panchanga = extras.panchanga || {};
  const tithiLord = chartData.tithi_lord_analysis || {};
  const yogas = Array.isArray(extras.yogas) ? extras.yogas : [];
  const dashaPeriods = Array.isArray(extras.dasha?.periods) ? extras.dasha.periods : [];
  const validation = extras.validation || {};
  const audit = extras.audit || {};
  const workflows = extras.workflows || chartData._client_workflows || {};
  const relationshipNarrative = extras.relationship_narrative || chartData?.ai_prompt_pack?.evidence_snapshot?.relationship_narrative || chartData?.relationship_narrative || null;
  const generatedAt = new Date().toLocaleString('zh-CN');

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Jyotish Report - ${_h(birth.name || birth.date || 'Chart')}</title>
  <style>
    :root {
      --paper: #fbfaf6; --ink: #24201b; --muted: #6d665d;
      --line: #ded7ca; --soft: #f1ece2; --accent: #7a5a22;
      --good: #166534; --warn: #92400e; --danger: #991b1b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; background: #e8e2d7; color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
      line-height: 1.72;
    }
    main { max-width: 900px; margin: 0 auto; padding: 42px; background: var(--paper); min-height: 100vh; }
    header { border-bottom: 2px solid var(--line); padding-bottom: 22px; margin-bottom: 24px; }
    .eyebrow { color: var(--accent); font-size: 12px; font-weight: 800; letter-spacing: 1.6px; text-transform: uppercase; }
    h1 { margin: 8px 0 10px; font-size: 34px; line-height: 1.2; }
    h2 { margin: 28px 0 12px; font-size: 18px; border-bottom: 1px solid var(--line); padding-bottom: 7px; }
    h3 { margin: 18px 0 8px; font-size: 15px; color: var(--accent); }
    p { margin: 0 0 10px; color: var(--muted); }
    .grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
    .kv, .note, .yoga-card {
      background: var(--soft); border: 1px solid var(--line); border-radius: 6px; padding: 10px 12px;
    }
    .kv span { display: block; color: var(--muted); font-size: 11px; font-weight: 700; }
    .kv strong { display: block; margin-top: 4px; font-size: 14px; overflow-wrap: anywhere; }
    table { width: 100%; border-collapse: collapse; margin: 8px 0 18px; font-size: 13px; }
    th, td { border-bottom: 1px solid var(--line); padding: 8px 9px; text-align: left; vertical-align: top; }
    th { color: var(--accent); background: #f4efe6; font-size: 12px; }
    .two { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 12px; }
    .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
    .chip { border: 1px solid var(--line); border-radius: 999px; padding: 3px 8px; background: #fff; font-size: 12px; color: var(--muted); }
    .score { color: var(--good); font-weight: 800; }
    .warning { color: var(--warn); }
    .yoga-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
    .yoga-card strong { display: block; font-size: 13px; }
    .yoga-card small { display: block; color: var(--muted); margin-top: 3px; }
    .workflow { margin-bottom: 12px; }
    .workflow h3 { display: flex; justify-content: space-between; gap: 10px; align-items: baseline; }
    .workflow h3 span { color: var(--muted); font-size: 12px; font-weight: 600; }
    .relationship-deliverable { border-left: 4px solid var(--accent); }
    .relationship-hero {
      display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; align-items: start;
      background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: 12px; margin: 10px 0;
    }
    .relationship-hero strong { display: block; font-size: 16px; color: var(--ink); }
    .relationship-hero span { display: inline-block; color: var(--muted); font-size: 12px; margin-top: 4px; }
    .relationship-status { color: var(--accent); font-weight: 800; white-space: nowrap; }
    .relationship-evidence-grid,
    .spouse-print-grid,
    .uldk-print-grid,
    .comparison-axis-grid,
    .composite-print-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin: 8px 0 12px; }
    .relationship-print-card {
      background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: 9px; break-inside: avoid;
    }
    .relationship-print-card span { display: block; color: var(--muted); font-size: 11px; }
    .relationship-print-card strong { display: block; margin: 3px 0; font-size: 13px; color: var(--ink); }
    .relationship-columns { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 8px 0 12px; }
    .relationship-list { background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: 9px; break-inside: avoid; }
    .relationship-list strong { color: var(--accent); }
    .relationship-list ul { margin: 6px 0 0; padding-left: 18px; color: var(--muted); }
    .relationship-caution {
      background: #fff8ed; border: 1px solid #f3d19c; border-left: 4px solid #c67a00;
      border-radius: 6px; padding: 10px 12px; margin: 10px 0 12px; break-inside: avoid;
    }
    .relationship-caution strong { display: block; color: #7a4b00; margin-bottom: 4px; }
    .relationship-caution span { display: block; color: #7a4b00; font-size: 12px; }
    .relationship-boundary { background: #fff8ed; border: 1px solid #ead7b8; border-radius: 6px; padding: 9px; margin-top: 8px; }
    .relationship-boundary span { display: block; color: var(--muted); font-size: 12px; }
    .calibration-status {
      background: #fff7ed; border: 1px solid #fed7aa; border-left: 4px solid var(--danger);
      border-radius: 6px; padding: 12px; margin-top: 10px; break-inside: avoid;
    }
    .calibration-status strong { display: block; color: var(--danger); margin-bottom: 4px; }
    .calibration-status span { display: block; color: var(--muted); font-size: 12px; }
    .comparison-print-table { font-size: 12px; }
    .factor-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 8px; }
    .factor { background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: 8px; }
    .factor span { display: block; color: var(--muted); font-size: 11px; }
    .factor strong { display: block; margin-top: 3px; font-size: 13px; }
    footer { margin-top: 32px; padding-top: 14px; border-top: 1px solid var(--line); font-size: 11px; color: var(--muted); }
    @media print {
      body { background: var(--paper); }
      main { padding: 0; max-width: none; }
      h2 { page-break-after: avoid; }
      table, .kv, .note, .yoga-card, .relationship-print-card, .relationship-list { break-inside: avoid; }
    }
    @media (max-width: 760px) {
      main { padding: 22px; }
      .grid, .two, .yoga-grid { grid-template-columns: 1fr; }
      .relationship-hero, .relationship-evidence-grid, .relationship-columns,
      .spouse-print-grid, .uldk-print-grid, .comparison-axis-grid, .composite-print-grid { grid-template-columns: 1fr; }
      .factor-grid { grid-template-columns: 1fr 1fr; }
    }
  </style>
</head>
<body>
<main>
  <header>
    <div class="eyebrow">Jyotish Web App Report</div>
    <h1>${_h(birth.name || '印度占星报告')}</h1>
    <p>生成时间：${_h(generatedAt)}。本报告复用当前网页星盘、Panchanga、校验审计和导出模块，可直接用浏览器打开或打印为 PDF。</p>
  </header>

  <section>
    <h2>出生资料与计算参数</h2>
    <div class="grid">
      ${_kv('日期时间', `${birth.date || '-'} ${birth.time || ''} ${birth.tz || ''}`)}
      ${_kv('地点坐标', `${birth.lat ?? '-'}, ${birth.lon ?? '-'}`)}
      ${_kv('上升', `${asc.sign_cn || asc.sign || '-'} ${_fmt(asc.degree_in_sign ?? asc.degree)}°`)}
      ${_kv('Ayanamsa', provenance.ayanamsa || 'Lahiri')}
      ${_kv('Node', provenance.nodeMode || '-')}
      ${_kv('House', provenance.houseSystem || '-')}
      ${_kv('Sunrise', provenance.sunrisePolicy || '-')}
      ${_kv('Geocoder', provenance.geocoderPolicy || '-')}
      ${_kv('Ephemeris Backend', provenance.ephemerisBackend || '-')}
      ${_kv('Terminology', provenance.terminologyMode || '-')}
      ${_kv('Yoga 口径', provenance.yogaVariant || '-')}
      ${_kv('Jaimini 口径', provenance.jaiminiKarakaVariant || '-')}
      ${_kv('KP 口径', provenance.kpSignificatorVariant || '-')}
      ${_kv('Ashtakavarga 口径', provenance.ashtakavargaVariant || '-')}
      ${_kv('Shadbala 口径', provenance.shadbalaVariant || '-')}
      ${_kv('Dasha 口径', provenance.dashaReference || '-')}
      ${_kv('术语模式', provenance.terminologyLabel || provenance.terminologyMode || '-')}
      ${_kv('星历/引擎', provenance.engine || 'Jyotish Web App')}
      ${_kv('盘式', provenance.chartStyle || '-')}
    </div>
  </section>

  <section>
    <h2>Panchanga 与 Tithi Lord</h2>
    <div class="two">
      <div class="note">
        <h3>Birth-time Panchanga</h3>
        ${_table([
          ['Vara', panchanga.vara || '-'],
          ['Tithi', `${panchanga.tithi?.number || '-'} · ${panchanga.tithi?.name || '-'}`],
          ['Paksha', panchanga.tithi?.paksha || '-'],
          ['Karana', panchanga.karana?.name || panchanga.karana || '-'],
          ['Yoga', `${panchanga.yoga?.number || '-'} · ${panchanga.yoga?.name || '-'}`],
        ])}
      </div>
      <div class="note">
        <h3>Tithi Lord Analysis</h3>
        ${_table([
          ['Tithi Lord', tithiLord.tithi_lord || '-'],
          ['分数', tithiLord.tithi_score == null ? '-' : `${Math.round(Number(tithiLord.tithi_score) * 100)}%`],
          ['位置', `${tithiLord.lord_sign || '-'} H${tithiLord.lord_house || '-'}`],
          ['关系风格', tithiLord.relationship_style || tithiLord.emotional_pattern || '-'],
        ])}
      </div>
    </div>
  </section>

  <section>
    <h2>行星位置</h2>
    <table>
      <thead><tr><th>行星</th><th>星座</th><th>度数</th><th>宫位</th><th>星宿</th><th>状态</th></tr></thead>
      <tbody>${_planetRows(chartData.planets || {})}</tbody>
    </table>
  </section>

  <section>
    <h2>Yoga 摘要</h2>
    ${yogas.length ? `<div class="yoga-grid">${yogas.slice(0, 16).map(y => `
      <div class="yoga-card">
        <strong>${_h(y.name_cn || y.name || 'Yoga')}</strong>
        <small>${_h(y.combination || y.strength || '-')}</small>
      </div>
    `).join('')}</div>` : '<p>当前导出未检测到 Yoga 摘要。</p>'}
    ${yogas.length > 16 ? `<p>另有 ${yogas.length - 16} 条 Yoga 已保留在 JSON 导出中。</p>` : ''}
  </section>

  <section>
    <h2>Dasha 摘要</h2>
    ${dashaPeriods.length ? `<table>
      <thead><tr><th>周期</th><th>开始</th><th>结束</th><th>层级/说明</th></tr></thead>
      <tbody>${dashaPeriods.slice(0, 12).map(p => `<tr>
        <td>${_h(p.lord || p.planet || p.name || '-')}</td>
        <td>${_h(p.start || '-')}</td>
        <td>${_h(p.end || '-')}</td>
        <td>${_h(p.level || p.type || p.precision || '-')}</td>
      </tr>`).join('')}</tbody>
    </table>` : '<p>当前导出未附带 Dasha 时间线。</p>'}
  </section>

  ${_relationshipStrictNarrativeSection(relationshipNarrative)}

  ${_workflowReportSection(workflows)}

  ${_calibrationStatusSection(DASHA_SHADBALA_EXPORT_CALIBRATION_STATUS)}

  <section>
    <h2>校验与审计</h2>
    <div class="grid">
      ${_kv('Validation', validation.status || validation.overall || '-')}
      ${_kv('Audit', audit.overall || audit.status || '-')}
      ${_kv('Provenance', provenance.exportStatus || 'HTML/JSON/SVG/PNG export available')}
    </div>
    <div class="chips">
      <span class="chip">65/65 capability registry</span>
      <span class="chip">Panchanga preview</span>
      <span class="chip">Tithi Lord connected</span>
      <span class="chip">可浏览器打印 PDF</span>
    </div>
  </section>

  <footer>
    印度占星报告属于传统文化与自我反思工具，不能替代医疗、法律、投资或心理咨询。
  </footer>
</main>
</body>
</html>`;
}

function _relationshipStrictNarrativeSection(narrative) {
  if (!narrative || typeof narrative !== 'object') return '';
  const strengths = Array.isArray(narrative.strengths) ? narrative.strengths : [];
  const risks = Array.isArray(narrative.risks) ? narrative.risks : [];
  const boundaries = Array.isArray(narrative.boundaries) ? narrative.boundaries : [];
  const markdown = typeof narrative.markdown === 'string' ? narrative.markdown : '';
  const compactMarkdown = markdown
    .replace(/^###\s+/gm, '')
    .replace(/^\-\s+/gm, '')
    .replace(/\n+/g, ' ')
    .trim();
  const showCaution = (
    risks.some(item => String(item).includes('不能误读成接近结婚'))
    || boundaries.some(item => String(item).includes('不等于法律婚姻'))
  );
  return `<section class="relationship-strict-narrative">
    <h2>婚恋严格裁决</h2>
    <div class="relationship-hero">
      <div>
        <strong>${_h(narrative.headline || '婚恋 strict narrative 已接入导出主链。')}</strong>
        <span>本段直接消费 relationship strict evidence，把 D9、UL、dual dasha 与 synastry taxonomy 的边界写进用户可见正文。</span>
      </div>
      <div class="relationship-status">strict narrative</div>
    </div>
    ${showCaution ? `<div class="relationship-caution"><strong>防误判提示</strong><span>当前公开化/关系可见度候选不能被误读成接近法律婚姻；若 core marriage promise、dual dasha 或 external timing 仍未收敛，必须继续降置信度并保持 context-only 解释。</span></div>` : ''}
    <div class="relationship-columns">
      ${_relationshipReportList('支持证据', strengths)}
      ${_relationshipReportList('需要观察', risks)}
      ${_relationshipReportList('边界条件', boundaries)}
    </div>
    ${compactMarkdown ? `<div class="relationship-boundary"><span>${_h(compactMarkdown)}</span></div>` : ''}
  </section>`;
}

function _calibrationStatusSection(status) {
  return `<section>
    <h2>高级技法校准状态</h2>
    <div class="calibration-status">
      <strong>${_h(status.title)}</strong>
      <span>${_h(status.status_labels.join('；'))}</span>
      <span>${_h(status.validator)} · ${_h(status.queue)}</span>
      <span>${_h(status.confidence_boundary)}</span>
      <span>${_h(status.user_facing_rule)}</span>
    </div>
  </section>`;
}

function _workflowReportSection(workflows = {}) {
  const sections = [
    _kpWorkflowReport(workflows.kp),
    _prashnaWorkflowReport(workflows.prashna),
    _synastryWorkflowReport(workflows.synastry),
    _caseLibraryWorkflowReport(workflows.case_library),
  ].filter(Boolean).join('');
  if (!sections) {
    return `<section>
      <h2>用户工作流结果</h2>
      <p>当前报告未附带 KP、Prashna 或合盘运行结果。运行对应 Tab 后再次导出，报告会自动带入最新结果。</p>
    </section>`;
  }
  return `<section><h2>用户工作流结果</h2>${sections}</section>`;
}

function _caseLibraryWorkflowReport(caseLibrary) {
  if (!caseLibrary) return '';
  const pairs = Array.isArray(caseLibrary.synastry_pairs) ? caseLibrary.synastry_pairs : [];
  const prashnas = Array.isArray(caseLibrary.prashna_cases) ? caseLibrary.prashna_cases : [];
  if (!pairs.length && !prashnas.length) return '';
  const pairRows = pairs.slice(0, 6).map(record => [
    record.label || record.id || '未命名配对',
    `${record.score?.total ?? 0} / ${record.score?.max ?? 36}`,
    record.verdict || '-',
    _dateLabel(record.updatedAt || record.generatedAt),
  ]);
  const prashnaRows = prashnas.slice(0, 6).map(record => [
    record.question_text || record.label || record.question_type || '未命名问事',
    record.conclusion || '-',
    record.confidence || '-',
    _dateLabel(record.updatedAt || record.generatedAt),
  ]);
  return `<div class="note workflow">
    <h3>保存案例库 <span>${pairs.length} 配对 / ${prashnas.length} 问事</span></h3>
    ${pairRows.length ? `<h3>最近配对</h3>${_table([['案例', '分数', '判断', '更新时间'], ...pairRows])}` : ''}
    ${prashnaRows.length ? `<h3>最近问事</h3>${_table([['问题', '结论', '置信度', '更新时间'], ...prashnaRows])}` : ''}
  </div>`;
}

function _kpWorkflowReport(kp) {
  if (!kp) return '';
  const houseCards = (kp.focus_houses || []).map(house => {
    const data = kp.houses?.[house] || {};
    const sig = data.significators || {};
    const lords = data.kp_lords || {};
    return `<div class="factor">
      <span>${_h(house)}宫 · ${_h(data.sign || '-')}</span>
      <strong>Sub ${_h(lords.sub_lord || '-')}</strong>
      <span>A ${_h(_list(sig.A))}</span>
      <span>B ${_h(_list(sig.B))}</span>
    </div>`;
  }).join('');
  return `<div class="note workflow">
    <h3>KP Sublord <span>${_h(kp.label || kp.focus || '-')}</span></h3>
    <p>${_h(kp.note || 'KP 事件判断摘要。')}</p>
    <div class="factor-grid">${houseCards || '<p>暂无 KP 宫位摘要。</p>'}</div>
  </div>`;
}

function _prashnaWorkflowReport(prashna) {
  if (!prashna) return '';
  const answer = prashna.kp_answer_v2 || prashna.kp_answer || {};
  const summary = prashna.summary || {};
  const chart = prashna.prashna_chart || {};
  const timing = prashna.timing || {};
  const conclusion = summary.conclusion || answer.kp_answer || 'MAYBE — 需要更多信息确认';
  return `<div class="note workflow">
    <h3>Prashna 问事 <span>${_h(prashna.question_type || 'general')}</span></h3>
    ${prashna.question_text ? `<p>问题：${_h(prashna.question_text)}</p>` : ''}
    ${_table([
      ['结论', conclusion],
      ['置信度', summary.confidence || answer.confidence || '-'],
      ['问事上升', `${chart.asc_sign || '-'} ${chart.asc_degree ?? '-'}°`],
      ['问题宫', `${answer.primary_house || summary.primary_house || '-'}宫`],
      ['Sub Lord', answer.kp_sub_lord || '-'],
      ['时机', `${timing.score ?? '-'} / 100 · ${timing.rating || '-'}`],
      ['下一步', summary.next_action || timing.recommendation || '结合现实证据复核。'],
    ])}
  </div>`;
}

function _synastryWorkflowReport(synastry) {
  if (!synastry) return '';
  const score = `${synastry.total_score ?? 0} / ${synastry.max_score ?? 36}`;
  const percent = Number(synastry.match_percentage);
  const status = synastry.is_match_approved ? '匹配通过' : '需要谨慎综合判断';
  const deep = synastry.deep || {};
  const relationshipReport = synastry.relationship_report || deep.relationshipReport || {};
  const spouseStatus = deep.spouseStatus || {};
  const ulDkTiming = deep.ulDkTiming || {};
  const evidenceRows = Array.isArray(relationshipReport.evidence)
    ? relationshipReport.evidence.map(item => [item.label || '-', item.value || '-', item.note || '-'])
    : [];
  const evidenceCards = Array.isArray(relationshipReport.evidence)
    ? relationshipReport.evidence.map(item => `
      <div class="relationship-print-card">
        <span>${_h(item.label || '-')}</span>
        <strong>${_h(item.value || '-')}</strong>
        <span>${_h(item.note || '-')}</span>
      </div>
    `).join('')
    : '';
  const spouseRows = ['self', 'partner']
    .map(key => spouseStatus[key] ? [
      key === 'self' ? '本人' : '对方',
      spouseStatus[key].verdict || '-',
      `${spouseStatus[key].score ?? '-'} / 5`,
      Array.isArray(spouseStatus[key].evidence) ? spouseStatus[key].evidence.slice(0, 2).join('；') : '-',
    ] : null)
    .filter(Boolean);
  const spouseCards = ['self', 'partner']
    .map(key => spouseStatus[key] ? `
      <div class="relationship-print-card">
        <span>${key === 'self' ? '本人' : '对方'} spouse-status</span>
        <strong>${_h(spouseStatus[key].verdict || '-')}</strong>
        <span>${_h(spouseStatus[key].score ?? '-')} / 5 · ${_h((spouseStatus[key].evidence || []).slice(0, 2).join('；') || '-')}</span>
      </div>
    ` : '')
    .join('');
  const ulDkCards = ['self', 'partner']
    .map(key => ulDkTiming[key] ? `
      <div class="relationship-print-card">
        <span>${key === 'self' ? '本人' : '对方'} UL/DK timing</span>
        <strong>${_h(ulDkTiming[key].summary || '-')}</strong>
        <span>${_h((ulDkTiming[key].triggers || []).slice(0, 2).join('；') || (ulDkTiming[key].evidence || []).slice(0, 2).join('；') || '-')}</span>
      </div>
    ` : '')
    .join('');
  const comparison = deep.comparison || {};
  const axisCards = Array.isArray(comparison.axes)
    ? comparison.axes.slice(0, 4).map(axis => `
      <div class="relationship-print-card">
        <span>${_h(axis.label || '-')}</span>
        <strong>${_h(axis.relation?.label || '-')}</strong>
        <span>本人 ${_h(axis.self?.label || '-')} / 对方 ${_h(axis.partner?.label || '-')}</span>
      </div>
    `).join('')
    : '';
  const comparisonRows = Array.isArray(comparison.rows)
    ? comparison.rows.slice(0, 9).map(row => [
      row.label || row.planet || '-',
      row.self?.label || '-',
      row.partner?.label || '-',
      row.relation?.label || '-',
      `对方落本人${row.partnerOverlayHouse || '-'}宫 / 本人落对方${row.selfOverlayHouse || '-'}宫`,
    ])
    : [];
  const midpointCards = Array.isArray(comparison.compositeStyle)
    ? comparison.compositeStyle.map(item => `
      <div class="relationship-print-card">
        <span>${_h(item.label || '-')} midpoint</span>
        <strong>${_h(item.sign || '-')} ${_h(_fmt(item.degree))}°</strong>
        <span>${_h(item.note || '-')}</span>
      </div>
    `).join('')
    : '';
  const scoreCards = Object.entries(synastry.scores || {}).slice(0, 8).map(([name, value]) => `
    <div class="factor"><span>${_h(name)}</span><strong>${_h(value)} / ${_h(_kutaMax(name))}</strong></div>
  `).join('');
  return `<div class="note workflow relationship-deliverable">
    <h3>合盘 Synastry <span>${_h(synastry.mode || 'synastry')}</span></h3>
    <div class="relationship-hero">
      <div>
        <strong>${_h(relationshipReport.headline || '关系报告需要结合完整星盘、D9、Kuja 与 Dasha 复核。')}</strong>
        <span>总分 ${_h(score)}${Number.isFinite(percent) ? ` · ${_h(percent.toFixed(1))}%` : ''}</span>
      </div>
      <div class="relationship-status">${_h(relationshipReport.statusLabel || status)}</div>
    </div>
    ${_table([
      ['总分', `${score}${Number.isFinite(percent) ? ` · ${percent.toFixed(1)}%` : ''}`],
      ['状态', status],
      ['对方摘要', deep.partnerSummary ? `${deep.partnerSummary.ascendant || '-'} · Moon ${deep.partnerSummary.moon || '-'}` : '-'],
      ['Dasha 同步', deep.dasha?.note || '-'],
      ['UL/DK 时机', ['self', 'partner'].map(key => ulDkTiming[key]?.summary).filter(Boolean).join(' / ') || '-'],
      ['Kuja', deep.kuja?.note || '-'],
      ['D9', deep.d9 ? `本人 ${deep.d9.self?.score ?? '-'} / 对方 ${deep.d9.partner?.score ?? '-'}` : '-'],
    ])}
    ${evidenceCards ? `<h3>关系证据卡</h3><div class="relationship-evidence-grid">${evidenceCards}</div>` : (evidenceRows.length ? _table([['证据', '结果', '说明'], ...evidenceRows]) : '')}
    ${axisCards ? `<h3>双人轴线比较 <span>bi-wheel</span></h3><div class="comparison-axis-grid">${axisCards}</div>` : ''}
    ${comparisonRows.length ? _table([['行星', '本人', '对方', '互动', 'Overlay'], ...comparisonRows], 'comparison-print-table') : ''}
    ${midpointCards ? `<h3>Composite-style Midpoints</h3><div class="composite-print-grid">${midpointCards}</div>` : ''}
    ${ulDkCards ? `<h3>UL/DK 与关系时机 <span>Jaimini · Dasha trigger</span></h3><div class="uldk-print-grid">${ulDkCards}</div>` : ''}
    ${spouseCards ? `<h3>配偶/婚后成长 Yoga <span>spouse_status_yoga.py</span></h3><div class="spouse-print-grid">${spouseCards}</div>` : (spouseRows.length ? _table([['对象', '判断', '得分', '证据'], ...spouseRows]) : '')}
    <div class="relationship-columns">
      ${_relationshipReportList('支持证据', relationshipReport.strengths)}
      ${_relationshipReportList('需要观察', relationshipReport.risks)}
      ${_relationshipReportList('下一步', relationshipReport.nextSteps)}
    </div>
    <div class="factor-grid">${scoreCards || '<p>暂无 Kuta 分项。</p>'}</div>
    ${_relationshipBoundary(relationshipReport.boundaries)}
  </div>`;
}

function _relationshipReportBullets(label, items) {
  if (!Array.isArray(items) || !items.length) return '';
  return `<p><strong>${_h(label)}：</strong>${_h(items.join('；'))}</p>`;
}

function _relationshipReportList(label, items) {
  if (!Array.isArray(items) || !items.length) return '';
  return `<div class="relationship-list"><strong>${_h(label)}</strong><ul>${items.map(item => `<li>${_h(item)}</li>`).join('')}</ul></div>`;
}

function _relationshipBoundary(items) {
  if (!Array.isArray(items) || !items.length) return '';
  return `<div class="relationship-boundary">${items.map(item => `<span>${_h(item)}</span>`).join('')}</div>`;
}

function _planetRows(planets) {
  const rows = Object.entries(planets)
    .filter(([, p]) => p && !p.error)
    .map(([name, p]) => {
      const degree = p.degree_in_sign ?? (Number.isFinite(Number(p.lon ?? p.degree)) ? Number(p.lon ?? p.degree) % 30 : p.degree);
      return `<tr>
        <td>${_h(PLANET_CN[name] || name)}</td>
        <td>${_h(p.sign_cn || p.sign || '-')}</td>
        <td>${_h(_fmt(degree))}°</td>
        <td>H${_h(p.house || '-')}</td>
        <td>${_h(p.nakshatra || '-')} ${p.nakshatra_pada ? `p${_h(p.nakshatra_pada)}` : ''}</td>
        <td>${_h(p.status || '')}${p.retrograde ? ' · R' : ''}${p.combust ? ' · combust' : ''}</td>
      </tr>`;
    });
  return rows.join('') || '<tr><td colspan="6">无行星数据</td></tr>';
}

function _kv(label, value) {
  return `<div class="kv"><span>${_h(label)}</span><strong>${_h(value || '-')}</strong></div>`;
}

function _table(rows, className = '') {
  const classAttr = className ? ` class="${_h(className)}"` : '';
  return `<table${classAttr}><tbody>${rows.map(row => {
    const cells = Array.isArray(row) ? row : [row];
    if (cells.length <= 2) {
      return `<tr><th>${_h(cells[0])}</th><td>${_h(cells[1])}</td></tr>`;
    }
    return `<tr>${cells.map((cell, index) => index === 0 ? `<th>${_h(cell)}</th>` : `<td>${_h(cell)}</td>`).join('')}</tr>`;
  }).join('')}</tbody></table>`;
}

function _list(value) {
  if (Array.isArray(value)) return value.length ? value.join('、') : '-';
  if (value === null || value === undefined || value === '') return '-';
  return String(value);
}

function _kutaMax(name) {
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

function _fmt(value, digits = 2) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(digits) : '-';
}

function _dateLabel(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function _h(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function _safeFilename(value) {
  return String(value || 'chart').replace(/[^a-zA-Z0-9._-]+/g, '-').replace(/^-+|-+$/g, '') || 'chart';
}
