// Guided 90-second judge walkthrough: Discover -> Compare -> Rank ->
// Interpret -> Safety Insight. Drives the real views; it shows nothing the
// views themselves do not show.

import { h, mount } from "./ui/dom.js";

export const DEMO_TARGET_SECONDS = 90;

export const DEMO_STEPS = [
  {
    key: "discover",
    title: "Discover",
    route: "#/explorer",
    seconds: 20,
    say: "Search the investigations. Each finding shows its evidence class, reported uncertainty, missing fields, and sources.",
  },
  {
    key: "compare",
    title: "Compare",
    route: "#/compare",
    seconds: 20,
    selectAll: true,
    say: "Put investigations side by side. Values are charted only when the same quantity and unit are confirmed. Otherwise the page says why.",
  },
  {
    key: "rank",
    title: "Rank",
    route: "#/rank",
    seconds: 15,
    say: "Choose a crewed environment. Scores come only from the backend, must trace to measured evidence, and are not risk values. Until the backend ranking and NASA data exist, this step shows the HTTP 501 “not implemented” state, not a ranking.",
  },
  {
    key: "interpret",
    title: "Interpret",
    route: "#/interpret",
    anchor: "implications",
    seconds: 20,
    say: "Each implication is a FlameGuard-SI interpretation traced to the measured records it uses.",
  },
  {
    key: "insight",
    title: "Safety Insight",
    route: "#/interpret",
    anchor: "limitations",
    seconds: 15,
    say: "The insight comes with its limits: tested conditions only, nothing gap-filled, simulations kept separate.",
  },
];

/**
 * @param {{ go: (route: string, anchor?: string) => void, selectAll: () => Promise<void> }} hooks
 */
export function createDemo(hooks) {
  const bar = h("aside", { class: "demo-bar", "aria-label": "Guided demo", hidden: true });
  let index = -1;
  let startedAt = 0;
  let timer = null;
  let timeEl = null;

  function tick() {
    if (index < 0 || !timeEl) return;
    const elapsed = Math.round((Date.now() - startedAt) / 1000);
    timeEl.textContent = `${elapsed}s / ${DEMO_TARGET_SECONDS}s`;
    timeEl.classList.toggle("over", elapsed > DEMO_TARGET_SECONDS);
  }

  function render() {
    if (index < 0) {
      bar.hidden = true;
      return;
    }
    const step = DEMO_STEPS[index];
    const elapsed = Math.round((Date.now() - startedAt) / 1000);
    // Keep keyboard focus in the bar across re-renders.
    const focused = bar.contains(document.activeElement) ? document.activeElement.dataset.action : null;
    bar.hidden = false;
    mount(
      bar,
      h(
        "ol",
        { class: "demo-steps" },
        DEMO_STEPS.map((s, i) => h("li", { class: i === index ? "current" : i < index ? "done" : "", "aria-current": i === index ? "step" : null }, h("span", { class: "n" }, String(i + 1)), s.title)),
      ),
      h("p", { class: "demo-say", "aria-live": "polite" }, h("strong", null, `${step.title}. `), step.say),
      h(
        "div",
        { class: "demo-controls" },
        (timeEl = h("span", { class: "demo-time mono", role: "timer", "aria-live": "off" }, `${elapsed}s / ${DEMO_TARGET_SECONDS}s`)),
        h("button", { type: "button", class: "btn btn-ghost", onclick: back, disabled: index === 0, "data-action": "back" }, "Back"),
        index < DEMO_STEPS.length - 1
          ? h("button", { type: "button", class: "btn btn-primary", onclick: next, "data-action": "next" }, "Next")
          : h("button", { type: "button", class: "btn btn-primary", onclick: restart, "data-action": "next" }, "Restart"),
        h("button", { type: "button", class: "btn btn-ghost", onclick: restart, title: "Restart the demonstration", "aria-label": "Restart the demonstration", "data-action": "restart" }, "↺"),
        h("button", { type: "button", class: "btn btn-ghost", onclick: stop, "data-action": "exit" }, "Exit"),
      ),
    );
    if (focused) {
      const target = bar.querySelector(`[data-action="${focused}"]:not([disabled])`) || bar.querySelector('[data-action="next"]');
      target?.focus();
    }
  }

  async function goTo(i) {
    index = i;
    const step = DEMO_STEPS[i];
    if (step.selectAll) await hooks.selectAll();
    hooks.go(step.route, step.anchor);
    render();
  }
  function next() {
    if (index < DEMO_STEPS.length - 1) goTo(index + 1);
  }
  function back() {
    if (index > 0) goTo(index - 1);
  }
  function restart() {
    startedAt = Date.now();
    goTo(0);
  }
  function stop() {
    index = -1;
    clearInterval(timer);
    timer = null;
    render();
  }

  return {
    element: bar,
    active: () => index >= 0,
    currentStep: () => (index >= 0 ? DEMO_STEPS[index] : null),
    start() {
      clearInterval(timer);
      timer = setInterval(tick, 1000);
      restart();
    },
    next,
    back,
    restart,
    stop,
  };
}
