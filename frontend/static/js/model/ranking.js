// Ranking display rules. The ranking itself is computed by the backend
// (GET /api/rankings?context=). This module never computes scores; it only
// checks what the backend returns against spec §5.1 before it is shown.
//
// An item is shown only if every supporting finding it cites resolves to a
// loaded finding and traces back, without any illustrative simulation, to
// measured evidence. Anything else is withheld with the reason.
//
// Must not import any simulation module (spec §2.3).

import { ENVIRONMENTS } from "./evidence.js";
import { traceSupport } from "./trace.js";

export const RANKING_CONTEXTS = Object.freeze(
  Object.entries(ENVIRONMENTS).map(([key, label]) => ({ key, label })),
);

const ALLOWED_INPUT_CLASSES = new Set(["measured", "interpretation"]);

/**
 * Check a ranking response.
 *
 * Withheld when:
 * - investigation_id, a numeric score, a rationale, or inputs are missing;
 * - any input ID does not resolve to a loaded finding;
 * - any input is not measured or interpretation;
 * - any input's evidence chain fails `traceSupport` (unresolved parents,
 *   bad provenance, cycles, or an illustrative simulation anywhere upstream).
 *
 * @param {{items?: import("../api/types.js").RankingItem[]}} response
 * @param {Map<string, import("../api/types.js").Finding>} findingsById
 */
export function reviewRankings(response, findingsById) {
  const accepted = [];
  const rejected = [];
  const items = response && Array.isArray(response.items) ? response.items : [];

  for (const item of items) {
    const problems = [];
    if (!item || typeof item.investigation_id !== "string") problems.push("Missing investigation_id.");
    if (!item || typeof item.score !== "number" || !Number.isFinite(item.score)) problems.push("Score is not a number.");
    if (!item || typeof item.rationale !== "string" || item.rationale.trim() === "") problems.push("No rationale given.");
    const inputs = item && Array.isArray(item.inputs) ? item.inputs : [];
    if (inputs.length === 0) problems.push("No supporting findings listed.");

    const resolved = [];
    for (const id of inputs) {
      const f = findingsById.get(id);
      if (!f) {
        problems.push(`Supporting finding ${id} is not among the loaded findings, so the ranking cannot be traced.`);
        continue;
      }
      if (!ALLOWED_INPUT_CLASSES.has(f.evidence_class)) {
        problems.push(`Input ${id} is ${f.evidence_class}; rankings may use only measured or interpretation findings.`);
      } else {
        const trace = traceSupport(f, findingsById);
        for (const r of trace.reasons) problems.push(`Input ${id}: ${r}`);
      }
      resolved.push(f);
    }

    const entry = { item, inputs: resolved, problems: [...new Set(problems)] };
    (entry.problems.length ? rejected : accepted).push(entry);
  }

  accepted.sort((a, b) => b.item.score - a.item.score);
  return { accepted, rejected };
}
