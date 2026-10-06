chrome.tabs.query({ active: true, currentWindow: true }, async ([tab]) => {
  document.getElementById("url").textContent = tab.url;
  try {
    const d = await (await fetch("http://localhost:8000/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url: tab.url })
    })).json();
    document.getElementById("out").innerHTML =
      `<span class="chip ${d.level}">${d.level}</span><div class="mu">${[...d.threats, ...d.flags].join("<br>") || "No threats detected."}</div>`;
  } catch { document.getElementById("out").textContent = "Backend offline (run uvicorn)."; }
});
