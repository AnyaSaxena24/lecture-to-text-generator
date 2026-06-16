const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RequestOptions extends RequestInit {
  token?: string | null;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  
  const headers = new Headers(options.headers || {});
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 204) {
    return {} as T;
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "An error occurred" }));
    throw new Error(errorData.detail || "Request failed");
  }

  return res.json();
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) => 
    request<T>(path, { ...options, method: "GET" }),
    
  post: <T>(path: string, body: any, options?: RequestOptions) => 
    request<T>(path, { 
      ...options, 
      method: "POST", 
      body: body instanceof FormData ? body : JSON.stringify(body) 
    }),
    
  delete: <T>(path: string, options?: RequestOptions) => 
    request<T>(path, { ...options, method: "DELETE" }),

  getBlob: async (path: string): Promise<Blob> => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const headers = new Headers();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    
    const res = await fetch(`${API_URL}${path}`, { headers });
    if (!res.ok) {
      throw new Error("Failed to download file");
    }
    return res.blob();
  }
};
