"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { publicInvoiceApi } from "@/lib/api";
import { ArrowLeft, Calendar, CheckCircle, Clock3, ExternalLink, Video } from "lucide-react";
import Link from "next/link";
import type { PublicInvoice } from "@/types";

export default function PaymentSuccessPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const [invoice, setInvoice] = useState<PublicInvoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const sessionId = searchParams.get("session_id");

  useEffect(() => {
    if (params.token) {
      void loadInvoice(params.token as string, true);
    }
  }, [params.token]);

  const loadInvoice = async (token: string, retryUntilPaid = false) => {
    try {
      let data = await publicInvoiceApi.get(token);
      setInvoice(data);

      if (retryUntilPaid && data.status !== "paid") {
        setRefreshing(true);
        for (let attempt = 0; attempt < 4; attempt += 1) {
          await new Promise((resolve) => window.setTimeout(resolve, 1500));
          data = await publicInvoiceApi.get(token);
          setInvoice(data);
          if (data.status === "paid") {
            break;
          }
        }
      }
    } catch {
      // Invoice might take a moment to update after webhook
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const formatDateTime = (dateString: string) =>
    new Date(dateString).toLocaleString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });

  if (loading) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center">
        <div className="max-w-lg w-full mx-auto px-4">
          <Skeleton className="h-64 rounded-lg" />
        </div>
      </div>
    );
  }

  const isPaid = invoice?.status === "paid";
  const primaryLineItem = invoice?.line_items?.[0];
  const booking = invoice?.booking;

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
              {isPaid ? "Payment received" : "Payment processing"}
            </h1>

            <p className="text-muted-foreground mb-6">
              {isPaid
                ? "Your payment has been received and your booking is confirmed."
                : "Your payment was submitted. We are finalizing your booking confirmation now."}
            </p>

            {refreshing && !isPaid && (
              <div className="mb-6 flex items-center justify-center gap-2 rounded-lg border border-border bg-muted/60 px-4 py-3 text-sm text-muted-foreground">
                <Clock3 className="h-4 w-4" />
                Waiting for payment confirmation to finish syncing...
              </div>
            )}

            {invoice && (
              <div className="bg-muted rounded-lg p-4 mb-6 text-left">
                <div className="space-y-2">
                  {primaryLineItem && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Session</span>
                      <span className="font-medium">{primaryLineItem.description}</span>
                    </div>
                  )}
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
                  {invoice.memo && (
                    <div className="mt-3 border-t border-border pt-3">
                      <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">Confirmation</p>
                      <p className="text-sm">{invoice.memo}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {booking && (
              <div className="mb-6 rounded-lg border border-border bg-background p-4 text-left">
                <div className="mb-3 text-xs uppercase tracking-wide text-muted-foreground">
                  Booking status
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">Session</span>
                    <span className="font-medium">{booking.booking_type_name}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">Status</span>
                    <span className="font-medium capitalize">{booking.status}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">When</span>
                    <span className="font-medium text-right">{formatDateTime(booking.start_time)}</span>
                  </div>
                  {booking.meeting_url && (
                    <div className="pt-2">
                      <a
                        href={booking.meeting_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-2 text-primary hover:underline"
                      >
                        <Video className="h-4 w-4" />
                        Open meeting link
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="space-y-3">
              <Link href={`/pay/${params.token}`}>
                <Button variant="outline" className="w-full cursor-pointer">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  View receipt
                </Button>
              </Link>
              {booking?.confirmation_token && (
                <Link href={`/book/manage/${booking.confirmation_token}`}>
                  <Button variant="outline" className="w-full cursor-pointer">
                    Manage booking
                  </Button>
                </Link>
              )}
              {booking?.meeting_url && (
                <a href={booking.meeting_url} target="_blank" rel="noreferrer">
                  <Button className="w-full cursor-pointer">
                    <Calendar className="h-4 w-4 mr-2" />
                    Go to meeting link
                  </Button>
                </a>
              )}
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
