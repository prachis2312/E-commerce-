import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

// Runs before every request this instance sends.
// Reads the JWT from sessionStorage and attaches it as a Bearer token,
// so individual API files (auth.js, products.js, etc.) never have to
// handle auth headers themselves.
apiClient.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;