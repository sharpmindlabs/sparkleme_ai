// Minimal JWT helpers. We only need to (a) decode the role claim from a real
// server token and (b) mint a demo token when running offline. No verification
// is performed client-side — the server is authoritative in production.

import type { Role } from "../types";

export interface JwtClaims {
  sub?: string;
  email: string;
  name: string;
  role: Role;
  status?: string;
}

function b64urlEncode(s: string): string {
  return btoa(unescape(encodeURIComponent(s)))
    .replace(/=+$/, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
}

function b64urlDecode(s: string): string {
  const pad = s.length % 4 === 0 ? "" : "=".repeat(4 - (s.length % 4));
  const b64 = (s + pad).replace(/-/g, "+").replace(/_/g, "/");
  return decodeURIComponent(escape(atob(b64)));
}

/** Decode the payload of a JWT. Returns null on any malformed token. */
export function decodeJwt(token: string): JwtClaims | null {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    const claims = JSON.parse(b64urlDecode(parts[1])) as JwtClaims;
    if (!claims.role) return null;
    return claims;
  } catch {
    return null;
  }
}

/** Mint an unsigned demo token (offline mode only). */
export function mintDemoToken(claims: JwtClaims): string {
  const header = b64urlEncode(JSON.stringify({ alg: "none", typ: "JWT" }));
  const payload = b64urlEncode(JSON.stringify(claims));
  return `${header}.${payload}.demo`;
}
