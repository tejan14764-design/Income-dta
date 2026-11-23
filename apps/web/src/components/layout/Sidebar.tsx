import React, { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { clsx } from "clsx";
import {
  LayoutDashboard, Users, GraduationCap, CalendarDays, DollarSign,
  CreditCard, CheckSquare, FileText, BarChart3, Download, Shield,
  ClipboardList, Settings, ChevronDown, ChevronRight, LogOut,
  Menu, X
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";

interface NavItem {
  label: string;
  to?: string;
  icon: React.ReactNode;
  children?: NavItem[];
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", to: "/dashboard", icon: <LayoutDashboard className="h-4 w-4" /> },
  { label: "Students", to: "/students", icon: <Users className="h-4 w-4" /> },
  { label: "Classes", to: "/classes", icon: <GraduationCap className="h-4 w-4" /> },
  { label: "Academic Years", to: "/academic-years", icon: <CalendarDays className="h-4 w-4" /> },
  {
    label: "Fee Management",
    icon: <DollarSign className="h-4 w-4" />,
    children: [
      { label: "Fee Categories", to: "/fees/categories", icon: <></> },
      { label: "Fee Templates", to: "/fees/templates", icon: <></> },
      { label: "Student Charges", to: "/fees/student-charges", icon: <></> },
    ],
  },
  { label: "Payments", to: "/payments", icon: <CreditCard className="h-4 w-4" /> },
  { label: "Verification", to: "/payment-verification", icon: <CheckSquare className="h-4 w-4" /> },
  { label: "Receipts", to: "/receipts", icon: <FileText className="h-4 w-4" /> },
  { label: "Reports", to: "/reports", icon: <BarChart3 className="h-4 w-4" /> },
  { label: "CSV Exports", to: "/exports", icon: <Download className="h-4 w-4" /> },
  { label: "Staff & Roles", to: "/staff", icon: <Shield className="h-4 w-4" /> },
  { label: "Audit Logs", to: "/audit", icon: <ClipboardList className="h-4 w-4" /> },
  { label: "Settings", to: "/settings", icon: <Settings className="h-4 w-4" /> },
];

function NavItemComponent({ item, depth = 0 }: { item: NavItem; depth?: number }) {
  const location = useLocation();
  const [open, setOpen] = useState(() =>
    item.children?.some((c) => c.to && location.pathname.startsWith(c.to)) ?? false
  );

  if (item.children) {
    const isActive = item.children.some((c) => c.to && location.pathname.startsWith(c.to));
    return (
      <div>
        <button
          onClick={() => setOpen(!open)}
          className={clsx(
            "sidebar-link w-full",
            isActive ? "text-primary" : "sidebar-link-inactive"
          )}
        >
          <span className="text-current opacity-70">{item.icon}</span>
          <span className="flex-1 text-left">{item.label}</span>
          {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        </button>
        {open && (
          <div className="ml-4 mt-0.5 border-l-2 border-surface-border pl-3 space-y-0.5">
            {item.children.map((child) => (
              <NavItemComponent key={child.to} item={child} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <NavLink
      to={item.to!}
      className={({ isActive }) =>
        clsx("sidebar-link", isActive ? "sidebar-link-active" : "sidebar-link-inactive")
      }
      end={item.to === "/dashboard"}
    >
      <span>{item.icon}</span>
      <span>{item.label}</span>
    </NavLink>
  );
}

interface SidebarProps {
  mobileOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ mobileOpen, onClose }: SidebarProps) {
  const { user, activeSchool, logout } = useAuthStore();

  const content = (
    <div className="flex flex-col h-full">
      {/* Logo / School */}
      <div className="px-4 py-5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <img
            src={`${import.meta.env.BASE_URL}pre-school.jpeg`}
            alt="Bright Future Pre-School logo"
            className="w-9 h-9 rounded-xl flex-shrink-0"
          />
          <div className="min-w-0">
            <p className="text-white font-bold text-sm leading-tight truncate">Bright Future Pre-School</p>
            <p className="text-white/60 text-xs truncate">{activeSchool?.school_name ?? "Select school"}</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5 scrollbar-thin">
        {NAV_ITEMS.map((item) => (
          <NavItemComponent key={item.label} item={item} />
        ))}
      </nav>

      {/* User footer */}
      <div className="px-3 py-4 border-t border-white/10">
        <div className="flex items-center gap-3 px-2 py-2 rounded-lg">
          <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-white text-xs font-bold">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white text-xs font-medium truncate">{user?.full_name}</p>
            <p className="text-white/60 text-xs truncate">{activeSchool?.role_name}</p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
            title="Logout"
            aria-label="Logout"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-64 bg-primary-900 h-screen fixed left-0 top-0 z-30">
        {content}
      </aside>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={onClose}
            aria-hidden="true"
          />
          <aside className="absolute left-0 top-0 bottom-0 w-64 bg-primary-900 flex flex-col">
            <div className="flex justify-end p-3">
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-white/60 hover:text-white hover:bg-white/10"
                aria-label="Close menu"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            {content}
          </aside>
        </div>
      )}
    </>
  );
}
