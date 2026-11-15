// Reusable UI building blocks. Every scientific value rendered here carries
// its evidence class, its value status, its fixture status, and a route back
// to its source. FlameGuard-SI text is always labelled as such; a recorded
// quote is never called "verified" (contract v0.2.0, S10d / Q3).

import {
  CONDITIONS,
  curationNotes,
  environmentLabel,
  evidenceInfo,
  findingSources,
  formatValue,
  isFixture,
  isMissing,
  missingFindingFields,
  missingInvestigationFields,
  missingSourceFields,
  provenanceIssues,
  SIMULATION_LABEL,
  valueStatusInfo,
} from "../model/evidence.js";
import { h, safeHttpUrl } from "./dom.js";

export function evidenceBadge(cls) {
  const info = evidenceInfo(cls);
  return h("span", { class: `badge ev ev-${info.key}`, title: info.description }, h("span", { class: "ev-dot", "aria-hidden": "true" }), info.label);
}

export function fixtureBadge() {
  return h("span", { class: "badge fixture", title: "Contract fixture with invented placeholder content." }, "Fixture · not NASA data");
}

export function valueStatusBadge(status) {
  const info = valueStatusInfo(status);
  return h("span", { class: `badge vs vs-${info.key}`, title: info.description }, info.label);
}

export function simulationLabel() {
  return h("p", { class: "sim-label", role: "note" }, h("strong", null, "Illustrative simulation: "), SIMULATION_LABEL);
}

/** Explicit "missing" chip list. */
export function missingList(fields, noun = "Not reported") {
  if (!fields.length) return null;
  return h(
    "div",
    { class: "missing" },
    h("span", { class: "missing-title" }, `${noun}:`),
    fields.map((f) => h("span", { class: "chip missing-chip" }, f.replaceAll("_", " "))),
  );
}

function link(url, text) {
  const href = safeHttpUrl(url);
  return href ? h("a", { href, target: "_blank", rel: "noopener noreferrer" }, text, h("span", { class: "sr-only" }, " (opens in new tab)")) : text;
}

/** @param {import("../api/types.js").Source} s */
export function sourceItem(s) {
  const missing = missingSourceFields(s);
  return h(
    "li",
    { class: "source" },
    h("div", { class: "source-title" }, link(s.url, s.title)),
    h(
      "dl",
      { class: "kv compact" },
      h("dt", null, "URL"),
      h("dd", { class: "mono break" }, s.url || "—"),
      h("dt", null, "Retrieved"),
      h("dd", null, s.retrieved || "—"),
      !isMissing(s.page) ? [h("dt", null, "Page"), h("dd", null, String(s.page))] : null,
      s.archive_id ? [h("dt", null, "Archive ID"), h("dd", { class: "mono" }, s.archive_id)] : null,
    ),
    s.quote ? h("blockquote", { class: "quote" }, h("span", { class: "quote-label" }, "Recorded quote: "), `“${s.quote}”`) : null,
    missingList(missing, "Source fields not provided"),
  );
}

export function sourceList(sources, emptyText = "No source cited.") {
  if (!sources || !sources.length) return h("p", { class: "muted" }, emptyText);
  return h("ul", { class: "sources" }, sources.map(sourceItem));
}

/** All eight condition keys; a null value is shown as "Not reported", never inferred. */
export function conditionsBlock(conditions) {
  if (!conditions || typeof conditions !== "object") return h("p", { class: "missing-value" }, "Conditions not provided.");
  return h(
    "dl",
    { class: "kv compact conditions", "aria-label": "Experimental conditions" },
    CONDITIONS.map(([key, label, unit]) => {
      const v = conditions[key];
      return [
        h("dt", null, label),
        h("dd", null, isMissing(v) ? h("span", { class: "missing-value" }, "Not reported") : `${v}${unit ? " " + unit : ""}`.replaceAll("_", " ")),
      ];
    }),
  );
}

/** FlameGuard-SI curation notes (caution / exclusion), each with its flag and recorded quote. */
export function curationNotesBlock(notes) {
  if (!notes.length) return null;
  return h(
    "div",
    { class: "curation" },
    notes.map((n) =>
      h(
        "div",
        { class: `curation-note note-${n.kind === "exclusion" ? "exclusion" : "caution"}`, role: "note" },
        h("p", { class: "note-head" }, h("strong", null, n.kind === "exclusion" ? "FlameGuard-SI exclusion" : "FlameGuard-SI caution"), h("span", { class: "muted small" }, " · FlameGuard-SI assessment, not source text")),
        h("p", null, n.note),
        n.source
          ? h(
              "p",
              { class: "small" },
              "Recorded quote",
              !isMissing(n.source.page) ? ` (p. ${n.source.page})` : "",
              ": ",
              h("q", null, n.source.quote || "—"),
              " · ",
              link(n.source.url, n.source.title),
            )
          : h("p", { class: "warn-text small" }, "No source recorded for this note."),
        n.flag_ref ? h("p", { class: "mono muted small" }, `Quality flag ${n.flag_ref.flag_id} in ${n.flag_ref.manifest_id}`) : h("p", { class: "warn-text small" }, "No quality-flag reference."),
      ),
    ),
  );
}

