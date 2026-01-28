"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, ArrowLeft, CheckCircle, Clock, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Contract {
  id: string;
  contract_number: string;
  title: string;
  status: string;
  created_at: string;
  signed_at: string | null;
  contact_name?: string;
}

export default function OrganizationContractsPage() {
  const { sessionToken, isOrgAdmin } = useClientAuth();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (!isOrgAdmin) {
      router.replace("/client/dashboard");
      return;
    }

    const loadData = async () => {
      if (!sessionToken) return;

      try {
        const data = await clientPortalApi.getContracts(sessionToken);
        setContracts(data);
      } catch (error) {
        console.error("Failed to load contracts:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [sessionToken, isOrgAdmin, router]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const getStatusInfo = (status: string) => {
    switch (status) {
      case "signed":
        return {
          color: "bg-green-100 text-green-800",
          icon: CheckCircle,
          iconColor: "text-green-600",
        };
      case "sent":
      case "viewed":
        return {
          color: "bg-yellow-100 text-yellow-800",
          icon: Clock,
          iconColor: "text-yellow-600",
        };
      case "expired":
        return {
          color: "bg-red-100 text-red-800",
          icon: AlertCircle,
          iconColor: "text-red-600",
        };
      default:
        return {
          color: "bg-gray-100 text-gray-800",
          icon: FileText,
          iconColor: "text-gray-600",
        };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  // Count by status
  const signedCount = contracts.filter((c) => c.status === "signed").length;
  const pendingCount = contracts.filter((c) => ["sent", "viewed"].includes(c.status)).length;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/client/organization">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
        </Link>
      </div>

      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Organization Contracts</h1>
        <p className="text-gray-500 mt-1">
          Coaching agreements and service contracts
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-xl">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Contracts</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {contracts.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-xl">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Signed</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {signedCount}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-yellow-100 rounded-xl">
                <Clock className="h-6 w-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Pending Signature</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {pendingCount}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Contract List */}
      {contracts.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No contracts</h3>
            <p className="text-gray-500">
              No contracts have been created for your organization yet
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {contracts.map((contract) => {
            const statusInfo = getStatusInfo(contract.status);
            const StatusIcon = statusInfo.icon;

            return (
              <Link key={contract.id} href={`/client/contracts/${contract.id}`}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="py-5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-lg bg-gray-100`}>
                          <StatusIcon className={`h-5 w-5 ${statusInfo.iconColor}`} />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">
                            {contract.title}
                          </p>
                          <p className="text-sm text-gray-500">
                            {contract.contract_number} • Created {formatDate(contract.created_at)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        {contract.signed_at && (
                          <p className="text-sm text-gray-500">
                            Signed {formatDate(contract.signed_at)}
                          </p>
                        )}
                        <Badge className={statusInfo.color}>
                          {contract.status}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
