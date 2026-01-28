"use client";

import { Bell, Search } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getInitials } from "@/lib/utils";

interface HeaderProps {
  user?: {
    name: string;
    email: string;
    avatar_url?: string;
  };
}

export function Header({ user }: HeaderProps) {
  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      {/* Search */}
      <div className="flex flex-1 items-center">
        <div className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <Input
            type="search"
            placeholder="Search contacts, organizations..."
            className="pl-10"
          />
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
        </Button>

        <div className="flex items-center gap-3">
          <Avatar>
            {user?.avatar_url ? (
              <AvatarImage src={user.avatar_url} alt={user.name} />
            ) : null}
            <AvatarFallback>
              {user?.name ? getInitials(user.name) : "U"}
            </AvatarFallback>
          </Avatar>
          <div className="hidden md:block">
            <p className="text-sm font-medium">{user?.name || "User"}</p>
            <p className="text-xs text-gray-500">{user?.email || ""}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
