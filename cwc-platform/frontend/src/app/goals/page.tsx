"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Shell } from "@/components/layout/Shell";
import { goalsApi, Goal, GoalMilestone, contactsApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Target,
  Plus,
  MoreHorizontal,
  Pencil,
  Trash2,
  User,
  Calendar,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Circle,
  Trophy,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";

interface Contact {
  id: string;
  first_name: string;
  last_name: string | null;
}

interface MilestoneInput {
  title: string;
  description: string;
  target_date: string;
}

const categoryOptions = [
  { value: "career", label: "Career" },
  { value: "health", label: "Health" },
  { value: "relationships", label: "Relationships" },
  { value: "finance", label: "Finance" },
  { value: "personal", label: "Personal Development" },
  { value: "education", label: "Education" },
];

const categoryColors: Record<string, string> = {
  career: "bg-blue-100 text-blue-700",
  health: "bg-green-100 text-green-700",
  relationships: "bg-pink-100 text-pink-700",
  finance: "bg-yellow-100 text-yellow-700",
  personal: "bg-purple-100 text-purple-700",
  education: "bg-indigo-100 text-indigo-700",
};

const statusColors: Record<string, string> = {
  active: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  abandoned: "bg-gray-100 text-gray-500",
};

export default function GoalsPage() {
  const { token } = useAuth();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filterContact, setFilterContact] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [expandedGoals, setExpandedGoals] = useState<Set<string>>(new Set());

  // Create/Edit dialog
  const [showDialog, setShowDialog] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [formData, setFormData] = useState({
    contact_id: "",
    title: "",
    description: "",
    category: "",
    target_date: "",
  });
  const [milestones, setMilestones] = useState<MilestoneInput[]>([]);
  const [saving, setSaving] = useState(false);

  // Delete confirmation
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Add milestone dialog
  const [addMilestoneGoalId, setAddMilestoneGoalId] = useState<string | null>(null);
  const [newMilestone, setNewMilestone] = useState<MilestoneInput>({
    title: "",
    description: "",
    target_date: "",
  });

  useEffect(() => {
    loadGoals();
    loadContacts();
  }, [token, page, filterContact, filterStatus]);

  const loadGoals = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const result = await goalsApi.list(token, {
        page,
        size: 20,
        contact_id: filterContact || undefined,
        status: filterStatus || undefined,
      });
      setGoals(result.items);
      setTotal(result.total);
    } catch (error) {
      console.error("Failed to load goals:", error);
      toast.error("Failed to load goals");
    } finally {
      setLoading(false);
    }
  };

  const loadContacts = async () => {
    if (!token) return;
    try {
      const result = await contactsApi.list(token);
      setContacts(result.items);
    } catch (error) {
      console.error("Failed to load contacts:", error);
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

  const openNewDialog = () => {
    setEditingGoal(null);
    setFormData({
      contact_id: "",
      title: "",
      description: "",
      category: "",
      target_date: "",
    });
    setMilestones([]);
    setShowDialog(true);
  };

  const openEditDialog = (goal: Goal) => {
    setEditingGoal(goal);
    setFormData({
      contact_id: goal.contact_id,
      title: goal.title,
      description: goal.description || "",
      category: goal.category || "",
      target_date: goal.target_date || "",
    });
    setMilestones([]);
    setShowDialog(true);
  };

  const addMilestoneField = () => {
    setMilestones([...milestones, { title: "", description: "", target_date: "" }]);
  };

  const updateMilestone = (index: number, field: keyof MilestoneInput, value: string) => {
    const updated = [...milestones];
    updated[index][field] = value;
    setMilestones(updated);
  };

  const removeMilestone = (index: number) => {
    setMilestones(milestones.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    if (!token || !formData.contact_id || !formData.title.trim()) return;
    try {
      setSaving(true);
      if (editingGoal) {
        await goalsApi.update(token, editingGoal.id, {
          title: formData.title.trim(),
          description: formData.description.trim() || undefined,
          category: formData.category || undefined,
          target_date: formData.target_date || undefined,
        });
        toast.success("Goal updated");
      } else {
        const validMilestones = milestones
          .filter((m) => m.title.trim())
          .map((m, i) => ({
            title: m.title.trim(),
            description: m.description.trim() || undefined,
            target_date: m.target_date || undefined,
            sort_order: i,
          }));

        await goalsApi.create(token, {
          contact_id: formData.contact_id,
          title: formData.title.trim(),
          description: formData.description.trim() || undefined,
          category: formData.category || undefined,
          target_date: formData.target_date || undefined,
          milestones: validMilestones.length > 0 ? validMilestones : undefined,
        });
        toast.success("Goal created");
      }
      setShowDialog(false);
      loadGoals();
    } catch (error) {
      console.error("Failed to save goal:", error);
      toast.error("Failed to save goal");
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateStatus = async (goal: Goal, newStatus: string) => {
    if (!token) return;
    try {
      await goalsApi.update(token, goal.id, { status: newStatus as any });
      toast.success("Status updated");
      loadGoals();
    } catch (error) {
      console.error("Failed to update status:", error);
      toast.error("Failed to update status");
    }
  };

  const handleDelete = async (id: string) => {
    if (!token) return;
    try {
      await goalsApi.delete(token, id);
      toast.success("Goal deleted");
      setDeletingId(null);
      loadGoals();
    } catch (error) {
      console.error("Failed to delete goal:", error);
      toast.error("Failed to delete goal");
    }
  };

  const handleAddMilestone = async () => {
    if (!token || !addMilestoneGoalId || !newMilestone.title.trim()) return;
    try {
      await goalsApi.addMilestone(token, addMilestoneGoalId, {
        title: newMilestone.title.trim(),
        description: newMilestone.description.trim() || undefined,
        target_date: newMilestone.target_date || undefined,
      });
      toast.success("Milestone added");
      setAddMilestoneGoalId(null);
      setNewMilestone({ title: "", description: "", target_date: "" });
      loadGoals();
    } catch (error) {
      console.error("Failed to add milestone:", error);
      toast.error("Failed to add milestone");
    }
  };

  const handleToggleMilestone = async (goal: Goal, milestone: GoalMilestone) => {
    if (!token) return;
    try {
      await goalsApi.updateMilestone(token, goal.id, milestone.id, {
        is_completed: !milestone.is_completed,
      });
      loadGoals();
    } catch (error) {
      console.error("Failed to update milestone:", error);
      toast.error("Failed to update milestone");
    }
  };

  const handleDeleteMilestone = async (goalId: string, milestoneId: string) => {
    if (!token) return;
    try {
      await goalsApi.deleteMilestone(token, goalId, milestoneId);
      toast.success("Milestone deleted");
      loadGoals();
    } catch (error) {
      console.error("Failed to delete milestone:", error);
      toast.error("Failed to delete milestone");
    }
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <Shell>
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">Goals</h1>
          <p className="text-gray-500">Client goals with milestone tracking</p>
        </div>
        <Button onClick={openNewDialog}>
          <Plus className="h-4 w-4 mr-2" />
          New Goal
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 items-center">
            <Select
              value={filterContact}
              onValueChange={(value) => {
                setFilterContact(value === "all" ? "" : value);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All clients" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All clients</SelectItem>
                {contacts.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.first_name} {c.last_name || ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={filterStatus}
              onValueChange={(value) => {
                setFilterStatus(value === "all" ? "" : value);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="abandoned">Abandoned</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Goals List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : goals.length === 0 ? (
            <div className="p-8 text-center">
              <Target className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">No goals</h3>
              <p className="text-gray-500 mt-1">
                Create goals to help clients track their progress
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {goals.map((goal) => {
                const isExpanded = expandedGoals.has(goal.id);

                return (
                  <div key={goal.id} className="p-4">
                    <div className="flex items-start gap-4">
                      <div
                        className="flex-shrink-0 pt-1 cursor-pointer"
                        onClick={() => toggleExpand(goal.id)}
                      >
                        {goal.status === "completed" ? (
                          <Trophy className="h-5 w-5 text-green-500" />
                        ) : goal.status === "abandoned" ? (
                          <XCircle className="h-5 w-5 text-gray-400" />
                        ) : (
                          <Target className="h-5 w-5 text-blue-500" />
                        )}
                      </div>
                      <div
                        className="flex-1 min-w-0 cursor-pointer"
                        onClick={() => toggleExpand(goal.id)}
                      >
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium text-gray-900">
                            {goal.title}
                          </span>
                          <Badge className={statusColors[goal.status]}>
                            {goal.status}
                          </Badge>
                          {goal.category && (
                            <Badge
                              className={
                                categoryColors[goal.category] ||
                                "bg-gray-100 text-gray-700"
                              }
                            >
                              {goal.category}
                            </Badge>
                          )}
                        </div>
                        {goal.description && (
                          <p className="text-sm text-gray-600 mt-1 line-clamp-1">
                            {goal.description}
                          </p>
                        )}
                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-400 flex-wrap">
                          <span className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {goal.contact_name}
                          </span>
                          {goal.target_date && (
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {format(new Date(goal.target_date), "MMM d, yyyy")}
                            </span>
                          )}
                        </div>

                        {/* Progress */}
                        <div className="mt-3 max-w-md">
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-gray-500">
                              {goal.milestones.filter((m) => m.is_completed).length}/
                              {goal.milestones.length} milestones
                            </span>
                            <span className="font-medium">{goal.progress_percent}%</span>
                          </div>
                          <Progress value={goal.progress_percent} className="h-1.5" />
                        </div>
                      </div>
                      <div className="flex-shrink-0 flex items-center gap-2">
                        {goal.status === "active" && (
                          <Select
                            value={goal.status}
                            onValueChange={(value) => handleUpdateStatus(goal, value)}
                          >
                            <SelectTrigger className="w-32 h-8 text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="active">Active</SelectItem>
                              <SelectItem value="completed">Completed</SelectItem>
                              <SelectItem value="abandoned">Abandoned</SelectItem>
                            </SelectContent>
                          </Select>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => toggleExpand(goal.id)}
                        >
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </Button>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEditDialog(goal)}>
                              <Pencil className="h-4 w-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => setAddMilestoneGoalId(goal.id)}
                            >
                              <Plus className="h-4 w-4 mr-2" />
                              Add Milestone
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-red-600"
                              onClick={() => setDeletingId(goal.id)}
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>

                    {/* Expanded Milestones */}
                    {isExpanded && (
                      <div className="mt-4 ml-9 pl-4 border-l-2 border-gray-100">
                        {goal.milestones.length === 0 ? (
                          <p className="text-sm text-gray-400 italic">
                            No milestones. Add milestones to track progress.
                          </p>
                        ) : (
                          <div className="space-y-2">
                            {goal.milestones
                              .sort((a, b) => a.sort_order - b.sort_order)
                              .map((m) => (
                                <div
                                  key={m.id}
                                  className="flex items-center gap-3 group"
                                >
                                  <button
                                    onClick={() => handleToggleMilestone(goal, m)}
                                    className="flex-shrink-0"
                                  >
                                    {m.is_completed ? (
                                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                                    ) : (
                                      <Circle className="h-4 w-4 text-gray-300" />
                                    )}
                                  </button>
                                  <span
                                    className={`text-sm flex-1 ${
                                      m.is_completed
                                        ? "text-gray-400 line-through"
                                        : "text-gray-700"
                                    }`}
                                  >
                                    {m.title}
                                  </span>
                                  {m.target_date && (
                                    <span className="text-xs text-gray-400">
                                      {format(new Date(m.target_date), "MMM d")}
                                    </span>
                                  )}
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-6 w-6 opacity-0 group-hover:opacity-100"
                                    onClick={() =>
                                      handleDeleteMilestone(goal.id, m.id)
                                    }
                                  >
                                    <Trash2 className="h-3 w-3 text-gray-400" />
                                  </Button>
                                </div>
                              ))}
                          </div>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="mt-2 text-gray-500"
                          onClick={() => setAddMilestoneGoalId(goal.id)}
                        >
                          <Plus className="h-3 w-3 mr-1" />
                          Add Milestone
                        </Button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of{" "}
            {total}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page === totalPages}
              onClick={() => setPage(page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingGoal ? "Edit Goal" : "New Goal"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Client</label>
              <Select
                value={formData.contact_id}
                onValueChange={(value) =>
                  setFormData({ ...formData, contact_id: value })
                }
                disabled={!!editingGoal}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a client..." />
                </SelectTrigger>
                <SelectContent>
                  {contacts.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.first_name} {c.last_name || ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Goal Title</label>
              <Input
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                placeholder="What's the goal?"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Description (optional)</label>
              <Textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="Add more details..."
                rows={2}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Category (optional)</label>
                <Select
                  value={formData.category}
                  onValueChange={(value) =>
                    setFormData({ ...formData, category: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select..." />
                  </SelectTrigger>
                  <SelectContent>
                    {categoryOptions.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Target Date (optional)</label>
                <Input
                  type="date"
                  value={formData.target_date}
                  onChange={(e) =>
                    setFormData({ ...formData, target_date: e.target.value })
                  }
                />
              </div>
            </div>

            {/* Milestones (only for new goals) */}
            {!editingGoal && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Milestones</label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={addMilestoneField}
                  >
                    <Plus className="h-3 w-3 mr-1" />
                    Add
                  </Button>
                </div>
                {milestones.length === 0 ? (
                  <p className="text-sm text-gray-400 italic">
                    No milestones. Add milestones to track progress.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {milestones.map((m, i) => (
                      <div key={i} className="flex gap-2 items-start">
                        <Input
                          value={m.title}
                          onChange={(e) =>
                            updateMilestone(i, "title", e.target.value)
                          }
                          placeholder="Milestone title"
                          className="flex-1"
                        />
                        <Input
                          type="date"
                          value={m.target_date}
                          onChange={(e) =>
                            updateMilestone(i, "target_date", e.target.value)
                          }
                          className="w-36"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeMilestone(i)}
                        >
                          <Trash2 className="h-4 w-4 text-gray-400" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setShowDialog(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={
                  !formData.contact_id || !formData.title.trim() || saving
                }
              >
                {saving ? "Saving..." : editingGoal ? "Save Changes" : "Create"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Add Milestone Dialog */}
      <Dialog
        open={!!addMilestoneGoalId}
        onOpenChange={() => setAddMilestoneGoalId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Milestone</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Title</label>
              <Input
                value={newMilestone.title}
                onChange={(e) =>
                  setNewMilestone({ ...newMilestone, title: e.target.value })
                }
                placeholder="What needs to be achieved?"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Description (optional)</label>
              <Textarea
                value={newMilestone.description}
                onChange={(e) =>
                  setNewMilestone({
                    ...newMilestone,
                    description: e.target.value,
                  })
                }
                placeholder="Add details..."
                rows={2}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Target Date (optional)</label>
              <Input
                type="date"
                value={newMilestone.target_date}
                onChange={(e) =>
                  setNewMilestone({
                    ...newMilestone,
                    target_date: e.target.value,
                  })
                }
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                onClick={() => setAddMilestoneGoalId(null)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleAddMilestone}
                disabled={!newMilestone.title.trim()}
              >
                Add Milestone
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deletingId} onOpenChange={() => setDeletingId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Goal</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-gray-600">
              Are you sure you want to delete this goal and all its milestones?
              This cannot be undone.
            </p>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setDeletingId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deletingId && handleDelete(deletingId)}
            >
              Delete
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
    </Shell>
  );
}
