"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { offboardingApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  ArrowLeft,
  User,
  FolderKanban,
  FileText,
  CheckCircle,
  Clock,
  Play,
  XCircle,
  Mail,
  MessageSquare,
  Quote,
  Star,
  Send,
  Check,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";

interface ChecklistItem {
  item: string;
  completed: boolean;
  completed_at: string | null;
}

interface Activity {
  id: string;
  action: string;
  details: Record<string, any> | null;
  created_at: string;
}

interface Workflow {
  id: string;
  contact_id: string;
  contact_name: string | null;
  contact_email: string | null;
  workflow_type: string;
  related_project_id: string | null;
  related_project_title: string | null;
  related_contract_id: string | null;
  status: string;
  initiated_at: string;
  completed_at: string | null;
  checklist: ChecklistItem[];
  send_survey: boolean;
  request_testimonial: boolean;
  send_certificate: boolean;
  survey_token: string | null;
  testimonial_token: string | null;
  survey_completed_at: string | null;
  survey_response: Record<string, any> | null;
  testimonial_received: boolean;
  testimonial_text: string | null;
  testimonial_author_name: string | null;
  testimonial_permission_granted: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-100 text-gray-800",
  in_progress: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  pending: <Clock className="h-4 w-4" />,
  in_progress: <Play className="h-4 w-4" />,
  completed: <CheckCircle className="h-4 w-4" />,
  cancelled: <XCircle className="h-4 w-4" />,
};

const WORKFLOW_TYPE_LABELS: Record<string, string> = {
  client: "Client Offboarding",
  project: "Project Completion",
  contract: "Contract End",
};

const WORKFLOW_TYPE_ICONS: Record<string, React.ReactNode> = {
  client: <User className="h-5 w-5" />,
  project: <FolderKanban className="h-5 w-5" />,
  contract: <FileText className="h-5 w-5" />,
};

const ACTION_LABELS: Record<string, string> = {
  initiated: "Workflow initiated",
  checklist_updated: "Checklist updated",
  survey_sent: "Survey email sent",
  testimonial_requested: "Testimonial requested",
  completion_email_sent: "Completion email sent",
  survey_completed: "Survey completed by client",
  testimonial_received: "Testimonial received",
  completed: "Workflow marked complete",
  cancelled: "Workflow cancelled",
};

