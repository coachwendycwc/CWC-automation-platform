"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { toast } from "sonner";
import { Shell } from "@/components/layout/Shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  ArrowLeft,
  Mail,
  Phone,
  Building2,
  Calendar,
  Edit,
  Trash2,
  Plus,
  UserMinus,
  MessageSquare,
  Send,
  ArrowDownLeft,
  ArrowUpRight,
  ClipboardCheck,
  Clock,
  CheckCircle,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import { contactsApi, interactionsApi, offboardingApi, notesApi, onboardingAssessmentsApi, Note, OnboardingAssessmentResponse } from "@/lib/api";
import { ContactWithOrganization, Interaction } from "@/types";
import { getInitials, formatDateTime } from "@/lib/utils";

export default function ContactDetailPage() {
  const router = useRouter();
  const params = useParams();
  const contactId = params.id as string;

  const [user, setUser] = useState<any>(null);
  const [contact, setContact] = useState<ContactWithOrganization | null>(null);
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [noteContent, setNoteContent] = useState("");
  const [savingNote, setSavingNote] = useState(false);

  // Client notes (two-way messaging)
  const [clientNotes, setClientNotes] = useState<Note[]>([]);
  const [clientNoteContent, setClientNoteContent] = useState("");
  const [sendingClientNote, setSendingClientNote] = useState(false);

  // Onboarding assessment
  const [assessment, setAssessment] = useState<OnboardingAssessmentResponse | null>(null);
  const [assessmentLoading, setAssessmentLoading] = useState(true);
  const [resendingAssessment, setResendingAssessment] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const userData = localStorage.getItem("user");

    if (!token) {
      router.push("/");
      return;
    }

    if (userData) {
      setUser(JSON.parse(userData));
    }

    fetchContact(token);
    fetchInteractions(token);
    fetchClientNotes(token);
    fetchAssessment(token);
  }, [router, contactId]);

  const fetchContact = async (token: string) => {
    try {
      const data = await contactsApi.get(token, contactId);
      setContact(data);
    } catch (error) {
      console.error("Failed to fetch contact:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchInteractions = async (token: string) => {
    try {
      const data = await interactionsApi.listForContact(token, contactId);
      setInteractions(data.items);
    } catch (error) {
      console.error("Failed to fetch interactions:", error);
    }
  };

  const fetchClientNotes = async (token: string) => {
    try {
      const data = await notesApi.list(token, { contact_id: contactId, size: 5 });
      setClientNotes(data.items);
    } catch (error) {
      console.error("Failed to fetch client notes:", error);
    }
  };

  const fetchAssessment = async (token: string) => {
    try {
      const data = await onboardingAssessmentsApi.getForContact(token, contactId);
      setAssessment(data);
    } catch (error: any) {
      // 404 is expected if no assessment exists yet
      if (error.status !== 404) {
        console.error("Failed to fetch assessment:", error);
      }
    } finally {
      setAssessmentLoading(false);
    }
  };

  const handleCreateAssessment = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    setResendingAssessment(true);
    try {
      const data = await onboardingAssessmentsApi.createForContact(token, contactId);
      setAssessment(data);
      toast.success("Assessment created and email sent");
    } catch (error: any) {
      console.error("Failed to create assessment:", error);
      toast.error(error.message || "Failed to create assessment");
    } finally {
      setResendingAssessment(false);
    }
  };

  const handleResendAssessment = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    setResendingAssessment(true);
    try {
      await onboardingAssessmentsApi.resendEmail(token, contactId);
      toast.success("Assessment email resent");
    } catch (error: any) {
      console.error("Failed to resend assessment:", error);
      toast.error(error.message || "Failed to resend email");
    } finally {
      setResendingAssessment(false);
    }
  };

  const handleSendClientNote = async () => {
    const token = localStorage.getItem("token");
    if (!token || !clientNoteContent.trim()) return;

    setSendingClientNote(true);
    try {
      await notesApi.create(token, {
        contact_id: contactId,
        content: clientNoteContent.trim(),
      });
      setClientNoteContent("");
      toast.success("Note sent to client");
      fetchClientNotes(token);
    } catch (error) {
      console.error("Failed to send note:", error);
      toast.error("Failed to send note");
    } finally {
      setSendingClientNote(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this contact?")) return;

    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      await contactsApi.delete(token, contactId);
      toast.success("Contact deleted successfully");
      router.push("/contacts");
    } catch (error) {
      console.error("Failed to delete contact:", error);
      toast.error("Failed to delete contact");
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token || !noteContent.trim()) return;

    setSavingNote(true);
    try {
      await interactionsApi.create(token, {
        contact_id: contactId,
        interaction_type: "note",
        content: noteContent,
      });
      setNoteContent("");
      setShowNoteForm(false);
      toast.success("Note added");
      fetchInteractions(token);
    } catch (error) {
      console.error("Failed to add note:", error);
      toast.error("Failed to add note");
    } finally {
      setSavingNote(false);
    }
  };

  const handleStartOffboarding = async () => {
    if (!confirm("Start offboarding workflow for this contact?")) return;

    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const workflow = await offboardingApi.initiate(token, {
        contact_id: contactId,
        workflow_type: "client",
      });
      toast.success("Offboarding workflow started");
      router.push(`/offboarding/${workflow.id}`);
    } catch (error: any) {
      console.error("Failed to start offboarding:", error);
      toast.error(error.message || "Failed to start offboarding");
    }
  };

  const getInteractionIcon = (type: string) => {
    switch (type) {
      case "email":
        return <Mail className="h-4 w-4" />;
      case "call":
        return <Phone className="h-4 w-4" />;
      case "meeting":
        return <Calendar className="h-4 w-4" />;
      default:
        return <Edit className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <Shell user={user}>
        <div className="text-center py-8 text-gray-500">Loading...</div>
      </Shell>
    );
  }

  if (!contact) {
    return (
      <Shell user={user}>
        <div className="text-center py-8">
          <p className="text-gray-500">Contact not found</p>
          <Button className="mt-4" onClick={() => router.push("/contacts")}>
            Back to Contacts
          </Button>
        </div>
      </Shell>
    );
  }

  return (
    <Shell user={user}>
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Info */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <Avatar className="h-16 w-16">
                      <AvatarFallback className="text-lg">
                        {getInitials(
                          `${contact.first_name} ${contact.last_name || ""}`
                        )}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h1 className="text-2xl font-bold">
                        {contact.first_name} {contact.last_name}
                      </h1>
                      {contact.title && (
                        <p className="text-gray-500">{contact.title}</p>
                      )}
                      <div className="flex gap-2 mt-2">
                        <Badge
                          variant={
                            contact.contact_type === "client"
                              ? "success"
                              : contact.contact_type === "lead"
                              ? "warning"
                              : "secondary"
                          }
                        >
                          {contact.contact_type}
                        </Badge>
                        {contact.coaching_type && (
                          <Badge variant="outline">
                            {contact.coaching_type} coaching
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled>
                      <Edit className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleDelete}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  {contact.email && (
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-gray-400" />
                      <a
                        href={`mailto:${contact.email}`}
                        className="text-blue-600 hover:underline"
                      >
                        {contact.email}
                      </a>
                    </div>
                  )}
                  {contact.phone && (
                    <div className="flex items-center gap-2">
                      <Phone className="h-4 w-4 text-gray-400" />
                      <a
                        href={`tel:${contact.phone}`}
                        className="text-blue-600 hover:underline"
                      >
                        {contact.phone}
                      </a>
                    </div>
                  )}
                  {contact.organization && (
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-gray-400" />
                      <span>{contact.organization.name}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Activity Timeline */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Activity</CardTitle>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowNoteForm(!showNoteForm)}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Note
                </Button>
              </CardHeader>
              <CardContent>
                {showNoteForm && (
                  <form onSubmit={handleAddNote} className="mb-4">
                    <textarea
                      value={noteContent}
                      onChange={(e) => setNoteContent(e.target.value)}
                      placeholder="Write a note..."
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[100px]"
                    />
                    <div className="flex gap-2 mt-2">
                      <Button type="submit" size="sm" disabled={savingNote}>
                        {savingNote ? "Saving..." : "Save Note"}
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => setShowNoteForm(false)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </form>
                )}

                {interactions.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">
                    No activity yet. Add a note to get started.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {interactions.map((interaction) => (
                      <div
                        key={interaction.id}
                        className="flex gap-3 border-l-2 border-gray-200 pl-4"
                      >
                        <div className="mt-1 rounded-full bg-gray-100 p-2">
                          {getInteractionIcon(interaction.interaction_type)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs">
                              {interaction.interaction_type}
                            </Badge>
                            <span className="text-xs text-gray-400">
                              {formatDateTime(interaction.created_at)}
                            </span>
                          </div>
                          {interaction.subject && (
                            <p className="font-medium mt-1">
                              {interaction.subject}
                            </p>
                          )}
                          {interaction.content && (
                            <p className="text-gray-600 text-sm mt-1 whitespace-pre-wrap">
                              {interaction.content}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            {contact.contact_type === "client" && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Actions</CardTitle>
                </CardHeader>
                <CardContent>
                  <Button
                    variant="outline"
                    className="w-full justify-start text-orange-600 hover:text-orange-700 hover:bg-orange-50"
                    onClick={handleStartOffboarding}
                  >
                    <UserMinus className="h-4 w-4 mr-2" />
                    Start Offboarding
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Client Notes */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <MessageSquare className="h-4 w-4" />
                    Client Notes
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs"
                    onClick={() => {
                      const token = localStorage.getItem("token");
                      if (token) {
                        window.location.href = `/notes?contact=${contactId}`;
                      }
                    }}
                  >
                    View All
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Recent notes */}
                {clientNotes.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-2">
                    No messages yet
                  </p>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {clientNotes.slice(0, 3).map((note) => (
                      <div
                        key={note.id}
                        className="text-sm p-2 rounded bg-gray-50"
                      >
                        <div className="flex items-center gap-1 mb-1">
                          {note.direction === "to_coach" ? (
                            <ArrowDownLeft className="h-3 w-3 text-blue-500" />
                          ) : (
                            <ArrowUpRight className="h-3 w-3 text-green-500" />
                          )}
                          <span className="text-xs text-gray-400">
                            {note.direction === "to_coach" ? "From client" : "To client"}
                          </span>
                          {note.direction === "to_coach" && !note.is_read && (
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 ml-1" />
                          )}
                        </div>
                        <p className="text-gray-600 line-clamp-2">{note.content}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Quick compose */}
                <div className="pt-2 border-t">
                  <div className="flex gap-2">
                    <Textarea
                      value={clientNoteContent}
                      onChange={(e) => setClientNoteContent(e.target.value)}
                      placeholder="Send a note..."
                      className="text-sm min-h-[60px] resize-none"
                      rows={2}
                    />
                  </div>
                  <Button
                    size="sm"
                    className="w-full mt-2"
                    onClick={handleSendClientNote}
                    disabled={!clientNoteContent.trim() || sendingClientNote}
                  >
                    <Send className="h-3 w-3 mr-1" />
                    {sendingClientNote ? "Sending..." : "Send Note"}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Onboarding Assessment */}
            {contact.contact_type === "client" && (
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base flex items-center gap-2">
                      <ClipboardCheck className="h-4 w-4" />
                      Onboarding Assessment
                    </CardTitle>
                    {assessment?.completed_at && (
                      <Badge variant="success" className="text-xs">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Completed
                      </Badge>
                    )}
                    {assessment && !assessment.completed_at && (
                      <Badge variant="warning" className="text-xs">
                        <Clock className="h-3 w-3 mr-1" />
                        Pending
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {assessmentLoading ? (
                    <p className="text-sm text-gray-500 text-center py-2">Loading...</p>
                  ) : !assessment ? (
                    <div className="text-center py-2">
                      <p className="text-sm text-gray-500 mb-3">
                        No assessment sent yet
                      </p>
                      <Button
                        size="sm"
                        onClick={handleCreateAssessment}
                        disabled={resendingAssessment}
                        className="w-full"
                      >
                        <Send className="h-3 w-3 mr-1" />
                        {resendingAssessment ? "Sending..." : "Send Assessment"}
                      </Button>
                    </div>
                  ) : (
                    <>
                      {assessment.completed_at ? (
                        <div className="space-y-2">
                          <p className="text-sm text-gray-500">
                            Completed {formatDateTime(assessment.completed_at)}
                          </p>
                          {assessment.role_title && (
                            <p className="text-sm">
                              <span className="text-gray-500">Role:</span>{" "}
                              {assessment.role_title}
                            </p>
                          )}
                          {assessment.organization_industry && (
                            <p className="text-sm">
                              <span className="text-gray-500">Industry:</span>{" "}
                              {assessment.organization_industry}
                            </p>
                          )}
                          <Link
                            href={`/contacts/${contactId}/onboarding`}
                            className="inline-flex items-center text-sm text-violet-600 hover:text-violet-700 font-medium"
                          >
                            View Full Assessment
                            <ExternalLink className="h-3 w-3 ml-1" />
                          </Link>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <p className="text-sm text-gray-500">
                            Sent {formatDateTime(assessment.created_at)}
                          </p>
                          <p className="text-sm text-amber-600">
                            Waiting for client to complete
                          </p>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={handleResendAssessment}
                            disabled={resendingAssessment}
                            className="w-full"
                          >
                            <RefreshCw className={`h-3 w-3 mr-1 ${resendingAssessment ? "animate-spin" : ""}`} />
                            {resendingAssessment ? "Sending..." : "Resend Email"}
                          </Button>
                        </div>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <span className="text-gray-500">Source:</span>
                  <span className="ml-2">{contact.source || "Not set"}</span>
                </div>
                <div>
                  <span className="text-gray-500">Role:</span>
                  <span className="ml-2">{contact.role || "Not set"}</span>
                </div>
                <div>
                  <span className="text-gray-500">Created:</span>
                  <span className="ml-2">
                    {formatDateTime(contact.created_at)}
                  </span>
                </div>
                {contact.tags && contact.tags.length > 0 && (
                  <div>
                    <span className="text-gray-500">Tags:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {contact.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Shell>
  );
}
