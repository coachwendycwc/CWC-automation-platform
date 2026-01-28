"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { authApi } from "@/lib/api";

interface User {
  id: string;
  email: string;
  name: string | null;
  role: string;
  avatar_url: string | null;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  devLogin: (email?: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Routes that don't require authentication
const publicRoutes = [
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
  "/book",
  "/sign",
  "/pay",
  "/client",
  "/feedback",
  "/testimonial",
];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // Check if current route is public
  const isPublicRoute = publicRoutes.some((route) => pathname?.startsWith(route));

  useEffect(() => {
    // Load token from localStorage on mount
    const savedToken = localStorage.getItem("token");
    if (savedToken) {
      setToken(savedToken);
      // Verify token and get user
      authApi
        .getMe(savedToken)
        .then((userData) => {
          setUser(userData);
          setIsLoading(false);
        })
        .catch(() => {
          // Token invalid, clear it
          localStorage.removeItem("token");
          setToken(null);
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, []);

  // Redirect to login if not authenticated and on protected route
  useEffect(() => {
    if (!isLoading && !token && !isPublicRoute && pathname !== "/") {
      router.push("/login");
    }
  }, [isLoading, token, isPublicRoute, pathname, router]);

  const login = async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    localStorage.setItem("token", response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    router.push("/dashboard");
  };

  const devLogin = async (email?: string) => {
    const response = await authApi.devLogin(email);
    localStorage.setItem("token", response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    router.push("/dashboard");
  };

  const register = async (email: string, password: string, name: string) => {
    const response = await authApi.register(email, password, name);
    localStorage.setItem("token", response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    router.push("/dashboard");
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!token,
        login,
        devLogin,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
