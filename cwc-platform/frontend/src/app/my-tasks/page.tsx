"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { workspaceApi, notificationsApi, MyTask, AppNotification } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CheckCircle2, Bell, AlertTriangle } from "lucide-react";

const GROUPS: { key: string; label: string; tone: string }[] = [
  { key: "overdue", label: "Overdue", tone: "text-destructive" },
  { key: "today", label: "Due today", tone: "text-primary" },
  { key: "upcoming", label: "Upcoming", tone: "text-foreground" },
  { key: "no_due_date", label: "No due date", tone: "text-muted-foreground" },
];

const PRIORITY_TONE: Record<string, string> = {
  urgent: "bg-destructive/15 text-destructive",
  high: "bg-warning/15 text-warning",
  medium: "bg-muted text-muted-foreground",
  low: "bg-muted text-muted-foreground",
};

export default function MyTasksPage() {
  const { token } = useAuth();
  const [groups, setGroups] = useState<Record<string, MyTask[]>>({});
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const [tasks, feed] = await Promise.all([
        workspaceApi.myTasks(token),
        notificationsApi.list(token),
      ]);
      setGroups(tasks);
      setNotifications(feed.items);
      setUnread(feed.unread_count);
    } catch (err: any) {
      setError(err.message || "Could not load your work");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  const complete = async (taskId: string) => {
    if (!token) return;
    try {
      await workspaceApi.setStatus(token, taskId, "completed");
      load();
    } catch (err: any) {
      setError(err.message || "Could not update the task");
    }
  };

  const markAllRead = async () => {
    if (!token) return;
    await notificationsApi.markAllRead(token);
    load();
  };

  const total = GROUPS.reduce((sum, g) => sum + (groups[g.key]?.length || 0), 0);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">My Tasks</h1>
        <p className="text-muted-foreground">
          {total === 0
            ? "Nothing assigned to you right now."
            : `${total} task${total === 1 ? "" : "s"} assigned to you.`}
        </p>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" aria-hidden />
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          {GROUPS.map((group) => {
            const tasks = groups[group.key] || [];
            if (tasks.length === 0) return null;
            return (
              <Card key={group.key}>
                <CardHeader className="pb-3">
                  <CardTitle className={`text-base ${group.tone}`}>
                    {group.label}
                    <span className="ml-2 text-sm text-muted-foreground">
                      {tasks.length}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {tasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center justify-between gap-3 border border-border rounded-md px-3 py-2"
                    >
                      <div className="min-w-0">
                        <Link
                          href={`/projects/${task.project_id}`}
                          className="font-medium hover:text-primary"
                        >
                          {task.title}
                        </Link>
                        <div className="text-sm text-muted-foreground">
                          {task.task_number}
                          {task.due_date ? ` · due ${task.due_date}` : ""}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Badge
                          variant="outline"
                          className={PRIORITY_TONE[task.priority] || ""}
                        >
                          {task.priority}
                        </Badge>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => complete(task.id)}
                          aria-label={`Mark ${task.title} complete`}
                        >
                          <CheckCircle2 className="h-4 w-4" aria-hidden />
                        </Button>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            );
          })}

          {total === 0 && (
            <Card>
              <CardContent className="py-10 text-center text-muted-foreground">
                You're all clear. Tasks assigned to you will show up here.
              </CardContent>
            </Card>
          )}
        </div>

        <Card className="lg:col-span-1 h-fit">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Bell className="h-4 w-4" aria-hidden />
              Activity
              {unread > 0 && (
                <Badge className="bg-primary/15 text-primary" variant="outline">
                  {unread} new
                </Badge>
              )}
            </CardTitle>
            {unread > 0 && (
              <Button size="sm" variant="ghost" onClick={markAllRead}>
                Mark all read
              </Button>
            )}
          </CardHeader>
          <CardContent className="space-y-2">
            {notifications.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Mentions and assignments will appear here.
              </p>
            )}
            {notifications.slice(0, 15).map((n) => (
              <div
                key={n.id}
                className={`text-sm border-l-2 pl-3 py-1 ${
                  n.read ? "border-border text-muted-foreground" : "border-primary"
                }`}
              >
                {n.message}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
