"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { publicBookingApi } from "@/lib/api";
import { TimeSlot } from "@/types";
import { Calendar, Clock, Check, X, AlertTriangle, ChevronLeft, ChevronRight } from "lucide-react";

interface BookingInfo {
  id: string;
  start_time: string;
  end_time: string;
  status: string;
  booking_type_name: string;
  booking_type_duration: number;
  can_cancel: boolean;
  can_reschedule: boolean;
}

export default function ManageBookingPage() {
  const params = useParams();
  const token = params.token as string;

  const [booking, setBooking] = useState<BookingInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Reschedule state
  const [showReschedule, setShowReschedule] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Cancel state
  const [showCancel, setShowCancel] = useState(false);
  const [cancelReason, setCancelReason] = useState("");

  useEffect(() => {
    loadBooking();
  }, [token]);

  const loadBooking = async () => {
    try {
      const data = await publicBookingApi.getBookingByToken(token);
      setBooking(data);
    } catch (err: any) {
      setError(err.message || "Booking not found");
    } finally {
      setLoading(false);
    }
  };

  const loadSlots = async (date: Date) => {
    if (!booking) return;
    setLoadingSlots(true);
    setSelectedSlot(null);
    try {
      // We need the slug from the booking type - for now use a workaround
      // The API would need to return the slug or we'd need another endpoint
      const dateStr = date.toISOString().split("T")[0];
      // For this demo, we'll show a message about needing to contact support
      setSlots([]);
    } catch (err) {
      setSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleReschedule = async () => {
    if (!selectedSlot) return;
    setSubmitting(true);
    setError("");

    try {
      await publicBookingApi.rescheduleBooking(token, selectedSlot.start_time);
      await loadBooking();
      setShowReschedule(false);
      setSelectedDate(null);
      setSelectedSlot(null);
    } catch (err: any) {
      setError(err.message || "Failed to reschedule");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async () => {
    setSubmitting(true);
    setError("");

    try {
      await publicBookingApi.cancelBooking(token, cancelReason || undefined);
      await loadBooking();
      setShowCancel(false);
      setCancelReason("");
    } catch (err: any) {
      setError(err.message || "Failed to cancel");
    } finally {
      setSubmitting(false);
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const STATUS_STYLES: Record<string, { bg: string; text: string; icon: any }> = {
    pending: { bg: "bg-warning/10", text: "text-warning", icon: Clock },
    confirmed: { bg: "bg-success/10", text: "text-success", icon: Check },
    completed: { bg: "bg-primary/10", text: "text-primary", icon: Check },
    cancelled: { bg: "bg-destructive/10", text: "text-destructive", icon: X },
    no_show: { bg: "bg-muted", text: "text-muted-foreground", icon: X },
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center">
        <div className="max-w-lg w-full mx-auto px-4 space-y-4">
          <Skeleton className="h-48 rounded-lg" />
          <Skeleton className="h-12 rounded-lg" />
        </div>
      </div>
    );
  }

  if (error && !booking) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="py-8 text-center">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-foreground mb-2">Booking Not Found</h2>
            <p className="text-muted-foreground">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!booking) return null;

  const statusStyle = STATUS_STYLES[booking.status] || STATUS_STYLES.pending;
  const StatusIcon = statusStyle.icon;

  return (
    <div className="min-h-screen bg-muted py-8 px-4">
      <div className="max-w-lg mx-auto">
        {/* Booking Details */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Your Booking</CardTitle>
              <Badge className={`${statusStyle.bg} ${statusStyle.text}`}>
                <StatusIcon className="h-3 w-3 mr-1" />
                {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <Calendar className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">{booking.booking_type_name}</h3>
                <p className="text-muted-foreground">{formatDateTime(booking.start_time)}</p>
                <p className="text-sm text-muted-foreground">
                  {booking.booking_type_duration} minutes
                </p>
              </div>
            </div>

            {error && (
              <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">{error}</div>
            )}

            {/* Action buttons */}
            {booking.status !== "cancelled" && booking.status !== "completed" && (
              <div className="flex gap-3 pt-4 border-t">
                {booking.can_reschedule && (
                  <Button
                    variant="outline"
                    onClick={() => setShowReschedule(true)}
                    disabled={showReschedule}
                    className="flex-1 cursor-pointer"
                  >
                    Reschedule
                  </Button>
                )}
                {booking.can_cancel && (
                  <Button
                    variant="outline"
                    onClick={() => setShowCancel(true)}
                    disabled={showCancel}
                    className="flex-1 text-destructive border-destructive hover:bg-destructive/10 cursor-pointer"
                  >
                    Cancel
                  </Button>
                )}
              </div>
            )}

            {!booking.can_cancel && !booking.can_reschedule && booking.status === "confirmed" && (
              <div className="pt-4 border-t">
                <p className="text-sm text-muted-foreground text-center">
                  Changes cannot be made less than 24 hours before the appointment.
                  Please contact us directly if you need to make changes.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Cancel Confirmation */}
        {showCancel && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-destructive">Cancel Booking</CardTitle>
              <CardDescription>
                Are you sure you want to cancel this booking?
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Reason (optional)
                </label>
                <textarea
                  className="w-full rounded-md border border-border px-3 py-2 text-sm"
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  rows={3}
                  placeholder="Let us know why you're cancelling..."
                />
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={handleCancel}
                  disabled={submitting}
                  className="bg-destructive hover:bg-destructive/90 cursor-pointer"
                >
                  {submitting ? "Cancelling..." : "Yes, Cancel Booking"}
                </Button>
                <Button
                  variant="outline"
                  className="cursor-pointer"
                  onClick={() => {
                    setShowCancel(false);
                    setCancelReason("");
                  }}
                >
                  Keep Booking
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Reschedule UI */}
        {showReschedule && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Reschedule Booking</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="cursor-pointer"
                  onClick={() => {
                    setShowReschedule(false);
                    setSelectedDate(null);
                    setSelectedSlot(null);
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <CardDescription>Select a new date and time for your appointment</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Calendar className="h-12 w-12 mx-auto mb-4 text-muted-foreground/40" />
                <p className="mb-4">
                  To reschedule your appointment, please contact us directly or book a new appointment and cancel this one.
                </p>
                <p className="text-sm">
                  This feature will be fully available soon.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Help text */}
        <p className="text-center text-sm text-muted-foreground mt-6">
          Need help? Contact us at support@example.com
        </p>
      </div>
    </div>
  );
}
