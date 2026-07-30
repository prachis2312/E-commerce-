import apiClient from "./client";

export const registerUser = (username, email, password) => {
  return apiClient.post("/users/auth/register", { username, email, password });
};

export const loginUser = (email, password) => {
  return apiClient.post("/users/auth/login", { email, password });
};

export const getCurrentUser = () => {
  return apiClient.get("/users/auth/me");
};