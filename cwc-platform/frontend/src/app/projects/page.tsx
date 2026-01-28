"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { projectsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  FolderKanban,
  Plus,
  CheckCircle,
  Clock,
  Play,
  Pause,
  Copy,
  Eye,
  ListTodo,
  Calendar,
} from "lucide-react";
import Link from "next/link";

interface Project {
  id: string;
  project_number: string;
  title: string;
  project_type: string;
  status: string;
  contact_id: string;
  contact_name: string | null;
  organization_name: string | null;
  start_date: string | null;
  target_end_date: string | null;
  progress_percent: number;
  task_count: number;
  created_at: string;
}

interface ProjectStats {
  total_projects: number;
  planning_count: number;
  active_count: number;
  paused_count: number;
  completed_count: number;
  total_estimated_hours: number;
  total_actual_hours: number;
  started_this_month: number;
  completed_this_month: number;
}

const STATUS_COLORS: Record<string, string> = {
  planning: "bg-gray-100 text-gray-800",
  active: "bg-blue-100 text-blue-800",
  paused: "bg-yellow-100 text-yellow-800",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  planning: <Clock className="h-4 w-4" />,
  active: <Play className="h-4 w-4" />,
  paused: <Pause className="h-4 w-4" />,
  completed: <CheckCircle className="h-4 w-4" />,
  cancelled: <Clock className="h-4 w-4" />,
};

const PROJECT_TYPE_LABELS: Record<string, string> = {
  coaching: "Coaching",
  workshop: "Workshop",
  consulting: "Consulting",
  speaking: "Speaking",
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<ProjectStats | null>(null);
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

      const [projectsData, statsData] = await Promise.all([
        projectsApi.list(token, {
          status: filter || undefined,
          search: search || undefined,
        }),
        projectsApi.getStats(token),
      ]);

      setProjects(projectsData);
      setStats(statsData);
    } catch (err) {
      console.error("Failed to load projects:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDuplicate = async (id: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await projectsApi.duplicate(token, id);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to duplicate project");
    }
  };

  const getProgressColor = (percent: number) => {
    if (percent >= 100) return "bg-green-500";
    if (percent >= 75) return "bg-blue-500";
    if (percent >= 50) return "bg-yellow-500";
    return "bg-gray-300";
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
            <h1 className="text-2xl font-bold">Projects</h1>
            <p className="text-gray-500">Manage projects and track progress</p>
          </div>
          <div className="flex gap-2">
            <Link href="/projects/templates">
              <Button variant="outline">
                <FolderKanban className="h-4 w-4 mr-2" />
                Templates
              </Button>
            </Link>
            <Link href="/projects/new">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Project
              </Button>
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Total Projects
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <FolderKanban className="h-5 w-5 text-gray-400" />
                <span className="text-2xl font-bold">{stats?.total_projects || 0}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Active
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Play className="h-5 w-5 text-blue-500" />
                <span className="text-2xl font-bold text-blue-600">
                  {stats?.active_count || 0}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Completed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="text-2xl font-bold text-green-600">
                  {stats?.completed_count || 0}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Hours Logged
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-purple-500" />
                <span className="text-2xl font-bold text-purple-600">
                  {Math.round(stats?.total_actual_hours || 0)}h
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex gap-4 items-center">
          <Input
            placeholder="Search projects..."
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
              variant={filter === "planning" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("planning")}
            >
              Planning
            </Button>
            <Button
              variant={filter === "active" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("active")}
            >
              Active
            </Button>
            <Button
              variant={filter === "paused" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("paused")}
            >
              Paused
            </Button>
            <Button
              variant={filter === "completed" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("completed")}
            >
              Completed
            </Button>
          </div>
        </div>

        {/* Projects List */}
        <Card>
          <CardContent className="p-0">
            {projects.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <FolderKanban className="h-12 w-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900">No projects yet</h3>
                <p className="text-gray-500 mt-1">
                  Create your first project to get started
                </p>
                <Link href="/projects/new">
                  <Button className="mt-4">
                    <Plus className="h-4 w-4 mr-2" />
                    New Project
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="divide-y">
                {projects.map((project) => (
                  <div
                    key={project.id}
                    className="flex items-center justify-between p-4 hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-100">
                        {STATUS_ICONS[project.status] || <FolderKanban className="h-4 w-4" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <Link href={`/projects/${project.id}`}>
                          <h3 className="font-medium text-gray-900 hover:text-blue-600 truncate">
                            {project.title}
                          </h3>
                        </Link>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <span>{project.project_number}</span>
                          <span>•</span>
                          <span>{PROJECT_TYPE_LABELS[project.project_type] || project.project_type}</span>
                          <span>•</span>
                          <span>
                            {project.contact_name || "Unknown Contact"}
                            {project.organization_name && ` (${project.organization_name})`}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-6">
                      {/* Progress */}
                      <div className="w-32">
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-gray-500">Progress</span>
                          <span className="font-medium">{project.progress_percent}%</span>
                        </div>
                        <Progress value={project.progress_percent} className="h-2" />
                      </div>

                      {/* Tasks */}
                      <div className="flex items-center gap-1 text-sm text-gray-500 w-20">
                        <ListTodo className="h-4 w-4" />
                        <span>{project.task_count} tasks</span>
                      </div>

                      {/* Dates */}
                      {project.target_end_date && (
                        <div className="flex items-center gap-1 text-sm text-gray-500 w-28">
                          <Calendar className="h-4 w-4" />
                          <span>{formatDate(project.target_end_date)}</span>
                        </div>
                      )}

                      {/* Status Badge */}
                      <Badge className={STATUS_COLORS[project.status]}>
                        {project.status}
                      </Badge>

                      {/* Actions */}
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDuplicate(project.id)}
                          title="Duplicate"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Link href={`/projects/${project.id}`}>
                          <Button variant="ghost" size="sm" title="View">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                      </div>
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
