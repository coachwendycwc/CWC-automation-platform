"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle, Calendar } from "lucide-react";

export default function ThankYouPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 flex items-center justify-center p-4">
      <Card className="max-w-lg w-full">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <CardTitle className="text-2xl">Thank You!</CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-6">
          <p className="text-gray-600">
            Your organizational needs assessment has been submitted successfully.
            We're excited to learn more about your goals and explore how we can partner together.
          </p>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-center justify-center gap-2 text-purple-700 mb-2">
              <Calendar className="w-5 h-5" />
              <span className="font-semibold">Next Step</span>
            </div>
            <p className="text-purple-600 text-sm">
              Book a discovery call so we can review your responses and co-create the best solution.
            </p>
          </div>

          <div className="pt-4">
            <Link href="/book/discovery-call">
              <Button className="w-full bg-purple-600 hover:bg-purple-700">
                Book Discovery Call
              </Button>
            </Link>
          </div>

          <p className="text-sm text-gray-500">
            Questions? Email us at{" "}
            <a href="mailto:info@coachingwomenofcolor.com" className="text-purple-600 hover:underline">
              info@coachingwomenofcolor.com
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
