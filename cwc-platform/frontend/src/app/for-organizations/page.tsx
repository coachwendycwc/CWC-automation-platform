"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// Form options
const areasOfInterest = [
  { value: "executive_coaching", label: "Executive Coaching for Leaders (1:1)" },
  { value: "group_coaching", label: "Group Coaching for Leaders / Cohorts" },
  { value: "keynote_speaking", label: "Keynote Speaking" },
  { value: "webinars_workshops", label: "Customized Webinars & Workshops" },
  { value: "virtual_series", label: "Multi-Session Virtual Series" },
  { value: "other", label: "Other" },
];

const desiredOutcomes = [
  { value: "executive_presence", label: "Strengthen executive presence and leadership effectiveness" },
  { value: "communication_collaboration", label: "Improve communication and collaboration" },
  { value: "psychological_safety", label: "Build psychological safety and trust" },
  { value: "navigating_bias", label: "Support leaders navigating bias and double standards" },
  { value: "retention_engagement", label: "Increase retention and engagement of women of color" },
  { value: "inclusive_leadership", label: "Develop inclusive leadership practices across managers/leaders" },
  { value: "team_reset", label: "Team reset after conflict, change, or reorg" },
  { value: "other", label: "Other" },
];

const primaryAudienceOptions = [
  { value: "senior_leaders", label: "Senior leaders / executives" },
  { value: "mid_level_managers", label: "Mid-level managers" },
  { value: "high_potential", label: "High-potential talent" },
  { value: "specific_team", label: "A specific team" },
  { value: "erg_affinity", label: "ERG / affinity group" },
  { value: "organization_wide", label: "Organization-wide" },
  { value: "other", label: "Other" },
];

const participantCounts = ["1-5", "6-15", "16-30", "31-50", "51-100", "100+"];

const formatOptions = [
  { value: "virtual", label: "Virtual" },
  { value: "in_person", label: "In-person" },
  { value: "hybrid", label: "Hybrid" },
  { value: "not_sure", label: "Not sure yet" },
];

const budgetRanges = [
  { value: "under_5k", label: "Under $5,000" },
  { value: "5k_10k", label: "$5,000–$9,999" },
  { value: "10k_20k", label: "$10,000–$19,999" },
  { value: "20k_40k", label: "$20,000–$39,999" },
  { value: "40k_plus", label: "$40,000+" },
  { value: "not_sure", label: "Not sure yet / need guidance" },
];

const timelineOptions = [
  { value: "asap", label: "ASAP (within 2–4 weeks)" },
  { value: "1_2_months", label: "1–2 months" },
  { value: "3_4_months", label: "3–4 months" },
  { value: "5_plus_months", label: "5+ months" },
  { value: "not_sure", label: "Not sure yet" },
];

const decisionMakerOptions = [
  { value: "self", label: "I'm the decision maker" },
  { value: "hr", label: "HR / People Team" },
  { value: "ld_talent", label: "L&D / Talent Development" },
  { value: "dei", label: "DEI / Inclusion" },
  { value: "executive", label: "Executive leadership" },
  { value: "procurement", label: "Procurement" },
  { value: "other", label: "Other" },
];

const decisionStageOptions = [
  { value: "exploring", label: "Exploring options" },
  { value: "comparing", label: "Comparing vendors" },
  { value: "ready_to_select", label: "Ready to select a partner soon" },
  { value: "need_approval", label: "Need internal approval" },
  { value: "other", label: "Other" },
];

interface FormData {
  full_name: string;
  title_role: string;
  organization_name: string;
  work_email: string;
  phone_number: string;
  organization_website: string;
  areas_of_interest: string[];
  areas_of_interest_other: string;
  desired_outcomes: string[];
  desired_outcomes_other: string;
  current_challenge: string;
  primary_audience: string[];
  primary_audience_other: string;
  participant_count: string;
  preferred_format: string;
  location: string;
  budget_range: string;
  specific_budget: string;
  ideal_timeline: string;
  specific_date: string;
  decision_makers: string[];
  decision_makers_other: string;
  decision_stage: string;
  decision_stage_other: string;
  success_definition: string;
  accessibility_needs: string;
}