export default function OffboardingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    if (params.id) {
      loadWorkflow(params.id as string);
    }
  }, [params.id]);

  const loadWorkflow = async (id: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const [workflowData, activityData] = await Promise.all([
        offboardingApi.get(token, id),
        offboardingApi.getActivity(token, id),
      ]);

      setWorkflow(workflowData);
      setActivities(activityData);
    } catch (err) {
      console.error("Failed to load workflow:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleChecklistItem = async (index: number) => {
    if (!workflow) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await offboardingApi.toggleChecklistItem(token, workflow.id, index);
      await loadWorkflow(workflow.id);
    } catch (err: any) {
      alert(err.message || "Failed to update checklist");
    }
  };

  const handleAction = async (action: string) => {
    if (!workflow) return;

    setActionLoading(action);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      switch (action) {
        case "send_survey":
          await offboardingApi.sendSurvey(token, workflow.id);
          break;
        case "request_testimonial":
          await offboardingApi.requestTestimonial(token, workflow.id);
          break;
        case "send_completion":
          await offboardingApi.sendCompletionEmail(token, workflow.id);
          break;
        case "complete":
          await offboardingApi.complete(token, workflow.id);
          break;
        case "cancel":
          if (confirm("Are you sure you want to cancel this workflow?")) {
            await offboardingApi.cancel(token, workflow.id);
          } else {
            setActionLoading(null);
            return;
          }
          break;
      }

      await loadWorkflow(workflow.id);
    } catch (err: any) {
      alert(err.message || "Action failed");
    } finally {
      setActionLoading(null);
    }
  };

  const renderStars = (rating: number) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-5 w-5 ${star <= rating ? "text-yellow-400 fill-yellow-400" : "text-gray-300"}`}
          />
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <Shell>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading...</div>
        </div>
      </Shell>
    );
  }

  if (!workflow) {
    return (
      <Shell>
        <div className="flex flex-col items-center justify-center h-64">
          <AlertCircle className="h-12 w-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium">Workflow not found</h3>
          <Link href="/offboarding">
            <Button className="mt-4">Back to Offboarding</Button>
          </Link>
        </div>
      </Shell>
    );
  }

  const checklistProgress =
    workflow.checklist.length > 0
      ? Math.round(
          (workflow.checklist.filter((i) => i.completed).length / workflow.checklist.length) * 100
        )
      : 0;

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/offboarding">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-12 h-12 rounded-full bg-gray-100">
                {WORKFLOW_TYPE_ICONS[workflow.workflow_type]}
              </div>
              <div>
                <h1 className="text-2xl font-bold">{workflow.contact_name || "Unknown Contact"}</h1>
                <div className="flex items-center gap-2 text-gray-500">
                  <span>{WORKFLOW_TYPE_LABELS[workflow.workflow_type]}</span>
                  <span>•</span>
                  <span>Started {formatDate(workflow.initiated_at)}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Badge className={`${STATUS_COLORS[workflow.status]} flex items-center gap-1`}>
              {STATUS_ICONS[workflow.status]}
              <span className="capitalize">{workflow.status.replace("_", " ")}</span>
            </Badge>

            {workflow.status !== "completed" && workflow.status !== "cancelled" && (
              <>
                <Button
                  variant="outline"
                  onClick={() => handleAction("cancel")}
                  disabled={actionLoading !== null}
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => handleAction("complete")}
                  disabled={actionLoading !== null}
                >
                  <Check className="h-4 w-4 mr-2" />
                  Mark Complete
                </Button>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Checklist */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Checklist</CardTitle>
                    <CardDescription>Complete all items before finishing</CardDescription>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">{checklistProgress}%</div>
                    <div className="text-sm text-gray-500">
                      {workflow.checklist.filter((i) => i.completed).length}/{workflow.checklist.length} complete
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {workflow.checklist.map((item, index) => (
                    <div
                      key={index}
                      className={`flex items-center gap-3 p-3 rounded-lg border ${
                        item.completed ? "bg-green-50 border-green-200" : "bg-white border-gray-200"
                      }`}
                    >
                      <Checkbox
                        checked={item.completed}
                        onCheckedChange={() => toggleChecklistItem(index)}
                        disabled={workflow.status === "completed" || workflow.status === "cancelled"}
                      />
                      <span className={item.completed ? "text-green-700 line-through" : ""}>
                        {item.item}
                      </span>
                      {item.completed && item.completed_at && (
                        <span className="ml-auto text-xs text-gray-500">
                          {formatDate(item.completed_at)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Survey Response */}
            {workflow.survey_completed_at && workflow.survey_response && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5 text-purple-500" />
                    Survey Response
                  </CardTitle>
                  <CardDescription>Completed {formatDate(workflow.survey_completed_at)}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Section 1: Overall Experience */}
                  <div className="space-y-4">
                    <h4 className="font-semibold text-gray-900 border-b pb-2">Overall Experience</h4>

                    <div className="grid grid-cols-2 gap-4">
                      {workflow.survey_response.satisfaction_rating && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">Satisfaction</div>
                          <div className="flex items-center gap-2">
                            <div className="text-2xl font-bold">{workflow.survey_response.satisfaction_rating}</div>
                            <div className="text-gray-500">/10</div>
                            {renderStars(Math.round(workflow.survey_response.satisfaction_rating / 2))}
                          </div>
                        </div>
                      )}

                      {workflow.survey_response.nps_score !== undefined && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">NPS Score</div>
                          <div className="flex items-center gap-2">
                            <div className="text-2xl font-bold">{workflow.survey_response.nps_score}</div>
                            <div className="text-gray-500">/10</div>
                            <Badge className={
                              workflow.survey_response.nps_score >= 9 ? "bg-green-100 text-green-800" :
                              workflow.survey_response.nps_score >= 7 ? "bg-yellow-100 text-yellow-800" :
                              "bg-red-100 text-red-800"
                            }>
                              {workflow.survey_response.nps_score >= 9 ? "Promoter" :
                               workflow.survey_response.nps_score >= 7 ? "Passive" : "Detractor"}
                            </Badge>
                          </div>
                        </div>
                      )}
                    </div>

                    {workflow.survey_response.initial_goals && (
                      <div>
                        <div className="text-sm font-medium text-gray-500 mb-1">Initial Goals</div>
                        <p className="text-gray-700">{workflow.survey_response.initial_goals}</p>
                      </div>
                    )}
                  </div>

                  {/* Section 2: Growth + Measurement */}
                  {(workflow.survey_response.outcomes || workflow.survey_response.specific_wins || workflow.survey_response.progress_rating || workflow.survey_response.most_transformative) && (
                    <div className="space-y-4">
                      <h4 className="font-semibold text-gray-900 border-b pb-2">Growth + Measurement</h4>

                      {workflow.survey_response.outcomes && workflow.survey_response.outcomes.length > 0 && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-2">Outcomes Achieved</div>
                          <div className="flex flex-wrap gap-2">
                            {workflow.survey_response.outcomes.map((outcome: string) => (
                              <Badge key={outcome} variant="outline" className="bg-green-50 text-green-700">
                                <Check className="h-3 w-3 mr-1" />
                                {outcome.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase())}
                              </Badge>
                            ))}
                          </div>
                          {workflow.survey_response.outcomes_other && (
                            <p className="text-gray-600 text-sm mt-2">Other: {workflow.survey_response.outcomes_other}</p>
                          )}
                        </div>
                      )}

                      {workflow.survey_response.progress_rating && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">Progress Toward Goals</div>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-gray-200 rounded-full h-3">
                              <div
                                className="bg-purple-600 h-3 rounded-full transition-all"
                                style={{ width: `${workflow.survey_response.progress_rating * 10}%` }}
                              />
                            </div>
                            <span className="font-medium">{workflow.survey_response.progress_rating}/10</span>
                          </div>
                        </div>
                      )}

                      {workflow.survey_response.specific_wins && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">Specific Wins</div>
                          <p className="text-gray-700">{workflow.survey_response.specific_wins}</p>
                        </div>
                      )}

                      {workflow.survey_response.most_transformative && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">Most Transformative</div>
                          <p className="text-gray-700">{workflow.survey_response.most_transformative}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Section 3: Coaching Process */}
                  {(workflow.survey_response.helpful_parts || workflow.survey_response.least_helpful || workflow.survey_response.wish_done_earlier) && (
                    <div className="space-y-4">
                      <h4 className="font-semibold text-gray-900 border-b pb-2">Coaching Process</h4>

                      {workflow.survey_response.helpful_parts && workflow.survey_response.helpful_parts.length > 0 && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-2">Most Helpful Parts</div>
                          <div className="flex flex-wrap gap-2">
                            {workflow.survey_response.helpful_parts.map((part: string) => (
                              <Badge key={part} variant="outline" className="bg-blue-50 text-blue-700">
                                {part.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase())}
                              </Badge>
                            ))}
                          </div>
                          {workflow.survey_response.helpful_parts_other && (
                            <p className="text-gray-600 text-sm mt-2">Other: {workflow.survey_response.helpful_parts_other}</p>
                          )}
                        </div>
                      )}

                      {workflow.survey_response.least_helpful && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">Least Helpful / Areas for Improvement</div>
                          <p className="text-gray-700">{workflow.survey_response.least_helpful}</p>
                        </div>
                      )}

                      {workflow.survey_response.wish_done_earlier && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">Wish We Had Done Earlier</div>
                          <p className="text-gray-700">{workflow.survey_response.wish_done_earlier}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Section 4: Equity, Safety & Support */}
                  {(workflow.survey_response.psychological_safety || workflow.survey_response.woc_support_rating || workflow.survey_response.support_feedback) && (
                    <div className="space-y-4">
                      <h4 className="font-semibold text-gray-900 border-b pb-2">Equity, Safety & Support</h4>

                      <div className="grid grid-cols-2 gap-4">
                        {workflow.survey_response.psychological_safety && (
                          <div>
                            <div className="text-sm font-medium text-gray-500 mb-1">Psychological Safety</div>
                            <Badge className={
                              ["strongly_agree", "agree"].includes(workflow.survey_response.psychological_safety)
                                ? "bg-green-100 text-green-800"
                                : workflow.survey_response.psychological_safety === "neutral"
                                  ? "bg-gray-100 text-gray-800"
                                  : "bg-red-100 text-red-800"
                            }>
                              {workflow.survey_response.psychological_safety.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase())}
                            </Badge>
                          </div>
                        )}

                        {workflow.survey_response.woc_support_rating && (
                          <div>
                            <div className="text-sm font-medium text-gray-500 mb-1">WOC Support Rating</div>
                            <div className="flex items-center gap-2">
                              <div className="text-2xl font-bold">{workflow.survey_response.woc_support_rating}</div>
                              <div className="text-gray-500">/10</div>
                            </div>
                          </div>
                        )}
                      </div>

                      {workflow.survey_response.support_feedback && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">What Helped Feel Supported</div>
                          <p className="text-gray-700">{workflow.survey_response.support_feedback}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Section 5: Testimonial Permission */}
                  {(workflow.survey_response.may_share_testimonial || workflow.survey_response.written_testimonial) && (
                    <div className="space-y-4">
                      <h4 className="font-semibold text-gray-900 border-b pb-2">Testimonial</h4>

                      {workflow.survey_response.may_share_testimonial && (
                        <div className="flex items-center gap-2">
                          <Badge className={
                            workflow.survey_response.may_share_testimonial === "yes_with_name"
                              ? "bg-green-100 text-green-800"
                              : "bg-gray-100 text-gray-800"
                          }>
                            {workflow.survey_response.may_share_testimonial === "yes_with_name"
                              ? "Willing to share with name"
                              : "Not ready to share"}
                          </Badge>
                        </div>
                      )}

                      {workflow.survey_response.display_name_title && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">Display As</div>
                          <p className="text-gray-700">{workflow.survey_response.display_name_title}</p>
                        </div>
                      )}

                      {workflow.survey_response.written_testimonial && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">Written Testimonial</div>
                          <blockquote className="text-gray-700 italic border-l-4 border-purple-500 pl-4">
                            "{workflow.survey_response.written_testimonial}"
                          </blockquote>
                        </div>
                      )}

                      {workflow.survey_response.video_url && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-2">Video Testimonial</div>
                          <div className="aspect-video bg-black rounded-lg overflow-hidden max-w-md">
                            <video
                              src={workflow.survey_response.video_url}
                              controls
                              className="w-full h-full"
                              poster={workflow.survey_response.video_thumbnail_url || undefined}
                            />
                          </div>
                          {workflow.survey_response.video_duration_seconds && (
                            <p className="text-xs text-gray-500 mt-1">
                              Duration: {Math.floor(workflow.survey_response.video_duration_seconds / 60)}:{(workflow.survey_response.video_duration_seconds % 60).toString().padStart(2, '0')}
                            </p>
                          )}
                        </div>
                      )}

                      {!workflow.survey_response.video_url && workflow.survey_response.willing_to_record_video !== undefined && (
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-500">Video testimonial:</span>
                          <Badge variant="outline">
                            {workflow.survey_response.willing_to_record_video ? "Open to recording" : "Not interested"}
                          </Badge>
                          {workflow.survey_response.willing_to_record_video && workflow.survey_response.video_upload_preference && (
                            <span className="text-sm text-gray-500">
                              (Prefers: {workflow.survey_response.video_upload_preference})
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Section 6: Final Feedback (Legacy fields) */}
                  {(workflow.survey_response.most_valued || workflow.survey_response.improvement_suggestions || workflow.survey_response.additional_comments) && (
                    <div className="space-y-4">
                      <h4 className="font-semibold text-gray-900 border-b pb-2">Final Feedback</h4>

                      {workflow.survey_response.most_valued && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">Most Valued</div>
                          <p className="text-gray-700">{workflow.survey_response.most_valued}</p>
                        </div>
                      )}

                      {workflow.survey_response.improvement_suggestions && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">Improvement Suggestions</div>
                          <p className="text-gray-700">{workflow.survey_response.improvement_suggestions}</p>
                        </div>
                      )}

                      {workflow.survey_response.additional_comments && (
                        <div>
                          <div className="text-sm font-medium text-gray-500 mb-1">Additional Comments</div>
                          <p className="text-gray-700">{workflow.survey_response.additional_comments}</p>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Testimonial */}
            {workflow.testimonial_received && workflow.testimonial_text && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Quote className="h-5 w-5 text-green-500" />
                    Testimonial Received
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <blockquote className="text-lg italic text-gray-700 border-l-4 border-green-500 pl-4">
                    "{workflow.testimonial_text}"
                  </blockquote>
                  {workflow.testimonial_author_name && (
                    <div className="mt-3 text-sm text-gray-500">
                      — {workflow.testimonial_author_name}
                    </div>
                  )}
                  {workflow.testimonial_permission_granted && (
                    <Badge className="mt-2 bg-green-100 text-green-800">
                      <Check className="h-3 w-3 mr-1" />
                      Permission granted to use publicly
                    </Badge>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Notes */}
            {workflow.notes && (
              <Card>
                <CardHeader>
                  <CardTitle>Notes</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 whitespace-pre-wrap">{workflow.notes}</p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Actions */}
            {workflow.status !== "completed" && workflow.status !== "cancelled" && (
              <Card>
                <CardHeader>
                  <CardTitle>Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => handleAction("send_completion")}
                    disabled={actionLoading !== null}
                  >
                    <Mail className="h-4 w-4 mr-2" />
                    Send Completion Email
                  </Button>

                  {workflow.send_survey && !workflow.survey_completed_at && (
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => handleAction("send_survey")}
                      disabled={actionLoading !== null}
                    >
                      <MessageSquare className="h-4 w-4 mr-2" />
                      Send Survey Request
                    </Button>
                  )}

                  {workflow.request_testimonial && !workflow.testimonial_received && (
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => handleAction("request_testimonial")}
                      disabled={actionLoading !== null}
                    >
                      <Quote className="h-4 w-4 mr-2" />
                      Request Testimonial
                    </Button>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Status Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Survey</span>
                  {workflow.send_survey ? (
                    workflow.survey_completed_at ? (
                      <Badge className="bg-green-100 text-green-800">
                        <Check className="h-3 w-3 mr-1" />
                        Completed
                      </Badge>
                    ) : (
                      <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>
                    )
                  ) : (
                    <Badge variant="outline">Not requested</Badge>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Testimonial</span>
                  {workflow.request_testimonial ? (
                    workflow.testimonial_received ? (
                      <Badge className="bg-green-100 text-green-800">
                        <Check className="h-3 w-3 mr-1" />
                        Received
                      </Badge>
                    ) : (
                      <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>
                    )
                  ) : (
                    <Badge variant="outline">Not requested</Badge>
                  )}
                </div>

                {workflow.related_project_title && (
                  <div className="pt-2 border-t">
                    <span className="text-sm text-gray-500">Related Project</span>
                    <Link
                      href={`/projects/${workflow.related_project_id}`}
                      className="block text-blue-600 hover:underline"
                    >
                      {workflow.related_project_title}
                    </Link>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Activity Log */}
            <Card>
              <CardHeader>
                <CardTitle>Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {activities.length === 0 ? (
                    <p className="text-gray-500 text-sm">No activity yet</p>
                  ) : (
                    activities.map((activity) => (
                      <div key={activity.id} className="flex gap-3 text-sm">
                        <div className="w-2 h-2 rounded-full bg-gray-400 mt-2 flex-shrink-0" />
                        <div>
                          <div className="text-gray-900">
                            {ACTION_LABELS[activity.action] || activity.action}
                          </div>
                          <div className="text-gray-500 text-xs">
                            {formatDate(activity.created_at)}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Contact Info */}
            <Card>
              <CardHeader>
                <CardTitle>Contact</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="font-medium">{workflow.contact_name}</div>
                  {workflow.contact_email && (
                    <div className="text-sm text-gray-500">{workflow.contact_email}</div>
                  )}
                  <Link href={`/contacts/${workflow.contact_id}`}>
                    <Button variant="link" className="p-0 h-auto text-blue-600">
                      View Contact
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Shell>
  );
}
