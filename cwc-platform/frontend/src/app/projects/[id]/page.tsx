"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { projectsApi, tasksApi, offboardingApi } from "@/lib/api";
import { toast } from "sonner";
import { formatDate, formatDateTime } from "@/lib/utils";
import { TaskListView } from "@/components/projects/TaskListView";
import { TaskKanbanView } from "@/components/projects/TaskKanbanView";
import {
  FolderKanban,
  ArrowLeft,
  Edit,
  Copy,
  CheckCircle,
  Play,
  Pause,
  Clock,
  Calendar,
  DollarSign,
  ListTodo,
  LayoutGrid,
  List,
  Plus,
  FileSignature,
  FileText,
  User,
  Building2,
  UserMinus,
} from "lucide-react";
import Link from "next/link";

interface Task {
  id: string;
  task_number: string;
  project_id: string;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  assigned_to: string | null;
  due_date: string | null;
  completed_at: string | null;
  estimated_hours: number | null;
  actual_hours: number;
  order_index: number;
  created_at: string;
}

interface ActivityLog {
  id: string;
  project_id: string;
  task_id: string | null;
  action: string;
  actor: string | null;
  details: Record<string, any> | null;
  created_at: string;
}

interface TaskStats {
  total_tasks: number;
  todo_count: number;
  in_progress_count: number;
  review_count: number;
  completed_count: number;
  blocked_count: number;
  estimated_hours: number;
  actual_hours: number;
}

interface Project {
  id: string;
  project_number: string;
  contact_id: string;
  organization_id: string | null;
  title: string;
  description: string | null;
  project_type: string;
  status: string;
  start_date: string | null;
  target_end_date: string | null;
  actual_end_date: string | null;
  budget_amount: number | null;
  estimated_hours: number | null;
  linked_contract_id: string | null;
  linked_invoice_id: string | null;
  template_id: string | null;
  progress_percent: number;
  view_token: string;
  client_visible: boolean;
  created_at: string;
  updated_at: string;
  contact_name: string | null;
  contact_email: string | null;
  organization_name: string | null;
  template_name: string | null;
  linked_contract_number: string | null;
  linked_invoice_number: string | null;
  tasks: Task[];
  activity_logs: ActivityLog[];
  task_stats: TaskStats | null;
}

