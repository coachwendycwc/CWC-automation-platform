"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Shell } from "@/components/layout/Shell";
import { notesApi, Note, contactsApi } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
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
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  MessageSquare,
  Search,
  ArrowDownLeft,
  ArrowUpRight,
  Send,
  Check,
  Clock,
  User,
} from "lucide-react";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";

interface Contact {
  id: string;
  first_name: string;
  last_name: string | null;
}

export default function NotesPage() {
  const { token } = useAuth();
  const [notes, setNotes] = useState<Note[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [filterContact, setFilterContact] = useState<string>("");
  const [filterUnread, setFilterUnread] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // New note dialog
  const [showNewNote, setShowNewNote] = useState(false);
  const [newNoteContact, setNewNoteContact] = useState("");
  const [newNoteContent, setNewNoteContent] = useState("");
  const [sending, setSending] = useState(false);

  // Note detail dialog
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [replyContent, setReplyContent] = useState("");
  const [replying, setReplying] = useState(false);

  useEffect(() => {
    loadNotes();
    loadContacts();
    loadUnreadCount();
  }, [token, page, search, filterContact, filterUnread]);

  const loadNotes = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const result = await notesApi.list(token, {
        page,
        size: 20,
        search: search || undefined,
        contact_id: filterContact || undefined,
        is_read: filterUnread ? false : undefined,
      });
      setNotes(result.items);
      setTotal(result.total);
    } catch (error) {
      console.error("Failed to load notes:", error);
      toast.error("Failed to load notes");
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

  const loadUnreadCount = async () => {
    if (!token) return;
    try {
      const result = await notesApi.getUnreadCount(token);
      setUnreadCount(result.count);
    } catch (error) {
      console.error("Failed to load unread count:", error);
    }
  };

  const handleSendNote = async () => {
    if (!token || !newNoteContact || !newNoteContent.trim()) return;
    try {
      setSending(true);
      await notesApi.create(token, {
        contact_id: newNoteContact,
        content: newNoteContent.trim(),
      });
      toast.success("Note sent");
      setShowNewNote(false);
      setNewNoteContact("");
      setNewNoteContent("");
      loadNotes();
    } catch (error) {
      console.error("Failed to send note:", error);
      toast.error("Failed to send note");
    } finally {
      setSending(false);
    }
  };

  const handleMarkAsRead = async (noteId: string) => {
    if (!token) return;
    try {
      await notesApi.markAsRead(token, noteId);
      loadNotes();
      loadUnreadCount();
    } catch (error) {
      console.error("Failed to mark as read:", error);
    }
  };

  const handleReply = async () => {
    if (!token || !selectedNote || !replyContent.trim()) return;
    try {
      setReplying(true);
      await notesApi.reply(token, selectedNote.id, replyContent.trim());
      toast.success("Reply sent");
      setReplyContent("");
      // Reload the note to get updated replies
      const updated = await notesApi.get(token, selectedNote.id);
      setSelectedNote(updated);
      loadNotes();
    } catch (error) {
      console.error("Failed to send reply:", error);
      toast.error("Failed to send reply");
    } finally {
      setReplying(false);
    }
  };

  const openNoteDetail = async (note: Note) => {
    if (!token) return;
    // Mark as read if it's from client and unread
    if (note.direction === "to_coach" && !note.is_read) {
      await handleMarkAsRead(note.id);
    }
    // Reload to get full details with replies
    const fullNote = await notesApi.get(token, note.id);
    setSelectedNote(fullNote);
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <Shell>
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            Client Notes
            {unreadCount > 0 && (
              <Badge className="bg-red-500 text-white">{unreadCount} new</Badge>
            )}
          </h1>
          <p className="text-gray-500">Messages between you and your clients</p>
        </div>
        <Button onClick={() => setShowNewNote(true)}>
          <Send className="h-4 w-4 mr-2" />
          Send Note
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 items-center">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search notes..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                  className="pl-10"
                />
              </div>
            </div>
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
            <div className="flex items-center gap-2">
              <Checkbox
                id="unread"
                checked={filterUnread}
                onCheckedChange={(checked) => {
                  setFilterUnread(checked === true);
                  setPage(1);
                }}
              />
              <label htmlFor="unread" className="text-sm text-gray-600">
                Unread only
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notes List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : notes.length === 0 ? (
            <div className="p-8 text-center">
              <MessageSquare className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">No notes</h3>
              <p className="text-gray-500 mt-1">
                {filterUnread
                  ? "No unread notes"
                  : "Start by sending a note to a client"}
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {notes.map((note) => (
                <div
                  key={note.id}
                  className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => openNoteDetail(note)}
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0">
                      {note.direction === "to_coach" ? (
                        <div className="p-2 rounded-full bg-blue-100">
                          <ArrowDownLeft className="h-4 w-4 text-blue-600" />
                        </div>
                      ) : (
                        <div className="p-2 rounded-full bg-green-100">
                          <ArrowUpRight className="h-4 w-4 text-green-600" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">
                          {note.contact_name}
                        </span>
                        {note.direction === "to_coach" && !note.is_read && (
                          <span className="w-2 h-2 rounded-full bg-blue-500" />
                        )}
                        {note.replies.length > 0 && (
                          <Badge variant="outline" className="text-xs">
                            {note.replies.length} {note.replies.length === 1 ? "reply" : "replies"}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-2 mt-1">
                        {note.content}
                      </p>
                      <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
                        <Clock className="h-3 w-3" />
                        {formatDistanceToNow(new Date(note.created_at), { addSuffix: true })}
                        <span className="text-gray-300">·</span>
                        {note.direction === "to_coach" ? "From client" : "To client"}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
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

      {/* New Note Dialog */}
      <Dialog open={showNewNote} onOpenChange={setShowNewNote}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send Note to Client</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Select Client</label>
              <Select value={newNoteContact} onValueChange={setNewNoteContact}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a client..." />
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
              <label className="text-sm font-medium">Message</label>
              <Textarea
                value={newNoteContent}
                onChange={(e) => setNewNoteContent(e.target.value)}
                placeholder="Type your message..."
                rows={4}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowNewNote(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleSendNote}
                disabled={!newNoteContact || !newNoteContent.trim() || sending}
              >
                {sending ? "Sending..." : "Send"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Note Detail Dialog */}
      <Dialog open={!!selectedNote} onOpenChange={() => setSelectedNote(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              {selectedNote?.contact_name}
            </DialogTitle>
          </DialogHeader>
          {selectedNote && (
            <div className="space-y-4 pt-2">
              {/* Original note */}
              <div
                className={`p-3 rounded-lg ${
                  selectedNote.direction === "to_coach"
                    ? "bg-blue-50 ml-0 mr-8"
                    : "bg-green-50 ml-8 mr-0"
                }`}
              >
                <p className="text-sm">{selectedNote.content}</p>
                <p className="text-xs text-gray-400 mt-2">
                  {formatDistanceToNow(new Date(selectedNote.created_at), { addSuffix: true })}
                  {" · "}
                  {selectedNote.direction === "to_coach" ? "From client" : "You"}
                </p>
              </div>

              {/* Replies */}
              {selectedNote.replies.map((reply) => (
                <div
                  key={reply.id}
                  className={`p-3 rounded-lg ${
                    reply.direction === "to_coach"
                      ? "bg-blue-50 ml-0 mr-8"
                      : "bg-green-50 ml-8 mr-0"
                  }`}
                >
                  <p className="text-sm">{reply.content}</p>
                  <p className="text-xs text-gray-400 mt-2">
                    {formatDistanceToNow(new Date(reply.created_at), { addSuffix: true })}
                    {" · "}
                    {reply.direction === "to_coach" ? "From client" : "You"}
                  </p>
                </div>
              ))}

              {/* Reply form */}
              <div className="flex gap-2 pt-2 border-t">
                <Textarea
                  value={replyContent}
                  onChange={(e) => setReplyContent(e.target.value)}
                  placeholder="Type a reply..."
                  rows={2}
                  className="flex-1"
                />
                <Button
                  onClick={handleReply}
                  disabled={!replyContent.trim() || replying}
                  size="icon"
                  className="self-end"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
    </Shell>
  );
}
