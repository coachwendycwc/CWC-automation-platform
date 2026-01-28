"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { Shell } from "@/components/layout/Shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  ArrowLeft,
  Building2,
  Globe,
  Users,
  Edit,
  Trash2,
  Mail,
} from "lucide-react";
import { organizationsApi, contactsApi } from "@/lib/api";
import { OrganizationWithContacts, Contact } from "@/types";
import { getInitials, formatCurrency, formatDateTime } from "@/lib/utils";

export default function OrganizationDetailPage() {
  const router = useRouter();
  const params = useParams();
  const orgId = params.id as string;

  const [user, setUser] = useState<any>(null);
  const [org, setOrg] = useState<OrganizationWithContacts | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);

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

    fetchOrganization(token);
    fetchContacts(token);
  }, [router, orgId]);

  const fetchOrganization = async (token: string) => {
    try {
      const data = await organizationsApi.get(token, orgId);
      setOrg(data);
    } catch (error) {
      console.error("Failed to fetch organization:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchContacts = async (token: string) => {
    try {
      const data = await contactsApi.list(token, { organization_id: orgId });
      setContacts(data.items);
    } catch (error) {
      console.error("Failed to fetch contacts:", error);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this organization?")) return;

    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      await organizationsApi.delete(token, orgId);
      router.push("/organizations");
    } catch (error) {
      console.error("Failed to delete organization:", error);
      alert("Failed to delete organization");
    }
  };

  if (loading) {
    return (
      <Shell user={user}>
        <div className="text-center py-8 text-gray-500">Loading...</div>
      </Shell>
    );
  }

  if (!org) {
    return (
      <Shell user={user}>
        <div className="text-center py-8">
          <p className="text-gray-500">Organization not found</p>
          <Button
            className="mt-4"
            onClick={() => router.push("/organizations")}
          >
            Back to Organizations
          </Button>
        </div>
      </Shell>
    );
  }

  return (
    <Shell user={user}>
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Info */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="rounded-lg bg-blue-100 p-4">
                      <Building2 className="h-8 w-8 text-blue-600" />
                    </div>
                    <div>
                      <h1 className="text-2xl font-bold">{org.name}</h1>
                      {org.industry && (
                        <p className="text-gray-500">{org.industry}</p>
                      )}
                      <div className="flex gap-2 mt-2">
                        <Badge
                          variant={
                            org.status === "active" ? "success" : "secondary"
                          }
                        >
                          {org.status}
                        </Badge>
                        {org.segment && (
                          <Badge variant="outline">{org.segment}</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled>
                      <Edit className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleDelete}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  {org.website && (
                    <div className="flex items-center gap-2">
                      <Globe className="h-4 w-4 text-gray-400" />
                      <a
                        href={org.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        {org.website}
                      </a>
                    </div>
                  )}
                  {org.size && (
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-gray-400" />
                      <span>{org.size} employees</span>
                    </div>
                  )}
                </div>

                {Number(org.lifetime_value) > 0 && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg">
                    <span className="text-sm text-gray-600">
                      Lifetime Value:
                    </span>
                    <span className="ml-2 text-xl font-bold text-green-600">
                      {formatCurrency(Number(org.lifetime_value))}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Contacts */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Contacts ({contacts.length})</CardTitle>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => router.push("/contacts/new")}
                >
                  Add Contact
                </Button>
              </CardHeader>
              <CardContent>
                {contacts.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">
                    No contacts yet.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {contacts.map((contact) => (
                      <Link
                        key={contact.id}
                        href={`/contacts/${contact.id}`}
                        className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50"
                      >
                        <Avatar className="h-10 w-10">
                          <AvatarFallback>
                            {getInitials(
                              `${contact.first_name} ${contact.last_name || ""}`
                            )}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <p className="font-medium">
                            {contact.first_name} {contact.last_name}
                          </p>
                          {contact.title && (
                            <p className="text-sm text-gray-500">
                              {contact.title}
                            </p>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={
                              contact.contact_type === "client"
                                ? "success"
                                : "secondary"
                            }
                          >
                            {contact.contact_type}
                          </Badge>
                          {contact.email && (
                            <Mail className="h-4 w-4 text-gray-400" />
                          )}
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <span className="text-gray-500">Source:</span>
                  <span className="ml-2">{org.source || "Not set"}</span>
                </div>
                <div>
                  <span className="text-gray-500">Created:</span>
                  <span className="ml-2">{formatDateTime(org.created_at)}</span>
                </div>
                {org.tags && org.tags.length > 0 && (
                  <div>
                    <span className="text-gray-500">Tags:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {org.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Shell>
  );
}
