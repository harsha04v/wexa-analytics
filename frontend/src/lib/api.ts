import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const orgId = localStorage.getItem("org_id");
  if (orgId) {
    config.headers["X-Organization-ID"] = orgId;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("org_id");
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// --- Auth ---
export const authApi = {
  signUp: (data: { email: string; password: string; full_name: string; organization_name: string }) =>
    api.post("/auth/signup", data),
  signIn: (data: { email: string; password: string }) =>
    api.post("/auth/signin", data),
  refresh: (refresh_token: string) =>
    api.post("/auth/refresh", { refresh_token }),
  me: () => api.get("/auth/me"),
  organizations: () => api.get("/auth/organizations"),
  members: () => api.get("/auth/members"),
  invite: (data: { email: string; role: string }) =>
    api.post("/auth/invite", data),
  acceptInvite: (data: { token: string; password: string; full_name: string }) =>
    api.post("/auth/accept-invite", data),
};

// --- Ingestion ---
export const ingestionApi = {
  createApiKey: (data: { name: string }) =>
    api.post("/ingestion/api-keys", data),
  listApiKeys: () => api.get("/ingestion/api-keys"),
  revokeApiKey: (id: string) => api.delete(`/ingestion/api-keys/${id}`),
  listDataSources: () => api.get("/ingestion/data-sources"),
  createDataSource: (data: { name: string; source_type: string; config?: object }) =>
    api.post("/ingestion/data-sources", data),
  listJobs: () => api.get("/ingestion/jobs"),
  getJob: (id: string) => api.get(`/ingestion/jobs/${id}`),
  uploadCsv: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/ingestion/upload-csv", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// --- Dashboards ---
export const dashboardApi = {
  list: () => api.get("/dashboards"),
  get: (id: string) => api.get(`/dashboards/${id}`),
  create: (data: { name: string; description?: string }) =>
    api.post("/dashboards", data),
  update: (id: string, data: { name?: string; description?: string }) =>
    api.patch(`/dashboards/${id}`, data),
  delete: (id: string) => api.delete(`/dashboards/${id}`),
  togglePublic: (id: string) => api.post(`/dashboards/${id}/toggle-public`),
  getPublic: (token: string) => api.get(`/dashboards/public/${token}`),
  // Widgets
  createWidget: (dashId: string, data: object) =>
    api.post(`/dashboards/${dashId}/widgets`, data),
  updateWidget: (dashId: string, widgetId: string, data: object) =>
    api.patch(`/dashboards/${dashId}/widgets/${widgetId}`, data),
  deleteWidget: (dashId: string, widgetId: string) =>
    api.delete(`/dashboards/${dashId}/widgets/${widgetId}`),
  updateLayout: (dashId: string, layouts: object[]) =>
    api.put(`/dashboards/${dashId}/layout`, { layouts }),
  // Analytics
  timeSeries: (params: Record<string, string>) =>
    api.get("/dashboards/analytics/time-series", { params }),
  topEvents: (params: Record<string, string>) =>
    api.get("/dashboards/analytics/top-events", { params }),
  kpi: (params: Record<string, string>) =>
    api.get("/dashboards/analytics/kpi", { params }),
};
