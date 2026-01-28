"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Shell } from "@/components/layout/Shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Search, Building2, Users, Globe } from "lucide-react";
import { organizationsApi } from "@/lib/api";
import { Organization } from "@/types";
import { formatCurrency } from "@/lib/utils";

export default function OrganizationsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [total, setTotal] = useState(0);

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

    fetchOrganizations(token);
  }, [router]);

  const fetchOrganizations = async (token: string, searchTerm?: string) => {
    setLoading(true);
    try {
      const response = await organizationsApi.list(token, {
        search: searchTerm,
        size: 50,
      });
      setOrganizations(response.items);
      setTotal(response.total);
    } catch (error) {
      console.error("Failed to fetch organizations:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (token) {
      fetchOrganizations(token, search);
    }
  };

  return (
    <Shell user={user}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Organizations</h1>
            <p className="text-gray-500">{total} total organizations</p>
          </div>
          <Button onClick={() => router.push("/organizations/new")}>
            <Plus className="mr-2 h-4 w-4" />
            Add Organization
          </Button>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <Input
              type="search"
              placeholder="Search organizations..."
              className="pl-10"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button type="submit" variant="outline">
            Search
          </Button>
        </form>

        {/* Organization List */}
        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : organizations.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center">
              <p className="text-gray-500">No organizations found.</p>
              <Button
                className="mt-4"
                onClick={() => router.push("/organizations/new")}
              >
                Add your first organization
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {organizations.map((org) => (
              <Link key={org.id} href={`/organizations/${org.id}`}>
                <Card className="cursor-pointer transition-shadow hover:shadow-md h-full">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="rounded-lg bg-blue-100 p-3">
                        <Building2 className="h-5 w-5 text-blue-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <h3 className="font-medium truncate">{org.name}</h3>
                          <Badge
                            variant={
                              org.status === "active" ? "success" : "secondary"
                            }
                          >
                            {org.status}
                          </Badge>
                        </div>
                        {org.industry && (
                          <p className="text-sm text-gray-500">{org.industry}</p>
                        )}
                        <div className="mt-3 space-y-1">
                          {org.size && (
                            <div className="flex items-center gap-1 text-xs text-gray-500">
                              <Users className="h-3 w-3" />
                              <span>{org.size} employees</span>
                            </div>
                          )}
                          {org.website && (
                            <div className="flex items-center gap-1 text-xs text-gray-500">
                              <Globe className="h-3 w-3" />
                              <span className="truncate">{org.website}</span>
                            </div>
                          )}
                        </div>
                        {org.lifetime_value > 0 && (
                          <div className="mt-2">
                            <span className="text-sm font-medium text-green-600">
                              {formatCurrency(Number(org.lifetime_value))}
                            </span>
                            <span className="text-xs text-gray-400 ml-1">
                              lifetime value
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </Shell>
  );
}
