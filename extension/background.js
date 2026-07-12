const SERVER = "http://localhost:8787";

function setupContextMenu() {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: "notibrief-capture",
      title: "Enviar a Notibrief",
      contexts: ["page"],
      documentUrlPatterns: ["https://www.linkedin.com/*"],
    });
  });
}

chrome.runtime.onInstalled.addListener(setupContextMenu);
chrome.runtime.onStartup.addListener(setupContextMenu);

function extractPost() {
  const target = window.__notibrief_target;
  if (!target || !target.container) return null;

  const fullText = (target.container.innerText || "").trim();
  if (fullText.length < 30) return null;

  const lines = fullText.split("\n").map(l => l.trim()).filter(l => l.length > 15);
  let bestBlock = "";
  let current = "";
  for (const line of lines) {
    if (line.length < 25 && current.length > 100) {
      if (current.length > bestBlock.length) bestBlock = current;
      current = "";
    } else {
      current += (current ? " " : "") + line;
    }
  }
  if (current.length > bestBlock.length) bestBlock = current;

  const text = bestBlock.length > 50 ? bestBlock.substring(0, 5000) : fullText.substring(0, 5000);

  const images = (target.images || []).slice(0, 10);

  const urn = target.container.getAttribute("data-urn") ||
    target.container.closest("[data-urn]")?.getAttribute("data-urn") || "";
  const url = window.location.href.split("?")[0] + (urn ? "#" + urn : "#" + Date.now());

  return { url, text, images, captured_at: new Date().toISOString() };
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (!tab?.id) return;

  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractPost,
    });

    const data = results?.[0]?.result;
    if (!data) {
      console.error("[Notibrief] No se pudo extraer el post");
      return;
    }

    console.log("[Notibrief] URL:", data.url);
    console.log("[Notibrief] Texto:", data.text.substring(0, 150));
    console.log("[Notibrief] Imagenes:", data.images.length);

    const resp = await fetch(`${SERVER}/api/capture`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const result = await resp.json();
    console.log("[Notibrief] OK:", result);
  } catch (e) {
    console.error("[Notibrief] Error:", e.message);
  }
});
