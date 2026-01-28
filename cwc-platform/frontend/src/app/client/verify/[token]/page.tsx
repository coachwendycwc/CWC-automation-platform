"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { clientAuthApi } from "@/lib/api";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";
import Link from "next/link";

export default function VerifyTokenPage() {
  const params = useParams();
  const router = useRouter();
  const { login } = useClientAuth();
  const token = params.token as string;

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const verifyToken = async () => {
      try {
        const result = await clientAuthApi.verifyToken(token);
        login(result.session_token, result.contact);
        setStatus("success");

        // Redirect to dashboard after brief delay
        setTimeout(() => {
          router.replace("/client/dashboard");
        }, 1500);
      } catch (error: any) {
        setStatus("error");
        setErrorMessage(error.message || "Invalid or expired login link");
      }
    };

    if (token) {
      verifyToken();
    }
  }, [token, login, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-white flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          {status === "loading" && (
            <div className="text-center space-y-4 py-8">
              <Loader2 className="h-12 w-12 text-purple-600 animate-spin mx-auto" />
              <h3 className="text-lg font-semibold">Verifying your login...</h3>
              <p className="text-gray-500">Please wait a moment</p>
            </div>
          )}

          {status === "success" && (
            <div className="text-center space-y-4 py-8">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-green-700">
                Login successful!
              </h3>
              <p className="text-gray-600">Redirecting to your dashboard...</p>
            </div>
          )}

          {status === "error" && (
            <div className="text-center space-y-4 py-8">
              <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                <XCircle className="h-8 w-8 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-red-700">Login failed</h3>
              <p className="text-gray-600">{errorMessage}</p>
              <Link href="/client/login">
                <Button className="mt-4">Request new login link</Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
