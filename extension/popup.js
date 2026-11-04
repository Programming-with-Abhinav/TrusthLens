// TrustLens AI – Extension Popup Script
// Complies with FR-E3, FR-E4 (safe DOM APIs), FR-E8

document.addEventListener("DOMContentLoaded", () => {
  const optionsLink = document.getElementById("open-options");
  if (optionsLink) {
    optionsLink.addEventListener("click", (e) => {
      e.preventDefault();
      if (chrome.runtime.openOptionsPage) {
        chrome.runtime.openOptionsPage();
      } else {
        window.open(chrome.runtime.getURL("options.html"));
      }
    });
  }

  chrome.tabs.query({ active: true, currentWindow: true }, async ([tab]) => {
    const urlContainer = document.getElementById("url");
    const outContainer = document.getElementById("out");

    if (!tab || !tab.url) {
      outContainer.textContent = "Unable to inspect active tab URL.";
      return;
    }

    urlContainer.textContent = tab.url;

    // Load backend URL and auth token from storage
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

      const summarizeButton = document.getElementById("summarize-page");
      const summaryOutput = document.getElementById("summary-output");
      summarizeButton.addEventListener("click", async () => {
        summarizeButton.disabled = true;
        summaryOutput.textContent = "Reading visible page text…";
        try {
          const pageContent = await new Promise((resolve, reject) => {
            chrome.tabs.sendMessage(tab.id, { action: "get_page_text" }, (response) => {
              if (chrome.runtime.lastError) {
                reject(new Error("This page does not allow text extraction."));
                return;
              }
              resolve(response?.text || "");
            });
          });
          if (!pageContent.trim()) throw new Error("No visible article text was found.");

          summaryOutput.textContent = "Creating a source-based summary…";
          const summaryResponse = await fetch(`${settings.backend_url}/api/summarize`, {
            method: "POST",
            headers,
            body: JSON.stringify({
              text: pageContent,
              url: tab.url,
              length: document.getElementById("summary-length").value
            })
          });
          const summaryData = await summaryResponse.json().catch(() => ({}));
          if (!summaryResponse.ok) throw new Error(summaryData.detail || `Summary failed (${summaryResponse.status})`);

          summaryOutput.replaceChildren();
          const sourceLabel = document.createElement("p");
          sourceLabel.className = "mu";
          sourceLabel.textContent = `${summaryData.source === "llm" ? "AI" : "Extractive"} summary; may omit details${summaryData.truncated ? " (input was truncated)" : ""}.`;
          summaryOutput.appendChild(sourceLabel);

          const summaryText = document.createElement("p");
          summaryText.className = "summary-text";
          summaryText.textContent = summaryData.summary;
          summaryOutput.appendChild(summaryText);

          const points = document.createElement("ul");
          (summaryData.key_points || []).forEach((point) => {
            const item = document.createElement("li");
            item.textContent = point;
            points.appendChild(item);
          });
          summaryOutput.appendChild(points);

          (summaryData.section_summaries || []).forEach((section) => {
            const sectionContainer = document.createElement("section");
            sectionContainer.className = "summary-section";
            const heading = document.createElement("strong");
            heading.textContent = section.title;
            sectionContainer.appendChild(heading);
            const sectionSummary = document.createElement("p");
            sectionSummary.textContent = section.summary;
            sectionContainer.appendChild(sectionSummary);
            summaryOutput.appendChild(sectionContainer);
          });

          const copyButton = document.createElement("button");
          copyButton.type = "button";
          copyButton.textContent = "Copy summary";
          copyButton.addEventListener("click", async () => {
            try {
              await navigator.clipboard.writeText(summaryData.summary);
              copyButton.textContent = "Copied";
            } catch {
              copyButton.textContent = "Copy unavailable";
            }
          });
          summaryOutput.appendChild(copyButton);
        } catch (error) {
          summaryOutput.textContent = error.message || "Unable to summarize this page.";
        } finally {
          summarizeButton.disabled = false;
        }
      });

      try {
        const response = await fetch(`${settings.backend_url}/api/scan`, {
          method: "POST",
          headers,
          body: JSON.stringify({ url: tab.url })
        });

        if (!response.ok) {
          const err = await response.json().catch(() => ({}));
          outContainer.textContent = err.detail || `Scan failed (${response.status})`;
          return;
        }

        const data = await response.json();

        // Render result safely without innerHTML (FR-E4)
        while (outContainer.firstChild) {
          outContainer.removeChild(outContainer.firstChild);
        }

        const badge = document.createElement("span");
        badge.className = `chip ${data.level || "Safe"}`;
        badge.textContent = data.level || "Safe";
        outContainer.appendChild(badge);

        const listContainer = document.createElement("div");
        listContainer.className = "mu";
        listContainer.style.marginTop = "8px";

        const items = [...(data.threats || []), ...(data.flags || [])];
        if (items.length === 0) {
          const itemElem = document.createElement("div");
          itemElem.textContent = "✓ No threats or deceptive heuristics detected.";
          itemElem.style.color = "#4ade80";
          listContainer.appendChild(itemElem);
        } else {
          items.forEach((itemText) => {
            const itemElem = document.createElement("div");
            itemElem.textContent = `• ${itemText}`;
            itemElem.style.marginBottom = "4px";
            listContainer.appendChild(itemElem);
          });
        }

        outContainer.appendChild(listContainer);
      } catch (err) {
        outContainer.textContent = "Backend offline. Check uvicorn server or Settings.";
      }
    });
  });
});