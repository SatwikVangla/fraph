const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const payload = await response.json();
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Keep the fallback message when the response is not JSON.
    }

    throw new Error(message);
  }

  return response.json();
}
