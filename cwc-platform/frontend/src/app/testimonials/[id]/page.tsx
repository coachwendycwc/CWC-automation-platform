"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { testimonialsApi, Testimonial } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  Video,
  User,
  Building2,
  Mail,
  Clock,
  CheckCircle,
  XCircle,
  Star,
  Copy,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";
import Link from "next/link";

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

export default function TestimonialDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuth();
  const [testimonial, setTestimonial] = useState<Testimonial | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({
    author_name: "",
    author_title: "",
    author_company: "",
    quote: "",
    transcript: "",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadTestimonial();
  }, [token, params.id]);

  const loadTestimonial = async () => {
    if (!token || !params.id) return;
    try {
      setLoading(true);
      const data = await testimonialsApi.get(token, params.id as string);
      setTestimonial(data);
      setEditData({
        author_name: data.author_name,
        author_title: data.author_title || "",
        author_company: data.author_company || "",
        quote: data.quote || "",
        transcript: data.transcript || "",
      });
    } catch (error) {
      console.error("Failed to load testimonial:", error);
      toast.error("Failed to load testimonial");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!token || !testimonial) return;
    try {
      setSaving(true);
      await testimonialsApi.update(token, testimonial.id, {
        author_name: editData.author_name.trim(),
        author_title: editData.author_title.trim() || undefined,
        author_company: editData.author_company.trim() || undefined,
        quote: editData.quote.trim() || undefined,
        transcript: editData.transcript.trim() || undefined,
      });
      toast.success("Testimonial updated");
      setEditing(false);
      loadTestimonial();
    } catch (error) {
      console.error("Failed to update:", error);
      toast.error("Failed to update testimonial");
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateStatus = async (status: "approved" | "rejected") => {
    if (!token || !testimonial) return;
    try {
      await testimonialsApi.update(token, testimonial.id, { status });
      toast.success(`Testimonial ${status}`);
      loadTestimonial();
    } catch (error) {
      console.error("Failed to update status:", error);
      toast.error("Failed to update status");
    }
  };

  const handleToggleFeatured = async () => {
    if (!token || !testimonial) return;
    try {
      await testimonialsApi.update(token, testimonial.id, { featured: !testimonial.featured });
      toast.success(testimonial.featured ? "Removed from featured" : "Added to featured");
      loadTestimonial();
    } catch (error) {
      console.error("Failed to update:", error);
      toast.error("Failed to update");
    }
  };

  const handleSendRequest = async () => {
    if (!token || !testimonial) return;
    try {
      await testimonialsApi.sendRequest(token, testimonial.id);
      toast.success("Request email sent");
      loadTestimonial();
    } catch (error) {
      console.error("Failed to send request:", error);
      toast.error("Failed to send request");
    }
  };

  const copyRecordingLink = () => {
    if (!testimonial) return;
    const url = `${window.location.origin}/record/${testimonial.request_token}`;
    navigator.clipboard.writeText(url);
    toast.success("Link copied to clipboard");
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "N/A";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!testimonial) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium">Testimonial not found</h3>
        <Link href="/testimonials" className="text-blue-600 hover:underline mt-2 inline-block">
          Back to testimonials
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{testimonial.author_name}</h1>
            <Badge className={statusColors[testimonial.status]}>
              {testimonial.status}
            </Badge>
            {testimonial.featured && (
              <Badge className="bg-amber-100 text-amber-700">
                <Star className="h-3 w-3 mr-1 fill-current" />
                Featured
              </Badge>
            )}
          </div>
          {testimonial.author_title && (
            <p className="text-gray-500">
              {testimonial.author_title}
              {testimonial.author_company && ` at ${testimonial.author_company}`}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          {testimonial.status === "pending" && testimonial.has_video && (
            <>
              <Button onClick={() => handleUpdateStatus("approved")}>
                <CheckCircle className="h-4 w-4 mr-2" />
                Approve
              </Button>
              <Button variant="outline" onClick={() => handleUpdateStatus("rejected")}>
                <XCircle className="h-4 w-4 mr-2" />
                Reject
              </Button>
            </>
          )}
          {testimonial.status === "approved" && (
            <Button variant="outline" onClick={handleToggleFeatured}>
              <Star className={`h-4 w-4 mr-2 ${testimonial.featured ? "fill-amber-500 text-amber-500" : ""}`} />
              {testimonial.featured ? "Remove Featured" : "Feature"}
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Video Section */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Video className="h-5 w-5" />
                Video
              </CardTitle>
            </CardHeader>
            <CardContent>
              {testimonial.video_url ? (
                <div className="space-y-4">
                  <div className="aspect-video rounded-lg overflow-hidden bg-black">
                    <video
                      src={testimonial.video_url}
                      controls
                      className="w-full h-full"
                      poster={testimonial.thumbnail_url || undefined}
                    />
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>Duration: {formatDuration(testimonial.video_duration_seconds)}</span>
                    {testimonial.submitted_at && (
                      <span>
                        Submitted: {format(new Date(testimonial.submitted_at), "MMM d, yyyy 'at' h:mm a")}
                      </span>
                    )}
                  </div>
                </div>
              ) : (
                <div className="aspect-video rounded-lg bg-gray-100 flex flex-col items-center justify-center">
                  <Video className="h-12 w-12 text-gray-300 mb-3" />
                  <p className="text-gray-500">No video submitted yet</p>
                  <div className="mt-4 flex gap-2">
                    <Button onClick={handleSendRequest} disabled={!!testimonial.request_sent_at}>
                      <Mail className="h-4 w-4 mr-2" />
                      {testimonial.request_sent_at ? "Request Sent" : "Send Request Email"}
                    </Button>
                    <Button variant="outline" onClick={copyRecordingLink}>
                      <Copy className="h-4 w-4 mr-2" />
                      Copy Recording Link
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quote & Transcript */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Content</CardTitle>
              {!editing && (
                <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                  Edit
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {editing ? (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Pull Quote</label>
                    <Textarea
                      value={editData.quote}
                      onChange={(e) => setEditData({ ...editData, quote: e.target.value })}
                      placeholder="A brief, impactful quote to display..."
                      rows={3}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Transcript</label>
                    <Textarea
                      value={editData.transcript}
                      onChange={(e) => setEditData({ ...editData, transcript: e.target.value })}
                      placeholder="Full video transcript..."
                      rows={6}
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setEditing(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={saving}>
                      {saving ? "Saving..." : "Save"}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Pull Quote</label>
                    {testimonial.quote ? (
                      <p className="mt-1 text-lg italic">"{testimonial.quote}"</p>
                    ) : (
                      <p className="mt-1 text-gray-400 italic">No quote added</p>
                    )}
                  </div>
                  {testimonial.transcript && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Transcript</label>
                      <p className="mt-1 whitespace-pre-wrap text-gray-700">{testimonial.transcript}</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Author Details */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Author</CardTitle>
              {!editing && (
                <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                  Edit
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {editing ? (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Name</label>
                    <Input
                      value={editData.author_name}
                      onChange={(e) => setEditData({ ...editData, author_name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Title</label>
                    <Input
                      value={editData.author_title}
                      onChange={(e) => setEditData({ ...editData, author_title: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Company</label>
                    <Input
                      value={editData.author_company}
                      onChange={(e) => setEditData({ ...editData, author_company: e.target.value })}
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <User className="h-4 w-4 text-gray-400" />
                    <span>{testimonial.author_name}</span>
                  </div>
                  {testimonial.author_title && (
                    <div className="flex items-center gap-3">
                      <span className="h-4 w-4" />
                      <span className="text-gray-500">{testimonial.author_title}</span>
                    </div>
                  )}
                  {testimonial.author_company && (
                    <div className="flex items-center gap-3">
                      <Building2 className="h-4 w-4 text-gray-400" />
                      <span>{testimonial.author_company}</span>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Request Details */}
          <Card>
            <CardHeader>
              <CardTitle>Request Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {testimonial.contact_name && (
                <div className="flex items-center gap-3">
                  <User className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Contact</p>
                    <p>{testimonial.contact_name}</p>
                  </div>
                </div>
              )}
              {testimonial.organization_name && (
                <div className="flex items-center gap-3">
                  <Building2 className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Organization</p>
                    <p>{testimonial.organization_name}</p>
                  </div>
                </div>
              )}
              <div className="flex items-center gap-3">
                <Clock className="h-4 w-4 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-500">Created</p>
                  <p>{format(new Date(testimonial.created_at), "MMM d, yyyy")}</p>
                </div>
              </div>
              {testimonial.request_sent_at && (
                <div className="flex items-center gap-3">
                  <Mail className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Request Sent</p>
                    <p>{format(new Date(testimonial.request_sent_at), "MMM d, yyyy")}</p>
                  </div>
                </div>
              )}
              {testimonial.reviewed_at && (
                <div className="flex items-center gap-3">
                  <CheckCircle className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Reviewed</p>
                    <p>{format(new Date(testimonial.reviewed_at), "MMM d, yyyy")}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recording Link */}
          <Card>
            <CardHeader>
              <CardTitle>Recording Link</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 mb-3">
                Share this link with the client to record their testimonial.
              </p>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={copyRecordingLink}>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy Link
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => window.open(`/record/${testimonial.request_token}`, "_blank")}
                >
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
