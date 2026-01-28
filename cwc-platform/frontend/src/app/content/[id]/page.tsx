"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { contentApi, Content, ContentUpdate, contactsApi, organizationsApi, projectsApi } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import Link from "next/link";
import { ArrowLeft, Save, Trash2, ExternalLink } from "lucide-react";
import { toast } from "sonner";

interface SelectOption {
  id: string;
  name: string;
}

export default function EditContentPage() {
  const router = useRouter();
  const params = useParams();
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [contacts, setContacts] = useState<SelectOption[]>([]);
  const [organizations, setOrganizations] = useState<SelectOption[]>([]);
  const [projects, setProjects] = useState<SelectOption[]>([]);
  const [categories, setCategories] = useState<string[]>([]);

  const [formData, setFormData] = useState<ContentUpdate>({
    title: "",
    description: "",
    content_type: "file",
    file_url: "",
    file_name: "",
    external_url: "",
    category: "",
    release_date: "",
    is_active: true,
    sort_order: 0,
  });

  const [assignTo, setAssignTo] = useState<"all" | "contact" | "organization" | "project">("all");

  useEffect(() => {
    loadContent();
    loadOptions();
  }, [token, params.id]);

  const loadContent = async () => {
    if (!token || !params.id) return;
    try {
      setLoading(true);
      const content = await contentApi.get(token, params.id as string);

      // Format release date for datetime-local input
      let releaseDate = "";
      if (content.release_date) {
        const date = new Date(content.release_date);
        releaseDate = date.toISOString().slice(0, 16);
      }

      setFormData({
        title: content.title,
        description: content.description || "",
        content_type: content.content_type,
        file_url: content.file_url || "",
        file_name: content.file_name || "",
        file_size: content.file_size || undefined,
        mime_type: content.mime_type || "",
        external_url: content.external_url || "",
        contact_id: content.contact_id,
        organization_id: content.organization_id,
        project_id: content.project_id,
        category: content.category || "",
        release_date: releaseDate,
        is_active: content.is_active,
        sort_order: content.sort_order,
      });

      // Determine assignment type
      if (content.contact_id) {
        setAssignTo("contact");
      } else if (content.organization_id) {
        setAssignTo("organization");
      } else if (content.project_id) {
        setAssignTo("project");
      } else {
        setAssignTo("all");
      }
    } catch (error) {
      console.error("Failed to load content:", error);
      toast.error("Failed to load content");
      router.push("/content");
    } finally {
      setLoading(false);
    }
  };

  const loadOptions = async () => {
    if (!token) return;
    try {
      const [contactsRes, orgsRes, projectsRes, categoriesRes] = await Promise.all([
        contactsApi.list(token),
        organizationsApi.list(token),
        projectsApi.list(token),
        contentApi.getCategories(token).catch(() => ({ categories: [] })),
      ]);

      setContacts(
        contactsRes.items.map((c: any) => ({
          id: c.id,
          name: `${c.first_name} ${c.last_name || ""}`.trim(),
        }))
      );
      setOrganizations(
        orgsRes.items.map((o: any) => ({ id: o.id, name: o.name }))
      );
      setProjects(
        projectsRes.map((p: any) => ({ id: p.id, name: p.name }))
      );
      setCategories(categoriesRes.categories);
    } catch (error) {
      console.error("Failed to load options:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !params.id) return;

    if (!formData.title) {
      toast.error("Title is required");
      return;
    }

    try {
      setSaving(true);
      const data: ContentUpdate = {
        ...formData,
        release_date: formData.release_date || null,
      };

      await contentApi.update(token, params.id as string, data);
      toast.success("Content updated successfully");
      router.push("/content");
    } catch (error) {
      console.error("Failed to update content:", error);
      toast.error("Failed to update content");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!token || !params.id) return;
    try {
      await contentApi.delete(token, params.id as string);
      toast.success("Content deleted");
      router.push("/content");
    } catch (error) {
      console.error("Failed to delete content:", error);
      toast.error("Failed to delete content");
    }
  };

  const updateFormData = (key: keyof ContentUpdate, value: any) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleAssignToChange = (value: string) => {
    setAssignTo(value as any);
    // Clear all assignment fields
    setFormData((prev) => ({
      ...prev,
      contact_id: null,
      organization_id: null,
      project_id: null,
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading content...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/content">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Edit Content</h1>
            <p className="text-gray-500">
              Update content details and settings
            </p>
          </div>
        </div>
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="outline" className="text-red-600 hover:text-red-700">
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Content</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete this content? This action cannot
                be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDelete}
                className="bg-red-600 hover:bg-red-700"
              >
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Content Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Title *</Label>
                  <Input
                    id="title"
                    value={formData.title || ""}
                    onChange={(e) => updateFormData("title", e.target.value)}
                    placeholder="e.g., Weekly Worksheet #1"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description || ""}
                    onChange={(e) => updateFormData("description", e.target.value)}
                    placeholder="Brief description of this content..."
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="content_type">Content Type</Label>
                  <Select
                    value={formData.content_type}
                    onValueChange={(value) => updateFormData("content_type", value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="file">File</SelectItem>
                      <SelectItem value="document">Document</SelectItem>
                      <SelectItem value="video">Video</SelectItem>
                      <SelectItem value="link">Link</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {formData.content_type === "link" || formData.content_type === "video" ? (
                  <div className="space-y-2">
                    <Label htmlFor="external_url">URL</Label>
                    <div className="flex gap-2">
                      <Input
                        id="external_url"
                        type="url"
                        value={formData.external_url || ""}
                        onChange={(e) => updateFormData("external_url", e.target.value)}
                        placeholder="https://..."
                        className="flex-1"
                      />
                      {formData.external_url && (
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          onClick={() => window.open(formData.external_url!, "_blank")}
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="file_url">File URL</Label>
                      <div className="flex gap-2">
                        <Input
                          id="file_url"
                          value={formData.file_url || ""}
                          onChange={(e) => updateFormData("file_url", e.target.value)}
                          placeholder="https://storage.example.com/file.pdf"
                          className="flex-1"
                        />
                        {formData.file_url && (
                          <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            onClick={() => window.open(formData.file_url!, "_blank")}
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                      <p className="text-xs text-gray-500">
                        Enter the URL where the file is hosted (e.g., Google Drive, Dropbox, S3)
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="file_name">File Name</Label>
                      <Input
                        id="file_name"
                        value={formData.file_name || ""}
                        onChange={(e) => updateFormData("file_name", e.target.value)}
                        placeholder="worksheet.pdf"
                      />
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="is_active">Active</Label>
                  <Switch
                    id="is_active"
                    checked={formData.is_active}
                    onCheckedChange={(checked) => updateFormData("is_active", checked)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Input
                    id="category"
                    value={formData.category || ""}
                    onChange={(e) => updateFormData("category", e.target.value)}
                    placeholder="e.g., Worksheets, Videos"
                    list="categories"
                  />
                  <datalist id="categories">
                    {categories.map((cat) => (
                      <option key={cat} value={cat} />
                    ))}
                  </datalist>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="release_date">Release Date</Label>
                  <Input
                    id="release_date"
                    type="datetime-local"
                    value={formData.release_date || ""}
                    onChange={(e) => updateFormData("release_date", e.target.value)}
                  />
                  <p className="text-xs text-gray-500">
                    Leave empty for immediate availability
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="sort_order">Sort Order</Label>
                  <Input
                    id="sort_order"
                    type="number"
                    value={formData.sort_order || 0}
                    onChange={(e) => updateFormData("sort_order", parseInt(e.target.value) || 0)}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Access</CardTitle>
                <CardDescription>
                  Who can see this content?
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Assign To</Label>
                  <Select value={assignTo} onValueChange={handleAssignToChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Clients</SelectItem>
                      <SelectItem value="contact">Specific Contact</SelectItem>
                      <SelectItem value="organization">Organization</SelectItem>
                      <SelectItem value="project">Project</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {assignTo === "contact" && (
                  <div className="space-y-2">
                    <Label>Contact</Label>
                    <Select
                      value={formData.contact_id || ""}
                      onValueChange={(value) => updateFormData("contact_id", value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select contact..." />
                      </SelectTrigger>
                      <SelectContent>
                        {contacts.map((c) => (
                          <SelectItem key={c.id} value={c.id}>
                            {c.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {assignTo === "organization" && (
                  <div className="space-y-2">
                    <Label>Organization</Label>
                    <Select
                      value={formData.organization_id || ""}
                      onValueChange={(value) => updateFormData("organization_id", value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select organization..." />
                      </SelectTrigger>
                      <SelectContent>
                        {organizations.map((o) => (
                          <SelectItem key={o.id} value={o.id}>
                            {o.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {assignTo === "project" && (
                  <div className="space-y-2">
                    <Label>Project</Label>
                    <Select
                      value={formData.project_id || ""}
                      onValueChange={(value) => updateFormData("project_id", value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select project..." />
                      </SelectTrigger>
                      <SelectContent>
                        {projects.map((p) => (
                          <SelectItem key={p.id} value={p.id}>
                            {p.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </CardContent>
            </Card>

            <Button type="submit" className="w-full" disabled={saving}>
              <Save className="h-4 w-4 mr-2" />
              {saving ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
