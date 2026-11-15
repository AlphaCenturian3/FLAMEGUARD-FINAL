// Evidence rules from the master spec §2 and contract v0.2.0. Pure functions; no DOM.

export const SIMULATION_LABEL = "Fluid and thermal transport model. No combustion chemistry.";

/** Evidence classes. A v0.2.0 Finding is measured or interpretation only. */
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
    description: "FlameGuard-SI model output. Never experimental data, and never a Finding.",
  },
});

/** The four v0.2.0 value statuses and their exact display wording. */
export const VALUE_STATUS = Object.freeze({
  reported: { label: "Reported", description: "The source gives a value." },
  not_reported: { label: "Not reported", description: "The source gives no value." },
  not_applicable: { label: "Not applicable", description: "No value applies (qualitative statement)." },
  excluded: {
    label: "Excluded by FlameGuard-SI",
    description: "The source prints a value, but a reviewed FlameGuard-SI quality flag excludes it from use. The value is not shown.",
  },
});

/** Experimental condition keys (units are part of the key name, contract conditions.schema.json). */
export const CONDITIONS = Object.freeze([
  ["gravity_environment", "Gravity environment", null],
  ["oxygen_mole_fraction", "O₂ mole fraction", null],
  ["pressure_kpa", "Pressure", "kPa"],
  ["flow_velocity_mm_s", "Flow velocity", "mm/s"],
  ["flow_configuration", "Flow configuration", null],
  ["diluent", "Diluent", null],
  ["fuel_or_material", "Fuel or material", null],
  ["sample_geometry", "Sample geometry", null],
]);

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

/** @param {unknown} status */
export function valueStatusInfo(status) {
  if (typeof status === "string" && Object.hasOwn(VALUE_STATUS, status)) return { key: status, valid: true, ...VALUE_STATUS[status] };
  return { key: "unknown", valid: false, label: "Unknown value status", description: "The record has no valid value_status." };
}

/** A value counts as missing when it is null, undefined, or an empty string. */
export function isMissing(v) {
  return v === null || v === undefined || (typeof v === "string" && v.trim() === "");
}

export function isExcluded(finding) {
  return Boolean(finding && finding.value_status === "excluded");
}

/**
 * Display text for a finding's value, or null when no value may be shown.
 * Only a `reported` value is ever displayed: an `excluded` finding never shows
 * a number, even if a malformed record carries one.
 */
export function formatValue(finding) {
  if (!finding || finding.value_status !== "reported" || isMissing(finding.value)) return null;
  const unit = isMissing(finding.unit) || finding.unit === "1" ? "" : ` ${finding.unit}`;
  return `${finding.value}${unit}`;
}

/** Condition keys the source does not report (null). */
export function unreportedConditions(finding) {
  const c = finding && finding.conditions;
  if (!c || typeof c !== "object") return [];
  return CONDITIONS.filter(([key]) => isMissing(c[key])).map(([key]) => key);
}

/** Fields a reader would expect that are absent (shown as missing, never filled in). */
export function missingFindingFields(finding) {
  const missing = [];
  if (finding.value_status === "not_reported") missing.push("value");
  if (finding.evidence_class === "measured" && isMissing(finding.uncertainty)) missing.push("uncertainty");
  return missing;
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

export function curationNotes(finding) {
  return Array.isArray(finding && finding.curation_notes) ? finding.curation_notes : [];
}

/**
 * Client-side re-check of the v0.2.0 provenance rules. The backend and CI
 * validate too; the UI repeats the check so a bad record is flagged on screen
 * instead of displayed as trustworthy.
 * @returns {string[]} human-readable problems; empty when OK.
 */
export function provenanceIssues(finding) {
  const issues = [];
  const p = finding && typeof finding.provenance === "object" && finding.provenance ? finding.provenance : null;
  const cls = finding && finding.evidence_class;
  if (cls === "illustrative_simulation") {
    issues.push("A simulation is not a Finding in contract v0.2.0; it must never appear among findings.");
    return issues;
  }
  if (!evidenceInfo(cls).valid) issues.push("Evidence class is missing or not measured / interpretation.");
  if (!valueStatusInfo(finding && finding.value_status).valid) issues.push("value_status is missing or invalid.");
  if (finding && finding.value_status !== "reported" && !isMissing(finding.value)) issues.push(`A ${finding.value_status} finding carries a value.`);
  if (!p) {
    issues.push("Provenance is missing.");
    return issues;
  }
  const notes = curationNotes(finding);
  if (cls === "measured") {
    if (isMissing(p.manifest_id)) issues.push("Measured finding has no manifest_id.");
    if (isMissing(p.locator)) issues.push("Measured finding has no locator (where in the source).");
    if (!Array.isArray(p.sources) || p.sources.length === 0) issues.push("Measured finding cites no source.");
    if (!finding.conditions || typeof finding.conditions !== "object") issues.push("Measured finding has no conditions.");
    notes.forEach((n, i) => {
      if (n.generated_by !== "FlameGuard-SI") issues.push(`Curation note ${i + 1} is not attributed to FlameGuard-SI.`);
      if (!n.flag_ref || isMissing(n.flag_ref.manifest_id) || isMissing(n.flag_ref.flag_id)) issues.push(`Curation note ${i + 1} has no quality-flag reference.`);
      if (!n.source || isMissing(n.source.quote)) issues.push(`Curation note ${i + 1} records no source quote.`);
    });
    if (finding.value_status === "excluded" && !notes.some((n) => n.kind === "exclusion")) issues.push("Excluded finding has no exclusion note.");
    if (finding.value_status !== "excluded" && notes.some((n) => n.kind === "exclusion")) issues.push("An exclusion note is attached to a value that is not excluded.");
  }
  if (cls === "interpretation") {
    if (!Array.isArray(p.derived_from) || p.derived_from.length === 0) issues.push("Interpretation does not list the findings it is derived from.");
    if (isMissing(p.method)) issues.push("Interpretation does not state its method.");
    if (isMissing(p.method_version)) issues.push("Interpretation does not state its method version.");
    if (p.generated_by !== "FlameGuard-SI") issues.push("Interpretation is not attributed to FlameGuard-SI.");
    if (!Array.isArray(finding.limitations) || finding.limitations.length === 0) issues.push("Interpretation lists no limitations.");
    if (notes.length) issues.push("Curation notes are not allowed on interpretations.");
  }
  return issues;
}

/** True when a record is a contract fixture rather than real data. */
export function isFixture(record) {
  return Boolean(record && record.fixture === true);
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
