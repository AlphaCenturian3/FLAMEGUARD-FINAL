// Evidence-class rules from master spec §2. Pure functions; no DOM.

export const SIMULATION_LABEL = "Fluid and thermal transport model. No combustion chemistry.";

export const EVIDENCE_CLASSES = Object.freeze({
  measured: {
    label: "Measured",
    short: "MEAS",
    description: "Taken directly from a NASA experimental record.",
  },
  interpretation: {
    label: "Interpretation",
    short: "INTERP",
    description: "FlameGuard-SI analysis derived from measured records. Not a NASA statement.",
  },
  illustrative_simulation: {
    label: "Illustrative simulation",
    short: "SIM",
    description: "FlameGuard-SI model output. Never experimental data.",
  },
});

/** @param {unknown} cls */
export function evidenceInfo(cls) {
  if (typeof cls === "string" && Object.hasOwn(EVIDENCE_CLASSES, cls)) {
    return { key: cls, valid: true, ...EVIDENCE_CLASSES[cls] };
  }
  return {
    key: "unknown",
    valid: false,
    label: "Unknown evidence class",
    short: "??",
    description: "This record does not carry a valid evidence class and must not be relied on.",
  };
}

/** A value counts as missing when it is null, undefined, or an empty string. */
export function isMissing(v) {
  return v === null || v === undefined || (typeof v === "string" && v.trim() === "");
}

/**
 * Fields a reader would expect on a finding that are absent. They are shown
 * as missing rather than filled in (spec §2.2).
 * @param {import("../api/types.js").Finding} finding
 * @returns {string[]}
 */
export function missingFindingFields(finding) {
  const fields = ["value", "unit", "uncertainty"];
  return fields.filter((f) => isMissing(finding[f]));
}

/** @param {import("../api/types.js").Source} source */
export function missingSourceFields(source) {
  return ["page", "quote", "archive_id"].filter((f) => isMissing(source[f]));
}

/** @param {import("../api/types.js").Investigation} inv */
export function missingInvestigationFields(inv) {
  const missing = [];
  if (isMissing(inv.acronym)) missing.push("acronym");
  if (isMissing(inv.platform)) missing.push("platform");
  if (!Array.isArray(inv.objectives) || inv.objectives.length === 0) missing.push("objectives");
  if (!Array.isArray(inv.relevant_environments) || inv.relevant_environments.length === 0) missing.push("relevant_environments");
  return missing;
}

/** Sources cited directly by a finding (only measured findings embed them). */
export function findingSources(finding) {
  const sources = finding && finding.provenance && finding.provenance.sources;
  return Array.isArray(sources) ? sources : [];
}

/**
 * Client-side re-check of the contract's provenance rules. The backend and CI
 * validate too; the UI repeats the check so a bad record is flagged on screen
 * instead of displayed as trustworthy.
 * @param {import("../api/types.js").Finding} finding
 * @returns {string[]} human-readable problems; empty when OK.
 */
export function provenanceIssues(finding) {
  const issues = [];
  const p = finding && typeof finding.provenance === "object" && finding.provenance ? finding.provenance : null;
  const info = evidenceInfo(finding && finding.evidence_class);
  if (!info.valid) issues.push("Evidence class is missing or not one of measured, interpretation, illustrative_simulation.");
  if (!p) {
    issues.push("Provenance is missing.");
    return issues;
  }
  if (info.key === "measured") {
    if (isMissing(p.manifest_id)) issues.push("Measured finding has no manifest_id.");
    if (!Array.isArray(p.sources) || p.sources.length === 0) issues.push("Measured finding cites no source.");
  }
  if (info.key === "interpretation") {
    if (!Array.isArray(p.derived_from) || p.derived_from.length === 0) issues.push("Interpretation does not list the findings it is derived from.");
    if (isMissing(p.method)) issues.push("Interpretation does not state its method.");
    if (p.generated_by !== "FlameGuard-SI") issues.push("Interpretation is not attributed to FlameGuard-SI.");
  }
  if (info.key === "illustrative_simulation") {
    if (finding.label !== SIMULATION_LABEL) issues.push("Simulation finding is missing the required label.");
    if (isMissing(p.model) || isMissing(p.model_version)) issues.push("Simulation finding does not name its model and version.");
  }
  return issues;
}

/** True when a record is a contract fixture rather than real data. */
export function isFixture(record) {
  return Boolean(record && record.fixture === true);
}

/**
 * Display text for a finding's value. Missing values say so explicitly and
 * are never replaced with an estimate.
 */
export function formatValue(finding) {
  if (isMissing(finding.value)) return null;
  const unit = isMissing(finding.unit) ? "" : ` ${finding.unit}`;
  return `${finding.value}${unit}`;
}

export const ENVIRONMENTS = Object.freeze({
  spacecraft: "Spacecraft",
  space_station: "Space station",
  lunar_base: "Lunar base",
  martian_base: "Martian base",
  pressurized_rover: "Pressurized rover",
  earth: "Earth (1 g reference)",
});

export function environmentLabel(key) {
  return Object.hasOwn(ENVIRONMENTS, key) ? ENVIRONMENTS[key] : key;
}
