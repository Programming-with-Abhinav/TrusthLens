const host = window.location.hostname || 'localhost';
const API_BASE = (window.location.protocol.startsWith('http') && window.location.port === '8000') ? '' : `http://${host}:8000`;
const $ = id => document.getElementById(id), chip = v => `<span class="chip ${v}">${v}</span>`;

async function post(p, b) {
    const res = await fetch(`${API_BASE}/api/${p}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(b)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

async function verify() {
    $('r1').innerHTML = '<p class=mu>Checking…</p>';
    try {
        const d = await post('verify', { text: $('t').value });
        $('r1').innerHTML = d.claims.map(c => `<div class=item>${chip(c.verdict)} ${c.cached ? '<small>(cached)</small>' : ''}<p>${c.claim}</p>
${c.sources.map(s => `<small>${s.publisher || ''}: <a href="${s.url}" target=_blank>${s.title || s.rating}</a></small><br>`).join('') || '<small>No fact-checks found.</small>'}</div>`).join('');
        load();
    } catch (e) {
        $('r1').innerHTML = `<p class=mu style="color:#ef4444">⚠️ Backend offline or error. Start uvicorn: <code>.venv\\Scripts\\uvicorn.exe main:app --reload --port 8000</code></p>`;
    }
}

async function scan() {
    $('r2').innerHTML = '<p class=mu>Scanning…</p>';
    try {
        const d = await post('scan', { url: $('u').value });
        $('r2').innerHTML = `<div class=item>${chip(d.level)} <small>${d.source}</small>
<p>${[...d.threats, ...d.flags].map(f => '• ' + f).join('<br>') || 'No threats detected.'}</p></div>`;
        load();
    } catch (e) {
        $('r2').innerHTML = `<p class=mu style="color:#ef4444">⚠️ Backend offline or error. Start uvicorn: <code>.venv\\Scripts\\uvicorn.exe main:app --reload --port 8000</code></p>`;
    }
}

async function load() {
    try {
        const res = await fetch(`${API_BASE}/api/history`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const h = await res.json();
        $('h').innerHTML = h.map(x => `<div class=item><small>${x.type}</small> ${x.input} ${x.result.map(chip).join(' ')}</div>`).join('') || '<small>Nothing yet.</small>';
    } catch (e) {
        $('h').innerHTML = '<small class=mu>Backend offline (in-memory history unavailable).</small>';
    }
}

async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/api/health`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const d = await res.json();
        $('mode').textContent = d.mode === 'live' ? '🟢 Live Google APIs' : '🟡 Demo mode (no API key)';
        load();
    } catch (e) {
        $('mode').textContent = '🔴 Backend offline (run uvicorn)';
        $('h').innerHTML = '<small class=mu>Backend is not running. Start the server with uvicorn on port 8000.</small>';
    }
}

checkHealth();