export default function ForOrganizationsPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentSection, setCurrentSection] = useState(1);

  const [formData, setFormData] = useState<FormData>({
    full_name: "",
    title_role: "",
    organization_name: "",
    work_email: "",
    phone_number: "",
    organization_website: "",
    areas_of_interest: [],
    areas_of_interest_other: "",
    desired_outcomes: [],
    desired_outcomes_other: "",
    current_challenge: "",
    primary_audience: [],
    primary_audience_other: "",
    participant_count: "",
    preferred_format: "",
    location: "",
    budget_range: "",
    specific_budget: "",
    ideal_timeline: "",
    specific_date: "",
    decision_makers: [],
    decision_makers_other: "",
    decision_stage: "",
    decision_stage_other: "",
    success_definition: "",
    accessibility_needs: "",
  });

  const updateField = (field: keyof FormData, value: string | string[]) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleArrayField = (field: keyof FormData, value: string) => {
    const current = formData[field] as string[];
    if (current.includes(value)) {
      updateField(field, current.filter((v) => v !== value));
    } else {
      updateField(field, [...current, value]);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/assessments/organizations/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to submit assessment");
      }

      const data = await response.json();

      // Redirect to booking page with assessment ID
      if (data.booking_url) {
        router.push(data.booking_url);
      } else {
        router.push("/for-organizations/thank-you");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  const canProceed = () => {
    switch (currentSection) {
      case 1:
        return (
          formData.full_name.trim() !== "" &&
          formData.title_role.trim() !== "" &&
          formData.organization_name.trim() !== "" &&
          formData.work_email.includes("@")
        );
      case 2:
        return formData.areas_of_interest.length > 0;
      case 3:
        return true; // Optional section
      case 4:
        return true; // Optional section
      case 5:
        return true; // Optional section
      case 6:
        return true; // Optional section
      default:
        return true;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Coaching Women of Color, LLC
          </h1>
          <p className="text-gray-600 mt-1">Organizational Needs Assessment</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="max-w-4xl mx-auto px-4 py-4">
        <div className="flex items-center gap-2">
          {[1, 2, 3, 4, 5, 6].map((section) => (
            <div
              key={section}
              className={`flex-1 h-2 rounded-full ${
                section <= currentSection ? "bg-purple-600" : "bg-gray-200"
              }`}
            />
          ))}
        </div>
        <p className="text-sm text-gray-500 mt-2">
          Section {currentSection} of 6
        </p>
      </div>

      {/* Form Content */}
      <div className="max-w-4xl mx-auto px-4 pb-12">
        <Card>
          <CardHeader>
            <CardDescription className="text-base">
              Thank you for your interest in partnering with Coaching Women of Color, LLC (CWC).
              This short needs assessment helps us understand your goals, timeline, and what support
              will be most impactful. After you complete this questionnaire, please book a discovery
              call so we can review your responses and co-create the best solution.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-8">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            {/* Section 1: Contact Information */}
            {currentSection === 1 && (
              <div className="space-y-6">
                <CardTitle>1) Contact Information</CardTitle>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="full_name">Full name *</Label>
                    <Input
                      id="full_name"
                      value={formData.full_name}
                      onChange={(e) => updateField("full_name", e.target.value)}
                      placeholder="Your full name"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="title_role">Title/Role *</Label>
                    <Input
                      id="title_role"
                      value={formData.title_role}
                      onChange={(e) => updateField("title_role", e.target.value)}
                      placeholder="Your job title"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="organization_name">Organization name *</Label>
                    <Input
                      id="organization_name"
                      value={formData.organization_name}
                      onChange={(e) => updateField("organization_name", e.target.value)}
                      placeholder="Your organization"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="work_email">Work email *</Label>
                    <Input
                      id="work_email"
                      type="email"
                      value={formData.work_email}
                      onChange={(e) => updateField("work_email", e.target.value)}
                      placeholder="you@company.com"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone_number">Phone number (optional)</Label>
                    <Input
                      id="phone_number"
                      value={formData.phone_number}
                      onChange={(e) => updateField("phone_number", e.target.value)}
                      placeholder="(555) 123-4567"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="organization_website">Organization website (optional)</Label>
                    <Input
                      id="organization_website"
                      value={formData.organization_website}
                      onChange={(e) => updateField("organization_website", e.target.value)}
                      placeholder="https://yourcompany.com"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Section 2: Areas of Interest */}
            {currentSection === 2 && (
              <div className="space-y-6">
                <CardTitle>2) Areas of Interest</CardTitle>
                <p className="text-gray-600">What are you interested in working with CWC on? (Select all that apply)</p>

                <div className="space-y-3">
                  {areasOfInterest.map((area) => (
                    <div key={area.value} className="flex items-center space-x-3">
                      <Checkbox
                        id={`area-${area.value}`}
                        checked={formData.areas_of_interest.includes(area.value)}
                        onCheckedChange={() => toggleArrayField("areas_of_interest", area.value)}
                      />
                      <Label htmlFor={`area-${area.value}`} className="cursor-pointer">
                        {area.label}
                      </Label>
                    </div>
                  ))}
                </div>

                {formData.areas_of_interest.includes("other") && (
                  <div className="space-y-2">
                    <Label htmlFor="areas_other">Please describe what you're looking for:</Label>
                    <Textarea
                      id="areas_other"
                      value={formData.areas_of_interest_other}
                      onChange={(e) => updateField("areas_of_interest_other", e.target.value)}
                      placeholder="Describe your needs..."
                    />
                  </div>
                )}
              </div>
            )}

            {/* Section 3: Goals and Needs */}
            {currentSection === 3 && (
              <div className="space-y-6">
                <CardTitle>3) Goals and Needs</CardTitle>

                <div className="space-y-4">
                  <p className="text-gray-600">What outcomes are you hoping to achieve? (Select up to 3)</p>
                  <div className="space-y-3">
                    {desiredOutcomes.map((outcome) => (
                      <div key={outcome.value} className="flex items-center space-x-3">
                        <Checkbox
                          id={`outcome-${outcome.value}`}
                          checked={formData.desired_outcomes.includes(outcome.value)}
                          onCheckedChange={() => toggleArrayField("desired_outcomes", outcome.value)}
                          disabled={
                            formData.desired_outcomes.length >= 3 &&
                            !formData.desired_outcomes.includes(outcome.value)
                          }
                        />
                        <Label htmlFor={`outcome-${outcome.value}`} className="cursor-pointer">
                          {outcome.label}
                        </Label>
                      </div>
                    ))}
                  </div>

                  {formData.desired_outcomes.includes("other") && (
                    <div className="space-y-2">
                      <Label htmlFor="outcomes_other">Please specify:</Label>
                      <Input
                        id="outcomes_other"
                        value={formData.desired_outcomes_other}
                        onChange={(e) => updateField("desired_outcomes_other", e.target.value)}
                      />
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="current_challenge">
                    Briefly describe the challenge you're trying to solve right now:
                  </Label>
                  <Textarea
                    id="current_challenge"
                    value={formData.current_challenge}
                    onChange={(e) => updateField("current_challenge", e.target.value)}
                    placeholder="What's the main challenge you're facing?"
                    rows={4}
                  />
                </div>

                <div className="space-y-4">
                  <p className="text-gray-600">Who is the primary audience for this work?</p>
                  <div className="space-y-3">
                    {primaryAudienceOptions.map((audience) => (
                      <div key={audience.value} className="flex items-center space-x-3">
                        <Checkbox
                          id={`audience-${audience.value}`}
                          checked={formData.primary_audience.includes(audience.value)}
                          onCheckedChange={() => toggleArrayField("primary_audience", audience.value)}
                        />
                        <Label htmlFor={`audience-${audience.value}`} className="cursor-pointer">
                          {audience.label}
                        </Label>
                      </div>
                    ))}
                  </div>

                  {formData.primary_audience.includes("other") && (
                    <div className="space-y-2">
                      <Label htmlFor="audience_other">Please specify:</Label>
                      <Input
                        id="audience_other"
                        value={formData.primary_audience_other}
                        onChange={(e) => updateField("primary_audience_other", e.target.value)}
                      />
                    </div>
                  )}
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Estimated number of participants:</Label>
                    <Select
                      value={formData.participant_count}
                      onValueChange={(value) => updateField("participant_count", value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select range" />
                      </SelectTrigger>
                      <SelectContent>
                        {participantCounts.map((count) => (
                          <SelectItem key={count} value={count}>
                            {count}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>What format do you prefer?</Label>
                    <Select
                      value={formData.preferred_format}
                      onValueChange={(value) => updateField("preferred_format", value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select format" />
                      </SelectTrigger>
                      <SelectContent>
                        {formatOptions.map((format) => (
                          <SelectItem key={format.value} value={format.value}>
                            {format.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {(formData.preferred_format === "in_person" || formData.preferred_format === "hybrid") && (
                  <div className="space-y-2">
                    <Label htmlFor="location">Where are you located? (City + State)</Label>
                    <Input
                      id="location"
                      value={formData.location}
                      onChange={(e) => updateField("location", e.target.value)}
                      placeholder="e.g., Atlanta, GA"
                    />
                  </div>
                )}
              </div>
            )}

            {/* Section 4: Budget and Timeline */}
            {currentSection === 4 && (
              <div className="space-y-6">
                <CardTitle>4) Budget and Timeline</CardTitle>

                <div className="space-y-4">
                  <Label>What budget range have you allocated for this project?</Label>
                  <RadioGroup
                    value={formData.budget_range}
                    onValueChange={(value) => updateField("budget_range", value)}
                    className="space-y-2"
                  >
                    {budgetRanges.map((budget) => (
                      <div key={budget.value} className="flex items-center space-x-3">
                        <RadioGroupItem value={budget.value} id={`budget-${budget.value}`} />
                        <Label htmlFor={`budget-${budget.value}`} className="cursor-pointer">
                          {budget.label}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="specific_budget">
                    If you have a specific budget amount or cap, share it here (optional):
                  </Label>
                  <Input
                    id="specific_budget"
                    value={formData.specific_budget}
                    onChange={(e) => updateField("specific_budget", e.target.value)}
                    placeholder="e.g., $15,000"
                  />
                </div>

                <div className="space-y-4">
                  <Label>What is your ideal start timeline?</Label>
                  <RadioGroup
                    value={formData.ideal_timeline}
                    onValueChange={(value) => updateField("ideal_timeline", value)}
                    className="space-y-2"
                  >
                    {timelineOptions.map((timeline) => (
                      <div key={timeline.value} className="flex items-center space-x-3">
                        <RadioGroupItem value={timeline.value} id={`timeline-${timeline.value}`} />
                        <Label htmlFor={`timeline-${timeline.value}`} className="cursor-pointer">
                          {timeline.label}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="specific_date">
                    Is there a specific date or event this is tied to? (optional)
                  </Label>
                  <Input
                    id="specific_date"
                    value={formData.specific_date}
                    onChange={(e) => updateField("specific_date", e.target.value)}
                    placeholder="e.g., Annual leadership retreat on March 15"
                  />
                </div>
              </div>
            )}

            {/* Section 5: Decision Process */}
            {currentSection === 5 && (
              <div className="space-y-6">
                <CardTitle>5) Decision Process</CardTitle>

                <div className="space-y-4">
                  <p className="text-gray-600">Who will be involved in approving this engagement? (Select all that apply)</p>
                  <div className="space-y-3">
                    {decisionMakerOptions.map((dm) => (
                      <div key={dm.value} className="flex items-center space-x-3">
                        <Checkbox
                          id={`dm-${dm.value}`}
                          checked={formData.decision_makers.includes(dm.value)}
                          onCheckedChange={() => toggleArrayField("decision_makers", dm.value)}
                        />
                        <Label htmlFor={`dm-${dm.value}`} className="cursor-pointer">
                          {dm.label}
                        </Label>
                      </div>
                    ))}
                  </div>

                  {formData.decision_makers.includes("other") && (
                    <div className="space-y-2">
                      <Label htmlFor="dm_other">Please specify:</Label>
                      <Input
                        id="dm_other"
                        value={formData.decision_makers_other}
                        onChange={(e) => updateField("decision_makers_other", e.target.value)}
                      />
                    </div>
                  )}
                </div>

                <div className="space-y-4">
                  <Label>Where are you in the decision process?</Label>
                  <RadioGroup
                    value={formData.decision_stage}
                    onValueChange={(value) => updateField("decision_stage", value)}
                    className="space-y-2"
                  >
                    {decisionStageOptions.map((stage) => (
                      <div key={stage.value} className="flex items-center space-x-3">
                        <RadioGroupItem value={stage.value} id={`stage-${stage.value}`} />
                        <Label htmlFor={`stage-${stage.value}`} className="cursor-pointer">
                          {stage.label}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>

                  {formData.decision_stage === "other" && (
                    <div className="space-y-2">
                      <Label htmlFor="stage_other">Please specify:</Label>
                      <Input
                        id="stage_other"
                        value={formData.decision_stage_other}
                        onChange={(e) => updateField("decision_stage_other", e.target.value)}
                      />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Section 6: Additional Context */}
            {currentSection === 6 && (
              <div className="space-y-6">
                <CardTitle>6) Additional Context</CardTitle>

                <div className="space-y-2">
                  <Label htmlFor="success_definition">
                    What would make this partnership a "win" six months from now? (optional)
                  </Label>
                  <Textarea
                    id="success_definition"
                    value={formData.success_definition}
                    onChange={(e) => updateField("success_definition", e.target.value)}
                    placeholder="Describe what success looks like for you..."
                    rows={4}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="accessibility_needs">
                    Any accessibility needs, considerations, or context we should be aware of? (optional)
                  </Label>
                  <Textarea
                    id="accessibility_needs"
                    value={formData.accessibility_needs}
                    onChange={(e) => updateField("accessibility_needs", e.target.value)}
                    placeholder="Share any accessibility needs or special considerations..."
                    rows={4}
                  />
                </div>

                <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 mt-8">
                  <h3 className="text-lg font-semibold text-purple-900 mb-2">Next Step</h3>
                  <p className="text-purple-700">
                    After submitting this assessment, you'll be directed to book a discovery call
                    to review your needs and co-create the best solution together.
                  </p>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-6 border-t">
              {currentSection > 1 ? (
                <Button
                  variant="outline"
                  onClick={() => setCurrentSection(currentSection - 1)}
                >
                  Previous
                </Button>
              ) : (
                <div />
              )}

              {currentSection < 6 ? (
                <Button
                  onClick={() => setCurrentSection(currentSection + 1)}
                  disabled={!canProceed()}
                >
                  Next
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={isSubmitting || !canProceed()}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  {isSubmitting ? "Submitting..." : "Submit & Book Discovery Call"}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
