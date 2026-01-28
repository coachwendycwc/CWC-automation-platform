"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { Video, FileText, CheckSquare, Clock, ExternalLink, Calendar, ArrowRight, User } from "lucide-react";

interface SessionRecording {
  id: string;
  meeting_title: string | null;
  recorded_at: string | null;
  duration_seconds: number | null;
  has_recording: boolean;
  has_transcript: boolean;
  has_summary: boolean;
  has_homework: boolean;
  contact_name: string | null;
}

interface Booking {
  id: string;
  booking_type_name: string;
  start_time: string;
  end_time: string;
  status: string;
  meeting_link: string | null;
}

export default function ClientSessionsPage() {
  const { sessionToken } = useClientAuth();
  const [recordings, setRecordings] = useState<SessionRecording[]>([]);
  const [upcomingBookings, setUpcomingBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"upcoming" | "past">("upcoming");

  useEffect(() => {
    const loadData = async () => {
      if (!sessionToken) return;

      try {
        const [recordingsData, bookingsData] = await Promise.all([
          clientPortalApi.getSessions(sessionToken),
          clientPortalApi.listBookings(sessionToken, true), // upcoming only
        ]);
        setRecordings(recordingsData);
        setUpcomingBookings(bookingsData);

        // Default to "past" if no upcoming but has recordings
        if (bookingsData.length === 0 && recordingsData.length > 0) {
          setActiveTab("past");
        }
      } catch (error) {
        console.error("Failed to load sessions:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [sessionToken]);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Unknown date";
    return new Date(dateString).toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Sessions</h1>
        <p className="text-gray-500 mt-1">Upcoming sessions, recordings, transcripts, and homework</p>
      </div>

      {/* Tab Switcher */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab("upcoming")}
          className={`px-4 py-2 text-sm font-medium rounded-full transition-all ${
            activeTab === "upcoming"
              ? "bg-gray-900 text-white"
              : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"
          }`}
        >
          Upcoming
          {upcomingBookings.length > 0 && (
            <span className="ml-2 px-2 py-0.5 text-xs bg-white/20 rounded-full">
              {upcomingBookings.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab("past")}
          className={`px-4 py-2 text-sm font-medium rounded-full transition-all ${
            activeTab === "past"
              ? "bg-gray-900 text-white"
              : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"
          }`}
        >
          Past
          {recordings.length > 0 && (
            <span className="ml-2 px-2 py-0.5 text-xs bg-white/20 rounded-full">
              {recordings.length}
            </span>
          )}
        </button>
      </div>

      {/* Upcoming Sessions */}
      {activeTab === "upcoming" && (
        <div className="space-y-3">
          {upcomingBookings.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="py-12 text-center">
                <Calendar className="h-10 w-10 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No upcoming sessions</p>
              </CardContent>
            </Card>
          ) : (
            upcomingBookings.map((booking) => (
              <Card key={booking.id} className="hover:shadow-md transition-shadow">
                <CardContent className="py-5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="text-center min-w-[60px]">
                        <p className="text-2xl font-semibold text-gray-900">
                          {new Date(booking.start_time).getDate()}
                        </p>
                        <p className="text-xs text-gray-500 uppercase">
                          {new Date(booking.start_time).toLocaleDateString("en-US", { month: "short" })}
                        </p>
                      </div>
                      <div className="h-12 w-px bg-gray-200" />
                      <div>
                        <p className="font-medium text-gray-900">{booking.booking_type_name}</p>
                        <p className="text-sm text-gray-500">
                          {formatTime(booking.start_time)} - {formatTime(booking.end_time)}
                        </p>
                      </div>
                    </div>
                    {booking.meeting_link && (
                      <a
                        href={booking.meeting_link}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Button size="sm">
                          Join
                          <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                      </a>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Past Sessions / Recordings */}
      {activeTab === "past" && (
        <div className="space-y-3">
          {recordings.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="py-12 text-center">
                <Video className="h-10 w-10 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No session recordings yet</p>
              </CardContent>
            </Card>
          ) : (
            recordings.map((session) => (
              <Card key={session.id} className="hover:shadow-md transition-shadow">
                <CardContent className="py-5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="p-2.5 bg-gray-100 rounded-xl">
                        <Video className="h-5 w-5 text-gray-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          {session.meeting_title || "Coaching Session"}
                        </p>
                        <div className="flex items-center gap-3 text-sm text-gray-500">
                          <span>{formatDate(session.recorded_at)}</span>
                          {session.duration_seconds && (
                            <>
                              <span className="text-gray-300">·</span>
                              <span>{formatDuration(session.duration_seconds)}</span>
                            </>
                          )}
                          {session.contact_name && (
                            <>
                              <span className="text-gray-300">·</span>
                              <span className="flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {session.contact_name}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="flex gap-1.5">
                        {session.has_transcript && (
                          <div className="p-1.5 bg-blue-50 rounded-lg" title="Transcript available">
                            <FileText className="h-4 w-4 text-blue-500" />
                          </div>
                        )}
                        {session.has_homework && (
                          <div className="p-1.5 bg-green-50 rounded-lg" title="Homework assigned">
                            <CheckSquare className="h-4 w-4 text-green-500" />
                          </div>
                        )}
                      </div>
                      <Link href={`/client/sessions/${session.id}`}>
                        <Button variant="ghost" size="sm">
                          View
                          <ArrowRight className="ml-1 h-4 w-4" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}
