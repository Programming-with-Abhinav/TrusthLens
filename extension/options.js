document.addEventListener("DOMContentLoaded", () => {
  const urlInput = document.getElementById("backend-url");
  const tokenInput = document.getElementById("auth-token");
  const saveBtn = document.getElementById("save-btn");
  const statusDiv = document.getElementById("status");

  // Load existing settings
  chrome.storage.sync.get({
    backend_url: "http://localhost:5500",
    auth_token: ""
  }, (items) => {
    const backendUrl = items.backend_url === "http://localhost:8000"
      ? "http://localhost:5500"
      : items.backend_url;
    urlInput.value = backendUrl;
    tokenInput.value = items.auth_token;
    if (backendUrl !== items.backend_url) {
      chrome.storage.sync.set({ backend_url: backendUrl });
    }
  });

  saveBtn.addEventListener("click", () => {
    const rawUrl = urlInput.value.trim() || "http://localhost:5500";
    const cleanUrl = rawUrl.replace(/\/+$/, "");
    const token = tokenInput.value.trim();

    chrome.storage.sync.set({
      backend_url: cleanUrl,
      auth_token: token
    }, () => {
      statusDiv.textContent = "✓ Settings saved successfully!";
      setTimeout(() => {
        statusDiv.textContent = "";
      }, 2500);
    });
  });
});
