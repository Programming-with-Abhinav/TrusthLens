const host = window.location.hostname || 'localhost';
// Live Server and FastAPI are separate services; the API always runs on 5500.
const API_BASE = `http://${host}:5500`;
const $ = id => document.getElementById(id), chip = v => `<span class="chip ${v}">${v}</span>`;
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[character]));

function sourceHref(value) {
    try {
        const url = new URL(value, window.location.origin);
        return ['http:', 'https:'].includes(url.protocol) ? escapeHtml(url.href) : '#';
    } catch {
        return '#';
    }
}

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
        $('r1').innerHTML = d.claims.map(c => {
            const correction = ['False', 'Misleading'].includes(c.verdict) && c.synthesis
                ? `<div class="correction"><strong>What the fact-check found</strong><p>${escapeHtml(c.synthesis)}</p></div>`
                : '';
            const sources = c.sources.map(s => `<small>${escapeHtml(s.publisher || '')}: <a href="${sourceHref(s.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(s.title || s.rating)}</a></small><br>`).join('') || '<small>No fact-checks found.</small>';
            return `<div class="item">${chip(escapeHtml(c.verdict))} ${c.cached ? '<small>(cached)</small>' : ''}<p>${escapeHtml(c.claim)}</p>${correction}${sources}</div>`;
        }).join('');
        load();
    } catch (e) {
        $('r1').innerHTML = `<p class=mu style="color:#ef4444">⚠️ Backend offline or error. Start uvicorn: <code>.venv\\Scripts\\uvicorn.exe main:app --reload --port 5500</code></p>`;
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
        $('r2').innerHTML = `<p class=mu style="color:#ef4444">⚠️ Backend offline or error. Start uvicorn: <code>.venv\\Scripts\\uvicorn.exe main:app --reload --port 5500</code></p>`;
    }
}

async function summarize() {
    const output = $('r3');
    const text = $('summary-text').value.trim();
    if (!text) {
        output.innerHTML = '<p class="notice notice-error">Paste page text to summarize.</p>';
        $('summary-text').focus();
        return;
    }

    const button = $('summarize-form').querySelector('button[type="submit"]');
    button.disabled = true;
    output.innerHTML = '<p class="mu">Summarizing page text…</p>';
    try {
        const data = await post('summarize', {
            text,
            url: $('summary-url').value.trim() || undefined,
            length: $('summary-length').value
        });
        const keyPoints = (data.key_points || []).map(point => `<li>${escapeHtml(point)}</li>`).join('');
        const sectionSummaries = (data.section_summaries || []).map(section => {
            const additionalPoints = (section.key_points || []).filter(point => point !== section.summary);
            const points = additionalPoints.length
                ? `<ul>${additionalPoints.map(point => `<li>${escapeHtml(point)}</li>`).join('')}</ul>`
                : '';
            return `<section class="summary-section"><strong>${escapeHtml(section.title)}</strong><p>${escapeHtml(section.summary)}</p>${points}</section>`;
        }).join('');
        const original = data.url
            ? `<a href="${sourceHref(data.url)}" target="_blank" rel="noopener noreferrer">Open original page</a>`
            : '';
        const truncated = data.truncated
            ? '<p class="summary-note">The input exceeded the processing limit; only its first 50,000 characters were summarized.</p>'
            : '';
        output.innerHTML = `<div class="summary-result"><div class="summary-result-heading"><strong>Summary may omit details</strong><span class="chip Unverified">${escapeHtml(data.source)}</span></div><p>${escapeHtml(data.summary)}</p><strong class="summary-points-heading">Key points</strong><ul>${keyPoints}</ul>${sectionSummaries ? `<strong class="summary-points-heading">By section</strong>${sectionSummaries}` : ''}${truncated}<div class="summary-result-footer">${original}<button class="copy-button" id="copy-summary" type="button">Copy summary</button></div></div>`;
        $('copy-summary').addEventListener('click', async event => {
            const copyButton = event.currentTarget;
            try {
                await navigator.clipboard.writeText(data.summary);
                copyButton.textContent = 'Copied';
            } catch {
                copyButton.textContent = 'Copy unavailable';
            }
        });
        load();
    } catch (error) {
        output.innerHTML = `<p class="notice notice-error">${escapeHtml(error.message || 'Unable to summarize this text.')}</p>`;
    } finally {
        button.disabled = false;
    }
}

async function load() {
    $('h').innerHTML = '<small class=mu>No browsing or claim history is stored.</small>';
}

async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/api/health`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const d = await res.json();
        $('mode').textContent = d.mode === 'live' ? '🟢 Google Fact Check enabled' : '🟡 Demo mode (no Fact Check key)';
        load();
    } catch (e) {
        $('mode').textContent = '🔴 Backend offline (run uvicorn)';
        $('h').innerHTML = '<small class=mu>No browsing or claim history is stored.</small>';
    }
}

$('summarize-form').addEventListener('submit', event => {
    event.preventDefault();
    summarize();
});

checkHealth();
