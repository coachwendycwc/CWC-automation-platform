"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { offboardingApi, contactsApi, projectsApi, contractsApi } from "@/lib/api";
import {
  ArrowLeft,
  User,
  FolderKanban,
  FileText,
  MessageSquare,
  Quote,
  Award,
} from "lucide-react";
import Link from "next/link";

interface Contact {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  contact_type: string;
}

interface Project {
  id: string;
  title: string;
  project_number: string;
  status: string;
}

interface Contract {
  id: string;
  title: string;
  contract_number: string;
  status: string;
}

export default function NewOffboardingPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  // Form state
  const [contactId, setContactId] = useState<string>("");
  const [workflowType, setWorkflowType] = useState<string>("client");
  const [relatedProjectId, setRelatedProjectId] = useState<string>("");
  const [relatedContractId, setRelatedContractId] = useState<string>("");
  const [sendSurvey, setSendSurvey] = useState(true);
  const [requestTestimonial, setRequestTestimonial] = useState(true);
  const [sendCertificate, setSendCertificate] = useState(false);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    // Load projects and contracts for selected contact
    if (contactId) {
      loadRelatedData(contactId);
    } else {
      setProjects([]);
      setContracts([]);
    }
  }, [contactId]);

  const loadData = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const contactsData = await contactsApi.list(token, { size: 500 });
      setContacts(contactsData.items || []);
    } catch (err) {
      console.error("Failed to load contacts:", err);
    } finally {
      setLoadingData(false);
    }
  };

  const loadRelatedData = async (contactId: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const [projectsData, contractsData] = await Promise.all([
        projectsApi.list(token, { contact_id: contactId }),
        contractsApi.list(token, { contact_id: contactId }),
      ]);

      setProjects(projectsData || []);
      setContracts(contractsData || []);
    } catch (err) {
      console.error("Failed to load related data:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!contactId) {
      alert("Please select a contact");
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const data = {
        contact_id: contactId,
        workflow_type: workflowType as "client" | "project" | "contract",
        related_project_id: relatedProjectId || undefined,
        related_contract_id: relatedContractId || undefined,
        send_survey: sendSurvey,
        request_testimonial: requestTestimonial,
        send_certificate: sendCertificate,
        notes: notes || undefined,
      };

      const workflow = await offboardingApi.initiate(token, data);
      router.push(`/offboarding/${workflow.id}`);
    } catch (err: any) {
      alert(err.message || "Failed to create offboarding workflow");
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <Shell>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading...</div>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/offboarding">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">New Offboarding Workflow</h1>
            <p className="text-gray-500">Start the offboarding process for a client</p>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Contact Selection */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-lg">Select Contact</CardTitle>
              <CardDescription>Choose the client to offboard</CardDescription>
            </CardHeader>
            <CardContent>
              <Select value={contactId} onValueChange={setContactId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a contact..." />
                </SelectTrigger>
                <SelectContent>
                  {contacts.map((contact) => (
                    <SelectItem key={contact.id} value={contact.id}>
                      {contact.first_name} {contact.last_name} ({contact.email})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {/* Workflow Type */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-lg">Workflow Type</CardTitle>
              <CardDescription>What type of offboarding is this?</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <button
                  type="button"
                  onClick={() => setWorkflowType("client")}
                  className={`p-4 rounded-lg border-2 text-center transition-colors ${
                    workflowType === "client"
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <User className="h-8 w-8 mx-auto mb-2 text-gray-600" />
                  <div className="font-medium">Client</div>
                  <div className="text-xs text-gray-500">Engagement ends</div>
                </button>

                <button
                  type="button"
                  onClick={() => setWorkflowType("project")}
                  className={`p-4 rounded-lg border-2 text-center transition-colors ${
                    workflowType === "project"
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <FolderKanban className="h-8 w-8 mx-auto mb-2 text-gray-600" />
                  <div className="font-medium">Project</div>
                  <div className="text-xs text-gray-500">Project completed</div>
                </button>

                <button
                  type="button"
                  onClick={() => setWorkflowType("contract")}
                  className={`p-4 rounded-lg border-2 text-center transition-colors ${
                    workflowType === "contract"
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <FileText className="h-8 w-8 mx-auto mb-2 text-gray-600" />
                  <div className="font-medium">Contract</div>
                  <div className="text-xs text-gray-500">Contract ends</div>
                </button>
              </div>

              {/* Related Project/Contract Selection */}
              {workflowType === "project" && projects.length > 0 && (
                <div className="mt-4">
                  <Label>Related Project</Label>
                  <Select value={relatedProjectId} onValueChange={setRelatedProjectId}>
                    <SelectTrigger className="mt-1">
                      <SelectValue placeholder="Select a project..." />
                    </SelectTrigger>
                    <SelectContent>
                      {projects.map((project) => (
                        <SelectItem key={project.id} value={project.id}>
                          {project.project_number} - {project.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {workflowType === "contract" && contracts.length > 0 && (
                <div className="mt-4">
                  <Label>Related Contract</Label>
                  <Select value={relatedContractId} onValueChange={setRelatedContractId}>
                    <SelectTrigger className="mt-1">
                      <SelectValue placeholder="Select a contract..." />
                    </SelectTrigger>
                    <SelectContent>
                      {contracts.map((contract) => (
                        <SelectItem key={contract.id} value={contract.id}>
                          {contract.contract_number} - {contract.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Options */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-lg">Options</CardTitle>
              <CardDescription>Configure what happens during offboarding</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-5 w-5 text-purple-500" />
                  <div>
                    <div className="font-medium">Send Feedback Survey</div>
                    <div className="text-sm text-gray-500">Request feedback about their experience</div>
                  </div>
                </div>
                <Switch checked={sendSurvey} onCheckedChange={setSendSurvey} />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Quote className="h-5 w-5 text-green-500" />
                  <div>
                    <div className="font-medium">Request Testimonial</div>
                    <div className="text-sm text-gray-500">Ask for a testimonial to share</div>
                  </div>
                </div>
                <Switch checked={requestTestimonial} onCheckedChange={setRequestTestimonial} />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Award className="h-5 w-5 text-yellow-500" />
                  <div>
                    <div className="font-medium">Send Certificate</div>
                    <div className="text-sm text-gray-500">Send a completion certificate</div>
                  </div>
                </div>
                <Switch checked={sendCertificate} onCheckedChange={setSendCertificate} />
              </div>
            </CardContent>
          </Card>

          {/* Notes */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-lg">Notes</CardTitle>
              <CardDescription>Any additional notes about this offboarding</CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add any notes or context for this offboarding..."
                rows={4}
              />
            </CardContent>
          </Card>

          {/* Submit */}
          <div className="flex gap-4">
            <Link href="/offboarding" className="flex-1">
              <Button type="button" variant="outline" className="w-full">
                Cancel
              </Button>
            </Link>
            <Button type="submit" className="flex-1" disabled={loading || !contactId}>
              {loading ? "Creating..." : "Start Offboarding"}
            </Button>
          </div>
        </form>
      </div>
    </Shell>
  );
}
