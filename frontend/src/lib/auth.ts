const TOKEN_KEY = "debtsense_access_token";
const REFRESH_TOKEN_KEY = "debtsense_refresh_token";

export interface StoredUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

/**
 * Retrieve the stored access token.
 */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Persist the access token in localStorage.
 */
export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Remove the access token from localStorage.
 */
export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Retrieve the stored refresh token.
 */
export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Persist the refresh token in localStorage.
 */
export function setRefreshToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
}

/**
 * Remove the refresh token from localStorage.
 */
export function removeRefreshToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Store both tokens at once (e.g. after login/register).
 */
export function setAuthTokens(tokens: AuthTokens): void {
  setToken(tokens.access_token);
  setRefreshToken(tokens.refresh_token);
}

/**
 * Clear all auth-related data from localStorage.
 */
export function clearAuth(): void {
  removeToken();
  removeRefreshToken();
  if (typeof window !== "undefined") {
    localStorage.removeItem("debtsense_user");
  }
}

/**
 * Check whether the user is currently authenticated (has a stored token).
 * Note: This does NOT validate token expiration on the client.
 */
export function isAuthenticated(): boolean {
  return getToken() !== null;
}

/**
 * Store user info in localStorage for quick access.
 */
export function setStoredUser(user: StoredUser): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("debtsense_user", JSON.stringify(user));
}

/**
 * Retrieve stored user info.
 */
export function getStoredUser(): StoredUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("debtsense_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredUser;
  } catch {
    return null;
  }
}
