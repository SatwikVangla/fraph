function resolveApiBaseUrl() {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  if (configuredBaseUrl) {
    return configuredBaseUrl.replace(/\/$/, "");
  }

  if (typeof window === "undefined") {
    return "";
  }

  const { protocol, hostname, port } = window.location;
  if (port && port !== "8000") {
    return `${protocol}//${hostname}:8000`;
  }

  return `${protocol}//${hostname}${port ? `:${port}` : ""}`;
}

export const API_BASE_URL = resolveApiBaseUrl();

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const contentType = response.headers.get("content-type") ?? "";

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

  if (!contentType.includes("application/json")) {
    throw new Error(
      `Expected JSON from ${path}, but received ${contentType || "an unknown response type"}. Check VITE_API_BASE_URL or backend routing.`,
    );
  }

  return response.json();
}
