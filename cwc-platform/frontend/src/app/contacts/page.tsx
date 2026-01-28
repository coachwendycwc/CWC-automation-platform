"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Shell } from "@/components/layout/Shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Plus, Search, Mail, Phone } from "lucide-react";
import { contactsApi } from "@/lib/api";
import { Contact } from "@/types";
import { getInitials } from "@/lib/utils";
import { SkeletonList } from "@/components/ui/skeleton";

export default function ContactsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
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

    fetchContacts(token);
  }, [router]);

  const fetchContacts = async (token: string, searchTerm?: string) => {
    setLoading(true);
    try {
      const response = await contactsApi.list(token, {
        search: searchTerm,
        size: 50,
      });
      setContacts(response.items);
      setTotal(response.total);
    } catch (error) {
      console.error("Failed to fetch contacts:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (token) {
      fetchContacts(token, search);
    }
  };

  const getContactTypeBadge = (type: string) => {
    const variants: Record<string, "default" | "secondary" | "success" | "warning"> = {
      lead: "warning",
      client: "success",
      past_client: "secondary",
      partner: "default",
    };
    return <Badge variant={variants[type] || "default"}>{type}</Badge>;
  };

  return (
    <Shell user={user}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Contacts</h1>
            <p className="text-gray-500">{total} total contacts</p>
          </div>
          <Button onClick={() => router.push("/contacts/new")}>
            <Plus className="mr-2 h-4 w-4" />
            Add Contact
          </Button>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <Input
              type="search"
              placeholder="Search by name or email..."
              className="pl-10"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button type="submit" variant="outline">
            Search
          </Button>
        </form>

        {/* Contact List */}
        {loading ? (
          <SkeletonList items={6} />
        ) : contacts.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center">
              <p className="text-gray-500">No contacts found.</p>
              <Button
                className="mt-4"
                onClick={() => router.push("/contacts/new")}
              >
                Add your first contact
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {contacts.map((contact) => (
              <Link key={contact.id} href={`/contacts/${contact.id}`}>
                <Card className="cursor-pointer transition-shadow hover:shadow-md">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <Avatar>
                        <AvatarFallback>
                          {getInitials(
                            `${contact.first_name} ${contact.last_name || ""}`
                          )}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <h3 className="font-medium truncate">
                            {contact.first_name} {contact.last_name}
                          </h3>
                          {getContactTypeBadge(contact.contact_type)}
                        </div>
                        {contact.title && (
                          <p className="text-sm text-gray-500 truncate">
                            {contact.title}
                          </p>
                        )}
                        <div className="mt-2 space-y-1">
                          {contact.email && (
                            <div className="flex items-center gap-1 text-xs text-gray-500">
                              <Mail className="h-3 w-3" />
                              <span className="truncate">{contact.email}</span>
                            </div>
                          )}
                          {contact.phone && (
                            <div className="flex items-center gap-1 text-xs text-gray-500">
                              <Phone className="h-3 w-3" />
                              <span>{contact.phone}</span>
                            </div>
                          )}
                        </div>
                        {contact.coaching_type && (
                          <Badge variant="outline" className="mt-2 text-xs">
                            {contact.coaching_type} coaching
                          </Badge>
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
