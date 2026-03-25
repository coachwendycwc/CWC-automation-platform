"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { ArrowLeft, Video, Clock, Calendar, XCircle } from "lucide-react";

interface Booking {
  id: string;
  booking_type_name: string;
  start_time: string;
  end_time: string;
  status: string;
  meeting_link: string | null;
  notes: string | null;
  can_cancel: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-warning/10 text-warning",
  confirmed: "bg-success/10 text-success",
  cancelled: "bg-destructive/10 text-destructive",
  completed: "bg-muted text-foreground",
  no_show: "bg-orange-100 text-warning",
};

export default function ClientBookingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { sessionToken } = useClientAuth();
  const bookingId = params.id as string;

  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    const loadBooking = async () => {
      if (!sessionToken || !bookingId) return;

      try {
        const data = await clientPortalApi.getBooking(sessionToken, bookingId);
        setBooking(data);
      } catch (error) {
        console.error("Failed to load booking:", error);
      } finally {
        setLoading(false);
      }
    };

    loadBooking();
  }, [sessionToken, bookingId]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  const handleCancel = async () => {
    if (!booking || !sessionToken) return;
    if (!confirm("Are you sure you want to cancel this booking?")) return;

    setCancelling(true);
    try {
      await clientPortalApi.cancelBooking(sessionToken, booking.id);
      toast.success("Booking cancelled successfully");
      router.push("/client/bookings");
    } catch (error: any) {
      toast.error(error.message || "Failed to cancel booking");
    } finally {
      setCancelling(false);
    }
  };

  const isUpcoming = booking
    ? new Date(booking.start_time) > new Date()
    : false;

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-9 w-20" />
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-40" />
          </div>
        </div>
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (!booking) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Booking not found</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/client/bookings">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{booking.booking_type_name}</h1>
              <Badge className={STATUS_COLORS[booking.status]}>
                {booking.status}
              </Badge>
            </div>
            <p className="text-muted-foreground">{formatDate(booking.start_time)}</p>
          </div>
        </div>

        <div className="flex gap-2">
          {booking.meeting_link && isUpcoming && (
            <a
              href={booking.meeting_link}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button>
                <Video className="h-4 w-4 mr-2" />
                Join Meeting
              </Button>
            </a>
          )}
          {booking.can_cancel && (
            <Button
              variant="outline"
              onClick={handleCancel}
              disabled={cancelling}
            >
              <XCircle className="h-4 w-4 mr-2" />
              {cancelling ? "Cancelling..." : "Cancel Booking"}
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Session Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-accent/10 rounded-lg">
                  <Calendar className="h-6 w-6 text-accent" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Date</p>
                  <p className="font-medium">{formatDate(booking.start_time)}</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="p-3 bg-primary/10 rounded-lg">
                  <Clock className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Time</p>
                  <p className="font-medium">
                    {formatTime(booking.start_time)} -{" "}
                    {formatTime(booking.end_time)}
                  </p>
                </div>
              </div>

              {booking.meeting_link && (
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-success/10 rounded-lg">
                    <Video className="h-6 w-6 text-success" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Meeting Link</p>
                    <a
                      href={booking.meeting_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-accent hover:underline"
                    >
                      {booking.meeting_link}
                    </a>
                  </div>
                </div>
              )}

              {booking.notes && (
                <div className="border-t pt-4">
                  <p className="text-sm text-muted-foreground mb-2">Notes</p>
                  <p className="text-foreground">{booking.notes}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {booking.meeting_link && isUpcoming && (
                <a
                  href={booking.meeting_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <Button className="w-full">
                    <Video className="h-4 w-4 mr-2" />
                    Join Meeting
                  </Button>
                </a>
              )}

              {booking.can_cancel ? (
                <Button
                  variant="outline"
                  className="w-full text-destructive hover:text-destructive hover:bg-destructive/5"
                  onClick={handleCancel}
                  disabled={cancelling}
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Cancel Booking
                </Button>
              ) : isUpcoming ? (
                <p className="text-sm text-muted-foreground text-center">
                  Cancellations must be made at least 24 hours in advance
                </p>
              ) : null}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
