"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Shell } from "@/components/layout/Shell";
import { testimonialsApi, Testimonial, contactsApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Video,
  Plus,
  MoreHorizontal,
  Eye,
  Trash2,
  Send,
  CheckCircle,
  XCircle,
  Star,
  Clock,
  Play,
} from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";
import Link from "next/link";

interface Contact {
  id: string;
  first_name: string;
  last_name: string | null;
  email: string | null;
}

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

export default function TestimonialsPage() {
  const { token } = useAuth();
  const [testimonials, setTestimonials] = useState<Testimonial[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filterStatus, setFilterStatus] = useState<string>("");

  // Create dialog
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [formData, setFormData] = useState({
    contact_id: "",
    author_name: "",
    author_title: "",
    author_company: "",
  });
  const [saving, setSaving] = useState(false);

  // Delete confirmation
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Video preview
  const [previewVideo, setPreviewVideo] = useState<string | null>(null);

  useEffect(() => {
    loadTestimonials();
    loadContacts();
  }, [token, page, filterStatus]);

  const loadTestimonials = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const result = await testimonialsApi.list(token, {
        page,
        size: 20,
        status: filterStatus || undefined,
      });
      setTestimonials(result.items);
      setTotal(result.total);
    } catch (error) {
      console.error("Failed to load testimonials:", error);
      toast.error("Failed to load testimonials");
    } finally {
      setLoading(false);
    }
  };

  const loadContacts = async () => {
    if (!token) return;
    try {
      const result = await contactsApi.list(token, { contact_type: "client" });
      setContacts(result.items);
    } catch (error) {
      console.error("Failed to load contacts:", error);
    }
  };

  const handleContactSelect = (contactId: string) => {
    const contact = contacts.find((c) => c.id === contactId);
    if (contact) {
      setFormData({
        ...formData,
        contact_id: contactId,
        author_name: `${contact.first_name} ${contact.last_name || ""}`.trim(),
      });
    }
  };

  const handleCreate = async () => {
    if (!token || !formData.contact_id || !formData.author_name.trim()) return;
    try {
      setSaving(true);
      await testimonialsApi.create(token, {
        contact_id: formData.contact_id,
        author_name: formData.author_name.trim(),
        author_title: formData.author_title.trim() || undefined,
        author_company: formData.author_company.trim() || undefined,
      });
      toast.success("Testimonial request created");
      setShowCreateDialog(false);
      setFormData({ contact_id: "", author_name: "", author_title: "", author_company: "" });
      loadTestimonials();
    } catch (error) {
      console.error("Failed to create testimonial:", error);
      toast.error("Failed to create testimonial");
    } finally {
      setSaving(false);
    }
  };

  const handleSendRequest = async (testimonial: Testimonial) => {
    if (!token) return;
    try {
      await testimonialsApi.sendRequest(token, testimonial.id);
      toast.success("Request email sent");
      loadTestimonials();
    } catch (error) {
      console.error("Failed to send request:", error);
      toast.error("Failed to send request");
    }
  };

  const handleUpdateStatus = async (testimonial: Testimonial, status: "approved" | "rejected") => {
    if (!token) return;
    try {
      await testimonialsApi.update(token, testimonial.id, { status });
      toast.success(`Testimonial ${status}`);
      loadTestimonials();
    } catch (error) {
      console.error("Failed to update status:", error);
      toast.error("Failed to update status");
    }
  };

  const handleToggleFeatured = async (testimonial: Testimonial) => {
    if (!token) return;
    try {
      await testimonialsApi.update(token, testimonial.id, { featured: !testimonial.featured });
      toast.success(testimonial.featured ? "Removed from featured" : "Added to featured");
      loadTestimonials();
    } catch (error) {
      console.error("Failed to update:", error);
      toast.error("Failed to update");
    }
  };

  const handleDelete = async (id: string) => {
    if (!token) return;
    try {
      await testimonialsApi.delete(token, id);
      toast.success("Testimonial deleted");
      setDeletingId(null);
      loadTestimonials();
    } catch (error) {
      console.error("Failed to delete testimonial:", error);
      toast.error("Failed to delete testimonial");
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <Shell>
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Video className="h-6 w-6" />
            Testimonials
          </h1>
          <p className="text-gray-500">Video testimonials from clients</p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Request Testimonial
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 items-center">
            <Select
              value={filterStatus}
              onValueChange={(value) => {
                setFilterStatus(value === "all" ? "" : value);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Testimonials List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : testimonials.length === 0 ? (
            <div className="p-8 text-center">
              <Video className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">No testimonials</h3>
              <p className="text-gray-500 mt-1">
                Request testimonials from your clients
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {testimonials.map((testimonial) => (
                <div key={testimonial.id} className="p-4">
                  <div className="flex items-start gap-4">
                    {/* Thumbnail or placeholder */}
                    <div
                      className="w-24 h-16 bg-gray-100 rounded-lg flex-shrink-0 overflow-hidden relative cursor-pointer group"
                      onClick={() => testimonial.video_url && setPreviewVideo(testimonial.video_url)}
                    >
                      {testimonial.thumbnail_url ? (
                        <>
                          <img
                            src={testimonial.thumbnail_url}
                            alt="Thumbnail"
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute inset-0 bg-black/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <Play className="h-6 w-6 text-white" />
                          </div>
                        </>
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Video className="h-6 w-6 text-gray-300" />
                        </div>
                      )}
                      {testimonial.video_duration_seconds && (
                        <span className="absolute bottom-1 right-1 text-xs bg-black/70 text-white px-1 rounded">
                          {formatDuration(testimonial.video_duration_seconds)}
                        </span>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-gray-900">
                          {testimonial.author_name}
                        </span>
                        <Badge className={statusColors[testimonial.status]}>
                          {testimonial.status}
                        </Badge>
                        {testimonial.featured && (
                          <Badge className="bg-amber-100 text-amber-700">
                            <Star className="h-3 w-3 mr-1 fill-current" />
                            Featured
                          </Badge>
                        )}
                        {!testimonial.has_video && testimonial.status === "pending" && (
                          <Badge variant="outline" className="text-gray-500">
                            <Clock className="h-3 w-3 mr-1" />
                            Awaiting submission
                          </Badge>
                        )}
                      </div>
                      {testimonial.author_title && (
                        <p className="text-sm text-gray-600">
                          {testimonial.author_title}
                          {testimonial.author_company && ` at ${testimonial.author_company}`}
                        </p>
                      )}
                      {testimonial.quote && (
                        <p className="text-sm text-gray-500 mt-1 line-clamp-2 italic">
                          "{testimonial.quote}"
                        </p>
                      )}
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-400 flex-wrap">
                        {testimonial.contact_name && (
                          <span>Client: {testimonial.contact_name}</span>
                        )}
                        {testimonial.request_sent_at && (
                          <span>
                            Requested: {format(new Date(testimonial.request_sent_at), "MMM d, yyyy")}
                          </span>
                        )}
                        {testimonial.submitted_at && (
                          <span>
                            Submitted: {format(new Date(testimonial.submitted_at), "MMM d, yyyy")}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex-shrink-0 flex items-center gap-2">
                      {/* Actions based on status */}
                      {testimonial.status === "pending" && testimonial.has_video && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleUpdateStatus(testimonial, "approved")}
                          >
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Approve
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleUpdateStatus(testimonial, "rejected")}
                          >
                            <XCircle className="h-4 w-4 mr-1" />
                            Reject
                          </Button>
                        </>
                      )}
                      {testimonial.status === "pending" && !testimonial.has_video && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSendRequest(testimonial)}
                          disabled={!!testimonial.request_sent_at}
                        >
                          <Send className="h-4 w-4 mr-1" />
                          {testimonial.request_sent_at ? "Sent" : "Send Request"}
                        </Button>
                      )}

                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem asChild>
                            <Link href={`/testimonials/${testimonial.id}`}>
                              <Eye className="h-4 w-4 mr-2" />
                              View Details
                            </Link>
                          </DropdownMenuItem>
                          {testimonial.status === "approved" && (
                            <DropdownMenuItem onClick={() => handleToggleFeatured(testimonial)}>
                              <Star className="h-4 w-4 mr-2" />
                              {testimonial.featured ? "Remove from Featured" : "Add to Featured"}
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => setDeletingId(testimonial.id)}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of {total}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page === totalPages}
              onClick={() => setPage(page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Request Testimonial</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Client</label>
              <Select
                value={formData.contact_id}
                onValueChange={handleContactSelect}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a client..." />
                </SelectTrigger>
                <SelectContent>
                  {contacts.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.first_name} {c.last_name || ""} {c.email ? `(${c.email})` : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Display Name</label>
              <Input
                value={formData.author_name}
                onChange={(e) => setFormData({ ...formData, author_name: e.target.value })}
                placeholder="Name shown on testimonial"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Title (optional)</label>
              <Input
                value={formData.author_title}
                onChange={(e) => setFormData({ ...formData, author_title: e.target.value })}
                placeholder="e.g., CEO, Manager"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Company (optional)</label>
              <Input
                value={formData.author_company}
                onChange={(e) => setFormData({ ...formData, author_company: e.target.value })}
                placeholder="Company name"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleCreate}
                disabled={!formData.contact_id || !formData.author_name.trim() || saving}
              >
                {saving ? "Creating..." : "Create Request"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Video Preview Dialog */}
      <Dialog open={!!previewVideo} onOpenChange={() => setPreviewVideo(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Video Preview</DialogTitle>
          </DialogHeader>
          {previewVideo && (
            <div className="aspect-video">
              <video
                src={previewVideo}
                controls
                autoPlay
                className="w-full h-full rounded-lg"
              />
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deletingId} onOpenChange={() => setDeletingId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Testimonial</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-gray-600">
              Are you sure you want to delete this testimonial? The video will also be removed.
              This cannot be undone.
            </p>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setDeletingId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deletingId && handleDelete(deletingId)}
            >
              Delete
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
    </Shell>
  );
}
