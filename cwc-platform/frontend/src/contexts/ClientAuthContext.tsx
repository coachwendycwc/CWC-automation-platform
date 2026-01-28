"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { clientAuthApi } from "@/lib/api";

interface ClientContact {
  id: string;
  first_name: string;
  last_name: string | null;
  email: string | null;
  organization_id: string | null;
  organization_name: string | null;
  organization_logo_url: string | null;
  is_org_admin: boolean;
}

interface ClientAuthContextType {
  contact: ClientContact | null;
  sessionToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isOrgAdmin: boolean;
  login: (sessionToken: string, contact: ClientContact) => void;
  logout: () => Promise<void>;
}

const ClientAuthContext = createContext<ClientAuthContextType | undefined>(undefined);

const CLIENT_SESSION_KEY = "client_session_token";

export function ClientAuthProvider({ children }: { children: ReactNode }) {
  const [contact, setContact] = useState<ClientContact | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const isOrgAdmin = !!(contact?.is_org_admin && contact?.organization_id);

  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = localStorage.getItem(CLIENT_SESSION_KEY);

        if (storedToken) {
          try {
            const contactData = await clientAuthApi.getMe(storedToken);
            setContact(contactData);
            setSessionToken(storedToken);
          } catch (error) {
            // Session expired or invalid
            localStorage.removeItem(CLIENT_SESSION_KEY);
          }
        }
      } catch (error) {
        console.error("Auth init error:", error);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  // Redirect unauthenticated users to login (except for login/verify pages)
  useEffect(() => {
    if (!isLoading && !contact && pathname) {
      const publicPaths = ["/client/login", "/client/verify"];
      const isPublicPath = publicPaths.some((p) => pathname.startsWith(p));

      if (pathname.startsWith("/client") && !isPublicPath) {
        router.replace("/client/login");
      }
    }
  }, [isLoading, contact, pathname, router]);

  const login = (token: string, contactData: ClientContact) => {
    localStorage.setItem(CLIENT_SESSION_KEY, token);
    setSessionToken(token);
    setContact(contactData);
  };

  const logout = async () => {
    if (sessionToken) {
      try {
        await clientAuthApi.logout(sessionToken);
      } catch (error) {
        // Ignore logout errors
      }
    }

    localStorage.removeItem(CLIENT_SESSION_KEY);
    setSessionToken(null);
    setContact(null);
    router.replace("/client/login");
  };

  return (
    <ClientAuthContext.Provider
      value={{
        contact,
        sessionToken,
        isLoading,
        isAuthenticated: !!contact,
        isOrgAdmin,
        login,
        logout,
      }}
    >
      {children}
    </ClientAuthContext.Provider>
  );
}

export function useClientAuth() {
  const context = useContext(ClientAuthContext);
  if (context === undefined) {
    throw new Error("useClientAuth must be used within a ClientAuthProvider");
  }
  return context;
}
