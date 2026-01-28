"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useClientAuth } from "@/contexts/ClientAuthContext";

export default function ClientPage() {
  const { isAuthenticated, isLoading } = useClientAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        router.replace("/client/dashboard");
      } else {
        router.replace("/client/login");
      }
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-gray-500">Redirecting...</div>
    </div>
  );
}
