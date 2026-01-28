"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { projectTemplatesApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  ArrowLeft,
  Plus,
  Edit,
  Copy,
  Trash2,
  FileText,
  ListTodo,
  Clock,
} from "lucide-react";
import Link from "next/link";

interface TaskTemplate {
  title: string;
  description?: string;
  estimated_hours?: number;
  order_index: number;
}

interface ProjectTemplate {
  id: string;
  name: string;
  description: string | null;
  project_type: string;
  default_duration_days: number;
  estimated_hours: number | null;
  task_templates: TaskTemplate[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const PROJECT_TYPES = [
  { value: "coaching", label: "Coaching" },
  { value: "workshop", label: "Workshop" },
  { value: "consulting", label: "Consulting" },
  { value: "speaking", label: "Speaking" },
];

export default function ProjectTemplatesPage() {
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ProjectTemplate | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [projectType, setProjectType] = useState("coaching");
  const [defaultDurationDays, setDefaultDurationDays] = useState("30");
  const [estimatedHours, setEstimatedHours] = useState("");
  const [taskTemplates, setTaskTemplates] = useState<TaskTemplate[]>([]);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const data = await projectTemplatesApi.list(token, { active_only: false });
      setTemplates(data);
    } catch (err) {
      console.error("Failed to load templates:", err);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setName("");
    setDescription("");
    setProjectType("coaching");
    setDefaultDurationDays("30");
    setEstimatedHours("");
    setTaskTemplates([]);
    setEditingTemplate(null);
  };

  const openCreateDialog = () => {
    resetForm();
    setDialogOpen(true);
  };

  const openEditDialog = async (templateId: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const template = await projectTemplatesApi.get(token, templateId);
      setEditingTemplate(template);
      setName(template.name);
      setDescription(template.description || "");
      setProjectType(template.project_type);
      setDefaultDurationDays(template.default_duration_days.toString());
      setEstimatedHours(template.estimated_hours?.toString() || "");
      setTaskTemplates(template.task_templates || []);
      setDialogOpen(true);
    } catch (err: any) {
      alert(err.message || "Failed to load template");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) return;

    setSubmitting(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const data = {
        name,
        description: description || undefined,
        project_type: projectType,
        default_duration_days: parseInt(defaultDurationDays),
        estimated_hours: estimatedHours ? parseFloat(estimatedHours) : undefined,
        task_templates: taskTemplates,
      };

      if (editingTemplate) {
        await projectTemplatesApi.update(token, editingTemplate.id, data);
      } else {
        await projectTemplatesApi.create(token, data);
      }

      setDialogOpen(false);
      resetForm();
      await loadTemplates();
    } catch (err: any) {
      alert(err.message || "Failed to save template");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDuplicate = async (templateId: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await projectTemplatesApi.duplicate(token, templateId);
      await loadTemplates();
    } catch (err: any) {
      alert(err.message || "Failed to duplicate template");
    }
  };

  const handleDelete = async (templateId: string) => {
    if (!confirm("Are you sure you want to delete this template?")) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await projectTemplatesApi.delete(token, templateId);
      await loadTemplates();
    } catch (err: any) {
      alert(err.message || "Failed to delete template");
    }
  };

  const addTaskTemplate = () => {
    setTaskTemplates([
      ...taskTemplates,
      { title: "", order_index: taskTemplates.length },
    ]);
  };

  const updateTaskTemplate = (index: number, updates: Partial<TaskTemplate>) => {
    const newTemplates = [...taskTemplates];
    newTemplates[index] = { ...newTemplates[index], ...updates };
    setTaskTemplates(newTemplates);
  };

