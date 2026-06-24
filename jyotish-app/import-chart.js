import { searchCities } from './jyotish-engine.js';
import { escapeHtml, escapeAttr, safeNumber } from './security.js';

const MONTHS = {
  jan: 1, january: 1, feb: 2, february: 2, mar: 3, march: 3,
  apr: 4, april: 4, may: 5, jun: 6, june: 6, jul: 7, july: 7,
  aug: 8, august: 8, sep: 9, sept: 9, september: 9, oct: 10,
  october: 10, nov: 11, november: 11, dec: 12, december: 12,
};

function normalizeText(text) {
  return String(text || '')
    .replace(/\r/g, '\n')
    .replace(/[：]/g, ':')
    .replace(/[，]/g, ',')
    .replace(/\u00a0/g, ' ')
    .replace(/[ \t]+/g, ' ')
    .trim();
}

function sectionAfter(text, labels) {
  const pattern = new RegExp(`(?:${labels.join('|')})\\s*[:：]?\\s*([^\\n]{1,80})`, 'i');
  return text.match(pattern)?.[1]?.trim() || '';
}

function parseDate(text) {
  const normalized = normalizeText(text);
  const labelValue = sectionAfter(normalized, [
    'date of birth', 'birth date', 'dob', '出生日期', '生日', '出生',
  ]);
  const candidates = [labelValue, normalized].filter(Boolean);
  for (const value of candidates) {
    let m = value.match(/\b((?:18|19|20)\d{2})[-/.年 ]+(\d{1,2})[-/.月 ]+(\d{1,2})/);
    if (m) return { year: +m[1], month: +m[2], day: +m[3] };
    m = value.match(/\b(\d{1,2})[-/. ]+(\d{1,2})[-/. ]+((?:18|19|20)\d{2})\b/);
    if (m) return { year: +m[3], month: +m[2], day: +m[1] };
    m = value.match(/\b(\d{1,2})\s+([A-Za-z]{3,9})\s+((?:18|19|20)\d{2})\b/);
    if (m && MONTHS[m[2].toLowerCase()]) return { year: +m[3], month: MONTHS[m[2].toLowerCase()], day: +m[1] };
    m = value.match(/\b([A-Za-z]{3,9})\s+(\d{1,2}),?\s+((?:18|19|20)\d{2})\b/);
    if (m && MONTHS[m[1].toLowerCase()]) return { year: +m[3], month: MONTHS[m[1].toLowerCase()], day: +m[2] };
  }
  return null;
}

function parseTime(text) {
  const normalized = normalizeText(text);
  const labelValue = sectionAfter(normalized, [
    'time of birth', 'birth time', 'tob', '出生时间', '时间',
  ]);
  const candidates = [labelValue, normalized].filter(Boolean);
  for (const value of candidates) {
    const m = value.match(/\b([01]?\d|2[0-3])[:：.](\d{2})(?:\s*(am|pm|AM|PM))?\b/);
    if (!m) continue;
    let hour = +m[1];
    const minute = +m[2];
    const suffix = m[3]?.toLowerCase();
    if (suffix === 'pm' && hour < 12) hour += 12;
    if (suffix === 'am' && hour === 12) hour = 0;
    return { hour, minute };
  }
  return null;
}

function parseCoord(text, kind) {
  const label = kind === 'lat'
    ? '(?:latitude|lat|纬度)'
    : '(?:longitude|lon|lng|经度)';
  const re = new RegExp(`${label}\\s*[:：]?\\s*([+-]?\\d{1,3}(?:\\.\\d+)?)\\s*([NSEW东西南北])?`, 'i');
  const m = normalizeText(text).match(re);
  if (!m) return null;
  let value = +m[1];
  const dir = m[2]?.toUpperCase();
  if (['S', 'W', '南', '西'].includes(dir)) value = -Math.abs(value);
  return Number.isFinite(value) ? value : null;
}

function parseTimezone(text) {
  const normalized = normalizeText(text);
  const m = normalized.match(/(?:timezone|time zone|tz|UTC|GMT|时区)\s*[:：]?\s*(?:UTC|GMT)?\s*([+-]?\d{1,2}(?:\.\d+)?)(?::?(\d{2}))?/i);
  if (!m) return null;
  const base = +m[1];
  const minutes = m[2] ? (+m[2] / 60) * (base < 0 ? -1 : 1) : 0;
  const tz = base + minutes;
  return Number.isFinite(tz) ? tz : null;
}

function parseCity(text) {
  const value = sectionAfter(normalizeText(text), [
    'place of birth', 'birth place', 'birth city', 'place', 'city', '出生地', '出生城市', '地点', '城市',
  ]);
  const cleaned = value.replace(/[,，].*$/, '').trim();
  if (cleaned.length >= 2) return cleaned;
  return '';
}

function resolveCity(city) {
  if (!city) return null;
  const results = searchCities(city);
  return results[0] || null;
}

