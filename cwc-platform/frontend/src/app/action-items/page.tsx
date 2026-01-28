"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Shell } from "@/components/layout/Shell";
import { actionItemsApi, ActionItem, contactsApi } from "@/lib/api";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
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
  ListTodo,
  Search,
  Plus,
  MoreHorizontal,
  Pencil,
  Trash2,
  Calendar,
  User,
  AlertCircle,
  Clock,
  CheckCircle2,
  Circle,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { format, formatDistanceToNow, isAfter, isBefore, isToday } from "date-fns";

interface Contact {
  id: string;
  first_name: string;
  last_name: string | null;
}

const priorityColors = {
  low: "bg-gray-100 text-gray-700",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-red-100 text-red-700",
};

const statusIcons = {
  pending: Circle,
  in_progress: Clock,
  completed: CheckCircle2,
  skipped: XCircle,
};

const statusColors = {
  pending: "text-gray-500",
  in_progress: "text-blue-500",
  completed: "text-green-500",
  skipped: "text-gray-400",
};

export default function ActionItemsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<ActionItem[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filterContact, setFilterContact] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [filterPriority, setFilterPriority] = useState<string>("");

  // New/Edit dialog
  const [showDialog, setShowDialog] = useState(false);
  const [editingItem, setEditingItem] = useState<ActionItem | null>(null);
  const [formData, setFormData] = useState({
    contact_id: "",
    title: "",
    description: "",
    due_date: "",
    priority: "medium" as "low" | "medium" | "high",
  });
  const [saving, setSaving] = useState(false);

  // Delete confirmation
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    loadItems();
    loadContacts();
  }, [token, page, filterContact, filterStatus, filterPriority]);

  const loadItems = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const result = await actionItemsApi.list(token, {
        page,
        size: 20,
        contact_id: filterContact || undefined,
        status: filterStatus || undefined,
        priority: filterPriority || undefined,
      });
      setItems(result.items);
      setTotal(result.total);
    } catch (error) {
      console.error("Failed to load action items:", error);
      toast.error("Failed to load action items");
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

  const openNewDialog = () => {
    setEditingItem(null);
    setFormData({
      contact_id: "",
      title: "",
      description: "",
      due_date: "",
      priority: "medium",
    });
    setShowDialog(true);
  };

  const openEditDialog = (item: ActionItem) => {
    setEditingItem(item);
    setFormData({
      contact_id: item.contact_id,
      title: item.title,
      description: item.description || "",
      due_date: item.due_date || "",
      priority: item.priority,
    });
    setShowDialog(true);
  };

  const handleSave = async () => {
    if (!token || !formData.contact_id || !formData.title.trim()) return;
    try {
      setSaving(true);
      if (editingItem) {
        await actionItemsApi.update(token, editingItem.id, {
          title: formData.title.trim(),
          description: formData.description.trim() || undefined,
          due_date: formData.due_date || undefined,
          priority: formData.priority,
        });
        toast.success("Action item updated");
      } else {
        await actionItemsApi.create(token, {
          contact_id: formData.contact_id,
          title: formData.title.trim(),
          description: formData.description.trim() || undefined,
          due_date: formData.due_date || undefined,
          priority: formData.priority,
        });
        toast.success("Action item created");
      }
      setShowDialog(false);
      loadItems();
    } catch (error) {
      console.error("Failed to save action item:", error);
      toast.error("Failed to save action item");
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateStatus = async (item: ActionItem, newStatus: string) => {
    if (!token) return;
    try {
      await actionItemsApi.update(token, item.id, { status: newStatus as any });
      toast.success("Status updated");
      loadItems();
    } catch (error) {
      console.error("Failed to update status:", error);
      toast.error("Failed to update status");
    }
  };

  const handleDelete = async (id: string) => {
    if (!token) return;
    try {
      await actionItemsApi.delete(token, id);
      toast.success("Action item deleted");
      setDeletingId(null);
      loadItems();
    } catch (error) {
      console.error("Failed to delete action item:", error);
      toast.error("Failed to delete action item");
    }
  };

  const getDueDateStatus = (dueDate: string | null) => {
    if (!dueDate) return null;
    const date = new Date(dueDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (isBefore(date, today)) {
      return "overdue";
    } else if (isToday(date)) {
      return "today";
    }
    return "upcoming";
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <Shell>
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            Action Items
          </h1>
          <p className="text-gray-500">Tasks assigned to your clients</p>
        </div>
        <Button onClick={openNewDialog}>
          <Plus className="h-4 w-4 mr-2" />
          New Action Item
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
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="skipped">Skipped</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={filterPriority}
              onValueChange={(value) => {
                setFilterPriority(value === "all" ? "" : value);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-36">
                <SelectValue placeholder="All priorities" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All priorities</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Items List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : items.length === 0 ? (
            <div className="p-8 text-center">
              <ListTodo className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">No action items</h3>
              <p className="text-gray-500 mt-1">
                Create action items to assign tasks to your clients
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {items.map((item) => {
                const StatusIcon = statusIcons[item.status];
                const dueDateStatus = getDueDateStatus(item.due_date);

                return (
                  <div
                    key={item.id}
                    className="p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 pt-1">
                        <StatusIcon className={`h-5 w-5 ${statusColors[item.status]}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium text-gray-900">
                            {item.title}
                          </span>
                          <Badge className={priorityColors[item.priority]}>
                            {item.priority}
                          </Badge>
                          {item.status === "completed" && (
                            <Badge className="bg-green-100 text-green-700">completed</Badge>
                          )}
                          {item.status === "skipped" && (
                            <Badge className="bg-gray-100 text-gray-500">skipped</Badge>
                          )}
                        </div>
                        {item.description && (
                          <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                            {item.description}
                          </p>
                        )}
                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-400 flex-wrap">
                          <span className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {item.contact_name}
                          </span>
                          {item.due_date && (
                            <span className={`flex items-center gap-1 ${
                              dueDateStatus === "overdue" ? "text-red-500" :
                              dueDateStatus === "today" ? "text-orange-500" :
                              "text-gray-400"
                            }`}>
                              <Calendar className="h-3 w-3" />
                              {dueDateStatus === "overdue" && "Overdue: "}
                              {dueDateStatus === "today" && "Today"}
                              {dueDateStatus === "upcoming" && format(new Date(item.due_date), "MMM d, yyyy")}
                              {dueDateStatus === "overdue" && format(new Date(item.due_date), "MMM d, yyyy")}
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                          </span>
                        </div>
                      </div>
                      <div className="flex-shrink-0 flex items-center gap-2">
                        {item.status !== "completed" && item.status !== "skipped" && (
                          <Select
                            value={item.status}
                            onValueChange={(value) => handleUpdateStatus(item, value)}
                          >
                            <SelectTrigger className="w-32 h-8 text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="pending">Pending</SelectItem>
                              <SelectItem value="in_progress">In Progress</SelectItem>
                              <SelectItem value="completed">Completed</SelectItem>
                              <SelectItem value="skipped">Skipped</SelectItem>
                            </SelectContent>
                          </Select>
                        )}
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEditDialog(item)}>
                              <Pencil className="h-4 w-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-red-600"
                              onClick={() => setDeletingId(item.id)}
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
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
            Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of {total}
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
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingItem ? "Edit Action Item" : "New Action Item"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Client</label>
              <Select
                value={formData.contact_id}
                onValueChange={(value) => setFormData({ ...formData, contact_id: value })}
                disabled={!!editingItem}
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
              <label className="text-sm font-medium">Title</label>
              <Input
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="What should the client do?"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Description (optional)</label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Add more details..."
                rows={3}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Due Date (optional)</label>
                <Input
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Priority</label>
                <Select
                  value={formData.priority}
                  onValueChange={(value: "low" | "medium" | "high") =>
                    setFormData({ ...formData, priority: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setShowDialog(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={!formData.contact_id || !formData.title.trim() || saving}
              >
                {saving ? "Saving..." : editingItem ? "Save Changes" : "Create"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deletingId} onOpenChange={() => setDeletingId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Action Item</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-gray-600">
              Are you sure you want to delete this action item? This cannot be undone.
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
