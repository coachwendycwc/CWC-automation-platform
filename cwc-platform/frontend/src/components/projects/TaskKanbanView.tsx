"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { tasksApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  Plus,
  Clock,
  User,
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

interface TaskKanbanViewProps {
  projectId: string;
  tasks: Task[];
  onTasksChange: () => void;
}

const COLUMNS = [
  { id: "todo", title: "To Do", color: "bg-gray-500" },
  { id: "in_progress", title: "In Progress", color: "bg-blue-500" },
  { id: "review", title: "Review", color: "bg-purple-500" },
  { id: "completed", title: "Done", color: "bg-green-500" },
];

const PRIORITY_COLORS: Record<string, string> = {
  low: "border-l-gray-300",
  medium: "border-l-yellow-400",
  high: "border-l-orange-500",
  urgent: "border-l-red-500",
};

export function TaskKanbanView({ projectId, tasks, onTasksChange }: TaskKanbanViewProps) {
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [addingToColumn, setAddingToColumn] = useState<string | null>(null);
  const [draggedTask, setDraggedTask] = useState<Task | null>(null);

  const getTasksByStatus = (status: string) => {
    return tasks
      .filter((task) => task.status === status)
      .sort((a, b) => a.order_index - b.order_index);
  };

  const handleCreateTask = async (status: string) => {
    if (!newTaskTitle.trim()) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await tasksApi.create(token, projectId, {
        title: newTaskTitle.trim(),
        status,
        priority: "medium",
      });

      setNewTaskTitle("");
      setAddingToColumn(null);
      onTasksChange();
    } catch (err: any) {
      alert(err.message || "Failed to create task");
    }
  };

  const handleDragStart = (e: React.DragEvent, task: Task) => {
    setDraggedTask(task);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDrop = async (e: React.DragEvent, newStatus: string) => {
    e.preventDefault();
    if (!draggedTask) return;

    if (draggedTask.status === newStatus) {
      setDraggedTask(null);
      return;
    }

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      // Get tasks in the target column to calculate order
      const tasksInColumn = getTasksByStatus(newStatus);
      const newOrderIndex = tasksInColumn.length;

      await tasksApi.reorder(token, [
        {
          id: draggedTask.id,
          status: newStatus,
          order_index: newOrderIndex,
        },
      ]);

      onTasksChange();
    } catch (err: any) {
      alert(err.message || "Failed to move task");
    } finally {
      setDraggedTask(null);
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

  return (
    <div className="grid grid-cols-4 gap-4">
      {COLUMNS.map((column) => {
        const columnTasks = getTasksByStatus(column.id);

        return (
          <div
            key={column.id}
            className="bg-gray-50 rounded-lg p-4 min-h-[400px]"
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, column.id)}
          >
            {/* Column Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${column.color}`} />
                <h3 className="font-medium">{column.title}</h3>
                <span className="text-sm text-gray-500">({columnTasks.length})</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setAddingToColumn(column.id)}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {/* Add Task Form */}
            {addingToColumn === column.id && (
              <div className="mb-4 p-3 bg-white rounded-lg border shadow-sm">
                <Input
                  placeholder="Task title..."
                  value={newTaskTitle}
                  onChange={(e) => setNewTaskTitle(e.target.value)}
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleCreateTask(column.id);
                    if (e.key === "Escape") {
                      setAddingToColumn(null);
                      setNewTaskTitle("");
                    }
                  }}
                />
                <div className="flex gap-2 mt-2">
                  <Button
                    size="sm"
                    onClick={() => handleCreateTask(column.id)}
                    disabled={!newTaskTitle.trim()}
                  >
                    Add
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setAddingToColumn(null);
                      setNewTaskTitle("");
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}

            {/* Tasks */}
            <div className="space-y-3">
              {columnTasks.map((task) => (
                <div
                  key={task.id}
                  className={`bg-white rounded-lg border p-3 shadow-sm cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow border-l-4 ${
                    PRIORITY_COLORS[task.priority]
                  } ${draggedTask?.id === task.id ? "opacity-50" : ""}`}
                  draggable
                  onDragStart={(e) => handleDragStart(e, task)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{task.title}</p>
                      {task.description && (
                        <p className="text-xs text-gray-500 truncate mt-1">
                          {task.description}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100"
                      onClick={() => handleDeleteTask(task.id)}
                    >
                      <Trash2 className="h-3 w-3 text-gray-400 hover:text-red-500" />
                    </Button>
                  </div>

                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <span className="text-xs text-gray-400">{task.task_number}</span>

                    {task.due_date && (
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDate(task.due_date)}
                      </span>
                    )}

                    {task.assigned_to && (
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {task.assigned_to}
                      </span>
                    )}

                    {task.actual_hours > 0 && (
                      <Badge variant="outline" className="text-xs">
                        {task.actual_hours}h
                      </Badge>
                    )}
                  </div>
                </div>
              ))}

              {columnTasks.length === 0 && (
                <div className="text-center py-8 text-gray-400 text-sm">
                  Drop tasks here
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
