// Ranking display rules (P4, contract v0.2.0). The ranking is computed by the
// backend (GET /api/rankings?context=). This module never computes, verifies,
// re-weights or re-orders scores (spec §4.3): items are shown in the backend's
// `rank` order. It only withholds, with reasons, items whose inputs cannot be
// traced to usable evidence.
//
// Must not import any simulation module (spec §2.3).

import { ENVIRONMENTS } from "./evidence.js";
import { traceSupport } from "./trace.js";

export const RANKING_CONTEXTS = Object.freeze(Object.entries(ENVIRONMENTS).map(([key, label]) => ({ key, label })));

const ALLOWED_INPUT_CLASSES = new Set(["measured", "interpretation"]);

/**
 * Withheld when:
 * - rank, investigation_id, a numeric score, a rationale or criterion scores are missing;
 * - a criterion score names a criterion not in `criteria`;
 * - an input finding_id does not resolve to a loaded finding;
 * - an input's declared evidence_class differs from the loaded finding's;
 * - an input is not measured / interpretation;
 * - an input's chain fails `traceSupport`: unresolved parents, bad provenance,
 *   cycles, a simulation, or an `excluded` finding at any depth (S9, transitive).
 *
 * @param {import("../api/types.js").Ranking} response
 * @param {Map<string, import("../api/types.js").Finding>} findingsById
 */
export function reviewRankings(response, findingsById) {
  const criteria = response && Array.isArray(response.criteria) ? response.criteria : [];
  const criterionIds = new Set(criteria.map((c) => c.id));
  const accepted = [];
  const rejected = [];
  const items = response && Array.isArray(response.items) ? response.items : [];

  for (const item of items) {
    const problems = [];
    if (!item || !Number.isInteger(item.rank)) problems.push("Missing rank.");
    if (!item || typeof item.investigation_id !== "string") problems.push("Missing investigation_id.");
    if (!item || typeof item.score !== "number" || !Number.isFinite(item.score)) problems.push("Score is not a number.");
    if (!item || typeof item.rationale !== "string" || item.rationale.trim() === "") problems.push("No rationale given.");
    const scores = item && Array.isArray(item.criterion_scores) ? item.criterion_scores : [];
    if (scores.length === 0) problems.push("No criterion scores.");

    const inputs = [];
    for (const cs of scores) {
      if (!criterionIds.has(cs.criterion_id)) problems.push(`Criterion ${cs.criterion_id} is not among the listed criteria.`);
      for (const input of Array.isArray(cs.inputs) ? cs.inputs : []) {
        const f = findingsById.get(input.finding_id);
        if (!f) {
          problems.push(`Input ${input.finding_id} is not among the loaded findings, so the ranking cannot be traced.`);
          continue;
        }
        if (f.evidence_class !== input.evidence_class) problems.push(`Input ${input.finding_id} is declared ${input.evidence_class} but the loaded finding is ${f.evidence_class}.`);
        if (!ALLOWED_INPUT_CLASSES.has(f.evidence_class)) {
          problems.push(`Input ${input.finding_id} is ${f.evidence_class}; rankings may use only measured or interpretation findings.`);
        } else {
          for (const r of traceSupport(f, findingsById).reasons) problems.push(`Input ${input.finding_id}: ${r}`);
        }
        inputs.push({ criterion_id: cs.criterion_id, finding: f });
      }
    }
    const entry = { item, inputs, problems: [...new Set(problems)] };
    (entry.problems.length ? rejected : accepted).push(entry);
  }

  // Backend order. No sorting by score: the rank field is authoritative.
  accepted.sort((a, b) => a.item.rank - b.item.rank);
  return {
    criteria,
    accepted,
    rejected,
    notRanked: response && Array.isArray(response.excluded) ? response.excluded : [],
  };
}
