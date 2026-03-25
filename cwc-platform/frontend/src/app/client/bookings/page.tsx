"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { Calendar, ExternalLink, Video, Clock } from "lucide-react";

interface Booking {
  id: string;
  booking_type_name: string;
  start_time: string;
  end_time: string;
  status: string;
  meeting_link: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-warning/10 text-warning",
  confirmed: "bg-success/10 text-success",
  cancelled: "bg-destructive/10 text-destructive",
  completed: "bg-muted text-foreground",
  no_show: "bg-orange-100 text-warning",
};

export default function ClientBookingsPage() {
  const { sessionToken } = useClientAuth();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpcoming, setShowUpcoming] = useState(true);

  useEffect(() => {
    const loadBookings = async () => {
      if (!sessionToken) return;

      try {
        const data = await clientPortalApi.listBookings(
          sessionToken,
          showUpcoming
        );
        setBookings(data);
      } catch (error) {
        console.error("Failed to load bookings:", error);
      } finally {
        setLoading(false);
      }
    };

    loadBookings();
  }, [sessionToken, showUpcoming]);

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

  const isUpcoming = (dateString: string) => {
    return new Date(dateString) > new Date();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Bookings</h1>
          <p className="text-muted-foreground">Your upcoming and past sessions</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <Button
          variant={showUpcoming ? "default" : "outline"}
          size="sm"
          onClick={() => setShowUpcoming(true)}
        >
          Upcoming
        </Button>
        <Button
          variant={!showUpcoming ? "default" : "outline"}
          size="sm"
          onClick={() => setShowUpcoming(false)}
        >
          All
        </Button>
      </div>

      {bookings.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Calendar className="h-12 w-12 text-muted-foreground/40 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground">No bookings</h3>
            <p className="text-muted-foreground">
              {showUpcoming
                ? "You don't have any upcoming sessions"
                : "You don't have any sessions yet"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {bookings.map((booking) => {
            const upcoming = isUpcoming(booking.start_time);

            return (
              <Card
                key={booking.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
              >
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div
                        className={`p-2 rounded-lg ${
                          upcoming ? "bg-accent/10" : "bg-muted"
                        }`}
                      >
                        <Clock
                          className={`h-5 w-5 ${
                            upcoming ? "text-accent" : "text-muted-foreground"
                          }`}
                        />
                      </div>
                      <div>
                        <p className="font-medium">{booking.booking_type_name}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatDate(booking.start_time)} at{" "}
                          {formatTime(booking.start_time)} -{" "}
                          {formatTime(booking.end_time)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <Badge className={STATUS_COLORS[booking.status]}>
                        {booking.status}
                      </Badge>

                      {booking.meeting_link && upcoming && (
                        <a
                          href={booking.meeting_link}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <Button size="sm">
                            <Video className="h-4 w-4 mr-2" />
                            Join
                          </Button>
                        </a>
                      )}

                      <Link href={`/client/bookings/${booking.id}`}>
                        <Button variant="outline" size="sm">
                          Details
                          <ExternalLink className="ml-2 h-4 w-4" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
