"use client";

import { useEffect, useState, useRef } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, MessageSquare } from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";

interface Note {
  id: string;
  content: string;
  direction: "to_coach" | "to_client";
  is_read: boolean;
  created_at: string;
}

export default function ClientNotesPage() {
  const { sessionToken } = useClientAuth();
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [newMessage, setNewMessage] = useState("");
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadNotes();
  }, [sessionToken]);

  useEffect(() => {
    // Scroll to bottom when notes change
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [notes]);

  const loadNotes = async () => {
    if (!sessionToken) return;
    try {
      setLoading(true);
      const data = await clientPortalApi.getNotes(sessionToken);
      setNotes(data);

      // Mark unread coach notes as read
      for (const note of data) {
        if (note.direction === "to_client" && !note.is_read) {
          try {
            await clientPortalApi.markNoteRead(sessionToken, note.id);
          } catch (error) {
            console.error("Failed to mark note as read:", error);
          }
        }
      }
    } catch (error) {
      console.error("Failed to load notes:", error);
      toast.error("Failed to load messages");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!sessionToken || !newMessage.trim()) return;

    try {
      setSending(true);
      const note = await clientPortalApi.createNote(sessionToken, newMessage.trim());
      setNotes([...notes, note]);
      setNewMessage("");
    } catch (error) {
      console.error("Failed to send message:", error);
      toast.error("Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return format(date, "'Today at' h:mm a");
    } else if (date.toDateString() === yesterday.toDateString()) {
      return format(date, "'Yesterday at' h:mm a");
    } else {
      return format(date, "MMM d, yyyy 'at' h:mm a");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading messages...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Messages</h1>
        <p className="text-gray-500">
          Send notes and updates to your coach
        </p>
      </div>

      <Card className="h-[calc(100vh-280px)] flex flex-col">
        <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {notes.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <MessageSquare className="h-12 w-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900">No messages yet</h3>
                <p className="text-gray-500 mt-1">
                  Send a message to your coach to get started
                </p>
              </div>
            ) : (
              <>
                {notes.map((note, index) => {
                  const isFromCoach = note.direction === "to_client";
                  const showDate =
                    index === 0 ||
                    new Date(note.created_at).toDateString() !==
                      new Date(notes[index - 1].created_at).toDateString();

                  return (
                    <div key={note.id}>
                      {showDate && (
                        <div className="flex justify-center my-4">
                          <span className="text-xs text-gray-400 bg-gray-100 px-3 py-1 rounded-full">
                            {format(new Date(note.created_at), "EEEE, MMMM d, yyyy")}
                          </span>
                        </div>
                      )}
                      <div
                        className={`flex ${isFromCoach ? "justify-start" : "justify-end"}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                            isFromCoach
                              ? "bg-gray-100 text-gray-900 rounded-bl-md"
                              : "bg-gray-900 text-white rounded-br-md"
                          }`}
                        >
                          <p className="text-sm whitespace-pre-wrap">{note.content}</p>
                          <p
                            className={`text-xs mt-1 ${
                              isFromCoach ? "text-gray-500" : "text-gray-400"
                            }`}
                          >
                            {format(new Date(note.created_at), "h:mm a")}
                          </p>
                        </div>
                      </div>
                      {isFromCoach && index === notes.length - 1 && (
                        <p className="text-xs text-gray-400 mt-1 ml-1">Coach</p>
                      )}
                    </div>
                  );
                })}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t p-4 bg-gray-50">
            <div className="flex gap-3">
              <Textarea
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message..."
                className="flex-1 min-h-[44px] max-h-32 resize-none bg-white"
                rows={1}
              />
              <Button
                onClick={handleSend}
                disabled={!newMessage.trim() || sending}
                size="icon"
                className="h-11 w-11"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
