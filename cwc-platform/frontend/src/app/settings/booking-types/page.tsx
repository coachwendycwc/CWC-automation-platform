"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowLeft, Copy, ExternalLink, Pencil, Plus, Trash2 } from "lucide-react";

import { Shell } from "@/components/layout/Shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { bookingTypesApi } from "@/lib/api";
import type { BookingIntakeQuestion, BookingType, BookingTypeFormData } from "@/types";

const createQuestion = (): BookingIntakeQuestion => ({
  id: `question-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  label: "",
  question_type: "short_text",
  required: false,
  placeholder: "",
  options: [],
});

const defaultFormData: BookingTypeFormData = {
  name: "",
  slug: "",
  description: "",
  duration_minutes: 60,
  color: "#3B82F6",
  price: undefined,
  show_price_on_booking_page: true,
  location_type: "zoom",
  location_details: "",
  post_booking_instructions: "",
  intake_questions: [],
  buffer_before: 0,
  buffer_after: 15,
  min_notice_hours: 24,
  max_advance_days: 60,
  requires_confirmation: false,
  is_active: true,
};

const STARTER_TEMPLATES: Array<{
  key: string;
  title: string;
  description: string;
  data: BookingTypeFormData;
}> = [
  {
    key: "discovery-call",
    title: "Discovery Call",
    description: "Free introductory session to understand fit and next steps.",
    data: {
      name: "Discovery Call",
      slug: "discovery-call",
      description: "A free conversation to explore your goals, current challenges, and whether we are a good fit to work together.",
      duration_minutes: 30,
      color: "#0F766E",
      price: undefined,
      show_price_on_booking_page: true,
      location_type: "zoom",
      location_details: "",
      post_booking_instructions: "Please come ready to share what support you are looking for and what you want to walk away with.",
      intake_questions: [
        {
          id: "discovery-focus",
          label: "What would you most like support with right now?",
          question_type: "long_text",
          required: true,
          placeholder: "Tell me what is bringing you to this call.",
          options: [],
        },
      ],
      buffer_before: 0,
      buffer_after: 15,
      min_notice_hours: 12,
      max_advance_days: 45,
      requires_confirmation: false,
      is_active: true,
    },
  },
  {
    key: "strategy-session",
    title: "Strategy Session",
    description: "Paid working session for focused problem-solving and planning.",
    data: {
      name: "Strategy Session",
      slug: "strategy-session",
      description: "A focused strategy session to work through a specific challenge, map next steps, and leave with a clear plan.",
      duration_minutes: 60,
      color: "#1D4ED8",
      price: 250,
      show_price_on_booking_page: true,
      location_type: "zoom",
      location_details: "",
      post_booking_instructions: "Bring any context, documents, or questions you want us to work through together during the session.",
      intake_questions: [
        {
          id: "strategy-outcome",
          label: "What outcome would make this session successful for you?",
          question_type: "long_text",
          required: true,
          placeholder: "Describe the result you want from this call.",
          options: [],
        },
      ],
      buffer_before: 15,
      buffer_after: 15,
      min_notice_hours: 24,
      max_advance_days: 60,
      requires_confirmation: false,
      is_active: true,
    },
  },
  {
    key: "coaching-session",
    title: "Coaching Session",
    description: "Standard coaching session for active clients.",
    data: {
      name: "Coaching Session",
      slug: "coaching-session",
      description: "A coaching session for ongoing client work, reflection, goal progress, and next-step accountability.",
      duration_minutes: 60,
      color: "#7C3AED",
      price: undefined,
      show_price_on_booking_page: false,
      location_type: "google_meet",
      location_details: "",
      post_booking_instructions: "Please take a few minutes before the session to reflect on wins, challenges, and what you want to focus on today.",
      intake_questions: [
        {
          id: "coaching-focus",
          label: "What would you like to focus on in this session?",
          question_type: "long_text",
          required: true,
          placeholder: "Share the main topic or challenge for today.",
          options: [],
        },
      ],
      buffer_before: 15,
      buffer_after: 15,
      min_notice_hours: 24,
      max_advance_days: 90,
      requires_confirmation: false,
      is_active: true,
    },
  },
];

const getPublicBookingUrl = (slug: string) => `${window.location.origin}/book/${slug}`;
const generateSlug = (name: string) =>
  name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");

const buildFormDataFromBookingType = (
  bookingType: BookingType,
  options?: { duplicate?: boolean }
): BookingTypeFormData => {
  const duplicate = options?.duplicate ?? false;
  const baseName = duplicate ? `${bookingType.name} Copy` : bookingType.name;

  return {
    name: baseName,
    slug: duplicate ? generateSlug(`${bookingType.slug}-copy`) : bookingType.slug,
    description: bookingType.description || "",
    duration_minutes: bookingType.duration_minutes,
    color: bookingType.color,
    price: bookingType.price ?? undefined,
    show_price_on_booking_page: bookingType.show_price_on_booking_page,
    location_type: bookingType.location_type,
    location_details: bookingType.location_details || "",
    post_booking_instructions: bookingType.post_booking_instructions || "",
    intake_questions: (bookingType.intake_questions || []).map((question) => ({
      ...question,
      id: createQuestion().id,
      options: [...question.options],
    })),
    buffer_before: bookingType.buffer_before,
    buffer_after: bookingType.buffer_after,
    min_notice_hours: bookingType.min_notice_hours,
    max_advance_days: bookingType.max_advance_days,
    max_per_day: bookingType.max_per_day ?? undefined,
    requires_confirmation: bookingType.requires_confirmation,
    is_active: bookingType.is_active,
  };
};

export default function BookingTypesPage() {
  const [bookingTypes, setBookingTypes] = useState<BookingType[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<BookingTypeFormData>(defaultFormData);
  const [saving, setSaving] = useState(false);
  const [templateKeyLoading, setTemplateKeyLoading] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void loadBookingTypes();
  }, []);

  const loadBookingTypes = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        return;
      }
      const response = await bookingTypesApi.list(token);
      setBookingTypes(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load booking types");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setShowForm(false);
    setEditingId(null);
    setFormData(defaultFormData);
    setError("");
  };

  const normalizePayload = (data: BookingTypeFormData): BookingTypeFormData => ({
    ...data,
    location_details: data.location_details?.trim() || undefined,
    post_booking_instructions: data.post_booking_instructions?.trim() || undefined,
    description: data.description?.trim() || undefined,
    price: data.price === undefined || Number.isNaN(data.price) ? undefined : data.price,
    intake_questions: (data.intake_questions || [])
      .map((question) => ({
        ...question,
        label: question.label.trim(),
        placeholder: question.placeholder?.trim() || undefined,
        options: question.question_type === "select"
          ? question.options.map((option) => option.trim()).filter(Boolean)
          : [],
      }))
      .filter((question) => question.label.length > 0),
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        return;
      }

      const payload = normalizePayload(formData);

      if (editingId) {
        await bookingTypesApi.update(token, editingId, payload);
      } else {
        await bookingTypesApi.create(token, payload);
      }

      await loadBookingTypes();
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save booking type");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (bookingType: BookingType) => {
    setFormData(buildFormDataFromBookingType(bookingType));
    setEditingId(bookingType.id);
    setShowForm(true);
    setError("");
  };

  const handleDuplicate = (bookingType: BookingType) => {
    setFormData(buildFormDataFromBookingType(bookingType, { duplicate: true }));
    setEditingId(null);
    setShowForm(true);
    setError("");
    toast.success("Booking type duplicated into the form");
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this booking type?")) {
      return;
    }

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        return;
      }
      await bookingTypesApi.delete(token, id);
      await loadBookingTypes();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete booking type");
    }
  };

  const copyBookingLink = async (slug: string) => {
    try {
      const link = getPublicBookingUrl(slug);
      await navigator.clipboard.writeText(link);
      toast.success("Booking link copied");
    } catch {
      toast.error("Failed to copy booking link");
    }
  };

  const handleCreateFromTemplate = async (templateKey: string) => {
    const token = localStorage.getItem("token");
    if (!token) {
      return;
    }

    const template = STARTER_TEMPLATES.find((item) => item.key === templateKey);
    if (!template) {
      toast.error("Starter template not found");
      return;
    }

    setTemplateKeyLoading(templateKey);
    setError("");

    try {
      const existingSlugs = new Set(bookingTypes.map((bookingType) => bookingType.slug));
      let nextSlug = template.data.slug || generateSlug(template.data.name);
      let attempt = 2;

      while (existingSlugs.has(nextSlug)) {
        nextSlug = `${template.data.slug}-${attempt}`;
        attempt += 1;
      }

      const payload = normalizePayload({
        ...template.data,
        slug: nextSlug,
        intake_questions: (template.data.intake_questions || []).map((question) => ({
          ...question,
          id: createQuestion().id,
          options: [...question.options],
        })),
      });

      await bookingTypesApi.create(token, payload);
      await loadBookingTypes();
      toast.success(`${template.title} created`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create booking type from template");
      toast.error("Failed to create starter template");
    } finally {
      setTemplateKeyLoading(null);
    }
  };

  const updateQuestion = (questionId: string, updater: (question: BookingIntakeQuestion) => BookingIntakeQuestion) => {
    setFormData((current) => ({
      ...current,
      intake_questions: (current.intake_questions || []).map((question) =>
        question.id === questionId ? updater(question) : question
      ),
    }));
  };

  const removeQuestion = (questionId: string) => {
    setFormData((current) => ({
      ...current,
      intake_questions: (current.intake_questions || []).filter((question) => question.id !== questionId),
    }));
  };

  if (loading) {
    return (
      <Shell>
        <div className="space-y-6">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-[220px] w-full" />
          <Skeleton className="h-[220px] w-full" />
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/settings" className="text-muted-foreground hover:text-foreground">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Booking Types</h1>
              <p className="text-muted-foreground">Configure session types, booking questions, and meeting setup.</p>
            </div>
          </div>
          {!showForm && (
            <Button onClick={() => setShowForm(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Booking Type
            </Button>
          )}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Starter Templates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              {STARTER_TEMPLATES.map((template) => (
                <div key={template.key} className="rounded-xl border border-border bg-background p-4">
                  <h3 className="font-semibold text-foreground">{template.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{template.description}</p>
                  <Button
                    className="mt-4 w-full"
                    variant="outline"
                    onClick={() => void handleCreateFromTemplate(template.key)}
                    disabled={templateKeyLoading !== null}
                  >
                    {templateKeyLoading === template.key ? "Creating..." : `Use ${template.title}`}
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {showForm && (
          <Card>
            <CardHeader>
              <CardTitle>{editingId ? "Edit Booking Type" : "New Booking Type"}</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {error && (
                  <div className="rounded-md border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
                    {error}
                  </div>
                )}

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Name</label>
                    <Input
                      value={formData.name}
                      onChange={(e) => {
                        const name = e.target.value;
                        setFormData((current) => ({
                          ...current,
                          name,
                          slug: editingId ? current.slug : generateSlug(name),
                        }));
                      }}
                      placeholder="Discovery Call"
                      required
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Slug (URL)</label>
                    <Input
                      value={formData.slug}
                      onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                      placeholder="discovery-call"
                      pattern="[a-z0-9-]+"
                      required
                    />
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                      <span>Booking URL:</span>
                      <span className="rounded-full border border-border bg-muted/40 px-3 py-1 font-mono text-xs">
                        /book/{formData.slug || "your-slug"}
                      </span>
                      {formData.slug && (
                        <>
                          <button
                            type="button"
                            onClick={() => void copyBookingLink(formData.slug)}
                            className="inline-flex items-center gap-1 text-primary hover:underline"
                          >
                            <Copy className="h-3.5 w-3.5" />
                            Copy
                          </button>
                          <a
                            href={getPublicBookingUrl(formData.slug)}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-primary hover:underline"
                          >
                            Preview
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Public Description</label>
                    <textarea
                      className="w-full rounded-md border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Tell people what this session is for and what to expect."
                      rows={4}
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Post-Booking Instructions</label>
                    <textarea
                      className="w-full rounded-md border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      value={formData.post_booking_instructions}
                      onChange={(e) => setFormData({ ...formData, post_booking_instructions: e.target.value })}
                      placeholder="Share prep details, materials to bring, or what happens next."
                      rows={4}
                    />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Duration (minutes)</label>
                    <Input
                      type="number"
                      value={formData.duration_minutes}
                      onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value, 10) || 0 })}
                      min={15}
                      max={480}
                      required
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Price ($)</label>
                    <Input
                      type="number"
                      value={formData.price ?? ""}
                      onChange={(e) => setFormData({ ...formData, price: e.target.value ? parseFloat(e.target.value) : undefined })}
                      min={0}
                      step="0.01"
                      placeholder="Leave blank for free"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Show Price Publicly</label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={formData.show_price_on_booking_page ? "yes" : "no"}
                      onChange={(e) =>
                        setFormData({ ...formData, show_price_on_booking_page: e.target.value === "yes" })
                      }
                    >
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Color</label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={formData.color}
                        onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                        className="h-10 w-12 cursor-pointer rounded border border-border"
                      />
                      <Input
                        value={formData.color}
                        onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                        pattern="^#[0-9A-Fa-f]{6}$"
                      />
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Location Type</label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={formData.location_type}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          location_type: e.target.value as BookingTypeFormData["location_type"],
                        })
                      }
                    >
                      <option value="zoom">Zoom</option>
                      <option value="google_meet">Google Meet</option>
                      <option value="phone">Phone</option>
                      <option value="in_person">In person</option>
                      <option value="custom">Custom link</option>
                    </select>
                  </div>
                  <div className="md:col-span-3">
                    <label className="mb-1 block text-sm font-medium text-foreground">Location Details</label>
                    <Input
                      value={formData.location_details}
                      onChange={(e) => setFormData({ ...formData, location_details: e.target.value })}
                      placeholder="Optional meeting link, phone number, address, or special directions"
                    />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Buffer Before (min)</label>
                    <Input
                      type="number"
                      value={formData.buffer_before}
                      onChange={(e) => setFormData({ ...formData, buffer_before: parseInt(e.target.value, 10) || 0 })}
                      min={0}
                      max={120}
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Buffer After (min)</label>
                    <Input
                      type="number"
                      value={formData.buffer_after}
                      onChange={(e) => setFormData({ ...formData, buffer_after: parseInt(e.target.value, 10) || 0 })}
                      min={0}
                      max={120}
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Min Notice (hours)</label>
                    <Input
                      type="number"
                      value={formData.min_notice_hours}
                      onChange={(e) => setFormData({ ...formData, min_notice_hours: parseInt(e.target.value, 10) || 0 })}
                      min={0}
                      max={720}
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Max Advance (days)</label>
                    <Input
                      type="number"
                      value={formData.max_advance_days}
                      onChange={(e) => setFormData({ ...formData, max_advance_days: parseInt(e.target.value, 10) || 1 })}
                      min={1}
                      max={365}
                    />
                  </div>
                </div>

                <div className="space-y-4 rounded-xl border border-border p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-foreground">Booking Questions</h3>
                      <p className="text-sm text-muted-foreground">Ask for the context you need before the call.</p>
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() =>
                        setFormData((current) => ({
                          ...current,
                          intake_questions: [...(current.intake_questions || []), createQuestion()],
                        }))
                      }
                    >
                      <Plus className="mr-2 h-4 w-4" />
                      Add Question
                    </Button>
                  </div>

                  {(formData.intake_questions || []).length === 0 ? (
                    <div className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                      No custom questions yet. Add the questions you want the person booking to answer.
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {(formData.intake_questions || []).map((question, index) => (
                        <div key={question.id} className="space-y-3 rounded-lg border border-border p-4">
                          <div className="flex items-center justify-between">
                            <div className="text-sm font-medium text-foreground">Question {index + 1}</div>
                            <Button type="button" variant="ghost" size="sm" onClick={() => removeQuestion(question.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                          <div className="grid gap-4 md:grid-cols-2">
                            <div>
                              <label className="mb-1 block text-sm font-medium text-foreground">Label</label>
                              <Input
                                value={question.label}
                                onChange={(e) =>
                                  updateQuestion(question.id, (current) => ({ ...current, label: e.target.value }))
                                }
                                placeholder="What would you like support with?"
                              />
                            </div>
                            <div>
                              <label className="mb-1 block text-sm font-medium text-foreground">Field Type</label>
                              <select
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                value={question.question_type}
                                onChange={(e) =>
                                  updateQuestion(question.id, (current) => ({
                                    ...current,
                                    question_type: e.target.value as BookingIntakeQuestion["question_type"],
                                    options: e.target.value === "select" ? current.options : [],
                                  }))
                                }
                              >
                                <option value="short_text">Short text</option>
                                <option value="long_text">Long text</option>
                                <option value="select">Dropdown</option>
                                <option value="phone">Phone</option>
                              </select>
                            </div>
                          </div>

                          <div className="grid gap-4 md:grid-cols-2">
                            <div>
                              <label className="mb-1 block text-sm font-medium text-foreground">Placeholder</label>
                              <Input
                                value={question.placeholder || ""}
                                onChange={(e) =>
                                  updateQuestion(question.id, (current) => ({ ...current, placeholder: e.target.value }))
                                }
                                placeholder="Optional helper text"
                              />
                            </div>
                            <label className="flex items-center gap-2 pt-7">
                              <input
                                type="checkbox"
                                checked={question.required}
                                onChange={(e) =>
                                  updateQuestion(question.id, (current) => ({ ...current, required: e.target.checked }))
                                }
                                className="rounded border-border"
                              />
                              <span className="text-sm text-foreground">Required</span>
                            </label>
                          </div>

                          {question.question_type === "select" && (
                            <div>
                              <label className="mb-1 block text-sm font-medium text-foreground">Options</label>
                              <Input
                                value={question.options.join(", ")}
                                onChange={(e) =>
                                  updateQuestion(question.id, (current) => ({
                                    ...current,
                                    options: e.target.value.split(",").map((option) => option.trim()).filter(Boolean),
                                  }))
                                }
                                placeholder="Option 1, Option 2, Option 3"
                              />
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-6">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.requires_confirmation}
                      onChange={(e) => setFormData({ ...formData, requires_confirmation: e.target.checked })}
                      className="rounded border-border"
                    />
                    <span className="text-sm text-foreground">Requires manual confirmation</span>
                  </label>

                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="rounded border-border"
                    />
                    <span className="text-sm text-foreground">Active and bookable</span>
                  </label>
                </div>

                <div className="flex gap-3 pt-2">
                  <Button type="submit" disabled={saving}>
                    {saving ? "Saving..." : editingId ? "Update Booking Type" : "Create Booking Type"}
                  </Button>
                  <Button type="button" variant="outline" onClick={resetForm}>
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        <div className="space-y-4">
          {bookingTypes.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">No booking types yet. Create your first one.</p>
              </CardContent>
            </Card>
          ) : (
            bookingTypes.map((bt) => (
              <Card key={bt.id} className="overflow-hidden">
                <div className="flex items-center">
                  <div className="w-2 self-stretch" style={{ backgroundColor: bt.color }} />
                  <div className="flex-1 p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-semibold text-foreground">{bt.name}</h3>
                          {!bt.is_active && <Badge variant="secondary">Inactive</Badge>}
                          {bt.requires_confirmation && <Badge variant="outline">Requires Approval</Badge>}
                          <Badge variant="outline">{bt.location_type.replace("_", " ")}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {bt.duration_minutes} minutes
                          {bt.price !== null ? ` • $${bt.price}` : " • Free"}
                          {!bt.show_price_on_booking_page && " • Price hidden"}
                          {` • ${(bt.intake_questions || []).length} question${(bt.intake_questions || []).length === 1 ? "" : "s"}`}
                        </p>
                        {bt.description && <p className="text-sm text-muted-foreground">{bt.description}</p>}
                        {bt.location_details && (
                          <p className="text-sm text-muted-foreground">Location: {bt.location_details}</p>
                        )}
                        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                          <span className="rounded-full border border-border bg-muted/40 px-3 py-1 font-mono text-xs">
                            /book/{bt.slug}
                          </span>
                          <a
                            href={getPublicBookingUrl(bt.slug)}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-primary hover:underline"
                          >
                            Open public page
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => void copyBookingLink(bt.slug)}
                          title="Copy booking link"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <a href={getPublicBookingUrl(bt.slug)} target="_blank" rel="noreferrer">
                          <Button variant="ghost" size="sm" title="Open public booking page">
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        </a>
                        <Button variant="ghost" size="sm" onClick={() => handleDuplicate(bt)} title="Duplicate booking type">
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleEdit(bt)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => void handleDelete(bt.id)}
                          className="text-destructive hover:bg-destructive/10 hover:text-destructive/80"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </Shell>
  );
}
