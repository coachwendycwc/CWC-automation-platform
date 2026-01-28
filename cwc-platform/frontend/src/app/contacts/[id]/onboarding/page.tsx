"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  User,
  BarChart,
  MessageSquare,
  Target,
  Heart,
  Calendar,
  CheckCircle,
  Clock,
  Send,
  RefreshCw,
  Copy,
} from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { contactsApi, onboardingAssessmentsApi, OnboardingAssessmentResponse } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";

// Motivation labels
const MOTIVATION_LABELS: Record<string, string> = {
  career_transition: "Career transition",
  new_role: "Getting into a new role/position",
  workplace_challenges: "Workplace challenges - Race / Gender tensions",
  work_life_balance: "Work/life balance / well-being concerns",
  leadership_step: "Desire to take the next leadership step",
};

// Feedback preference labels
const FEEDBACK_LABELS: Record<string, string> = {
  direct: "Direct and straightforward",
  gentle: "Gentle and supportive",
  both: "A mix of both",
  explore: "Let's explore together what works best",
};

export default function OnboardingAssessmentViewPage() {
  const router = useRouter();
  const params = useParams();
  const contactId = params.id as string;

  const [contact, setContact] = useState<any>(null);
  const [assessment, setAssessment] = useState<OnboardingAssessmentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/");
      return;
    }
    fetchData(token);
  }, [router, contactId]);

  const fetchData = async (token: string) => {
    try {
      const [contactData, assessmentData] = await Promise.all([
        contactsApi.get(token, contactId),
        onboardingAssessmentsApi.getForContact(token, contactId),
      ]);
      setContact(contactData);
      setAssessment(assessmentData);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    setResending(true);
    try {
      await onboardingAssessmentsApi.resendEmail(token, contactId);
      toast.success("Assessment email resent");
    } catch (error: any) {
      toast.error(error.message || "Failed to resend email");
    } finally {
      setResending(false);
    }
  };

  const handleCopyLink = () => {
    if (!assessment) return;
    const url = `${window.location.origin}/onboarding/${assessment.token}`;
    navigator.clipboard.writeText(url);
    toast.success("Link copied to clipboard");
  };

  const RatingDisplay = ({ value, label }: { value: number | null | undefined; label: string }) => {
    if (!value) return null;
    return (
      <div className="flex items-center justify-between py-2 border-b last:border-b-0">
        <span className="text-sm text-gray-600">{label}</span>
        <div className="flex items-center gap-1">
          <span className="text-sm font-medium">{value}/10</span>
          <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-violet-500 rounded-full"
              style={{ width: `${(value / 10) * 100}%` }}
            />
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <Shell>
        <div className="flex items-center justify-center py-12">
          <div className="text-gray-500">Loading...</div>
        </div>
      </Shell>
    );
  }

  if (!assessment) {
    return (
      <Shell>
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">Onboarding Assessment</h1>
              <p className="text-gray-500">{contact?.full_name}</p>
            </div>
          </div>

          <Card>
            <CardContent className="py-12 text-center">
              <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h2 className="text-lg font-medium mb-2">No Assessment Yet</h2>
              <p className="text-gray-500 mb-4">
                This contact hasn't been sent an onboarding assessment yet.
              </p>
              <Link href={`/contacts/${contactId}`}>
                <Button>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Contact
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">Onboarding Assessment</h1>
              <p className="text-gray-500">{contact?.full_name}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {assessment.completed_at ? (
              <Badge variant="success" className="flex items-center gap-1">
                <CheckCircle className="h-3 w-3" />
                Completed {formatDateTime(assessment.completed_at)}
              </Badge>
            ) : (
              <>
                <Badge variant="warning" className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Pending
                </Badge>
                <Button variant="outline" size="sm" onClick={handleCopyLink}>
                  <Copy className="h-4 w-4 mr-1" />
                  Copy Link
                </Button>
                <Button variant="outline" size="sm" onClick={handleResend} disabled={resending}>
                  <RefreshCw className={`h-4 w-4 mr-1 ${resending ? "animate-spin" : ""}`} />
                  {resending ? "Sending..." : "Resend"}
                </Button>
              </>
            )}
          </div>
        </div>

        {!assessment.completed_at ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Send className="h-12 w-12 text-amber-500 mx-auto mb-4" />
              <h2 className="text-lg font-medium mb-2">Awaiting Response</h2>
              <p className="text-gray-500 mb-4">
                The assessment was sent on {formatDateTime(assessment.created_at)}.
                The client has not yet completed it.
              </p>
              <div className="flex justify-center gap-2">
                <Button variant="outline" onClick={handleCopyLink}>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy Assessment Link
                </Button>
                <Button variant="outline" onClick={handleResend} disabled={resending}>
                  <RefreshCw className={`h-4 w-4 mr-2 ${resending ? "animate-spin" : ""}`} />
                  {resending ? "Sending..." : "Resend Email"}
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {/* Section 1: Client Context */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Client Context
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {assessment.name_pronouns && (
                  <div>
                    <span className="text-sm text-gray-500">Name & Pronouns</span>
                    <p className="font-medium">{assessment.name_pronouns}</p>
                  </div>
                )}
                {assessment.phone && (
                  <div>
                    <span className="text-sm text-gray-500">Phone</span>
                    <p className="font-medium">{assessment.phone}</p>
                  </div>
                )}
                {assessment.role_title && (
                  <div>
                    <span className="text-sm text-gray-500">Role / Title</span>
                    <p className="font-medium">{assessment.role_title}</p>
                  </div>
                )}
                {assessment.organization_industry && (
                  <div>
                    <span className="text-sm text-gray-500">Organization / Industry</span>
                    <p className="font-medium">{assessment.organization_industry}</p>
                  </div>
                )}
                {assessment.time_in_role && (
                  <div>
                    <span className="text-sm text-gray-500">Time in Role</span>
                    <p className="font-medium">{assessment.time_in_role}</p>
                  </div>
                )}
                {assessment.role_description && (
                  <div>
                    <span className="text-sm text-gray-500">Role Description</span>
                    <p className="text-gray-700 whitespace-pre-wrap">{assessment.role_description}</p>
                  </div>
                )}
                {assessment.coaching_motivations && assessment.coaching_motivations.length > 0 && (
                  <div>
                    <span className="text-sm text-gray-500">Coaching Motivations</span>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {assessment.coaching_motivations.map((m) => (
                        <Badge key={m} variant="outline">
                          {MOTIVATION_LABELS[m] || m}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Section 2: Self Assessment */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart className="h-5 w-5" />
                  Self Assessment
                </CardTitle>
                <CardDescription>Ratings on a scale of 1-10</CardDescription>
              </CardHeader>
              <CardContent className="space-y-1">
                <RatingDisplay value={assessment.confidence_leadership} label="Confidence in leadership abilities" />
                <RatingDisplay value={assessment.feeling_respected} label="Feeling respected and valued" />
                <RatingDisplay value={assessment.clear_goals_short_term} label="Clear short-term goals (6-12 months)" />
                <RatingDisplay value={assessment.clear_goals_long_term} label="Clear long-term vision (3-5 years)" />
                <RatingDisplay value={assessment.work_life_balance} label="Work-life balance" />
                <RatingDisplay value={assessment.stress_management} label="Stress management" />
                <RatingDisplay value={assessment.access_mentors} label="Access to mentors/sponsors" />
                <RatingDisplay value={assessment.navigate_bias} label="Navigating bias and microaggressions" />
                <RatingDisplay value={assessment.communication_effectiveness} label="Communication effectiveness" />
                <RatingDisplay value={assessment.taking_up_space} label="Taking up space, making voice heard" />
                <RatingDisplay value={assessment.team_advocacy} label="Managing and advocating for team" />
                <RatingDisplay value={assessment.career_satisfaction} label="Overall career satisfaction" />

                {assessment.priority_focus_areas && (
                  <div className="pt-4 border-t mt-4">
                    <span className="text-sm text-gray-500">Priority Focus Areas</span>
                    <p className="text-gray-700 whitespace-pre-wrap mt-1">{assessment.priority_focus_areas}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Section 3: Identity & Workplace Experience */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Identity & Workplace Experience
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {assessment.workplace_experience && (
                  <div>
                    <span className="text-sm text-gray-500">Workplace Experience</span>
                    <p className="text-gray-700 whitespace-pre-wrap mt-1">{assessment.workplace_experience}</p>
                  </div>
                )}
                {assessment.self_doubt_patterns && (
                  <div>
                    <span className="text-sm text-gray-500">Where Self-Doubt Shows Up</span>
                    <p className="text-gray-700 whitespace-pre-wrap mt-1">{assessment.self_doubt_patterns}</p>
                  </div>
                )}
                {assessment.habits_to_shift && (
                  <div>
                    <span className="text-sm text-gray-500">Patterns/Habits to Shift</span>
                    <p className="text-gray-700 whitespace-pre-wrap mt-1">{assessment.habits_to_shift}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Section 4: Goals for Coaching */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Goals for Coaching
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {assessment.coaching_goal && (
                  <div>
                    <span className="text-sm text-gray-500">Coaching Goal</span>
                    <p className="text-gray-700 whitespace-pre-wrap mt-1">{assessment.coaching_goal}</p>
                  </div>
                )}
                {assessment.success_evidence && (
                  <div>
                    <span className="text-sm text-gray-500">Evidence of Success</span>
                    <p className="text-gray-700 whitespace-pre-wrap mt-1">{assessment.success_evidence}</p>
                  </div>
                )}
                {assessment.thriving_vision && (
                  <div>
                    <span className="text-sm text-gray-500">Thriving Vision</span>
                    <p className="text-gray-700 whitespace-pre-wrap mt-1">{assessment.thriving_vision}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Section 5: Wellbeing & Support */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Heart className="h-5 w-5" />
                  Wellbeing & Support
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-violet-50 rounded-lg p-4 space-y-1">
                  <span className="text-sm font-medium text-violet-900">Commitment Levels</span>
                  <RatingDisplay value={assessment.commitment_time} label="Time" />
                  <RatingDisplay value={assessment.commitment_energy} label="Energy" />
                  <RatingDisplay value={assessment.commitment_focus} label="Focus" />
                </div>

                {assessment.potential_barriers && (
                  <div>
                    <span className="text-sm text-gray-500">Potential Barriers</span>
                    <p className="text-gray-700 whitespace-pre-wrap mt-1">{assessment.potential_barriers}</p>
                  </div>
                )}
                {assessment.support_needed && (
                  <div>
                    <span className="text-sm text-gray-500">Support Needed</span>
                    <p className="text-gray-700 whitespace-pre-wrap mt-1">{assessment.support_needed}</p>
                  </div>
                )}
                {assessment.feedback_preference && (
                  <div>
                    <span className="text-sm text-gray-500">Feedback Preference</span>
                    <p className="font-medium mt-1">
                      {FEEDBACK_LABELS[assessment.feedback_preference] || assessment.feedback_preference}
                    </p>
                  </div>
                )}
                {assessment.sensitive_topics && (
                  <div>
                    <span className="text-sm text-gray-500">Sensitive Topics to Avoid</span>
                    <p className="text-gray-700 whitespace-pre-wrap mt-1">{assessment.sensitive_topics}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Section 6: Logistics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Logistics & Preferences
                </CardTitle>
              </CardHeader>
              <CardContent>
                {assessment.scheduling_preferences ? (
                  <div>
                    <span className="text-sm text-gray-500">Scheduling Preferences</span>
                    <p className="text-gray-700 whitespace-pre-wrap mt-1">{assessment.scheduling_preferences}</p>
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No scheduling preferences provided</p>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </Shell>
  );
}
