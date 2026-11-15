// First-party accessibility audit helpers for the test harness (WCAG 2.2 AA oriented).
// They run inside real Chrome against the real app loaded in a same-origin iframe, using
// computed styles and layout. They are automated checks only: they do not replace a
// screen-reader or manual review.

/** Load the app (or any same-origin page) in an iframe of the given size. */
export async function loadPage(url, { width = 1280, height = 900, theme = null } = {}) {
  const frame = document.createElement("iframe");
  frame.style.cssText = `width:${width}px;height:${height}px;border:0;position:absolute;left:-10000px;top:0`;
  frame.src = url;
  document.body.appendChild(frame);
  await new Promise((resolve, reject) => {
    frame.addEventListener("load", resolve, { once: true });
    setTimeout(() => reject(new Error(`timeout loading ${url}`)), 15000);
  });
  const doc = frame.contentDocument;
  await waitFor(() => doc.querySelector("#main h1") && !doc.querySelector("#main .spinner"), 10000, `render ${url}`);
  if (theme) doc.documentElement.dataset.theme = theme;
  await new Promise((r) => setTimeout(r, 150));
  return { frame, doc, win: frame.contentWindow, close: () => frame.remove() };
}

export async function waitFor(fn, ms = 5000, what = "condition") {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    if (fn()) return true;
    await new Promise((r) => setTimeout(r, 50));
  }
  throw new Error(`timeout waiting for ${what}`);
}

// ---------- colour ----------
function parse(c) {
  const m = String(c).match(/rgba?\(([^)]+)\)/);
  if (!m) return null;
  const [r, g, b, a = "1"] = m[1].split(/[ ,/]+/).filter(Boolean);
  return { r: +r, g: +g, b: +b, a: parseFloat(a) };
}
function lum({ r, g, b }) {
  const f = (v) => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
export function ratio(a, b) {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}
function over(top, under) {
  const a = top.a;
  return { r: top.r * a + under.r * (1 - a), g: top.g * a + under.g * (1 - a), b: top.b * a + under.b * (1 - a), a: 1 };
}

/**
 * Background colours behind an element: solid layers are composited from the root; a
 * gradient contributes each of its colour stops (the worst stop is used).
 */
export function backgrounds(el, win) {
  const chain = [];
  for (let n = el; n && n.nodeType === 1; n = n.parentElement) chain.unshift(n);
  let bases = [{ r: 255, g: 255, b: 255, a: 1 }];
  for (const n of chain) {
    const s = win.getComputedStyle(n);
    const img = s.backgroundImage;
    if (img && img.includes("gradient")) {
      const stops = (img.match(/rgba?\([^)]+\)/g) || []).map(parse).filter(Boolean);
      if (stops.length) bases = stops.flatMap((stop) => bases.map((b) => over(stop, b)));
    }
    const c = parse(s.backgroundColor);
    if (c && c.a > 0) bases = bases.map((b) => over(c, b));
  }
  return bases;
}

/** Visible elements that directly contain text. */
export function textElements(doc, win) {
  const out = [];
  const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  for (let t = walker.nextNode(); t; t = walker.nextNode()) {
    const el = t.parentElement;
    if (!el || seen.has(el) || !t.textContent.trim()) continue;
    seen.add(el);
    if (el.closest("[aria-hidden=true], .sr-only, script, style, svg")) continue;
    const r = el.getBoundingClientRect();
    const s = win.getComputedStyle(el);
    if (r.width === 0 || r.height === 0 || s.visibility === "hidden" || parseFloat(s.opacity) === 0) continue;
    out.push(el);
  }
  return out;
}

/** WCAG 1.4.3: text contrast >= 4.5:1, or 3:1 for large text (>= 24px, or >= 18.66px bold). */
export function contrastFailures(doc, win) {
  const fails = [];
  for (const el of textElements(doc, win)) {
    const s = win.getComputedStyle(el);
    const fg = parse(s.color);
    if (!fg) continue;
    const size = parseFloat(s.fontSize);
    const bold = parseInt(s.fontWeight, 10) >= 700;
    const need = size >= 24 || (bold && size >= 18.66) ? 3 : 4.5;
    for (const bg of backgrounds(el, win)) {
      const got = ratio(fg.a < 1 ? over(fg, bg) : fg, bg);
      if (got + 1e-6 < need) {
        fails.push(`${describe(el)} "${el.textContent.trim().slice(0, 30)}" ${got.toFixed(2)}:1 < ${need}`);
        break;
      }
    }
  }
  return fails;
}

