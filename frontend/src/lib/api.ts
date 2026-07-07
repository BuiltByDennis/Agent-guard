const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch(input: string, init?: RequestInit) {
  const headers = new Headers(init?.headers);
  
  // Extract CSRF token from non-HttpOnly cookie if present
  let csrfToken = null;
  if (typeof document !== 'undefined') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith('csrf_token=')) {
        csrfToken = cookie.substring('csrf_token='.length, cookie.length);
        break;
      }
    }
  }

  // Attach CSRF token for state-changing requests
  const method = (init?.method || 'GET').toUpperCase();
  if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    headers.set('X-CSRF-Token', csrfToken);
  }
  
  const url = input.startsWith("http") ? input : `${API_BASE}${input}`;
  
  // Always include credentials so HttpOnly cookies are sent
  let response = await fetch(url, { ...init, headers, credentials: "include" });
  
  if (response.status === 401 && !input.includes("/auth/token") && !input.includes("/auth/refresh")) {
    try {
      const refreshRes = await fetch(`${API_BASE}/v1/auth/refresh`, {
        method: "POST",
        credentials: "include"
      });
      if (refreshRes.ok) {
        // CSRF cookie might have been updated, let's grab the latest one before retrying
        let newCsrfToken = null;
        if (typeof document !== 'undefined') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith('csrf_token=')) {
              newCsrfToken = cookie.substring('csrf_token='.length, cookie.length);
              break;
            }
          }
        }
        if (newCsrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
          headers.set('X-CSRF-Token', newCsrfToken);
        }
        
        response = await fetch(url, { ...init, headers, credentials: "include" });
      } else {
        if (typeof window !== "undefined") window.location.href = "/login";
      }
    } catch {
      if (typeof window !== "undefined") window.location.href = "/login";
    }
  }
  return response;
}
