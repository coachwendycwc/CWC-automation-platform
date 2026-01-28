"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { invoicesApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  FileText,
  Plus,
  DollarSign,
  Clock,
  AlertTriangle,
  Send,
  Copy,
  MoreHorizontal,
  Eye,
} from "lucide-react";
import Link from "next/link";
import { Skeleton, SkeletonStats, SkeletonTable } from "@/components/ui/skeleton";

interface Invoice {
  id: string;
  invoice_number: string;
  contact_id: string;
  contact_name: string | null;
  organization_name: string | null;
  total: number;
  balance_due: number;
  status: string;
  due_date: string;
  created_at: string;
}

interface InvoiceStats {
  total_revenue: number;
  total_outstanding: number;
  total_overdue: number;
  invoices_count: number;
  paid_count: number;
  pending_count: number;
  overdue_count: number;
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

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [stats, setStats] = useState<InvoiceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("");
  const [search, setSearch] = useState<string>("");

  useEffect(() => {
    loadData();
  }, [filter, search]);

  const loadData = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const [invoicesData, statsData] = await Promise.all([
        invoicesApi.list(token, {
          status: filter || undefined,
          search: search || undefined,
        }),
        invoicesApi.getStats(token),
      ]);

      setInvoices(invoicesData);
      setStats(statsData);
    } catch (err) {
      console.error("Failed to load invoices:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (id: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await invoicesApi.send(token, id);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to send invoice");
    }
  };

  const handleDuplicate = async (id: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await invoicesApi.duplicate(token, id);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to duplicate invoice");
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const formatDueDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(date);
    due.setHours(0, 0, 0, 0);

    const diffDays = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return `${Math.abs(diffDays)} days overdue`;
    } else if (diffDays === 0) {
      return "Due today";
    } else if (diffDays === 1) {
      return "Due tomorrow";
    } else if (diffDays <= 7) {
      return `Due in ${diffDays} days`;
    } else {
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    }
  };

  if (loading) {
    return (
      <Shell>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-10 w-36" />
          </div>
          <SkeletonStats count={4} />
          <SkeletonTable rows={5} />
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
            <p className="text-gray-600">Create and manage your invoices</p>
          </div>
          <Link href="/invoices/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Invoice
            </Button>
          </Link>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center">
                  <DollarSign className="h-8 w-8 text-green-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Revenue</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(stats.total_revenue)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center">
                  <Clock className="h-8 w-8 text-blue-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Outstanding</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(stats.total_outstanding)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center">
                  <AlertTriangle className="h-8 w-8 text-red-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Overdue</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(stats.total_overdue)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center">
                  <FileText className="h-8 w-8 text-purple-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Invoices</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {stats.invoices_count}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters */}
        <Card>
          <CardContent className="py-4">
            <div className="flex flex-wrap gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                >
                  <option value="">All statuses</option>
                  <option value="draft">Draft</option>
                  <option value="sent">Sent</option>
                  <option value="viewed">Viewed</option>
                  <option value="partial">Partial</option>
                  <option value="paid">Paid</option>
                  <option value="overdue">Overdue</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
                <input
                  type="text"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  placeholder="Search by invoice number..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              {(filter || search) && (
                <div className="flex items-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setFilter("");
                      setSearch("");
                    }}
                  >
                    Clear filters
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Invoices List */}
        {invoices.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No invoices found</h3>
              <p className="text-gray-500 mb-4">
                {filter || search
                  ? "Try adjusting your filters"
                  : "Create your first invoice to get started"}
              </p>
              {!filter && !search && (
                <Link href="/invoices/new">
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Invoice
                  </Button>
                </Link>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-0">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Invoice
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Client
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Due Date
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {invoices.map((invoice) => (
                    <tr key={invoice.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link href={`/invoices/${invoice.id}`} className="text-blue-600 hover:underline font-medium">
                          {invoice.invoice_number}
                        </Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{invoice.contact_name || "Unknown"}</div>
                        {invoice.organization_name && (
                          <div className="text-sm text-gray-500">{invoice.organization_name}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {formatCurrency(invoice.total)}
                        </div>
                        {invoice.balance_due > 0 && invoice.balance_due < invoice.total && (
                          <div className="text-xs text-gray-500">
                            {formatCurrency(invoice.balance_due)} due
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge className={STATUS_COLORS[invoice.status]}>
                          {invoice.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDueDate(invoice.due_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end gap-2">
                          <Link href={`/invoices/${invoice.id}`}>
                            <Button size="sm" variant="ghost">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </Link>
                          {invoice.status === "draft" && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleSend(invoice.id)}
                              title="Send invoice"
                            >
                              <Send className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDuplicate(invoice.id)}
                            title="Duplicate"
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}
      </div>
    </Shell>
  );
}
