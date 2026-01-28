"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { publicInvoiceApi, stripeApi } from "@/lib/api";
import { AlertTriangle, CheckCircle, CreditCard, Loader2 } from "lucide-react";

interface LineItem {
  description: string;
  quantity: number;
  unit_price: number;
  amount: number;
  service_type?: string;
}

interface PublicInvoice {
  invoice_number: string;
  line_items: LineItem[];
  subtotal: number;
  tax_rate: number | null;
  tax_amount: number;
  discount_amount: number;
  total: number;
  amount_paid: number;
  balance_due: number;
  payment_terms: string;
  due_date: string;
  status: string;
  memo: string | null;
  contact_name: string;
  organization_name: string | null;
  is_overdue: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-800",
  sent: "bg-blue-100 text-blue-800",
  viewed: "bg-purple-100 text-purple-800",
  partial: "bg-yellow-100 text-yellow-800",
  paid: "bg-green-100 text-green-800",
  overdue: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-500",
};

export default function PublicInvoicePage() {
  const params = useParams();
  const [invoice, setInvoice] = useState<PublicInvoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [paying, setPaying] = useState(false);

  useEffect(() => {
    if (params.token) {
      loadInvoice(params.token as string);
    }
  }, [params.token]);

  const loadInvoice = async (token: string) => {
    try {
      const data = await publicInvoiceApi.get(token);
      setInvoice(data);
    } catch (err: any) {
      if (err.status === 410) {
        setError("This invoice has been cancelled.");
      } else if (err.status === 404) {
        setError("Invoice not found. The link may be invalid or expired.");
      } else {
        setError("Failed to load invoice. Please try again later.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePay = async () => {
    if (!params.token) return;

    setPaying(true);
    try {
      // Create Stripe checkout session and redirect
      const result = await stripeApi.createCheckoutByToken(params.token as string);

      if (result.url) {
        // Redirect to Stripe Checkout
        window.location.href = result.url;
      } else {
        throw new Error("Failed to create checkout session");
      }
    } catch (err: any) {
      if (err.message?.includes("not configured")) {
        alert("Online payments are not yet available. Please contact us to arrange payment.");
      } else {
        alert(err.message || "Payment failed. Please try again.");
      }
      setPaying(false);
    }
    // Note: Don't set paying=false on success because we're redirecting
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading invoice...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="py-12 text-center">
            <AlertTriangle className="h-12 w-12 mx-auto text-red-500 mb-4" />
            <h2 className="text-xl font-bold text-gray-900 mb-2">Invoice Not Available</h2>
            <p className="text-gray-500">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!invoice) {
    return null;
  }

  const isPaid = invoice.status === "paid";

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <Image
            src="/images/logo.png"
            alt="Coaching Women of Color"
            width={200}
            height={170}
            className="h-20 w-auto mx-auto mb-2"
          />
          <p className="text-gray-500 mt-1">Invoice</p>
        </div>

        {/* Status Banner */}
        {isPaid && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
            <CheckCircle className="h-6 w-6 text-green-600" />
            <div>
              <p className="font-medium text-green-800">Invoice Paid</p>
              <p className="text-sm text-green-600">Thank you for your payment!</p>
            </div>
          </div>
        )}

        {invoice.is_overdue && !isPaid && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-red-600" />
            <div>
              <p className="font-medium text-red-800">Invoice Overdue</p>
              <p className="text-sm text-red-600">This invoice was due on {formatDate(invoice.due_date)}</p>
            </div>
          </div>
        )}

        <Card>
          <CardHeader className="border-b">
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-xl">{invoice.invoice_number}</CardTitle>
                <p className="text-gray-500 mt-1">Bill To: {invoice.contact_name}</p>
                {invoice.organization_name && (
                  <p className="text-gray-500">{invoice.organization_name}</p>
                )}
              </div>
              <div className="text-right">
                <Badge className={STATUS_COLORS[invoice.status]}>{invoice.status}</Badge>
                <p className="text-sm text-gray-500 mt-2">Due: {formatDate(invoice.due_date)}</p>
              </div>
            </div>
          </CardHeader>

          <CardContent className="py-6">
            {/* Line Items */}
            <table className="w-full">
              <thead className="border-b">
                <tr className="text-left text-xs font-medium text-gray-500 uppercase">
                  <th className="pb-3">Description</th>
                  <th className="pb-3 text-center">Qty</th>
                  <th className="pb-3 text-right">Price</th>
                  <th className="pb-3 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {invoice.line_items.map((item, index) => (
                  <tr key={index}>
                    <td className="py-4">
                      <div className="font-medium text-gray-900">{item.description}</div>
                      {item.service_type && (
                        <div className="text-sm text-gray-500 capitalize">{item.service_type}</div>
                      )}
                    </td>
                    <td className="py-4 text-center text-gray-600">{item.quantity}</td>
                    <td className="py-4 text-right text-gray-600">{formatCurrency(item.unit_price)}</td>
                    <td className="py-4 text-right font-medium">{formatCurrency(item.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Totals */}
            <div className="mt-6 border-t pt-6">
              <div className="flex justify-end">
                <div className="w-64 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Subtotal</span>
                    <span>{formatCurrency(invoice.subtotal)}</span>
                  </div>
                  {invoice.tax_rate && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Tax ({invoice.tax_rate}%)</span>
                      <span>{formatCurrency(invoice.tax_amount)}</span>
                    </div>
                  )}
                  {invoice.discount_amount > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Discount</span>
                      <span className="text-red-500">-{formatCurrency(invoice.discount_amount)}</span>
                    </div>
                  )}
                  <div className="border-t pt-2 flex justify-between font-bold text-lg">
                    <span>Total</span>
                    <span>{formatCurrency(invoice.total)}</span>
                  </div>
                  {invoice.amount_paid > 0 && (
                    <>
                      <div className="flex justify-between text-sm text-green-600">
                        <span>Paid</span>
                        <span>-{formatCurrency(invoice.amount_paid)}</span>
                      </div>
                      <div className="flex justify-between font-bold text-lg">
                        <span>Balance Due</span>
                        <span>{formatCurrency(invoice.balance_due)}</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Memo */}
            {invoice.memo && (
              <div className="mt-6 pt-6 border-t">
                <h4 className="text-sm font-medium text-gray-500 mb-2">Notes</h4>
                <p className="text-gray-700">{invoice.memo}</p>
              </div>
            )}

            {/* Payment Button */}
            {!isPaid && invoice.balance_due > 0 && (
              <div className="mt-8 pt-6 border-t">
                <div className="bg-gray-50 rounded-lg p-6 text-center">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Amount Due: {formatCurrency(invoice.balance_due)}
                  </h3>
                  <p className="text-sm text-gray-500 mb-4">
                    Click below to pay securely with credit card or bank transfer
                  </p>
                  <Button size="lg" onClick={handlePay} disabled={paying}>
                    {paying ? (
                      <>
                        <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                        Redirecting to payment...
                      </>
                    ) : (
                      <>
                        <CreditCard className="h-5 w-5 mr-2" />
                        Pay Now
                      </>
                    )}
                  </Button>
                  <p className="text-xs text-gray-400 mt-4">
                    Secure payment processing by Stripe
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Questions about this invoice? Contact us at support@coachingwomenofcolor.com</p>
          <p className="mt-1">Coaching Women of Color - Empowering Women of Color in Leadership</p>
        </div>
      </div>
    </div>
  );
}
