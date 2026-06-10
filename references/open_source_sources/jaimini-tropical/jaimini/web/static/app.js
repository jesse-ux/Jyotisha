'use strict';

// ===== DOM Refs =====
const form = document.getElementById('chart-form');
const dateInput = document.getElementById('input-date');
const timeInput = document.getElementById('input-time');
const tzSelect = document.getElementById('input-tz');
const latInput = document.getElementById('input-lat');
const lonInput = document.getElementById('input-lon');
const nameInput = document.getElementById('input-name');
const houseSelect = document.getElementById('input-house');
const calcBtn = document.getElementById('calc-btn');
const locateBtn = document.getElementById('locate-btn');
const locateStatus = document.getElementById('locate-status');
const resultsPanel = document.getElementById('results-panel');
const loadingOverlay = document.getElementById('loading-overlay');

// ===== State =====
let chartData = null;
let map = null;
let marker = null;

// ===== Init Date/Time to Now =====
function initDateTime() {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    const hh = String(now.getHours()).padStart(2, '0');
    const mi = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    dateInput.value = `${yyyy}-${mm}-${dd}`;
    timeInput.value = `${hh}:${mi}:${ss}`;
}

// ===== Geolocation =====
function locateUser() {
    if (!navigator.geolocation) {
        locateStatus.textContent = '浏览器不支持定位';
        return;
    }

    locateBtn.classList.add('locating');
    locateBtn.textContent = '📍 定位中...';
    locateStatus.textContent = '';

    navigator.geolocation.getCurrentPosition(
        function(pos) {
            const lat = pos.coords.latitude.toFixed(4);
            const lon = pos.coords.longitude.toFixed(4);
            latInput.value = lat;
            lonInput.value = lon;

            // Update map marker
            if (marker && map) {
                marker.setLatLng([lat, lon]);
                map.setView([lat, lon], 12);
            }

            // Auto-detect timezone
            const tzOffset = -pos.coords.longitude / 15; // rough estimate
            const tzRounded = Math.round(tzOffset * 4) / 4; // round to nearest 0.25h
            const tzStr = tzRounded >= 0
                ? `+${tzRounded}`.replace('.25',':15').replace('.5',':30').replace('.75',':45')
                : `-${Math.abs(tzRounded)}`.replace('.25',':15').replace('.5',':30').replace('.75',':45');

            // Try to find closest match in timezone dropdown
            for (const opt of tzSelect.options) {
                if (opt.value === tzStr) {
                    tzSelect.value = tzStr;
                    break;
                }
            }

            locateBtn.classList.remove('locating');
            locateBtn.textContent = '📍 已定位';
            locateStatus.textContent = `${lat}, ${lon}`;
            setTimeout(() => { locateBtn.textContent = '📍 获取当前位置'; }, 2000);
        },
        function(err) {
            locateBtn.classList.remove('locating');
            locateBtn.textContent = '📍 定位失败';
            locateStatus.textContent = '请手动输入或使用地图';
            setTimeout(() => { locateBtn.textContent = '📍 获取当前位置'; }, 3000);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
}

// ===== Planet names =====
const PLANET_CN = {
    Su: '太阳', Mo: '月亮', Ma: '火星', Me: '水星',
    Ju: '木星', Ve: '金星', Sa: '土星',
    Ra: '罗睺', Ke: '计都', Ur: '天王', Ne: '海王', Pl: '冥王'
};
const PLANET_ORDER = ['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke','Ur','Ne','Pl'];

// ===== Leaflet Map =====
function initMap() {
    if (typeof L === 'undefined') return;

    map = L.map('map', { zoomControl: true }).setView([39.907, 116.397], 4);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
        maxZoom: 18,
    }).addTo(map);

    marker = L.marker([39.907, 116.397], { draggable: true }).addTo(map);
    marker.on('dragend', updateCoordsFromMarker);

    map.on('click', function(e) {
        marker.setLatLng(e.latlng);
        updateCoordsFromMarker();
    });
}

function updateCoordsFromMarker() {
    const pos = marker.getLatLng();
    latInput.value = pos.lat.toFixed(4);
    lonInput.value = pos.lng.toFixed(4);
}

// ===== Form Submit =====
form.addEventListener('submit', async function(e) {
    e.preventDefault();
    await calculateChart();
});

