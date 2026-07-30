"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  workspaceApi,
  staffApi,
  tasksApi,
  StaffMember,
  TaskComment,
} from "@/lib/api";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { MessageSquare, Send, AlertTriangle } from "lucide-react";

const UNASSIGNED = "__unassigned__";

interface TaskDetailDialogProps {
  taskId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onChange?: () => void;
}

export function TaskDetailDialog({
  taskId,
  open,
  onOpenChange,
  onChange,
}: TaskDetailDialogProps) {
  const { token } = useAuth();
  const [task, setTask] = useState<any | null>(null);
  const [comments, setComments] = useState<TaskComment[]>([]);
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [posting, setPosting] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!token || !taskId) return;
    setLoading(true);
    setError("");
    try {
      const [taskData, commentData, staffData] = await Promise.all([
        tasksApi.get(token, taskId),
        workspaceApi.listComments(token, taskId),
        staffApi.list(token),
      ]);
      setTask(taskData);
      setComments(commentData);
      setStaff(staffData);
    } catch (err: any) {
      setError(err.message || "Could not load this task");
    } finally {
      setLoading(false);
    }
  }, [token, taskId]);

  useEffect(() => {
    if (open && taskId) load();
  }, [open, taskId, load]);

  const assign = async (value: string) => {
    if (!token || !taskId) return;
    const assigneeId = value === UNASSIGNED ? null : value;
    try {
      await workspaceApi.assign(token, taskId, assigneeId);
      await load();
      onChange?.();
    } catch (err: any) {
      setError(err.message || "Could not assign this task");
    }
  };

  const postComment = async () => {
    if (!token || !taskId || !draft.trim()) return;
    setPosting(true);
    setError("");
    try {
      await workspaceApi.addComment(token, taskId, draft.trim());
      setDraft("");
      const refreshed = await workspaceApi.listComments(token, taskId);
      setComments(refreshed);
    } catch (err: any) {
      setError(err.message || "Could not post your comment");
    } finally {
      setPosting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{task?.title || "Task"}</DialogTitle>
        </DialogHeader>

        {error && (
          <div className="bg-destructive/10 border border-destructive/20 text-destructive px-3 py-2 rounded text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" aria-hidden />
            {error}
          </div>
        )}

        {loading && !task ? (
          <div className="space-y-3">
            <Skeleton className="h-6 w-2/3" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : (
          task && (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                <span>{task.task_number}</span>
                <Badge variant="outline">{task.status}</Badge>
                <Badge variant="outline">{task.priority}</Badge>
                {task.due_date && <span>due {task.due_date}</span>}
              </div>

              {task.description && (
                <p className="text-sm whitespace-pre-wrap">{task.description}</p>
              )}

              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">Assigned to</span>
                <Select
                  value={task.assignee_id || UNASSIGNED}
                  onValueChange={assign}
                >
                  <SelectTrigger className="w-64">
                    <SelectValue placeholder="Unassigned" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={UNASSIGNED}>Unassigned</SelectItem>
                    {staff.map((member) => (
                      <SelectItem key={member.id} value={member.id}>
                        {member.name}
                        {member.role === "assistant" ? " (assistant)" : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-3">
                <h3 className="text-sm font-medium flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" aria-hidden />
                  Comments
                  {comments.length > 0 && (
                    <span className="text-muted-foreground">{comments.length}</span>
                  )}
                </h3>

                {comments.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No comments yet. Mention someone with @their-email to notify them.
                  </p>
                )}

                <div className="space-y-3">
                  {comments.map((comment) => (
                    <div key={comment.id} className="border-l-2 border-border pl-3">
                      <div className="text-sm font-medium">
                        {comment.author_name}
                        <span className="ml-2 text-xs text-muted-foreground font-normal">
                          {comment.created_at
                            ? new Date(comment.created_at).toLocaleString()
                            : ""}
                        </span>
                      </div>
                      <p className="text-sm whitespace-pre-wrap">{comment.body}</p>
                    </div>
                  ))}
                </div>

                <div className="space-y-2">
                  <Textarea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    placeholder="Add a comment — @email to notify someone"
                    rows={3}
                  />
                  <Button
                    size="sm"
                    onClick={postComment}
                    disabled={posting || !draft.trim()}
                  >
                    <Send className="h-4 w-4 mr-2" aria-hidden />
                    {posting ? "Posting..." : "Comment"}
                  </Button>
                </div>
              </div>
            </div>
          )
        )}
      </DialogContent>
    </Dialog>
  );
}
