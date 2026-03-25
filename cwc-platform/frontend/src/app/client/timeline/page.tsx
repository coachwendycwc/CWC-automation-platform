"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Clock,
  Calendar,
  Target,
  Trophy,
  CheckCircle2,
  CheckSquare,
  MessageSquare,
  FileCheck,
  XCircle,
  Filter,
} from "lucide-react";
import { toast } from "sonner";
import { format, formatDistanceToNow, isToday, isYesterday, parseISO } from "date-fns";

interface TimelineEvent {
  id: string;
  type: string;
  title: string;
  description: string | null;
  date: string;
  icon: string;
  color: string;
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  calendar: Calendar,
  "check-circle": CheckCircle2,
  "x-circle": XCircle,
  target: Target,
  trophy: Trophy,
  "check-square": CheckSquare,
  "message-square": MessageSquare,
  "file-check": FileCheck,
};

const colorMap: Record<string, string> = {
  blue: "bg-primary/10 text-primary",
  green: "bg-success/10 text-success",
  purple: "bg-accent/10 text-accent",
  gold: "bg-warning/10 text-warning",
  gray: "bg-muted text-muted-foreground",
};

const eventTypeLabels: Record<string, string> = {
  session_scheduled: "Session Scheduled",
  session_completed: "Session Completed",
  session_cancelled: "Session Cancelled",
  goal_created: "Goal Set",
  goal_completed: "Goal Achieved",
  milestone_completed: "Milestone Completed",
  action_completed: "Task Completed",
  message: "Message",
  contract_signed: "Contract Signed",
};

export default function ClientTimelinePage() {
  const { sessionToken } = useClientAuth();
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    loadTimeline();
  }, [sessionToken, filter]);

  const loadTimeline = async () => {
    if (!sessionToken) return;
    try {
      setLoading(true);
      const eventTypes = filter === "all" ? undefined : filter;
      const data = await clientPortalApi.getTimeline(sessionToken, {
        event_types: eventTypes,
      });
      setEvents(data.events);
    } catch (error) {
      console.error("Failed to load timeline:", error);
      toast.error("Failed to load timeline");
    } finally {
      setLoading(false);
    }
  };

  // Group events by date
  const groupedEvents: Record<string, TimelineEvent[]> = {};
  events.forEach((event) => {
    const date = parseISO(event.date);
    let dateKey: string;
    if (isToday(date)) {
      dateKey = "Today";
    } else if (isYesterday(date)) {
      dateKey = "Yesterday";
    } else {
      dateKey = format(date, "MMMM d, yyyy");
    }
    if (!groupedEvents[dateKey]) {
      groupedEvents[dateKey] = [];
    }
    groupedEvents[dateKey].push(event);
  });

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
      <div>
        <h1 className="text-2xl font-bold text-foreground">My Journey</h1>
        <p className="text-muted-foreground">Your coaching progress over time</p>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-3">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter events" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Events</SelectItem>
            <SelectItem value="sessions">Sessions</SelectItem>
            <SelectItem value="goals">Goals & Milestones</SelectItem>
            <SelectItem value="action_items">Action Items</SelectItem>
            <SelectItem value="notes">Messages</SelectItem>
            <SelectItem value="contracts">Contracts</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Timeline */}
      {events.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Clock className="h-12 w-12 text-muted-foreground/40 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground">No events yet</h3>
            <p className="text-muted-foreground mt-1">
              {filter === "all"
                ? "Your coaching journey events will appear here"
                : `No ${filter.replace("_", " ")} events found`}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-8">
          {Object.entries(groupedEvents).map(([dateLabel, dayEvents]) => (
            <div key={dateLabel}>
              <div className="flex items-center gap-3 mb-4">
                <div className="h-px flex-1 bg-border" />
                <span className="text-sm font-medium text-muted-foreground bg-card px-3">
                  {dateLabel}
                </span>
                <div className="h-px flex-1 bg-border" />
              </div>

              <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-5 top-0 bottom-0 w-px bg-border" />

                <div className="space-y-4">
                  {dayEvents.map((event, index) => {
                    const IconComponent = iconMap[event.icon] || CheckCircle2;
                    const colorClass = colorMap[event.color] || colorMap.gray;

                    return (
                      <div key={event.id} className="relative flex gap-4">
                        {/* Icon */}
                        <div
                          className={`relative z-10 flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${colorClass}`}
                        >
                          <IconComponent className="h-5 w-5" />
                        </div>

                        {/* Content */}
                        <Card className="flex-1">
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <p className="font-medium text-foreground">
                                  {event.title}
                                </p>
                                {event.description && (
                                  <p className="text-sm text-muted-foreground mt-1">
                                    {event.description}
                                  </p>
                                )}
                              </div>
                              <div className="flex-shrink-0 text-right">
                                <p className="text-xs text-muted-foreground">
                                  {format(parseISO(event.date), "h:mm a")}
                                </p>
                                <Badge
                                  variant="outline"
                                  className="mt-1 text-xs"
                                >
                                  {eventTypeLabels[event.type] || event.type}
                                </Badge>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
