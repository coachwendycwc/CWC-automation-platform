"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { publicBookingApi } from "@/lib/api";
import { PublicBookingTypeInfo, TimeSlot } from "@/types";
import { Clock, Calendar, ChevronLeft, ChevronRight, Check } from "lucide-react";

export default function PublicBookingPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const [bookingType, setBookingType] = useState<PublicBookingTypeInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Date selection
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);

  // Time selection
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);

  // Form
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    notes: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [bookingToken, setBookingToken] = useState("");

  useEffect(() => {
    loadBookingType();
  }, [slug]);

  useEffect(() => {
    if (selectedDate) {
      loadSlots(selectedDate);
    }
  }, [selectedDate]);

  const loadBookingType = async () => {
    try {
      const data = await publicBookingApi.getBookingType(slug);
      setBookingType(data);
    } catch (err: any) {
      setError(err.message || "Booking type not found");
    } finally {
      setLoading(false);
    }
  };

  const loadSlots = async (date: Date) => {
    setLoadingSlots(true);
    setSelectedSlot(null);
    try {
      const dateStr = date.toISOString().split("T")[0];
      const data = await publicBookingApi.getSlots(slug, dateStr);
      setSlots(data.slots);
    } catch (err) {
      setSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSlot) return;

    setSubmitting(true);
    setError("");

    try {
      const response = await publicBookingApi.createBooking(slug, {
        start_time: selectedSlot.start_time,
        ...formData,
      });
      setSuccess(true);
      // Store token for manage page link
      if (response.id) {
        // We'd need to get the token from response
      }
    } catch (err: any) {
      setError(err.message || "Failed to create booking");
    } finally {
      setSubmitting(false);
    }
  };

  // Calendar helpers
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const days: (Date | null)[] = [];

    // Add empty slots for days before first day
    for (let i = 0; i < firstDay.getDay(); i++) {
      days.push(null);
    }

    // Add all days in month
    for (let i = 1; i <= lastDay.getDate(); i++) {
      days.push(new Date(year, month, i));
    }

    return days;
  };

  const isDateSelectable = (date: Date) => {
    if (!bookingType) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const minDate = new Date(today);
    minDate.setHours(minDate.getHours() + bookingType.min_notice_hours);

    const maxDate = new Date(today);
    maxDate.setDate(maxDate.getDate() + bookingType.max_advance_days);

    return date >= minDate && date <= maxDate;
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center">
        <div className="max-w-4xl w-full mx-auto px-4 space-y-6">
          <div className="text-center space-y-3">
            <Skeleton className="h-8 w-64 mx-auto" />
            <Skeleton className="h-4 w-96 mx-auto" />
            <Skeleton className="h-4 w-40 mx-auto" />
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <Skeleton className="h-80 rounded-lg" />
            <Skeleton className="h-80 rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  if (error && !bookingType) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="py-8 text-center">
            <h2 className="text-lg font-semibold text-foreground mb-2">Booking Not Available</h2>
            <p className="text-muted-foreground">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="py-12 text-center">
            <div className="w-16 h-16 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="h-8 w-8 text-success" />
            </div>
            <h2 className="text-2xl font-bold text-foreground mb-2">Booking Confirmed!</h2>
            <p className="text-muted-foreground mb-4">
              Your {bookingType?.name} has been scheduled for{" "}
              {selectedDate?.toLocaleDateString("en-US", {
                weekday: "long",
                month: "long",
                day: "numeric",
              })}{" "}
              at {selectedSlot && formatTime(selectedSlot.start_time)}.
            </p>
            <p className="text-sm text-muted-foreground">
              A confirmation email has been sent to {formData.email}.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground">{bookingType?.name}</h1>
          {bookingType?.description && (
            <p className="text-muted-foreground mt-2">{bookingType.description}</p>
          )}
          <div className="flex items-center justify-center gap-4 mt-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {bookingType?.duration_minutes} minutes
            </span>
            {bookingType?.price && (
              <span className="font-medium text-foreground">${bookingType.price}</span>
            )}
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Calendar */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Select a Date</CardTitle>
            </CardHeader>
            <CardContent>
              {/* Month navigation */}
              <div className="flex items-center justify-between mb-4">
                <Button
                  variant="ghost"
                  size="sm"
                  className="cursor-pointer"
                  onClick={() => setCurrentMonth(new Date(currentMonth.setMonth(currentMonth.getMonth() - 1)))}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="font-medium">
                  {currentMonth.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="cursor-pointer"
                  onClick={() => setCurrentMonth(new Date(currentMonth.setMonth(currentMonth.getMonth() + 1)))}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>

              {/* Day headers */}
              <div className="grid grid-cols-7 gap-1 text-center text-sm font-medium text-muted-foreground mb-2">
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                  <div key={day}>{day}</div>
                ))}
              </div>

              {/* Calendar grid */}
              <div className="grid grid-cols-7 gap-1">
                {getDaysInMonth(currentMonth).map((date, i) => {
                  if (!date) {
                    return <div key={i} className="h-10" />;
                  }

                  const isSelectable = isDateSelectable(date);
                  const isSelected = selectedDate?.toDateString() === date.toDateString();
                  const isToday = new Date().toDateString() === date.toDateString();

                  return (
                    <button
                      key={i}
                      onClick={() => isSelectable && setSelectedDate(date)}
                      disabled={!isSelectable}
                      className={`h-10 rounded-md text-sm font-medium transition-colors cursor-pointer ${
                        isSelected
                          ? "bg-primary text-primary-foreground"
                          : isSelectable
                          ? "hover:bg-primary/10 text-foreground"
                          : "text-muted-foreground/40 cursor-not-allowed"
                      } ${isToday && !isSelected ? "border border-primary" : ""}`}
                    >
                      {date.getDate()}
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Time slots or form */}
          <Card>
            {!showForm ? (
              <>
                <CardHeader>
                  <CardTitle className="text-lg">
                    {selectedDate
                      ? `Available Times for ${selectedDate.toLocaleDateString("en-US", {
                          weekday: "long",
                          month: "short",
                          day: "numeric",
                        })}`
                      : "Select a Time"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {!selectedDate ? (
                    <p className="text-muted-foreground text-center py-8">
                      Please select a date to see available times
                    </p>
                  ) : loadingSlots ? (
                    <div className="space-y-2 py-4">
                      <div className="grid grid-cols-2 gap-2">
                        {Array.from({ length: 6 }).map((_, i) => (
                          <Skeleton key={i} className="h-10 rounded-md" />
                        ))}
                      </div>
                    </div>
                  ) : slots.length === 0 ? (
                    <p className="text-muted-foreground text-center py-8">
                      No available times for this date. Please select another date.
                    </p>
                  ) : (
                    <div className="grid grid-cols-2 gap-2 max-h-80 overflow-y-auto">
                      {slots.map((slot, i) => (
                        <button
                          key={i}
                          onClick={() => {
                            setSelectedSlot(slot);
                            setShowForm(true);
                          }}
                          className={`py-2 px-4 rounded-md text-sm font-medium border transition-colors cursor-pointer ${
                            selectedSlot?.start_time === slot.start_time
                              ? "bg-primary text-primary-foreground border-primary"
                              : "border-border hover:border-primary hover:text-primary"
                          }`}
                        >
                          {formatTime(slot.start_time)}
                        </button>
                      ))}
                    </div>
                  )}
                </CardContent>
              </>
            ) : (
              <>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm" className="cursor-pointer" onClick={() => setShowForm(false)}>
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <CardTitle className="text-lg">Enter Your Details</CardTitle>
                  </div>
                  <CardDescription>
                    {selectedDate?.toLocaleDateString("en-US", {
                      weekday: "long",
                      month: "long",
                      day: "numeric",
                    })}{" "}
                    at {selectedSlot && formatTime(selectedSlot.start_time)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                      <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">{error}</div>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-1">
                          First Name *
                        </label>
                        <Input
                          value={formData.first_name}
                          onChange={(e) =>
                            setFormData({ ...formData, first_name: e.target.value })
                          }
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-1">
                          Last Name
                        </label>
                        <Input
                          value={formData.last_name}
                          onChange={(e) =>
                            setFormData({ ...formData, last_name: e.target.value })
                          }
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Email *
                      </label>
                      <Input
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Phone
                      </label>
                      <Input
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Notes (optional)
                      </label>
                      <textarea
                        className="w-full rounded-md border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        rows={3}
                        placeholder="Anything you'd like us to know before the session..."
                      />
                    </div>

                    <Button type="submit" className="w-full cursor-pointer" disabled={submitting}>
                      {submitting ? "Booking..." : "Confirm Booking"}
                    </Button>
                  </form>
                </CardContent>
              </>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
