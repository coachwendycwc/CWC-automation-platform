"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { bookingsApi, bookingTypesApi } from "@/lib/api";
import { BookingWithDetails, BookingType } from "@/types";
import { formatDate } from "@/lib/utils";
import { Calendar, Clock, User, Check, X, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-warning/10 text-warning",
  confirmed: "bg-success/10 text-success",
  completed: "bg-primary/10 text-primary",
  cancelled: "bg-destructive/10 text-destructive",
  no_show: "bg-muted text-foreground",
};

export default function BookingsPage() {
  const [bookings, setBookings] = useState<BookingWithDetails[]>([]);
  const [bookingTypes, setBookingTypes] = useState<BookingType[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");

  useEffect(() => {
    loadData();
  }, [filter, startDate, endDate]);

  const loadData = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const [bookingsResponse, typesResponse] = await Promise.all([
        bookingsApi.list(token, {
          status: filter || undefined,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
        }),
        bookingTypesApi.list(token),
      ]);

      setBookings(bookingsResponse.items);
      setBookingTypes(typesResponse.items);
    } catch (err) {
      console.error("Failed to load bookings:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (id: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await bookingsApi.confirm(token, id);
      toast.success("Booking confirmed");
      await loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to confirm booking");
    }
  };

  const handleCancel = async (id: string) => {
    const reason = prompt("Enter cancellation reason (optional):");
    if (reason === null) return; // User clicked cancel

    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await bookingsApi.cancel(token, id, reason);
      toast.success("Booking cancelled");
      await loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to cancel booking");
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const formatDateDisplay = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  };

  // Group bookings by date
  const groupedBookings = bookings.reduce<Record<string, BookingWithDetails[]>>((acc, booking) => {
    const date = booking.start_time.split("T")[0];
    if (!acc[date]) acc[date] = [];
    acc[date].push(booking);
    return acc;
  }, {});

  if (loading) {
    return (
      <Shell>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-10 w-44" />
          </div>
          <Skeleton className="h-20 w-full" />
          <div className="space-y-4">
            <Skeleton className="h-5 w-24" />
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Bookings</h1>
            <p className="text-muted-foreground">View and manage your appointments</p>
          </div>
          <Link href="/settings/booking-types">
            <Button variant="outline">Manage Booking Types</Button>
          </Link>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="py-4">
            <div className="flex flex-wrap gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Status</label>
                <select
                  className="rounded-md border border-border px-3 py-2 text-sm"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                >
                  <option value="">All statuses</option>
                  <option value="pending">Pending</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="no_show">No Show</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">From</label>
                <input
                  type="date"
                  className="rounded-md border border-border px-3 py-2 text-sm"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">To</label>
                <input
                  type="date"
                  className="rounded-md border border-border px-3 py-2 text-sm"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
              {(filter || startDate || endDate) && (
                <div className="flex items-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setFilter("");
                      setStartDate("");
                      setEndDate("");
                    }}
                  >
                    Clear filters
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Bookings List */}
        {bookings.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No bookings found</h3>
              <p className="text-muted-foreground">
                {filter || startDate || endDate
                  ? "Try adjusting your filters"
                  : "Share your booking links to start receiving appointments"}
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedBookings)
              .sort(([a], [b]) => new Date(b).getTime() - new Date(a).getTime())
              .map(([date, dateBookings]) => (
                <div key={date}>
                  <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
                    {formatDateDisplay(date + "T00:00:00")}
                  </h3>
                  <div className="space-y-3">
                    {dateBookings
                      .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
                      .map((booking) => (
                        <Card key={booking.id} className="overflow-hidden">
                          <div className="flex">
                            <div
                              className="w-2"
                              style={{ backgroundColor: booking.booking_type.color }}
                            />
                            <div className="flex-1 p-4">
                              <div className="flex items-start justify-between">
                                <div className="flex items-start gap-4">
                                  <div className="text-center min-w-[60px]">
                                    <div className="text-lg font-semibold text-foreground">
                                      {formatTime(booking.start_time)}
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                      {booking.booking_type.duration_minutes}min
                                    </div>
                                  </div>
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <span className="font-medium text-foreground">
                                        {booking.contact.first_name} {booking.contact.last_name || ""}
                                      </span>
                                      <Badge className={STATUS_COLORS[booking.status]}>
                                        {booking.status}
                                      </Badge>
                                    </div>
                                    <div className="text-sm text-muted-foreground mt-1">
                                      {booking.booking_type.name}
                                    </div>
                                    {booking.contact.email && (
                                      <div className="text-sm text-muted-foreground">
                                        {booking.contact.email}
                                      </div>
                                    )}
                                    {booking.notes && (
                                      <div className="text-sm text-muted-foreground mt-2 italic">
                                        "{booking.notes}"
                                      </div>
                                    )}
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  {booking.status === "pending" && (
                                    <>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => handleConfirm(booking.id)}
                                        className="text-success border-success hover:bg-success/10"
                                      >
                                        <Check className="h-4 w-4 mr-1" />
                                        Confirm
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => handleCancel(booking.id)}
                                        className="text-destructive border-destructive hover:bg-destructive/10"
                                      >
                                        <X className="h-4 w-4 mr-1" />
                                        Decline
                                      </Button>
                                    </>
                                  )}
                                  {booking.status === "confirmed" && (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleCancel(booking.id)}
                                      className="text-destructive border-destructive hover:bg-destructive/10"
                                    >
                                      Cancel
                                    </Button>
                                  )}
                                  <Link href={`/contacts/${booking.contact_id}`}>
                                    <Button size="sm" variant="ghost">
                                      <User className="h-4 w-4" />
                                    </Button>
                                  </Link>
                                </div>
                              </div>
                            </div>
                          </div>
                        </Card>
                      ))}
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </Shell>
  );
}
