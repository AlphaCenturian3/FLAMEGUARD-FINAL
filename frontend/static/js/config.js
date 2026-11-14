// Runtime configuration from the page URL (spec §5.3).
//
//   (default)            talk to the backend at the same origin
//   ?fixtures=1          read contracts/examples/ (labelled FIXTURE DATA. NOT NASA DATA.)
//   ?api=http://host     API base URL when not same-origin
//   ?fixtures_base=URL   location of contracts/examples/ (default ../contracts/examples/)

import { createFixtureSource } from "./api/fixtures.js";
import { createHttpSource } from "./api/http.js";

/** Contract version this dashboard implements. */
export const CONTRACT_VERSION = "0.2.0";
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
  if (typeof reported !== "string" || reported === CONTRACT_VERSION) return null;
  return `The API reports contract ${reported}; this dashboard implements ${CONTRACT_VERSION}. Some fields may be missing or misread.`;
}
