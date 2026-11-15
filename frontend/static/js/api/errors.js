/** Error raised by every data adapter. Mirrors contracts/schemas/error.schema.json. */
export class ApiError extends Error {
  /**
   * @param {number} status  HTTP status, or 0 for network failure.
   * @param {string} code    e.g. not_implemented, not_found, network_error.
   * @param {string} message
   */
  constructor(status, code, message) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

/** True when the backend says the endpoint is planned but not built (HTTP 501). */
export function isNotImplemented(err) {
  return err instanceof ApiError && (err.status === 501 || err.code === "not_implemented");
}

/**
 * Build an ApiError from a non-2xx response, reading the contract Error body
 * when present.
 * @param {Response} res
 */
export async function errorFromResponse(res) {
  let code = `http_${res.status}`;
  let message = `Request failed with HTTP ${res.status}.`;
  try {
    const body = await res.json();
    if (body && body.error && typeof body.error.code === "string") {
      code = body.error.code;
      if (typeof body.error.message === "string") message = body.error.message;
    }
  } catch {
    // Body was not JSON; keep the generic message.
  }
  return new ApiError(res.status, code, message);
}
