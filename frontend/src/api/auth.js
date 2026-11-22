import apiClient from "./client";

export const registerUser = (username, email, password) => {
  return apiClient.post("/users/auth/register", { username, email, password });
};

export const loginUser = (email, password) => {
  return apiClient.post("/users/auth/login", { email, password });
};

// Tells the server to revoke the refresh token, so logout is real (not just local).
export const logoutUser = (refreshToken) => {
  return apiClient.post("/users/auth/logout", { refresh_token: refreshToken });
};

export const getCurrentUser = () => {
  return apiClient.get("/users/auth/me");
};
