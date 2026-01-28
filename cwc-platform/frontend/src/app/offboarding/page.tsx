"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { offboardingApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  UserMinus,
  Plus,
  CheckCircle,
  Clock,
  Play,
  XCircle,
  Eye,
  MessageSquare,
  Quote,
  User,
  FolderKanban,
  FileText,
  Settings,
} from "lucide-react";
import Link from "next/link";

interface OffboardingWorkflow {
  id: string;
  contact_id: string;
  contact_name: string | null;
  contact_email: string | null;
  workflow_type: string;
  related_project_id: string | null;
  related_project_title: string | null;
  related_contract_id: string | null;
  status: string;
  initiated_at: string;
  completed_at: string | null;
  checklist: Array<{ item: string; completed: boolean; completed_at: string | null }>;
  send_survey: boolean;
  request_testimonial: boolean;
  survey_completed_at: string | null;
  testimonial_received: boolean;
  created_at: string;
}

interface OffboardingStats {
  total_workflows: number;
  pending: number;
  in_progress: number;
  completed: number;
  cancelled: number;
  surveys_sent: number;
  surveys_completed: number;
  testimonials_received: number;
  testimonials_approved: number;
  avg_satisfaction: number | null;
  avg_nps: number | null;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-100 text-gray-800",
  in_progress: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  pending: <Clock className="h-4 w-4" />,
  in_progress: <Play className="h-4 w-4" />,
  completed: <CheckCircle className="h-4 w-4" />,
  cancelled: <XCircle className="h-4 w-4" />,
};

const WORKFLOW_TYPE_LABELS: Record<string, string> = {
  client: "Client Offboarding",
  project: "Project Completion",
  contract: "Contract End",
};

const WORKFLOW_TYPE_ICONS: Record<string, React.ReactNode> = {
  client: <User className="h-4 w-4" />,
  project: <FolderKanban className="h-4 w-4" />,
  contract: <FileText className="h-4 w-4" />,
};

