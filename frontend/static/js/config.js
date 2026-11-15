// Runtime configuration from the page URL (spec §5.3).
//
//   (default)            talk to the backend at the same origin
//   ?fixtures=1          read contracts/examples/ (labelled FIXTURE DATA. NOT NASA DATA.)
//   ?api=http://host     API base URL when not same-origin
//   ?fixtures_base=URL   location of contracts/examples/ (default ../contracts/examples/)

import { createFixtureSource } from "./api/fixtures.js";
import { createHttpSource } from "./api/http.js";

/** Newest contract version this dashboard implements (adds test_id and test_outcome, v0.2.2). */
export const CONTRACT_VERSION = "0.2.2";
/**
 * Contract versions accepted without a warning. 0.2.1 only adds FLEX quantities and 0.2.2 only adds
 * the optional test_id / test_outcome fields, so documents valid under 0.2.0 stay valid. A version is
 * added here only after the dashboard is tested with a response of that version
 * (frontend/tests/flex.test.js) and its schema change is confirmed additive. Anything else warns.
 */
export const SUPPORTED_CONTRACT_VERSIONS = Object.freeze(["0.2.0", "0.2.1", "0.2.2"]);
export const FIXTURE_BANNER = "FIXTURE DATA. NOT NASA DATA.";

/** @param {string} [href] */
export function readConfig(href = window.location.href) {
  const url = new URL(href);
  const params = url.searchParams;
  return {
    source: params.get("fixtures") === "1" ? "fixtures" : "api",
    apiBase: params.get("api") || "",
    fixturesBase: params.get("fixtures_base") || new URL("../contracts/examples/", url).href,
  };
}

/** @param {ReturnType<typeof readConfig>} config */
export function createDataSource(config) {
  return config.source === "fixtures" ? createFixtureSource({ baseUrl: config.fixturesBase }) : createHttpSource({ baseUrl: config.apiBase });
}

/** URL of the current page with fixture mode switched on or off. */
export function urlWithFixtures(on, href = window.location.href) {
  const url = new URL(href);
  if (on) url.searchParams.set("fixtures", "1");
  else url.searchParams.delete("fixtures");
  return url.href;
}

/** Warning text when an API response names a different contract version, else null. */
export function versionMismatch(reported) {
  if (typeof reported !== "string" || SUPPORTED_CONTRACT_VERSIONS.includes(reported)) return null;
  return `The API reports contract ${reported}; this dashboard supports ${SUPPORTED_CONTRACT_VERSIONS.join(", ")}. Some fields may be missing or misread.`;
}