export function parseImportedChartText(text) {
  const normalized = normalizeText(text);
  const date = parseDate(normalized);
  const time = parseTime(normalized);
  const city = parseCity(normalized);
  const cityMatch = resolveCity(city);
  const lat = parseCoord(normalized, 'lat') ?? cityMatch?.lat ?? null;
  const lon = parseCoord(normalized, 'lon') ?? cityMatch?.lon ?? null;
  const tz = parseTimezone(normalized) ?? cityMatch?.tz ?? null;
  const fields = {
    ...(date || {}),
    ...(time || {}),
    city: city || cityMatch?.name || '',
    lat,
    lon,
    tz,
  };
  const missing = [];
  if (!date) missing.push('出生日期');
  if (!time) missing.push('出生时间');
  if (lat == null || lon == null) missing.push('出生地经纬度');
  if (tz == null) missing.push('时区');
  const quality = Math.round([
    date ? 30 : 0,
    time ? 25 : 0,
    lat != null && lon != null ? 25 : 0,
    tz != null ? 15 : 0,
    city || cityMatch ? 5 : 0,
  ].reduce((sum, score) => sum + score, 0));
  return {
    fields,
    missing,
    quality,
    text_length: normalized.length,
    preview: normalized.slice(0, 600),
  };
}

function applyImportedFields(result) {
  const f = result?.fields || {};
  const yearEl = document.getElementById('birth-year');
  const monthEl = document.getElementById('birth-month');
  const dayEl = document.getElementById('birth-day');
  if (f.year) yearEl.value = String(f.year);
  if (f.month) monthEl.value = String(f.month);
  if (f.year || f.month) monthEl.dispatchEvent(new Event('change'));
  if (f.day) dayEl.value = String(f.day);
  if (f.hour != null && f.minute != null) {
    document.getElementById('birth-time').value = `${String(f.hour).padStart(2, '0')}:${String(f.minute).padStart(2, '0')}`;
  }
  if (f.city) document.getElementById('birth-city').value = f.city;
  if (f.lat != null) document.getElementById('birth-lat').value = safeNumber(f.lat);
  if (f.lon != null) document.getElementById('birth-lon').value = safeNumber(f.lon);
  if (f.tz != null) document.getElementById('birth-tz').value = String(safeNumber(f.tz));
}

function renderImportResult(resultEl, result) {
  const missingHtml = result.missing.length
    ? `<p class="chart-import-warning">仍需手动补充：${escapeHtml(result.missing.join('、'))}</p>`
    : '<p class="chart-import-ok">已识别完整出生信息，可直接生成星盘。</p>';
  const f = result.fields || {};
  resultEl.innerHTML = `
    <div class="chart-import-result-card">
      <div class="chart-import-score"><strong>${escapeHtml(result.quality)}</strong><span>质量分</span></div>
      <div class="chart-import-fields">
        <span>日期：${escapeHtml([f.year, f.month, f.day].filter(Boolean).join('-') || '-')}</span>
        <span>时间：${escapeHtml(f.hour != null ? `${String(f.hour).padStart(2, '0')}:${String(f.minute).padStart(2, '0')}` : '-')}</span>
        <span>地点：${escapeHtml(f.city || '-')}</span>
        <span>坐标：${escapeHtml(f.lat != null && f.lon != null ? `${safeNumber(f.lat).toFixed(4)}, ${safeNumber(f.lon).toFixed(4)}` : '-')}</span>
        <span>时区：${escapeHtml(f.tz != null ? `UTC${f.tz >= 0 ? '+' : ''}${f.tz}` : '-')}</span>
      </div>
    </div>
    ${missingHtml}
  `;
}

async function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(reader.error || new Error('文件读取失败'));
    reader.readAsText(file);
  });
}

async function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(reader.error || new Error('文件读取失败'));
    reader.readAsDataURL(file);
  });
}

export function initChartImport() {
  const panel = document.getElementById('chart-import-panel');
  if (!panel || panel.dataset.bound) return;
  panel.dataset.bound = 'true';
  const textEl = document.getElementById('chart-import-text');
  const fileEl = document.getElementById('chart-import-file');
  const parseBtn = document.getElementById('chart-import-parse');
  const applyBtn = document.getElementById('chart-import-apply');
  const resultEl = document.getElementById('chart-import-result');
  let lastResult = null;

  async function parseCurrentInput() {
    resultEl.innerHTML = '<p>正在识别出生信息...</p>';
    let text = textEl.value || '';
    const file = fileEl.files?.[0];
    if (file) {
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        try {
          const dataUrl = await readFileAsDataUrl(file);
          const apiResult = await window.JyotishAPI?.importChart?.({
            filename: file.name,
            content_base64: dataUrl.split(',')[1],
          });
          text = apiResult?.text || '';
        } catch (error) {
          resultEl.innerHTML = `<p class="chart-import-warning">PDF文本抽取失败：${escapeHtml(error?.message || '本地 API 服务不可用')}。可复制PDF文字后粘贴到文本框。</p>`;
          return;
        }
      } else {
        text = await readFileAsText(file);
      }
    }
    lastResult = parseImportedChartText(text);
    renderImportResult(resultEl, lastResult);
    applyBtn.disabled = lastResult.quality < 50;
  }

  parseBtn.addEventListener('click', parseCurrentInput);
  applyBtn.addEventListener('click', () => {
    if (!lastResult) return;
    applyImportedFields(lastResult);
    resultEl.insertAdjacentHTML('beforeend', `<p class="chart-import-ok">已填入表单。${lastResult.missing.length ? '请补齐缺失字段后生成星盘。' : '可以生成星盘了。'}</p>`);
  });
  fileEl.addEventListener('change', () => {
    if (fileEl.files?.[0]) {
      textEl.value = '';
      resultEl.innerHTML = `<p>已选择：${escapeHtml(fileEl.files[0].name)}</p>`;
    }
  });
}