async function calculateChart() {
    calcBtn.disabled = true;
    calcBtn.textContent = '计算中...';
    loadingOverlay.classList.add('visible');

    try {
        const payload = {
            date: dateInput.value,
            time: timeInput.value.length === 5 ? timeInput.value + ':00' : timeInput.value,
            tz: tzSelect.value,
            lat: latInput.value,
            lon: lonInput.value,
            name: nameInput.value || '',
            house_system: houseSelect.value,
        };

        const resp = await fetch('/api/chart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        const result = await resp.json();

        if (!result.success) {
            alert('计算错误: ' + (result.error || '未知错误'));
            return;
        }

        chartData = result.data;
        resultsPanel.style.display = 'block';
        renderAll();

    } catch (err) {
        alert('请求失败: ' + err.message);
    } finally {
        calcBtn.disabled = false;
        calcBtn.textContent = '计算星盘';
        loadingOverlay.classList.remove('visible');
    }
}

// ===== Tabs =====
document.addEventListener('click', function(e) {
    if (!e.target.classList.contains('tab')) return;
    const tabGroup = e.target.parentElement;
    const tabName = e.target.dataset.tab;

    tabGroup.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    e.target.classList.add('active');

    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    const panel = document.getElementById('tab-' + tabName);
    if (panel) panel.classList.add('active');
});

// ===== Render All =====
function renderAll() {
    if (!chartData) return;
    renderPanchanga(chartData.panchanga);
    renderPlanets(chartData.planets);
    renderHouses(chartData.houses);
    renderKarakas(chartData.karakas_7);
    renderDashas(chartData.dasha_years, chartData.chara_dasha);
    renderPadas(chartData.padas, chartData.upapada);
    renderLagnas(chartData.special_lagnas, chartData.ascendant);
    renderDivisions(chartData.divisions);
    renderArgala(chartData.argalas, chartData.lagna_rajayoga, chartData.karakamsa_rajayoga);
}

// ===== Panchanga =====
function renderPanchanga(p) {
    if (!p) return;
    const container = document.getElementById('panchanga-cards');
    container.innerHTML = [
        renderTithiCard(p.tithi),
        renderNakshatraCard(p.nakshatra),
        renderYogaCard(p.yoga),
        renderKaranaCard(p.karana),
        renderVaraCard(p.vara),
    ].join('');
}

function renderTithiCard(t) {
    if (!t) return '';
    const pct = (t.progress * 100).toFixed(1);
    const isShukla = t.paksha === 'Shukla';
    const cls = isShukla ? 'progress-shukla' : 'progress-krishna';
    const border = isShukla ? 'var(--accent-shukla)' : 'var(--accent-krishna)';
    return `<div class="panchanga-card" style="border-top:3px solid ${border}">
        <div class="card-icon">${isShukla ? '☀️' : '🌙'}</div>
        <div class="card-title">Tithi 月日</div>
        <div class="card-name">${t.name}</div>
        <div class="card-chinese">${t.paksha_chinese} ${t.name_chinese}</div>
        <div class="card-detail">第${t.number}月日 (${t.paksha_tithi}日)</div>
        <div class="progress-bar"><div class="progress-fill ${cls}" style="width:${pct}%"></div></div>
        <div class="card-detail">${pct}%</div>
    </div>`;
}

function renderNakshatraCard(n) {
    if (!n) return '';
    const pct = (n.progress * 100).toFixed(1);
    return `<div class="panchanga-card">
        <div class="card-icon">⭐</div>
        <div class="card-title">Nakshatra 星宿</div>
        <div class="card-name">${n.name}</div>
        <div class="card-chinese">${n.name_chinese} (${n.meaning})</div>
        <div class="card-detail">Pada ${n.pada}/4 · Lord: ${n.lord}</div>
        <div class="progress-bar"><div class="progress-fill progress-shukla" style="width:${pct}%"></div></div>
        <div class="card-detail">${pct}%</div>
    </div>`;
}

function renderYogaCard(y) {
    if (!y) return '';
    return `<div class="panchanga-card">
        <div class="card-icon">🔗</div>
        <div class="card-title">Yoga 合朔</div>
        <div class="card-name">${y.name}</div>
        <div class="card-chinese">${y.name_chinese}</div>
        <div class="card-detail">${y.meaning}</div>
    </div>`;
}

function renderKaranaCard(k) {
    if (!k) return '';
    return `<div class="panchanga-card">
        <div class="card-icon">🕐</div>
        <div class="card-title">Karana 半日</div>
        <div class="card-name">${k.name}</div>
        <div class="card-chinese">${k.name_chinese}</div>
        <div class="card-detail">${k.type} · 第${k.half}半</div>
    </div>`;
}

function renderVaraCard(v) {
    if (!v) return '';
    const icons = {0:'☀️',1:'🌙',2:'♂️',3:'☿',4:'♃',5:'♀',6:'♄'};
    return `<div class="panchanga-card">
        <div class="card-icon">${icons[v.index] || '📅'}</div>
        <div class="card-title">Vara 曜日</div>
        <div class="card-name">${v.name}</div>
        <div class="card-chinese">${v.name_chinese}</div>
        <div class="card-detail">${v.planet_chinese}</div>
    </div>`;
}

// ===== Planets =====
function renderPlanets(planets) {
    if (!planets) return;
    let html = `<thead><tr>
        <th>行星</th><th>黄经 (°)</th><th>星座</th><th>星内度数</th><th>速度 (°/d)</th><th>方向</th>
    </tr></thead><tbody>`;

    for (const p of PLANET_ORDER) {
        if (!planets[p]) continue;
        const pl = planets[p];
        html += `<tr>
            <td>${p} ${PLANET_CN[p]||''}</td>
            <td class="number-cell">${pl.lon.toFixed(4)}</td>
            <td>${pl.sign}</td>
            <td class="number-cell">${pl.sign_deg.toFixed(2)}°</td>
            <td class="number-cell">${(pl.speed||0).toFixed(4)}</td>
            <td class="${pl.retrograde?'retro':''}">${pl.retrograde?'R':'D'}</td>
        </tr>`;
    }
    document.getElementById('planet-table').innerHTML = html + '</tbody>';
}

// ===== Houses =====
function renderHouses(houses) {
    if (!houses) return;
    let html = `<thead><tr>
        <th>宫位</th><th>星座</th><th>宫头</th><th>星内度数</th><th>宫内行星</th>
    </tr></thead><tbody>`;

    for (const h of houses) {
        const planets = h.planets || [];
        const planetStr = planets.length ? planets.map(p => p + ' ' + (PLANET_CN[p]||'')).join(', ') : '—';
        html += `<tr>
            <td>H${h.house}</td>
            <td>${h.sign}</td>
            <td class="number-cell">${h.cusp.toFixed(4)}°</td>
            <td class="number-cell">${h.sign_deg.toFixed(2)}°</td>
            <td>${planetStr}</td>
        </tr>`;
    }
    document.getElementById('house-table').innerHTML = html + '</tbody>';
}

// ===== Karakas =====
function renderKarakas(karakas) {
    if (!karakas) return;
    let html = `<thead><tr>
        <th>序号</th><th>Karaka</th><th>全名</th><th>行星</th><th>星座内度</th><th>星座</th>
    </tr></thead><tbody>`;

    for (const k of karakas) {
        html += `<tr>
            <td>${k.rank}</td>
            <td style="color:var(--accent-gold);font-weight:700">${k.karaka}</td>
            <td>${k.karaka_full}</td>
            <td>${k.planet} ${PLANET_CN[k.planet]||''}</td>
            <td class="number-cell">${k.degree_in_sign.toFixed(4)}°</td>
            <td>${k.sign}</td>
        </tr>`;
    }
    document.getElementById('karaka-table').innerHTML = html + '</tbody>';
}

// ===== Dashas =====
function renderDashas(dashaYears, charaDasha) {
    // Dasha years grid
    if (dashaYears) {
        let grid = '';
        for (const d of dashaYears) {
            grid += `<div class="info-card">
                <div class="info-label">${d.sign_name}</div>
                <div class="info-value">${d.years} 年</div>
                <div class="info-sub">Lord: ${d.lord}</div>
            </div>`;
        }
        document.getElementById('dasha-years-grid').innerHTML = grid;
    }

    // Chara Dasha table
    if (charaDasha) {
        let html = `<thead><tr>
            <th>大运</th><th>Lord</th><th>年数</th><th>Antar (子运)</th>
        </tr></thead><tbody>`;
        for (const p of charaDasha) {
            const antars = (p.antar||[]).map(a => `${a.sign_name}(${a.lord}:${a.years.toFixed(2)}y)`).join(', ');
            html += `<tr>
                <td>${p.sign_name}</td>
                <td>${p.lord}</td>
                <td>${p.years.toFixed(2)}</td>
                <td style="font-size:0.75rem;color:var(--text-secondary)">${antars}</td>
            </tr>`;
        }
        document.getElementById('dasha-table').innerHTML = html + '</tbody>';
    }
}

// ===== Padas =====
function renderPadas(padas, upapada) {
    if (!padas) return;
    const order = ['1','2','3','4','5','6','7','8','9','10','11','12'];
    let html = `<thead><tr>
        <th>宫位</th><th>Pada</th><th>Arudha</th><th>星座</th><th>Lord</th>
    </tr></thead><tbody>`;

    for (const h of order) {
        const p = padas[h];
        if (!p) continue;
        html += `<tr>
            <td>H${h}</td>
            <td>${p.name||''}</td>
            <td>${p.sign_full||p.sign}</td>
            <td>${p.sign}</td>
            <td>${p.lord}</td>
        </tr>`;
    }

    if (upapada) {
        html += `<tr style="border-top:2px solid var(--accent-gold)">
            <td>H12</td>
            <td style="color:var(--accent-gold);font-weight:700">UL</td>
            <td>${upapada.sign_full}</td>
            <td>${upapada.sign}</td>
            <td>${upapada.lord}</td>
        </tr>`;
    }

    document.getElementById('pada-table').innerHTML = html + '</tbody>';
}

// ===== Special Lagnas =====
function renderLagnas(lagnas, asc) {
    if (!lagnas) return;
    let grid = '';

    // Ascendant
    if (asc) {
        grid += `<div class="info-card" style="border-left:3px solid var(--accent-gold)">
            <div class="info-label">Ascendant (上升)</div>
            <div class="info-value">${asc.sign} ${asc.sign_deg.toFixed(2)}°</div>
            <div class="info-sub">${asc.sign_str}</div>
        </div>`;
    }

    const order = ['HL', 'GL', 'VL'];
    const names = {HL:'Hora Lagna', GL:'Ghatika Lagna', VL:'Varnada Lagna'};
    for (const key of order) {
        const l = lagnas[key];
        if (!l || !l.sign_idx && l.sign_idx !== 0) {
            grid += `<div class="info-card">
                <div class="info-label">${key} — ${names[key]||key}</div>
                <div class="info-value">${typeof l === 'object' ? JSON.stringify(l) : l}</div>
            </div>`;
            continue;
        }
        grid += `<div class="info-card">
            <div class="info-label">${key} — ${names[key]||key}</div>
            <div class="info-value">${l.sign}</div>
            <div class="info-sub">Lord: ${l.lord||'—'}</div>
        </div>`;
    }
    document.getElementById('lagnas-grid').innerHTML = grid;
}

// ===== Divisions =====
function renderDivisions(divisions) {
    if (!divisions) return;

    if (divisions.D9) {
        let html = `<thead><tr><th>行星</th><th>D-9 Navamsa 星座</th></tr></thead><tbody>`;
        for (const [name, data] of Object.entries(divisions.D9)) {
            html += `<tr><td>${name}</td><td>${data.sign}</td></tr>`;
        }
        document.getElementById('d9-table').innerHTML = html + '</tbody>';
    }

    if (divisions.D3) {
        let html = `<thead><tr><th>行星</th><th>D-3 Drekkana 星座</th></tr></thead><tbody>`;
        for (const [name, data] of Object.entries(divisions.D3)) {
            html += `<tr><td>${name}</td><td>${data.sign}</td></tr>`;
        }
        document.getElementById('d3-table').innerHTML = html + '</tbody>';
    }
}

// ===== Argala =====
function renderArgala(argalas, lagnaRajayoga, karakamsaRajayoga) {
    if (!argalas) return;
    const order = ['1','2','3','4','5','6','7','8','9','10','11','12'];
    let html = `<thead><tr>
        <th>宫位</th><th>Argala</th><th>Virodhargala</th><th>净结果</th>
    </tr></thead><tbody>`;

    for (const h of order) {
        const a = argalas[h];
        if (!a) continue;
        html += `<tr>
            <td>H${h}</td>
            <td>${a.argala_count||0}</td>
            <td>${a.virodhargala_count||0}</td>
            <td>${a.net_result||'neutral'}</td>
        </tr>`;
    }

    document.getElementById('argala-table').innerHTML = html + '</tbody>';

    // Rajayoga
    if (lagnaRajayoga || karakamsaRajayoga) {
        let grid = '';
        if (lagnaRajayoga) {
            grid += `<div class="info-card" style="border-left:3px solid var(--accent-gold)">
                <div class="info-label">Lagna Argala Rajayoga</div>
                <div class="info-value">${lagnaRajayoga.type} (Level ${lagnaRajayoga.level})</div>
                <div class="info-sub">${lagnaRajayoga.desc}</div>
            </div>`;
        }
        if (karakamsaRajayoga) {
            const kr = karakamsaRajayoga;
            grid += `<div class="info-card" style="border-left:3px solid var(--accent-amber)">
                <div class="info-label">Karakamsa Rajayoga</div>
                <div class="info-value">${kr.is_rajayoga?'YES':'No'} (Level ${kr.yoga_level})</div>
                <div class="info-sub">AK: ${kr.ak_planet} · Karakamsa: ${kr.karakamsa_sign} · ${kr.description}</div>
            </div>`;
        }
        document.getElementById('rajayoga-info').innerHTML = grid;
    }
}

// ===== Export =====
function getExportFilename(ext) {
    if (!chartData) return `jaimini-export.${ext}`;
    const input = chartData.input || {};
    const date = (input.date || 'unknown').replace(/-/g, '');
    const name = (input.name || 'chart').replace(/[^a-zA-Z0-9一-鿿]/g, '_');
    return `jaimini-${name}-${date}.${ext}`;
}

function downloadBlob(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function exportJSON() {
    if (!chartData) return;
    // Add export timestamp
    const payload = Object.assign({}, chartData);
    payload.exported_at = new Date().toISOString();
    const json = JSON.stringify(payload, null, 2);
    downloadBlob(json, getExportFilename('json'), 'application/json');
}

function exportTXT() {
    if (!chartData) return;

    const d = chartData;
    const algo = d.algorithm || {};
    const inp = d.input || {};
    const asc = d.ascendant || {};

    const pcn = {Su:'太阳',Mo:'月亮',Ma:'火星',Me:'水星',Ju:'木星',Ve:'金星',Sa:'土星',Ra:'罗睺',Ke:'计都',Ur:'天王',Ne:'海王',Pl:'冥王'};
    const signCN = {Ari:'白羊',Tau:'金牛',Gem:'双子',Cnc:'巨蟹',Leo:'狮子',Vir:'处女',Lib:'天秤',Sco:'天蝎',Sgr:'射手',Cap:'摩羯',Aqr:'水瓶',Psc:'双鱼'};

    const lines = [];
    const sep = '='.repeat(68);
    const sub = '-'.repeat(62);
    const ssub = '·'.repeat(50);

    // ═══════════ HEADER ═══════════
    lines.push(sep);
    lines.push('  JAIMINI TROPICAL ASTROLOGY ENGINE — 完整星盘报告');
    lines.push(`  导出时间: ${new Date().toLocaleString('zh-CN')}`);
    lines.push(sep);
    lines.push('');

    // ═══════════ ALGORITHM ═══════════
    lines.push('一、【算法标注 — 本章节内容是解读的前提，务必先行阅读】');
    lines.push(sub);
    const algoLines = [
        ['引擎名称', algo.engine || 'Jaimini Tropical Astrology Engine'],
        ['版本号', algo.version || '1.0.0'],
        ['占星体系', algo.tradition || ''],
        ['黄道系统', algo.zodiac || ''],
        ['宫位系统', algo.house_system || ''],
        ['行星历表', algo.ephemeris || ''],
        ['主星系统', algo.karaka_system || ''],
        ['大运系统', algo.dasha_system || ''],
        ['映射系统', algo.pada_system || ''],
        ['分盘系统', algo.division_system || ''],
        ['障碍系统', algo.argala_system || ''],
    ];
    for (const [label, value] of algoLines) {
        lines.push(`  ${(label+':').padEnd(10)} ${value}`);
    }
    lines.push('');
    lines.push(`  ★ 重要声明: ${algo.note || ''}`);
    lines.push('');

    // ═══════════ INPUT ═══════════
    lines.push('二、【输入数据】');
    lines.push(sub);
    lines.push(`  出生日期 (UTC):  ${inp.date || ''}`);
    lines.push(`  出生时间 (UTC):  ${inp.time || ''}`);
    lines.push(`  本地时区:        UTC${(inp.tz||0)>=0?'+':''}${inp.tz||0}`);
    lines.push(`  纬度:            ${(inp.lat||0).toFixed(4)}°`);
    lines.push(`  经度:            ${(inp.lon||0).toFixed(4)}°`);
    lines.push(`  姓名/备注:       ${inp.name || '(未命名)'}`);
    lines.push(`  宫位制:          ${algo.house_system || inp.house_system || 'Whole Sign'}`);
    lines.push('');

    // ═══════════ ASCENDANT ═══════════
    if (asc.sign) {
        lines.push(`  上升点 (Asc):    ${asc.sign_full || asc.sign} ${(asc.sign_deg||0).toFixed(2)}°  [${signCN[asc.sign]||asc.sign}]`);
        lines.push('');
    }

    // ═══════════ PANCHANGA ═══════════
    const p = d.panchanga || {};
    if (p.tithi) {
        lines.push('三、【Panchanga 五支历法】');
        lines.push(sub);
        const t = p.tithi;
        lines.push(`  Tithi (月日)       ${t.name.padEnd(14)} ${t.paksha_chinese}·第${t.paksha_tithi}日  已过${(t.progress*100).toFixed(1)}%`);
        lines.push(`                     解释: 月日指示月亮相对于太阳的位置，管理每日吉凶`);
        const n = p.nakshatra;
        lines.push(`  Nakshatra (星宿)   ${n.name.padEnd(14)} 第${n.pada}/4足  Lord: ${n.lord} (${n.lord_full})  已过${(n.progress*100).toFixed(1)}%`);
        lines.push(`                     解释: ${n.name_chinese}(${n.meaning}), 27星宿之一，是月亮当晚所驻之星座`);
        const y = p.yoga;
        lines.push(`  Nitya Yoga (合朔)  ${y.name.padEnd(14)} ${y.name_chinese} — ${y.meaning}`);
        const k = p.karana;
        lines.push(`  Karana (半日)      ${k.name.padEnd(14)} ${k.name_chinese}  [${k.type}]  第${k.half}半`);
        const v = p.vara;
        lines.push(`  Vara (曜日)        ${v.name.padEnd(14)} ${v.name_chinese}  ${v.planet_chinese}`);
        lines.push('');
    }

    // ═══════════ PLANETS ═══════════
    if (d.planets) {
        lines.push('四、【行星位置 — 回归黄道】');
        lines.push(sub);
        const header = `  ${'行星'.padEnd(8)}${'符号'.padEnd(6)}${'黄经 °'.padEnd(13)}${'星座'.padEnd(8)}${'星宿(Nak)'.padEnd(14)}${'速度°/d'.padEnd(10)}${'方向'}`;
        lines.push(header);
        lines.push(`  ${'-'.repeat(62)}`);
        const order = ['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke','Ur','Ne','Pl'];
        for (const key of order) {
            const pl = d.planets[key];
            if (!pl) continue;
            const cn = pcn[key] || '';
            const retro = pl.retrograde ? 'R 逆行' : 'D 顺行';
            const degDMS = toDMS(pl.lon);
            lines.push(`  ${cn.padEnd(8)}${key.padEnd(6)}${degDMS.padEnd(13)}${(pl.sign+'').padEnd(8)}${''.padEnd(14)}${(pl.speed||0).toFixed(4).padEnd(10)}${retro}`);
        }
        lines.push('');
        lines.push(`  注: 黄经为回归黄道(Tropical/Sayana)经度，未做任何岁差修正`);
        lines.push('');
    }

    // ═══════════ HOUSES ═══════════
    if (d.houses) {
        lines.push('五、【宫位 — 整宫制 Whole Sign Houses】');
        lines.push(sub);
        const bhavaCN = {1:'命宫',2:'财帛',3:'兄弟',4:'田宅',5:'子女',6:'疾病',7:'夫妻',8:'死亡',9:'福德',10:'事业',11:'朋友',12:'损失'};
        for (const h of d.houses) {
            const pls = (h.planets||[]).map(p => p + ' ' + (pcn[p]||'')).join(', ') || '(空)';
            const bhava = bhavaCN[h.house] || '';
            lines.push(`  H${String(h.house).padStart(2)} ${bhava.padEnd(6)} | ${(h.sign+'').padEnd(5)} ${(signCN[h.sign]||'').padEnd(4)} | ${pls}`);
        }
        lines.push('');
    }

    // ═══════════ KARAKAS ═══════════
    if (d.karakas_7) {
        lines.push('六、【Chara Karaka — 七曜变格主星】');
        lines.push(sub);
        lines.push('  Jaimini 体系核心: 以行星在星座内的度数排序，度数最高者为灵魂主星(AK)。');
        lines.push('  此排序随出生时间而变，是 Jaimini 区别于 Parashara(固定主星)的标志。');
        lines.push('');
        for (const k of d.karakas_7) {
            lines.push(`  ${k.karaka.padEnd(4)} ${k.karaka_full.padEnd(20)} = ${k.planet} ${(pcn[k.planet]||'').padEnd(6)} | ${(k.sign+'').padEnd(5)} ${k.degree_in_sign.toFixed(4)}° °`);
        }
        lines.push('');
        lines.push('  Sthira Karaka (固定主星, 仅参考):');
        lines.push('    Su=父亲(PK)  Mo=母亲(MK)  Ma=兄弟(BK)  Me=事业(AmK)');
        lines.push('    Ju=财富(PK)  Ve=配偶(DK)  Sa=苦修(GK/DK)');
        lines.push('');
        lines.push('  ★ 解读提示: AK 代表灵魂方向, AmK 代表心智, BK 代表勇气, DK 代表婚姻。');
        lines.push('    每个 Karaka 的星座/宫位/分盘位置决定了该领域的吉凶。');
        lines.push('');
    }

    // ═══════════ DASHA ═══════════
    if (d.dasha_years) {
        lines.push('七、【Chara Dasha — Jaimini 大运系统】');
        lines.push(sub);
        lines.push('  计算方法: 以第9宫(Pitri Bhava)主星所在星座为起点，');
        lines.push('  Prakriti Chakra 序列(奇宫顺数/偶宫逆数)。');
        lines.push('');
        lines.push('  ── 12 星座大运年数 ──');
        for (const dy of d.dasha_years) {
            const bar = '█'.repeat(Math.max(1, Math.round(dy.years)));
            lines.push(`  ${dy.sign_name.padEnd(6)} Lord:${dy.lord.padEnd(4)} ${dy.years.toString().padStart(2)}年  ${bar}`);
        }
        lines.push('');
    }

    // Chara Dasha timeline
    if (d.chara_dasha && d.chara_dasha.length) {
        lines.push('  ── 大运时间线 (Mahadasha) ──');
        for (const md of d.chara_dasha) {
            lines.push(`  ${md.sign_name.padEnd(6)} ${md.lord}  ${md.years.toFixed(2)}年  |  Antar: ${(md.antar||[]).map(a => a.sign_name+'('+a.lord+'):'+a.years.toFixed(2)+'y').join('  ')}`);
        }
        lines.push('');
    }

    // ═══════════ PADAS ═══════════
    if (d.padas && d.padas['1']) {
        lines.push('八、【Arudha Padas — 映射点系统】');
        lines.push(sub);
        lines.push('  Arudha = 宫主星所在星座 + (宫主星所在星座 - 宫位星座)');
        lines.push('  若落在第1宫或第7宫，则移至第10宫(例外规则)。');
        lines.push('');
        lines.push('  全部 12 宫的 Arudha：');
        lines.push(`  ${'宫位'.padEnd(6)}${'Pada名称'.padEnd(10)}${'Arudha星座'.padEnd(14)}${'Lord'.padEnd(8)}`);
        lines.push(`  ${'-'.repeat(40)}`);
        const padaNames = {1:'AL (命)',2:'A2 (财)',3:'A3 (兄)',4:'A4 (田)',5:'A5 (子)',6:'A6 (病)',7:'A7 (妻)',8:'A8 (死)',9:'A9 (福)',10:'A10 (事)',11:'A11 (友)',12:'UL (姻)'};
        for (let hnum = 1; hnum <= 12; hnum++) {
            const pd = d.padas[String(hnum)];
            if (!pd) continue;
            lines.push(`  H${hnum.toString().padStart(2)}     ${(padaNames[hnum]||'').padEnd(10)} ${(pd.sign_full||pd.sign).padEnd(14)} ${(pd.lord||'').padEnd(8)}`);
        }
        lines.push('');
        // Upapada detail
        if (d.upapada) {
            lines.push(`  ★ Upapada (UL): ${d.upapada.sign_full}  Lord: ${d.upapada.lord}`);
            lines.push(`    ${d.upapada.description || ''}`);
        }
        lines.push('');
    }

    // ═══════════ SPECIAL LAGNAS ═══════════
    if (d.special_lagnas) {
        const sl = d.special_lagnas;
        const hasLagnas = (sl.HL && sl.HL.sign) || (sl.GL && sl.GL.sign) || (sl.VL && sl.VL.sign);
        if (hasLagnas) {
            lines.push('九、【特殊上升点 — Special Lagnas】');
            lines.push(sub);
            if (sl.HL && sl.HL.sign) {
                lines.push(`  Hora Lagna (HL):     ${sl.HL.sign_full || sl.HL.sign}   Lord: ${sl.HL.lord || ''}`);
                lines.push(`    解释: 每约1小时变化一次，代表财富和繁荣。用于财运判断。`);
            }
            if (sl.GL && sl.GL.sign) {
                lines.push(`  Ghatika Lagna (GL):  ${sl.GL.sign_full || sl.GL.sign}   Lord: ${sl.GL.lord || ''}`);
                lines.push(`    解释: 每约24分钟(Ghati)变化一次，代表权力和权威。用于政运判断。`);
            }
            if (sl.VL && sl.VL.sign) {
                lines.push(`  Varnada Lagna (VL):  ${sl.VL.sign_full || sl.VL.sign}   Lord: ${sl.VL.lord || ''}`);
                lines.push(`    解释: 由上升星座派生(asc_sign × 3 mod 12)，代表社会地位和阶层。`);
            }
            lines.push('');
        }
    }

    // ═══════════ DIVISIONS ═══════════
    if (d.divisions) {
        lines.push('十、【Jaimini 分盘 — Varga Divisions】');
        lines.push(sub);
        lines.push('  Jaimini 分盘遵循 "阳顺阴逆" 原则: 阳星座顺排/阴星座逆排。');
        lines.push('');

        // D-9 Navamsa
        if (d.divisions.D9) {
            lines.push('  ── D-9 Navamsa (九分盘, 配偶/内在自我) ──');
            lines.push('  每星座 9 等分 (3°20\' 每份)');
            for (const [name, dv] of Object.entries(d.divisions.D9)) {
                const label = name === 'Asc' ? '上升' : (pcn[name]||name);
                lines.push(`    ${label.padEnd(8)} → ${(dv.sign+'').padEnd(5)} ${signCN[dv.sign]||''}`);
            }
            lines.push('');
        }

        // D-3 Drekkana
        if (d.divisions.D3) {
            lines.push('  ── D-3 Drekkana (三分盘, 兄弟姐妹) ──');
            lines.push('  每星座 3 等分 (10° 每份), Parivrittitraya 三重旋转法');
            for (const [name, dv] of Object.entries(d.divisions.D3)) {
                const label = name === 'Asc' ? '上升' : (pcn[name]||name);
                lines.push(`    ${label.padEnd(8)} → ${(dv.sign+'').padEnd(5)} ${signCN[dv.sign]||''}`);
            }
            lines.push('');
        }

        // D-12 Dwadashamsha
        if (d.divisions.D12) {
            lines.push('  ── D-12 Dwadashamsha (十二分盘, 父母) ──');
            lines.push('  每星座 12 等分 (2°30\' 每份)');
            for (const [name, dv] of Object.entries(d.divisions.D12)) {
                const label = name === 'Asc' ? '上升' : (pcn[name]||name);
                lines.push(`    ${label.padEnd(8)} → ${(dv.sign+'').padEnd(5)} ${signCN[dv.sign]||''}`);
            }
            lines.push('');
        }
    }

    // ═══════════ ARGALA ═══════════
    if (d.argalas) {
        lines.push('十一、【Argala 障碍分析 — Jaimini 判断系统】');
        lines.push(sub);
        lines.push('  Primary Argala: 宫位 2、4、11 (从参考宫位起算)');
        lines.push('  Virodhargala (反障碍): 宫位 12、10、3 (分别阻碍 2、4、11)');
        lines.push('  Secondary Argala: 宫位 5、9');
        lines.push('');
        lines.push(`  ${'宫位'.padEnd(6)}${'Primary'.padEnd(20)}${'Virodhargala'.padEnd(20)}${'Secondary'.padEnd(16)}${'净结果'}`);
        lines.push(`  ${'-'.repeat(65)}`);
        const pLabels = {H2:'2', H4:'4', H11:'11'};
        const vLabels = {H12:'12', H10:'10', H3:'3'};
        const sLabels = {H5:'5', H9:'9'};
        for (let hnum = 1; hnum <= 12; hnum++) {
            const a = d.argalas[String(hnum)];
            if (!a) continue;
            const pri = Object.entries(a.primary||{}).map(([k,v]) => `${k}:${v.planet||'—'}`).join(' ') || '无';
            const vir = Object.entries(a.virodhargala||{}).map(([k,v]) => `${k}:${v.planet||'—'}`).join(' ') || '无';
            const sec = Object.entries(a.secondary||{}).map(([k,v]) => `${k}:${v.planet||'—'}`).join(' ') || '无';
            const net = {supported:'★ 吉', obstructed:'▼ 凶', neutral:'— 平'}[a.net_result] || a.net_result;
            lines.push(`  H${hnum.toString().padStart(2)}     ${pri.padEnd(20)}${vir.padEnd(20)}${sec.padEnd(16)}${net}`);
        }
        lines.push('');
    }

    // ═══════════ RAJAYOGA ═══════════
    if (d.lagna_rajayoga || d.karakamsa_rajayoga) {
        lines.push('十二、【Rajayoga — 王者瑜伽总结】');
        lines.push(sub);
        if (d.lagna_rajayoga) {
            const lr = d.lagna_rajayoga;
            const levels = {1:'Padargala (弱)', 2:'Ardhargala (中)', 3:'Tripadargala (强)', 4:'Poornargala (极强)'};
            lines.push(`  Lagna Argala Rajayoga:  ${lr.type} — ${levels[lr.level] || 'Level '+lr.level}`);
            lines.push(`    解读: H1的Argala意味着第2/4/11宫有行星占据，带来对命宫的支持。`);
            lines.push(`    Level ${lr.level}: ${lr.desc}`);
        }
        if (d.karakamsa_rajayoga) {
            const kr = d.karakamsa_rajayoga;
            lines.push(`  Karakamsa Rajayoga:     ${kr.is_rajayoga?'★ 存在王者瑜伽':'— 未形成'} (Level ${kr.yoga_level})`);
            lines.push(`    Atmakaraka: ${kr.ak_planet} | Karakamsa Sign: ${kr.karakamsa_sign}`);
            lines.push(`    解读: ${kr.description}`);
        }
        lines.push('');
    }

    // ═══════════ KARAKAMSA ═══════════
    lines.push('十三、【Jaimini 解读指引】');
    lines.push(sub);
    lines.push('  本报告基于纯 Jaimini 体系(Iranganti Rangacharya 方法):');
    lines.push('  1. 以 Chara Karaka(变格主星)为核心，7 行星按度排序取 AK~DK');
    lines.push('  2. 大运使用 Chara Dasha(Prakriti Chakra)，非 Vimshottari');
    lines.push('  3. 宫位使用整宫制(Whole Sign)，Rasi = Bhava');
    lines.push('  4. 映射点 Arudha Pada 用于判断世俗层面的表现');
    lines.push('  5. Argala 系统用于判断宫位间的支持与阻碍');
    lines.push('  6. D-9 Navamsa 用于判断内在自我、婚姻质量');
    lines.push('  7. 所有星体位置为回归黄道(Tropical)，非恒星黄道(Sidereal)');
    lines.push('');

    // ═══════════ FOOTER ═══════════
    lines.push(sep);
    lines.push(`  导出时间: ${new Date().toISOString()}`);
    lines.push(`  ★ 重要提醒: 若使用本报告数据与其他占星软件对比，请务必确认对方使用`);
    lines.push(`     相同的算法体系。纯 Jaimini 回归黄道的结果与 Parashara/恒星黄道/`);
    lines.push(`     Vimshottari Dasha 体系的结果完全不具可比性。混用体系必导致判读错误。`);
    lines.push(sep);

    downloadBlob(lines.join('\n'), getExportFilename('txt'), 'text/plain;charset=utf-8');
}

// Helper: decimal degrees → DMS string
function toDMS(deg) {
    const d = Math.floor(deg);
    const mf = (deg - d) * 60;
    const m = Math.floor(mf);
    const s = ((mf - m) * 60).toFixed(1);
    return `${d}°${String(m).padStart(2,'0')}'${String(s).padStart(4,'0')}"`;
}

// ===== Export Buttons =====
const exportJsonBtn = document.getElementById('export-json-btn');
const exportTxtBtn = document.getElementById('export-txt-btn');
if (exportJsonBtn) exportJsonBtn.addEventListener('click', exportJSON);
if (exportTxtBtn) exportTxtBtn.addEventListener('click', exportTXT);

// ===== Locate Button =====
if (locateBtn) {
    locateBtn.addEventListener('click', locateUser);
}

// ===== Init =====
document.addEventListener('DOMContentLoaded', function() {
    initDateTime();
    initMap();
});
