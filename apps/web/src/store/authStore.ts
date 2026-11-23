/**
 * INCOME – Authentication store using Zustand.
 * Persists tokens and user to localStorage.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, SchoolMembership } from "@/types";

interface AuthStore {
  user: User | null;
  memberships: SchoolMembership[];
  access: string | null;
  refresh: string | null;
  activeSchool: SchoolMembership | null;

  // Actions
  login: (user: User, memberships: SchoolMembership[], access: string, refresh: string) => void;
  logout: () => void;
  setTokens: (access: string, refresh: string) => void;
  setActiveSchool: (school: SchoolMembership) => void;
  updateUser: (user: Partial<User>) => void;
  isAuthenticated: () => boolean;
  hasPermission: (roleSlug: string) => boolean;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      memberships: [],
      access: null,
      refresh: null,
      activeSchool: null,

      login: (user, memberships, access, refresh) => {
        const activeSchool = memberships.length > 0 ? memberships[0] : null;
        set({ user, memberships, access, refresh, activeSchool });
      },

      logout: () => {
        set({ user: null, memberships: [], access: null, refresh: null, activeSchool: null });
        // Clear any cached queries - done in component
        const isElectron = !!(window as Window & { income?: unknown }).income || navigator.userAgent.toLowerCase().includes("electron");
        if (isElectron) {
          window.location.hash = "/login";
        } else {
          window.location.href = "/login";
        }
      },

      setTokens: (access, refresh) => set({ access, refresh }),

      setActiveSchool: (school) => set({ activeSchool: school }),

      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),

      isAuthenticated: () => {
        const { access, user } = get();
        return !!(access && user);
      },

      hasPermission: (roleSlug) => {
        const { user, activeSchool } = get();
        if (!user) return false;
        if (user.is_active === false) return false;
        return activeSchool?.role_slug === roleSlug || 
               activeSchool?.role_slug === "super_admin" ||
               activeSchool?.role_slug === "school_admin";
      },
    }),
    {
      name: "income-auth",
      partialize: (state) => ({
        user: state.user,
        memberships: state.memberships,
        access: state.access,
        refresh: state.refresh,
        activeSchool: state.activeSchool,
      }),
    }
  )
);
