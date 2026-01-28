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
import { publicFeedbackApi, publicTestimonialsApi } from "@/lib/api";
import { CheckCircle, AlertCircle, ChevronRight, Video, Quote } from "lucide-react";
import VideoRecorder from "@/components/VideoRecorder";

interface SurveyData {
  contact_name: string;
  workflow_type: string;
  project_title: string | null;
  already_completed: boolean;
}

// Outcome options
const OUTCOME_OPTIONS = [
  { value: "increased_confidence", label: "Increased confidence/executive presence" },
  { value: "stronger_communication", label: "Stronger communication" },
  { value: "clearer_decision_making", label: "Clearer decision-making" },
  { value: "better_boundaries", label: "Better boundaries" },
  { value: "navigated_bias", label: "Navigated bias more effectively" },
  { value: "career_move_promotion", label: "Career move/promotion/new role" },
  { value: "pay_increase", label: "Pay increase/negotiation" },
  { value: "improved_work_relationships", label: "Improved relationships at work" },
  { value: "reduced_imposter_syndrome", label: "Reduced imposter syndrome" },
  { value: "clarity_on_identity", label: "Greater clarity on values/voice/leadership identity" },
];

// Helpful parts options
const HELPFUL_PARTS_OPTIONS = [
  { value: "powerful_questions", label: "Powerful questions / reflection" },
  { value: "practical_tools", label: "Practical tools + frameworks" },
  { value: "accountability", label: "Accountability and follow-through" },
  { value: "role_play", label: "Role-play/practice" },
  { value: "mindset_work", label: "Mindset + limiting beliefs work" },
  { value: "values_identity_work", label: "Values/identity work" },
  { value: "navigating_bias_support", label: "Support navigating workplace dynamics/bias" },
  { value: "resources_homework", label: "Resources/homework between sessions" },
];

// Psychological safety options
const SAFETY_OPTIONS = [
  { value: "strongly_agree", label: "Strongly agree" },
  { value: "agree", label: "Agree" },
  { value: "neutral", label: "Neutral" },
  { value: "disagree", label: "Disagree" },
  { value: "strongly_disagree", label: "Strongly disagree" },
];