/**
 * Provenance panel for one finding.
 * @param {import("../api/types.js").Finding} finding
 * @param {Map<string, import("../api/types.js").Finding>} [findingsById]
 */
export function provenanceBlock(finding, findingsById = new Map()) {
  const p = finding.provenance || {};
  const info = evidenceInfo(finding.evidence_class);
  const rows = [];
  if (info.key === "measured") {
    rows.push(h("dt", null, "Manifest entry"), h("dd", { class: "mono" }, p.manifest_id || "missing"), h("dt", null, "Locator"), h("dd", null, p.locator || h("span", { class: "missing-value" }, "missing")));
  } else if (info.key === "interpretation") {
    rows.push(
      h("dt", null, "Derived from"),
      h(
        "dd",
        null,
        (p.derived_from || []).length
          ? h(
              "ul",
              { class: "inline-list" },
              p.derived_from.map((id) => {
                const src = findingsById.get(id);
                return h("li", null, h("span", { class: "mono" }, id), src ? [" ", evidenceBadge(src.evidence_class), " ", valueStatusBadge(src.value_status)] : h("span", { class: "warn-text" }, " (not loaded)"));
              }),
            )
          : "missing",
      ),
      h("dt", null, "Method"),
      h("dd", { class: "mono" }, `${p.method || "missing"}${p.method_version ? " v" + p.method_version : " (version missing)"}`),
      h("dt", null, "Generated by"),
      h("dd", null, p.generated_by || "missing"),
    );
  }
  const issues = provenanceIssues(finding);
  return h(
    "div",
    { class: "provenance" },
    rows.length ? h("dl", { class: "kv compact" }, rows) : null,
    info.key === "measured" ? sourceList(findingSources(finding), "No source cited.") : null,
    issues.length ? h("div", { class: "alert alert-warn", role: "status" }, h("strong", null, "Provenance problems: "), h("ul", null, issues.map((i) => h("li", null, i)))) : null,
  );
}

function valueBlock(finding) {
  const status = valueStatusInfo(finding.value_status);
  const value = formatValue(finding);
  let shown;
  if (status.key === "reported") shown = value ?? h("span", { class: "missing-value" }, "Reported, but no value present");
  else if (status.key === "excluded") shown = h("span", { class: "excluded-value" }, "Excluded by FlameGuard-SI — value not shown");
  else shown = h("span", { class: "missing-value" }, status.label);
  return [
    h("dt", null, finding.quantity ? finding.quantity.replaceAll("_", " ") : "Value"),
    h("dd", { "data-value-status": status.key }, shown),
  ];
}

/**
 * @param {import("../api/types.js").Finding} finding
 * @param {Map<string, import("../api/types.js").Finding>} [findingsById]
 * @param {{ hideConditions?: boolean }} [opts]
 */
const OUTCOME_HINT = "The label the source prints for this test. Not a FlameGuard-SI classification of what happened.";

/**
 * The structured test identity (contract v0.2.2): the source's test identifier and its printed
 * outcome label, verbatim. Nothing is inferred from other values. Null when the finding carries
 * neither field (legacy data).
 */
export function testIdentity(finding) {
  const id = finding.test_id || null;
  const outcome = finding.test_outcome || null;
  if (!id && !outcome) return null;
  return h(
    "p",
    { class: "test-identity small" },
    h("span", { class: "chip test-id" }, id ? `Test ${id}` : "Test not identified"),
    " ",
    h("span", { class: `chip test-outcome${outcome ? "" : " missing-value"}`, title: OUTCOME_HINT }, `Test end as printed: ${outcome || "Not reported"}`),
  );
}

