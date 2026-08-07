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


export function togglePw(id, btn) {
  const input = document.getElementById(id);
  const isHidden = input.type === 'password';
  input.type = isHidden ? 'text' : 'password';
  
  btn.innerHTML = isHidden ? `<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 2l12 12M6.5 6.6A2 2 0 0110 9.5M4.2 4.3C2.6 5.4 1 8 1 8s2.5 5 7 5a7 7 0 003.8-1.2M6 3.1A7 7 0 0115 8s-.8 1.7-2.2 3"/></svg>` : `<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 8s2.5-5 7-5 7 5 7 5-2.5 5-7 5-7-5-7-5z"/><circle cx="8" cy="8" r="2"/></svg>`;
}