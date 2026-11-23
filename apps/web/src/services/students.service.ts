import { api } from "./api";
import type { Student, Guardian, StudentGuardian, StudentConfidential, FinancialSummary, PaginatedResponse } from "@/types";

export const studentsService = {
  list: (params: Record<string, string | number | undefined>) =>
    api.get<PaginatedResponse<Student>>("/students/", { params }),

  get: (id: string) =>
    api.get<Student>(`/students/${id}/`),

  create: (data: FormData) =>
    api.upload<Student>("/students/", data),

  update: (id: string, data: Partial<Student> | FormData) =>
    api.patch<Student>(`/students/${id}/`, data),

  getConfidential: (id: string) =>
    api.get<StudentConfidential>(`/students/${id}/confidential/`),

  updateConfidential: (id: string, data: Partial<StudentConfidential>) =>
    api.patch(`/students/${id}/confidential/`, data),

  getFinancialSummary: (id: string) =>
    api.get<{ success: boolean; data: FinancialSummary }>(`/students/${id}/financial_summary/`),

  // Guardians
  listGuardians: (schoolId: string) =>
    api.get<PaginatedResponse<Guardian>>("/students/guardians/", { params: { school: schoolId } }),

  createGuardian: (data: Partial<Guardian>) =>
    api.post<Guardian>("/students/guardians/", data),

  linkGuardian: (data: Partial<StudentGuardian>) =>
    api.post<StudentGuardian>("/students/student-guardians/", data),

  listStudentGuardians: (studentId: string) =>
    api.get<PaginatedResponse<StudentGuardian>>("/students/student-guardians/", {
      params: { student: studentId },
    }),
};