export function findingCard(finding, findingsById, opts = {}) {
  const info = evidenceInfo(finding.evidence_class);
  const measured = info.key === "measured";
  const showValue = measured || finding.value_status === "reported";
  return h(
    "article",
    { class: `finding ev-border-${info.key}${finding.value_status === "excluded" ? " is-excluded" : ""}`, "aria-label": `${info.label} finding ${finding.id}` },
    h(
      "header",
      { class: "finding-head" },
      evidenceBadge(finding.evidence_class),
      showValue ? valueStatusBadge(finding.value_status) : null,
      isFixture(finding) ? fixtureBadge() : null,
      h("span", { class: "mono muted small" }, finding.id),
    ),
    finding.evidence_class === "illustrative_simulation" ? simulationLabel() : null,
    h("p", { class: "statement" }, finding.statement),
    measured && !opts.hideTestIdentity ? testIdentity(finding) : null,
    info.key === "interpretation" ? h("p", { class: "small muted" }, "Generated by FlameGuard-SI. Not a NASA statement.") : null,
    showValue
      ? h(
          "dl",
          { class: "kv" },
          valueBlock(finding),
          measured
            ? [
                h("dt", null, "Uncertainty"),
                h("dd", null, isMissing(finding.uncertainty) ? h("span", { class: "missing-value" }, "Not reported by the source") : [h("span", { class: "muted small" }, "Reported by the source: "), finding.uncertainty]),
              ]
            : null,
        )
      : h("p", { class: "small muted" }, "Qualitative statement; no numerical value."),
    measured ? curationNotesBlock(curationNotes(finding)) : null,
    info.key === "interpretation" && Array.isArray(finding.limitations) && finding.limitations.length
      ? h("div", { class: "limitations" }, h("p", { class: "small" }, h("strong", null, "Limitations (FlameGuard-SI):")), h("ul", { class: "small" }, finding.limitations.map((l) => h("li", null, l))))
      : null,
    info.key === "interpretation" && (finding.relevant_environments || []).length
      ? h("p", { class: "small" }, "Argued to apply to: ", finding.relevant_environments.map((e) => h("span", { class: "chip" }, environmentLabel(e))))
      : null,
    missingList(missingFindingFields(finding), "Missing from record"),
    measured && !opts.hideConditions ? h("details", { class: "prov-details" }, h("summary", null, "Experimental conditions"), conditionsBlock(finding.conditions)) : null,
    h("details", { class: "prov-details" }, h("summary", null, "Provenance and sources"), provenanceBlock(finding, findingsById)),
  );
}

/** @param {import("../api/types.js").Investigation} inv */
export function investigationMeta(inv) {
  return h(
    "dl",
    { class: "kv" },
    h("dt", null, "Platform"),
    h("dd", null, inv.platform || h("span", { class: "missing-value" }, "Not reported")),
    h("dt", null, "Environments"),
    h("dd", null, (inv.relevant_environments || []).length ? inv.relevant_environments.map((e) => h("span", { class: "chip" }, environmentLabel(e))) : h("span", { class: "missing-value" }, "Not reported")),
    h("dt", null, "Objectives"),
    h("dd", null, (inv.objectives || []).length ? h("ul", { class: "plain" }, inv.objectives.map((o) => h("li", null, o))) : h("span", { class: "missing-value" }, "Not reported")),
    (inv.datasets || []).length ? [h("dt", null, "Datasets"), h("dd", { class: "mono small" }, inv.datasets.join(", "))] : null,
  );
}

/**
 * Loading / empty / error / not-implemented panel.
 * @param {{kind: "loading"|"empty"|"error"|"not_implemented", title: string, message?: string, detail?: string, action?: Node}} opts
 */
export function statePanel({ kind, title, message, detail, action }) {
  const role = kind === "error" ? "alert" : "status";
  return h(
    "div",
    { class: `state state-${kind}`, role, "aria-live": kind === "loading" ? "polite" : null },
    kind === "loading" ? h("span", { class: "spinner", "aria-hidden": "true" }) : h("span", { class: "state-icon", "aria-hidden": "true" }, kind === "error" ? "!" : kind === "not_implemented" ? "501" : "∅"),
    h("div", null, h("p", { class: "state-title" }, title), message ? h("p", null, message) : null, detail ? h("p", { class: "mono small muted" }, detail) : null, action || null),
  );
}

const ERROR_TITLES = {
  invalid_request: "The request was rejected (HTTP 400)",
  not_found: "Not found (HTTP 404)",
  unavailable: "Service unavailable",
  network_error: "The API could not be reached",
  fixture_unavailable: "Fixture file could not be loaded",
};

/** Standard panel for a failed or not-yet-implemented resource (F6). */
export function resourcePanel(resource, what, endpoint) {
  if (resource.state === "not_implemented") {
    return statePanel({
      kind: "not_implemented",
      title: `${what}: not implemented by the backend yet`,
      message: `${endpoint} returned HTTP 501. This view will fill in automatically once the backend implements it. Nothing is shown in its place.`,
      detail: resource.error && resource.error.message,
    });
  }
  const code = resource.error && resource.error.code;
  return statePanel({
    kind: "error",
    title: `${ERROR_TITLES[code] || "Request failed"}: ${what.toLowerCase()}`,
    message: resource.error ? resource.error.message : "Unknown error.",
    detail: code ? `code: ${code}${resource.error.status ? ` · HTTP ${resource.error.status}` : ""}` : null,
  });
}

export { missingInvestigationFields };
