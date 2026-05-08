const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem("token");
  
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error?.message || "An unexpected error occurred");
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  get: (endpoint: string) => apiFetch(endpoint, { method: "GET" }),
  post: (endpoint: string, body: any) => apiFetch(endpoint, { method: "POST", body: JSON.stringify(body) }),
  patch: (endpoint: string, body: any) => apiFetch(endpoint, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (endpoint: string) => apiFetch(endpoint, { method: "DELETE" }),
};
