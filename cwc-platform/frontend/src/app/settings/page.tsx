"use client";

import Link from "next/link";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, Clock, User, Bell } from "lucide-react";

const settingsLinks = [
  {
    name: "Booking Types",
    description: "Manage the types of sessions you offer (coaching, strategy, etc.)",
    href: "/settings/booking-types",
    icon: Calendar,
  },
  {
    name: "Availability",
    description: "Set your weekly schedule and date-specific overrides",
    href: "/settings/availability",
    icon: Clock,
  },
  {
    name: "Profile",
    description: "Update your personal information and preferences",
    href: "/settings/profile",
    icon: User,
    disabled: true,
  },
  {
    name: "Notifications",
    description: "Configure email notifications and reminders",
    href: "/settings/notifications",
    icon: Bell,
    disabled: true,
  },
];

export default function SettingsPage() {
  return (
    <Shell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600">Manage your platform settings and preferences</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {settingsLinks.map((link) => (
            <Link
              key={link.name}
              href={link.disabled ? "#" : link.href}
              className={link.disabled ? "cursor-not-allowed" : ""}
              onClick={(e) => link.disabled && e.preventDefault()}
            >
              <Card className={`h-full transition-shadow hover:shadow-md ${link.disabled ? "opacity-50" : ""}`}>
                <CardHeader className="flex flex-row items-center gap-4">
                  <div className="rounded-lg bg-blue-100 p-2">
                    <link.icon className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">
                      {link.name}
                      {link.disabled && <span className="ml-2 text-xs text-gray-400">(Coming soon)</span>}
                    </CardTitle>
                    <CardDescription>{link.description}</CardDescription>
                  </div>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </Shell>
  );
}
