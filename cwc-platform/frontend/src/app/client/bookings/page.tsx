"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
  pending: "bg-yellow-100 text-yellow-800",
  confirmed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
  completed: "bg-gray-100 text-gray-800",
  no_show: "bg-orange-100 text-orange-800",
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
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading bookings...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Bookings</h1>
          <p className="text-gray-500">Your upcoming and past sessions</p>
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
            <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No bookings</h3>
            <p className="text-gray-500">
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
                className="hover:shadow-md transition-shadow"
              >
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div
                        className={`p-2 rounded-lg ${
                          upcoming ? "bg-purple-100" : "bg-gray-100"
                        }`}
                      >
                        <Clock
                          className={`h-5 w-5 ${
                            upcoming ? "text-purple-600" : "text-gray-500"
                          }`}
                        />
                      </div>
                      <div>
                        <p className="font-medium">{booking.booking_type_name}</p>
                        <p className="text-sm text-gray-500">
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
