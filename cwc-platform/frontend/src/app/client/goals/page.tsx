"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import {
  Target,
  ChevronDown,
  ChevronUp,
  Calendar,
  CheckCircle2,
  Circle,
  Trophy,
  Flame,
} from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";

interface Milestone {
  id: string;
  goal_id: string;
  title: string;
  description: string | null;
  target_date: string | null;
  is_completed: boolean;
  completed_at: string | null;
  sort_order: number;
  created_at: string;
}

interface Goal {
  id: string;
  title: string;
  description: string | null;
  category: string | null;
  status: string;
  target_date: string | null;
  progress_percent: number;
  milestones: Milestone[];
  created_at: string;
}

const categoryColors: Record<string, string> = {
  career: "bg-blue-100 text-blue-700",
  health: "bg-green-100 text-green-700",
  relationships: "bg-pink-100 text-pink-700",
  finance: "bg-yellow-100 text-yellow-700",
  personal: "bg-purple-100 text-purple-700",
  education: "bg-indigo-100 text-indigo-700",
};

export default function ClientGoalsPage() {
  const { sessionToken } = useClientAuth();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedGoals, setExpandedGoals] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<"all" | "active" | "completed">("all");

  useEffect(() => {
    loadGoals();
  }, [sessionToken]);

  const loadGoals = async () => {
    if (!sessionToken) return;
    try {
      setLoading(true);
      const data = await clientPortalApi.getGoals(sessionToken);
      setGoals(data);
      // Auto-expand active goals
      const activeGoalIds = new Set(
        data.filter((g) => g.status === "active").map((g) => g.id)
      );
      setExpandedGoals(activeGoalIds);
    } catch (error) {
      console.error("Failed to load goals:", error);
      toast.error("Failed to load goals");
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (goalId: string) => {
    setExpandedGoals((prev) => {
      const next = new Set(prev);
      if (next.has(goalId)) {
        next.delete(goalId);
      } else {
        next.add(goalId);
      }
      return next;
    });
  };

  const handleToggleMilestone = async (goal: Goal, milestone: Milestone) => {
    if (!sessionToken) return;
    try {
      const newStatus = !milestone.is_completed;
      await clientPortalApi.completeMilestone(
        sessionToken,
        goal.id,
        milestone.id,
        newStatus
      );

      // Update local state
      setGoals(
        goals.map((g) => {
          if (g.id !== goal.id) return g;
          const updatedMilestones = g.milestones.map((m) =>
            m.id === milestone.id
              ? {
                  ...m,
                  is_completed: newStatus,
                  completed_at: newStatus ? new Date().toISOString() : null,
                }
              : m
          );
          const completedCount = updatedMilestones.filter((m) => m.is_completed).length;
          const progress = updatedMilestones.length > 0
            ? Math.round((completedCount / updatedMilestones.length) * 100)
            : 0;
          return {
            ...g,
            milestones: updatedMilestones,
            progress_percent: progress,
          };
        })
      );

      toast.success(
        newStatus ? "Milestone completed!" : "Milestone marked as incomplete"
      );
    } catch (error) {
      console.error("Failed to update milestone:", error);
      toast.error("Failed to update milestone");
    }
  };

  const filteredGoals = goals.filter((goal) => {
    if (filter === "active") return goal.status === "active";
    if (filter === "completed") return goal.status === "completed";
    return true;
  });

  const activeGoals = goals.filter((g) => g.status === "active");
  const completedGoals = goals.filter((g) => g.status === "completed");

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading goals...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Goals</h1>
        <p className="text-gray-500">Track your progress and celebrate wins</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Flame className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{activeGoals.length}</p>
              <p className="text-sm text-gray-500">Active Goals</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Trophy className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{completedGoals.length}</p>
              <p className="text-sm text-gray-500">Achieved</p>
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
          variant={filter === "active" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("active")}
        >
          Active ({activeGoals.length})
        </Button>
        <Button
          variant={filter === "completed" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("completed")}
        >
          Completed ({completedGoals.length})
        </Button>
      </div>

      {/* Goals List */}
      {filteredGoals.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Target className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No goals yet</h3>
            <p className="text-gray-500 mt-1">
              {filter === "completed"
                ? "No completed goals yet. Keep working toward your goals!"
                : filter === "active"
                ? "No active goals. Your coach will set goals for you."
                : "Your coach will set goals with milestones for you."}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredGoals.map((goal) => {
            const isExpanded = expandedGoals.has(goal.id);
            const isCompleted = goal.status === "completed";

            return (
              <Card
                key={goal.id}
                className={isCompleted ? "border-green-200 bg-green-50/50" : ""}
              >
                <CardHeader className="pb-2">
                  <div
                    className="flex items-start justify-between cursor-pointer"
                    onClick={() => toggleExpand(goal.id)}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        {isCompleted ? (
                          <Trophy className="h-5 w-5 text-green-600" />
                        ) : (
                          <Target className="h-5 w-5 text-gray-400" />
                        )}
                        <CardTitle
                          className={`text-lg ${
                            isCompleted ? "text-green-800" : "text-gray-900"
                          }`}
                        >
                          {goal.title}
                        </CardTitle>
                        {goal.category && (
                          <Badge
                            className={
                              categoryColors[goal.category.toLowerCase()] ||
                              "bg-gray-100 text-gray-700"
                            }
                          >
                            {goal.category}
                          </Badge>
                        )}
                        {isCompleted && (
                          <Badge className="bg-green-100 text-green-700">
                            Achieved
                          </Badge>
                        )}
                      </div>
                      {goal.description && (
                        <p className="text-sm text-gray-600 mt-1 ml-7">
                          {goal.description}
                        </p>
                      )}
                    </div>
                    <Button variant="ghost" size="icon" className="flex-shrink-0">
                      {isExpanded ? (
                        <ChevronUp className="h-5 w-5" />
                      ) : (
                        <ChevronDown className="h-5 w-5" />
                      )}
                    </Button>
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-3 ml-7">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-600">Progress</span>
                      <span
                        className={`font-medium ${
                          goal.progress_percent === 100
                            ? "text-green-600"
                            : "text-gray-900"
                        }`}
                      >
                        {goal.progress_percent}%
                      </span>
                    </div>
                    <Progress
                      value={goal.progress_percent}
                      className={`h-2 ${
                        goal.progress_percent === 100 ? "bg-green-100" : ""
                      }`}
                    />
                    {goal.target_date && (
                      <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        Target: {format(new Date(goal.target_date), "MMM d, yyyy")}
                      </p>
                    )}
                  </div>
                </CardHeader>

                {/* Milestones (Expanded) */}
                {isExpanded && goal.milestones.length > 0 && (
                  <CardContent className="pt-2">
                    <div className="ml-7 border-t pt-4">
                      <p className="text-sm font-medium text-gray-700 mb-3">
                        Milestones ({goal.milestones.filter((m) => m.is_completed).length}/
                        {goal.milestones.length})
                      </p>
                      <div className="space-y-3">
                        {goal.milestones
                          .sort((a, b) => a.sort_order - b.sort_order)
                          .map((milestone) => (
                            <div
                              key={milestone.id}
                              className="flex items-start gap-3"
                            >
                              <Checkbox
                                checked={milestone.is_completed}
                                onCheckedChange={() =>
                                  handleToggleMilestone(goal, milestone)
                                }
                                disabled={isCompleted}
                                className="mt-0.5 h-5 w-5"
                              />
                              <div className="flex-1">
                                <p
                                  className={`text-sm ${
                                    milestone.is_completed
                                      ? "text-gray-500 line-through"
                                      : "text-gray-900"
                                  }`}
                                >
                                  {milestone.title}
                                </p>
                                {milestone.description && (
                                  <p className="text-xs text-gray-400 mt-0.5">
                                    {milestone.description}
                                  </p>
                                )}
                                {milestone.target_date && !milestone.is_completed && (
                                  <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
                                    <Calendar className="h-3 w-3" />
                                    Due: {format(new Date(milestone.target_date), "MMM d")}
                                  </p>
                                )}
                                {milestone.is_completed && milestone.completed_at && (
                                  <p className="text-xs text-green-600 mt-0.5 flex items-center gap-1">
                                    <CheckCircle2 className="h-3 w-3" />
                                    Completed {format(new Date(milestone.completed_at), "MMM d")}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  </CardContent>
                )}

                {/* No milestones message */}
                {isExpanded && goal.milestones.length === 0 && (
                  <CardContent className="pt-2">
                    <div className="ml-7 border-t pt-4">
                      <p className="text-sm text-gray-500 italic">
                        No milestones set for this goal yet.
                      </p>
                    </div>
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
