"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { toast } from "sonner";
import {
  ArrowLeft,
  Calendar,
  Check,
  Clock,
  Link2,
  Mail,
  MapPin,
  Phone,
  User,
  Video,
  X,
} from "lucide-react";
import { Shell } from "@/components/layout/Shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { bookingsApi } from "@/lib/api";
import { BookingWithDetails } from "@/types";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-warning/10 text-warning",
  confirmed: "bg-success/10 text-success",
  completed: "bg-primary/10 text-primary",
  cancelled: "bg-destructive/10 text-destructive",
  no_show: "bg-muted text-foreground",
};

function getMeetingLabel(booking: BookingWithDetails) {
  switch (booking.meeting_provider) {
    case "zoom":
      return "Zoom";
    case "google_meet":
      return "Google Meet";
    case "phone":
      return "Phone";
    case "in_person":
      return "In person";
    case "custom":
      return "Custom link";
    default:
      return booking.booking_type.location_type === "custom"
        ? "Custom location"
        : "Meeting details";
  }
}

function getMeetingIcon(booking: BookingWithDetails) {
  switch (booking.meeting_provider ?? booking.booking_type.location_type) {
    case "phone":
      return Phone;
    case "in_person":
      return MapPin;
    case "custom":
      return Link2;
    default:
      return Video;
  }
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function formatTime(dateString: string) {
  return new Date(dateString).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return "Something went wrong";
}

export default function BookingDetailPage() {
  const params = useParams();
  const bookingId = params.id as string;

  const [booking, setBooking] = useState<BookingWithDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const loadBooking = async () => {
    const token = localStorage.getItem("token");
    if (!token || !bookingId) {
      setLoading(false);
      return;
    }

    try {
      const data = await bookingsApi.get(token, bookingId);
      setBooking(data);
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadBooking();
  }, [bookingId]);

  const handleConfirm = async () => {
    const token = localStorage.getItem("token");
    if (!token || !booking) return;

    setSubmitting(true);
    try {
      const updated = await bookingsApi.confirm(token, booking.id);
      setBooking(updated);
      toast.success("Booking confirmed");
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async () => {
    const token = localStorage.getItem("token");
    if (!token || !booking) return;

    const reason = window.prompt("Enter cancellation reason (optional):");
    if (reason === null) return;

    setSubmitting(true);
    try {
      const updated = await bookingsApi.cancel(token, booking.id, reason);
      setBooking(updated);
      toast.success("Booking cancelled");
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Shell>
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Skeleton className="h-9 w-24" />
            <div className="space-y-2">
              <Skeleton className="h-8 w-64" />
              <Skeleton className="h-4 w-40" />
            </div>
          </div>
          <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
            <Skeleton className="h-96 w-full rounded-2xl" />
            <Skeleton className="h-64 w-full rounded-2xl" />
          </div>
        </div>
      </Shell>
    );
  }

  if (!booking) {
    return (
      <Shell>
        <Card>
          <CardContent className="py-16 text-center">
            <p className="text-muted-foreground">Booking not found.</p>
          </CardContent>
        </Card>
      </Shell>
    );
  }

  const MeetingIcon = getMeetingIcon(booking);
  const intakeEntries = Object.entries(booking.intake_responses ?? {});
  const meetingDetails = booking.meeting_url ?? booking.booking_type.location_details;

  return (
    <Shell>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Link href="/bookings">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
            </Link>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-foreground">{booking.booking_type.name}</h1>
                <Badge className={STATUS_COLORS[booking.status]}>{booking.status}</Badge>
              </div>
              <p className="text-muted-foreground">{formatDate(booking.start_time)}</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {booking.meeting_url && (
              <a href={booking.meeting_url} target="_blank" rel="noreferrer">
                <Button variant="outline">
                  <MeetingIcon className="mr-2 h-4 w-4" />
                  Open Link
                </Button>
              </a>
            )}
            {booking.status === "pending" && (
              <>
                <Button onClick={handleConfirm} disabled={submitting}>
                  <Check className="mr-2 h-4 w-4" />
                  Confirm
                </Button>
                <Button variant="outline" onClick={handleCancel} disabled={submitting}>
                  <X className="mr-2 h-4 w-4" />
                  Decline
                </Button>
              </>
            )}
            {booking.status === "confirmed" && (
              <Button variant="outline" onClick={handleCancel} disabled={submitting}>
                <X className="mr-2 h-4 w-4" />
                Cancel
              </Button>
            )}
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Session Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-xl border border-border bg-background p-4">
                    <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                      <Calendar className="h-4 w-4" />
                      Date
                    </div>
                    <p className="font-medium text-foreground">{formatDate(booking.start_time)}</p>
                  </div>
                  <div className="rounded-xl border border-border bg-background p-4">
                    <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      Time
                    </div>
                    <p className="font-medium text-foreground">
                      {formatTime(booking.start_time)} - {formatTime(booking.end_time)}
                    </p>
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-background p-4">
                  <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                    <MeetingIcon className="h-4 w-4" />
                    {getMeetingLabel(booking)}
                  </div>
                  {meetingDetails ? (
                    booking.meeting_url ? (
                      <a
                        href={booking.meeting_url}
                        target="_blank"
                        rel="noreferrer"
                        className="break-all font-medium text-primary hover:underline"
                      >
                        {booking.meeting_url}
                      </a>
                    ) : (
                      <p className="whitespace-pre-wrap text-foreground">{meetingDetails}</p>
                    )
                  ) : (
                    <p className="text-muted-foreground">Meeting details will appear here once confirmed.</p>
                  )}
                </div>

                {booking.booking_type.description && (
                  <div className="rounded-xl border border-border bg-background p-4">
                    <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                      Call Description
                    </h2>
                    <p className="whitespace-pre-wrap text-foreground">{booking.booking_type.description}</p>
                  </div>
                )}

                {booking.booking_type.post_booking_instructions && (
                  <div className="rounded-xl border border-border bg-background p-4">
                    <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                      Booking Instructions
                    </h2>
                    <p className="whitespace-pre-wrap text-foreground">
                      {booking.booking_type.post_booking_instructions}
                    </p>
                  </div>
                )}

                {intakeEntries.length > 0 && (
                  <div className="rounded-xl border border-border bg-background p-4">
                    <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                      Intake Responses
                    </h2>
                    <div className="space-y-4">
                      {intakeEntries.map(([questionId, response]) => {
                        const question = booking.booking_type.intake_questions.find(
                          (item) => item.id === questionId
                        );

                        return (
                          <div key={questionId} className="border-b border-border pb-4 last:border-b-0 last:pb-0">
                            <p className="text-sm font-medium text-foreground">
                              {question?.label ?? questionId}
                            </p>
                            <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground">
                              {response}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {booking.notes && (
                  <div className="rounded-xl border border-border bg-background p-4">
                    <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                      Internal Notes
                    </h2>
                    <p className="whitespace-pre-wrap text-foreground">{booking.notes}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Client</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="rounded-full bg-primary/10 p-2 text-primary">
                    <User className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">
                      {booking.contact.first_name} {booking.contact.last_name ?? ""}
                    </p>
                    <p className="text-sm text-muted-foreground capitalize">
                      {booking.contact.contact_type}
                    </p>
                  </div>
                </div>

                {booking.contact.email && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Mail className="h-4 w-4" />
                    <span>{booking.contact.email}</span>
                  </div>
                )}

                {booking.contact.phone && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Phone className="h-4 w-4" />
                    <span>{booking.contact.phone}</span>
                  </div>
                )}

                <Link href={`/contacts/${booking.contact_id}`} className="block">
                  <Button variant="outline" className="w-full">
                    Open Contact
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Booking Metadata</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex items-center justify-between gap-4">
                  <span className="text-muted-foreground">Booking Type</span>
                  <span className="text-right font-medium text-foreground">{booking.booking_type.name}</span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span className="text-muted-foreground">Duration</span>
                  <span className="text-right font-medium text-foreground">
                    {booking.booking_type.duration_minutes} minutes
                  </span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span className="text-muted-foreground">Provider</span>
                  <span className="text-right font-medium text-foreground">
                    {getMeetingLabel(booking)}
                  </span>
                </div>
                {booking.google_event_id && (
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-muted-foreground">Calendar Sync</span>
                    <span className="text-right font-medium text-foreground">Connected</span>
                  </div>
                )}
                {booking.cancellation_reason && (
                  <div className="border-t border-border pt-3">
                    <p className="mb-1 text-muted-foreground">Cancellation Reason</p>
                    <p className="whitespace-pre-wrap text-foreground">{booking.cancellation_reason}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Shell>
  );
}
