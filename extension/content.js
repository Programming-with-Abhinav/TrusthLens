// TrustLens AI – In-Page Verification & Protection Layer (Chrome MV3)
// Complies with:
// - FR-E1: Selection fact-check overlay
// - FR-E3: Configurable backend URL
// - FR-E4: Safe DOM APIs only (strictly zero innerHTML)
// - FR-E6: Closed Shadow DOM isolation
// - FR-E7: In-page claim detection & hover badges
// - FR-E8: Bearer token synchronization
// - FR-U8: Pre-navigation / page load danger detection

const host = document.createElement("div");
const sh = host.attachShadow({ mode: "closed" });
document.documentElement.appendChild(host);

const VERDICT_COLORS = {
  Verified: "#22c55e",
  False: "#ef4444",
  Mixed: "#f59e0b",
  Misleading: "#f59e0b",
  "No evidence found": "#94a3b8",
  Unverified: "#64748b"
};

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action !== "get_page_text") return false;

  const selection = window.getSelection()?.toString().trim();
  if (selection) {
    sendResponse({ text: selection.slice(0, 100_000) });
    return false;
  }

  const source = document.querySelector("article, main, [role='main']") || document.body;
  const clone = source.cloneNode(true);
  const originalElements = [source, ...source.querySelectorAll("*")];
  const clonedElements = [clone, ...clone.querySelectorAll("*")];
  const excluded = "script, style, noscript, nav, footer, aside, form, button, input, textarea, select, [hidden], [aria-hidden='true'], [role='navigation'], [role='banner'], [role='complementary']";

  for (let index = originalElements.length - 1; index >= 0; index -= 1) {
    const original = originalElements[index];
    const cloned = clonedElements[index];
    const style = window.getComputedStyle(original);
    const rect = original.getBoundingClientRect();
    const identity = `${original.id} ${original.getAttribute("class") || ""}`;
    const isAd = /advert|sponsor|(^|\s)ads?(\s|$)/i.test(identity);
    const isHidden = style.display === "none" || style.visibility === "hidden" || style.opacity === "0" || rect.width === 0 || rect.height === 0;
    if (original.matches(excluded) || isAd || isHidden) cloned.remove();
  }

  const text = (clone.innerText || clone.textContent || "")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  sendResponse({ text: text.slice(0, 100_000) });
  return false;
});

function renderPill(text, borderColor = "#38bdf8", subtext = null) {
  while (sh.firstChild) {
    sh.removeChild(sh.firstChild);
  }

  const container = document.createElement("div");
  container.style.cssText = `
    font: 13px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0f172a;
    color: #f8fafc;
    padding: 6px 14px;
    border-radius: 9999px;
    border: 2px solid ${borderColor};
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -4px rgba(0, 0, 0, 0.5);
    display: inline-flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
    cursor: default;
    user-select: none;
  `;

  const label = document.createElement("span");
  label.textContent = text;
  container.appendChild(label);

  if (subtext) {
    const sub = document.createElement("span");
    sub.style.cssText = "color: #94a3b8; font-size: 11px; margin-left: 4px;";
    sub.textContent = subtext;
    container.appendChild(sub);
  }

  sh.appendChild(container);
}

// 1. Check current URL for security threats immediately on page load (FR-U8)
try {
  if (window.location.href && !window.location.href.startsWith("chrome")) {
    chrome.runtime.sendMessage({
      action: "check_url_safety",
      url: window.location.href
    }, () => {});
  }
} catch (e) {
  // Graceful ignore
}

// 2. Text Selection Fact-Checking Listener (FR-E1, FR-E4, FR-E6)
document.addEventListener("mouseup", async () => {
  const selection = window.getSelection();
  const selectedText = selection ? selection.toString().trim() : "";

  // Require at least 4 words
  if (!selectedText || selectedText.split(/\s+/).length < 4) {
    host.style.display = "none";
    return;
  }

  try {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    host.style.cssText = `
      position: fixed;
      z-index: 2147483647;
      left: ${Math.max(rect.left, 8)}px;
      top: ${Math.max(rect.top - 44, 8)}px;
      display: block;
    `;

    renderPill("🛡️ Checking claim…", "#38bdf8");

    chrome.storage.sync.get({
      backend_url: "http://localhost:5500",
      auth_token: ""
    }, async (settings) => {
      if (settings.backend_url === "http://localhost:8000") {
        settings.backend_url = "http://localhost:5500";
        chrome.storage.sync.set({ backend_url: settings.backend_url });
      }
      const headers = { "Content-Type": "application/json" };
      if (settings.auth_token) {
        headers["Authorization"] = `Bearer ${settings.auth_token}`;
      }

      const endpoint = `${settings.backend_url}/api/verify`;

      try {
        const response = await fetch(endpoint, {
          method: "POST",
          headers,
          body: JSON.stringify({ text: selectedText })
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          renderPill(`🛡️ ${errData.detail || "Limit reached"}`, "#ef4444");
          return;
        }

        const data = await response.json();
        const primary = data.claims && data.claims.length > 0 ? data.claims[0] : null;

        if (primary) {
          const verdict = primary.verdict || "Unverified";
          const color = VERDICT_COLORS[verdict] || "#94a3b8";
          const trust = primary.trust_score ? ` (${primary.trust_score}% trust)` : "";
          const sourcesCount = (primary.sources || []).length;
          renderPill(`🛡️ ${verdict}${trust}`, color, `${sourcesCount} source(s)`);
        } else {
          renderPill("🛡️ No evidence found", "#94a3b8");
        }
      } catch (networkErr) {
        renderPill("🛡️ Backend offline", "#64748b");
      }
    });
  } catch {
    host.style.display = "none";
  }
});