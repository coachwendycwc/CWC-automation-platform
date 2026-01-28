"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { reportsApi } from "@/lib/api";
import {
  Users,
  Building2,
  Calendar,
  DollarSign,
  FileText,
  FolderKanban,
  TrendingUp,
  Clock,
  AlertCircle,
  ArrowUpRight,
  Download,
} from "lucide-react";
import { Skeleton, SkeletonStats } from "@/components/ui/skeleton";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";

interface DashboardData {
  revenue: { total: number; this_month: number; outstanding: number };
  invoices: { draft: number; sent: number; partial: number; paid: number; overdue: number };
  contacts: number;
  projects: { active: number };
  bookings: { this_month: number; upcoming: number };
}

interface MonthlyRevenue {
  year: number;
  months: Array<{ month: string; month_num: number; revenue: number }>;
  total: number;
}

interface AgingData {
  current: { total: number; count: number };
  "1_30_days": { total: number; count: number };
  "31_60_days": { total: number; count: number };
  "61_90_days": { total: number; count: number };
  "90_plus_days": { total: number; count: number };
  summary: { total_outstanding: number; total_invoices: number };
}

interface TopContact {
  id: string;
  name: string;
  email: string;
  total_revenue: number;
  invoice_count: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const { token, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [monthlyRevenue, setMonthlyRevenue] = useState<MonthlyRevenue | null>(null);
  const [aging, setAging] = useState<AgingData | null>(null);
  const [topContacts, setTopContacts] = useState<TopContact[]>([]);

  useEffect(() => {
    if (!token) {
      router.push("/");
      return;
    }

    const fetchData = async () => {
      try {
        const [dashboardData, revenueData, agingData, engagementData] = await Promise.all([
          reportsApi.getDashboard(token),
          reportsApi.getMonthlyRevenue(token),
          reportsApi.getInvoiceAging(token),
          reportsApi.getContactEngagement(token, 5),
        ]);

        setDashboard(dashboardData);
        setMonthlyRevenue(revenueData);
        setAging(agingData);
        setTopContacts(engagementData.top_contacts);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token, router]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (loading) {
    return (
      <Shell>
        <div className="space-y-6">
          <Skeleton className="h-8 w-48" />
          <SkeletonStats count={4} />
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <Skeleton className="h-5 w-32" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-64 w-full" />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <Skeleton className="h-5 w-32" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-64 w-full" />
              </CardContent>
            </Card>
          </div>
        </div>
      </Shell>
    );
  }

  const statCards = [
    {
      title: "Total Revenue",
      value: formatCurrency(dashboard?.revenue.total || 0),
      icon: DollarSign,
      color: "text-green-600",
      bgColor: "bg-green-100",
      href: "/invoices",
    },
    {
      title: "This Month",
      value: formatCurrency(dashboard?.revenue.this_month || 0),
      icon: TrendingUp,
      color: "text-blue-600",
      bgColor: "bg-blue-100",
      href: "/invoices",
    },
    {
      title: "Outstanding",
      value: formatCurrency(dashboard?.revenue.outstanding || 0),
      icon: AlertCircle,
      color: "text-orange-600",
      bgColor: "bg-orange-100",
      href: "/invoices?status=sent",
    },
    {
      title: "Upcoming Bookings",
      value: dashboard?.bookings.upcoming || 0,
      icon: Calendar,
      color: "text-purple-600",
      bgColor: "bg-purple-100",
      href: "/bookings",
    },
  ];

  const quickStats = [
    { label: "Contacts", value: dashboard?.contacts || 0, icon: Users, href: "/contacts" },
    { label: "Active Projects", value: dashboard?.projects.active || 0, icon: FolderKanban, href: "/projects" },
    { label: "Bookings This Month", value: dashboard?.bookings.this_month || 0, icon: Calendar, href: "/calendar" },
    { label: "Paid Invoices", value: dashboard?.invoices.paid || 0, icon: FileText, href: "/invoices?status=paid" },
  ];

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <p className="text-gray-500">Welcome back, {user?.name || "User"}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" asChild>
              <a href={reportsApi.exportInvoicesCsv(token || "")} download>
                <Download className="h-4 w-4 mr-2" />
                Export Invoices
              </a>
            </Button>
          </div>
        </div>

        {/* Main Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {statCards.map((stat) => (
            <Link key={stat.title} href={stat.href}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-gray-500">
                    {stat.title}
                  </CardTitle>
                  <div className={`rounded-full p-2 ${stat.bgColor}`}>
                    <stat.icon className={`h-4 w-4 ${stat.color}`} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stat.value}</div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Revenue Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Monthly Revenue ({monthlyRevenue?.year})</span>
                <span className="text-sm font-normal text-gray-500">
                  Total: {formatCurrency(monthlyRevenue?.total || 0)}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={monthlyRevenue?.months || []}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis
                      tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                      tick={{ fontSize: 12 }}
                    />
                    <Tooltip
                      formatter={(value) => [formatCurrency(value as number), "Revenue"]}
                      labelFormatter={(label) => `${label} ${monthlyRevenue?.year}`}
                    />
                    <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Invoice Aging */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Invoice Aging</span>
                <span className="text-sm font-normal text-gray-500">
                  {aging?.summary.total_invoices || 0} unpaid invoices
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { label: "Current (not due)", data: aging?.current, color: "bg-green-500" },
                  { label: "1-30 days overdue", data: aging?.["1_30_days"], color: "bg-yellow-500" },
                  { label: "31-60 days overdue", data: aging?.["31_60_days"], color: "bg-orange-500" },
                  { label: "61-90 days overdue", data: aging?.["61_90_days"], color: "bg-red-400" },
                  { label: "90+ days overdue", data: aging?.["90_plus_days"], color: "bg-red-600" },
                ].map((bucket) => (
                  <div key={bucket.label} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${bucket.color}`} />
                      <span className="text-sm">{bucket.label}</span>
                      <span className="text-xs text-gray-400">({bucket.data?.count || 0})</span>
                    </div>
                    <span className="font-medium">
                      {formatCurrency(bucket.data?.total || 0)}
                    </span>
                  </div>
                ))}
                <div className="border-t pt-4 flex items-center justify-between font-semibold">
                  <span>Total Outstanding</span>
                  <span>{formatCurrency(aging?.summary.total_outstanding || 0)}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Bottom Row */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {quickStats.map((stat) => (
                <Link
                  key={stat.label}
                  href={stat.href}
                  className="flex items-center justify-between hover:bg-gray-50 -mx-2 px-2 py-1 rounded"
                >
                  <div className="flex items-center gap-3">
                    <stat.icon className="h-4 w-4 text-gray-400" />
                    <span className="text-sm">{stat.label}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{stat.value}</span>
                    <ArrowUpRight className="h-3 w-3 text-gray-400" />
                  </div>
                </Link>
              ))}
            </CardContent>
          </Card>

          {/* Top Clients */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Top Clients by Revenue</span>
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/contacts">View All</Link>
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {topContacts.length === 0 ? (
                <p className="text-gray-500 text-sm">No client data yet.</p>
              ) : (
                <div className="space-y-4">
                  {topContacts.map((contact, index) => (
                    <Link
                      key={contact.id}
                      href={`/contacts/${contact.id}`}
                      className="flex items-center justify-between hover:bg-gray-50 -mx-2 px-2 py-2 rounded"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-sm font-medium">
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium">{contact.name}</p>
                          <p className="text-xs text-gray-500">{contact.invoice_count} invoices</p>
                        </div>
                      </div>
                      <span className="font-semibold text-green-600">
                        {formatCurrency(contact.total_revenue)}
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Button variant="outline" asChild>
              <Link href="/contacts/new">
                <Users className="h-4 w-4 mr-2" />
                Add Contact
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/invoices/new">
                <FileText className="h-4 w-4 mr-2" />
                Create Invoice
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/projects/new">
                <FolderKanban className="h-4 w-4 mr-2" />
                New Project
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/calendar">
                <Calendar className="h-4 w-4 mr-2" />
                View Calendar
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}