/** WCAG 1.4.11: form-control boundaries >= 3:1 against what surrounds them. */
export function controlBorderFailures(doc, win) {
  const fails = [];
  for (const el of doc.querySelectorAll("input[type=search], select, textarea")) {
    if (!el.getClientRects().length) continue;
    const s = win.getComputedStyle(el);
    const border = parse(s.borderTopColor);
    const outside = backgrounds(el.parentElement, win)[0];
    const inside = backgrounds(el, win)[0];
    const got = Math.max(ratio(border, outside), ratio(inside, outside));
    if (got < 3) fails.push(`${describe(el)} boundary ${got.toFixed(2)}:1 < 3`);
  }
  return fails;
}

/** WCAG 2.5.8: pointer targets at least 24x24 CSS px (inline links in text are exempt). */
export function targetSizeFailures(doc) {
  const fails = [];
  const targets = doc.querySelectorAll("button, select, summary, input[type=checkbox], input[type=search], textarea, .sidebar a, .btn");
  for (const el of targets) {
    if (!el.getClientRects().length) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 24 || r.height < 24) fails.push(`${describe(el)} ${Math.round(r.width)}x${Math.round(r.height)}`);
  }
  return fails;
}

/** Accessible name (simplified accname: aria-labelledby, aria-label, label, content, title). */
export function accessibleName(el) {
  const doc = el.ownerDocument;
  if (el.getAttribute("aria-labelledby")) {
    return el.getAttribute("aria-labelledby").split(/\s+/).map((id) => doc.getElementById(id)?.textContent || "").join(" ").trim();
  }
  if (el.getAttribute("aria-label")) return el.getAttribute("aria-label").trim();
  if (el.id) {
    const l = doc.querySelector(`label[for="${CSS.escape(el.id)}"]`);
    if (l) return l.textContent.trim();
  }
  const wrap = el.closest("label");
  if (wrap) return wrap.textContent.trim();
  if (["BUTTON", "A", "SUMMARY"].includes(el.tagName)) {
    const clone = el.cloneNode(true);
    clone.querySelectorAll("[aria-hidden=true]").forEach((n) => n.remove());
    const t = clone.textContent.trim();
    if (t) return t;
  }
  return (el.getAttribute("title") || "").trim();
}

export function unnamedControls(doc) {
  return [...doc.querySelectorAll("button, a[href], input, select, textarea, summary, [role=region], [tabindex='0']")]
    .filter((el) => el.getClientRects().length || el.matches("[role=region]"))
    .filter((el) => !accessibleName(el))
    .map(describe);
}

/** Visible text outside any landmark (WCAG 1.3.1 / best practice "region"). */
export function textOutsideLandmarks(doc, win) {
  const landmark = "header, nav, main, aside, footer, [role=banner], [role=navigation], [role=main], [role=complementary], [role=contentinfo], [role=region][aria-label], [role=region][aria-labelledby], [role=alert], [role=status]";
  return textElements(doc, win)
    .filter((el) => !el.closest(landmark) && !el.matches(".skip-link")) // a skip link conventionally precedes all landmarks
    .map((el) => `${describe(el)} "${el.textContent.trim().slice(0, 30)}"`);
}

/** Exactly one h1, and heading levels never skip downwards (WCAG 1.3.1, 2.4.6). */
export function headingProblems(doc) {
  const hs = [...doc.querySelectorAll("h1, h2, h3, h4, h5, h6")].filter((h) => h.getClientRects().length);
  const problems = [];
  const h1s = hs.filter((h) => h.tagName === "H1").length;
  if (h1s !== 1) problems.push(`${h1s} h1 elements`);
  let prev = 0;
  for (const h of hs) {
    const lvl = +h.tagName[1];
    if (prev && lvl > prev + 1) problems.push(`h${prev} -> h${lvl} ("${h.textContent.trim().slice(0, 30)}")`);
    prev = lvl;
  }
  return problems;
}

export function duplicateIds(doc) {
  const counts = {};
  doc.querySelectorAll("[id]").forEach((el) => (counts[el.id] = (counts[el.id] || 0) + 1));
  return Object.entries(counts).filter(([, n]) => n > 1).map(([id, n]) => `${id} x${n}`);
}

export function describe(el) {
  const cls = typeof el.className === "string" && el.className ? "." + el.className.trim().split(/\s+/).slice(0, 2).join(".") : "";
  return `${el.tagName.toLowerCase()}${el.id ? "#" + el.id : ""}${cls}`;
}
