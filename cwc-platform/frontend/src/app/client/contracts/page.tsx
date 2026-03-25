"use client";

import { useEffect, useState } from "react";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { FileSignature, ExternalLink, CheckCircle, Clock, User } from "lucide-react";

interface Contract {
  id: string;
  contract_number: string;
  title: string;
  status: string;
  created_at: string;
  signed_at: string | null;
  contact_name: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-muted text-foreground",
  sent: "bg-primary/10 text-primary",
  viewed: "bg-accent/10 text-accent",
  signed: "bg-success/10 text-success",
  expired: "bg-orange-100 text-warning",
  declined: "bg-destructive/10 text-destructive",
  void: "bg-muted text-muted-foreground",
};

export default function ClientContractsPage() {
  const { sessionToken } = useClientAuth();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadContracts = async () => {
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

    loadContracts();
  }, [sessionToken]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Contracts</h1>
        <p className="text-muted-foreground">View and sign your contracts</p>
      </div>

      {contracts.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileSignature className="h-12 w-12 text-muted-foreground/40 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground">No contracts</h3>
            <p className="text-muted-foreground">You don&apos;t have any contracts yet</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {contracts.map((contract) => (
            <Card key={contract.id} className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${
                      contract.status === "signed"
                        ? "bg-success/10"
                        : "bg-accent/10"
                    }`}>
                      {contract.status === "signed" ? (
                        <CheckCircle className="h-5 w-5 text-success" />
                      ) : (
                        <Clock className="h-5 w-5 text-accent" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium">{contract.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {contract.contract_number} &middot; Created{" "}
                        {formatDate(contract.created_at)}
                        {contract.contact_name && (
                          <>
                            {" "}&middot;{" "}
                            <span className="inline-flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {contract.contact_name}
                            </span>
                          </>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    {contract.signed_at && (
                      <p className="text-sm text-muted-foreground">
                        Signed {formatDate(contract.signed_at)}
                      </p>
                    )}
                    <Badge className={STATUS_COLORS[contract.status]}>
                      {contract.status}
                    </Badge>
                    <Link href={`/client/contracts/${contract.id}`}>
                      <Button variant="outline" size="sm">
                        View
                        <ExternalLink className="ml-2 h-4 w-4" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
