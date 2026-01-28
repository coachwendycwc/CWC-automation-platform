"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { publicOnboardingApi, OnboardingAssessmentSubmission } from "@/lib/api";
import { CheckCircle, AlertCircle, ChevronRight, ChevronLeft, User, BarChart, MessageSquare, Target, Heart, Calendar } from "lucide-react";

interface AssessmentData {
  contact_name: string;
  already_completed: boolean;
}

// Motivation options for Section 1
const MOTIVATION_OPTIONS = [
  { value: "career_transition", label: "Career transition" },
  { value: "new_role", label: "Getting into a new role/position" },
  { value: "workplace_challenges", label: "Workplace challenges - Race / Gender tensions" },
  { value: "work_life_balance", label: "Work/life balance / well-being concerns" },
  { value: "leadership_step", label: "Desire to take the next leadership step" },
];

// Feedback preference options
const FEEDBACK_PREFERENCE_OPTIONS = [
  { value: "direct", label: "Direct and straightforward" },
  { value: "gentle", label: "Gentle and supportive" },
  { value: "both", label: "A mix of both" },
  { value: "explore", label: "Let's explore together what works best" },
];

export default function OnboardingAssessmentPage() {
  const params = useParams();
  const token = params.token as string;

  const [assessmentData, setAssessmentData] = useState<AssessmentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [currentSection, setCurrentSection] = useState(1);

  // Section 1: Client Context
  const [namePronouns, setNamePronouns] = useState("");
  const [phone, setPhone] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [organizationIndustry, setOrganizationIndustry] = useState("");
  const [timeInRole, setTimeInRole] = useState("");
  const [roleDescription, setRoleDescription] = useState("");
  const [coachingMotivations, setCoachingMotivations] = useState<string[]>([]);

  // Section 2: Self Assessment (1-10 ratings)
  const [confidenceLeadership, setConfidenceLeadership] = useState<number>(0);
  const [feelingRespected, setFeelingRespected] = useState<number>(0);
  const [clearGoalsShortTerm, setClearGoalsShortTerm] = useState<number>(0);
  const [clearGoalsLongTerm, setClearGoalsLongTerm] = useState<number>(0);
  const [workLifeBalance, setWorkLifeBalance] = useState<number>(0);
  const [stressManagement, setStressManagement] = useState<number>(0);
  const [accessMentors, setAccessMentors] = useState<number>(0);
  const [navigateBias, setNavigateBias] = useState<number>(0);
  const [communicationEffectiveness, setCommunicationEffectiveness] = useState<number>(0);
  const [takingUpSpace, setTakingUpSpace] = useState<number>(0);
  const [teamAdvocacy, setTeamAdvocacy] = useState<number>(0);
  const [careerSatisfaction, setCareerSatisfaction] = useState<number>(0);
  const [priorityFocusAreas, setPriorityFocusAreas] = useState("");

  // Section 3: Identity & Workplace Experience
  const [workplaceExperience, setWorkplaceExperience] = useState("");
  const [selfDoubtPatterns, setSelfDoubtPatterns] = useState("");
  const [habitsToShift, setHabitsToShift] = useState("");

  // Section 4: Goals for Coaching
  const [coachingGoal, setCoachingGoal] = useState("");
  const [successEvidence, setSuccessEvidence] = useState("");
  const [thrivingVision, setThrivingVision] = useState("");

  // Section 5: Wellbeing & Support
  const [commitmentTime, setCommitmentTime] = useState<number>(0);
  const [commitmentEnergy, setCommitmentEnergy] = useState<number>(0);
  const [commitmentFocus, setCommitmentFocus] = useState<number>(0);
  const [potentialBarriers, setPotentialBarriers] = useState("");
  const [supportNeeded, setSupportNeeded] = useState("");
  const [feedbackPreference, setFeedbackPreference] = useState("");
  const [sensitiveTopics, setSensitiveTopics] = useState("");

  // Section 6: Logistics
  const [schedulingPreferences, setSchedulingPreferences] = useState("");

  useEffect(() => {
    if (token) {
      loadAssessment();
    }
  }, [token]);

  const loadAssessment = async () => {
    try {
      const data = await publicOnboardingApi.getAssessment(token);
      setAssessmentData(data);
      if (data.already_completed) {
        setSubmitted(true);
      }
    } catch (err: any) {
      setError(err.message || "Assessment not found or has expired");
    } finally {
      setLoading(false);
    }
  };

  const toggleMotivation = (value: string) => {
    setCoachingMotivations(prev =>
      prev.includes(value)
        ? prev.filter(v => v !== value)
        : [...prev, value]
    );
  };

  const canProceed = () => {
    switch (currentSection) {
      case 1:
        return namePronouns.trim().length > 0;
      case 2:
      case 3:
      case 4:
      case 5:
      case 6:
        return true;
      default:
        return true;
    }
  };

  const handleSubmit = async () => {
    if (!namePronouns.trim()) {
      alert("Please enter your name and pronouns");
      return;
    }

    setSubmitting(true);
    try {
      const submission: OnboardingAssessmentSubmission = {
        // Section 1
        name_pronouns: namePronouns,
        phone: phone || undefined,
        role_title: roleTitle || undefined,
        organization_industry: organizationIndustry || undefined,
        time_in_role: timeInRole || undefined,
        role_description: roleDescription || undefined,
        coaching_motivations: coachingMotivations.length > 0 ? coachingMotivations : undefined,
        // Section 2
        confidence_leadership: confidenceLeadership > 0 ? confidenceLeadership : undefined,
        feeling_respected: feelingRespected > 0 ? feelingRespected : undefined,
        clear_goals_short_term: clearGoalsShortTerm > 0 ? clearGoalsShortTerm : undefined,
        clear_goals_long_term: clearGoalsLongTerm > 0 ? clearGoalsLongTerm : undefined,
        work_life_balance: workLifeBalance > 0 ? workLifeBalance : undefined,
        stress_management: stressManagement > 0 ? stressManagement : undefined,
        access_mentors: accessMentors > 0 ? accessMentors : undefined,
        navigate_bias: navigateBias > 0 ? navigateBias : undefined,
        communication_effectiveness: communicationEffectiveness > 0 ? communicationEffectiveness : undefined,
        taking_up_space: takingUpSpace > 0 ? takingUpSpace : undefined,
        team_advocacy: teamAdvocacy > 0 ? teamAdvocacy : undefined,
        career_satisfaction: careerSatisfaction > 0 ? careerSatisfaction : undefined,
        priority_focus_areas: priorityFocusAreas || undefined,
        // Section 3
        workplace_experience: workplaceExperience || undefined,
        self_doubt_patterns: selfDoubtPatterns || undefined,
        habits_to_shift: habitsToShift || undefined,
        // Section 4
        coaching_goal: coachingGoal || undefined,
        success_evidence: successEvidence || undefined,
        thriving_vision: thrivingVision || undefined,
        // Section 5
        commitment_time: commitmentTime > 0 ? commitmentTime : undefined,
        commitment_energy: commitmentEnergy > 0 ? commitmentEnergy : undefined,
        commitment_focus: commitmentFocus > 0 ? commitmentFocus : undefined,
        potential_barriers: potentialBarriers || undefined,
        support_needed: supportNeeded || undefined,
        feedback_preference: feedbackPreference || undefined,
        sensitive_topics: sensitiveTopics || undefined,
        // Section 6
        scheduling_preferences: schedulingPreferences || undefined,
      };

      await publicOnboardingApi.submitAssessment(token, submission);
      setSubmitted(true);
    } catch (err: any) {
      alert(err.message || "Failed to submit assessment");
    } finally {
      setSubmitting(false);
    }
  };

  // Rating scale component
  const RatingScale = ({
    value,
    onChange,
    lowLabel = "Low",
    highLabel = "High"
  }: {
    value: number;
    onChange: (v: number) => void;
    lowLabel?: string;
    highLabel?: string;
  }) => (
    <div>
      <div className="flex flex-wrap gap-2">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((rating) => (
          <button
            key={rating}
            type="button"
            onClick={() => onChange(rating)}
            className={`w-10 h-10 rounded-lg border-2 font-medium transition-all ${
              value === rating
                ? "border-violet-500 bg-violet-50 text-violet-600"
                : "border-gray-200 hover:border-gray-300"
            }`}
          >
            {rating}
          </button>
        ))}
      </div>
      <div className="flex justify-between text-xs text-gray-400 mt-1 px-1">
        <span>{lowLabel}</span>
        <span>{highLabel}</span>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Assessment Not Available</h2>
            <p className="text-gray-500">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Thank You!</h2>
            <p className="text-gray-500">
              Your onboarding assessment has been submitted. This helps us tailor your coaching experience to your unique needs and goals. Looking forward to our work together!
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const totalSections = 6;
  const sectionIcons = [User, BarChart, MessageSquare, Target, Heart, Calendar];
  const sectionTitles = [
    "Client Context",
    "Self Assessment",
    "Identity & Workplace",
    "Goals for Coaching",
    "Wellbeing & Support",
    "Logistics"
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
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
          <h1 className="text-2xl font-bold mb-2">Onboarding Assessment</h1>
          <p className="text-gray-500">
            Welcome, {assessmentData?.contact_name}! Please complete this assessment to help us prepare for our coaching engagement.
          </p>
          <p className="text-sm text-gray-400 mt-2">This should take about 10-15 minutes.</p>
        </div>

        {/* Progress indicator */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-500 mb-2">
            <span>Section {currentSection} of {totalSections}: {sectionTitles[currentSection - 1]}</span>
            <span>{Math.round((currentSection / totalSections) * 100)}% complete</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-violet-600 transition-all duration-300"
              style={{ width: `${(currentSection / totalSections) * 100}%` }}
            />
          </div>
          {/* Section dots */}
          <div className="flex justify-between mt-4">
            {sectionIcons.map((Icon, index) => (
              <button
                key={index}
                onClick={() => setCurrentSection(index + 1)}
                className={`flex flex-col items-center gap-1 ${
                  currentSection === index + 1
                    ? "text-violet-600"
                    : currentSection > index + 1
                      ? "text-green-500"
                      : "text-gray-300"
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  currentSection === index + 1
                    ? "bg-violet-100 border-2 border-violet-600"
                    : currentSection > index + 1
                      ? "bg-green-100 border-2 border-green-500"
                      : "bg-gray-100 border-2 border-gray-200"
                }`}>
                  <Icon className="h-4 w-4" />
                </div>
              </button>
            ))}
          </div>
        </div>

        <Card>
          <CardContent className="pt-6 space-y-6">
            {/* Section 1: Client Context */}
            {currentSection === 1 && (
              <>
                <CardHeader className="px-0 pt-0">
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Client Context
                  </CardTitle>
                  <CardDescription>Tell us about yourself and what brings you to coaching</CardDescription>
                </CardHeader>

                <div>
                  <Label htmlFor="namePronouns" className="text-base font-medium">
                    Name & Pronouns *
                  </Label>
                  <Input
                    id="namePronouns"
                    value={namePronouns}
                    onChange={(e) => setNamePronouns(e.target.value)}
                    placeholder="e.g., Sarah Chen (she/her)"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="phone" className="text-base font-medium">
                    Phone Number
                  </Label>
                  <Input
                    id="phone"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="e.g., (555) 123-4567"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="roleTitle" className="text-base font-medium">
                    Role / Title
                  </Label>
                  <Input
                    id="roleTitle"
                    value={roleTitle}
                    onChange={(e) => setRoleTitle(e.target.value)}
                    placeholder="e.g., Senior Product Manager"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="organizationIndustry" className="text-base font-medium">
                    Organization / Industry
                  </Label>
                  <Input
                    id="organizationIndustry"
                    value={organizationIndustry}
                    onChange={(e) => setOrganizationIndustry(e.target.value)}
                    placeholder="e.g., Tech startup / Financial services"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="timeInRole" className="text-base font-medium">
                    How long have you been in your current role?
                  </Label>
                  <Input
                    id="timeInRole"
                    value={timeInRole}
                    onChange={(e) => setTimeInRole(e.target.value)}
                    placeholder="e.g., 2 years"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="roleDescription" className="text-base font-medium">
                    Describe your current role and responsibilities
                  </Label>
                  <Textarea
                    id="roleDescription"
                    value={roleDescription}
                    onChange={(e) => setRoleDescription(e.target.value)}
                    placeholder="What does your day-to-day look like? What are you responsible for?"
                    rows={3}
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label className="text-base font-medium">
                    What motivated you to seek coaching? (Check all that apply)
                  </Label>
                  <div className="mt-3 space-y-3">
                    {MOTIVATION_OPTIONS.map((option) => (
                      <label key={option.value} className="flex items-center gap-3 cursor-pointer">
                        <Checkbox
                          checked={coachingMotivations.includes(option.value)}
                          onCheckedChange={() => toggleMotivation(option.value)}
                        />
                        <span className="text-sm">{option.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Section 2: Self Assessment */}
            {currentSection === 2 && (
              <>
                <CardHeader className="px-0 pt-0">
                  <CardTitle className="flex items-center gap-2">
                    <BarChart className="h-5 w-5" />
                    Self Assessment
                  </CardTitle>
                  <CardDescription>Rate yourself on a scale of 1-10 for each area</CardDescription>
                </CardHeader>

                <div>
                  <Label className="text-base font-medium">
                    Confidence in my leadership abilities
                  </Label>
                  <div className="mt-2">
                    <RatingScale value={confidenceLeadership} onChange={setConfidenceLeadership} />
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">
                    Feeling respected and valued in my organization
                  </Label>
                  <div className="mt-2">
                    <RatingScale value={feelingRespected} onChange={setFeelingRespected} />
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">
                    Clear professional/career goals (6-12 months)
                  </Label>
                  <div className="mt-2">
                    <RatingScale value={clearGoalsShortTerm} onChange={setClearGoalsShortTerm} />
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">
                    Clarity on long-term career vision (3-5 years)
                  </Label>
                  <div className="mt-2">
                    <RatingScale value={clearGoalsLongTerm} onChange={setClearGoalsLongTerm} />
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">
                    Healthy balance between work and personal life
                  </Label>
                  <div className="mt-2">
                    <RatingScale value={workLifeBalance} onChange={setWorkLifeBalance} />
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">
                    Managing stress in a way that supports well-being
                  </Label>
                  <div className="mt-2">
                    <RatingScale value={stressManagement} onChange={setStressManagement} />
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">
                    Access to mentors and sponsors for career growth
                  </Label>
                  <div className="mt-2">
                    <RatingScale value={accessMentors} onChange={setAccessMentors} />
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">
                    Equipped to navigate bias, microaggressions, inequitable dynamics
                  </Label>
                  <div className="mt-2">
                    <RatingScale value={navigateBias} onChange={setNavigateBias} />
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">
                    Communicating effectively in the workplace
                  </Label>
                  <div className="mt-2">
                    <RatingScale value={communicationEffectiveness} onChange={setCommunicationEffectiveness} />
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">
                    Confidence taking up space and making my voice heard
                  </Label>
                  <div className="mt-2">
                    <RatingScale value={takingUpSpace} onChange={setTakingUpSpace} />
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">
                    Confidence managing and advocating for my team
                  </Label>
                  <div className="mt-2">
                    <RatingScale value={teamAdvocacy} onChange={setTeamAdvocacy} />
                  </div>
                </div>

                <div>
                  <Label className="text-base font-medium">
                    Overall satisfaction with my career right now
                  </Label>
                  <div className="mt-2">
                    <RatingScale value={careerSatisfaction} onChange={setCareerSatisfaction} />
                  </div>
                </div>

                <div>
                  <Label htmlFor="priorityFocusAreas" className="text-base font-medium">
                    Which 2-3 areas feel most important to focus on in coaching?
                  </Label>
                  <Textarea
                    id="priorityFocusAreas"
                    value={priorityFocusAreas}
                    onChange={(e) => setPriorityFocusAreas(e.target.value)}
                    placeholder="Based on your ratings above, what areas would you most like to work on?"
                    rows={3}
                    className="mt-2"
                  />
                </div>
              </>
            )}

            {/* Section 3: Identity & Workplace Experience */}
            {currentSection === 3 && (
              <>
                <CardHeader className="px-0 pt-0">
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Identity & Workplace Experience
                  </CardTitle>
                  <CardDescription>Help us understand your workplace context</CardDescription>
                </CardHeader>

                <div>
                  <Label htmlFor="workplaceExperience" className="text-base font-medium">
                    Describe your experience in your current workplace. Does it feel supportive? Challenging? Both?
                  </Label>
                  <Textarea
                    id="workplaceExperience"
                    value={workplaceExperience}
                    onChange={(e) => setWorkplaceExperience(e.target.value)}
                    placeholder="Share what your workplace environment is like..."
                    rows={4}
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="selfDoubtPatterns" className="text-base font-medium">
                    Where does self-doubt or second-guessing show up most for you?
                  </Label>
                  <Textarea
                    id="selfDoubtPatterns"
                    value={selfDoubtPatterns}
                    onChange={(e) => setSelfDoubtPatterns(e.target.value)}
                    placeholder="In meetings? When speaking up? With certain people?"
                    rows={4}
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="habitsToShift" className="text-base font-medium">
                    What 2-3 patterns or habits would you like to shift?
                  </Label>
                  <Textarea
                    id="habitsToShift"
                    value={habitsToShift}
                    onChange={(e) => setHabitsToShift(e.target.value)}
                    placeholder="What behaviors or thought patterns are holding you back?"
                    rows={4}
                    className="mt-2"
                  />
                </div>
              </>
            )}

            {/* Section 4: Goals for Coaching */}
            {currentSection === 4 && (
              <>
                <CardHeader className="px-0 pt-0">
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    Goals for Coaching
                  </CardTitle>
                  <CardDescription>What do you want to achieve through coaching?</CardDescription>
                </CardHeader>

                <div>
                  <Label htmlFor="coachingGoal" className="text-base font-medium">
                    What is your coaching goal for this engagement?
                  </Label>
                  <Textarea
                    id="coachingGoal"
                    value={coachingGoal}
                    onChange={(e) => setCoachingGoal(e.target.value)}
                    placeholder="What do you most want to accomplish or change?"
                    rows={4}
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="successEvidence" className="text-base font-medium">
                    What would tangible evidence of success look like?
                  </Label>
                  <Textarea
                    id="successEvidence"
                    value={successEvidence}
                    onChange={(e) => setSuccessEvidence(e.target.value)}
                    placeholder="How would you know coaching worked? What would be different?"
                    rows={4}
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="thrivingVision" className="text-base font-medium">
                    If you were THRIVING at the end of this engagement, what would be different?
                  </Label>
                  <Textarea
                    id="thrivingVision"
                    value={thrivingVision}
                    onChange={(e) => setThrivingVision(e.target.value)}
                    placeholder="Paint a picture of your ideal future self..."
                    rows={4}
                    className="mt-2"
                  />
                </div>
              </>
            )}

            {/* Section 5: Wellbeing & Support */}
            {currentSection === 5 && (
              <>
                <CardHeader className="px-0 pt-0">
                  <CardTitle className="flex items-center gap-2">
                    <Heart className="h-5 w-5" />
                    Wellbeing & Support
                  </CardTitle>
                  <CardDescription>How can we best support you?</CardDescription>
                </CardHeader>

                <div className="p-4 bg-violet-50 rounded-lg border border-violet-100">
                  <Label className="text-base font-medium text-violet-900">
                    On a scale of 1-10, what's your current commitment level?
                  </Label>
                  <p className="text-sm text-violet-700 mt-1 mb-4">
                    Coaching works best when there's genuine commitment to the process.
                  </p>

                  <div className="space-y-4">
                    <div>
                      <Label className="text-sm font-medium mb-2 block">Time</Label>
                      <RatingScale value={commitmentTime} onChange={setCommitmentTime} />
                    </div>
                    <div>
                      <Label className="text-sm font-medium mb-2 block">Energy</Label>
                      <RatingScale value={commitmentEnergy} onChange={setCommitmentEnergy} />
                    </div>
                    <div>
                      <Label className="text-sm font-medium mb-2 block">Focus</Label>
                      <RatingScale value={commitmentFocus} onChange={setCommitmentFocus} />
                    </div>
                  </div>
                </div>

                <div>
                  <Label htmlFor="potentialBarriers" className="text-base font-medium">
                    What might get in the way of fully engaging in coaching?
                  </Label>
                  <Textarea
                    id="potentialBarriers"
                    value={potentialBarriers}
                    onChange={(e) => setPotentialBarriers(e.target.value)}
                    placeholder="Work demands, personal obligations, energy levels..."
                    rows={3}
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="supportNeeded" className="text-base font-medium">
                    What support or accountability do you need from your coach?
                  </Label>
                  <Textarea
                    id="supportNeeded"
                    value={supportNeeded}
                    onChange={(e) => setSupportNeeded(e.target.value)}
                    placeholder="What helps you stay on track and engaged?"
                    rows={3}
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label className="text-base font-medium">
                    How do you prefer to receive feedback?
                  </Label>
                  <RadioGroup
                    value={feedbackPreference}
                    onValueChange={setFeedbackPreference}
                    className="mt-3 space-y-2"
                  >
                    {FEEDBACK_PREFERENCE_OPTIONS.map((option) => (
                      <div key={option.value} className="flex items-center gap-3">
                        <RadioGroupItem value={option.value} id={`feedback_${option.value}`} />
                        <Label htmlFor={`feedback_${option.value}`} className="font-normal cursor-pointer">
                          {option.label}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>

                <div>
                  <Label htmlFor="sensitiveTopics" className="text-base font-medium">
                    Are there any sensitive topics you'd prefer we avoid pushing on?
                  </Label>
                  <Textarea
                    id="sensitiveTopics"
                    value={sensitiveTopics}
                    onChange={(e) => setSensitiveTopics(e.target.value)}
                    placeholder="This is optional - share only what feels comfortable"
                    rows={2}
                    className="mt-2"
                  />
                </div>
              </>
            )}

            {/* Section 6: Logistics */}
            {currentSection === 6 && (
              <>
                <CardHeader className="px-0 pt-0">
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    Logistics & Preferences
                  </CardTitle>
                  <CardDescription>Help us schedule our sessions</CardDescription>
                </CardHeader>

                <div>
                  <Label htmlFor="schedulingPreferences" className="text-base font-medium">
                    What are your best days/times for sessions? Any constraints we should know about?
                  </Label>
                  <Textarea
                    id="schedulingPreferences"
                    value={schedulingPreferences}
                    onChange={(e) => setSchedulingPreferences(e.target.value)}
                    placeholder="e.g., Tuesdays and Thursdays after 2pm EST work best. I have a standing meeting on Wednesdays..."
                    rows={4}
                    className="mt-2"
                  />
                </div>

                <div className="p-4 bg-green-50 rounded-lg border border-green-100">
                  <p className="text-sm text-green-800">
                    Thank you for taking the time to complete this assessment. Your thoughtful responses help ensure our coaching engagement is tailored specifically to your needs and goals.
                  </p>
                </div>
              </>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-4 border-t">
              {currentSection > 1 ? (
                <Button
                  variant="outline"
                  onClick={() => setCurrentSection(currentSection - 1)}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
              ) : (
                <div />
              )}

              {currentSection < totalSections ? (
                <Button
                  onClick={() => setCurrentSection(currentSection + 1)}
                  disabled={!canProceed()}
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={submitting || !canProceed()}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {submitting ? "Submitting..." : "Submit Assessment"}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-gray-500 mt-4">
          Your responses are confidential and will only be used to support your coaching journey.
        </p>
      </div>
    </div>
  );
}
