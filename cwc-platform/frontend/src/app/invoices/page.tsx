"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
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
  due_soon_reminder_sent_at: string | null;
  overdue_reminder_sent_at: string | null;
  final_notice_sent_at: string | null;
  last_collection_email_sent_at: string | null;
  collection_stage: "due_soon" | "overdue" | "final_notice" | null;
  needs_collection_attention: boolean;
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
  collections_attention_count: number;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-muted text-foreground",
  sent: "bg-primary/10 text-primary",
  viewed: "bg-accent/10 text-accent",
  partial: "bg-warning/10 text-warning",
  paid: "bg-success/10 text-success",
  overdue: "bg-destructive/10 text-destructive",
  cancelled: "bg-muted text-muted-foreground",
};

const COLLECTION_STAGE_LABELS: Record<NonNullable<Invoice["collection_stage"]>, string> = {
  due_soon: "Due Soon Reminder",
  overdue: "Overdue Reminder",
  final_notice: "Final Notice",
};

export default function InvoicesPage() {
  const searchParams = useSearchParams();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [stats, setStats] = useState<InvoiceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [queueFilter, setQueueFilter] = useState<string>("");
  const [sendingReminderFor, setSendingReminderFor] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [filter, search]);

  useEffect(() => {
    setFilter(searchParams.get("status") || "");
    setSearch(searchParams.get("search") || "");
    setQueueFilter(searchParams.get("queue") === "follow-up" ? "follow-up" : "");
  }, [searchParams]);

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
      toast.success("Invoice sent");
      await loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to send invoice");
    }
  };

  const handleDuplicate = async (id: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await invoicesApi.duplicate(token, id);
      toast.success("Invoice duplicated");
      await loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to duplicate invoice");
    }
  };

  const getReminderKind = (invoice: Invoice): "due_soon" | "overdue" | "final_notice" => {
    const dueDate = new Date(invoice.due_date);
    const now = new Date();
    const daysUntilDue = Math.ceil((dueDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    if (daysUntilDue < -14) {
      return "final_notice";
    }
    if (daysUntilDue < 0) {
      return "overdue";
    }
    return "due_soon";
  };

  const getReminderLabel = (invoice: Invoice) => {
    const kind = getReminderKind(invoice);
    if (kind === "final_notice") return "Final notice";
    if (kind === "overdue") return "Remind";
    return "Nudge";
  };

  const canSendReminder = (invoice: Invoice) =>
    invoice.balance_due > 0 && ["sent", "viewed", "partial", "overdue"].includes(invoice.status);

  const handleSendReminder = async (invoice: Invoice) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      setSendingReminderFor(invoice.id);
      await invoicesApi.sendReminder(token, invoice.id, { kind: getReminderKind(invoice) });
      toast.success("Collections email sent");
      await loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to send reminder");
    } finally {
      setSendingReminderFor(null);
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

  const formatCollectionTimestamp = (value: string | null) => {
    if (!value) return "Not sent";
    return new Date(value).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  const visibleInvoices = useMemo(() => {
    if (queueFilter !== "follow-up") {
      return invoices;
    }
    return invoices.filter((invoice) => invoice.needs_collection_attention);
  }, [invoices, queueFilter]);

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
            <h1 className="text-2xl font-bold text-foreground">Invoices</h1>
            <p className="text-muted-foreground">Create and manage your invoices</p>
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
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center">
                  <DollarSign className="h-8 w-8 text-green-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground">Total Revenue</p>
                    <p className="text-2xl font-bold text-foreground">
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
                    <p className="text-sm font-medium text-muted-foreground">Outstanding</p>
                    <p className="text-2xl font-bold text-foreground">
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
                    <p className="text-sm font-medium text-muted-foreground">Overdue</p>
                    <p className="text-2xl font-bold text-foreground">
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
                    <p className="text-sm font-medium text-muted-foreground">Total Invoices</p>
                    <p className="text-2xl font-bold text-foreground">
                      {stats.invoices_count}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center">
                  <Send className="h-8 w-8 text-amber-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground">Needs Follow-Up</p>
                    <p className="text-2xl font-bold text-foreground">
                      {stats.collections_attention_count}
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
                <label className="block text-sm font-medium text-foreground mb-1">Status</label>
                <select
                  className="rounded-md border border-border px-3 py-2 text-sm"
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
                <label className="block text-sm font-medium text-foreground mb-1">Search</label>
                <input
                  type="text"
                  className="w-full rounded-md border border-border px-3 py-2 text-sm"
                  placeholder="Search by invoice number..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <div className="flex items-end">
                <Button
                  variant={queueFilter === "follow-up" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setQueueFilter((current) => (current === "follow-up" ? "" : "follow-up"))}
                >
                  Needs Follow-Up
                  {stats ? ` (${stats.collections_attention_count})` : ""}
                </Button>
              </div>
              {(filter || search || queueFilter) && (
                <div className="flex items-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setFilter("");
                      setSearch("");
                      setQueueFilter("");
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
        {visibleInvoices.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No invoices found</h3>
              <p className="text-muted-foreground mb-4">
                {filter || search || queueFilter
                  ? "Try adjusting your filters"
                  : "Create your first invoice to get started"}
              </p>
              {!filter && !search && !queueFilter && (
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
                <thead className="bg-muted border-b">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Invoice
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Client
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Due Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Collections
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {visibleInvoices.map((invoice) => (
                    <tr key={invoice.id} className="hover:bg-muted cursor-pointer">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link href={`/invoices/${invoice.id}`} className="text-primary hover:underline font-medium">
                          {invoice.invoice_number}
                        </Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-foreground">{invoice.contact_name || "Unknown"}</div>
                        {invoice.organization_name && (
                          <div className="text-sm text-muted-foreground">{invoice.organization_name}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-foreground">
                          {formatCurrency(invoice.total)}
                        </div>
                        {invoice.balance_due > 0 && invoice.balance_due < invoice.total && (
                          <div className="text-xs text-muted-foreground">
                            {formatCurrency(invoice.balance_due)} due
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge className={STATUS_COLORS[invoice.status]}>
                          {invoice.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                        {formatDueDate(invoice.due_date)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          {invoice.collection_stage ? (
                            <Badge variant="outline">
                              {COLLECTION_STAGE_LABELS[invoice.collection_stage]}
                            </Badge>
                          ) : invoice.needs_collection_attention ? (
                            <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-700">
                              Follow up now
                            </Badge>
                          ) : (
                            <span className="text-sm text-muted-foreground">Quiet</span>
                          )}
                          <div className="text-xs text-muted-foreground">
                            Last email: {formatCollectionTimestamp(invoice.last_collection_email_sent_at)}
                          </div>
                        </div>
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
                          {canSendReminder(invoice) && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleSendReminder(invoice)}
                              disabled={sendingReminderFor === invoice.id}
                              title={getReminderLabel(invoice)}
                            >
                              <Clock className="h-4 w-4" />
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