  const removeTaskTemplate = (index: number) => {
    setTaskTemplates(taskTemplates.filter((_, i) => i !== index));
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
          <div className="flex items-center gap-4">
            <Link href="/projects">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold">Project Templates</h1>
              <p className="text-gray-500">Reusable project structures with pre-defined tasks</p>
            </div>
          </div>
          <Button onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            New Template
          </Button>
        </div>

        {/* Templates List */}
        <Card>
          <CardContent className="p-0">
            {templates.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <FileText className="h-12 w-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900">No templates yet</h3>
                <p className="text-gray-500 mt-1">
                  Create your first template to streamline project creation
                </p>
                <Button className="mt-4" onClick={openCreateDialog}>
                  <Plus className="h-4 w-4 mr-2" />
                  New Template
                </Button>
              </div>
            ) : (
              <div className="divide-y">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className="flex items-center justify-between p-4 hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-100">
                        <FileText className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{template.name}</h3>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <span>{PROJECT_TYPES.find((t) => t.value === template.project_type)?.label}</span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {template.default_duration_days} days
                          </span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <ListTodo className="h-3 w-3" />
                            {template.task_templates?.length || 0} tasks
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      {!template.is_active && (
                        <Badge variant="outline" className="text-gray-500">
                          Inactive
                        </Badge>
                      )}
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditDialog(template.id)}
                          title="Edit"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDuplicate(template.id)}
                          title="Duplicate"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(template.id)}
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4 text-gray-400 hover:text-red-500" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Create/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingTemplate ? "Edit Template" : "New Project Template"}
              </DialogTitle>
              <DialogDescription>
                Define a reusable project structure with pre-defined tasks
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Info */}
              <div className="space-y-4">
                <div>
                  <Label htmlFor="name">Template Name *</Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g., Executive Coaching 12-Week"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Brief description of when to use this template"
                    rows={2}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="projectType">Project Type</Label>
                    <Select value={projectType} onValueChange={setProjectType}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PROJECT_TYPES.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="defaultDurationDays">Default Duration (days)</Label>
                    <Input
                      id="defaultDurationDays"
                      type="number"
                      value={defaultDurationDays}
                      onChange={(e) => setDefaultDurationDays(e.target.value)}
                      min="1"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="estimatedHours">Estimated Hours</Label>
                  <Input
                    id="estimatedHours"
                    type="number"
                    value={estimatedHours}
                    onChange={(e) => setEstimatedHours(e.target.value)}
                    placeholder="Total estimated hours"
                    step="0.5"
                    min="0"
                  />
                </div>
              </div>

              {/* Task Templates */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Task Templates</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addTaskTemplate}>
                    <Plus className="h-4 w-4 mr-1" />
                    Add Task
                  </Button>
                </div>

                {taskTemplates.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">
                    No tasks defined. Add tasks to include them when creating projects from this template.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {taskTemplates.map((task, index) => (
                      <div
                        key={index}
                        className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
                      >
                        <span className="text-sm text-gray-400 mt-2">{index + 1}.</span>
                        <div className="flex-1 space-y-2">
                          <Input
                            value={task.title}
                            onChange={(e) =>
                              updateTaskTemplate(index, { title: e.target.value })
                            }
                            placeholder="Task title"
                          />
                          <div className="grid grid-cols-2 gap-2">
                            <Input
                              value={task.description || ""}
                              onChange={(e) =>
                                updateTaskTemplate(index, { description: e.target.value })
                              }
                              placeholder="Description (optional)"
                            />
                            <Input
                              type="number"
                              value={task.estimated_hours || ""}
                              onChange={(e) =>
                                updateTaskTemplate(index, {
                                  estimated_hours: e.target.value
                                    ? parseFloat(e.target.value)
                                    : undefined,
                                })
                              }
                              placeholder="Hours (optional)"
                              step="0.5"
                              min="0"
                            />
                          </div>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeTaskTemplate(index)}
                        >
                          <Trash2 className="h-4 w-4 text-gray-400 hover:text-red-500" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting || !name}>
                  {submitting
                    ? "Saving..."
                    : editingTemplate
                    ? "Save Changes"
                    : "Create Template"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </Shell>
  );
}
