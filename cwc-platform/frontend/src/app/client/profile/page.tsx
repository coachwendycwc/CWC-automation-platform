"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useClientAuth } from "@/contexts/ClientAuthContext";
import { clientPortalApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { User, Building2, Save } from "lucide-react";

interface Profile {
  id: string;
  first_name: string;
  last_name: string | null;
  email: string | null;
  phone: string | null;
  organization_name: string | null;
  is_org_admin: boolean;
}

export default function ClientProfilePage() {
  const { sessionToken } = useClientAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");

  useEffect(() => {
    const loadProfile = async () => {
      if (!sessionToken) return;

      try {
        const data = await clientPortalApi.getProfile(sessionToken);
        setProfile(data);
        setFirstName(data.first_name);
        setLastName(data.last_name || "");
        setPhone(data.phone || "");
      } catch (error) {
        console.error("Failed to load profile:", error);
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, [sessionToken]);

  const handleSave = async () => {
    if (!sessionToken) return;

    setSaving(true);
    try {
      const updated = await clientPortalApi.updateProfile(sessionToken, {
        first_name: firstName,
        last_name: lastName || undefined,
        phone: phone || undefined,
      });
      setProfile(updated);
      toast.success("Profile updated successfully");
    } catch (error: any) {
      toast.error(error.message || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading profile...</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Profile not found</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
        <p className="text-gray-500">Manage your account information</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center">
              <User className="h-8 w-8 text-purple-600" />
            </div>
            <div>
              <CardTitle>
                {profile.first_name} {profile.last_name}
              </CardTitle>
              <p className="text-gray-500">{profile.email}</p>
              {profile.is_org_admin && (
                <Badge className="mt-1 bg-purple-100 text-purple-800">
                  Organization Admin
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Organization Info */}
          {profile.organization_name && (
            <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
              <Building2 className="h-5 w-5 text-gray-500" />
              <div>
                <p className="text-sm text-gray-500">Organization</p>
                <p className="font-medium">{profile.organization_name}</p>
              </div>
            </div>
          )}

          {/* Edit Form */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="firstName">First Name</Label>
                <Input
                  id="firstName"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="lastName">Last Name</Label>
                <Input
                  id="lastName"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" value={profile.email || ""} disabled />
              <p className="text-xs text-gray-500">
                Contact support to change your email address
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 (555) 123-4567"
              />
            </div>
          </div>

          <Button onClick={handleSave} disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
