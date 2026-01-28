"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { FileText, ExternalLink, User } from "lucide-react";

interface Invoice {
  id: string;
  invoice_number: string;
  created_at: string;
  due_date: string;
  total: number;
  balance_due: number;
  status: string;
  contact_name: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-800",
  sent: "bg-blue-100 text-blue-800",
  viewed: "bg-purple-100 text-purple-800",
  partial: "bg-yellow-100 text-yellow-800",
  paid: "bg-green-100 text-green-800",
  overdue: "bg-red-100 text-red-800",
};

export default function ClientInvoicesPage() {
  const { sessionToken } = useClientAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("");

  useEffect(() => {
    const loadInvoices = async () => {
      if (!sessionToken) return;

      try {
        const data = await clientPortalApi.getInvoices(
          sessionToken,
          filter || undefined
        );
        setInvoices(data);
      } catch (error) {
        console.error("Failed to load invoices:", error);
      } finally {
        setLoading(false);
      }
    };

    loadInvoices();
  }, [sessionToken, filter]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading invoices...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
          <p className="text-gray-500">View and pay your invoices</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <Button
          variant={filter === "" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("")}
        >
          All
        </Button>
        <Button
          variant={filter === "sent" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("sent")}
        >
          Pending
        </Button>
        <Button
          variant={filter === "paid" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("paid")}
        >
          Paid
        </Button>
      </div>

      {/* Invoices List */}
      {invoices.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No invoices</h3>
            <p className="text-gray-500">
              {filter ? "No invoices match this filter" : "You don't have any invoices yet"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {invoices.map((invoice) => (
            <Card key={invoice.id} className="hover:shadow-md transition-shadow">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <FileText className="h-5 w-5 text-purple-600" />
                    </div>
                    <div>
                      <p className="font-medium">{invoice.invoice_number}</p>
                      <p className="text-sm text-gray-500">
                        Issued {formatDate(invoice.created_at)} &middot; Due{" "}
                        {formatDate(invoice.due_date)}
                        {invoice.contact_name && (
                          <>
                            {" "}&middot;{" "}
                            <span className="inline-flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {invoice.contact_name}
                            </span>
                          </>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm text-gray-500">Balance Due</p>
                      <p className="text-lg font-semibold">
                        {formatCurrency(invoice.balance_due)}
                      </p>
                    </div>
                    <Badge className={STATUS_COLORS[invoice.status] || "bg-gray-100"}>
                      {invoice.status}
                    </Badge>
                    <Link href={`/client/invoices/${invoice.id}`}>
                      <Button variant="outline" size="sm">
                        View
                        <ExternalLink className="ml-2 h-4 w-4" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
