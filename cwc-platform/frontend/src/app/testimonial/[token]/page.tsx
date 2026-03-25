"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { publicFeedbackApi } from "@/lib/api";
import { CheckCircle, Quote, AlertCircle, Heart, Camera, X } from "lucide-react";

interface TestimonialData {
  contact_name: string;
  workflow_type: string;
  already_submitted: boolean;
}

export default function TestimonialPage() {
  const params = useParams();
  const token = params.token as string;

  const [testimonialData, setTestimonialData] = useState<TestimonialData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  // Form state
  const [testimonialText, setTestimonialText] = useState("");
  const [authorName, setAuthorName] = useState("");
  const [authorTitle, setAuthorTitle] = useState("");
  const [photo, setPhoto] = useState<string | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [permissionGranted, setPermissionGranted] = useState(false);

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Check file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert("Photo must be less than 5MB");
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result as string;
        setPhoto(base64);
        setPhotoPreview(base64);
      };
      reader.readAsDataURL(file);
    }
  };

  const removePhoto = () => {
    setPhoto(null);
    setPhotoPreview(null);
  };

  useEffect(() => {
    if (token) {
      loadTestimonial();
    }
  }, [token]);

  const loadTestimonial = async () => {
    try {
      const data = await publicFeedbackApi.getTestimonialRequest(token);
      setTestimonialData(data);
      if (data.already_submitted) {
        setSubmitted(true);
      }
      // Pre-fill author name
      setAuthorName(data.contact_name || "");
    } catch (err: any) {
      setError(err.message || "Testimonial request not found or has expired");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!testimonialText.trim()) {
      alert("Please enter your testimonial");
      return;
    }

    if (!authorName.trim()) {
      alert("Please enter your name");
      return;
    }

    setSubmitting(true);
    try {
      await publicFeedbackApi.submitTestimonial(token, {
        testimonial_text: testimonialText,
        author_name: authorName,
        author_title: authorTitle || null,
        photo: photo || null,
        permission_granted: permissionGranted,
      });
      setSubmitted(true);
    } catch (err: any) {
      alert(err.message || "Failed to submit testimonial");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center">
        <div className="max-w-2xl w-full mx-auto px-4 space-y-6">
          <div className="text-center space-y-3">
            <Skeleton className="h-16 w-32 mx-auto" />
            <Skeleton className="h-8 w-48 mx-auto" />
            <Skeleton className="h-4 w-80 mx-auto" />
          </div>
          <Skeleton className="h-96 rounded-lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Request Not Available</h2>
            <p className="text-muted-foreground">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <Heart className="h-12 w-12 text-pink-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Thank You!</h2>
            <p className="text-muted-foreground">
              Your testimonial has been submitted. We truly appreciate you sharing your story with us.
              It means the world to us!
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <Image
            src="/images/logo.png"
            alt="Coaching Women of Color"
            width={120}
            height={102}
            className="mx-auto mb-4"
          />
          <h1 className="text-2xl font-bold mb-2">Share Your Story</h1>
          <p className="text-muted-foreground">
            Dear {testimonialData?.contact_name}, we hope our work together has made a positive impact.
            We'd be honored if you'd share your experience with others.
          </p>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <Quote className="h-8 w-8 text-success" />
              <div>
                <CardTitle>Your Testimonial</CardTitle>
                <CardDescription>
                  Your words help others discover the value of our services
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Testimonial Text */}
            <div>
              <Label htmlFor="testimonial" className="text-base font-medium">
                Your Experience *
              </Label>
              <p className="text-sm text-muted-foreground mb-2">
                What transformation or results did you experience? What would you tell someone considering working with us?
              </p>
              <Textarea
                id="testimonial"
                value={testimonialText}
                onChange={(e) => setTestimonialText(e.target.value)}
                placeholder="Share your story here..."
                rows={6}
                className="mt-2"
              />
            </div>

            {/* Author Name */}
            <div>
              <Label htmlFor="authorName" className="text-base font-medium">
                Your Name *
              </Label>
              <Input
                id="authorName"
                value={authorName}
                onChange={(e) => setAuthorName(e.target.value)}
                placeholder="How would you like to be credited?"
                className="mt-2"
              />
            </div>

            {/* Author Title */}
            <div>
              <Label htmlFor="authorTitle" className="text-base font-medium">
                Title / Company (Optional)
              </Label>
              <Input
                id="authorTitle"
                value={authorTitle}
                onChange={(e) => setAuthorTitle(e.target.value)}
                placeholder="e.g., CEO, ABC Company"
                className="mt-2"
              />
            </div>

            {/* Photo Upload */}
            <div>
              <Label className="text-base font-medium">
                Your Photo (Optional)
              </Label>
              <p className="text-sm text-muted-foreground mb-2">
                Add a headshot to personalize your testimonial
              </p>

              {photoPreview ? (
                <div className="relative inline-block">
                  <img
                    src={photoPreview}
                    alt="Preview"
                    className="w-24 h-24 rounded-full object-cover border-2 border-border"
                  />
                  <button
                    type="button"
                    onClick={removePhoto}
                    className="absolute -top-2 -right-2 bg-destructive text-white rounded-full p-1 hover:bg-destructive/90 cursor-pointer"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <label className="flex items-center gap-3 cursor-pointer border-2 border-dashed border-border rounded-lg p-4 hover:border-muted-foreground transition-colors">
                  <div className="bg-muted rounded-full p-3">
                    <Camera className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <div>
                    <span className="text-sm font-medium text-foreground">Upload a photo</span>
                    <p className="text-sm text-muted-foreground">JPG, PNG up to 5MB</p>
                  </div>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handlePhotoChange}
                    className="hidden"
                  />
                </label>
              )}
            </div>

            {/* Permission */}
            <div className="bg-muted p-4 rounded-lg">
              <div className="flex items-start gap-3">
                <Checkbox
                  id="permission"
                  checked={permissionGranted}
                  onCheckedChange={(checked) => setPermissionGranted(checked === true)}
                  className="mt-1"
                />
                <div>
                  <Label htmlFor="permission" className="text-base font-medium cursor-pointer">
                    Permission to Share
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    I grant Coaching Women of Color permission to use my testimonial on their website,
                    social media, and marketing materials.
                  </p>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <Button
              className="w-full cursor-pointer"
              size="lg"
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? "Submitting..." : "Submit Testimonial"}
            </Button>

            <p className="text-center text-sm text-muted-foreground">
              Thank you for taking the time to share your experience. Your words inspire us to continue our mission.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
