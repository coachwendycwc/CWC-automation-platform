"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi, OnboardingAssessmentResponse } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
  ClipboardCheck,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";

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

export default function ClientOnboardingPage() {
  const router = useRouter();
  const { sessionToken, contact } = useClientAuth();
  const [assessment, setAssessment] = useState<OnboardingAssessmentResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAssessment = async () => {
      if (!sessionToken) return;

      try {
        const data = await clientPortalApi.getOnboardingAssessment(sessionToken);
        setAssessment(data);
      } catch (error: any) {
        console.error("Failed to load assessment:", error);
      } finally {
        setLoading(false);
      }
    };

    loadAssessment();
  }, [sessionToken]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
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
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="flex items-center justify-center py-12">
          <div className="text-gray-500">Loading...</div>
        </div>
      </div>
    );
  }

  // No assessment or not completed - show link to complete it
  if (!assessment || !assessment.completed_at) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">Onboarding Assessment</h1>
            </div>
          </div>

          <Card className="bg-amber-50 border-amber-200">
            <CardContent className="py-8 text-center">
              <ClipboardCheck className="h-12 w-12 text-amber-500 mx-auto mb-4" />
              <h2 className="text-lg font-medium mb-2">Assessment Not Completed</h2>
              <p className="text-gray-600 mb-6 max-w-md mx-auto">
                Please complete your onboarding assessment to help us prepare for your coaching engagement.
                This is required before your first session.
              </p>
              {assessment && assessment.token && (
                <Link href={`/onboarding/${assessment.token}`}>
                  <Button>
                    <ClipboardCheck className="h-4 w-4 mr-2" />
                    Complete Assessment
                  </Button>
                </Link>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">My Onboarding Assessment</h1>
              <p className="text-gray-500">Submitted {formatDate(assessment.completed_at)}</p>
            </div>
          </div>
          <Badge variant="success" className="flex items-center gap-1">
            <CheckCircle className="h-3 w-3" />
            Completed
          </Badge>
        </div>

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
              <CardDescription>Your ratings on a scale of 1-10</CardDescription>
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
                  <span className="text-sm text-gray-500">Sensitive Topics</span>
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
      </div>
    </div>
  );
}
