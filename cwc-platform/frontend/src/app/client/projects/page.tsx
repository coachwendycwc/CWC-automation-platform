"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { FolderKanban, ExternalLink, User } from "lucide-react";

interface Project {
  id: string;
  name: string;
  status: string;
  progress: number;
  created_at: string;
  contact_name: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  planning: "bg-warning/10 text-warning",
  in_progress: "bg-primary/10 text-primary",
  review: "bg-accent/10 text-accent",
  completed: "bg-success/10 text-success",
  on_hold: "bg-muted text-foreground",
  cancelled: "bg-destructive/10 text-destructive",
};

export default function ClientProjectsPage() {
  const { sessionToken } = useClientAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProjects = async () => {
      if (!sessionToken) return;

      try {
        const data = await clientPortalApi.getProjects(sessionToken);
        setProjects(data);
      } catch (error) {
        console.error("Failed to load projects:", error);
      } finally {
        setLoading(false);
      }
    };

    loadProjects();
  }, [sessionToken]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Projects</h1>
        <p className="text-muted-foreground">Track the progress of your projects</p>
      </div>

      {projects.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FolderKanban className="h-12 w-12 text-muted-foreground/40 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground">No projects</h3>
            <p className="text-muted-foreground">You don&apos;t have any active projects</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {projects.map((project) => (
            <Card
              key={project.id}
              className="hover:shadow-md transition-shadow cursor-pointer"
            >
              <CardContent className="pt-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-lg">{project.name}</h3>
                    <p className="text-sm text-muted-foreground">
                      Started {formatDate(project.created_at)}
                      {project.contact_name && (
                        <>
                          {" "}&middot;{" "}
                          <span className="inline-flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {project.contact_name}
                          </span>
                        </>
                      )}
                    </p>
                  </div>
                  <Badge className={STATUS_COLORS[project.status]}>
                    {project.status.replace("_", " ")}
                  </Badge>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Progress</span>
                    <span className="font-medium">
                      {Math.round(project.progress)}%
                    </span>
                  </div>
                  <Progress value={project.progress} className="h-2" />
                </div>

                <Link href={`/client/projects/${project.id}`}>
                  <Button variant="outline" size="sm" className="w-full">
                    View Details
                    <ExternalLink className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
