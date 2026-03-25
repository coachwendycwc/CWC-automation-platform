"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Search,
  Building2,
  Users,
  Clock,
  CheckCircle,
  MessageSquare,
  Archive,
  Eye,
  DollarSign,
} from "lucide-react";
import { Shell } from "@/components/layout/Shell";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface Assessment {
  id: string;
  full_name: string;
  title_role: string;
  organization_name: string;
  work_email: string;
  phone_number: string | null;
  areas_of_interest: string[];
  budget_range: string | null;
  ideal_timeline: string | null;
  status: string;
  created_at: string;
}

interface Stats {
  total: number;
  submitted: number;
  reviewed: number;
  contacted: number;
  converted: number;
  archived: number;
}

const statusConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  submitted: { label: "New", color: "bg-primary/10 text-primary", icon: <Clock className="w-3 h-3" /> },
  reviewed: { label: "Reviewed", color: "bg-warning/10 text-warning", icon: <Eye className="w-3 h-3" /> },
  contacted: { label: "Contacted", color: "bg-accent/10 text-accent", icon: <MessageSquare className="w-3 h-3" /> },
  converted: { label: "Converted", color: "bg-success/10 text-success", icon: <CheckCircle className="w-3 h-3" /> },
  archived: { label: "Archived", color: "bg-muted text-muted-foreground", icon: <Archive className="w-3 h-3" /> },
};

const budgetLabels: Record<string, string> = {
  under_5k: "< $5K",
  "5k_10k": "$5K-$10K",
  "10k_20k": "$10K-$20K",
  "20k_40k": "$20K-$40K",
  "40k_plus": "$40K+",
  not_sure: "TBD",
};

const timelineLabels: Record<string, string> = {
  asap: "ASAP",
  "1_2_months": "1-2 mo",
  "3_4_months": "3-4 mo",
  "5_plus_months": "5+ mo",
  not_sure: "TBD",
};

const areaLabels: Record<string, string> = {
  executive_coaching: "Exec Coaching",
  group_coaching: "Group Coaching",
  keynote_speaking: "Keynote",
  webinars_workshops: "Workshops",
  virtual_series: "Virtual Series",
  other: "Other",
};

export default function AssessmentsPage() {
  const router = useRouter();
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    fetchAssessments();
    fetchStats();
  }, [statusFilter]);

  const fetchAssessments = async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter && statusFilter !== "all") {
        params.append("status", statusFilter);
      }
      if (search) {
        params.append("search", search);
      }

      const response = await fetch(`${API_URL}/api/assessments?${params}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAssessments(data.items);
      }
    } catch (error) {
      console.error("Failed to fetch assessments:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/assessments/stats`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchAssessments();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <Shell>
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground">Organizational Assessments</h1>
            <p className="text-muted-foreground mt-1">
              Review and manage needs assessments from organizations
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            <Card
              className={`cursor-pointer transition-all ${statusFilter === "all" ? "ring-2 ring-purple-500" : "hover:shadow-md"}`}
              onClick={() => setStatusFilter("all")}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total</p>
                    <p className="text-2xl font-bold">{stats?.total || 0}</p>
                  </div>
                  <Building2 className="w-8 h-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>

            <Card
              className={`cursor-pointer transition-all ${statusFilter === "submitted" ? "ring-2 ring-blue-500" : "hover:shadow-md"}`}
              onClick={() => setStatusFilter("submitted")}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">New</p>
                    <p className="text-2xl font-bold text-primary">{stats?.submitted || 0}</p>
                  </div>
                  <Clock className="w-8 h-8 text-primary/60" />
                </div>
              </CardContent>
            </Card>

            <Card
              className={`cursor-pointer transition-all ${statusFilter === "reviewed" ? "ring-2 ring-yellow-500" : "hover:shadow-md"}`}
              onClick={() => setStatusFilter("reviewed")}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Reviewed</p>
                    <p className="text-2xl font-bold text-warning">{stats?.reviewed || 0}</p>
                  </div>
                  <Eye className="w-8 h-8 text-warning/60" />
                </div>
              </CardContent>
            </Card>

            <Card
              className={`cursor-pointer transition-all ${statusFilter === "contacted" ? "ring-2 ring-purple-500" : "hover:shadow-md"}`}
              onClick={() => setStatusFilter("contacted")}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Contacted</p>
                    <p className="text-2xl font-bold text-accent">{stats?.contacted || 0}</p>
                  </div>
                  <MessageSquare className="w-8 h-8 text-accent/60" />
                </div>
              </CardContent>
            </Card>

            <Card
              className={`cursor-pointer transition-all ${statusFilter === "converted" ? "ring-2 ring-green-500" : "hover:shadow-md"}`}
              onClick={() => setStatusFilter("converted")}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Converted</p>
                    <p className="text-2xl font-bold text-success">{stats?.converted || 0}</p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-success/60" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filters */}
          <Card className="mb-6">
            <CardContent className="p-4">
              <form onSubmit={handleSearch} className="flex gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by organization, name, or email..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="All statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="submitted">New</SelectItem>
                    <SelectItem value="reviewed">Reviewed</SelectItem>
                    <SelectItem value="contacted">Contacted</SelectItem>
                    <SelectItem value="converted">Converted</SelectItem>
                    <SelectItem value="archived">Archived</SelectItem>
                  </SelectContent>
                </Select>
                <Button type="submit">Search</Button>
              </form>
            </CardContent>
          </Card>

          {/* Table */}
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="p-8 space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : assessments.length === 0 ? (
                <div className="p-8 text-center">
                  <Building2 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-foreground mb-1">No assessments found</h3>
                  <p className="text-muted-foreground">
                    {statusFilter !== "all"
                      ? "Try changing the filter or search terms"
                      : "Assessments will appear here when organizations submit the form"}
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Organization</TableHead>
                      <TableHead>Contact</TableHead>
                      <TableHead>Interests</TableHead>
                      <TableHead>Budget</TableHead>
                      <TableHead>Timeline</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Submitted</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {assessments.map((assessment) => (
                      <TableRow
                        key={assessment.id}
                        className="cursor-pointer hover:bg-muted"
                        onClick={() => router.push(`/assessments/${assessment.id}`)}
                      >
                        <TableCell>
                          <div className="font-medium">{assessment.organization_name}</div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <div className="font-medium">{assessment.full_name}</div>
                            <div className="text-muted-foreground">{assessment.title_role}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {assessment.areas_of_interest.slice(0, 2).map((area) => (
                              <Badge key={area} variant="outline" className="text-xs">
                                {areaLabels[area] || area}
                              </Badge>
                            ))}
                            {assessment.areas_of_interest.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{assessment.areas_of_interest.length - 2}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1 text-sm">
                            <DollarSign className="w-3 h-3 text-muted-foreground" />
                            {assessment.budget_range
                              ? budgetLabels[assessment.budget_range] || assessment.budget_range
                              : "-"}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1 text-sm">
                            <Clock className="w-3 h-3 text-muted-foreground" />
                            {assessment.ideal_timeline
                              ? timelineLabels[assessment.ideal_timeline] || assessment.ideal_timeline
                              : "-"}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={statusConfig[assessment.status]?.color || "bg-muted"}>
                            <span className="flex items-center gap-1">
                              {statusConfig[assessment.status]?.icon}
                              {statusConfig[assessment.status]?.label || assessment.status}
                            </span>
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatDate(assessment.created_at)}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/assessments/${assessment.id}`);
                            }}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
    </Shell>
  );
}
