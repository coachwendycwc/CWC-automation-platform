"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import { projectsApi, projectTemplatesApi, contactsApi } from "@/lib/api";
import {
  ArrowLeft,
  FolderKanban,
  FileText,
  CheckCircle,
} from "lucide-react";
import Link from "next/link";

interface Contact {
  id: string;
  first_name: string;
  last_name: string | null;
  email: string | null;
  organization_id: string | null;
}

interface ProjectTemplate {
  id: string;
  name: string;
  description: string | null;
  project_type: string;
  default_duration_days: number;
  task_count: number;
  is_active: boolean;
}

const PROJECT_TYPES = [
  { value: "coaching", label: "Coaching" },
  { value: "workshop", label: "Workshop" },
  { value: "consulting", label: "Consulting" },
  { value: "speaking", label: "Speaking" },
];

export default function NewProjectPage() {
  const router = useRouter();

  const [step, setStep] = useState<"template" | "details">("template");
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [projectType, setProjectType] = useState("coaching");
  const [contactId, setContactId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [targetEndDate, setTargetEndDate] = useState("");
  const [budgetAmount, setBudgetAmount] = useState("");
  const [estimatedHours, setEstimatedHours] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const [templatesData, contactsData] = await Promise.all([
        projectTemplatesApi.list(token, { active_only: true }),
        contactsApi.list(token, { size: 100 }),
      ]);

      setTemplates(templatesData);
      setContacts(contactsData);
    } catch (err) {
      console.error("Failed to load data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTemplate = (templateId: string | null) => {
    setSelectedTemplateId(templateId);

    if (templateId) {
      const template = templates.find((t) => t.id === templateId);
      if (template) {
        setProjectType(template.project_type);
        if (!title) {
          setTitle(template.name);
        }
      }
    }

    setStep("details");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !contactId) return;

    setSubmitting(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const data: any = {
        title,
        description: description || undefined,
        project_type: projectType,
        contact_id: contactId,
        template_id: selectedTemplateId || undefined,
        start_date: startDate || undefined,
        target_end_date: targetEndDate || undefined,
        budget_amount: budgetAmount ? parseFloat(budgetAmount) : undefined,
        estimated_hours: estimatedHours ? parseFloat(estimatedHours) : undefined,
      };

      const project = await projectsApi.create(token, data);
      router.push(`/projects/${project.id}`);
    } catch (err: any) {
      alert(err.message || "Failed to create project");
    } finally {
      setSubmitting(false);
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

  return (
    <Shell>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/projects">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">New Project</h1>
            <p className="text-gray-500">
              {step === "template" ? "Choose a template or start from scratch" : "Enter project details"}
            </p>
          </div>
        </div>

        {/* Step 1: Template Selection */}
        {step === "template" && (
          <div className="space-y-4">
            {/* Start from Scratch */}
            <Card
              className="cursor-pointer hover:border-blue-500 transition-colors"
              onClick={() => handleSelectTemplate(null)}
            >
              <CardContent className="flex items-center gap-4 p-6">
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-gray-100">
                  <FolderKanban className="h-6 w-6 text-gray-600" />
                </div>
                <div>
                  <h3 className="font-medium">Start from Scratch</h3>
                  <p className="text-sm text-gray-500">Create a blank project without any tasks</p>
                </div>
              </CardContent>
            </Card>

            {/* Templates */}
            {templates.length > 0 && (
              <>
                <div className="text-sm font-medium text-gray-500 mt-6 mb-2">Or choose a template</div>
                <div className="grid gap-4">
                  {templates.map((template) => (
                    <Card
                      key={template.id}
                      className="cursor-pointer hover:border-blue-500 transition-colors"
                      onClick={() => handleSelectTemplate(template.id)}
                    >
                      <CardContent className="flex items-center gap-4 p-6">
                        <div className="flex items-center justify-center w-12 h-12 rounded-full bg-blue-100">
                          <FileText className="h-6 w-6 text-blue-600" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-medium">{template.name}</h3>
                          <p className="text-sm text-gray-500">
                            {template.description || `${template.project_type} • ${template.default_duration_days} days`}
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            {template.task_count} tasks included
                          </p>
                        </div>
                        <CheckCircle className="h-5 w-5 text-transparent" />
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Step 2: Project Details */}
        {step === "details" && (
          <Card>
            <CardHeader>
              <CardTitle>Project Details</CardTitle>
              <CardDescription>
                {selectedTemplateId
                  ? "Customize your project based on the selected template"
                  : "Fill in the details for your new project"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Basic Info */}
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="title">Project Title *</Label>
                    <Input
                      id="title"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="Enter project title"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Brief description of the project"
                      rows={3}
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
                      <Label htmlFor="contact">Contact *</Label>
                      <Select value={contactId} onValueChange={setContactId} required>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a contact" />
                        </SelectTrigger>
                        <SelectContent>
                          {contacts.map((contact) => (
                            <SelectItem key={contact.id} value={contact.id}>
                              {contact.first_name} {contact.last_name}
                              {contact.email && ` (${contact.email})`}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>

                {/* Timeline */}
                <div className="space-y-4">
                  <h3 className="font-medium">Timeline</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="startDate">Start Date</Label>
                      <Input
                        id="startDate"
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="targetEndDate">Target End Date</Label>
                      <Input
                        id="targetEndDate"
                        type="date"
                        value={targetEndDate}
                        onChange={(e) => setTargetEndDate(e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                {/* Budget & Hours */}
                <div className="space-y-4">
                  <h3 className="font-medium">Budget & Hours</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="budgetAmount">Budget ($)</Label>
                      <Input
                        id="budgetAmount"
                        type="number"
                        value={budgetAmount}
                        onChange={(e) => setBudgetAmount(e.target.value)}
                        placeholder="0.00"
                        step="0.01"
                        min="0"
                      />
                    </div>
                    <div>
                      <Label htmlFor="estimatedHours">Estimated Hours</Label>
                      <Input
                        id="estimatedHours"
                        type="number"
                        value={estimatedHours}
                        onChange={(e) => setEstimatedHours(e.target.value)}
                        placeholder="0"
                        step="0.5"
                        min="0"
                      />
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-between pt-4 border-t">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setStep("template")}
                  >
                    Back to Templates
                  </Button>
                  <Button type="submit" disabled={submitting || !title || !contactId}>
                    {submitting ? "Creating..." : "Create Project"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}
      </div>
    </Shell>
  );
}
