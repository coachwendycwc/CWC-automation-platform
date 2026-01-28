"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { ArrowLeft, ExternalLink, CheckCircle, Clock, Download } from "lucide-react";

interface Contract {
  id: string;
  contract_number: string;
  title: string;
  content: string;
  status: string;
  created_at: string;
  signed_at: string | null;
  expires_at: string | null;
  view_token: string;
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

export default function ClientContractDetailPage() {
  const params = useParams();
  const { sessionToken } = useClientAuth();
  const contractId = params.id as string;

  const [contract, setContract] = useState<Contract | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const loadContract = async () => {
      if (!sessionToken || !contractId) return;

      try {
        const data = await clientPortalApi.getContract(sessionToken, contractId);
        setContract(data);
      } catch (error) {
        console.error("Failed to load contract:", error);
      } finally {
        setLoading(false);
      }
    };

    loadContract();
  }, [sessionToken, contractId]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  const handleSign = () => {
    if (contract?.view_token) {
      window.open(`/sign/${contract.view_token}`, "_blank");
    }
  };

  const handleDownloadPdf = async () => {
    if (!sessionToken || !contract) return;

    setDownloading(true);
    try {
      const blob = await clientPortalApi.downloadContractPdf(sessionToken, contract.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${contract.contract_number}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Failed to download PDF:", error);
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading contract...</div>
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Contract not found</div>
      </div>
    );
  }

  const needsSignature = ["sent", "viewed"].includes(contract.status);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/client/contracts">
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

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleDownloadPdf} disabled={downloading}>
            <Download className="h-4 w-4 mr-2" />
            {downloading ? "Downloading..." : "Download PDF"}
          </Button>
          {needsSignature && (
            <Button onClick={handleSign}>
              <ExternalLink className="h-4 w-4 mr-2" />
              Sign Contract
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Contract Content */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Contract Content</CardTitle>
            </CardHeader>
            <CardContent>
              <div
                className="prose max-w-none"
                dangerouslySetInnerHTML={{ __html: contract.content }}
              />
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                {contract.status === "signed" ? (
                  <div className="p-2 bg-green-100 rounded-full">
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  </div>
                ) : (
                  <div className="p-2 bg-purple-100 rounded-full">
                    <Clock className="h-6 w-6 text-purple-600" />
                  </div>
                )}
                <div>
                  <p className="font-medium capitalize">{contract.status}</p>
                  {contract.signed_at && (
                    <p className="text-sm text-gray-500">
                      Signed on {formatDate(contract.signed_at)}
                    </p>
                  )}
                </div>
              </div>

              <div className="border-t pt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Created</span>
                  <span>{formatDate(contract.created_at)}</span>
                </div>
                {contract.expires_at && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Expires</span>
                    <span>{formatDate(contract.expires_at)}</span>
                  </div>
                )}
              </div>

              {needsSignature && (
                <Button className="w-full" onClick={handleSign}>
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Sign Contract
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
