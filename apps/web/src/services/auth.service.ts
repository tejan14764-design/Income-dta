import { api } from "./api";
import type { User, SchoolMembership } from "@/types";

interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
  memberships: SchoolMembership[];
}

export const authService = {
  login: (username: string, password: string) =>
    api.post<LoginResponse>("/auth/login/", { username, password }),

  logout: (refresh: string) =>
    api.post("/auth/logout/", { refresh }),

  me: () => api.get<{ success: boolean; data: User & { memberships: SchoolMembership[] } }>("/auth/me/"),

  refreshToken: (refresh: string) =>
    api.post<{ access: string }>("/auth/token/refresh/", { refresh }),

  changePassword: (data: { current_password: string; new_password: string; confirm_password: string }) =>
    api.post("/auth/change-password/", data),
};