const STATUS_COLORS: Record<string, string> = {
  planning: "bg-gray-100 text-gray-800",
  active: "bg-blue-100 text-blue-800",
  paused: "bg-yellow-100 text-yellow-800",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

const PROJECT_TYPE_LABELS: Record<string, string> = {
  coaching: "Coaching",
  workshop: "Workshop",
  consulting: "Consulting",
  speaking: "Speaking",
};

const ACTION_LABELS: Record<string, string> = {
  created: "Project created",
  status_changed: "Status changed",
  task_added: "Task added",
  task_completed: "Task completed",
  task_status_changed: "Task status changed",
  task_deleted: "Task deleted",
  time_logged: "Time logged",
  completed: "Project completed",
};

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [taskView, setTaskView] = useState<"list" | "kanban">("kanban");
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    if (projectId) {
      loadProject();
    }
  }, [projectId]);

  const loadProject = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const data = await projectsApi.get(token, projectId);
      setProject(data);
    } catch (err) {
      console.error("Failed to load project:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token || !project) return;

      if (newStatus === "completed") {
        await projectsApi.complete(token, project.id);
      } else {
        await projectsApi.update(token, project.id, { status: newStatus });
      }
      await loadProject();
    } catch (err: any) {
      alert(err.message || "Failed to update status");
    }
  };

  const handleDuplicate = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token || !project) return;

      const newProject = await projectsApi.duplicate(token, project.id);
      router.push(`/projects/${newProject.id}`);
    } catch (err: any) {
      alert(err.message || "Failed to duplicate project");
    }
  };

  const handleTasksChange = () => {
    loadProject();
  };

  const handleCompleteAndOffboard = async () => {
    if (!confirm("Complete this project and start offboarding for the client?")) return;

    try {
      const token = localStorage.getItem("token");
      if (!token || !project) return;

      // First complete the project
      await projectsApi.complete(token, project.id);

      // Then start offboarding workflow
      const workflow = await offboardingApi.initiate(token, {
        contact_id: project.contact_id,
        workflow_type: "project",
        related_project_id: project.id,
      });

      toast.success("Project completed and offboarding started");
      router.push(`/offboarding/${workflow.id}`);
    } catch (err: any) {
      console.error("Failed to complete and offboard:", err);
      toast.error(err.message || "Failed to complete and offboard");
    }
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

  if (!project) {
    return (
      <Shell>
        <div className="flex flex-col items-center justify-center h-64">
          <h2 className="text-xl font-bold">Project not found</h2>
          <Link href="/projects">
            <Button className="mt-4">Back to Projects</Button>
          </Link>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <Link href="/projects">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold">{project.title}</h1>
                <Badge className={STATUS_COLORS[project.status]}>
                  {project.status}
                </Badge>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                <span>{project.project_number}</span>
                <span>•</span>
                <span>{PROJECT_TYPE_LABELS[project.project_type] || project.project_type}</span>
                <span>•</span>
                <span>
                  {project.contact_name}
                  {project.organization_name && ` (${project.organization_name})`}
                </span>
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            {project.status === "planning" && (
              <Button onClick={() => handleStatusChange("active")}>
                <Play className="h-4 w-4 mr-2" />
                Start Project
              </Button>
            )}
            {project.status === "active" && (
              <>
                <Button variant="outline" onClick={() => handleStatusChange("paused")}>
                  <Pause className="h-4 w-4 mr-2" />
                  Pause
                </Button>
                <Button onClick={() => handleStatusChange("completed")}>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Complete
                </Button>
                <Button
                  variant="outline"
                  className="text-orange-600 hover:text-orange-700 hover:bg-orange-50"
                  onClick={handleCompleteAndOffboard}
                >
                  <UserMinus className="h-4 w-4 mr-2" />
                  Complete & Offboard
                </Button>
              </>
            )}
            {project.status === "paused" && (
              <Button onClick={() => handleStatusChange("active")}>
                <Play className="h-4 w-4 mr-2" />
                Resume
              </Button>
            )}
            <Button variant="outline" onClick={handleDuplicate}>
              <Copy className="h-4 w-4 mr-2" />
              Duplicate
            </Button>
          </div>
        </div>

        {/* Progress Bar */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Project Progress</span>
              <span className="text-sm font-bold">{project.progress_percent}%</span>
            </div>
            <Progress value={project.progress_percent} className="h-3" />
            {project.task_stats && (
              <div className="flex gap-4 mt-3 text-sm text-gray-500">
                <span>{project.task_stats.completed_count} / {project.task_stats.total_tasks} tasks completed</span>
                {project.task_stats.actual_hours > 0 && (
                  <>
                    <span>•</span>
                    <span>{project.task_stats.actual_hours}h logged</span>
                  </>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="tasks">
              Tasks ({project.tasks?.length || 0})
            </TabsTrigger>
            <TabsTrigger value="activity">Activity</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Project Details */}
              <Card>
                <CardHeader>
                  <CardTitle>Project Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {project.description && (
                    <div>
                      <label className="text-sm text-gray-500">Description</label>
                      <p className="mt-1">{project.description}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-gray-500">Start Date</label>
                      <p className="mt-1 flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        {project.start_date ? formatDate(project.start_date) : "Not set"}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">Target End Date</label>
                      <p className="mt-1 flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        {project.target_end_date ? formatDate(project.target_end_date) : "Not set"}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-gray-500">Budget</label>
                      <p className="mt-1 flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-gray-400" />
                        {project.budget_amount ? `$${project.budget_amount.toLocaleString()}` : "Not set"}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">Estimated Hours</label>
                      <p className="mt-1 flex items-center gap-2">
                        <Clock className="h-4 w-4 text-gray-400" />
                        {project.estimated_hours ? `${project.estimated_hours}h` : "Not set"}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Client & Links */}
              <Card>
                <CardHeader>
                  <CardTitle>Client & Links</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm text-gray-500">Contact</label>
                    <p className="mt-1 flex items-center gap-2">
                      <User className="h-4 w-4 text-gray-400" />
                      <Link href={`/contacts/${project.contact_id}`} className="text-blue-600 hover:underline">
                        {project.contact_name}
                      </Link>
                    </p>
                    {project.contact_email && (
                      <p className="text-sm text-gray-500 ml-6">{project.contact_email}</p>
                    )}
                  </div>

                  {project.organization_name && (
                    <div>
                      <label className="text-sm text-gray-500">Organization</label>
                      <p className="mt-1 flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-gray-400" />
                        <Link href={`/organizations/${project.organization_id}`} className="text-blue-600 hover:underline">
                          {project.organization_name}
                        </Link>
                      </p>
                    </div>
                  )}

                  {project.linked_contract_number && (
                    <div>
                      <label className="text-sm text-gray-500">Linked Contract</label>
                      <p className="mt-1 flex items-center gap-2">
                        <FileSignature className="h-4 w-4 text-gray-400" />
                        <Link href={`/contracts/${project.linked_contract_id}`} className="text-blue-600 hover:underline">
                          {project.linked_contract_number}
                        </Link>
                      </p>
                    </div>
                  )}

                  {project.linked_invoice_number && (
                    <div>
                      <label className="text-sm text-gray-500">Linked Invoice</label>
                      <p className="mt-1 flex items-center gap-2">
                        <FileText className="h-4 w-4 text-gray-400" />
                        <Link href={`/invoices/${project.linked_invoice_id}`} className="text-blue-600 hover:underline">
                          {project.linked_invoice_number}
                        </Link>
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Task Stats */}
            {project.task_stats && project.task_stats.total_tasks > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Task Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold">{project.task_stats.todo_count}</p>
                      <p className="text-sm text-gray-500">To Do</p>
                    </div>
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">{project.task_stats.in_progress_count}</p>
                      <p className="text-sm text-gray-500">In Progress</p>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded-lg">
                      <p className="text-2xl font-bold text-purple-600">{project.task_stats.review_count}</p>
                      <p className="text-sm text-gray-500">Review</p>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <p className="text-2xl font-bold text-green-600">{project.task_stats.completed_count}</p>
                      <p className="text-sm text-gray-500">Completed</p>
                    </div>
                    <div className="text-center p-3 bg-red-50 rounded-lg">
                      <p className="text-2xl font-bold text-red-600">{project.task_stats.blocked_count}</p>
                      <p className="text-sm text-gray-500">Blocked</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Tasks Tab */}
          <TabsContent value="tasks" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex gap-2">
                <Button
                  variant={taskView === "kanban" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setTaskView("kanban")}
                >
                  <LayoutGrid className="h-4 w-4 mr-2" />
                  Kanban
                </Button>
                <Button
                  variant={taskView === "list" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setTaskView("list")}
                >
                  <List className="h-4 w-4 mr-2" />
                  List
                </Button>
              </div>
            </div>

            {taskView === "kanban" ? (
              <TaskKanbanView
                projectId={project.id}
                tasks={project.tasks || []}
                onTasksChange={handleTasksChange}
              />
            ) : (
              <TaskListView
                projectId={project.id}
                tasks={project.tasks || []}
                onTasksChange={handleTasksChange}
              />
            )}
          </TabsContent>

          {/* Activity Tab */}
          <TabsContent value="activity">
            <Card>
              <CardHeader>
                <CardTitle>Activity Log</CardTitle>
              </CardHeader>
              <CardContent>
                {project.activity_logs?.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No activity yet</p>
                ) : (
                  <div className="space-y-4">
                    {project.activity_logs?.map((log) => (
                      <div key={log.id} className="flex items-start gap-4 border-l-2 border-gray-200 pl-4">
                        <div className="flex-1">
                          <p className="font-medium">
                            {ACTION_LABELS[log.action] || log.action}
                          </p>
                          {log.details && (
                            <p className="text-sm text-gray-500">
                              {log.details.task_title && `Task: ${log.details.task_title}`}
                              {log.details.old_status && log.details.new_status &&
                                ` (${log.details.old_status} → ${log.details.new_status})`}
                              {log.details.hours && ` (${log.details.hours}h)`}
                            </p>
                          )}
                          <p className="text-xs text-gray-400 mt-1">
                            {formatDateTime(log.created_at)}
                            {log.actor && ` by ${log.actor}`}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </Shell>
  );
}
