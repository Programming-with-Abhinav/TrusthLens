// Select text -> Shadow-DOM badge (no layout shift) -> backend -> verdict
const host = document.createElement("div");
const sh = host.attachShadow({ mode: "closed" });
document.documentElement.appendChild(host);
const col = { Verified: "#22c55e", False: "#ef4444", Mixed: "#f59e0b", Misleading: "#f59e0b", Unverified: "#64748b" };
const pill = (txt, c = "#334") => `<div style="font:13px system-ui;background:#131c2e;color:#fff;padding:6px 12px;border-radius:99px;border:2px solid ${c}">${txt}</div>`;
document.addEventListener("mouseup", async () => {
  const t = getSelection().toString().trim();
  if (t.split(" ").length < 4) { host.style.display = "none"; return; }
  const r = getSelection().getRangeAt(0).getBoundingClientRect();
  host.style.cssText = `position:fixed;z-index:2147483647;left:${r.left}px;top:${Math.max(r.top - 40, 4)}px`;
  sh.innerHTML = pill("🛡️ Checking…");
  try {
    const d = await (await fetch("http://localhost:8000/api/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: t }) })).json();
    const c = d.claims[0]; sh.innerHTML = pill(`🛡️ ${c.verdict} · ${c.sources.length} source(s)`, col[c.verdict]);
  } catch { sh.innerHTML = pill("Backend offline"); }
});
