"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { contractsApi, offboardingApi } from "@/lib/api";
import {
  ArrowLeft,
  Send,
  Copy,
  Download,
  XCircle,
  Clock,
  CheckCircle,
  Eye,
  ExternalLink,
  RefreshCw,
  UserMinus,
} from "lucide-react";
import Link from "next/link";

interface Contract {
  id: string;
  contract_number: string;
  title: string;
  content: string;
  status: string;
  contact_id: string;
  contact_name: string | null;
  contact_email: string | null;
  organization_name: string | null;
  template_name: string | null;
  signer_name: string | null;
  signer_email: string | null;
  signature_type: string | null;
  signed_at: string | null;
  sent_at: string | null;
  viewed_at: string | null;
  expires_at: string | null;
  declined_at: string | null;
  decline_reason: string | null;
  view_token: string;
  notes: string | null;
  linked_invoice_id: string | null;
  linked_invoice_number: string | null;
  created_at: string;
  updated_at: string;
  audit_logs: AuditLog[];
}

interface AuditLog {
  id: string;
  action: string;
  actor_email: string | null;
  ip_address: string | null;
  user_agent: string | null;
  details: Record<string, any> | null;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-800",
  sent: "bg-blue-100 text-blue-800",
  viewed: "bg-purple-100 text-purple-800",
  signed: "bg-green-100 text-green-800",
  expired: "bg-orange-100 text-orange-800",
  declined: "bg-red-100 text-red-800",
  void: "bg-gray-100 text-gray-500",
};

const ACTION_LABELS: Record<string, string> = {
  created: "Contract created",
  sent: "Sent for signature",
  resent: "Reminder sent",
  viewed: "Viewed by recipient",
  signed: "Contract signed",
  declined: "Contract declined",
  expired: "Contract expired",
  voided: "Contract voided",
};

