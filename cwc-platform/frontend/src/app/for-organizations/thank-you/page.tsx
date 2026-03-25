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
          <div className="mx-auto w-16 h-16 bg-success/10 rounded-full flex items-center justify-center mb-4">
            <CheckCircle className="w-10 h-10 text-success" />
          </div>
          <CardTitle className="text-2xl">Thank You!</CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-6">
          <p className="text-muted-foreground">
            Your organizational needs assessment has been submitted successfully.
            We're excited to learn more about your goals and explore how we can partner together.
          </p>

          <div className="bg-accent/10 border border-accent/20 rounded-lg p-4">
            <div className="flex items-center justify-center gap-2 text-accent mb-2">
              <Calendar className="w-5 h-5" />
              <span className="font-semibold">Next Step</span>
            </div>
            <p className="text-muted-foreground text-sm">
              Book a discovery call so we can review your responses and co-create the best solution.
            </p>
          </div>

          <div className="pt-4">
            <Link href="/book/discovery-call">
              <Button className="w-full bg-purple-600 hover:bg-purple-700 cursor-pointer">
                Book Discovery Call
              </Button>
            </Link>
          </div>

          <p className="text-sm text-muted-foreground">
            Questions? Email us at{" "}
            <a href="mailto:info@coachingwomenofcolor.com" className="text-primary hover:text-primary/80">
              info@coachingwomenofcolor.com
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
