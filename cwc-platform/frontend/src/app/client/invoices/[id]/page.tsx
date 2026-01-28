"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { ArrowLeft, CreditCard, CheckCircle } from "lucide-react";

interface Invoice {
  id: string;
  invoice_number: string;
  created_at: string;
  due_date: string;
  total: number;
  balance_due: number;
  status: string;
  view_token: string;
  line_items: {
    description: string;
    quantity: number;
    unit_price: number;
    amount: number;
  }[];
  payments: {
    id: string;
    amount: number;
    payment_date: string;
    payment_method: string | null;
  }[];
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-800",
  sent: "bg-blue-100 text-blue-800",
  viewed: "bg-purple-100 text-purple-800",
  partial: "bg-yellow-100 text-yellow-800",
  paid: "bg-green-100 text-green-800",
  overdue: "bg-red-100 text-red-800",
};

export default function ClientInvoiceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { sessionToken } = useClientAuth();
  const invoiceId = params.id as string;

  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadInvoice = async () => {
      if (!sessionToken || !invoiceId) return;

      try {
        const data = await clientPortalApi.getInvoice(sessionToken, invoiceId);
        setInvoice(data);
      } catch (error) {
        console.error("Failed to load invoice:", error);
      } finally {
        setLoading(false);
      }
    };

    loadInvoice();
  }, [sessionToken, invoiceId]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const handlePayNow = () => {
    if (invoice?.view_token) {
      window.open(`/pay/${invoice.view_token}`, "_blank");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading invoice...</div>
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Invoice not found</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/client/invoices">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{invoice.invoice_number}</h1>
              <Badge className={STATUS_COLORS[invoice.status]}>
                {invoice.status}
              </Badge>
            </div>
            <p className="text-gray-500">
              Issued {formatDate(invoice.created_at)}
            </p>
          </div>
        </div>

        {invoice.balance_due > 0 && (
          <Button onClick={handlePayNow}>
            <CreditCard className="h-4 w-4 mr-2" />
            Pay Now
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Invoice Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Line Items */}
          <Card>
            <CardHeader>
              <CardTitle>Items</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 font-medium">Description</th>
                    <th className="text-right py-2 font-medium">Qty</th>
                    <th className="text-right py-2 font-medium">Price</th>
                    <th className="text-right py-2 font-medium">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {invoice.line_items.map((item, index) => (
                    <tr key={index} className="border-b">
                      <td className="py-3">{item.description}</td>
                      <td className="text-right py-3">{item.quantity}</td>
                      <td className="text-right py-3">
                        {formatCurrency(item.unit_price)}
                      </td>
                      <td className="text-right py-3 font-medium">
                        {formatCurrency(item.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan={3} className="text-right py-3 font-semibold">
                      Total
                    </td>
                    <td className="text-right py-3 font-semibold text-lg">
                      {formatCurrency(invoice.total)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </CardContent>
          </Card>

          {/* Payments */}
          {invoice.payments.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Payments</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {invoice.payments.map((payment) => (
                    <div
                      key={payment.id}
                      className="flex items-center justify-between p-3 bg-green-50 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        <div>
                          <p className="font-medium">Payment Received</p>
                          <p className="text-sm text-gray-500">
                            {formatDate(payment.payment_date)}
                            {payment.payment_method &&
                              ` via ${payment.payment_method}`}
                          </p>
                        </div>
                      </div>
                      <p className="font-semibold text-green-700">
                        {formatCurrency(payment.amount)}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Summary Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-500">Total</span>
                <span className="font-medium">{formatCurrency(invoice.total)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Paid</span>
                <span className="font-medium text-green-600">
                  {formatCurrency(invoice.total - invoice.balance_due)}
                </span>
              </div>
              <div className="border-t pt-4">
                <div className="flex justify-between">
                  <span className="font-semibold">Balance Due</span>
                  <span className="font-bold text-lg">
                    {formatCurrency(invoice.balance_due)}
                  </span>
                </div>
              </div>

              <div className="pt-4">
                <p className="text-sm text-gray-500">
                  Due Date:{" "}
                  <span className="font-medium text-gray-900">
                    {formatDate(invoice.due_date)}
                  </span>
                </p>
              </div>

              {invoice.balance_due > 0 && (
                <Button className="w-full" onClick={handlePayNow}>
                  <CreditCard className="h-4 w-4 mr-2" />
                  Pay Now
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