export default function ContractDetailPage() {
  const params = useParams();
  const router = useRouter();
  const contractId = params.id as string;

  const [contract, setContract] = useState<Contract | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (contractId) {
      loadContract();
    }
  }, [contractId]);

  const loadContract = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const data = await contractsApi.get(token, contractId);
      setContract(data);
    } catch (err) {
      console.error("Failed to load contract:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!contract) return;
    setActionLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await contractsApi.send(token, contract.id);
      toast.success("Contract sent for signature");
      await loadContract();
    } catch (err: any) {
      toast.error(err.message || "Failed to send contract");
    } finally {
      setActionLoading(false);
    }
  };

  const handleResend = async () => {
    if (!contract) return;
    setActionLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await contractsApi.resend(token, contract.id);
      toast.success("Reminder sent");
      await loadContract();
    } catch (err: any) {
      toast.error(err.message || "Failed to resend contract");
    } finally {
      setActionLoading(false);
    }
  };

  const handleVoid = async () => {
    if (!contract) return;
    const reason = window.prompt("Reason for voiding this contract (optional):");
    if (reason === null) return; // cancelled

    setActionLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await contractsApi.void(token, contract.id, reason);
      toast.success("Contract voided");
      await loadContract();
    } catch (err: any) {
      toast.error(err.message || "Failed to void contract");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDuplicate = async () => {
    if (!contract) return;
    setActionLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      const newContract = await contractsApi.duplicate(token, contract.id);
      toast.success("Contract duplicated");
      router.push(`/contracts/${newContract.id}`);
    } catch (err: any) {
      toast.error(err.message || "Failed to duplicate contract");
    } finally {
      setActionLoading(false);
    }
  };

  const getSigningLink = () => {
    if (!contract) return "";
    const baseUrl = typeof window !== "undefined" ? window.location.origin : "";
    return `${baseUrl}/sign/${contract.view_token}`;
  };

  const copySigningLink = () => {
    navigator.clipboard.writeText(getSigningLink());
    toast.success("Signing link copied to clipboard");
  };

  const handleCloseAndOffboard = async () => {
    if (!confirm("Close this contract and start offboarding for the client?")) return;

    setActionLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token || !contract) return;

      // Start offboarding workflow
      const workflow = await offboardingApi.initiate(token, {
        contact_id: contract.contact_id,
        workflow_type: "contract",
        related_contract_id: contract.id,
      });

      toast.success("Contract closed and offboarding started");
      router.push(`/offboarding/${workflow.id}`);
    } catch (err: any) {
      toast.error(err.message || "Failed to close and offboard");
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
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

  if (!contract) {
    return (
      <Shell>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Contract not found</div>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/contracts">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold">{contract.title}</h1>
                <Badge className={STATUS_COLORS[contract.status]}>
                  {contract.status}
                </Badge>
              </div>
              <p className="text-gray-500">{contract.contract_number}</p>
            </div>
          </div>

          <div className="flex gap-2">
            {contract.status === "draft" && (
              <Button onClick={handleSend} disabled={actionLoading}>
                <Send className="h-4 w-4 mr-2" />
                Send for Signature
              </Button>
            )}
            {["sent", "viewed"].includes(contract.status) && (
              <>
                <Button variant="outline" onClick={handleResend} disabled={actionLoading}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Resend
                </Button>
                <Button variant="outline" onClick={copySigningLink}>
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Copy Link
                </Button>
              </>
            )}
            <Button variant="outline" onClick={handleDuplicate} disabled={actionLoading}>
              <Copy className="h-4 w-4 mr-2" />
              Duplicate
            </Button>
            {contract.status === "signed" && (
              <Button
                variant="outline"
                className="text-orange-600 hover:text-orange-700 hover:bg-orange-50"
                onClick={handleCloseAndOffboard}
                disabled={actionLoading}
              >
                <UserMinus className="h-4 w-4 mr-2" />
                Close & Offboard
              </Button>
            )}
            {!["signed", "void"].includes(contract.status) && (
              <Button variant="outline" onClick={handleVoid} disabled={actionLoading}>
                <XCircle className="h-4 w-4 mr-2" />
                Void
              </Button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Contract Preview */}
            <Card>
              <CardHeader>
                <CardTitle>Contract Content</CardTitle>
              </CardHeader>
              <CardContent>
                <div
                  className="prose max-w-none border rounded-lg p-6 bg-white"
                  dangerouslySetInnerHTML={{ __html: contract.content }}
                />
              </CardContent>
            </Card>

            {/* Signature Info (if signed) */}
            {contract.status === "signed" && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-green-700">
                    <CheckCircle className="h-5 w-5" />
                    Signature Details
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Signed by</p>
                      <p className="font-medium">{contract.signer_name}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Email</p>
                      <p className="font-medium">{contract.signer_email}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Signature Type</p>
                      <p className="font-medium capitalize">{contract.signature_type}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Signed At</p>
                      <p className="font-medium">
                        {contract.signed_at && formatDate(contract.signed_at)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Decline Info */}
            {contract.status === "declined" && (
              <Card className="border-red-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-red-700">
                    <XCircle className="h-5 w-5" />
                    Contract Declined
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    {contract.decline_reason || "No reason provided"}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Declined on{" "}
                    {contract.declined_at && formatDate(contract.declined_at)}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Contract Info */}
            <Card>
              <CardHeader>
                <CardTitle>Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500">Client</p>
                  <p className="font-medium">{contract.contact_name || "Unknown"}</p>
                  {contract.contact_email && (
                    <p className="text-sm text-gray-500">{contract.contact_email}</p>
                  )}
                </div>
                {contract.organization_name && (
                  <div>
                    <p className="text-sm text-gray-500">Organization</p>
                    <p className="font-medium">{contract.organization_name}</p>
                  </div>
                )}
                {contract.template_name && (
                  <div>
                    <p className="text-sm text-gray-500">Template</p>
                    <p className="font-medium">{contract.template_name}</p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-gray-500">Created</p>
                  <p className="font-medium">{formatDate(contract.created_at)}</p>
                </div>
                {contract.sent_at && (
                  <div>
                    <p className="text-sm text-gray-500">Sent</p>
                    <p className="font-medium">{formatDate(contract.sent_at)}</p>
                  </div>
                )}
                {contract.expires_at && ["sent", "viewed"].includes(contract.status) && (
                  <div>
                    <p className="text-sm text-gray-500">Expires</p>
                    <p className="font-medium">{formatDate(contract.expires_at)}</p>
                  </div>
                )}
                {contract.notes && (
                  <div>
                    <p className="text-sm text-gray-500">Notes</p>
                    <p className="text-sm">{contract.notes}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Signing Link (for sent/viewed) */}
            {["sent", "viewed"].includes(contract.status) && (
              <Card>
                <CardHeader>
                  <CardTitle>Signing Link</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <p className="text-sm text-gray-500">
                    Share this link with your client to sign the contract
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={copySigningLink}
                    >
                      <Copy className="h-4 w-4 mr-2" />
                      Copy Link
                    </Button>
                    <a href={getSigningLink()} target="_blank" rel="noopener noreferrer">
                      <Button variant="outline" size="sm">
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </a>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Audit Log */}
            <Card>
              <CardHeader>
                <CardTitle>Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {contract.audit_logs.length === 0 ? (
                    <p className="text-sm text-gray-500">No activity yet</p>
                  ) : (
                    contract.audit_logs.map((log) => (
                      <div key={log.id} className="flex items-start gap-3 text-sm">
                        <div className="mt-1">
                          {log.action === "signed" ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : log.action === "viewed" ? (
                            <Eye className="h-4 w-4 text-purple-500" />
                          ) : log.action === "sent" || log.action === "resent" ? (
                            <Send className="h-4 w-4 text-blue-500" />
                          ) : (
                            <Clock className="h-4 w-4 text-gray-400" />
                          )}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium">
                            {ACTION_LABELS[log.action] || log.action}
                          </p>
                          <p className="text-gray-500">
                            {formatDate(log.created_at)}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Shell>
  );
}
