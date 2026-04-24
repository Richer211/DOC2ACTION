export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export const JWT_STORAGE_KEY = "doc2action_jwt";
export const JWT_USER_STORAGE_KEY = "doc2action_jwt_user";

/** 优先 session 中的 JWT；否则 NEXT_PUBLIC_DOC2ACTION_API_KEY（勿提交）。 */
export function apiHeaders(extra?: Record<string, string>): Record<string, string> {
  const h: Record<string, string> = { ...extra };
  if (typeof window !== "undefined") {
    const jwt = sessionStorage.getItem(JWT_STORAGE_KEY);
    if (jwt) {
      h["Authorization"] = `Bearer ${jwt}`;
      return h;
    }
  }
  const key = process.env.NEXT_PUBLIC_DOC2ACTION_API_KEY;
  if (key) {
    h["X-API-Key"] = key;
  }
  return h;
}

export async function readErrorMessage(response: Response): Promise<string> {
  const base = `HTTP ${response.status}`;
  try {
    const data: unknown = await response.json();
    if (data && typeof data === "object" && "detail" in data) {
      const d = (data as { detail: unknown }).detail;
      if (typeof d === "string") {
        return `${base}: ${d}`;
      }
      if (
        d &&
        typeof d === "object" &&
        "message" in d &&
        typeof (d as { message: unknown }).message === "string"
      ) {
        return `${base}: ${(d as { message: string }).message}`;
      }
    }
  } catch {
    /* ignore non-JSON body */
  }
  return base;
}
