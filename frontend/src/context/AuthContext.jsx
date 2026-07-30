import { createContext, useContext, useState, useEffect } from "react";
import { decodeToken } from "../utils/jwt";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => sessionStorage.getItem("token"));
  const [user, setUser] = useState(() => {
    const existingToken = sessionStorage.getItem("token");
    return existingToken ? decodeToken(existingToken) : null;
  });

  useEffect(() => {
    if (token) {
      sessionStorage.setItem("token", token);
      setUser(decodeToken(token));
    } else {
      sessionStorage.removeItem("token");
      setUser(null);
    }
  }, [token]);

  const login = (accessToken) => {
    setToken(accessToken); // user gets set automatically by the effect above
  };

  const logout = () => {
    setToken(null);
  };

  const value = {
    token,
    user,
    isAuthenticated: !!token,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}