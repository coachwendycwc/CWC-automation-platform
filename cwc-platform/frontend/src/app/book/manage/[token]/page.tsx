"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { toast } from "sonner";
import { publicBookingApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Calendar, Clock3, ExternalLink, MapPin, Video } from "lucide-react";
import type { PublicBookingResult, TimeSlot } from "@/types";

export default function ManageBookingPage() {
  const params = useParams();
  const [booking, setBooking] = useState<PublicBookingResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [selectedDate, setSelectedDate] = useState("");
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [rescheduling, setRescheduling] = useState(false);

  useEffect(() => {
    if (!params.token) return;
    void loadBooking(params.token as string);
  }, [params.token]);

  const loadBooking = async (token: string) => {
    try {
      const data = await publicBookingApi.getBookingByToken(token);
      setBooking(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load booking";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!params.token || !booking?.can_cancel) return;

    setCancelling(true);
    try {
      const updated = await publicBookingApi.cancelBooking(
        params.token as string,
        cancelReason.trim() || undefined
      );
      setBooking(updated);
      toast.success("Booking cancelled");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to cancel booking";
      toast.error(message);
    } finally {
      setCancelling(false);
    }
  };

  const loadSlots = async (date: string) => {
    if (!booking?.booking_type_slug) return;
    setLoadingSlots(true);
    try {
      const data = await publicBookingApi.getSlots(booking.booking_type_slug, date);
      setAvailableSlots(data.slots as TimeSlot[]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load available times";
      toast.error(message);
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleDateChange = async (value: string) => {
    setSelectedDate(value);
    if (!value) {
      setAvailableSlots([]);
      return;
    }
    await loadSlots(value);
  };

  const handleReschedule = async (startTime: string) => {
    if (!params.token || !booking?.can_reschedule) return;

    setRescheduling(true);
    try {
      const updated = await publicBookingApi.rescheduleBooking(params.token as string, startTime);
      setBooking(updated);
      setSelectedDate("");
      setAvailableSlots([]);
      toast.success("Booking rescheduled");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to reschedule booking";
      toast.error(message);
    } finally {
      setRescheduling(false);
    }
  };

  const formatDate = (value: string) =>
    new Date(value).toLocaleString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });

  const formatTime = (value: string) =>
    new Date(value).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f5f3ee] px-4 py-12">
        <div className="mx-auto max-w-3xl">
          <Skeleton className="h-80 rounded-[28px]" />
        </div>
      </div>
    );
  }

  if (!booking) {
    return (
      <div className="min-h-screen bg-[#f5f3ee] px-4 py-12">
        <div className="mx-auto max-w-2xl">
          <Card className="rounded-[28px] border-white/60 bg-white/90 shadow-sm">
            <CardContent className="space-y-4 px-8 py-10 text-center">
              <h1 className="text-2xl font-semibold text-slate-900">Booking not found</h1>
              <p className="text-sm text-slate-600">
                This booking link may be invalid or no longer available.
              </p>
              <Button variant="outline" asChild>
                <Link href="/">Return to home</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f5f3ee] px-4 py-12 text-slate-900">
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="space-y-2 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
            Manage booking
          </p>
          <h1 className="text-3xl font-semibold tracking-tight">
            {booking.booking_type_name}
          </h1>
          <p className="text-sm text-slate-600">
            Review your session details, access your meeting link, or cancel if your plans changed.
          </p>
        </div>

        <Card className="rounded-[28px] border-white/60 bg-white/90 shadow-sm">
          <CardHeader className="space-y-3 px-8 pt-8">
            <div className="flex flex-wrap items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
              <span className="rounded-full bg-slate-100 px-3 py-1">
                {booking.status.replace("_", " ")}
              </span>
              <span className="rounded-full bg-slate-100 px-3 py-1">
                {booking.booking_type_duration} min
              </span>
            </div>
            <CardTitle className="text-2xl font-semibold tracking-tight">
              Session details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6 px-8 pb-8">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                  <Calendar className="h-4 w-4" />
                  When
                </div>
                <p className="text-sm text-slate-600">{formatDate(booking.start_time)}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                  <Clock3 className="h-4 w-4" />
                  Format
                </div>
                <p className="text-sm capitalize text-slate-600">
                  {(booking.meeting_provider || "session").replace("_", " ")}
                </p>
              </div>
            </div>

            {booking.meeting_url && (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5">
                <div className="mb-2 flex items-center gap-2 text-sm font-medium text-emerald-900">
                  <Video className="h-4 w-4" />
                  Meeting link
                </div>
                <p className="mb-4 break-all text-sm text-emerald-800">{booking.meeting_url}</p>
                <Button asChild>
                  <a href={booking.meeting_url} target="_blank" rel="noreferrer">
                    Open meeting link
                    <ExternalLink className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            )}

            {!booking.meeting_url && booking.location_details && (
              <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-5">
                <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                  <MapPin className="h-4 w-4" />
                  Location details
                </div>
                <p className="whitespace-pre-wrap text-sm text-slate-600">
                  {booking.location_details}
                </p>
              </div>
            )}

            {booking.post_booking_instructions && (
              <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-5">
                <div className="mb-2 text-sm font-medium text-slate-700">
                  What happens next
                </div>
                <p className="whitespace-pre-wrap text-sm leading-6 text-slate-600">
                  {booking.post_booking_instructions}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="rounded-[28px] border-white/60 bg-white/90 shadow-sm">
          <CardHeader className="px-8 pt-8">
            <CardTitle className="text-xl font-semibold tracking-tight">
              Changes to your booking
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 px-8 pb-8">
            {booking.can_reschedule && booking.status !== "cancelled" && (
              <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50/80 p-5">
                <div>
                  <div className="mb-1 text-sm font-medium text-slate-800">Reschedule</div>
                  <p className="text-sm text-slate-600">
                    Pick a new date to see the currently available times for this session.
                  </p>
                </div>
                <Input
                  type="date"
                  value={selectedDate}
                  onChange={(event) => void handleDateChange(event.target.value)}
                  className="h-12 rounded-2xl border-slate-200 bg-white"
                />
                {loadingSlots ? (
                  <div className="grid grid-cols-2 gap-3">
                    {Array.from({ length: 4 }).map((_, index) => (
                      <Skeleton key={index} className="h-11 rounded-2xl" />
                    ))}
                  </div>
                ) : availableSlots.length > 0 ? (
                  <div className="grid grid-cols-2 gap-3">
                    {availableSlots.map((slot) => (
                      <Button
                        key={slot.start_time}
                        variant="outline"
                        className="justify-center rounded-2xl"
                        disabled={rescheduling}
                        onClick={() => void handleReschedule(slot.start_time)}
                      >
                        {rescheduling ? "Updating..." : formatTime(slot.start_time)}
                      </Button>
                    ))}
                  </div>
                ) : selectedDate ? (
                  <p className="text-sm text-slate-500">
                    No available times on that date.
                  </p>
                ) : null}
              </div>
            )}

            {booking.can_cancel ? (
              <>
                <p className="text-sm text-slate-600">
                  If you cannot make this session, cancel here so the time opens back up.
                </p>
                <Textarea
                  value={cancelReason}
                  onChange={(event) => setCancelReason(event.target.value)}
                  placeholder="Optional cancellation reason"
                  className="min-h-[120px] rounded-2xl border-slate-200 bg-slate-50/70"
                />
                <Button
                  variant="destructive"
                  onClick={handleCancel}
                  disabled={cancelling}
                >
                  {cancelling ? "Cancelling..." : "Cancel booking"}
                </Button>
              </>
            ) : (
              <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-5 text-sm text-slate-600">
                {booking.status === "cancelled"
                  ? "This booking has already been cancelled."
                  : "This booking can no longer be changed online."}
              </div>
            )}
            <Button variant="outline" asChild>
              <Link href="/">Done</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
