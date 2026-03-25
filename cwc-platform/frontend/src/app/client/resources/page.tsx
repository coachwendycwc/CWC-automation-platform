"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import {
  FileText,
  Video,
  Link as LinkIcon,
  Download,
  ExternalLink,
  FolderOpen,
  Clock,
  File,
} from "lucide-react";

interface Resource {
  id: string;
  title: string;
  description: string | null;
  content_type: string;
  category: string | null;
  file_name: string | null;
  file_size: number | null;
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

export default function ClientResourcesPage() {
  const { sessionToken } = useClientAuth();
  const [resources, setResources] = useState<Resource[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      if (!sessionToken) return;

      try {
        const [resourcesData, categoriesData] = await Promise.all([
          clientPortalApi.getResources(sessionToken, selectedCategory || undefined),
          clientPortalApi.getResourceCategories(sessionToken),
        ]);
        setResources(resourcesData);
        setCategories(categoriesData.categories);
      } catch (error) {
        console.error("Failed to load resources:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [sessionToken, selectedCategory]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
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

  const getIcon = (type: string) => {
    const Icon = CONTENT_TYPE_ICONS[type] || File;
    return Icon;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  // Group resources by category
  const groupedResources = resources.reduce((acc, resource) => {
    const category = resource.category || "General";
    if (!acc[category]) acc[category] = [];
    acc[category].push(resource);
    return acc;
  }, {} as Record<string, Resource[]>);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Resources</h1>
        <p className="text-muted-foreground">
          Downloads, worksheets, and materials for your coaching journey
        </p>
      </div>

      {/* Category Filter */}
      {categories.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          <Button
            variant={selectedCategory === "" ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedCategory("")}
          >
            All
          </Button>
          {categories.map((cat) => (
            <Button
              key={cat}
              variant={selectedCategory === cat ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </Button>
          ))}
        </div>
      )}

      {/* Resources */}
      {resources.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FolderOpen className="h-12 w-12 text-muted-foreground/40 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground">No resources</h3>
            <p className="text-muted-foreground">
              {selectedCategory
                ? "No resources in this category"
                : "No resources available yet"}
            </p>
          </CardContent>
        </Card>
      ) : selectedCategory ? (
        // Flat list when filtered
        <div className="space-y-3">
          {resources.map((resource) => (
            <ResourceCard key={resource.id} resource={resource} />
          ))}
        </div>
      ) : (
        // Grouped by category when showing all
        <div className="space-y-8">
          {Object.entries(groupedResources).map(([category, items]) => (
            <div key={category}>
              <h2 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
                <FolderOpen className="h-5 w-5 text-muted-foreground" />
                {category}
              </h2>
              <div className="space-y-3">
                {items.map((resource) => (
                  <ResourceCard key={resource.id} resource={resource} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ResourceCard({ resource }: { resource: Resource }) {
  const Icon = CONTENT_TYPE_ICONS[resource.content_type] || File;
  const colorClass = CONTENT_TYPE_COLORS[resource.content_type] || "bg-muted text-muted-foreground";

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer">
      <CardContent className="py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-2.5 rounded-xl ${colorClass}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <p className="font-medium text-foreground">{resource.title}</p>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                {resource.description && (
                  <span className="line-clamp-1 max-w-md">
                    {resource.description}
                  </span>
                )}
                {!resource.description && resource.file_name && (
                  <span>{resource.file_name}</span>
                )}
                {resource.file_size && (
                  <>
                    <span className="text-muted-foreground/40">·</span>
                    <span>{formatFileSize(resource.file_size)}</span>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {!resource.is_released && resource.release_date && (
              <Badge variant="outline" className="text-orange-600 border-orange-200">
                <Clock className="h-3 w-3 mr-1" />
                Available {formatDate(resource.release_date)}
              </Badge>
            )}
            {resource.is_released && (
              <Link href={`/client/resources/${resource.id}`}>
                <Button variant="outline" size="sm">
                  {resource.external_url ? (
                    <>
                      Open
                      <ExternalLink className="ml-2 h-4 w-4" />
                    </>
                  ) : (
                    <>
                      View
                      <Download className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
              </Link>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
