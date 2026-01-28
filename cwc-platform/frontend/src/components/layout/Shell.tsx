"use client";

import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

interface ShellProps {
  children: React.ReactNode;
  user?: {
    name: string;
    email: string;
    avatar_url?: string;
  };
}

export function Shell({ children, user }: ShellProps) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header user={user} />
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
