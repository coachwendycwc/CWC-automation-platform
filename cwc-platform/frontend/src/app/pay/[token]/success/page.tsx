"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { publicInvoiceApi } from "@/lib/api";
import { CheckCircle, Download, ArrowLeft } from "lucide-react";
import Link from "next/link";

interface PublicInvoice {
  invoice_number: string;
  total: number;
  amount_paid: number;
  balance_due: number;
  status: string;
  contact_name: string;
  organization_name: string | null;
}

export default function PaymentSuccessPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const [invoice, setInvoice] = useState<PublicInvoice | null>(null);
  const [loading, setLoading] = useState(true);

  const sessionId = searchParams.get("session_id");

  useEffect(() => {
    if (params.token) {
      loadInvoice(params.token as string);
    }
  }, [params.token]);

  const loadInvoice = async (token: string) => {
    try {
      const data = await publicInvoiceApi.get(token);
      setInvoice(data);
    } catch {
      // Invoice might take a moment to update after webhook
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center">
        <div className="max-w-lg w-full mx-auto px-4">
          <Skeleton className="h-64 rounded-lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted py-12 px-4">
      <div className="max-w-lg mx-auto">
        <Card>
          <CardContent className="py-12 text-center">
            <div className="mb-6">
              <div className="mx-auto w-16 h-16 bg-success/10 rounded-full flex items-center justify-center">
                <CheckCircle className="h-10 w-10 text-success" />
              </div>
            </div>

            <h1 className="text-2xl font-bold text-foreground mb-2">
              Payment Successful!
            </h1>

            <p className="text-muted-foreground mb-6">
              Thank you for your payment. A confirmation email has been sent.
            </p>

            {invoice && (
              <div className="bg-muted rounded-lg p-4 mb-6 text-left">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Invoice</span>
                    <span className="font-medium">{invoice.invoice_number}</span>
                  </div>
                  {invoice.status === "paid" ? (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Amount Paid</span>
                      <span className="font-medium text-success">
                        {formatCurrency(invoice.total)}
                      </span>
                    </div>
                  ) : (
                    <>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Total</span>
                        <span className="font-medium">
                          {formatCurrency(invoice.total)}
                        </span>
                      </div>
                      {invoice.balance_due > 0 && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Remaining Balance</span>
                          <span className="font-medium">
                            {formatCurrency(invoice.balance_due)}
                          </span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="space-y-3">
              <Link href={`/pay/${params.token}`}>
                <Button variant="outline" className="w-full cursor-pointer">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  View Invoice
                </Button>
              </Link>
            </div>

            {sessionId && (
              <p className="text-sm text-muted-foreground mt-6">
                Reference: {sessionId.substring(0, 20)}...
              </p>
            )}
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-muted-foreground">
          <p>Questions? Contact us at support@cwc-coaching.com</p>
          <p className="mt-1">CWC Coaching - Empowering Women of Color in Leadership</p>
        </div>
      </div>
    </div>
  );
}
