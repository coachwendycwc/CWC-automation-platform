"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DollarSign, FileText, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Invoice {
  id: string;
  invoice_number: string;
  created_at: string;
  due_date: string;
  total: number;
  balance_due: number;
  status: string;
  contact_name?: string;
}

export default function OrganizationBillingPage() {
  const { sessionToken, isOrgAdmin } = useClientAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (!isOrgAdmin) {
      router.replace("/client/dashboard");
      return;
    }

    const loadData = async () => {
      if (!sessionToken) return;

      try {
        // Fetch org invoices (via organization_id filter on backend)
        const data = await clientPortalApi.getInvoices(sessionToken);
        setInvoices(data);
      } catch (error) {
        console.error("Failed to load invoices:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [sessionToken, isOrgAdmin, router]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "paid":
        return "bg-green-100 text-green-800";
      case "overdue":
        return "bg-red-100 text-red-800";
      case "partial":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-blue-100 text-blue-800";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  // Calculate totals
  const totalOutstanding = invoices.reduce((sum, inv) => sum + inv.balance_due, 0);
  const totalPaid = invoices.reduce((sum, inv) => sum + (inv.total - inv.balance_due), 0);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/client/organization">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
        </Link>
      </div>

      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Organization Billing</h1>
        <p className="text-gray-500 mt-1">
          Invoices for your organization's coaching services
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-xl">
                <DollarSign className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Paid</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formatCurrency(totalPaid)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-orange-100 rounded-xl">
                <DollarSign className="h-6 w-6 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Outstanding</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formatCurrency(totalOutstanding)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-xl">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Invoices</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {invoices.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Invoice List */}
      {invoices.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No invoices</h3>
            <p className="text-gray-500">
              No invoices have been created for your organization yet
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {invoices.map((invoice) => (
            <Link key={invoice.id} href={`/client/invoices/${invoice.id}`}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="py-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">
                        {invoice.invoice_number}
                      </p>
                      <p className="text-sm text-gray-500">
                        Due {formatDate(invoice.due_date)}
                      </p>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="font-semibold text-gray-900">
                          {formatCurrency(invoice.balance_due)}
                        </p>
                        <p className="text-xs text-gray-500">
                          of {formatCurrency(invoice.total)}
                        </p>
                      </div>
                      <Badge className={getStatusColor(invoice.status)}>
                        {invoice.status}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
