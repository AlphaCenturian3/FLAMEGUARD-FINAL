// Evidence-chain tracing. Pure functions; no DOM.
//
// A finding counts as evidence-backed only when every path through its
// `derived_from` links resolves to loaded findings, every node passes the
// contract's provenance rules, no node is an illustrative simulation, and
// the chain ends in at least one measured finding. Used by both the ranking
// guard and the Interpretation view, so the two cannot disagree.

import { evidenceInfo, provenanceIssues } from "./evidence.js";

export const MAX_TRACE_DEPTH = 25;

/**
 * @param {import("../api/types.js").Finding} finding
 * @param {Map<string, import("../api/types.js").Finding>} findingsById
 * @returns {{ supported: boolean, reasons: string[], measuredRoots: import("../api/types.js").Finding[] }}
 */
export function traceSupport(finding, findingsById) {
  const reasons = [];
  const roots = new Map();
  const done = new Set();

  function visit(f, path) {
    const id = f && f.id ? f.id : "(no id)";
    if (path.length > MAX_TRACE_DEPTH) {
      reasons.push(`Evidence chain through ${id} is deeper than ${MAX_TRACE_DEPTH} links.`);
      return;
    }
    if (done.has(id)) return;
    done.add(id);

    for (const issue of provenanceIssues(f)) reasons.push(`${id}: ${issue}`);
    const cls = evidenceInfo(f && f.evidence_class).key;

    if (cls === "measured") {
      roots.set(id, f);
    } else if (cls === "illustrative_simulation") {
      reasons.push(
        path.length === 0
          ? `${id} is an illustrative simulation, not evidence.`
          : `Depends on illustrative simulation ${id} (via ${[...path, id].join(" → ")}). Simulations may not support rankings or insights.`,
      );
    } else if (cls === "interpretation") {
      const parents = Array.isArray(f.provenance && f.provenance.derived_from) ? f.provenance.derived_from : [];
      for (const pid of parents) {
        if (path.includes(pid) || pid === id) {
          reasons.push(`Circular derivation: ${[...path, id, pid].join(" → ")}.`);
          continue;
        }
        const parent = findingsById.get(pid);
        if (!parent) {
          reasons.push(`Supporting finding ${pid} (cited by ${id}) is not among the loaded findings.`);
          continue;
        }
        visit(parent, [...path, id]);
      }
    }
  }

  if (!finding) return { supported: false, reasons: ["Finding is missing."], measuredRoots: [] };
  visit(finding, []);
  if (reasons.length === 0 && roots.size === 0) reasons.push("The evidence chain does not reach any measured finding.");
  return { supported: reasons.length === 0, reasons: [...new Set(reasons)], measuredRoots: [...roots.values()] };
}
