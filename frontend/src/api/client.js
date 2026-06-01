import axios from "axios";
import { tokens } from "../auth/tokens.js";

// Base URL for the Django API. Configured per-environment via VITE_API_BASE.
const baseURL = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

// Attach the access token to every request.
api.interceptors.request.use((config) => {
  const access = tokens.access;
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

// On a 401, try a single refresh then replay the original request. If refresh
// fails, clear tokens and let the app redirect to /login.
let refreshing = null;

api.interceptors.response.use(
  (resp) => resp,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    const isAuthCall = original?.url?.includes("/api/auth/");

    if (status === 401 && !original._retry && !isAuthCall && tokens.refresh) {
      original._retry = true;
      try {
        refreshing =
          refreshing ||
          axios.post(`${baseURL}/api/auth/refresh/`, { refresh: tokens.refresh });
        const { data } = await refreshing;
        refreshing = null;
        tokens.set({ access: data.access });
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch (refreshErr) {
        refreshing = null;
        tokens.clear();
        // Force a clean redirect to login.
        if (window.location.pathname !== "/login") {
          window.location.assign("/login");
        }
        return Promise.reject(refreshErr);
      }
    }
    return Promise.reject(error);
  }
);

export default api;
