"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import listPlugin from "@fullcalendar/list";
import { useAuth } from "@/contexts/AuthContext";
import { bookingsApi } from "@/lib/api";
import { Shell } from "@/components/layout/Shell";

interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  backgroundColor?: string;
  borderColor?: string;
  extendedProps?: {
    status: string;
    contactName: string;
    bookingType: string;
  };
}

const statusColors: Record<string, { bg: string; border: string }> = {
  confirmed: { bg: "#22c55e", border: "#16a34a" },
  pending: { bg: "#eab308", border: "#ca8a04" },
  completed: { bg: "#6b7280", border: "#4b5563" },
  cancelled: { bg: "#ef4444", border: "#dc2626" },
  no_show: { bg: "#f97316", border: "#ea580c" },
};

export default function CalendarPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (token) {
      loadBookings();
    }
  }, [token]);

  const loadBookings = async () => {
    try {
      setIsLoading(true);
      const response = await bookingsApi.list(token!, { limit: 500 });

      const calendarEvents: CalendarEvent[] = response.items.map((booking: any) => {
        const colors = statusColors[booking.status] || statusColors.confirmed;
        return {
          id: booking.id,
          title: `${booking.booking_type?.name || "Booking"} - ${booking.contact?.first_name || "Unknown"}`,
          start: booking.start_time,
          end: booking.end_time,
          backgroundColor: colors.bg,
          borderColor: colors.border,
          extendedProps: {
            status: booking.status,
            contactName: booking.contact?.first_name + " " + booking.contact?.last_name,
            bookingType: booking.booking_type?.name,
          },
        };
      });

      setEvents(calendarEvents);
    } catch (error) {
      console.error("Failed to load bookings:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEventClick = (info: any) => {
    router.push(`/bookings/${info.event.id}`);
  };

  const handleDateClick = (info: any) => {
    // Navigate to create booking with pre-selected date
    router.push(`/bookings/new?date=${info.dateStr}`);
  };

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <Shell>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Calendar</h1>
          <p className="text-gray-600">View and manage your bookings</p>
        </div>

        {/* Legend */}
        <div className="mb-4 flex flex-wrap gap-4">
          {Object.entries(statusColors).map(([status, colors]) => (
            <div key={status} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: colors.bg }}
              />
              <span className="text-sm text-gray-600 capitalize">{status.replace("_", " ")}</span>
            </div>
          ))}
        </div>

        {/* Calendar */}
        <div className="bg-white rounded-lg shadow p-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-96">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          ) : (
            <FullCalendar
              plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin, listPlugin]}
              initialView="dayGridMonth"
              headerToolbar={{
                left: "prev,next today",
                center: "title",
                right: "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
              }}
              events={events}
              eventClick={handleEventClick}
              dateClick={handleDateClick}
              editable={false}
              selectable={true}
              selectMirror={true}
              dayMaxEvents={3}
              weekends={true}
              nowIndicator={true}
              height="auto"
              eventTimeFormat={{
                hour: "numeric",
                minute: "2-digit",
                meridiem: "short",
              }}
              slotMinTime="06:00:00"
              slotMaxTime="22:00:00"
            />
          )}
        </div>
      </div>
    </Shell>
  );
}
