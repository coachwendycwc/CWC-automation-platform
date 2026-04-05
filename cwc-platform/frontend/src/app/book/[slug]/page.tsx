"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { publicBookingApi } from "@/lib/api";
import { PublicBookingResult, PublicBookingTypeInfo, TimeSlot } from "@/types";
import { Clock, ChevronLeft, ChevronRight, Check } from "lucide-react";

export default function PublicBookingPage() {
  const params = useParams();
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
  const [formData, setFormData] = useState<Record<string, string>>({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    notes: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [paymentRedirecting, setPaymentRedirecting] = useState(false);
  const [bookingResult, setBookingResult] = useState<PublicBookingResult | null>(null);

  const brandColor = bookingType?.booking_page_brand_color || "#2A7B8C";
  const bookingTitle = bookingType?.booking_page_title || bookingType?.name || "Book your session";
  const bookingDescription = bookingType?.booking_page_description || bookingType?.description || "";
  const bookingLogoUrl = bookingType?.booking_page_logo_url;
  const bookingBannerUrl = bookingType?.booking_page_banner_url;
  const hostName = bookingType?.host_name;
  const hostAvatarUrl = bookingType?.host_avatar_url;

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
      const result: PublicBookingResult = await publicBookingApi.createBooking(slug, {
        start_time: selectedSlot.start_time,
        intake_responses: Object.fromEntries(
          (bookingType?.intake_questions || []).map((question) => [question.id, formData[question.id] || ""])
        ),
        ...formData,
      });

      if (result.payment_required && result.payment_url) {
        setPaymentRedirecting(true);
        window.location.href = result.payment_url;
        return;
      }
      setBookingResult(result);
      setSuccess(true);
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

  const selectedDateLabel = selectedDate?.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
  const selectedTimeLabel = selectedSlot ? formatTime(selectedSlot.start_time) : null;

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
      <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(255,255,255,0.92),_rgba(241,245,249,0.92)_48%,_rgba(233,241,244,0.96))] p-4">
        <div className="mx-auto flex min-h-screen max-w-xl items-center justify-center">
        <Card className="w-full rounded-[2rem] border-white/70 bg-white/92 shadow-[0_30px_90px_rgba(15,23,42,0.12)] backdrop-blur">
          <CardContent className="px-8 py-12 text-center md:px-10">
            <div
              className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full border border-white/70 shadow-[0_16px_36px_rgba(15,23,42,0.08)]"
              style={{ backgroundColor: `${brandColor}1A` }}
            >
              <Check className="h-9 w-9 text-success" />
            </div>
            <div className="mb-3 inline-flex rounded-full border border-slate-200/80 bg-slate-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
              Confirmed
            </div>
            <h2 className="mb-3 text-3xl font-semibold tracking-[-0.04em] text-slate-950">Booking confirmed</h2>
            <p className="mx-auto mb-6 max-w-md text-[15px] leading-7 text-slate-600">
              Your {bookingType?.name} is scheduled for {selectedDateLabel} at {selectedTimeLabel}.
            </p>
            <div className="mb-6 rounded-[1.5rem] border border-slate-200/80 bg-slate-50/80 p-4 text-left">
              <div className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                Session details
              </div>
              <div className="space-y-2 text-sm text-slate-600">
                <div className="flex items-center justify-between gap-4">
                  <span>Date</span>
                  <span className="font-medium text-slate-900">{selectedDateLabel}</span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>Time</span>
                  <span className="font-medium text-slate-900">{selectedTimeLabel}</span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>Email</span>
                  <span className="font-medium text-slate-900">{formData.email}</span>
                </div>
              </div>
            </div>
            <p className="text-sm text-slate-500">
              A confirmation email has been sent to {formData.email}.
            </p>
            {bookingResult?.confirmation_token && (
              <div className="mt-6">
                <Button variant="outline" asChild className="w-full rounded-2xl">
                  <Link href={`/book/manage/${bookingResult.confirmation_token}`}>
                    Manage booking
                  </Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(255,255,255,0.92),_rgba(241,245,249,0.92)_48%,_rgba(233,241,244,0.96))] px-4 py-10">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <div className="mb-8 overflow-hidden rounded-[2rem] border border-white/70 bg-background/90 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur">
          {bookingBannerUrl && (
            <div className="relative h-56 w-full overflow-hidden">
              <img
                src={bookingBannerUrl}
                alt={bookingTitle}
                className="h-full w-full object-cover"
              />
              <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(15,23,42,0.08),rgba(15,23,42,0.34))]" />
            </div>
          )}
          <div className="p-8 md:p-10">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="flex items-start gap-4 md:gap-5">
              {hostAvatarUrl && (
                <img
                  src={hostAvatarUrl}
                  alt={hostName ? `${hostName} profile photo` : "Host profile photo"}
                  className="mt-1 h-14 w-14 flex-none rounded-full border border-white/80 object-cover shadow-[0_10px_30px_rgba(15,23,42,0.14)] md:h-16 md:w-16"
                />
              )}
              <div className="text-center md:text-left">
                {bookingLogoUrl && (
                  <div className="mb-5 flex h-16 w-full max-w-[220px] items-center justify-center overflow-hidden rounded-2xl border border-slate-200/80 bg-white px-4 py-3 shadow-[0_12px_28px_rgba(15,23,42,0.06)] md:justify-start">
                    <img
                      src={bookingLogoUrl}
                      alt={hostName ? `${hostName} logo` : "Booking logo"}
                      className="max-h-full max-w-full object-contain"
                    />
                  </div>
                )}
                <div
                  className="mb-4 inline-flex rounded-full border border-slate-200/70 bg-white/90 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-600"
                >
                  {bookingType?.name || "Booking page"}
                </div>
                <h1 className="max-w-2xl text-3xl font-semibold tracking-[-0.04em] text-slate-950 md:text-[2.6rem]">
                  {bookingTitle}
                </h1>
                {bookingDescription && (
                  <p className="mt-3 max-w-2xl text-[15px] leading-7 text-slate-600 md:text-base">
                    {bookingDescription}
                  </p>
                )}
                {bookingType?.post_booking_instructions && (
                  <div className="mt-5 max-w-2xl rounded-2xl border border-slate-200/80 bg-slate-50/80 px-4 py-3 text-sm leading-6 text-slate-600">
                    {bookingType.post_booking_instructions}
                  </div>
                )}
                {hostName && (
                  <p className="mt-4 text-sm font-medium text-slate-500">
                    Meet with {hostName}
                  </p>
                )}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600 md:max-w-[240px] md:justify-end">
              <span className="inline-flex items-center gap-2 rounded-full border border-slate-200/80 bg-slate-50 px-3 py-2">
                <Clock className="h-4 w-4" />
                {bookingType?.duration_minutes} minutes
              </span>
              {bookingType?.show_price_on_booking_page && bookingType?.price !== null && (
                <span
                  className="inline-flex items-center rounded-full px-3 py-2 font-semibold text-white shadow-sm"
                  style={{ backgroundColor: brandColor }}
                >
                  ${bookingType.price}
                </span>
              )}
            </div>
          </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.12fr_0.88fr]">
          {/* Calendar */}
          <Card className="rounded-[2rem] border-white/70 bg-white/85 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-semibold tracking-[-0.02em] text-slate-950">Select a Date</CardTitle>
              <CardDescription className="text-sm text-slate-500">
                Choose a day that fits your schedule. Available times update automatically.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {/* Month navigation */}
              <div className="flex items-center justify-between rounded-2xl border border-slate-200/80 bg-slate-50/90 px-3 py-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="cursor-pointer rounded-full text-slate-600 hover:bg-white hover:text-slate-950"
                  onClick={() => setCurrentMonth(new Date(currentMonth.setMonth(currentMonth.getMonth() - 1)))}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">
                  {currentMonth.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="cursor-pointer rounded-full text-slate-600 hover:bg-white hover:text-slate-950"
                  onClick={() => setCurrentMonth(new Date(currentMonth.setMonth(currentMonth.getMonth() + 1)))}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>

              {/* Day headers */}
              <div className="mb-2 grid grid-cols-7 gap-2 text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                  <div key={day}>{day}</div>
                ))}
              </div>

              {/* Calendar grid */}
              <div className="grid grid-cols-7 gap-2">
                {getDaysInMonth(currentMonth).map((date, i) => {
                  if (!date) {
                    return <div key={i} className="h-11" />;
                  }

                  const isSelectable = isDateSelectable(date);
                  const isSelected = selectedDate?.toDateString() === date.toDateString();
                  const isToday = new Date().toDateString() === date.toDateString();

                  return (
                    <button
                      key={i}
                      onClick={() => isSelectable && setSelectedDate(date)}
                      disabled={!isSelectable}
                      className={`h-11 rounded-2xl text-sm font-semibold transition-all cursor-pointer ${
                        isSelected
                          ? "scale-[1.02] text-white shadow-sm"
                          : isSelectable
                          ? "border border-slate-200/80 bg-white text-slate-900 hover:border-slate-300 hover:bg-slate-50"
                          : "cursor-not-allowed text-slate-300"
                      } ${isToday && !isSelected ? "ring-1 ring-offset-0" : ""}`}
                      style={{
                        backgroundColor: isSelected ? brandColor : undefined,
                        borderColor: isToday && !isSelected ? brandColor : undefined,
                        boxShadow: isToday && !isSelected ? `0 0 0 1px ${brandColor}22 inset` : undefined,
                      }}
                    >
                      {date.getDate()}
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Time slots or form */}
          <Card className="rounded-[2rem] border-white/70 bg-white/85 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur">
            {!showForm ? (
              <>
                <CardHeader className="pb-4">
                  <div className="mb-2 inline-flex rounded-full border border-slate-200/80 bg-slate-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                    {selectedDate ? "Step 2" : "Step 1"}
                  </div>
                  <CardTitle className="text-xl font-semibold tracking-[-0.02em] text-slate-950">
                    {selectedDate
                      ? `Available Times for ${selectedDate.toLocaleDateString("en-US", {
                          weekday: "long",
                          month: "short",
                          day: "numeric",
                        })}`
                      : "Select a Time"}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {!selectedDate ? (
                    <p className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/80 py-10 text-center text-sm text-slate-500">
                      Please select a date to see available times
                    </p>
                  ) : loadingSlots ? (
                    <div className="space-y-2 py-2">
                      <div className="grid grid-cols-2 gap-3">
                        {Array.from({ length: 6 }).map((_, i) => (
                          <Skeleton key={i} className="h-12 rounded-2xl" />
                        ))}
                      </div>
                    </div>
                  ) : slots.length === 0 ? (
                    <p className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/80 py-10 text-center text-sm text-slate-500">
                      No available times for this date. Please select another date.
                    </p>
                  ) : (
                    <div className="grid max-h-80 grid-cols-2 gap-3 overflow-y-auto pr-1">
                      {slots.map((slot, i) => (
                        <button
                          key={i}
                          onClick={() => {
                            setSelectedSlot(slot);
                            setShowForm(true);
                          }}
                          className={`rounded-2xl border px-4 py-3 text-sm font-semibold transition-all cursor-pointer ${
                            selectedSlot?.start_time === slot.start_time
                              ? "scale-[1.01] text-white shadow-sm"
                              : "border-slate-200 bg-white text-slate-800 hover:border-slate-300 hover:bg-slate-50"
                          }`}
                          style={{
                            backgroundColor: selectedSlot?.start_time === slot.start_time ? brandColor : undefined,
                            borderColor: selectedSlot?.start_time === slot.start_time ? brandColor : undefined,
                            color: selectedSlot?.start_time === slot.start_time ? "#FFFFFF" : undefined,
                          }}
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
                <CardHeader className="pb-4">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="cursor-pointer rounded-full text-slate-600 hover:bg-slate-100 hover:text-slate-950"
                      onClick={() => setShowForm(false)}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <CardTitle className="text-xl font-semibold tracking-[-0.02em] text-slate-950">Enter Your Details</CardTitle>
                  </div>
                  <CardDescription className="text-sm text-slate-500">
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

                    {bookingType?.price !== null && bookingType?.price !== undefined && bookingType.price > 0 && (
                      <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4 text-sm text-slate-600">
                        <p className="font-medium text-slate-900">Your time will be reserved after you continue to payment.</p>
                        <p className="mt-1">
                          Once payment is completed, your booking will be confirmed and your meeting details will be sent automatically.
                        </p>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="block text-sm font-medium text-slate-700">
                          First Name *
                        </label>
                        <Input
                          className="h-12 rounded-2xl border-slate-200 bg-white px-4 text-slate-900 focus-visible:border-slate-300 focus-visible:ring-0 focus-visible:ring-offset-0"
                          value={formData.first_name}
                          onChange={(e) =>
                            setFormData({ ...formData, first_name: e.target.value })
                          }
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="block text-sm font-medium text-slate-700">
                          Last Name
                        </label>
                        <Input
                          className="h-12 rounded-2xl border-slate-200 bg-white px-4 text-slate-900 focus-visible:border-slate-300 focus-visible:ring-0 focus-visible:ring-offset-0"
                          value={formData.last_name}
                          onChange={(e) =>
                            setFormData({ ...formData, last_name: e.target.value })
                          }
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-slate-700">
                        Email *
                      </label>
                      <Input
                        className="h-12 rounded-2xl border-slate-200 bg-white px-4 text-slate-900 focus-visible:border-slate-300 focus-visible:ring-0 focus-visible:ring-offset-0"
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-slate-700">
                        Phone
                      </label>
                      <Input
                        className="h-12 rounded-2xl border-slate-200 bg-white px-4 text-slate-900 focus-visible:border-slate-300 focus-visible:ring-0 focus-visible:ring-offset-0"
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      />
                    </div>

                    {(bookingType?.intake_questions || []).map((question) => (
                      <div key={question.id} className="space-y-2">
                        <label className="block text-sm font-medium text-slate-700">
                          {question.label}
                          {question.required ? " *" : ""}
                        </label>
                        {question.question_type === "long_text" ? (
                          <textarea
                            className="w-full rounded-2xl border border-slate-200 px-3 py-3 text-sm text-slate-900 transition focus:border-slate-300 focus:outline-none focus:ring-0"
                            value={formData[question.id] || ""}
                            onChange={(e) =>
                              setFormData((current) => ({ ...current, [question.id]: e.target.value }))
                            }
                            rows={4}
                            placeholder={question.placeholder || ""}
                            required={question.required}
                          />
                        ) : question.question_type === "select" ? (
                          <select
                            className="flex h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-900 focus:border-slate-300 focus:outline-none"
                            value={formData[question.id] || ""}
                            onChange={(e) =>
                              setFormData((current) => ({ ...current, [question.id]: e.target.value }))
                            }
                            required={question.required}
                          >
                            <option value="">Select an option</option>
                            {question.options.map((option) => (
                              <option key={option} value={option}>
                                {option}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <Input
                            className="h-12 rounded-2xl border-slate-200 bg-white px-4 text-slate-900 focus-visible:border-slate-300 focus-visible:ring-0 focus-visible:ring-offset-0"
                            type={question.question_type === "phone" ? "tel" : "text"}
                            value={formData[question.id] || ""}
                            onChange={(e) =>
                              setFormData((current) => ({ ...current, [question.id]: e.target.value }))
                            }
                            placeholder={question.placeholder || ""}
                            required={question.required}
                          />
                        )}
                      </div>
                    ))}

                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-slate-700">
                        Notes (optional)
                      </label>
                      <textarea
                        className="w-full rounded-2xl border border-slate-200 px-3 py-3 text-sm text-slate-900 transition focus:border-slate-300 focus:outline-none focus:ring-0"
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        rows={3}
                        placeholder="Anything you'd like us to know before the session..."
                        style={{
                          borderColor: undefined,
                          boxShadow: "none",
                        }}
                      />
                    </div>

                    <Button
                      type="submit"
                      className="h-12 w-full cursor-pointer rounded-2xl text-white shadow-[0_18px_40px_rgba(15,23,42,0.14)]"
                      disabled={submitting || paymentRedirecting}
                      style={{ backgroundColor: brandColor }}
                    >
                      {paymentRedirecting
                        ? "Redirecting to payment..."
                        : submitting
                        ? "Booking..."
                        : bookingType?.price && bookingType.price > 0
                        ? "Continue to payment"
                        : "Confirm booking"}
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
