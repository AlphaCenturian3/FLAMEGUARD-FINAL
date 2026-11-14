// Evidence-chain tracing. Pure functions; no DOM.
//
// A finding counts as evidence-backed only when every path through its
// `derived_from` links resolves to loaded findings, every node passes the
// contract's provenance rules, there are no cycles, no node is excluded
// (S9, transitive), and the chain ends in at least one measured finding.
// Used by the ranking display guard, the Interpretation view and the TARS UI,
// so they cannot disagree. Display-only: it never scores anything.

import { curationNotes, evidenceInfo, provenanceIssues } from "./evidence.js";

export const MAX_TRACE_DEPTH = 25;

/**
 * @param {import("../api/types.js").Finding} finding
 * @param {Map<string, import("../api/types.js").Finding>} findingsById
 * @returns {{ supported: boolean, reasons: string[], measuredRoots: import("../api/types.js").Finding[], excludedAncestors: import("../api/types.js").Finding[] }}
 */
export function traceSupport(finding, findingsById) {
  const reasons = []; // provenance / resolution / cycle / simulation problems
  const exclusionReasons = []; // S9: depends on an excluded value
  const roots = new Map();
  const excluded = new Map();
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

    if (f && f.value_status === "excluded") {
      excluded.set(id, f);
      exclusionReasons.push(
        path.length === 0
          ? `${id} is excluded by FlameGuard-SI and is not evidence (S9).`
          : `Depends on excluded finding ${id} (via ${[...path, id].join(" → ")}). An exclusion-dependent finding may only explain the exclusion (S9).`,
      );
    } else if (cls === "measured") {
      roots.set(id, f);
    } else if (f && f.evidence_class === "illustrative_simulation") {
      reasons.push(`Depends on simulation ${id}. Simulations are never evidence.`);
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

  if (!finding) return { supported: false, reasons: ["Finding is missing."], problems: ["Finding is missing."], exclusionReasons: [], measuredRoots: [], excludedAncestors: [] };
  visit(finding, []);
  if (reasons.length === 0 && exclusionReasons.length === 0 && roots.size === 0) reasons.push("The evidence chain does not reach any measured finding.");
  const problems = [...new Set(reasons)];
  const excl = [...new Set(exclusionReasons)];
  return {
    supported: problems.length === 0 && excl.length === 0,
    reasons: [...problems, ...excl], // everything that blocks use as evidence
    problems, // blocking problems other than exclusion
    exclusionReasons: excl,
    measuredRoots: [...roots.values()],
    excludedAncestors: [...excluded.values()],
  };
}

/**
 * Exclusion explanation for an exclusion-dependent finding: the excluded
 * ancestors (or the finding itself) and their exclusion notes. Empty when the
 * finding does not depend on an excluded value.
 */
export function exclusionContext(finding, findingsById) {
  const { excludedAncestors } = traceSupport(finding, findingsById);
  return excludedAncestors.map((f) => ({
    finding: f,
    notes: curationNotes(f).filter((n) => n.kind === "exclusion"),
  }));
}
