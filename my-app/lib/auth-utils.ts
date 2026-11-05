/**
 * Validates and normalizes redirect URLs to strictly enforce same-site relative paths.
 * Blocks open-redirect attacks like:
 * - https://evil.com
 * - //evil.com
 * - javascript:...
 * Complies with TrustLens_PRD_v1.1 FR-A5 and Auth Checklist Item 4.
 */
export function getSafeRedirectUrl(nextParam: string | null | undefined, fallback: string = '/dashboard'): string {
  if (!nextParam) return fallback;

  // Trim and decode
  const trimmed = nextParam.trim();

  // Reject protocol-relative URLs (e.g. //evil.com) and absolute URIs (e.g. https://evil.com, javascript:)
  if (
    trimmed.startsWith('/') &&
    !trimmed.startsWith('//') &&
    !trimmed.startsWith('/\\') &&
    !trimmed.includes('://')
  ) {
    return trimmed;
  }

  return fallback;
}
