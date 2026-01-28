"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { contractsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  FileText,
  Plus,
  CheckCircle,
  Clock,
  Send,
  Copy,
  Eye,
  XCircle,
  AlertTriangle,
  FileSignature,
} from "lucide-react";
import Link from "next/link";

interface Contract {
  id: string;
  contract_number: string;
  title: string;
  contact_id: string;
  contact_name: string | null;
  organization_name: string | null;
  status: string;
  sent_at: string | null;
  signed_at: string | null;
  expires_at: string | null;
  created_at: string;
}

interface ContractStats {
  total_contracts: number;
  draft_count: number;
  sent_count: number;
  signed_count: number;
  pending_signature_count: number;
  declined_count: number;
  expired_count: number;
  signed_this_month: number;
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

const STATUS_ICONS: Record<string, React.ReactNode> = {
  draft: <FileText className="h-4 w-4" />,
  sent: <Send className="h-4 w-4" />,
  viewed: <Eye className="h-4 w-4" />,
  signed: <CheckCircle className="h-4 w-4" />,
  expired: <AlertTriangle className="h-4 w-4" />,
  declined: <XCircle className="h-4 w-4" />,
  void: <XCircle className="h-4 w-4" />,
};

export default function ContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [stats, setStats] = useState<ContractStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("");
  const [search, setSearch] = useState<string>("");

  useEffect(() => {
    loadData();
  }, [filter, search]);

  const loadData = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const [contractsData, statsData] = await Promise.all([
        contractsApi.list(token, {
          status: filter || undefined,
          search: search || undefined,
        }),
        contractsApi.getStats(token),
      ]);

      setContracts(contractsData);
      setStats(statsData);
    } catch (err) {
      console.error("Failed to load contracts:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (id: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await contractsApi.send(token, id);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to send contract");
    }
  };

  const handleDuplicate = async (id: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await contractsApi.duplicate(token, id);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to duplicate contract");
    }
  };

  const formatExpiryDate = (expiresAt: string | null, status: string) => {
    if (!expiresAt || !["sent", "viewed"].includes(status)) return null;

    const date = new Date(expiresAt);
    const now = new Date();
    const diffHours = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60));

    if (diffHours < 0) {
      return "Expired";
    } else if (diffHours < 24) {
      return `Expires in ${diffHours}h`;
    } else {
      const diffDays = Math.ceil(diffHours / 24);
      return `Expires in ${diffDays}d`;
    }
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
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Contracts</h1>
            <p className="text-gray-500">Manage contracts and e-signatures</p>
          </div>
          <div className="flex gap-2">
            <Link href="/contracts/templates">
              <Button variant="outline">
                <FileText className="h-4 w-4 mr-2" />
                Templates
              </Button>
            </Link>
            <Link href="/contracts/new">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Contract
              </Button>
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Total Contracts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <FileSignature className="h-5 w-5 text-gray-400" />
                <span className="text-2xl font-bold">{stats?.total_contracts || 0}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Pending Signature
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-blue-500" />
                <span className="text-2xl font-bold text-blue-600">
                  {stats?.pending_signature_count || 0}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Signed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="text-2xl font-bold text-green-600">
                  {stats?.signed_count || 0}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Signed This Month
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <FileSignature className="h-5 w-5 text-purple-500" />
                <span className="text-2xl font-bold text-purple-600">
                  {stats?.signed_this_month || 0}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex gap-4 items-center">
          <Input
            placeholder="Search contracts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-sm"
          />
          <div className="flex gap-2">
            <Button
              variant={filter === "" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("")}
            >
              All
            </Button>
            <Button
              variant={filter === "draft" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("draft")}
            >
              Draft
            </Button>
            <Button
              variant={filter === "sent" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("sent")}
            >
              Sent
            </Button>
            <Button
              variant={filter === "viewed" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("viewed")}
            >
              Viewed
            </Button>
            <Button
              variant={filter === "signed" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("signed")}
            >
              Signed
            </Button>
          </div>
        </div>

        {/* Contracts List */}
        <Card>
          <CardContent className="p-0">
            {contracts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <FileText className="h-12 w-12 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900">No contracts yet</h3>
                <p className="text-gray-500 mt-1">
                  Create your first contract to get started
                </p>
                <Link href="/contracts/new">
                  <Button className="mt-4">
                    <Plus className="h-4 w-4 mr-2" />
                    New Contract
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="divide-y">
                {contracts.map((contract) => (
                  <div
                    key={contract.id}
                    className="flex items-center justify-between p-4 hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-100">
                        {STATUS_ICONS[contract.status] || <FileText className="h-4 w-4" />}
                      </div>
                      <div>
                        <Link href={`/contracts/${contract.id}`}>
                          <h3 className="font-medium text-gray-900 hover:text-blue-600">
                            {contract.title}
                          </h3>
                        </Link>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <span>{contract.contract_number}</span>
                          <span>•</span>
                          <span>
                            {contract.contact_name || "Unknown Contact"}
                            {contract.organization_name && ` (${contract.organization_name})`}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <Badge className={STATUS_COLORS[contract.status]}>
                          {contract.status}
                        </Badge>
                        {formatExpiryDate(contract.expires_at, contract.status) && (
                          <p className="text-xs text-gray-500 mt-1">
                            {formatExpiryDate(contract.expires_at, contract.status)}
                          </p>
                        )}
                      </div>

                      <div className="flex gap-1">
                        {contract.status === "draft" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleSend(contract.id)}
                            title="Send for signature"
                          >
                            <Send className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDuplicate(contract.id)}
                          title="Duplicate"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Link href={`/contracts/${contract.id}`}>
                          <Button variant="ghost" size="sm" title="View">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}
