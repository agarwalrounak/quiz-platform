import { createContext, useContext, useEffect, useMemo, useState } from "react";
import api from "../api/client.js";
import { tokens } from "./tokens.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On first load, if we have a token, resolve the current user.
  useEffect(() => {
    let active = true;
    if (!tokens.access) {
      setLoading(false);
      return;
    }
    api
      .get("/api/auth/me/")
      .then((res) => active && setUser(res.data))
      .catch(() => {
        tokens.clear();
        if (active) setUser(null);
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  async function login(username, password) {
    const { data } = await api.post("/api/auth/login/", { username, password });
    tokens.set({ access: data.access, refresh: data.refresh });
    setUser(data.user);
    return data.user;
  }

  async function register(username, email, password) {
    await api.post("/api/auth/register/", { username, email, password });
    return login(username, password);
  }

  function logout() {
    tokens.clear();
    setUser(null);
  }

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: !!user,
      isAdmin: user?.role === "admin",
      login,
      register,
      logout,
    }),
    [user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
