"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { extractionsApi } from "@/lib/api";
import {
  Brain,
  FileText,
  CheckCircle,
  Clock,
  AlertCircle,
  Play,
  Eye,
  ThumbsUp,
  ThumbsDown,
  DollarSign,
  Loader2,
} from "lucide-react";

interface ExtractionStats {
  pending_webhooks: number;
  pending_extractions: number;
  approved_today: number;
  total_extracted_value: number;
}

interface Webhook {
  id: string;
  recording_id: string | null;
  meeting_title: string | null;
  attendees: any[] | null;
  duration_seconds: number | null;
  recorded_at: string | null;
  processing_status: string;
  created_at: string;
}

interface Extraction {
  id: string;
  fathom_webhook_id: string;
  contact_id: string | null;
  extracted_data: {
    client_name?: string;
    service_type?: string;
    package_name?: string;
    price?: number;
    is_billable?: boolean;
    key_topics?: string[];
    notes?: string;
  };
  confidence_scores: Record<string, number>;
  confidence_level: string;
  status: string;
  draft_invoice_id: string | null;
  created_at: string;
}

export default function ExtractionsPage() {
  const { token } = useAuth();
  const [stats, setStats] = useState<ExtractionStats | null>(null);
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [extractions, setExtractions] = useState<Extraction[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"webhooks" | "extractions">("webhooks");

  useEffect(() => {
    if (token) {
      loadData();
    }
  }, [token]);

  const loadData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [statsData, webhooksData, extractionsData] = await Promise.all([
        extractionsApi.getStats(token),
        extractionsApi.listWebhooks(token, "pending"),
        extractionsApi.list(token, { limit: 50 }),
      ]);
      setStats(statsData);
      setWebhooks(webhooksData);
      setExtractions(extractionsData.items);
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  };

  const processWebhook = async (webhookId: string) => {
    if (!token) return;
    setProcessingId(webhookId);
    try {
      await extractionsApi.process(token, webhookId);
      await loadData();
    } catch (error: any) {
      alert(error.message || "Failed to process webhook");
    } finally {
      setProcessingId(null);
    }
  };

  const reviewExtraction = async (id: string, action: "approve" | "reject") => {
    if (!token) return;
    try {
      await extractionsApi.review(token, id, { action });
      await loadData();
    } catch (error: any) {
      alert(error.message || "Failed to review extraction");
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    return `${mins} min`;
  };

  const getConfidenceBadge = (level: string) => {
    switch (level) {
      case "high":
        return <Badge className="bg-green-100 text-green-800">High Confidence</Badge>;
      case "medium":
        return <Badge className="bg-yellow-100 text-yellow-800">Medium Confidence</Badge>;
      default:
        return <Badge className="bg-red-100 text-red-800">Low Confidence</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pending":
        return <Badge variant="outline">Pending Review</Badge>;
      case "approved":
        return <Badge className="bg-green-100 text-green-800">Approved</Badge>;
      case "rejected":
        return <Badge className="bg-red-100 text-red-800">Rejected</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <Shell>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Brain className="h-6 w-6" />
            AI Invoice Extraction
          </h1>
          <p className="text-gray-500 mt-1">
            Process Fathom transcripts and generate draft invoices with AI
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Clock className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.pending_webhooks || 0}</p>
                  <p className="text-sm text-gray-500">Pending Webhooks</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-yellow-100 rounded-lg">
                  <AlertCircle className="h-6 w-6 text-yellow-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.pending_extractions || 0}</p>
                  <p className="text-sm text-gray-500">Awaiting Review</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.approved_today || 0}</p>
                  <p className="text-sm text-gray-500">Approved Today</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <DollarSign className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">
                    {formatCurrency(stats?.total_extracted_value || 0)}
                  </p>
                  <p className="text-sm text-gray-500">Total Extracted</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 border-b">
          <button
            onClick={() => setActiveTab("webhooks")}
            className={`pb-2 px-1 font-medium ${
              activeTab === "webhooks"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Pending Webhooks ({webhooks.length})
          </button>
          <button
            onClick={() => setActiveTab("extractions")}
            className={`pb-2 px-1 font-medium ${
              activeTab === "extractions"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Extractions ({extractions.length})
          </button>
        </div>

        {/* Content */}
        {activeTab === "webhooks" && (
          <div className="space-y-4">
            {webhooks.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900">No pending webhooks</h3>
                  <p className="text-gray-500 mt-1">
                    When you record calls with Fathom, they'll appear here for processing
                  </p>
                </CardContent>
              </Card>
            ) : (
              webhooks.map((webhook) => (
                <Card key={webhook.id}>
                  <CardContent className="py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium">
                          {webhook.meeting_title || "Untitled Meeting"}
                        </h3>
                        <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                          {webhook.duration_seconds && (
                            <span>{formatDuration(webhook.duration_seconds)}</span>
                          )}
                          {webhook.attendees && (
                            <span>{webhook.attendees.length} attendees</span>
                          )}
                          <span>
                            {new Date(webhook.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <Button
                        onClick={() => processWebhook(webhook.id)}
                        disabled={processingId === webhook.id}
                      >
                        {processingId === webhook.id ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Processing...
                          </>
                        ) : (
                          <>
                            <Play className="h-4 w-4 mr-2" />
                            Extract Invoice
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        )}

        {activeTab === "extractions" && (
          <div className="space-y-4">
            {extractions.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Brain className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900">No extractions yet</h3>
                  <p className="text-gray-500 mt-1">
                    Process a webhook to see AI-extracted invoice data
                  </p>
                </CardContent>
              </Card>
            ) : (
              extractions.map((extraction) => (
                <Card key={extraction.id}>
                  <CardContent className="py-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          {getStatusBadge(extraction.status)}
                          {getConfidenceBadge(extraction.confidence_level)}
                          {extraction.extracted_data.is_billable === false && (
                            <Badge variant="outline">Not Billable</Badge>
                          )}
                        </div>

                        <h3 className="font-medium">
                          {extraction.extracted_data.client_name || "Unknown Client"}
                        </h3>

                        <div className="mt-2 space-y-1 text-sm">
                          {extraction.extracted_data.service_type && (
                            <p>
                              <span className="text-gray-500">Service:</span>{" "}
                              {extraction.extracted_data.service_type}
                            </p>
                          )}
                          {extraction.extracted_data.package_name && (
                            <p>
                              <span className="text-gray-500">Package:</span>{" "}
                              {extraction.extracted_data.package_name}
                            </p>
                          )}
                          {extraction.extracted_data.price && (
                            <p>
                              <span className="text-gray-500">Price:</span>{" "}
                              {formatCurrency(extraction.extracted_data.price)}
                            </p>
                          )}
                          {extraction.extracted_data.key_topics && (
                            <p>
                              <span className="text-gray-500">Topics:</span>{" "}
                              {extraction.extracted_data.key_topics.slice(0, 3).join(", ")}
                            </p>
                          )}
                        </div>

                        <p className="text-xs text-gray-400 mt-2">
                          {new Date(extraction.created_at).toLocaleString()}
                        </p>
                      </div>

                      {extraction.status === "pending" && (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => reviewExtraction(extraction.id, "reject")}
                          >
                            <ThumbsDown className="h-4 w-4 mr-1" />
                            Reject
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => reviewExtraction(extraction.id, "approve")}
                          >
                            <ThumbsUp className="h-4 w-4 mr-1" />
                            Approve
                          </Button>
                        </div>
                      )}

                      {extraction.status === "approved" && extraction.draft_invoice_id && (
                        <Button size="sm" variant="outline" asChild>
                          <a href={`/invoices/${extraction.draft_invoice_id}`}>
                            <Eye className="h-4 w-4 mr-1" />
                            View Invoice
                          </a>
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        )}
      </div>
    </Shell>
  );
}
