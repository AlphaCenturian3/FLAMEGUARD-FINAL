// Shared application-context selector (spacecraft, lunar base, ...), used by
// the Rank and Interpret views.

import { RANKING_CONTEXTS } from "../model/ranking.js";
import { h } from "../ui/dom.js";

let current = "spacecraft";
try {
  const saved = sessionStorage.getItem("flameguard.context");
  if (saved && RANKING_CONTEXTS.some((c) => c.key === saved)) current = saved;
} catch {
  // ignore
}

export function getContext() {
  return current;
}

export function setContext(key) {
  current = key;
  try {
    sessionStorage.setItem("flameguard.context", key);
  } catch {
    // ignore
  }
}

/** @param {(key: string) => void} onChange */
export function contextSelect(onChange) {
  return h(
    "label",
    { class: "field context-field" },
    h("span", null, "Application context"),
    h(
      "select",
      {
        name: "context",
        onchange: (e) => {
          setContext(e.target.value);
          onChange(e.target.value);
        },
      },
      RANKING_CONTEXTS.map((c) => h("option", { value: c.key, selected: c.key === current }, c.label)),
    ),
  );
}
