const FALLBACK_STORAGE_KEY = "anonymous_user_id";
export const ANONYMOUS_ID_HEADER = "X-Anonymous-Id";


export function readStoredAnonymousId(): string | null {
  try {
    return sessionStorage.getItem(FALLBACK_STORAGE_KEY);
  } catch {
    return null;
  }
}


export function storeAnonymousId(userId: string): void {
  try {
    sessionStorage.setItem(FALLBACK_STORAGE_KEY, userId);
  } catch {
    // If storage is unavailable we silently continue with cookie-only mode.
  }
}
