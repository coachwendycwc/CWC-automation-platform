"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, Calendar, Clock, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Employee {
  id: string;
  first_name: string;
  last_name: string | null;
  email: string | null;
  sessions_completed: number;
  sessions_upcoming: number;
  last_session_date: string | null;
}

export default function OrganizationTeamPage() {
  const { sessionToken, isOrgAdmin } = useClientAuth();
  const [employees, setEmployees] = useState<Employee[]>([]);
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
        const data = await clientPortalApi.getOrganizationEmployees(sessionToken);
        setEmployees(data);
      } catch (error) {
        console.error("Failed to load employees:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [sessionToken, isOrgAdmin, router]);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "No sessions yet";
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

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
        <h1 className="text-2xl font-semibold text-gray-900">Team Members</h1>
        <p className="text-gray-500 mt-1">
          {employees.length} team member{employees.length !== 1 ? "s" : ""} enrolled in coaching
        </p>
      </div>

      {/* Employee List */}
      {employees.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center">
            <Users className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No team members</h3>
            <p className="text-gray-500">
              No employees are currently enrolled in coaching
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {employees.map((employee) => (
            <Card key={employee.id} className="hover:shadow-md transition-shadow">
              <CardContent className="py-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                      <span className="text-lg font-semibold text-purple-600">
                        {employee.first_name[0]}
                        {employee.last_name?.[0] || ""}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        {employee.first_name} {employee.last_name}
                      </p>
                      {employee.email && (
                        <p className="text-sm text-gray-500">{employee.email}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    {/* Sessions Completed */}
                    <div className="text-center">
                      <div className="flex items-center gap-1.5 text-gray-600">
                        <Calendar className="h-4 w-4" />
                        <span className="text-lg font-semibold">
                          {employee.sessions_completed}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500">Completed</p>
                    </div>

                    {/* Upcoming */}
                    <div className="text-center">
                      <div className="flex items-center gap-1.5 text-gray-600">
                        <Clock className="h-4 w-4" />
                        <span className="text-lg font-semibold">
                          {employee.sessions_upcoming}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500">Upcoming</p>
                    </div>

                    {/* Status Badge */}
                    <Badge
                      className={
                        employee.sessions_upcoming > 0
                          ? "bg-green-100 text-green-800"
                          : employee.sessions_completed > 0
                          ? "bg-blue-100 text-blue-800"
                          : "bg-gray-100 text-gray-600"
                      }
                    >
                      {employee.sessions_upcoming > 0
                        ? "Active"
                        : employee.sessions_completed > 0
                        ? "Engaged"
                        : "New"}
                    </Badge>
                  </div>
                </div>

                {/* Last Session Info */}
                {employee.last_session_date && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <p className="text-xs text-gray-500">
                      Last session: {formatDate(employee.last_session_date)}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Privacy Notice */}
      <div className="bg-gray-50 rounded-xl p-4">
        <p className="text-sm text-gray-500">
          <span className="font-medium text-gray-700">Privacy Note:</span> Session content,
          transcripts, and homework are confidential between the coach and coachee. Only
          session counts and dates are visible to organization administrators.
        </p>
      </div>
    </div>
  );
}
