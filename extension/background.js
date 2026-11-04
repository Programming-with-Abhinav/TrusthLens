// TrustLens AI - Background Service Worker (Chrome MV3)
// Implements: Active navigation protection, interstitial trigger (FR-U8), and tab status cache.

chrome.runtime.onInstalled.addListener(() => {
  console.log("TrustLens AI Service Worker installed.");
});

// Message listener for scanning active tab and handling navigation blocks
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "check_url_safety" && message.url) {
    chrome.storage.sync.get({
      backend_url: "http://localhost:5500",
      auth_token: ""
    }, async (settings) => {
      if (settings.backend_url === "http://localhost:8000") {
        settings.backend_url = "http://localhost:5500";
        chrome.storage.sync.set({ backend_url: settings.backend_url });
      }
      try {
        const headers = { "Content-Type": "application/json" };
        if (settings.auth_token) {
          headers["Authorization"] = `Bearer ${settings.auth_token}`;
        }
        const resp = await fetch(`${settings.backend_url}/api/scan`, {
          method: "POST",
          headers,
          body: JSON.stringify({ url: message.url })
        });
        if (resp.ok) {
          const data = await resp.json();
          // If critical risk or should_block is true, redirect tab to interstitial
          if (data.should_block && sender.tab && sender.tab.id) {
            const interstitialUrl = chrome.runtime.getURL(`interstitial.html?url=${encodeURIComponent(message.url)}`);
            chrome.tabs.update(sender.tab.id, { url: interstitialUrl });
          }
          sendResponse({ success: true, scan: data });
        } else {
          sendResponse({ success: false });
        }
      } catch (err) {
        sendResponse({ success: false, error: err.message });
      }
    });
    return true; // Keep message channel open for async response
  }
});
