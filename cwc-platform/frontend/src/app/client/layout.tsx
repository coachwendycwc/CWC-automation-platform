"use client";

import { ClientAuthProvider, useClientAuth } from "@/contexts/ClientAuthContext";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Toaster } from "sonner";
import Image from "next/image";

// Coachee navigation - independent (pays their own invoices)
const INDEPENDENT_COACHEE_NAV_ITEMS = [
  { href: "/client/dashboard", label: "Home" },
  { href: "/client/sessions", label: "Sessions" },
  { href: "/client/action-items", label: "Tasks" },
  { href: "/client/goals", label: "Goals" },
  { href: "/client/notes", label: "Messages" },
  { href: "/client/timeline", label: "Journey" },
  { href: "/client/resources", label: "Resources" },
  { href: "/client/invoices", label: "Billing" },
];

// Coachee navigation - org-sponsored (org pays, no billing needed)
const ORG_COACHEE_NAV_ITEMS = [
  { href: "/client/dashboard", label: "Home" },
  { href: "/client/sessions", label: "Sessions" },
  { href: "/client/action-items", label: "Tasks" },
  { href: "/client/goals", label: "Goals" },
  { href: "/client/notes", label: "Messages" },
  { href: "/client/timeline", label: "Journey" },
  { href: "/client/resources", label: "Resources" },
];

// Org admin navigation (organization admin seeing org-wide data)
const ORG_ADMIN_NAV_ITEMS = [
  { href: "/client/organization", label: "Overview" },
  { href: "/client/organization/team", label: "Team" },
  { href: "/client/organization/billing", label: "Billing" },
  { href: "/client/organization/contracts", label: "Contracts" },
];

function ClientNav() {
  const { contact, logout, isAuthenticated, isOrgAdmin } = useClientAuth();
  const pathname = usePathname();

  if (!isAuthenticated) return null;

  // Determine navigation based on user type:
  // - Org admin: sees org dashboard, team, billing, contracts
  // - Org coachee (has org but not admin): sees home, sessions only (org pays)
  // - Independent coachee (no org): sees home, sessions, billing
  const isOrgCoachee = !isOrgAdmin && !!contact?.organization_id;

  let navItems;
  if (isOrgAdmin) {
    navItems = ORG_ADMIN_NAV_ITEMS;
  } else if (isOrgCoachee) {
    navItems = ORG_COACHEE_NAV_ITEMS;
  } else {
    navItems = INDEPENDENT_COACHEE_NAV_ITEMS;
  }

  const homeLink = isOrgAdmin ? "/client/organization" : "/client/dashboard";

  // Show org logo for org-sponsored coachees
  const showOrgBranding = isOrgCoachee && contact?.organization_logo_url;

  return (
    <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-6">
        <div className="flex justify-between items-center h-20">
          {/* Logo - show org logo for org coachees, CWC logo for others */}
          <div className="flex items-center gap-4">
            <Link href={homeLink}>
              <Image
                src="/images/logo.png"
                alt="CWC"
                width={240}
                height={80}
                className="h-16 w-auto"
              />
            </Link>
            {showOrgBranding && (
              <>
                <div className="h-8 w-px bg-gray-200" />
                <img
                  src={contact.organization_logo_url!}
                  alt={contact.organization_name || "Organization"}
                  className="h-10 w-auto object-contain"
                />
              </>
            )}
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-4 py-1.5 text-sm font-medium transition-all rounded-full ${
                    isActive
                      ? "bg-gray-900 text-white"
                      : "text-gray-500 hover:text-gray-900"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* User Section */}
          <div className="flex items-center gap-3">
            <Link
              href="/client/profile"
              className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
            >
              {contact?.first_name}
            </Link>
            <Button
              variant="ghost"
              size="sm"
              onClick={logout}
              className="text-gray-400 hover:text-gray-600 p-2"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}

function ClientLayoutContent({ children }: { children: React.ReactNode }) {
  const { isLoading, isAuthenticated } = useClientAuth();
  const pathname = usePathname();

  // Public paths that don't need auth
  const isPublicPath =
    pathname === "/client/login" ||
    pathname?.startsWith("/client/verify");

  // For public paths, render immediately without waiting for auth
  if (isPublicPath) {
    return <>{children}</>;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50/50 flex items-center justify-center">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  // For authenticated routes, show the nav
  return (
    <div className="min-h-screen bg-gray-50/50">
      <ClientNav />
      <main className="max-w-5xl mx-auto px-6 py-10">
        {children}
      </main>
    </div>
  );
}

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClientAuthProvider>
      <ClientLayoutContent>{children}</ClientLayoutContent>
      <Toaster position="bottom-right" richColors />
    </ClientAuthProvider>
  );
}
