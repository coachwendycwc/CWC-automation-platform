"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ArrowLeft,
  Building2,
  User,
  Mail,
  Phone,
  Globe,
  Target,
  Users,
  DollarSign,
  Clock,
  CheckCircle,
  MessageSquare,
  Calendar,
  Briefcase,
  Eye,
  Archive,
  ExternalLink,
} from "lucide-react";
import Sidebar from "@/components/layout/Sidebar";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface Assessment {
  id: string;
  full_name: string;
  title_role: string;
  organization_name: string;
  work_email: string;
  phone_number: string | null;
  organization_website: string | null;
  areas_of_interest: string[];
  areas_of_interest_other: string | null;
  desired_outcomes: string[];
  desired_outcomes_other: string | null;
  current_challenge: string | null;
  primary_audience: string[];
  primary_audience_other: string | null;
  participant_count: string | null;
  preferred_format: string | null;
  location: string | null;
  budget_range: string | null;
  specific_budget: string | null;
  ideal_timeline: string | null;
  specific_date: string | null;
  decision_makers: string[];
  decision_makers_other: string | null;
  decision_stage: string | null;
  decision_stage_other: string | null;
  success_definition: string | null;
  accessibility_needs: string | null;
  contact_id: string | null;
  organization_id: string | null;
  booking_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

const statusConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  submitted: { label: "New", color: "bg-blue-100 text-blue-800", icon: <Clock className="w-4 h-4" /> },
  reviewed: { label: "Reviewed", color: "bg-yellow-100 text-yellow-800", icon: <Eye className="w-4 h-4" /> },
  contacted: { label: "Contacted", color: "bg-purple-100 text-purple-800", icon: <MessageSquare className="w-4 h-4" /> },
  converted: { label: "Converted", color: "bg-green-100 text-green-800", icon: <CheckCircle className="w-4 h-4" /> },
  archived: { label: "Archived", color: "bg-gray-100 text-gray-800", icon: <Archive className="w-4 h-4" /> },
};

const areaLabels: Record<string, string> = {
  executive_coaching: "Executive Coaching for Leaders (1:1)",
  group_coaching: "Group Coaching for Leaders / Cohorts",
  keynote_speaking: "Keynote Speaking",
  webinars_workshops: "Customized Webinars & Workshops",
  virtual_series: "Multi-Session Virtual Series",
  other: "Other",
};

const outcomeLabels: Record<string, string> = {
  executive_presence: "Strengthen executive presence and leadership effectiveness",
  communication_collaboration: "Improve communication and collaboration",
  psychological_safety: "Build psychological safety and trust",
  navigating_bias: "Support leaders navigating bias and double standards",
  retention_engagement: "Increase retention and engagement of women of color",
  inclusive_leadership: "Develop inclusive leadership practices across managers/leaders",
  team_reset: "Team reset after conflict, change, or reorg",
  other: "Other",
};

const audienceLabels: Record<string, string> = {
  senior_leaders: "Senior leaders / executives",
  mid_level_managers: "Mid-level managers",
  high_potential: "High-potential talent",
  specific_team: "A specific team",
  erg_affinity: "ERG / affinity group",
  organization_wide: "Organization-wide",
  other: "Other",
};

const formatLabels: Record<string, string> = {
  virtual: "Virtual",
  in_person: "In-person",
  hybrid: "Hybrid",
  not_sure: "Not sure yet",
};

const budgetLabels: Record<string, string> = {
  under_5k: "Under $5,000",
  "5k_10k": "$5,000–$9,999",
  "10k_20k": "$10,000–$19,999",
  "20k_40k": "$20,000–$39,999",
  "40k_plus": "$40,000+",
  not_sure: "Not sure yet / need guidance",
};

const timelineLabels: Record<string, string> = {
  asap: "ASAP (within 2–4 weeks)",
  "1_2_months": "1–2 months",
  "3_4_months": "3–4 months",
  "5_plus_months": "5+ months",
  not_sure: "Not sure yet",
};

const decisionMakerLabels: Record<string, string> = {
  self: "I'm the decision maker",
  hr: "HR / People Team",
  ld_talent: "L&D / Talent Development",
  dei: "DEI / Inclusion",
  executive: "Executive leadership",
  procurement: "Procurement",
  other: "Other",
};

const decisionStageLabels: Record<string, string> = {
  exploring: "Exploring options",
  comparing: "Comparing vendors",
  ready_to_select: "Ready to select a partner soon",
  need_approval: "Need internal approval",
  other: "Other",
};

