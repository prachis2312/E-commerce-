import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL;

// ---------------------------------------------------------------------------
// Token storage. Access token = short-lived (15 min). Refresh token = long-lived
// (7 days) and is the thing that keeps you "logged in" like a normal website.
// localStorage (not sessionStorage) so the session survives closing the tab.
// ---------------------------------------------------------------------------
const ACCESS_KEY = "token";
const REFRESH_KEY = "refresh_token";

export const tokenStore = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set(access, refresh) {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
    window.dispatchEvent(new Event("auth:changed"));
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    window.dispatchEvent(new Event("auth:changed"));
  },
};

const apiClient = axios.create({ baseURL: API_URL });

apiClient.interceptors.request.use((config) => {
  const token = tokenStore.getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------------------------------------------------------------------------
// Silent refresh. When any call gets a 401 (access token expired), we:
//   1. exchange the refresh token for a new pair (ONE refresh at a time -
//      the backend rotates tokens, so two parallel refreshes would look like
//      token theft and kill the session),
//   2. retry the original request with the new access token,
//   3. only if the refresh itself fails do we log the user out.
// ---------------------------------------------------------------------------
let refreshPromise = null;

function refreshTokens() {
  if (!refreshPromise) {
    const refreshToken = tokenStore.getRefresh();
    if (!refreshToken) return Promise.reject(new Error("No refresh token"));

    // Plain axios (not apiClient) so this call can't trigger the interceptor again.
    refreshPromise = axios
      .post(`${API_URL}/users/auth/refresh`, { refresh_token: refreshToken })
      .then((res) => {
        tokenStore.set(res.data.access_token, res.data.refresh_token);
        return res.data.access_token;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

function endSession() {
  tokenStore.clear();
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    const isAuthEndpoint = original?.url?.includes("/auth/login") || original?.url?.includes("/auth/refresh");

    // Not a token problem, already retried once, or a login attempt -> pass the error on.
    if (status !== 401 || !original || original._retried || isAuthEndpoint) {
      return Promise.reject(error);
    }

    // Guest (never logged in): nothing to refresh, let the page handle the 401.
    if (!tokenStore.getRefresh()) {
      return Promise.reject(error);
    }

    original._retried = true;

    try {
      // Another browser tab may already have refreshed and stored a newer token.
      const current = tokenStore.getAccess();
      const sentWith = original.headers?.Authorization;
      const newAccess =
        current && sentWith !== `Bearer ${current}` ? current : await refreshTokens();

      original.headers.Authorization = `Bearer ${newAccess}`;
      return apiClient(original);
    } catch {
      endSession();
      return Promise.reject(error);
    }
  }
);

export default apiClient;
