"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { publicTestimonialsApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import VideoRecorder from "@/components/VideoRecorder";
import {
  Video,
  CheckCircle,
  AlertCircle,
  User,
  Building2,
  Briefcase,
  Quote,
} from "lucide-react";
import { toast } from "sonner";

interface RequestInfo {
  id: string;
  author_name: string;
  author_title: string | null;
  author_company: string | null;
  status: string;
  already_submitted: boolean;
}

type PageState = "loading" | "ready" | "submitted" | "error" | "not_found";

export default function RecordTestimonialPage() {
  const params = useParams();
  const token = params.token as string;

  const [pageState, setPageState] = useState<PageState>("loading");
  const [requestInfo, setRequestInfo] = useState<RequestInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form data
  const [formData, setFormData] = useState({
    author_name: "",
    author_title: "",
    author_company: "",
    quote: "",
  });
  const [videoData, setVideoData] = useState<{
    video_url: string;
    video_public_id: string;
    video_duration_seconds: number;
    thumbnail_url: string | null;
  } | null>(null);
  const [permissionGranted, setPermissionGranted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadRequest();
  }, [token]);

  const loadRequest = async () => {
    try {
      const data = await publicTestimonialsApi.getRequest(token);
      setRequestInfo(data);

      if (data.already_submitted) {
        setPageState("submitted");
      } else {
        setFormData({
          author_name: data.author_name,
          author_title: data.author_title || "",
          author_company: data.author_company || "",
          quote: "",
        });
        setPageState("ready");
      }
    } catch (err: any) {
      console.error("Failed to load request:", err);
      if (err.status === 404) {
        setPageState("not_found");
      } else {
        setError("Failed to load testimonial request");
        setPageState("error");
      }
    }
  };

  const handleVideoComplete = (data: {
    video_url: string;
    video_public_id: string;
    video_duration_seconds: number;
    thumbnail_url: string | null;
  }) => {
    setVideoData(data);
    toast.success("Video uploaded successfully!");
  };

  const handleSubmit = async () => {
    if (!videoData || !permissionGranted) return;

    try {
      setSubmitting(true);
      await publicTestimonialsApi.submit(token, {
        author_name: formData.author_name.trim(),
        author_title: formData.author_title.trim() || undefined,
        author_company: formData.author_company.trim() || undefined,
        quote: formData.quote.trim() || undefined,
        video_url: videoData.video_url,
        video_public_id: videoData.video_public_id,
        video_duration_seconds: videoData.video_duration_seconds,
        thumbnail_url: videoData.thumbnail_url || undefined,
        permission_granted: true,
      });
      setPageState("submitted");
    } catch (err) {
      console.error("Failed to submit:", err);
      toast.error("Failed to submit testimonial. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  // Loading state
  if (pageState === "loading") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  // Not found
  if (pageState === "not_found") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-8 text-center">
            <AlertCircle className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Testimonial Request Not Found
            </h2>
            <p className="text-gray-500">
              This link may be invalid or expired. Please contact us if you believe this is an error.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (pageState === "error") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-8 text-center">
            <AlertCircle className="h-16 w-16 text-red-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Something went wrong
            </h2>
            <p className="text-gray-500 mb-4">{error}</p>
            <Button onClick={loadRequest}>Try Again</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Already submitted
  if (pageState === "submitted") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-8 text-center">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Thank You!
            </h2>
            <p className="text-gray-500">
              Your testimonial has been submitted successfully. We really appreciate you taking the time to share your experience!
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Ready to record
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-violet-100 rounded-full mb-4">
            <Video className="h-8 w-8 text-violet-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Share Your Story</h1>
          <p className="text-gray-500 mt-2">
            Record a short video testimonial about your experience
          </p>
        </div>

        {/* Video Recorder */}
        <Card>
          <CardHeader>
            <CardTitle>1. Record Your Video</CardTitle>
          </CardHeader>
          <CardContent>
            <VideoRecorder
              maxDuration={120}
              onUpload={publicTestimonialsApi.uploadVideo}
              onComplete={handleVideoComplete}
            />
            {videoData && (
              <div className="mt-4 p-3 bg-green-50 rounded-lg flex items-center gap-2 text-green-700">
                <CheckCircle className="h-5 w-5" />
                Video ready!
              </div>
            )}
          </CardContent>
        </Card>

        {/* Form */}
        <Card>
          <CardHeader>
            <CardTitle>2. Your Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <User className="h-4 w-4 text-gray-400" />
                Your Name
              </label>
              <Input
                value={formData.author_name}
                onChange={(e) => setFormData({ ...formData, author_name: e.target.value })}
                placeholder="How should we display your name?"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-gray-400" />
                  Title (optional)
                </label>
                <Input
                  value={formData.author_title}
                  onChange={(e) => setFormData({ ...formData, author_title: e.target.value })}
                  placeholder="e.g., CEO, Manager"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-gray-400" />
                  Company (optional)
                </label>
                <Input
                  value={formData.author_company}
                  onChange={(e) => setFormData({ ...formData, author_company: e.target.value })}
                  placeholder="Your company"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <Quote className="h-4 w-4 text-gray-400" />
                Key Quote (optional)
              </label>
              <Textarea
                value={formData.quote}
                onChange={(e) => setFormData({ ...formData, quote: e.target.value })}
                placeholder="A brief summary of your testimonial that we can use as a pull quote..."
                rows={3}
              />
              <p className="text-xs text-gray-400">
                This will be displayed alongside your video
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Permission */}
        <Card>
          <CardHeader>
            <CardTitle>3. Permission</CardTitle>
          </CardHeader>
          <CardContent>
            <label className="flex items-start gap-3 cursor-pointer">
              <Checkbox
                checked={permissionGranted}
                onCheckedChange={(checked) => setPermissionGranted(checked === true)}
                className="mt-0.5"
              />
              <span className="text-sm text-gray-600">
                I grant permission to use my video testimonial on the website, social media, and marketing materials. I understand my testimonial may be edited for length or clarity.
              </span>
            </label>
          </CardContent>
        </Card>

        {/* Submit */}
        <div className="flex justify-center">
          <Button
            size="lg"
            onClick={handleSubmit}
            disabled={!videoData || !permissionGranted || !formData.author_name.trim() || submitting}
          >
            {submitting ? "Submitting..." : "Submit Testimonial"}
          </Button>
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-gray-400">
          Your testimonial will be reviewed before being published.
          <br />
          Thank you for sharing your experience!
        </p>
      </div>
    </div>
  );
}
