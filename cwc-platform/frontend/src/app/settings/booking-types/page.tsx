"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { bookingTypesApi } from "@/lib/api";
import { BookingType, BookingTypeFormData } from "@/types";
import { Plus, Pencil, Trash2, Copy, ArrowLeft } from "lucide-react";
import Link from "next/link";

const defaultFormData: BookingTypeFormData = {
  name: "",
  slug: "",
  description: "",
  duration_minutes: 60,
  color: "#3B82F6",
  buffer_before: 0,
  buffer_after: 15,
  min_notice_hours: 24,
  max_advance_days: 60,
  requires_confirmation: false,
  is_active: true,
};

export default function BookingTypesPage() {
  const [bookingTypes, setBookingTypes] = useState<BookingType[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<BookingTypeFormData>(defaultFormData);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadBookingTypes();
  }, []);

  const loadBookingTypes = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      const response = await bookingTypesApi.list(token);
      setBookingTypes(response.items);
    } catch (err) {
      console.error("Failed to load booking types:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      if (editingId) {
        await bookingTypesApi.update(token, editingId, formData);
      } else {
        await bookingTypesApi.create(token, formData);
      }

      await loadBookingTypes();
      setShowForm(false);
      setEditingId(null);
      setFormData(defaultFormData);
    } catch (err: any) {
      setError(err.message || "Failed to save booking type");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (bookingType: BookingType) => {
    setFormData({
      name: bookingType.name,
      slug: bookingType.slug,
      description: bookingType.description || "",
      duration_minutes: bookingType.duration_minutes,
      color: bookingType.color,
      price: bookingType.price || undefined,
      buffer_before: bookingType.buffer_before,
      buffer_after: bookingType.buffer_after,
      min_notice_hours: bookingType.min_notice_hours,
      max_advance_days: bookingType.max_advance_days,
      max_per_day: bookingType.max_per_day || undefined,
      requires_confirmation: bookingType.requires_confirmation,
      is_active: bookingType.is_active,
    });
    setEditingId(bookingType.id);
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this booking type?")) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await bookingTypesApi.delete(token, id);
      await loadBookingTypes();
    } catch (err: any) {
      alert(err.message || "Failed to delete booking type");
    }
  };

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  };

  const copyBookingLink = (slug: string) => {
    const link = `${window.location.origin}/book/${slug}`;
    navigator.clipboard.writeText(link);
    alert("Booking link copied to clipboard!");
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
            <Link href="/settings" className="text-gray-500 hover:text-gray-700">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Booking Types</h1>
              <p className="text-gray-600">Manage the types of sessions you offer</p>
            </div>
          </div>
          {!showForm && (
            <Button onClick={() => setShowForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Booking Type
            </Button>
          )}
        </div>

        {/* Form */}
        {showForm && (
          <Card>
            <CardHeader>
              <CardTitle>{editingId ? "Edit Booking Type" : "New Booking Type"}</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">{error}</div>
                )}

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <Input
                      value={formData.name}
                      onChange={(e) => {
                        const name = e.target.value;
                        setFormData({
                          ...formData,
                          name,
                          slug: editingId ? formData.slug : generateSlug(name),
                        });
                      }}
                      placeholder="Coaching Session"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Slug (URL)</label>
                    <Input
                      value={formData.slug}
                      onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                      placeholder="coaching-session"
                      pattern="[a-z0-9-]+"
                      required
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Booking URL: /book/{formData.slug || "your-slug"}
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="A 60-minute coaching session to discuss your goals..."
                    rows={3}
                  />
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Duration (minutes)</label>
                    <Input
                      type="number"
                      value={formData.duration_minutes}
                      onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })}
                      min={15}
                      max={480}
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Price ($)</label>
                    <Input
                      type="number"
                      value={formData.price || ""}
                      onChange={(e) => setFormData({ ...formData, price: e.target.value ? parseFloat(e.target.value) : undefined })}
                      min={0}
                      step="0.01"
                      placeholder="0 = Free"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={formData.color}
                        onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                        className="h-9 w-12 cursor-pointer rounded border border-gray-300"
                      />
                      <Input
                        value={formData.color}
                        onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                        pattern="^#[0-9A-Fa-f]{6}$"
                        className="flex-1"
                      />
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Buffer Before (min)</label>
                    <Input
                      type="number"
                      value={formData.buffer_before}
                      onChange={(e) => setFormData({ ...formData, buffer_before: parseInt(e.target.value) })}
                      min={0}
                      max={120}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Buffer After (min)</label>
                    <Input
                      type="number"
                      value={formData.buffer_after}
                      onChange={(e) => setFormData({ ...formData, buffer_after: parseInt(e.target.value) })}
                      min={0}
                      max={120}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Min Notice (hours)</label>
                    <Input
                      type="number"
                      value={formData.min_notice_hours}
                      onChange={(e) => setFormData({ ...formData, min_notice_hours: parseInt(e.target.value) })}
                      min={0}
                      max={720}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Advance (days)</label>
                    <Input
                      type="number"
                      value={formData.max_advance_days}
                      onChange={(e) => setFormData({ ...formData, max_advance_days: parseInt(e.target.value) })}
                      min={1}
                      max={365}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.requires_confirmation}
                      onChange={(e) => setFormData({ ...formData, requires_confirmation: e.target.checked })}
                      className="rounded border-gray-300"
                    />
                    <span className="text-sm text-gray-700">Requires manual confirmation</span>
                  </label>

                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="rounded border-gray-300"
                    />
                    <span className="text-sm text-gray-700">Active (visible for booking)</span>
                  </label>
                </div>

                <div className="flex gap-3 pt-4">
                  <Button type="submit" disabled={saving}>
                    {saving ? "Saving..." : editingId ? "Update" : "Create"}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowForm(false);
                      setEditingId(null);
                      setFormData(defaultFormData);
                      setError("");
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* List */}
        <div className="space-y-4">
          {bookingTypes.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-gray-500">No booking types yet. Create your first one!</p>
              </CardContent>
            </Card>
          ) : (
            bookingTypes.map((bt) => (
              <Card key={bt.id} className="overflow-hidden">
                <div className="flex items-center">
                  <div
                    className="w-2 self-stretch"
                    style={{ backgroundColor: bt.color }}
                  />
                  <div className="flex-1 p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-gray-900">{bt.name}</h3>
                          {!bt.is_active && (
                            <Badge variant="secondary">Inactive</Badge>
                          )}
                          {bt.requires_confirmation && (
                            <Badge variant="outline">Requires Approval</Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                          {bt.duration_minutes} minutes
                          {bt.price ? ` • $${bt.price}` : " • Free"}
                          {" • "}{bt.buffer_after}min buffer
                        </p>
                        {bt.description && (
                          <p className="text-sm text-gray-600 mt-2">{bt.description}</p>
                        )}
                        <p className="text-xs text-gray-400 mt-2">
                          /book/{bt.slug}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyBookingLink(bt.slug)}
                          title="Copy booking link"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(bt)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(bt.id)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
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
