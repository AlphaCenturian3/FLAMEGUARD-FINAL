// Runtime configuration from the page URL.
//
//   ?source=api        (default) talk to the backend at the same origin
//   ?source=fixtures   read contracts/examples/ (labelled, not NASA data)
//   ?api=http://host   API base URL when not same-origin
//   ?fixtures=URL      location of contracts/examples/ (default ../contracts/examples/)

import { createFixtureSource } from "./api/fixtures.js";
import { createHttpSource } from "./api/http.js";

export const CONTRACT_VERSION = "0.1.0";

/** @param {string} [href] */
export function readConfig(href = window.location.href) {
  const url = new URL(href);
  const params = url.searchParams;
  const source = params.get("source") === "fixtures" ? "fixtures" : "api";
  return {
    source,
    apiBase: params.get("api") || "",
    fixturesBase: params.get("fixtures") || new URL("../contracts/examples/", url).href,
  };
}

/** @param {ReturnType<typeof readConfig>} config */
export function createDataSource(config) {
  return config.source === "fixtures"
    ? createFixtureSource({ baseUrl: config.fixturesBase })
    : createHttpSource({ baseUrl: config.apiBase });
}

/** URL of the current page switched to the given source. */
export function urlWithSource(source, href = window.location.href) {
  const url = new URL(href);
  if (source === "api") url.searchParams.delete("source");
  else url.searchParams.set("source", source);
  return url.href;
}
