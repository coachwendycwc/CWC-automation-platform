"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { tasksApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  Plus,
  CheckCircle,
  Clock,
  AlertTriangle,
  Trash2,
  GripVertical,
} from "lucide-react";

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

interface TaskListViewProps {
  projectId: string;
  tasks: Task[];
  onTasksChange: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  todo: "bg-gray-100 text-gray-800",
  in_progress: "bg-blue-100 text-blue-800",
  review: "bg-purple-100 text-purple-800",
  completed: "bg-green-100 text-green-800",
  blocked: "bg-red-100 text-red-800",
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-gray-100 text-gray-600",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-orange-100 text-orange-700",
  urgent: "bg-red-100 text-red-700",
};

export function TaskListView({ projectId, tasks, onTasksChange }: TaskListViewProps) {
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const [showAddTask, setShowAddTask] = useState(false);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    setCreating(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await tasksApi.create(token, projectId, {
        title: newTaskTitle.trim(),
        priority: "medium",
      });

      setNewTaskTitle("");
      setShowAddTask(false);
      onTasksChange();
    } catch (err: any) {
      alert(err.message || "Failed to create task");
    } finally {
      setCreating(false);
    }
  };

  const handleToggleComplete = async (task: Task) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const newStatus = task.status === "completed" ? "todo" : "completed";
      await tasksApi.update(token, task.id, { status: newStatus });
      onTasksChange();
    } catch (err: any) {
      alert(err.message || "Failed to update task");
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!confirm("Are you sure you want to delete this task?")) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await tasksApi.delete(token, taskId);
      onTasksChange();
    } catch (err: any) {
      alert(err.message || "Failed to delete task");
    }
  };

  const sortedTasks = [...tasks].sort((a, b) => {
    // Completed tasks at the bottom
    if (a.status === "completed" && b.status !== "completed") return 1;
    if (a.status !== "completed" && b.status === "completed") return -1;
    // Then by order index
    return a.order_index - b.order_index;
  });

  return (
    <Card>
      <CardContent className="p-0">
        {/* Add Task */}
        <div className="border-b p-4">
          {showAddTask ? (
            <form onSubmit={handleCreateTask} className="flex gap-2">
              <Input
                placeholder="Task title..."
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                autoFocus
                disabled={creating}
              />
              <Button type="submit" disabled={creating || !newTaskTitle.trim()}>
                Add
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setShowAddTask(false);
                  setNewTaskTitle("");
                }}
              >
                Cancel
              </Button>
            </form>
          ) : (
            <Button variant="outline" onClick={() => setShowAddTask(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Task
            </Button>
          )}
        </div>

        {/* Task List */}
        {tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <CheckCircle className="h-12 w-12 text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No tasks yet</h3>
            <p className="text-gray-500 mt-1">Add your first task to get started</p>
          </div>
        ) : (
          <div className="divide-y">
            {sortedTasks.map((task) => (
              <div
                key={task.id}
                className={`flex items-center gap-4 p-4 hover:bg-gray-50 ${
                  task.status === "completed" ? "opacity-60" : ""
                }`}
              >
                <Checkbox
                  checked={task.status === "completed"}
                  onCheckedChange={() => handleToggleComplete(task)}
                />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-medium ${
                        task.status === "completed" ? "line-through text-gray-500" : ""
                      }`}
                    >
                      {task.title}
                    </span>
                    <span className="text-xs text-gray-400">{task.task_number}</span>
                  </div>
                  {task.description && (
                    <p className="text-sm text-gray-500 truncate">{task.description}</p>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {task.due_date && (
                    <span className="text-sm text-gray-500 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(task.due_date)}
                    </span>
                  )}

                  <Badge className={PRIORITY_COLORS[task.priority]}>{task.priority}</Badge>
                  <Badge className={STATUS_COLORS[task.status]}>{task.status.replace("_", " ")}</Badge>

                  {task.actual_hours > 0 && (
                    <span className="text-sm text-gray-500">{task.actual_hours}h</span>
                  )}

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteTask(task.id)}
                  >
                    <Trash2 className="h-4 w-4 text-gray-400 hover:text-red-500" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
