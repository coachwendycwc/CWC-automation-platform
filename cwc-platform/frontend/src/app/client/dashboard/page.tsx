"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi, OnboardingAssessmentResponse } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import {
  FileText,
  Calendar,
  FolderKanban,
  FileSignature,
  DollarSign,
  ArrowRight,
  Clock,
  Video,
  ClipboardCheck,
  AlertCircle,
} from "lucide-react";

interface DashboardData {
  stats: {
    unpaid_invoices: number;
    total_due: number;
    upcoming_bookings: number;
    active_projects: number;
    pending_contracts: number;
  };
  recent_invoices: any[];
  upcoming_bookings: any[];
}

const STATUS_COLORS: Record<string, string> = {
  sent: "bg-blue-100 text-blue-800",
  viewed: "bg-purple-100 text-purple-800",
  partial: "bg-yellow-100 text-yellow-800",
  paid: "bg-green-100 text-green-800",
  overdue: "bg-red-100 text-red-800",
  confirmed: "bg-green-100 text-green-800",
};

export default function ClientDashboardPage() {
  const { sessionToken, contact, isOrgAdmin } = useClientAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [assessment, setAssessment] = useState<OnboardingAssessmentResponse | null>(null);
  const [assessmentPending, setAssessmentPending] = useState(false);

  // Org coachee = belongs to org but not admin (org pays their bills)
  const isOrgCoachee = !isOrgAdmin && !!contact?.organization_id;

  useEffect(() => {
    const loadDashboard = async () => {
      if (!sessionToken) return;

      try {
        const dashboardData = await clientPortalApi.getDashboard(sessionToken);
        setData(dashboardData);
      } catch (error) {
        console.error("Failed to load dashboard:", error);
      } finally {
        setLoading(false);
      }
    };

    const loadAssessment = async () => {
      if (!sessionToken) return;

      try {
        const assessmentData = await clientPortalApi.getOnboardingAssessment(sessionToken);
        setAssessment(assessmentData);
        // Assessment is pending if it exists but not completed
        if (assessmentData && !assessmentData.completed_at) {
          setAssessmentPending(true);
        }
      } catch (error: any) {
        // 404 is expected if no assessment exists
        if (error.status !== 404) {
          console.error("Failed to load assessment:", error);
        }
      }
    };

    loadDashboard();
    loadAssessment();
  }, [sessionToken]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
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
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {contact?.first_name}!
        </h1>
        <p className="text-gray-500">
          {isOrgCoachee && contact?.organization_name
            ? `Your coaching is sponsored by ${contact.organization_name}`
            : "Here's an overview of your account"}
        </p>
      </div>

      {/* Pending Assessment Banner */}
      {assessmentPending && assessment && (
        <Card className="bg-amber-50 border-amber-200">
          <CardContent className="py-4">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-amber-100 rounded-lg">
                <ClipboardCheck className="h-6 w-6 text-amber-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-amber-900">
                  Complete Your Onboarding Assessment
                </h3>
                <p className="text-sm text-amber-800 mt-1">
                  Please complete the onboarding assessment before your first coaching session.
                  This helps tailor your experience to your unique needs and goals.
                </p>
                <div className="mt-3">
                  <Link href={`/onboarding/${assessment.token}`}>
                    <Button className="bg-amber-600 hover:bg-amber-700">
                      <ClipboardCheck className="h-4 w-4 mr-2" />
                      Complete Assessment
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Cards - different for org coachees vs independent */}
      {isOrgCoachee ? (
        // Org coachee: only show sessions
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <Calendar className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Upcoming Sessions</p>
                  <p className="text-2xl font-bold">
                    {data?.stats.upcoming_bookings || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <Video className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Session Recordings</p>
                  <Link href="/client/sessions" className="text-2xl font-bold text-purple-600 hover:underline">
                    View All
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        // Independent coachee: show billing stats
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <DollarSign className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Amount Due</p>
                  <p className="text-2xl font-bold">
                    {formatCurrency(data?.stats.total_due || 0)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Unpaid Invoices</p>
                  <p className="text-2xl font-bold">
                    {data?.stats.unpaid_invoices || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <Calendar className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Upcoming Sessions</p>
                  <p className="text-2xl font-bold">
                    {data?.stats.upcoming_bookings || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-orange-100 rounded-lg">
                  <FileSignature className="h-6 w-6 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Pending Contracts</p>
                  <p className="text-2xl font-bold">
                    {data?.stats.pending_contracts || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Content sections - different for org coachees */}
      {isOrgCoachee ? (
        // Org coachee: only show upcoming sessions
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">Upcoming Sessions</CardTitle>
            <Link href="/client/sessions">
              <Button variant="ghost" size="sm">
                View All Sessions
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {data?.upcoming_bookings.length === 0 ? (
              <p className="text-gray-500 text-center py-4">
                No upcoming sessions scheduled
              </p>
            ) : (
              <div className="space-y-3">
                {data?.upcoming_bookings.map((booking) => (
                  <div
                    key={booking.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-gray-50"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-purple-100 rounded-lg">
                        <Clock className="h-5 w-5 text-purple-600" />
                      </div>
                      <div>
                        <p className="font-medium">{booking.booking_type_name}</p>
                        <p className="text-sm text-gray-500">
                          {formatDate(booking.start_time)} at{" "}
                          {formatTime(booking.start_time)}
                        </p>
                      </div>
                    </div>
                    {booking.meeting_link && (
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => window.open(booking.meeting_link, "_blank")}
                      >
                        Join Session
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        // Independent coachee: show invoices and bookings
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Invoices */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">Recent Invoices</CardTitle>
              <Link href="/client/invoices">
                <Button variant="ghost" size="sm">
                  View All
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {data?.recent_invoices.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No invoices yet</p>
              ) : (
                <div className="space-y-3">
                  {data?.recent_invoices.map((invoice) => (
                    <Link
                      key={invoice.id}
                      href={`/client/invoices/${invoice.id}`}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div>
                        <p className="font-medium">{invoice.invoice_number}</p>
                        <p className="text-sm text-gray-500">
                          Due {formatDate(invoice.due_date)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">
                          {formatCurrency(invoice.balance_due)}
                        </p>
                        <Badge className={STATUS_COLORS[invoice.status] || "bg-gray-100"}>
                          {invoice.status}
                        </Badge>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Upcoming Bookings */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">Upcoming Sessions</CardTitle>
              <Link href="/client/sessions">
                <Button variant="ghost" size="sm">
                  View All
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {data?.upcoming_bookings.length === 0 ? (
                <p className="text-gray-500 text-center py-4">
                  No upcoming sessions
                </p>
              ) : (
                <div className="space-y-3">
                  {data?.upcoming_bookings.map((booking) => (
                    <div
                      key={booking.id}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-purple-100 rounded-lg">
                          <Clock className="h-5 w-5 text-purple-600" />
                        </div>
                        <div>
                          <p className="font-medium">{booking.booking_type_name}</p>
                          <p className="text-sm text-gray-500">
                            {formatDate(booking.start_time)} at{" "}
                            {formatTime(booking.start_time)}
                          </p>
                        </div>
                      </div>
                      {booking.meeting_link && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(booking.meeting_link, "_blank")}
                        >
                          Join
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Quick Actions - different for org coachees */}
      {!isOrgCoachee && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Link href="/client/invoices">
                <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2">
                  <FileText className="h-6 w-6" />
                  <span>View Invoices</span>
                </Button>
              </Link>
              <Link href="/client/contracts">
                <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2">
                  <FileSignature className="h-6 w-6" />
                  <span>View Contracts</span>
                </Button>
              </Link>
              <Link href="/client/sessions">
                <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2">
                  <Calendar className="h-6 w-6" />
                  <span>My Sessions</span>
                </Button>
              </Link>
              <Link href="/client/projects">
                <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2">
                  <FolderKanban className="h-6 w-6" />
                  <span>My Projects</span>
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
