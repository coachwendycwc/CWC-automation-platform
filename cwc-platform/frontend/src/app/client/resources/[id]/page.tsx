"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import {
  ArrowLeft,
  FileText,
  Video,
  Link as LinkIcon,
  Download,
  ExternalLink,
  File,
  Calendar,
  Clock,
} from "lucide-react";

interface ResourceDetail {
  id: string;
  title: string;
  description: string | null;
  content_type: string;
  category: string | null;
  file_name: string | null;
  file_size: number | null;
  file_url: string | null;
  mime_type: string | null;
  external_url: string | null;
  release_date: string | null;
  is_released: boolean;
  created_at: string;
}

const CONTENT_TYPE_ICONS: Record<string, any> = {
  file: File,
  document: FileText,
  video: Video,
  link: LinkIcon,
};

const CONTENT_TYPE_COLORS: Record<string, string> = {
  file: "bg-primary/10 text-primary",
  document: "bg-accent/10 text-accent",
  video: "bg-destructive/10 text-destructive",
  link: "bg-success/10 text-success",
};

export default function ResourceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { sessionToken } = useClientAuth();
  const [resource, setResource] = useState<ResourceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadResource = async () => {
      if (!sessionToken || !params.id) return;

      try {
        const data = await clientPortalApi.getResource(
          sessionToken,
          params.id as string
        );
        setResource(data);
      } catch (err: any) {
        console.error("Failed to load resource:", err);
        if (err.response?.status === 404) {
          setError("Resource not found");
        } else if (err.response?.status === 403) {
          setError("This resource is not yet available");
        } else {
          setError("Failed to load resource");
        }
      } finally {
        setLoading(false);
      }
    };

    loadResource();
  }, [sessionToken, params.id]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleDownload = async () => {
    if (!resource?.file_url) return;

    // Open the file URL in a new tab or trigger download
    window.open(resource.file_url, "_blank");
  };

  const handleOpenLink = () => {
    if (!resource?.external_url) return;
    window.open(resource.external_url, "_blank", "noopener,noreferrer");
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-9 w-20" />
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-40" />
          </div>
        </div>
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Link
          href="/client/resources"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Resources
        </Link>
        <Card>
          <CardContent className="py-12 text-center">
            <div className="text-destructive mb-2">{error}</div>
            <Button variant="outline" onClick={() => router.push("/client/resources")}>
              Return to Resources
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!resource) {
    return null;
  }

  const Icon = CONTENT_TYPE_ICONS[resource.content_type] || File;
  const colorClass =
    CONTENT_TYPE_COLORS[resource.content_type] || "bg-muted text-muted-foreground";

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href="/client/resources"
        className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to Resources
      </Link>

      {/* Resource Detail Card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-xl ${colorClass}`}>
                <Icon className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl">{resource.title}</CardTitle>
                {resource.category && (
                  <Badge variant="outline" className="mt-1">
                    {resource.category}
                  </Badge>
                )}
              </div>
            </div>

            {/* Action Button */}
            {resource.is_released && (
              <div>
                {resource.external_url ? (
                  <Button onClick={handleOpenLink}>
                    Open Link
                    <ExternalLink className="ml-2 h-4 w-4" />
                  </Button>
                ) : resource.file_url ? (
                  <Button onClick={handleDownload}>
                    Download
                    <Download className="ml-2 h-4 w-4" />
                  </Button>
                ) : null}
              </div>
            )}

            {!resource.is_released && resource.release_date && (
              <Badge variant="outline" className="text-orange-600 border-orange-200">
                <Clock className="h-3 w-3 mr-1" />
                Available {formatDate(resource.release_date)}
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Description */}
          {resource.description && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Description</h3>
              <p className="text-foreground whitespace-pre-wrap">{resource.description}</p>
            </div>
          )}

          {/* File Details */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            {resource.file_name && (
              <div>
                <span className="text-muted-foreground">File name:</span>
                <span className="ml-2 text-foreground">{resource.file_name}</span>
              </div>
            )}
            {resource.file_size && (
              <div>
                <span className="text-muted-foreground">Size:</span>
                <span className="ml-2 text-foreground">
                  {formatFileSize(resource.file_size)}
                </span>
              </div>
            )}
            {resource.mime_type && (
              <div>
                <span className="text-muted-foreground">Type:</span>
                <span className="ml-2 text-foreground">{resource.mime_type}</span>
              </div>
            )}
            <div>
              <span className="text-muted-foreground">Added:</span>
              <span className="ml-2 text-foreground">
                {formatDate(resource.created_at)}
              </span>
            </div>
          </div>

          {/* Video Preview (for video content) */}
          {resource.content_type === "video" && resource.external_url && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-muted-foreground mb-3">Preview</h3>
              {resource.external_url.includes("youtube.com") ||
              resource.external_url.includes("youtu.be") ? (
                <div className="aspect-video rounded-lg overflow-hidden bg-muted">
                  <iframe
                    src={convertToEmbedUrl(resource.external_url)}
                    className="w-full h-full"
                    allowFullScreen
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  />
                </div>
              ) : resource.external_url.includes("vimeo.com") ? (
                <div className="aspect-video rounded-lg overflow-hidden bg-muted">
                  <iframe
                    src={convertVimeoToEmbed(resource.external_url)}
                    className="w-full h-full"
                    allowFullScreen
                  />
                </div>
              ) : (
                <Button onClick={handleOpenLink} variant="outline">
                  Watch Video
                  <ExternalLink className="ml-2 h-4 w-4" />
                </Button>
              )}
            </div>
          )}

          {/* Document Preview hint */}
          {resource.content_type === "document" && resource.file_url && (
            <div className="p-4 bg-muted rounded-lg text-center">
              <FileText className="h-12 w-12 text-muted-foreground/40 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">
                Click the Download button to view this document
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Helper function to convert YouTube URLs to embed format
function convertToEmbedUrl(url: string): string {
  // Handle youtu.be format
  const shortMatch = url.match(/youtu\.be\/([^?&]+)/);
  if (shortMatch) {
    return `https://www.youtube.com/embed/${shortMatch[1]}`;
  }

  // Handle youtube.com/watch format
  const watchMatch = url.match(/youtube\.com\/watch\?v=([^&]+)/);
  if (watchMatch) {
    return `https://www.youtube.com/embed/${watchMatch[1]}`;
  }

  // Already embed format or unknown
  return url;
}

// Helper function to convert Vimeo URLs to embed format
function convertVimeoToEmbed(url: string): string {
  const match = url.match(/vimeo\.com\/(\d+)/);
  if (match) {
    return `https://player.vimeo.com/video/${match[1]}`;
  }
  return url;
}
