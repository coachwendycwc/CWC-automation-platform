"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import {
  Building2,
  DollarSign,
  Clock,
  FileText,
  ArrowRight,
  Calendar,
  TrendingUp,
  Users,
} from "lucide-react";
import { useRouter } from "next/navigation";

interface OrgDashboard {
  organization_name: string;
  organization_id: string;
  billing: {
    total_invoiced: number;
    total_paid: number;
    total_outstanding: number;
    invoice_count: number;
  };
  usage: {
    total_employees: number;
    employees_with_sessions: number;
    total_sessions_completed: number;
    total_sessions_upcoming: number;
    total_coaching_hours: number;
  };
  recent_invoices: any[];
  pending_contracts: number;
}

export default function OrganizationDashboardPage() {
  const { sessionToken, isOrgAdmin } = useClientAuth();
  const [data, setData] = useState<OrgDashboard | null>(null);
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
        const dashboardData = await clientPortalApi.getOrganizationDashboard(sessionToken);
        setData(dashboardData);
      } catch (error) {
        console.error("Failed to load org dashboard:", error);
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

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Unable to load organization data</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="p-3 bg-accent/10 rounded-2xl">
          <Building2 className="h-8 w-8 text-accent" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold text-foreground">{data.organization_name}</h1>
          <p className="text-muted-foreground">Organization Dashboard</p>
        </div>
      </div>

      {/* Billing Overview */}
      <div>
        <h2 className="text-lg font-medium text-foreground mb-4">Billing Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-success/10 rounded-xl">
                  <DollarSign className="h-6 w-6 text-success" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Paid</p>
                  <p className="text-2xl font-semibold text-foreground">
                    {formatCurrency(data.billing.total_paid)}
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
                  <p className="text-sm text-muted-foreground">Outstanding</p>
                  <p className="text-2xl font-semibold text-foreground">
                    {formatCurrency(data.billing.total_outstanding)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-primary/10 rounded-xl">
                  <FileText className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Invoices</p>
                  <p className="text-2xl font-semibold text-foreground">
                    {data.billing.invoice_count}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Usage Stats */}
      <div>
        <h2 className="text-lg font-medium text-foreground mb-4">Coaching Usage</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6 text-center">
              <TrendingUp className="h-8 w-8 text-green-500 mx-auto mb-2" />
              <p className="text-3xl font-semibold text-foreground">
                {data.usage.employees_with_sessions}
              </p>
              <p className="text-sm text-muted-foreground">Active Coachees</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6 text-center">
              <Calendar className="h-8 w-8 text-blue-500 mx-auto mb-2" />
              <p className="text-3xl font-semibold text-foreground">
                {data.usage.total_sessions_completed}
              </p>
              <p className="text-sm text-muted-foreground">Sessions Completed</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6 text-center">
              <Clock className="h-8 w-8 text-orange-500 mx-auto mb-2" />
              <p className="text-3xl font-semibold text-foreground">
                {data.usage.total_coaching_hours}h
              </p>
              <p className="text-sm text-muted-foreground">Coaching Hours</p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recent Invoices & Coachees */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Invoices */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">Recent Invoices</CardTitle>
            <Link href="/client/organization/billing">
              <Button variant="ghost" size="sm">
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {data.recent_invoices.length === 0 ? (
              <p className="text-muted-foreground text-center py-4">No invoices yet</p>
            ) : (
              <div className="space-y-3">
                {data.recent_invoices.map((invoice) => (
                  <Link
                    key={invoice.id}
                    href={`/client/organization/billing`}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors cursor-pointer"
                  >
                    <div>
                      <p className="font-medium text-foreground">{invoice.invoice_number}</p>
                      <p className="text-sm text-muted-foreground">
                        Due {formatDate(invoice.due_date)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-foreground">
                        {formatCurrency(invoice.balance_due)}
                      </p>
                      <Badge
                        className={
                          invoice.status === "paid"
                            ? "bg-success/10 text-success"
                            : invoice.status === "overdue"
                            ? "bg-destructive/10 text-destructive"
                            : "bg-primary/10 text-primary"
                        }
                      >
                        {invoice.status}
                      </Badge>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Coachees Overview */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">Coachees</CardTitle>
            <Link href="/client/organization/team">
              <Button variant="ghost" size="sm">
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-muted rounded-xl">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-accent/10 rounded-lg">
                    <Users className="h-5 w-5 text-accent" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">
                      {data.usage.total_employees} Coachees
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {data.usage.employees_with_sessions} receiving coaching
                    </p>
                  </div>
                </div>
                <Link href="/client/organization/team">
                  <Button variant="outline" size="sm">
                    Manage
                  </Button>
                </Link>
              </div>

              {data.usage.total_sessions_upcoming > 0 && (
                <div className="flex items-center gap-3 p-4 bg-primary/5 rounded-xl">
                  <Calendar className="h-5 w-5 text-primary" />
                  <p className="text-sm text-blue-900">
                    <span className="font-medium">{data.usage.total_sessions_upcoming}</span> upcoming sessions scheduled
                  </p>
                </div>
              )}

              {data.pending_contracts > 0 && (
                <Link href="/client/organization/contracts">
                  <div className="flex items-center gap-3 p-4 bg-orange-50 rounded-xl hover:bg-orange-100 transition-colors cursor-pointer">
                    <FileText className="h-5 w-5 text-orange-600" />
                    <p className="text-sm text-orange-900">
                      <span className="font-medium">{data.pending_contracts}</span> contracts pending signature
                    </p>
                  </div>
                </Link>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
