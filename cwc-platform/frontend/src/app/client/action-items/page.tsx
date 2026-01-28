"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  ListTodo,
  Calendar,
  Clock,
  CheckCircle2,
  Circle,
  XCircle,
  AlertCircle,
} from "lucide-react";
import { toast } from "sonner";
import { format, isBefore, isToday, isPast, parseISO } from "date-fns";

interface ActionItem {
  id: string;
  title: string;
  description: string | null;
  due_date: string | null;
  priority: string;
  status: string;
  completed_at: string | null;
  created_at: string;
}

const priorityColors: Record<string, string> = {
  low: "bg-gray-100 text-gray-600",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-red-100 text-red-700",
};

export default function ClientActionItemsPage() {
  const { sessionToken } = useClientAuth();
  const [items, setItems] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "pending" | "completed">("all");

  useEffect(() => {
    loadItems();
  }, [sessionToken]);

  const loadItems = async () => {
    if (!sessionToken) return;
    try {
      setLoading(true);
      const data = await clientPortalApi.getActionItems(sessionToken);
      setItems(data);
    } catch (error) {
      console.error("Failed to load action items:", error);
      toast.error("Failed to load action items");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleComplete = async (item: ActionItem) => {
    if (!sessionToken) return;
    const newStatus = item.status === "completed" ? "pending" : "completed";
    try {
      await clientPortalApi.updateActionItemStatus(sessionToken, item.id, newStatus as any);
      setItems(items.map(i =>
        i.id === item.id
          ? { ...i, status: newStatus, completed_at: newStatus === "completed" ? new Date().toISOString() : null }
          : i
      ));
      toast.success(newStatus === "completed" ? "Marked as complete!" : "Marked as pending");
    } catch (error) {
      console.error("Failed to update status:", error);
      toast.error("Failed to update status");
    }
  };

  const handleSkip = async (item: ActionItem) => {
    if (!sessionToken) return;
    try {
      await clientPortalApi.updateActionItemStatus(sessionToken, item.id, "skipped");
      setItems(items.map(i =>
        i.id === item.id
          ? { ...i, status: "skipped" }
          : i
      ));
      toast.success("Item skipped");
    } catch (error) {
      console.error("Failed to skip item:", error);
      toast.error("Failed to skip item");
    }
  };

  const getDueDateInfo = (dueDate: string | null): { text: string; isOverdue: boolean; isToday: boolean } | null => {
    if (!dueDate) return null;
    const date = parseISO(dueDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dateOnly = new Date(date);
    dateOnly.setHours(0, 0, 0, 0);

    if (isBefore(dateOnly, today)) {
      return { text: `Overdue (${format(date, "MMM d")})`, isOverdue: true, isToday: false };
    } else if (isToday(date)) {
      return { text: "Due today", isOverdue: false, isToday: true };
    }
    return { text: `Due ${format(date, "MMM d")}`, isOverdue: false, isToday: false };
  };

  // Filter and group items
  const filteredItems = items.filter(item => {
    if (filter === "pending") return item.status === "pending" || item.status === "in_progress";
    if (filter === "completed") return item.status === "completed" || item.status === "skipped";
    return true;
  });

  const pendingItems = filteredItems.filter(i => i.status === "pending" || i.status === "in_progress");
  const completedItems = filteredItems.filter(i => i.status === "completed" || i.status === "skipped");

  // Sort pending by due date (overdue first, then today, then upcoming, then no date)
  pendingItems.sort((a, b) => {
    if (!a.due_date && !b.due_date) return 0;
    if (!a.due_date) return 1;
    if (!b.due_date) return -1;
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
  });

  // Sort completed by completed_at descending
  completedItems.sort((a, b) => {
    if (!a.completed_at && !b.completed_at) return 0;
    if (!a.completed_at) return 1;
    if (!b.completed_at) return -1;
    return new Date(b.completed_at).getTime() - new Date(a.completed_at).getTime();
  });

  const pendingCount = items.filter(i => i.status === "pending" || i.status === "in_progress").length;
  const completedCount = items.filter(i => i.status === "completed").length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading action items...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Action Items</h1>
        <p className="text-gray-500">
          Tasks and assignments from your coach
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Clock className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{pendingCount}</p>
              <p className="text-sm text-gray-500">Pending</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{completedCount}</p>
              <p className="text-sm text-gray-500">Completed</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        <Button
          variant={filter === "all" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("all")}
        >
          All
        </Button>
        <Button
          variant={filter === "pending" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("pending")}
        >
          Pending ({pendingCount})
        </Button>
        <Button
          variant={filter === "completed" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("completed")}
        >
          Completed ({completedCount})
        </Button>
      </div>

      {/* Items List */}
      {filteredItems.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <ListTodo className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No action items</h3>
            <p className="text-gray-500 mt-1">
              {filter === "completed"
                ? "No completed items yet"
                : filter === "pending"
                ? "You're all caught up!"
                : "Your coach hasn't assigned any tasks yet"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {/* Pending Items */}
          {pendingItems.length > 0 && (filter === "all" || filter === "pending") && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                  <Circle className="h-4 w-4 text-gray-400" />
                  To Do
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="divide-y">
                  {pendingItems.map((item) => {
                    const dueDateInfo = getDueDateInfo(item.due_date);
                    return (
                      <div
                        key={item.id}
                        className="py-4 first:pt-0 last:pb-0"
                      >
                        <div className="flex items-start gap-3">
                          <Checkbox
                            checked={false}
                            onCheckedChange={() => handleToggleComplete(item)}
                            className="mt-1 h-5 w-5"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-medium text-gray-900">
                                {item.title}
                              </span>
                              <Badge className={priorityColors[item.priority] || "bg-gray-100"}>
                                {item.priority}
                              </Badge>
                            </div>
                            {item.description && (
                              <p className="text-sm text-gray-600 mt-1">
                                {item.description}
                              </p>
                            )}
                            {dueDateInfo && (
                              <p className={`text-xs mt-2 flex items-center gap-1 ${
                                dueDateInfo.isOverdue ? "text-red-600" :
                                dueDateInfo.isToday ? "text-orange-600" :
                                "text-gray-500"
                              }`}>
                                {dueDateInfo.isOverdue && <AlertCircle className="h-3 w-3" />}
                                <Calendar className="h-3 w-3" />
                                {dueDateInfo.text}
                              </p>
                            )}
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-gray-600"
                            onClick={() => handleSkip(item)}
                          >
                            Skip
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Completed Items */}
          {completedItems.length > 0 && (filter === "all" || filter === "completed") && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Completed
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="divide-y">
                  {completedItems.map((item) => (
                    <div
                      key={item.id}
                      className="py-4 first:pt-0 last:pb-0"
                    >
                      <div className="flex items-start gap-3">
                        {item.status === "completed" ? (
                          <Checkbox
                            checked={true}
                            onCheckedChange={() => handleToggleComplete(item)}
                            className="mt-1 h-5 w-5"
                          />
                        ) : (
                          <XCircle className="h-5 w-5 text-gray-400 mt-1" />
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className={`font-medium ${
                              item.status === "skipped" ? "text-gray-400 line-through" : "text-gray-500 line-through"
                            }`}>
                              {item.title}
                            </span>
                            {item.status === "skipped" && (
                              <Badge variant="outline" className="text-gray-400">
                                Skipped
                              </Badge>
                            )}
                          </div>
                          {item.completed_at && (
                            <p className="text-xs text-gray-400 mt-1">
                              {item.status === "completed" ? "Completed" : "Skipped"} {format(new Date(item.completed_at), "MMM d, yyyy")}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
