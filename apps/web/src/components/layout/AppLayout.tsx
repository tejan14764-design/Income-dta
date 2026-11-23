import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import { Menu, Bell, Search } from "lucide-react";
import { Sidebar } from "./Sidebar";
import { useAuthStore } from "@/store/authStore";

export function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { activeSchool } = useAuthStore();

  return (
    <div className="min-h-screen bg-surface">
      <Sidebar mobileOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />

      {/* Main content */}
      <div className="lg:pl-64 flex flex-col min-h-screen">
        {/* Top header */}
        <header className="sticky top-0 z-20 bg-white border-b border-surface-border px-4 lg:px-6 h-14 flex items-center gap-4">
          <button
            className="lg:hidden p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-muted"
            onClick={() => setMobileMenuOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* School name breadcrumb */}
          <span className="hidden sm:block text-sm text-text-muted">
            {activeSchool?.school_name}
          </span>

          <div className="flex-1" />

          {/* Notification bell */}
          <button
            className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-muted relative"
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5" />
          </button>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
