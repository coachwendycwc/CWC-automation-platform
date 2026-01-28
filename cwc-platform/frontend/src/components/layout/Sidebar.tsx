"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import {
  LayoutDashboard,
  Users,
  Building2,
  Calendar,
  CalendarDays,
  FileText,
  FileSignature,
  FolderKanban,
  FolderOpen,
  MessageSquare,
  Settings,
  LogOut,
  Brain,
  Receipt,
  UserMinus,
  ListTodo,
  Target,
  Video,
  ClipboardList,
  Clock,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Briefcase,
  DollarSign,
  Sparkles,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface NavItem {
  name: string;
  href: string;
  icon: any;
  disabled?: boolean;
}

interface NavGroup {
  name: string;
  icon: any;
  items: NavItem[];
}

// Top level items (always visible)
const topNavigation: NavItem[] = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Calendar", href: "/calendar", icon: CalendarDays },
];

// Grouped navigation
const navGroups: NavGroup[] = [
  {
    name: "Clients",
    icon: Users,
    items: [
      { name: "Contacts", href: "/contacts", icon: Users },
      { name: "Organizations", href: "/organizations", icon: Building2 },
      { name: "Notes", href: "/notes", icon: MessageSquare },
      { name: "Action Items", href: "/action-items", icon: ListTodo },
      { name: "Goals", href: "/goals", icon: Target },
      { name: "Assessments", href: "/assessments", icon: ClipboardList },
    ],
  },
  {
    name: "Business",
    icon: Briefcase,
    items: [
      { name: "Bookings", href: "/bookings", icon: Calendar },
      { name: "Projects", href: "/projects", icon: FolderKanban },
      { name: "Invoices", href: "/invoices", icon: FileText },
      { name: "Contracts", href: "/contracts", icon: FileSignature },
    ],
  },
  {
    name: "Finance",
    icon: DollarSign,
    items: [
      { name: "Bookkeeping", href: "/bookkeeping", icon: Receipt },
    ],
  },
  {
    name: "Growth",
    icon: Sparkles,
    items: [
      { name: "Content", href: "/content", icon: FolderOpen },
      { name: "Testimonials", href: "/testimonials", icon: Video },
      { name: "ICF Tracker", href: "/icf-tracker", icon: Clock },
    ],
  },
  {
    name: "Admin",
    icon: Settings,
    items: [
      { name: "Offboarding", href: "/offboarding", icon: UserMinus },
      { name: "AI Extractions", href: "/extractions", icon: Brain },
    ],
  },
];