export default function FeedbackSurveyPage() {
  const params = useParams();
  const token = params.token as string;

  const [surveyData, setSurveyData] = useState<SurveyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [currentSection, setCurrentSection] = useState(1);

  // Section 1: Overall Experience
  const [satisfactionRating, setSatisfactionRating] = useState<number>(0);
  const [npsScore, setNpsScore] = useState<number | null>(null);
  const [initialGoals, setInitialGoals] = useState("");

  // Section 2: Growth + Measurement
  const [outcomes, setOutcomes] = useState<string[]>([]);
  const [outcomesOther, setOutcomesOther] = useState("");
  const [specificWins, setSpecificWins] = useState("");
  const [progressRating, setProgressRating] = useState<number>(0);
  const [mostTransformative, setMostTransformative] = useState("");

  // Section 3: Coaching Process
  const [helpfulParts, setHelpfulParts] = useState<string[]>([]);
  const [helpfulPartsOther, setHelpfulPartsOther] = useState("");
  const [leastHelpful, setLeastHelpful] = useState("");
  const [wishDoneEarlier, setWishDoneEarlier] = useState("");

  // Section 4: Equity, Safety, Support
  const [psychologicalSafety, setPsychologicalSafety] = useState("");
  const [wocSupportRating, setWocSupportRating] = useState<number>(0);
  const [supportFeedback, setSupportFeedback] = useState("");

  // Section 5: Testimonial
  const [mayShareTestimonial, setMayShareTestimonial] = useState("");
  const [displayNameTitle, setDisplayNameTitle] = useState("");
  const [writtenTestimonial, setWrittenTestimonial] = useState("");
  const [willingToRecordVideo, setWillingToRecordVideo] = useState<boolean | null>(null);
  const [videoUploadPreference, setVideoUploadPreference] = useState("");

  // Video testimonial data
  const [videoData, setVideoData] = useState<{
    video_url: string;
    video_public_id: string;
    video_duration_seconds: number;
    thumbnail_url: string | null;
  } | null>(null);

  // Final comments
  const [additionalComments, setAdditionalComments] = useState("");

  useEffect(() => {
    if (token) {
      loadSurvey();
    }
  }, [token]);

  const loadSurvey = async () => {
    try {
      const data = await publicFeedbackApi.getSurvey(token);
      setSurveyData(data);
      if (data.already_completed) {
        setSubmitted(true);
      }
    } catch (err: any) {
      setError(err.message || "Survey not found or has expired");
    } finally {
      setLoading(false);
    }
  };

  const toggleOutcome = (value: string) => {
    setOutcomes(prev =>
      prev.includes(value)
        ? prev.filter(v => v !== value)
        : [...prev, value]
    );
  };

  const toggleHelpfulPart = (value: string) => {
    setHelpfulParts(prev =>
      prev.includes(value)
        ? prev.filter(v => v !== value)
        : [...prev, value]
    );
  };

  const canProceed = () => {
    switch (currentSection) {
      case 1:
        return satisfactionRating > 0 && npsScore !== null;
      case 2:
      case 3:
      case 4:
      case 5:
        return true; // Optional sections
      default:
        return true;
    }
  };

  const handleSubmit = async () => {
    if (satisfactionRating === 0) {
      alert("Please rate your overall satisfaction");
      return;
    }

    if (npsScore === null) {
      alert("Please indicate how likely you are to recommend coaching");
      return;
    }

    setSubmitting(true);
    try {
      await publicFeedbackApi.submitSurvey(token, {
        // Section 1
        satisfaction_rating: satisfactionRating,
        nps_score: npsScore,
        initial_goals: initialGoals || undefined,
        // Section 2
        outcomes: outcomes.length > 0 ? outcomes : undefined,
        outcomes_other: outcomesOther || undefined,
        specific_wins: specificWins || undefined,
        progress_rating: progressRating > 0 ? progressRating : undefined,
        most_transformative: mostTransformative || undefined,
        // Section 3
        helpful_parts: helpfulParts.length > 0 ? helpfulParts : undefined,
        helpful_parts_other: helpfulPartsOther || undefined,
        least_helpful: leastHelpful || undefined,
        wish_done_earlier: wishDoneEarlier || undefined,
        // Section 4
        psychological_safety: psychologicalSafety || undefined,
        woc_support_rating: wocSupportRating > 0 ? wocSupportRating : undefined,
        support_feedback: supportFeedback || undefined,
        // Section 5
        may_share_testimonial: mayShareTestimonial || undefined,
        display_name_title: displayNameTitle || undefined,
        written_testimonial: writtenTestimonial || undefined,
        willing_to_record_video: willingToRecordVideo ?? undefined,
        video_upload_preference: videoUploadPreference || undefined,
        // Video data (if recorded)
        video_url: videoData?.video_url,
        video_public_id: videoData?.video_public_id,
        video_duration_seconds: videoData?.video_duration_seconds,
        video_thumbnail_url: videoData?.thumbnail_url,
        // Final
        additional_comments: additionalComments || undefined,
      });
      setSubmitted(true);
    } catch (err: any) {
      alert(err.message || "Failed to submit survey");
    } finally {
      setSubmitting(false);
    }
  };

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
            <h2 className="text-xl font-bold mb-2">Survey Not Available</h2>
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
              Your feedback has been submitted. We truly appreciate you taking the time to share your experience. Your reflections help serve women of color leaders with even more clarity and care.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const totalSections = 6;

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
          <h1 className="text-2xl font-bold mb-2">End-of-Engagement Feedback</h1>
          <p className="text-gray-500">
            Congratulations on completing your coaching engagement, {surveyData?.contact_name}!
            Your feedback helps measure impact and keep improving.
          </p>
          <p className="text-sm text-gray-400 mt-2">This should take about 5-7 minutes.</p>
        </div>

        {/* Progress indicator */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-500 mb-2">
            <span>Section {currentSection} of {totalSections}</span>
            <span>{Math.round((currentSection / totalSections) * 100)}% complete</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-violet-600 transition-all duration-300"
              style={{ width: `${(currentSection / totalSections) * 100}%` }}
            />
          </div>
        </div>

        <Card>
          <CardContent className="pt-6 space-y-6">
            {/* Section 1: Overall Experience */}
            {currentSection === 1 && (
              <>
                <CardHeader className="px-0 pt-0">
                  <CardTitle>Overall Experience</CardTitle>
                  <CardDescription>Tell us about your overall coaching experience</CardDescription>
                </CardHeader>

                {/* Satisfaction Rating 1-10 */}
                <div>
                  <Label className="text-base font-medium">
                    Overall, how satisfied are you with your coaching experience? *
                  </Label>
                  <p className="text-sm text-gray-500 mb-3">1 = Very Dissatisfied, 10 = Extremely Satisfied</p>
                  <div className="flex flex-wrap gap-2">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((rating) => (
                      <button
                        key={rating}
                        type="button"
                        onClick={() => setSatisfactionRating(rating)}
                        className={`w-10 h-10 rounded-lg border-2 font-medium transition-all ${
                          satisfactionRating === rating
                            ? "border-violet-500 bg-violet-50 text-violet-600"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        {rating}
                      </button>
                    ))}
                  </div>
                </div>

                {/* NPS Score */}
                <div>
                  <Label className="text-base font-medium">
                    How likely are you to recommend coaching with Wendy to a colleague/friend? *
                  </Label>
                  <p className="text-sm text-gray-500 mb-3">0 = Not at all likely, 10 = Extremely likely</p>
                  <div className="flex flex-wrap gap-2">
                    {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((score) => (
                      <button
                        key={score}
                        type="button"
                        onClick={() => setNpsScore(score)}
                        className={`w-10 h-10 rounded-lg border-2 font-medium transition-all ${
                          npsScore === score
                            ? "border-violet-500 bg-violet-50 text-violet-600"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        {score}
                      </button>
                    ))}
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-1 px-1">
                    <span>Not likely</span>
                    <span>Extremely likely</span>
                  </div>
                </div>

                {/* Initial Goals */}
                <div>
                  <Label htmlFor="initialGoals" className="text-base font-medium">
                    When you started coaching, what were you hoping to get out of the engagement?
                  </Label>
                  <Textarea
                    id="initialGoals"
                    value={initialGoals}
                    onChange={(e) => setInitialGoals(e.target.value)}
                    placeholder="Share what you were hoping to achieve..."
                    rows={3}
                    className="mt-2"
                  />
                </div>
              </>
            )}

            {/* Section 2: Growth + Measurement */}
            {currentSection === 2 && (
              <>
                <CardHeader className="px-0 pt-0">
                  <CardTitle>Growth + Measurement</CardTitle>
                  <CardDescription>What outcomes did you experience?</CardDescription>
                </CardHeader>

                {/* Outcomes Checklist */}
                <div>
                  <Label className="text-base font-medium">
                    What outcomes did you experience during our engagement? (Check all that apply)
                  </Label>
                  <div className="mt-3 space-y-3">
                    {OUTCOME_OPTIONS.map((option) => (
                      <label key={option.value} className="flex items-center gap-3 cursor-pointer">
                        <Checkbox
                          checked={outcomes.includes(option.value)}
                          onCheckedChange={() => toggleOutcome(option.value)}
                        />
                        <span className="text-sm">{option.label}</span>
                      </label>
                    ))}
                    <div className="flex items-center gap-3">
                      <Checkbox
                        checked={outcomesOther.length > 0}
                        onCheckedChange={() => {}}
                        disabled
                      />
                      <Input
                        placeholder="Other (please specify)"
                        value={outcomesOther}
                        onChange={(e) => setOutcomesOther(e.target.value)}
                        className="flex-1"
                      />
                    </div>
                  </div>
                </div>

                {/* Specific Wins */}
                <div>
                  <Label htmlFor="specificWins" className="text-base font-medium">
                    What are 1-3 specific wins you're most proud of?
                  </Label>
                  <Textarea
                    id="specificWins"
                    value={specificWins}
                    onChange={(e) => setSpecificWins(e.target.value)}
                    placeholder="Share your proudest wins..."
                    rows={3}
                    className="mt-2"
                  />
                </div>

                {/* Progress Rating */}
                <div>
                  <Label className="text-base font-medium">
                    On a scale of 1-10, how much progress did you make toward your original goals?
                  </Label>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((rating) => (
                      <button
                        key={rating}
                        type="button"
                        onClick={() => setProgressRating(rating)}
                        className={`w-10 h-10 rounded-lg border-2 font-medium transition-all ${
                          progressRating === rating
                            ? "border-violet-500 bg-violet-50 text-violet-600"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        {rating}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Most Transformative */}
                <div>
                  <Label htmlFor="mostTransformative" className="text-base font-medium">
                    What felt most transformative about our work together?
                  </Label>
                  <Textarea
                    id="mostTransformative"
                    value={mostTransformative}
                    onChange={(e) => setMostTransformative(e.target.value)}
                    placeholder="What made the biggest difference..."
                    rows={3}
                    className="mt-2"
                  />
                </div>
              </>
            )}

            {/* Section 3: Coaching Process */}
            {currentSection === 3 && (
              <>
                <CardHeader className="px-0 pt-0">
                  <CardTitle>Coaching Process</CardTitle>
                  <CardDescription>What worked well and what could be improved?</CardDescription>
                </CardHeader>

                {/* Helpful Parts Checklist */}
                <div>
                  <Label className="text-base font-medium">
                    Which parts of the coaching were most helpful? (Check all that apply)
                  </Label>
                  <div className="mt-3 space-y-3">
                    {HELPFUL_PARTS_OPTIONS.map((option) => (
                      <label key={option.value} className="flex items-center gap-3 cursor-pointer">
                        <Checkbox
                          checked={helpfulParts.includes(option.value)}
                          onCheckedChange={() => toggleHelpfulPart(option.value)}
                        />
                        <span className="text-sm">{option.label}</span>
                      </label>
                    ))}
                    <div className="flex items-center gap-3">
                      <Checkbox
                        checked={helpfulPartsOther.length > 0}
                        onCheckedChange={() => {}}
                        disabled
                      />
                      <Input
                        placeholder="Other (please specify)"
                        value={helpfulPartsOther}
                        onChange={(e) => setHelpfulPartsOther(e.target.value)}
                        className="flex-1"
                      />
                    </div>
                  </div>
                </div>

                {/* Least Helpful */}
                <div>
                  <Label htmlFor="leastHelpful" className="text-base font-medium">
                    What was least helpful (or could have been better)?
                  </Label>
                  <Textarea
                    id="leastHelpful"
                    value={leastHelpful}
                    onChange={(e) => setLeastHelpful(e.target.value)}
                    placeholder="Share any suggestions..."
                    rows={3}
                    className="mt-2"
                  />
                </div>

                {/* Wish Done Earlier */}
                <div>
                  <Label htmlFor="wishDoneEarlier" className="text-base font-medium">
                    What do you wish we had done earlier in the engagement?
                  </Label>
                  <Textarea
                    id="wishDoneEarlier"
                    value={wishDoneEarlier}
                    onChange={(e) => setWishDoneEarlier(e.target.value)}
                    placeholder="Looking back, what would you have liked sooner..."
                    rows={3}
                    className="mt-2"
                  />
                </div>
              </>
            )}

            {/* Section 4: Equity, Safety, Support */}
            {currentSection === 4 && (
              <>
                <CardHeader className="px-0 pt-0">
                  <CardTitle>Equity, Safety, and Support</CardTitle>
                  <CardDescription>How supported did you feel throughout coaching?</CardDescription>
                </CardHeader>

                {/* Psychological Safety */}
                <div>
                  <Label className="text-base font-medium">
                    I felt psychologically safe, respected, and able to show up authentically in coaching.
                  </Label>
                  <RadioGroup
                    value={psychologicalSafety}
                    onValueChange={setPsychologicalSafety}
                    className="mt-3 space-y-2"
                  >
                    {SAFETY_OPTIONS.map((option) => (
                      <div key={option.value} className="flex items-center gap-3">
                        <RadioGroupItem value={option.value} id={option.value} />
                        <Label htmlFor={option.value} className="font-normal cursor-pointer">
                          {option.label}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>

                {/* WOC Support Rating */}
                <div>
                  <Label className="text-base font-medium">
                    How well did coaching support you as a woman of color navigating your workplace context?
                  </Label>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((rating) => (
                      <button
                        key={rating}
                        type="button"
                        onClick={() => setWocSupportRating(rating)}
                        className={`w-10 h-10 rounded-lg border-2 font-medium transition-all ${
                          wocSupportRating === rating
                            ? "border-violet-500 bg-violet-50 text-violet-600"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        {rating}
                      </button>
                    ))}
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-1 px-1">
                    <span>Not well</span>
                    <span>Extremely well</span>
                  </div>
                </div>

                {/* Support Feedback */}
                <div>
                  <Label htmlFor="supportFeedback" className="text-base font-medium">
                    Anything you want to name about what helped you feel supported (or what could be improved)?
                  </Label>
                  <Textarea
                    id="supportFeedback"
                    value={supportFeedback}
                    onChange={(e) => setSupportFeedback(e.target.value)}
                    placeholder="Share your thoughts..."
                    rows={3}
                    className="mt-2"
                  />
                </div>
              </>
            )}

            {/* Section 5: Testimonial */}
            {currentSection === 5 && (
              <>
                <CardHeader className="px-0 pt-0">
                  <CardTitle className="flex items-center gap-2">
                    <Quote className="h-5 w-5" />
                    Testimonial (Optional)
                  </CardTitle>
                  <CardDescription>
                    A warm invitation: If you're open to it, a testimonial helps other women of color understand what's possible through coaching.
                  </CardDescription>
                </CardHeader>

                {/* Permission */}
                <div>
                  <Label className="text-base font-medium">
                    May I share your testimonial publicly?
                  </Label>
                  <RadioGroup
                    value={mayShareTestimonial}
                    onValueChange={setMayShareTestimonial}
                    className="mt-3 space-y-2"
                  >
                    <div className="flex items-center gap-3">
                      <RadioGroupItem value="yes_with_name" id="yes_with_name" />
                      <Label htmlFor="yes_with_name" className="font-normal cursor-pointer">
                        Yes, with my name + title
                      </Label>
                    </div>
                    <div className="flex items-center gap-3">
                      <RadioGroupItem value="not_now" id="not_now" />
                      <Label htmlFor="not_now" className="font-normal cursor-pointer">
                        Not at this time
                      </Label>
                    </div>
                  </RadioGroup>
                </div>

                {mayShareTestimonial === "yes_with_name" && (
                  <div>
                    <Label htmlFor="displayNameTitle" className="text-base font-medium">
                      How should I list your name/title/company?
                    </Label>
                    <Input
                      id="displayNameTitle"
                      value={displayNameTitle}
                      onChange={(e) => setDisplayNameTitle(e.target.value)}
                      placeholder="e.g., Jane Doe, VP of Marketing at Acme Inc."
                      className="mt-2"
                    />
                  </div>
                )}

                {/* Written Testimonial */}
                <div>
                  <Label htmlFor="writtenTestimonial" className="text-base font-medium">
                    Written testimonial (3-6 sentences)
                  </Label>
                  <p className="text-sm text-gray-500 mt-1 mb-2">
                    If helpful, you can use any of these starters:
                  </p>
                  <ul className="text-sm text-gray-500 mb-3 space-y-1 list-disc list-inside">
                    <li>Before coaching, I was struggling with ___.</li>
                    <li>The biggest shift for me was ___.</li>
                    <li>A specific win I'm proud of is ___.</li>
                    <li>Wendy's coaching style is ___ and that helped me ___.</li>
                    <li>If you're a woman of color navigating ___, I'd recommend Wendy because ___.</li>
                  </ul>
                  <Textarea
                    id="writtenTestimonial"
                    value={writtenTestimonial}
                    onChange={(e) => setWrittenTestimonial(e.target.value)}
                    placeholder="Share your experience..."
                    rows={5}
                  />
                </div>

                {/* Video Testimonial */}
                <div className="p-4 bg-violet-50 rounded-lg border border-violet-100">
                  <div className="flex items-center gap-2 mb-3">
                    <Video className="h-5 w-5 text-violet-600" />
                    <Label className="text-base font-medium text-violet-900">
                      Video Testimonial (60-120 seconds)
                    </Label>
                  </div>
                  <p className="text-sm text-violet-700 mb-3">
                    If you're open to it, would you be willing to record a short video testimonial?
                    Video testimonials are especially powerful for helping others see the real impact of coaching.
                  </p>

                  {!videoData && (
                    <RadioGroup
                      value={willingToRecordVideo === true ? "yes" : willingToRecordVideo === false ? "no" : ""}
                      onValueChange={(v) => setWillingToRecordVideo(v === "yes")}
                      className="space-y-2"
                    >
                      <div className="flex items-center gap-3">
                        <RadioGroupItem value="yes" id="video_yes" />
                        <Label htmlFor="video_yes" className="font-normal cursor-pointer">
                          Yes, I'd like to record one now
                        </Label>
                      </div>
                      <div className="flex items-center gap-3">
                        <RadioGroupItem value="no" id="video_no" />
                        <Label htmlFor="video_no" className="font-normal cursor-pointer">
                          Not at this time
                        </Label>
                      </div>
                    </RadioGroup>
                  )}

                  {willingToRecordVideo && !videoData && (
                    <div className="mt-4 bg-white rounded-lg p-4">
                      <VideoRecorder
                        maxDuration={120}
                        onUpload={publicTestimonialsApi.uploadVideo}
                        onComplete={(data) => {
                          setVideoData(data);
                        }}
                      />
                    </div>
                  )}

                  {videoData && (
                    <div className="mt-4 bg-white rounded-lg p-4">
                      <div className="flex items-center gap-3 text-green-700">
                        <CheckCircle className="h-5 w-5" />
                        <span className="font-medium">Video recorded successfully!</span>
                      </div>
                      <p className="text-sm text-gray-500 mt-2">
                        Your video testimonial has been uploaded and will be included with your feedback.
                      </p>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="mt-3"
                        onClick={() => {
                          setVideoData(null);
                          setWillingToRecordVideo(true);
                        }}
                      >
                        Record a different video
                      </Button>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* Section 6: Final */}
            {currentSection === 6 && (
              <>
                <CardHeader className="px-0 pt-0">
                  <CardTitle>Final Feedback</CardTitle>
                  <CardDescription>Any last thoughts before you submit?</CardDescription>
                </CardHeader>

                <div>
                  <Label htmlFor="additionalComments" className="text-base font-medium">
                    Any final feedback you'd like to share?
                  </Label>
                  <Textarea
                    id="additionalComments"
                    value={additionalComments}
                    onChange={(e) => setAdditionalComments(e.target.value)}
                    placeholder="Anything else on your mind..."
                    rows={4}
                    className="mt-2"
                  />
                </div>

                <div className="p-4 bg-green-50 rounded-lg border border-green-100">
                  <p className="text-sm text-green-800">
                    Thank you for taking the time to complete this feedback form. Your reflections help serve women of color leaders with even more clarity and care.
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
                  {submitting ? "Submitting..." : "Submit Feedback"}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-gray-500 mt-4">
          Your feedback is confidential and helps improve our services.
        </p>
      </div>
    </div>
  );
}
