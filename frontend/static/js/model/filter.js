// Evidence Explorer filtering. Pure functions; no DOM.
//
// Contract v0.1.0 has no structured experimental parameters (oxygen fraction,
// pressure, flow speed, fuel). Filters therefore use only fields the contract
// defines: text, platform, environment, evidence class, and whether a
// finding reports a value.

/**
 * @typedef {Object} ExplorerFilters
 * @property {string} [query]
 * @property {string} [platform]        "" = any
 * @property {string} [environment]     "" = any
 * @property {string} [evidenceClass]   "" = any
 * @property {string} [valueStatus]     "" = any; else investigations with a finding in that value_status
 * @property {boolean} [withValuesOnly] only investigations with a finding that reports a value
 */

export const EMPTY_FILTERS = Object.freeze({ query: "", platform: "", environment: "", evidenceClass: "", valueStatus: "", withValuesOnly: false });

function norm(s) {
  return String(s || "").toLowerCase();
}

/**
 * @param {import("../api/types.js").Investigation[]} investigations
 * @param {ExplorerFilters} filters
 * @param {Map<string, import("../api/types.js").Finding[]>} findingsByInvestigation
 */
export function filterInvestigations(investigations, filters, findingsByInvestigation = new Map()) {
  const f = { ...EMPTY_FILTERS, ...filters };
  const terms = norm(f.query).split(/\s+/).filter(Boolean);

  return investigations.filter((inv) => {
    const findings = findingsByInvestigation.get(inv.id) || [];

    if (terms.length) {
      const haystack = norm(
        [inv.id, inv.name, inv.acronym, inv.platform, ...(inv.objectives || []), ...findings.map((x) => x.statement)].join(" "),
      );
      if (!terms.every((t) => haystack.includes(t))) return false;
    }
    if (f.platform && inv.platform !== f.platform) return false;
    if (f.environment && !(inv.relevant_environments || []).includes(f.environment)) return false;
    if (f.evidenceClass && !findings.some((x) => x.evidence_class === f.evidenceClass)) return false;
    if (f.withValuesOnly && !findings.some((x) => x.value_status === "reported" && x.value !== null && x.value !== undefined && x.value !== "")) return false;
    if (f.valueStatus && !findings.some((x) => x.value_status === f.valueStatus)) return false;
    return true;
  });
}

/** Options for the filter dropdowns, built from the loaded data only. */
export function facetOptions(investigations) {
  const platforms = new Set();
  const environments = new Set();
  for (const inv of investigations) {
    if (inv.platform) platforms.add(inv.platform);
    for (const env of inv.relevant_environments || []) environments.add(env);
  }
  return { platforms: [...platforms].sort(), environments: [...environments].sort() };
}

/** Group findings by investigation_id. */
export function groupFindings(findings) {
  const map = new Map();
  for (const f of findings) {
    if (!map.has(f.investigation_id)) map.set(f.investigation_id, []);
    map.get(f.investigation_id).push(f);
  }
  return map;
}