export default function OffboardingPage() {
  const [workflows, setWorkflows] = useState<OffboardingWorkflow[]>([]);
  const [stats, setStats] = useState<OffboardingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [search, setSearch] = useState<string>("");

  useEffect(() => {
    loadData();
  }, [filter, typeFilter, search]);

  const loadData = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const [workflowsResponse, statsData] = await Promise.all([
        offboardingApi.list(token, {
          status: filter || undefined,
          workflow_type: typeFilter || undefined,
        }),
        offboardingApi.getStats(token),
      ]);

      setWorkflows(workflowsResponse.items || []);
      setStats(statsData);
    } catch (err) {
      console.error("Failed to load offboarding workflows:", err);
    } finally {
      setLoading(false);
    }
  };

  const getChecklistProgress = (checklist: OffboardingWorkflow["checklist"]) => {
    if (!checklist || checklist.length === 0) return 0;
    const completed = checklist.filter((item) => item.completed).length;
    return Math.round((completed / checklist.length) * 100);
  };

  if (loading) {
    return (
      <Shell>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading...</div>
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
            <h1 className="text-2xl font-bold">Offboarding</h1>
            <p className="text-gray-500">Manage client offboarding and completion workflows</p>
          </div>
          <div className="flex gap-2">
            <Link href="/offboarding/templates">
              <Button variant="outline">
                <Settings className="h-4 w-4 mr-2" />
                Templates
              </Button>
            </Link>
            <Link href="/offboarding/new">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Workflow
              </Button>
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Total Workflows
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <UserMinus className="h-5 w-5 text-gray-400" />
                <span className="text-2xl font-bold">{stats?.total_workflows || 0}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                In Progress
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Play className="h-5 w-5 text-blue-500" />
                <span className="text-2xl font-bold text-blue-600">
                  {stats?.in_progress || 0}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Surveys Completed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-purple-500" />
                <span className="text-2xl font-bold text-purple-600">
                  {stats?.surveys_completed || 0}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Testimonials Received
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Quote className="h-5 w-5 text-green-500" />
                <span className="text-2xl font-bold text-green-600">
                  {stats?.testimonials_received || 0}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 items-center">
          <Input
            placeholder="Search by contact name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-sm"
          />
          <div className="flex gap-2">
            <Button
              variant={filter === "" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("")}
            >
              All
            </Button>
            <Button
              variant={filter === "pending" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("pending")}
            >
              Pending
            </Button>
            <Button
              variant={filter === "in_progress" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("in_progress")}
            >
              In Progress
            </Button>
            <Button
              variant={filter === "completed" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("completed")}
            >
              Completed
            </Button>
          </div>
          <div className="flex gap-2 border-l pl-4">
            <Button
              variant={typeFilter === "" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setTypeFilter("")}
            >
              All Types
            </Button>
            <Button
              variant={typeFilter === "client" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setTypeFilter("client")}
            >
              <User className="h-3 w-3 mr-1" />
              Client
            </Button>
            <Button
              variant={typeFilter === "project" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setTypeFilter("project")}
            >
              <FolderKanban className="h-3 w-3 mr-1" />
              Project
            </Button>
            <Button
              variant={typeFilter === "contract" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setTypeFilter("contract")}
            >
              <FileText className="h-3 w-3 mr-1" />
              Contract
            </Button>
          </div>
        </div>

        {/* Workflows List */}
        <Card>
          <CardContent className="p-0">
            {workflows.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <UserMinus className="h-12 w-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900">No offboarding workflows</h3>
                <p className="text-gray-500 mt-1">
                  Start an offboarding workflow when a client engagement ends
                </p>
                <Link href="/offboarding/new">
                  <Button className="mt-4">
                    <Plus className="h-4 w-4 mr-2" />
                    New Workflow
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="divide-y">
                {workflows.map((workflow) => (
                  <div
                    key={workflow.id}
                    className="flex items-center justify-between p-4 hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-100">
                        {WORKFLOW_TYPE_ICONS[workflow.workflow_type] || <UserMinus className="h-4 w-4" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <Link href={`/offboarding/${workflow.id}`}>
                          <h3 className="font-medium text-gray-900 hover:text-blue-600 truncate">
                            {workflow.contact_name || "Unknown Contact"}
                          </h3>
                        </Link>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <span>{WORKFLOW_TYPE_LABELS[workflow.workflow_type]}</span>
                          {workflow.related_project_title && (
                            <>
                              <span>•</span>
                              <span>{workflow.related_project_title}</span>
                            </>
                          )}
                          <span>•</span>
                          <span>Started {formatDate(workflow.initiated_at)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-6">
                      {/* Checklist Progress */}
                      <div className="w-24 text-center">
                        <div className="text-sm font-medium">
                          {getChecklistProgress(workflow.checklist)}%
                        </div>
                        <div className="text-xs text-gray-500">
                          {workflow.checklist?.filter((i) => i.completed).length || 0}/
                          {workflow.checklist?.length || 0} items
                        </div>
                      </div>

                      {/* Survey/Testimonial Status */}
                      <div className="flex gap-2">
                        {workflow.send_survey && (
                          <Badge
                            variant="outline"
                            className={workflow.survey_completed_at ? "border-green-500 text-green-600" : "border-gray-300"}
                          >
                            <MessageSquare className="h-3 w-3 mr-1" />
                            Survey {workflow.survey_completed_at ? "Done" : "Pending"}
                          </Badge>
                        )}
                        {workflow.request_testimonial && (
                          <Badge
                            variant="outline"
                            className={workflow.testimonial_received ? "border-green-500 text-green-600" : "border-gray-300"}
                          >
                            <Quote className="h-3 w-3 mr-1" />
                            {workflow.testimonial_received ? "Received" : "Requested"}
                          </Badge>
                        )}
                      </div>

                      {/* Status Badge */}
                      <Badge className={STATUS_COLORS[workflow.status]}>
                        {STATUS_ICONS[workflow.status]}
                        <span className="ml-1">{workflow.status.replace("_", " ")}</span>
                      </Badge>

                      {/* Actions */}
                      <Link href={`/offboarding/${workflow.id}`}>
                        <Button variant="ghost" size="sm" title="View">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}
