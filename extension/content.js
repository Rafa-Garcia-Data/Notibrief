document.addEventListener("contextmenu", (e) => {
  let el = e.target;
  let best = null;
  let bestLen = 0;

  while (el && el !== document.body) {
    const text = (el.innerText || "").trim();
    if (text.length > bestLen) {
      bestLen = text.length;
      best = el;
    }
    if (text.length > 500) break;
    el = el.parentElement;
  }

  const container = best && bestLen > 30 ? best : null;
  if (!container) {
    window.__notibrief_target = null;
    return;
  }

  const imgs = Array.from(container.querySelectorAll("img"))
    .filter(img => {
      const w = img.naturalWidth || img.width || parseInt(img.getAttribute("width")) || 0;
      const h = img.naturalHeight || img.height || parseInt(img.getAttribute("height")) || 0;
      const src = img.src || img.dataset.src || "";
      if (w > 0 && w < 100 && h > 0 && h < 100) return false;
      if (src.startsWith("data:")) return false;
      if (src.includes("emotion") || src.includes("reaction")) return false;
      return src.startsWith("http");
    })
    .map(img => ({
      src: img.src || img.dataset.src || "",
      alt: img.alt || ""
    }));

  window.__notibrief_target = { container, images: imgs };
}, true);
