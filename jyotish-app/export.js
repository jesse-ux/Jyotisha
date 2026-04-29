/**
 * Jyotish Export System v2.0 — 100% 完整星盘数据导出
 * 覆盖 Python engine full-reading 全部13模块:
 *   dasha, yoga, varga_full, aspects, jaimini, nakshatra_advanced,
 *   argala, tajika, shadbala, ashtakavarga, validation, audit, actionable_context
 *
 * 导出格式: JSON / SVG / PNG
 */

import { SIGNS, SIGN_LORDS, PLANET_CN } from './jyotish-engine.js';

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

  downloadFile(
    JSON.stringify(payload, null, 2),
    `jyotish-chart-${birth_info?.date || 'export'}.json`,
    'application/json'
  );
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
