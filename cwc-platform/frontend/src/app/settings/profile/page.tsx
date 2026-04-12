"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { toast } from "sonner";
import { ArrowLeft, Paintbrush, Upload, User } from "lucide-react";

import { Shell } from "@/components/layout/Shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { usersApi } from "@/lib/api";
import type { User as UserType } from "@/types";

export default function ProfileSettingsPage() {
  const avatarInputRef = useRef<HTMLInputElement | null>(null);
  const logoInputRef = useRef<HTMLInputElement | null>(null);
  const bannerInputRef = useRef<HTMLInputElement | null>(null);
  const [profile, setProfile] = useState<UserType | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingTarget, setUploadingTarget] = useState<"avatar" | "booking_logo" | "booking_banner" | null>(null);
  const [suggestedColors, setSuggestedColors] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [formData, setFormData] = useState({
    name: "",
    avatar_url: "",
    booking_page_title: "",
    booking_page_description: "",
    booking_page_brand_color: "#2A7B8C",
    booking_page_logo_url: "",
    booking_page_banner_url: "",
  });

  useEffect(() => {
    void loadProfile();
  }, []);

  const loadProfile = async () => {
    setLoading(true);
    setError("");

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        setError("You must be signed in to manage your profile.");
        return;
      }

      const data = await usersApi.getMe(token);
      setProfile(data);
      setSuggestedColors([]);
      setFormData({
        name: data.name || "",
        avatar_url: data.avatar_url || "",
        booking_page_title: data.booking_page_title || "",
        booking_page_description: data.booking_page_description || "",
        booking_page_brand_color: data.booking_page_brand_color || "#2A7B8C",
        booking_page_logo_url: data.booking_page_logo_url || "",
        booking_page_banner_url: data.booking_page_banner_url || "",
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load profile");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const data = await usersApi.updateMe(token, {
        name: formData.name.trim() || null,
        avatar_url: formData.avatar_url.trim() || null,
        booking_page_title: formData.booking_page_title.trim() || null,
        booking_page_description: formData.booking_page_description.trim() || null,
        booking_page_brand_color: formData.booking_page_brand_color,
        booking_page_logo_url: formData.booking_page_logo_url.trim() || null,
        booking_page_banner_url: formData.booking_page_banner_url.trim() || null,
      });

      setProfile(data);
      setSuggestedColors([]);
      setMessage("Profile and booking page branding updated.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  const handleImageUpload = async (target: "avatar" | "booking_logo" | "booking_banner", file: File | null) => {
    if (!file) return;

    const token = localStorage.getItem("token");
    if (!token) {
      setError("You must be signed in to upload images.");
      return;
    }

    setUploadingTarget(target);
    setError("");
    setMessage("");

    try {
      const response = await usersApi.uploadImage(token, target, file);
      const data = response.user;
      setProfile(data);
      setFormData({
        name: data.name || "",
        avatar_url: data.avatar_url || "",
        booking_page_title: data.booking_page_title || "",
        booking_page_description: data.booking_page_description || "",
        booking_page_brand_color: data.booking_page_brand_color || "#2A7B8C",
        booking_page_logo_url: data.booking_page_logo_url || "",
        booking_page_banner_url: data.booking_page_banner_url || "",
      });
      setSuggestedColors(target === "booking_logo" ? response.suggested_colors || [] : []);
      toast.success(
        target === "avatar"
          ? "Profile photo uploaded"
          : target === "booking_logo"
          ? "Booking logo uploaded"
          : "Banner image uploaded"
      );
      if (target === "booking_logo" && response.suggested_colors?.length) {
        setMessage("Logo uploaded. Choose the brand color you want to use from the suggested palette below.");
      }
    } catch (err: unknown) {
      const messageText = err instanceof Error ? err.message : "Upload failed";
      setError(messageText);
      toast.error(messageText);
    } finally {
      setUploadingTarget(null);
      if (target === "avatar" && avatarInputRef.current) {
        avatarInputRef.current.value = "";
      }
      if (target === "booking_logo" && logoInputRef.current) {
        logoInputRef.current.value = "";
      }
      if (target === "booking_banner" && bannerInputRef.current) {
        bannerInputRef.current.value = "";
      }
    }
  };

  return (
    <Shell>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/settings" className="text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Profile & Booking Branding</h1>
            <p className="text-muted-foreground">
              Control how your public booking page looks and feels.
            </p>
          </div>
        </div>

        {error && (
          <div className="rounded-md border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {message && (
          <div className="rounded-md border border-primary/20 bg-primary/10 px-4 py-3 text-sm text-primary">
            {message}
          </div>
        )}

        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-48 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Profile
                </CardTitle>
                <CardDescription>Basic public-facing information for your booking page.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-foreground">Display Name</label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Wendy Amara"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-foreground">Avatar URL</label>
                  <Input
                    value={formData.avatar_url}
                    onChange={(e) => setFormData({ ...formData, avatar_url: e.target.value })}
                    placeholder="https://..."
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="mb-2 block text-sm font-medium text-foreground">Profile Photo</label>
                  <div className="flex flex-col gap-3 rounded-xl border border-border p-4 md:flex-row md:items-center md:justify-between">
                    <div className="flex items-center gap-3">
                      <div className="relative h-16 w-16 overflow-hidden rounded-full border border-border bg-muted">
                        {formData.avatar_url ? (
                          <Image
                            src={formData.avatar_url}
                            alt="Profile preview"
                            fill
                            className="object-cover"
                            unoptimized
                          />
                        ) : (
                          <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                            No photo
                          </div>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Upload a headshot or profile image for your booking page.
                      </p>
                    </div>
                    <div>
                      <input
                        ref={avatarInputRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => void handleImageUpload("avatar", e.target.files?.[0] ?? null)}
                      />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => avatarInputRef.current?.click()}
                        disabled={uploadingTarget === "avatar"}
                      >
                        <Upload className="mr-2 h-4 w-4" />
                        {uploadingTarget === "avatar" ? "Uploading..." : "Upload Photo"}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Paintbrush className="h-5 w-5" />
                  Booking Page Branding
                </CardTitle>
                <CardDescription>
                  Customize the headline, support text, logo, and accent color on your public booking page.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">Custom Booking Title</label>
                    <Input
                      value={formData.booking_page_title}
                      onChange={(e) => setFormData({ ...formData, booking_page_title: e.target.value })}
                      placeholder="Book time with Coaching Women of Color"
                    />
                  </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-foreground">Brand Color</label>
                  <div className="flex gap-2">
                      <input
                        type="color"
                        value={formData.booking_page_brand_color}
                        onChange={(e) => setFormData({ ...formData, booking_page_brand_color: e.target.value })}
                        className="h-10 w-14 cursor-pointer rounded border border-border"
                      />
                      <Input
                        value={formData.booking_page_brand_color}
                        onChange={(e) => setFormData({ ...formData, booking_page_brand_color: e.target.value })}
                        pattern="^#[0-9A-Fa-f]{6}$"
                      />
                    </div>
                    {suggestedColors.length > 0 && (
                      <div className="mt-3">
                        <div className="mb-2 text-sm font-medium text-foreground">Suggested Logo Colors</div>
                        <div className="flex flex-wrap gap-2">
                          {suggestedColors.map((color) => (
                            <button
                              key={color}
                              type="button"
                              onClick={() => setFormData({ ...formData, booking_page_brand_color: color })}
                              className={`h-10 w-10 rounded-full border-2 transition-transform hover:scale-105 ${
                                formData.booking_page_brand_color === color ? "border-foreground" : "border-border"
                              }`}
                              style={{ backgroundColor: color }}
                              aria-label={`Choose ${color} as brand color`}
                              title={color}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-foreground">Custom Booking Description</label>
                  <Textarea
                    value={formData.booking_page_description}
                    onChange={(e) => setFormData({ ...formData, booking_page_description: e.target.value })}
                    placeholder="Add the message guests should see before they choose a date and time."
                    rows={4}
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-foreground">Booking Logo URL</label>
                  <Input
                    value={formData.booking_page_logo_url}
                    onChange={(e) => setFormData({ ...formData, booking_page_logo_url: e.target.value })}
                    placeholder="https://..."
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-foreground">Booking Banner URL</label>
                  <Input
                    value={formData.booking_page_banner_url}
                    onChange={(e) => setFormData({ ...formData, booking_page_banner_url: e.target.value })}
                    placeholder="https://..."
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-foreground">Booking Logo</label>
                  <div className="flex flex-col gap-3 rounded-xl border border-border p-4">
                    <div className="relative flex h-20 w-32 items-center justify-center overflow-hidden rounded-2xl border border-border bg-white p-3">
                      {formData.booking_page_logo_url ? (
                        <Image
                          src={formData.booking_page_logo_url}
                          alt="Booking logo preview"
                          fill
                          className="object-contain p-3"
                          unoptimized
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                          No logo
                        </div>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Upload your logo directly instead of pasting a URL.
                    </p>
                    <div>
                      <input
                        ref={logoInputRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => void handleImageUpload("booking_logo", e.target.files?.[0] ?? null)}
                      />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => logoInputRef.current?.click()}
                        disabled={uploadingTarget === "booking_logo"}
                      >
                        <Upload className="mr-2 h-4 w-4" />
                        {uploadingTarget === "booking_logo" ? "Uploading..." : "Upload Logo"}
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="md:col-span-2">
                  <label className="mb-2 block text-sm font-medium text-foreground">Booking Banner</label>
                  <div className="flex flex-col gap-3 rounded-xl border border-border p-4">
                    <div className="relative h-36 w-full overflow-hidden rounded-2xl border border-border bg-muted">
                      {formData.booking_page_banner_url ? (
                        <Image
                          src={formData.booking_page_banner_url}
                          alt="Booking banner preview"
                          fill
                          className="object-cover"
                          unoptimized
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                          No banner selected
                        </div>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Add a full-width hero image to make your booking page feel branded and polished.
                    </p>
                    <div>
                      <input
                        ref={bannerInputRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => void handleImageUpload("booking_banner", e.target.files?.[0] ?? null)}
                      />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => bannerInputRef.current?.click()}
                        disabled={uploadingTarget === "booking_banner"}
                      >
                        <Upload className="mr-2 h-4 w-4" />
                        {uploadingTarget === "booking_banner" ? "Uploading..." : "Upload Banner"}
                      </Button>
                    </div>
                  </div>
                </div>

                <div
                  className="overflow-hidden rounded-xl border border-border"
                  style={{ borderColor: formData.booking_page_brand_color }}
                >
                  {formData.booking_page_banner_url && (
                    <div className="relative h-40 w-full">
                      <Image
                        src={formData.booking_page_banner_url}
                        alt="Booking banner preview"
                        fill
                        className="object-cover"
                        unoptimized
                      />
                      <div className="absolute inset-0 bg-black/25" />
                    </div>
                  )}
                  <div className="p-5">
                    <div className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      Preview
                    </div>
                    {formData.booking_page_logo_url && (
                      <div className="relative mb-4 flex h-14 w-28 items-center justify-center overflow-hidden rounded-xl border border-border bg-white p-2">
                        <Image
                          src={formData.booking_page_logo_url}
                          alt="Booking logo preview"
                          fill
                          className="object-contain p-2"
                          unoptimized
                        />
                      </div>
                    )}
                    <h3 className="text-xl font-semibold text-foreground">
                      {formData.booking_page_title || profile?.name || "Book your session"}
                    </h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {formData.booking_page_description || "Your public booking page will show this customized message."}
                    </p>
                    <div
                      className="mt-4 inline-flex rounded-full px-3 py-1 text-sm font-medium text-white"
                      style={{ backgroundColor: formData.booking_page_brand_color }}
                    >
                      Accent Color Preview
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-end">
              <Button type="submit" disabled={saving}>
                {saving ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </form>
        )}
      </div>
    </Shell>
  );
}
