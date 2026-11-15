// One polite live region for short status messages (WCAG 4.1.3). Views announce a one-line
// summary ("Comparison loaded: not comparable, 2 reasons") instead of making whole result
// containers live, which would read entire lists aloud on every update.

/** @param {string} message */
export function announce(message) {
  const el = typeof document !== "undefined" && document.getElementById("announcer");
  if (!el) return;
  el.textContent = "";
  // Clear first, then set on the next tick, so an identical message is announced again.
  setTimeout(() => {
    el.textContent = message;
  }, 50);
}

/** True when the user asked the system to reduce motion (WCAG 2.3.3 / prefers-reduced-motion). */
export function prefersReducedMotion() {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}