const bottomNavigation: NavItem[] = [
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<string[]>([]);

  // Load states from localStorage
  useEffect(() => {
    const storedCollapsed = localStorage.getItem("sidebar-collapsed");
    if (storedCollapsed) {
      setCollapsed(storedCollapsed === "true");
    }

    const storedGroups = localStorage.getItem("sidebar-expanded-groups");
    if (storedGroups) {
      setExpandedGroups(JSON.parse(storedGroups));
    } else {
      // Default: expand the group that contains the current page
      const activeGroup = navGroups.find(g =>
        g.items.some(item => pathname.startsWith(item.href))
      );
      if (activeGroup) {
        setExpandedGroups([activeGroup.name]);
      }
    }
  }, []);

  // Auto-expand group when navigating to a page in that group (accordion style)
  useEffect(() => {
    const activeGroup = navGroups.find(g =>
      g.items.some(item => pathname.startsWith(item.href))
    );
    if (activeGroup && !expandedGroups.includes(activeGroup.name)) {
      // Accordion: only this group open
      setExpandedGroups([activeGroup.name]);
      localStorage.setItem("sidebar-expanded-groups", JSON.stringify([activeGroup.name]));
    }
  }, [pathname]);

  const toggleCollapsed = () => {
    const newState = !collapsed;
    setCollapsed(newState);
    localStorage.setItem("sidebar-collapsed", String(newState));
  };

  const toggleGroup = (groupName: string) => {
    // Accordion behavior: close others when opening one
    const newGroups = expandedGroups.includes(groupName)
      ? [] // Close if already open
      : [groupName]; // Open only this one
    setExpandedGroups(newGroups);
    localStorage.setItem("sidebar-expanded-groups", JSON.stringify(newGroups));
  };

  const renderNavItem = (item: NavItem, isNested = false) => {
    const isActive = pathname.startsWith(item.href);
    const linkContent = (
      <Link
        href={item.disabled ? "#" : item.href}
        className={cn(
          "group flex items-center rounded-md py-1.5 text-sm font-medium transition-colors",
          collapsed ? "justify-center px-2" : isNested ? "px-3 pl-9" : "px-3",
          isActive
            ? "bg-gray-800 text-white"
            : "text-gray-300 hover:bg-gray-800 hover:text-white",
          item.disabled && "cursor-not-allowed opacity-50"
        )}
        onClick={(e) => item.disabled && e.preventDefault()}
      >
        <item.icon
          className={cn(
            "h-4 w-4 flex-shrink-0",
            !collapsed && "mr-2",
            isActive ? "text-white" : "text-gray-400 group-hover:text-white"
          )}
        />
        {!collapsed && (
          <>
            <span className="truncate">{item.name}</span>
            {item.disabled && (
              <span className="ml-auto text-xs text-gray-500">Soon</span>
            )}
          </>
        )}
      </Link>
    );

    if (collapsed) {
      return (
        <Tooltip key={item.name}>
          <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
          <TooltipContent side="right" className="bg-gray-800 text-white border-gray-700">
            {item.name}
          </TooltipContent>
        </Tooltip>
      );
    }

    return <div key={item.name}>{linkContent}</div>;
  };

  const renderNavGroup = (group: NavGroup) => {
    const isExpanded = expandedGroups.includes(group.name);
    const hasActiveItem = group.items.some(item => pathname.startsWith(item.href));

    if (collapsed) {
      // In collapsed mode, show all items with tooltips
      return (
        <div key={group.name} className="space-y-0.5">
          {group.items.map(item => renderNavItem(item))}
        </div>
      );
    }

    return (
      <div key={group.name} className="space-y-0.5">
        <button
          onClick={() => toggleGroup(group.name)}
          className={cn(
            "group flex w-full items-center rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
            hasActiveItem
              ? "text-white"
              : "text-gray-400 hover:bg-gray-800 hover:text-white"
          )}
        >
          <group.icon className="h-4 w-4 mr-2 flex-shrink-0" />
          <span className="flex-1 text-left">{group.name}</span>
          <ChevronDown
            className={cn(
              "h-4 w-4 transition-transform",
              isExpanded && "rotate-180"
            )}
          />
        </button>
        {isExpanded && (
          <div className="space-y-0.5">
            {group.items.map(item => renderNavItem(item, true))}
          </div>
        )}
      </div>
    );
  };

  return (
    <TooltipProvider delayDuration={0}>
      <div
        className={cn(
          "flex h-full flex-col bg-gray-900 transition-all duration-300",
          collapsed ? "w-16" : "w-56"
        )}
      >
        {/* Logo */}
        <div className="flex h-14 items-center justify-center px-3 py-2">
          <Link href="/dashboard">
            {collapsed ? (
              <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                C
              </div>
            ) : (
              <Image
                src="/images/logo-small.png"
                alt="Coaching Women of Color"
                width={140}
                height={120}
                className="h-12 w-auto"
                priority
              />
            )}
          </Link>
        </div>

        {/* Toggle Button */}
        <div className="px-2 mb-1">
          <button
            onClick={toggleCollapsed}
            className={cn(
              "flex items-center justify-center w-full rounded-md py-1.5 text-gray-400 hover:bg-gray-800 hover:text-white transition-colors",
              collapsed ? "px-0" : "px-2"
            )}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4 mr-1" />
                <span className="text-xs">Collapse</span>
              </>
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-2 py-1 overflow-y-auto">
          {/* Top items */}
          <div className="space-y-0.5">
            {topNavigation.map(item => renderNavItem(item))}
          </div>

          {/* Separator */}
          <div className="border-t border-gray-800 my-2" />

          {/* Grouped items */}
          <div className="space-y-1">
            {navGroups.map(group => renderNavGroup(group))}
          </div>
        </nav>

        {/* Bottom navigation */}
        <div className="border-t border-gray-800 px-2 py-2">
          {bottomNavigation.map(item => renderNavItem(item))}

          {/* User section */}
          {user && (
            <div className={cn(
              "mt-2 pt-2 border-t border-gray-800",
              collapsed && "flex flex-col items-center"
            )}>
              {!collapsed && (
                <div className="px-2 py-1">
                  <p className="text-xs font-medium text-white truncate">{user.name}</p>
                  <p className="text-xs text-gray-400 truncate">{user.email}</p>
                </div>
              )}
              {collapsed ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={logout}
                      className="group flex items-center justify-center rounded-md px-2 py-1.5 text-sm font-medium text-gray-300 hover:bg-gray-800 hover:text-white"
                    >
                      <LogOut className="h-4 w-4 flex-shrink-0 text-gray-400 group-hover:text-white" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right" className="bg-gray-800 text-white border-gray-700">
                    Sign Out ({user.name})
                  </TooltipContent>
                </Tooltip>
              ) : (
                <button
                  onClick={logout}
                  className="group flex w-full items-center rounded-md px-2 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-800 hover:text-white"
                >
                  <LogOut className="mr-2 h-4 w-4 flex-shrink-0 text-gray-400 group-hover:text-white" />
                  Sign Out
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}
