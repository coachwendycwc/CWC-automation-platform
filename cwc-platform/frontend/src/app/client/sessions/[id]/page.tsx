"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Link from "next/link";
import { toast } from "sonner";
import {
  ArrowLeft,
  Video,
  FileText,
  CheckSquare,
  Clock,
  Play,
  ListChecks,
  Sparkles,
} from "lucide-react";

interface HomeworkItem {
  description: string;
  completed: boolean;
}

interface SessionDetail {
  id: string;
  meeting_title: string | null;
  recorded_at: string | null;
  duration_seconds: number | null;
  recording_url: string | null;
  transcript: string | null;
  summary: any;
  action_items: string[] | null;
  homework: HomeworkItem[] | null;
}

export default function ClientSessionDetailPage() {
  const params = useParams();
  const { sessionToken } = useClientAuth();
  const sessionId = params.id as string;

  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatingHomework, setUpdatingHomework] = useState<number | null>(null);

  useEffect(() => {
    const loadSession = async () => {
      if (!sessionToken || !sessionId) return;

      try {
        const data = await clientPortalApi.getSession(sessionToken, sessionId);
        setSession(data);
      } catch (error) {
        console.error("Failed to load session:", error);
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, [sessionToken, sessionId]);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Unknown date";
    return new Date(dateString).toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minutes`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours} hour${hours > 1 ? "s" : ""} ${remainingMinutes} minutes`;
  };

  const handleHomeworkToggle = async (index: number, completed: boolean) => {
    if (!sessionToken || !session) return;

    setUpdatingHomework(index);
    try {
      await clientPortalApi.updateHomeworkStatus(sessionToken, sessionId, index, completed);

      // Update local state
      const updatedHomework = [...(session.homework || [])];
      updatedHomework[index] = { ...updatedHomework[index], completed };
      setSession({ ...session, homework: updatedHomework });

      toast.success(completed ? "Homework marked as complete!" : "Homework marked as incomplete");
    } catch (error) {
      console.error("Failed to update homework:", error);
      toast.error("Failed to update homework status");
    } finally {
      setUpdatingHomework(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading session...</div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Session not found</div>
      </div>
    );
  }

  const completedHomework = session.homework?.filter((h) => h.completed).length || 0;
  const totalHomework = session.homework?.length || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/client/sessions">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">
            {session.meeting_title || "Coaching Session"}
          </h1>
          <div className="flex items-center gap-3 text-gray-500">
            <span>{formatDate(session.recorded_at)}</span>
            {session.duration_seconds && (
              <>
                <span>&middot;</span>
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {formatDuration(session.duration_seconds)}
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Video Player */}
      {session.recording_url && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Video className="h-5 w-5" />
              Session Recording
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
              <a
                href={session.recording_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col items-center gap-3 text-white hover:text-purple-300 transition-colors"
              >
                <div className="p-4 bg-purple-600 rounded-full">
                  <Play className="h-8 w-8" />
                </div>
                <span className="text-lg font-medium">Watch Recording</span>
              </a>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs for Content */}
      <Tabs defaultValue={session.homework?.length ? "homework" : "summary"} className="space-y-4">
        <TabsList>
          {session.summary && (
            <TabsTrigger value="summary" className="flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              Summary
            </TabsTrigger>
          )}
          {session.homework && session.homework.length > 0 && (
            <TabsTrigger value="homework" className="flex items-center gap-2">
              <CheckSquare className="h-4 w-4" />
              Homework ({completedHomework}/{totalHomework})
            </TabsTrigger>
          )}
          {session.action_items && session.action_items.length > 0 && (
            <TabsTrigger value="actions" className="flex items-center gap-2">
              <ListChecks className="h-4 w-4" />
              Action Items
            </TabsTrigger>
          )}
          {session.transcript && (
            <TabsTrigger value="transcript" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Transcript
            </TabsTrigger>
          )}
        </TabsList>

        {/* Summary Tab */}
        {session.summary && (
          <TabsContent value="summary">
            <Card>
              <CardHeader>
                <CardTitle>Session Summary</CardTitle>
              </CardHeader>
              <CardContent className="prose prose-sm max-w-none">
                {typeof session.summary === "string" ? (
                  <p className="whitespace-pre-wrap">{session.summary}</p>
                ) : (
                  <div className="space-y-4">
                    {session.summary.overview && (
                      <div>
                        <h4 className="font-semibold text-gray-900">Overview</h4>
                        <p className="text-gray-700">{session.summary.overview}</p>
                      </div>
                    )}
                    {session.summary.key_points && (
                      <div>
                        <h4 className="font-semibold text-gray-900">Key Points</h4>
                        <ul className="list-disc pl-5 space-y-1">
                          {session.summary.key_points.map((point: string, i: number) => (
                            <li key={i} className="text-gray-700">{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {session.summary.insights && (
                      <div>
                        <h4 className="font-semibold text-gray-900">Insights</h4>
                        <p className="text-gray-700">{session.summary.insights}</p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Homework Tab */}
        {session.homework && session.homework.length > 0 && (
          <TabsContent value="homework">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Homework & To-Dos</span>
                  <span className="text-sm font-normal text-gray-500">
                    {completedHomework} of {totalHomework} completed
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {session.homework.map((item, index) => (
                    <div
                      key={index}
                      className={`flex items-start gap-3 p-4 rounded-lg border ${
                        item.completed
                          ? "bg-green-50 border-green-200"
                          : "bg-white border-gray-200"
                      }`}
                    >
                      <Checkbox
                        checked={item.completed}
                        disabled={updatingHomework === index}
                        onCheckedChange={(checked) =>
                          handleHomeworkToggle(index, checked as boolean)
                        }
                        className="mt-0.5"
                      />
                      <span
                        className={`flex-1 ${
                          item.completed ? "text-gray-500 line-through" : "text-gray-900"
                        }`}
                      >
                        {item.description}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Action Items Tab */}
        {session.action_items && session.action_items.length > 0 && (
          <TabsContent value="actions">
            <Card>
              <CardHeader>
                <CardTitle>Action Items</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {session.action_items.map((item, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg"
                    >
                      <CheckSquare className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Transcript Tab */}
        {session.transcript && (
          <TabsContent value="transcript">
            <Card>
              <CardHeader>
                <CardTitle>Full Transcript</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700 bg-gray-50 p-4 rounded-lg max-h-[600px] overflow-y-auto">
                    {session.transcript}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      {/* Empty State */}
      {!session.recording_url && !session.summary && !session.transcript && !session.homework?.length && (
        <Card>
          <CardContent className="py-12 text-center">
            <Video className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">Session content pending</h3>
            <p className="text-gray-500">
              The recording and transcript for this session are still being processed.
              Check back soon!
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
