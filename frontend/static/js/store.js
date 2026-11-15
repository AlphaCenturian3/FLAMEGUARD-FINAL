// Loads and caches evidence from the active data source. Each resource is a
// small state machine: loading -> ready | not_implemented | error.

import { isNotImplemented } from "./api/errors.js";
import { versionMismatch } from "./config.js";
import { groupFindings } from "./model/filter.js";

/**
 * @typedef {{ state: "idle"|"loading"|"ready"|"not_implemented"|"error", data?: any, error?: any }} Resource
 */

/**
 * Display checks on a v0.2.0 list response (S7 and version). They only warn;
 * they never change the data.
 */
export function listWarnings(res, what) {
  const out = [];
  const items = Array.isArray(res && res.items) ? res.items : null;
  if (!items) out.push(`${what}: response has no items array.`);
  else if (typeof res.total !== "number") out.push(`${what}: response has no total.`);
  else if (res.total !== items.length) out.push(`${what}: total is ${res.total} but ${items.length} items were returned (S7).`);
  const v = versionMismatch(res && res.contract_version);
  if (v) out.push(`${what}: ${v}`);
  return out;
}

/** Alert text when the backend withheld evidence files (X-FlameGuard-Rejected-Entries), else null. */
export function rejectedWarning(count) {
  if (count === 0 || count === undefined || count === null) return null;
  if (Number.isNaN(count)) return "The backend reported that some evidence files were rejected and are not shown. The lists on this page are incomplete; see the server log.";
  const files = count === 1 ? "1 evidence file was" : `${count} evidence files were`;
  return `${files} rejected by the backend's checks and ${count === 1 ? "is" : "are"} not shown. The lists on this page are incomplete; see the server log.`;
}

/** @param {any} err */
export function resourceFromError(err) {
  return { state: isNotImplemented(err) ? "not_implemented" : "error", error: err };
}

/** @param {import("./api/types.js").DataSource} source */
export function createStore(source) {
  let evidencePromise = null;
  const listeners = new Set();
  const selection = new Set(readSelection());

  async function loadEvidence() {
    /** @type {Resource} */ let investigations;
    /** @type {Resource} */ let findings;
    const warnings = [];
    const readList = (res, what) => {
      const items = Array.isArray(res && res.items) ? res.items : [];
      warnings.push(...listWarnings(res, what));
      return items;
    };
    try {
      investigations = { state: "ready", data: readList(await source.listInvestigations(), "Investigation list") };
    } catch (err) {
      investigations = resourceFromError(err);
    }
    try {
      findings = { state: "ready", data: readList(await source.listFindings(), "Finding list") };
    } catch (err) {
      findings = resourceFromError(err);
    }
    const rejectedEntries = typeof source.rejectedEntries === "function" ? source.rejectedEntries() : 0;
    const rejected = rejectedWarning(rejectedEntries);
    if (rejected) warnings.push(rejected);
    const findingList = findings.state === "ready" ? findings.data : [];
    return {
      rejectedEntries,
      investigations,
      findings,
      warnings,
      findingsByInvestigation: groupFindings(findingList),
      findingsById: new Map(findingList.map((f) => [f.id, f])),
    };
  }

  return {
    source,
    /** Investigations + findings, loaded once per page. */
    evidence() {
      if (!evidencePromise) evidencePromise = loadEvidence();
      return evidencePromise;
    },
    reload() {
      evidencePromise = null;
      return this.evidence();
    },
    selection: {
      has: (id) => selection.has(id),
      ids: () => [...selection],
      toggle(id) {
        if (selection.has(id)) selection.delete(id);
        else selection.add(id);
        writeSelection([...selection]);
        listeners.forEach((fn) => fn());
      },
      set(ids) {
        selection.clear();
        ids.forEach((id) => selection.add(id));
        writeSelection([...selection]);
        listeners.forEach((fn) => fn());
      },
    },
    onSelectionChange(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    },
  };
}

const KEY = "flameguard.compareSelection";
function readSelection() {
  try {
    const raw = sessionStorage.getItem(KEY);
    const ids = raw ? JSON.parse(raw) : [];
    return Array.isArray(ids) ? ids.filter((x) => typeof x === "string") : [];
  } catch {
    return [];
  }
}
function writeSelection(ids) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(ids));
  } catch {
    // Storage unavailable (private mode); selection lasts for this page only.
  }
}
