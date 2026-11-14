// Loads and caches evidence from the active data source. Each resource is a
// small state machine: loading -> ready | not_implemented | error.

import { isNotImplemented } from "./api/errors.js";
import { groupFindings } from "./model/filter.js";

/**
 * @typedef {{ state: "idle"|"loading"|"ready"|"not_implemented"|"error", data?: any, error?: any }} Resource
 */

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
    try {
      const res = await source.listInvestigations();
      investigations = { state: "ready", data: Array.isArray(res.items) ? res.items : [] };
    } catch (err) {
      investigations = resourceFromError(err);
    }
    try {
      const res = await source.listFindings();
      findings = { state: "ready", data: Array.isArray(res.items) ? res.items : [] };
    } catch (err) {
      findings = resourceFromError(err);
    }
    const findingList = findings.state === "ready" ? findings.data : [];
    return {
      investigations,
      findings,
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
