// src/lib/apiClient.ts

const API_URL = import.meta.env.VITE_API_URL;

export async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include", // 🔥 REQUIRED FOR SESSION COOKIES
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  // For /me, backend returns 401 if not logged in → treat as error
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}
