// Dependency-free horizontal bar chart (inline SVG). Used only for values
// that model/compare.js has already judged compatible. No error bars are
// drawn: uncertainty is shown as text exactly as reported.

import { h } from "./dom.js";

const SVG = "http://www.w3.org/2000/svg";
function s(tag, attrs = {}, text) {
  const el = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  if (text !== undefined) el.textContent = text;
  return el;
}

/**
 * @param {{label: string, value: number, note?: string, fixture?: boolean}[]} rows
 * @param {{unit?: string|null, title: string}} opts
 */
export function barChart(rows, { unit, title }) {
  const max = Math.max(...rows.map((r) => r.value), 0) || 1;
  const rowH = 34;
  const labelW = 180;
  const width = 640;
  const plotW = width - labelW - 90;
  const height = rows.length * rowH + 10;

  const svg = s("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": `${title} by investigation, in ${unit || "reported units"}`, class: "bar-chart" });
  rows.forEach((r, i) => {
    const y = i * rowH + 6;
    const w = Math.max(2, (r.value / max) * plotW);
    svg.appendChild(s("text", { x: labelW - 8, y: y + 16, "text-anchor": "end", class: "bar-label" }, truncate(r.label, 26)));
    svg.appendChild(s("rect", { x: labelW, y, width: w, height: 22, rx: 3, class: r.fixture ? "bar bar-fixture" : "bar" }));
    svg.appendChild(s("text", { x: labelW + w + 6, y: y + 16, class: "bar-value" }, `${r.value}${unit ? " " + unit : ""}`));
  });

  return h(
    "figure",
    { class: "chart" },
    svg,
    h(
      "figcaption",
      { class: "small muted" },
      h("ul", { class: "plain" }, rows.map((r) => h("li", null, `${r.label}: ${r.value}${unit ? " " + unit : ""} (${r.note || "uncertainty not reported"})${r.fixture ? " [fixture, not NASA data]" : ""}`))),
    ),
  );
}

function truncate(t, n) {
  return t.length > n ? t.slice(0, n - 1) + "…" : t;
}
