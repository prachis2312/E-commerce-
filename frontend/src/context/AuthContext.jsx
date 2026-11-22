import { createContext, useContext, useState, useEffect, useMemo } from "react";
import { decodeToken } from "../utils/jwt";
import { tokenStore } from "../api/client";
import { logoutUser } from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => tokenStore.getAccess());

  // The axios interceptor refreshes tokens behind the scenes and announces it
  // with an "auth:changed" event; the "storage" event covers other browser tabs.
  useEffect(() => {
    const sync = () => setToken(tokenStore.getAccess());
    window.addEventListener("auth:changed", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("auth:changed", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  const user = useMemo(() => (token ? decodeToken(token) : null), [token]);

  const login = (accessToken, refreshToken) => {
    tokenStore.set(accessToken, refreshToken);
  };

  const logout = async () => {
    const refreshToken = tokenStore.getRefresh();
    tokenStore.clear(); // log out locally right away
    if (refreshToken) {
      try {
        await logoutUser(refreshToken); // ...and revoke it on the server
      } catch {
        // Server unreachable: the token still expires on its own.
      }
    }
  };

  const value = {
    token,
    user,
    isAuthenticated: !!token,
    isAdmin: !!user?.is_admin,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
