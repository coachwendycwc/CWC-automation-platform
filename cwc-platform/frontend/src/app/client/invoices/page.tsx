"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
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
  draft: "bg-muted text-foreground",
  sent: "bg-primary/10 text-primary",
  viewed: "bg-accent/10 text-accent",
  partial: "bg-warning/10 text-warning",
  paid: "bg-success/10 text-success",
  overdue: "bg-destructive/10 text-destructive",
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
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Invoices</h1>
          <p className="text-muted-foreground">View and pay your invoices</p>
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
            <FileText className="h-12 w-12 text-muted-foreground/40 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground">No invoices</h3>
            <p className="text-muted-foreground">
              {filter ? "No invoices match this filter" : "You don't have any invoices yet"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {invoices.map((invoice) => (
            <Card key={invoice.id} className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="p-2 bg-accent/10 rounded-lg">
                      <FileText className="h-5 w-5 text-accent" />
                    </div>
                    <div>
                      <p className="font-medium">{invoice.invoice_number}</p>
                      <p className="text-sm text-muted-foreground">
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
                      <p className="text-sm text-muted-foreground">Balance Due</p>
                      <p className="text-lg font-semibold">
                        {formatCurrency(invoice.balance_due)}
                      </p>
                    </div>
                    <Badge className={STATUS_COLORS[invoice.status] || "bg-muted"}>
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
