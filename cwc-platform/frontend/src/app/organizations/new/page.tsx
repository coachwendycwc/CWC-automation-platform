"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";
import { organizationsApi } from "@/lib/api";

export default function NewOrganizationPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    industry: "",
    size: "",
    website: "",
    segment: "",
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
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token) return;

    setLoading(true);
    try {
      await organizationsApi.create(token, formData);
      router.push("/organizations");
    } catch (error) {
      console.error("Failed to create organization:", error);
      alert("Failed to create organization");
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
        <Button variant="ghost" onClick={() => router.back()} className="mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>

        <Card>
          <CardHeader>
            <CardTitle>New Organization</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Organization Name *
                </label>
                <Input
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  placeholder="e.g., Acme Corporation"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Industry
                  </label>
                  <Input
                    name="industry"
                    value={formData.industry}
                    onChange={handleChange}
                    placeholder="e.g., Technology"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Company Size
                  </label>
                  <select
                    name="size"
                    value={formData.size}
                    onChange={handleChange}
                    className="w-full rounded-md border border-input bg-background px-3 py-2"
                  >
                    <option value="">Select size</option>
                    <option value="1-10">1-10 employees</option>
                    <option value="11-50">11-50 employees</option>
                    <option value="51-200">51-200 employees</option>
                    <option value="201-500">201-500 employees</option>
                    <option value="501-1000">501-1000 employees</option>
                    <option value="1001-5000">1001-5000 employees</option>
                    <option value="5000+">5000+ employees</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Website</label>
                <Input
                  name="website"
                  value={formData.website}
                  onChange={handleChange}
                  placeholder="https://example.com"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Segment
                  </label>
                  <select
                    name="segment"
                    value={formData.segment}
                    onChange={handleChange}
                    className="w-full rounded-md border border-input bg-background px-3 py-2"
                  >
                    <option value="">Select segment</option>
                    <option value="enterprise">Enterprise</option>
                    <option value="mid-market">Mid-Market</option>
                    <option value="small-business">Small Business</option>
                    <option value="nonprofit">Nonprofit</option>
                    <option value="education">Education</option>
                    <option value="government">Government</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Source</label>
                  <Input
                    name="source"
                    value={formData.source}
                    onChange={handleChange}
                    placeholder="e.g., LinkedIn, Referral"
                  />
                </div>
              </div>

              <div className="flex gap-2 pt-4">
                <Button type="submit" disabled={loading}>
                  {loading ? "Creating..." : "Create Organization"}
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
