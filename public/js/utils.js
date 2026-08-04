// Client-side helpers for working with this app's FastAPI backend.

/**
 * Turns a FastAPI error response into a single display-ready message plus
 * a per-field breakdown, so the same error can drive a Modal.alert, a flash
 * banner, or individual form field messages.
 *
 * Accepts:
 *  - a fetch Response (its JSON body is read and parsed)
 *  - an already-parsed FastAPI error body, e.g. { detail: "..." } or
 *    { detail: [{ loc, msg, type }, ...] } (pydantic validation errors)
 *  - a thrown Error (e.g. fetch() rejecting when the network is down)
 *  - a plain string
 *
 * Always resolves — never throws — so callers can use it directly in a
 * .catch() or right after checking `!response.ok`.
 *
 * @param {Response|Error|object|string} source
 * @returns {Promise<{ message: string, fields: { field: string|null, msg: string }[] }>}
 */
export async function extractError(source) {
  const FALLBACK = 'Something went wrong. Please try again.';

  if (source instanceof Response) {
    let body = null;
    try {
      body = await source.json();
    } catch {
      return { message: source.statusText || FALLBACK, fields: [] };
    }
    return parseBody(body, FALLBACK);
  }

  if (source instanceof Error) {
    return { message: source.message || FALLBACK, fields: [] };
  }

  if (typeof source === 'string') {
    return { message: source.trim() || FALLBACK, fields: [] };
  }

  if (source && typeof source === 'object') {
    return parseBody(source, FALLBACK);
  }

  return { message: FALLBACK, fields: [] };
}

/**
 * Looks up the message for a specific field from extractError()'s `fields`
 * list — handy for highlighting a single input after a form submit.
 *
 * @param {{ field: string|null, msg: string }[]} fields
 * @param {string} name
 * @returns {string|null}
 */
export function getFieldError(fields, name) {
  const match = (fields || []).find((f) => f.field === name);
  return match ? match.msg : null;
}

function parseBody(body, fallback) {
  if (!body || typeof body !== 'object') return { message: fallback, fields: [] };

  const detail = body.detail ?? body.message;

  if (typeof detail === 'string' && detail.trim()) {
    return { message: detail, fields: [] };
  }

  if (Array.isArray(detail) && detail.length) {
    const fields = detail.map((item) => ({
      field: fieldFromLoc(item.loc),
      msg: item.msg || fallback,
    }));
    const message = fields.map((f) => (f.field ? `${f.field}: ${f.msg}` : f.msg)).join('; ');
    return { message: message || fallback, fields };
  }

  return { message: fallback, fields: [] };
}

function fieldFromLoc(loc) {
  if (!Array.isArray(loc) || !loc.length) return null;
  const last = loc[loc.length - 1];
  return typeof last === 'string' ? last : null;
}
