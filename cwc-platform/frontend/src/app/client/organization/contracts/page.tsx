"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
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
          color: "bg-success/10 text-success",
          icon: CheckCircle,
          iconColor: "text-success",
        };
      case "sent":
      case "viewed":
        return {
          color: "bg-warning/10 text-warning",
          icon: Clock,
          iconColor: "text-warning",
        };
      case "expired":
        return {
          color: "bg-destructive/10 text-destructive",
          icon: AlertCircle,
          iconColor: "text-destructive",
        };
      default:
        return {
          color: "bg-muted text-foreground",
          icon: FileText,
          iconColor: "text-muted-foreground",
        };
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-64 w-full rounded-xl" />
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
        <h1 className="text-2xl font-semibold text-foreground">Organization Contracts</h1>
        <p className="text-muted-foreground mt-1">
          Coaching agreements and service contracts
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary/10 rounded-xl">
                <FileText className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Contracts</p>
                <p className="text-2xl font-semibold text-foreground">
                  {contracts.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-success/10 rounded-xl">
                <CheckCircle className="h-6 w-6 text-success" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Signed</p>
                <p className="text-2xl font-semibold text-foreground">
                  {signedCount}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-warning/10 rounded-xl">
                <Clock className="h-6 w-6 text-warning" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Pending Signature</p>
                <p className="text-2xl font-semibold text-foreground">
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
            <FileText className="h-12 w-12 text-muted-foreground/40 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground">No contracts</h3>
            <p className="text-muted-foreground">
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
                        <div className={`p-2 rounded-lg bg-muted`}>
                          <StatusIcon className={`h-5 w-5 ${statusInfo.iconColor}`} />
                        </div>
                        <div>
                          <p className="font-medium text-foreground">
                            {contract.title}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {contract.contract_number} • Created {formatDate(contract.created_at)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        {contract.signed_at && (
                          <p className="text-sm text-muted-foreground">
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
