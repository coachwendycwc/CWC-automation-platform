"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { clientAuthApi } from "@/lib/api";
import { Mail, CheckCircle, ArrowRight } from "lucide-react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { useEffect } from "react";
import Image from "next/image";

export default function ClientLoginPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const { isAuthenticated, isLoading } = useClientAuth();
  const router = useRouter();

  // Redirect if already authenticated
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/client/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email) {
      toast.error("Please enter your email address");
      return;
    }

    setLoading(true);

    try {
      await clientAuthApi.requestLogin(email);
      setEmailSent(true);
      toast.success("Check your email for the login link!");
    } catch (error: any) {
      if (error.status === 429) {
        toast.error("Too many requests. Please try again later.");
      } else {
        toast.error(error.message || "Failed to send login link");
      }
    } finally {
      setLoading(false);
    }
  };

  // Don't show loading state - just render the login form immediately
  // The useEffect will redirect if already authenticated once loading completes
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-white flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4">
            <Image
              src="/images/logo.png"
              alt="Coaching Women of Color"
              width={180}
              height={60}
              className="h-14 w-auto"
              priority
            />
          </div>
          <CardTitle className="text-2xl">Client Portal</CardTitle>
          <CardDescription>
            Access your invoices, contracts, bookings, and more
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!emailSent ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10"
                    disabled={loading}
                    autoFocus
                  />
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? (
                  "Sending..."
                ) : (
                  <>
                    Send Login Link
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>

              <p className="text-center text-sm text-gray-500">
                We&apos;ll send you a magic link to sign in instantly.
              </p>
            </form>
          ) : (
            <div className="text-center space-y-4 py-4">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold">Check your email</h3>
              <p className="text-gray-600">
                We sent a login link to <strong>{email}</strong>
              </p>
              <p className="text-sm text-gray-500">
                The link will expire in 15 minutes.
              </p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => {
                  setEmailSent(false);
                  setEmail("");
                }}
              >
                Use a different email
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