export default function AssessmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchAssessment();
  }, [params.id]);

  const fetchAssessment = async () => {
    try {
      const response = await fetch(`${API_URL}/api/assessments/${params.id}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAssessment(data);
      } else {
        router.push("/assessments");
      }
    } catch (error) {
      console.error("Failed to fetch assessment:", error);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (newStatus: string) => {
    if (!assessment) return;
    setUpdating(true);

    try {
      const response = await fetch(`${API_URL}/api/assessments/${assessment.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (response.ok) {
        const data = await response.json();
        setAssessment(data);
      }
    } catch (error) {
      console.error("Failed to update status:", error);
    } finally {
      setUpdating(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 p-8">
          <div className="max-w-4xl mx-auto space-y-6">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-48 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
        </main>
      </div>
    );
  }

  if (!assessment) {
    return null;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <Link href="/assessments" className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Assessments
            </Link>

            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{assessment.organization_name}</h1>
                <p className="text-gray-600 mt-1">
                  Submitted {formatDate(assessment.created_at)}
                </p>
              </div>

              <div className="flex items-center gap-3">
                <Select
                  value={assessment.status}
                  onValueChange={updateStatus}
                  disabled={updating}
                >
                  <SelectTrigger className="w-44">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="submitted">New</SelectItem>
                    <SelectItem value="reviewed">Reviewed</SelectItem>
                    <SelectItem value="contacted">Contacted</SelectItem>
                    <SelectItem value="converted">Converted</SelectItem>
                    <SelectItem value="archived">Archived</SelectItem>
                  </SelectContent>
                </Select>

                <Badge className={`${statusConfig[assessment.status]?.color} px-3 py-1`}>
                  <span className="flex items-center gap-1">
                    {statusConfig[assessment.status]?.icon}
                    {statusConfig[assessment.status]?.label}
                  </span>
                </Badge>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex gap-3 mb-6">
            <Button asChild>
              <a href={`mailto:${assessment.work_email}`}>
                <Mail className="w-4 h-4 mr-2" />
                Send Email
              </a>
            </Button>
            {assessment.contact_id && (
              <Button variant="outline" asChild>
                <Link href={`/contacts/${assessment.contact_id}`}>
                  <User className="w-4 h-4 mr-2" />
                  View Contact
                </Link>
              </Button>
            )}
            {assessment.organization_id && (
              <Button variant="outline" asChild>
                <Link href={`/organizations/${assessment.organization_id}`}>
                  <Building2 className="w-4 h-4 mr-2" />
                  View Organization
                </Link>
              </Button>
            )}
          </div>

          {/* Contact Information */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5" />
                Contact Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-500">Full Name</p>
                    <p className="font-medium">{assessment.full_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Title / Role</p>
                    <p className="font-medium">{assessment.title_role}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Organization</p>
                    <p className="font-medium">{assessment.organization_name}</p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-500">Email</p>
                    <a href={`mailto:${assessment.work_email}`} className="font-medium text-purple-600 hover:underline flex items-center gap-1">
                      <Mail className="w-4 h-4" />
                      {assessment.work_email}
                    </a>
                  </div>
                  {assessment.phone_number && (
                    <div>
                      <p className="text-sm text-gray-500">Phone</p>
                      <a href={`tel:${assessment.phone_number}`} className="font-medium flex items-center gap-1">
                        <Phone className="w-4 h-4" />
                        {assessment.phone_number}
                      </a>
                    </div>
                  )}
                  {assessment.organization_website && (
                    <div>
                      <p className="text-sm text-gray-500">Website</p>
                      <a href={assessment.organization_website} target="_blank" rel="noopener noreferrer" className="font-medium text-purple-600 hover:underline flex items-center gap-1">
                        <Globe className="w-4 h-4" />
                        {assessment.organization_website}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Areas of Interest */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5" />
                Areas of Interest
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {assessment.areas_of_interest.map((area) => (
                  <Badge key={area} variant="secondary" className="px-3 py-1">
                    {areaLabels[area] || area}
                  </Badge>
                ))}
              </div>
              {assessment.areas_of_interest_other && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500 mb-1">Additional details:</p>
                  <p>{assessment.areas_of_interest_other}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Goals and Needs */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5" />
                Goals and Needs
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {assessment.desired_outcomes.length > 0 && (
                <div>
                  <p className="text-sm text-gray-500 mb-2">Desired Outcomes</p>
                  <ul className="space-y-2">
                    {assessment.desired_outcomes.map((outcome) => (
                      <li key={outcome} className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span>{outcomeLabels[outcome] || outcome}</span>
                      </li>
                    ))}
                  </ul>
                  {assessment.desired_outcomes_other && (
                    <p className="mt-2 text-gray-600 italic">Other: {assessment.desired_outcomes_other}</p>
                  )}
                </div>
              )}

              {assessment.current_challenge && (
                <div>
                  <p className="text-sm text-gray-500 mb-2">Current Challenge</p>
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                    <p>{assessment.current_challenge}</p>
                  </div>
                </div>
              )}

              {assessment.primary_audience.length > 0 && (
                <div>
                  <p className="text-sm text-gray-500 mb-2">Primary Audience</p>
                  <div className="flex flex-wrap gap-2">
                    {assessment.primary_audience.map((audience) => (
                      <Badge key={audience} variant="outline">
                        {audienceLabels[audience] || audience}
                      </Badge>
                    ))}
                  </div>
                  {assessment.primary_audience_other && (
                    <p className="mt-2 text-gray-600 italic">Other: {assessment.primary_audience_other}</p>
                  )}
                </div>
              )}

              <div className="grid md:grid-cols-2 gap-4">
                {assessment.participant_count && (
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500">Participants:</span>
                    <span className="font-medium">{assessment.participant_count}</span>
                  </div>
                )}
                {assessment.preferred_format && (
                  <div className="flex items-center gap-2">
                    <Briefcase className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500">Format:</span>
                    <span className="font-medium">{formatLabels[assessment.preferred_format] || assessment.preferred_format}</span>
                  </div>
                )}
                {assessment.location && (
                  <div className="flex items-center gap-2 md:col-span-2">
                    <Globe className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500">Location:</span>
                    <span className="font-medium">{assessment.location}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Budget and Timeline */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="w-5 h-5" />
                Budget and Timeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-500">Budget Range</p>
                    <p className="font-medium text-lg">
                      {assessment.budget_range ? budgetLabels[assessment.budget_range] || assessment.budget_range : "Not specified"}
                    </p>
                  </div>
                  {assessment.specific_budget && (
                    <div>
                      <p className="text-sm text-gray-500">Specific Budget</p>
                      <p className="font-medium">{assessment.specific_budget}</p>
                    </div>
                  )}
                </div>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-500">Ideal Timeline</p>
                    <p className="font-medium text-lg">
                      {assessment.ideal_timeline ? timelineLabels[assessment.ideal_timeline] || assessment.ideal_timeline : "Not specified"}
                    </p>
                  </div>
                  {assessment.specific_date && (
                    <div>
                      <p className="text-sm text-gray-500">Tied to Specific Date/Event</p>
                      <p className="font-medium">{assessment.specific_date}</p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Decision Process */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Decision Process
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {assessment.decision_makers.length > 0 && (
                <div>
                  <p className="text-sm text-gray-500 mb-2">Decision Makers Involved</p>
                  <div className="flex flex-wrap gap-2">
                    {assessment.decision_makers.map((dm) => (
                      <Badge key={dm} variant="outline">
                        {decisionMakerLabels[dm] || dm}
                      </Badge>
                    ))}
                  </div>
                  {assessment.decision_makers_other && (
                    <p className="mt-2 text-gray-600 italic">Other: {assessment.decision_makers_other}</p>
                  )}
                </div>
              )}

              {assessment.decision_stage && (
                <div>
                  <p className="text-sm text-gray-500 mb-1">Decision Stage</p>
                  <p className="font-medium">
                    {decisionStageLabels[assessment.decision_stage] || assessment.decision_stage}
                  </p>
                  {assessment.decision_stage_other && (
                    <p className="text-gray-600 italic">Other: {assessment.decision_stage_other}</p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Additional Context */}
          {(assessment.success_definition || assessment.accessibility_needs) && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  Additional Context
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {assessment.success_definition && (
                  <div>
                    <p className="text-sm text-gray-500 mb-2">What would make this partnership a "win" six months from now?</p>
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <p>{assessment.success_definition}</p>
                    </div>
                  </div>
                )}

                {assessment.accessibility_needs && (
                  <div>
                    <p className="text-sm text-gray-500 mb-2">Accessibility needs or considerations</p>
                    <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                      <p>{assessment.accessibility_needs}</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
