"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { offboardingTemplatesApi } from "@/lib/api";
import {
  ArrowLeft,
  Plus,
  Edit,
  Trash2,
  User,
  FolderKanban,
  FileText,
  X,
  Check,
} from "lucide-react";
import Link from "next/link";

interface OffboardingTemplate {
  id: string;
  name: string;
  workflow_type: string;
  checklist_items: string[];
  completion_email_subject: string;
  completion_email_body: string;
  survey_email_subject: string;
  survey_email_body: string;
  testimonial_email_subject: string;
  testimonial_email_body: string;
  survey_delay_days: number;
  testimonial_delay_days: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

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

export default function OffboardingTemplatesPage() {
  const [templates, setTemplates] = useState<OffboardingTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<OffboardingTemplate | null>(null);
  const [saving, setSaving] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    workflow_type: "client",
    checklist_items: [""],
    completion_email_subject: "Thank You for Working with Coaching Women of Color",
    completion_email_body: "Dear {{client_name}},\n\nThank you for the opportunity to work together...",
    survey_email_subject: "We'd Love Your Feedback!",
    survey_email_body: "Dear {{client_name}},\n\nYour experience matters to us. Please take a few minutes to share your feedback.",
    testimonial_email_subject: "Would You Share Your Experience?",
    testimonial_email_body: "Dear {{client_name}},\n\nWe're so glad we could help you. Would you consider sharing your story?",
    survey_delay_days: 3,
    testimonial_delay_days: 7,
    is_active: true,
  });

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const data = await offboardingTemplatesApi.list(token);
      setTemplates(data);
    } catch (err) {
      console.error("Failed to load templates:", err);
    } finally {
      setLoading(false);
    }
  };

  const openNewDialog = () => {
    setEditingTemplate(null);
    setFormData({
      name: "",
      workflow_type: "client",
      checklist_items: [""],
      completion_email_subject: "Thank You for Working with Coaching Women of Color",
      completion_email_body: "Dear {{client_name}},\n\nThank you for the opportunity to work together...",
      survey_email_subject: "We'd Love Your Feedback!",
      survey_email_body: "Dear {{client_name}},\n\nYour experience matters to us. Please take a few minutes to share your feedback.",
      testimonial_email_subject: "Would You Share Your Experience?",
      testimonial_email_body: "Dear {{client_name}},\n\nWe're so glad we could help you. Would you consider sharing your story?",
      survey_delay_days: 3,
      testimonial_delay_days: 7,
      is_active: true,
    });
    setDialogOpen(true);
  };

  const openEditDialog = (template: OffboardingTemplate) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      workflow_type: template.workflow_type,
      checklist_items: template.checklist_items.length > 0 ? template.checklist_items : [""],
      completion_email_subject: template.completion_email_subject,
      completion_email_body: template.completion_email_body,
      survey_email_subject: template.survey_email_subject,
      survey_email_body: template.survey_email_body,
      testimonial_email_subject: template.testimonial_email_subject,
      testimonial_email_body: template.testimonial_email_body,
      survey_delay_days: template.survey_delay_days,
      testimonial_delay_days: template.testimonial_delay_days,
      is_active: template.is_active,
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      alert("Please enter a template name");
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const data = {
        ...formData,
        checklist_items: formData.checklist_items.filter((item) => item.trim() !== ""),
      };

      if (editingTemplate) {
        await offboardingTemplatesApi.update(token, editingTemplate.id, data);
      } else {
        await offboardingTemplatesApi.create(token, data);
      }

      setDialogOpen(false);
      await loadTemplates();
    } catch (err: any) {
      alert(err.message || "Failed to save template");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this template?")) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await offboardingTemplatesApi.delete(token, id);
      await loadTemplates();
    } catch (err: any) {
      alert(err.message || "Failed to delete template");
    }
  };

  const addChecklistItem = () => {
    setFormData({
      ...formData,
      checklist_items: [...formData.checklist_items, ""],
    });
  };

  const updateChecklistItem = (index: number, value: string) => {
    const updated = [...formData.checklist_items];
    updated[index] = value;
    setFormData({ ...formData, checklist_items: updated });
  };

  const removeChecklistItem = (index: number) => {
    const updated = formData.checklist_items.filter((_, i) => i !== index);
    setFormData({ ...formData, checklist_items: updated.length > 0 ? updated : [""] });
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
            <Link href="/offboarding">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold">Offboarding Templates</h1>
              <p className="text-gray-500">Configure default checklists and email templates</p>
            </div>
          </div>
          <Button onClick={openNewDialog}>
            <Plus className="h-4 w-4 mr-2" />
            New Template
          </Button>
        </div>

        {/* Templates List */}
        <div className="grid gap-4">
          {templates.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900">No templates yet</h3>
                <p className="text-gray-500 mt-1">
                  Create a template to streamline your offboarding process
                </p>
                <Button className="mt-4" onClick={openNewDialog}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Template
                </Button>
              </CardContent>
            </Card>
          ) : (
            templates.map((template) => (
              <Card key={template.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-100">
                        {WORKFLOW_TYPE_ICONS[template.workflow_type]}
                      </div>
                      <div>
                        <h3 className="font-medium">{template.name}</h3>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <span>{WORKFLOW_TYPE_LABELS[template.workflow_type]}</span>
                          <span>•</span>
                          <span>{template.checklist_items.length} checklist items</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <Badge className={template.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}>
                        {template.is_active ? "Active" : "Inactive"}
                      </Badge>
                      <Button variant="ghost" size="sm" onClick={() => openEditDialog(template)}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(template.id)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>

      {/* Template Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingTemplate ? "Edit Template" : "New Template"}
            </DialogTitle>
            <DialogDescription>
              Configure the default checklist and email templates for this workflow type
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Template Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Executive Coaching Completion"
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="workflow_type">Workflow Type</Label>
                <Select
                  value={formData.workflow_type}
                  onValueChange={(value) => setFormData({ ...formData, workflow_type: value })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="client">Client Offboarding</SelectItem>
                    <SelectItem value="project">Project Completion</SelectItem>
                    <SelectItem value="contract">Contract End</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Checklist Items */}
            <div>
              <Label>Checklist Items</Label>
              <div className="space-y-2 mt-1">
                {formData.checklist_items.map((item, index) => (
                  <div key={index} className="flex gap-2">
                    <Input
                      value={item}
                      onChange={(e) => updateChecklistItem(index, e.target.value)}
                      placeholder={`Item ${index + 1}`}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeChecklistItem(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                <Button type="button" variant="outline" size="sm" onClick={addChecklistItem}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Item
                </Button>
              </div>
            </div>

            {/* Timing */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="survey_delay">Survey Delay (days)</Label>
                <Input
                  id="survey_delay"
                  type="number"
                  min="0"
                  value={formData.survey_delay_days}
                  onChange={(e) => setFormData({ ...formData, survey_delay_days: parseInt(e.target.value) || 0 })}
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">Days after initiation to send survey</p>
              </div>
              <div>
                <Label htmlFor="testimonial_delay">Testimonial Delay (days)</Label>
                <Input
                  id="testimonial_delay"
                  type="number"
                  min="0"
                  value={formData.testimonial_delay_days}
                  onChange={(e) => setFormData({ ...formData, testimonial_delay_days: parseInt(e.target.value) || 0 })}
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">Days after initiation to request testimonial</p>
              </div>
            </div>

            {/* Active Status */}
            <div className="flex items-center justify-between">
              <div>
                <Label>Active</Label>
                <p className="text-sm text-gray-500">Allow this template to be used for new workflows</p>
              </div>
              <Switch
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
              />
            </div>

            {/* Email Templates (Collapsible) */}
            <div className="border-t pt-4">
              <h4 className="font-medium mb-4">Email Templates</h4>
              <p className="text-sm text-gray-500 mb-4">
                Use {"{{client_name}}"}, {"{{survey_url}}"}, {"{{testimonial_url}}"} as placeholders
              </p>

              <div className="space-y-4">
                <div>
                  <Label>Completion Email Subject</Label>
                  <Input
                    value={formData.completion_email_subject}
                    onChange={(e) => setFormData({ ...formData, completion_email_subject: e.target.value })}
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label>Completion Email Body</Label>
                  <Textarea
                    value={formData.completion_email_body}
                    onChange={(e) => setFormData({ ...formData, completion_email_body: e.target.value })}
                    rows={4}
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label>Survey Email Subject</Label>
                  <Input
                    value={formData.survey_email_subject}
                    onChange={(e) => setFormData({ ...formData, survey_email_subject: e.target.value })}
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label>Survey Email Body</Label>
                  <Textarea
                    value={formData.survey_email_body}
                    onChange={(e) => setFormData({ ...formData, survey_email_body: e.target.value })}
                    rows={4}
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label>Testimonial Email Subject</Label>
                  <Input
                    value={formData.testimonial_email_subject}
                    onChange={(e) => setFormData({ ...formData, testimonial_email_subject: e.target.value })}
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label>Testimonial Email Body</Label>
                  <Textarea
                    value={formData.testimonial_email_body}
                    onChange={(e) => setFormData({ ...formData, testimonial_email_body: e.target.value })}
                    rows={4}
                    className="mt-1"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "Saving..." : "Save Template"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Shell>
  );
}
