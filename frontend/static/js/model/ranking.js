// Ranking display rules. The ranking itself is computed by the backend
// (GET /api/rankings?context=). This module never computes scores; it only
// checks what the backend returns against spec §5.1 before it is shown.
//
// Must not import any simulation module (spec §2.3).

import { ENVIRONMENTS } from "./evidence.js";

export const RANKING_CONTEXTS = Object.freeze(
  Object.entries(ENVIRONMENTS).map(([key, label]) => ({ key, label })),
);

const ALLOWED_INPUT_CLASSES = new Set(["measured", "interpretation"]);

/**
 * Check a ranking response.
 * - Items whose inputs include an illustrative_simulation finding are rejected.
 * - Inputs that cannot be resolved against loaded findings are flagged.
 * - Items with a non-numeric score or no rationale are rejected.
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
    const warnings = [];
    if (!item || typeof item.investigation_id !== "string") problems.push("Missing investigation_id.");
    if (!item || typeof item.score !== "number" || !Number.isFinite(item.score)) problems.push("Score is not a number.");
    if (!item || typeof item.rationale !== "string" || item.rationale.trim() === "") problems.push("No rationale given.");
    const inputs = item && Array.isArray(item.inputs) ? item.inputs : [];
    if (inputs.length === 0) problems.push("No supporting findings listed.");

    const resolved = [];
    for (const id of inputs) {
      const f = findingsById.get(id);
      if (!f) {
        warnings.push(`Input ${id} is not among the loaded findings.`);
        continue;
      }
      if (!ALLOWED_INPUT_CLASSES.has(f.evidence_class)) {
        problems.push(`Input ${id} is ${f.evidence_class}; rankings may use only measured or interpretation findings.`);
      }
      resolved.push(f);
    }

    const entry = { item, inputs: resolved, problems, warnings };
    (problems.length ? rejected : accepted).push(entry);
  }

  accepted.sort((a, b) => b.item.score - a.item.score);
  return { accepted, rejected };
}
