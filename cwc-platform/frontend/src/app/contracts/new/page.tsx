"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { contractsApi, contractTemplatesApi, contactsApi } from "@/lib/api";
import { ArrowLeft, FileText, User } from "lucide-react";
import Link from "next/link";

interface Template {
  id: string;
  name: string;
  description: string | null;
  category: string;
  merge_fields: string[];
}

interface Contact {
  id: string;
  first_name: string;
  last_name: string | null;
  email: string | null;
  organization_id: string | null;
}

interface MergeFieldInfo {
  name: string;
  description: string;
  category: string;
  sample_value: string;
}

export default function NewContractPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [mergeFieldInfo, setMergeFieldInfo] = useState<{
    auto_fields: MergeFieldInfo[];
    custom_fields: MergeFieldInfo[];
  } | null>(null);

  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [selectedContact, setSelectedContact] = useState<string>("");
  const [title, setTitle] = useState("");
  const [mergeData, setMergeData] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const [templatesData, contactsData, mergeFields] = await Promise.all([
        contractTemplatesApi.list(token, { is_active: true }),
        contactsApi.list(token, { size: 100 }),
        contractTemplatesApi.getMergeFields(token),
      ]);

      setTemplates(templatesData);
      setContacts(contactsData);
      setMergeFieldInfo(mergeFields);
    } catch (err) {
      console.error("Failed to load data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateSelect = (templateId: string) => {
    const template = templates.find((t) => t.id === templateId);
    setSelectedTemplate(template || null);
    if (template) {
      setTitle(`${template.name}`);
      // Reset merge data for custom fields
      const customFields = template.merge_fields.filter((f) =>
        mergeFieldInfo?.custom_fields.some((cf) => cf.name === f)
      );
      const newMergeData: Record<string, string> = {};
      customFields.forEach((f) => {
        newMergeData[f] = "";
      });
      setMergeData(newMergeData);
    }
  };

  const handleContactSelect = (contactId: string) => {
    setSelectedContact(contactId);
    const contact = contacts.find((c) => c.id === contactId);
    if (contact && selectedTemplate) {
      setTitle(`${selectedTemplate.name} - ${contact.first_name} ${contact.last_name || ""}`);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTemplate || !selectedContact || !title) return;

    setSubmitting(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const contract = await contractsApi.create(token, {
        template_id: selectedTemplate.id,
        contact_id: selectedContact,
        title,
        merge_data: mergeData,
        notes: notes || undefined,
      });

      router.push(`/contracts/${contract.id}`);
    } catch (err: any) {
      alert(err.message || "Failed to create contract");
    } finally {
      setSubmitting(false);
    }
  };

  const getCustomFields = () => {
    if (!selectedTemplate || !mergeFieldInfo) return [];
    return selectedTemplate.merge_fields.filter((f) =>
      mergeFieldInfo.custom_fields.some((cf) => cf.name === f)
    );
  };

  if (loading) {
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
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/contracts">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">New Contract</h1>
            <p className="text-gray-500">Create a contract from a template</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Template Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Select Template
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Contract Template *</Label>
                <Select onValueChange={handleTemplateSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a template" />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map((template) => (
                      <SelectItem key={template.id} value={template.id}>
                        <div className="flex flex-col">
                          <span>{template.name}</span>
                          {template.description && (
                            <span className="text-xs text-gray-500">
                              {template.description}
                            </span>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {templates.length === 0 && (
                <div className="text-center py-4 text-gray-500">
                  <p>No templates available.</p>
                  <Link href="/contracts/templates/new">
                    <Button variant="link">Create a template first</Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Client Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Select Client
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Client *</Label>
                <Select value={selectedContact} onValueChange={handleContactSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a client" />
                  </SelectTrigger>
                  <SelectContent>
                    {contacts.map((contact) => (
                      <SelectItem key={contact.id} value={contact.id}>
                        {contact.first_name} {contact.last_name || ""}{" "}
                        {contact.email && `(${contact.email})`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Contract Details */}
          {selectedTemplate && selectedContact && (
            <Card>
              <CardHeader>
                <CardTitle>Contract Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Contract Title *</Label>
                  <Input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g., Executive Coaching Agreement - John Smith"
                    required
                  />
                </div>

                {/* Custom Merge Fields */}
                {getCustomFields().length > 0 && (
                  <div className="space-y-4 pt-4 border-t">
                    <h3 className="font-medium">Custom Fields</h3>
                    <p className="text-sm text-gray-500">
                      Fill in these fields to customize your contract
                    </p>
                    {getCustomFields().map((fieldName) => {
                      const fieldInfo = mergeFieldInfo?.custom_fields.find(
                        (f) => f.name === fieldName
                      );
                      return (
                        <div key={fieldName}>
                          <Label>{fieldInfo?.description || fieldName}</Label>
                          <Input
                            value={mergeData[fieldName] || ""}
                            onChange={(e) =>
                              setMergeData({ ...mergeData, [fieldName]: e.target.value })
                            }
                            placeholder={fieldInfo?.sample_value || `Enter ${fieldName}`}
                          />
                        </div>
                      );
                    })}
                  </div>
                )}

                <div className="pt-4 border-t">
                  <Label>Internal Notes (optional)</Label>
                  <Textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Notes visible only to you"
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Submit */}
          <div className="flex justify-end gap-4">
            <Link href="/contracts">
              <Button variant="outline">Cancel</Button>
            </Link>
            <Button
              type="submit"
              disabled={!selectedTemplate || !selectedContact || !title || submitting}
            >
              {submitting ? "Creating..." : "Create Contract"}
            </Button>
          </div>
        </form>
      </div>
    </Shell>
  );
}
