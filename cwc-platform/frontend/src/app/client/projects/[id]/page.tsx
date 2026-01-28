"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import Link from "next/link";
import { ArrowLeft, CheckCircle, Circle, Clock } from "lucide-react";

interface Task {
  id: string;
  title: string;
  status: string;
  due_date: string | null;
}

interface Project {
  id: string;
  name: string;
  description: string | null;
  status: string;
  progress: number;
  created_at: string;
  tasks: Task[];
}

const STATUS_COLORS: Record<string, string> = {
  planning: "bg-yellow-100 text-yellow-800",
  in_progress: "bg-blue-100 text-blue-800",
  review: "bg-purple-100 text-purple-800",
  completed: "bg-green-100 text-green-800",
  on_hold: "bg-gray-100 text-gray-800",
  cancelled: "bg-red-100 text-red-800",
};

const TASK_STATUS_ICONS: Record<string, React.ReactNode> = {
  todo: <Circle className="h-4 w-4 text-gray-400" />,
  in_progress: <Clock className="h-4 w-4 text-blue-500" />,
  review: <Clock className="h-4 w-4 text-purple-500" />,
  completed: <CheckCircle className="h-4 w-4 text-green-500" />,
};

export default function ClientProjectDetailPage() {
  const params = useParams();
  const { sessionToken } = useClientAuth();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProject = async () => {
      if (!sessionToken || !projectId) return;

      try {
        const data = await clientPortalApi.getProject(sessionToken, projectId);
        setProject(data);
      } catch (error) {
        console.error("Failed to load project:", error);
      } finally {
        setLoading(false);
      }
    };

    loadProject();
  }, [sessionToken, projectId]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading project...</div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Project not found</div>
      </div>
    );
  }

  const completedTasks = project.tasks.filter(
    (t) => t.status === "completed"
  ).length;
  const totalTasks = project.tasks.length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/client/projects">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{project.name}</h1>
              <Badge className={STATUS_COLORS[project.status]}>
                {project.status.replace("_", " ")}
              </Badge>
            </div>
            <p className="text-gray-500">
              Started {formatDate(project.created_at)}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          {project.description && (
            <Card>
              <CardHeader>
                <CardTitle>About This Project</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700">{project.description}</p>
              </CardContent>
            </Card>
          )}

          {/* Tasks */}
          <Card>
            <CardHeader>
              <CardTitle>Tasks</CardTitle>
            </CardHeader>
            <CardContent>
              {project.tasks.length === 0 ? (
                <p className="text-gray-500 text-center py-4">
                  No tasks to display
                </p>
              ) : (
                <div className="space-y-2">
                  {project.tasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center justify-between p-3 rounded-lg border"
                    >
                      <div className="flex items-center gap-3">
                        {TASK_STATUS_ICONS[task.status] || (
                          <Circle className="h-4 w-4 text-gray-400" />
                        )}
                        <span
                          className={
                            task.status === "completed"
                              ? "text-gray-500 line-through"
                              : ""
                          }
                        >
                          {task.title}
                        </span>
                      </div>
                      {task.due_date && (
                        <span className="text-sm text-gray-500">
                          Due {formatDate(task.due_date)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Progress</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <p className="text-4xl font-bold text-purple-600">
                  {Math.round(project.progress)}%
                </p>
                <p className="text-sm text-gray-500">Complete</p>
              </div>

              <Progress value={project.progress} className="h-3" />

              <div className="text-center text-sm text-gray-500">
                {completedTasks} of {totalTasks} tasks completed
              </div>

              <div className="border-t pt-4 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <Circle className="h-3 w-3 text-gray-400" />
                    <span>To Do</span>
                  </div>
                  <span>
                    {project.tasks.filter((t) => t.status === "todo").length}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <Clock className="h-3 w-3 text-blue-500" />
                    <span>In Progress</span>
                  </div>
                  <span>
                    {
                      project.tasks.filter((t) => t.status === "in_progress")
                        .length
                    }
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span>Completed</span>
                  </div>
                  <span>{completedTasks}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
