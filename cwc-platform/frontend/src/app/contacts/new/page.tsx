"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";
import { contactsApi, organizationsApi } from "@/lib/api";
import { ContactType, CoachingType, Organization } from "@/types";

export default function NewContactPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    organization_id: "",
    title: "",
    role: "",
    contact_type: "lead" as ContactType,
    coaching_type: "" as CoachingType | "",
    source: "",
  });

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

    // Fetch organizations for dropdown
    organizationsApi.list(token, { size: 100 }).then((res) => {
      setOrganizations(res.items);
    });
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token) return;

    setLoading(true);
    try {
      const data = {
        ...formData,
        organization_id: formData.organization_id || undefined,
        coaching_type: formData.coaching_type || undefined,
      };
      await contactsApi.create(token, data);
      router.push("/contacts");
    } catch (error) {
      console.error("Failed to create contact:", error);
      alert("Failed to create contact");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <Shell user={user}>
      <div className="max-w-2xl mx-auto space-y-6">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>

        <Card>
          <CardHeader>
            <CardTitle>New Contact</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    First Name *
                  </label>
                  <Input
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Last Name
                  </label>
                  <Input
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Email</label>
                  <Input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Phone</label>
                  <Input
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Organization
                </label>
                <select
                  name="organization_id"
                  value={formData.organization_id}
                  onChange={handleChange}
                  className="w-full rounded-md border border-input bg-background px-3 py-2"
                >
                  <option value="">No organization (B2C)</option>
                  {organizations.map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Title</label>
                  <Input
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    placeholder="e.g., VP of Engineering"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Role</label>
                  <Input
                    name="role"
                    value={formData.role}
                    onChange={handleChange}
                    placeholder="e.g., Primary Contact"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Contact Type
                  </label>
                  <select
                    name="contact_type"
                    value={formData.contact_type}
                    onChange={handleChange}
                    className="w-full rounded-md border border-input bg-background px-3 py-2"
                  >
                    <option value="lead">Lead</option>
                    <option value="client">Client</option>
                    <option value="past_client">Past Client</option>
                    <option value="partner">Partner</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Coaching Type
                  </label>
                  <select
                    name="coaching_type"
                    value={formData.coaching_type}
                    onChange={handleChange}
                    className="w-full rounded-md border border-input bg-background px-3 py-2"
                  >
                    <option value="">Not applicable</option>
                    <option value="executive">Executive Coaching</option>
                    <option value="life">Life Coaching</option>
                    <option value="group">Group Coaching</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Source</label>
                <Input
                  name="source"
                  value={formData.source}
                  onChange={handleChange}
                  placeholder="e.g., LinkedIn, Referral, Website"
                />
              </div>

              <div className="flex gap-2 pt-4">
                <Button type="submit" disabled={loading}>
                  {loading ? "Creating..." : "Create Contact"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.back()}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}
