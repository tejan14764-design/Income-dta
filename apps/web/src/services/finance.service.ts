import { api } from "./api";
import type {
  FeeCategory, FeeTemplate, FeeTemplateItem,
  StudentFeeAssignment, StudentCharge, PaginatedResponse
} from "@/types";

export const financeService = {
  // Fee Categories
  listCategories: (schoolId: string) =>
    api.get<PaginatedResponse<FeeCategory>>("/fees/categories/", { params: { school: schoolId } }),

  createCategory: (data: Partial<FeeCategory>) =>
    api.post<FeeCategory>("/fees/categories/", data),

  updateCategory: (id: string, data: Partial<FeeCategory>) =>
    api.patch<FeeCategory>(`/fees/categories/${id}/`, data),

  // Fee Templates
  listTemplates: (params: Record<string, string | undefined>) =>
    api.get<PaginatedResponse<FeeTemplate>>("/fees/templates/", { params }),

  getTemplate: (id: string) =>
    api.get<FeeTemplate>(`/fees/templates/${id}/`),

  createTemplate: (data: Partial<FeeTemplate>) =>
    api.post<FeeTemplate>("/fees/templates/", data),

  updateTemplate: (id: string, data: Partial<FeeTemplate>) =>
    api.patch<FeeTemplate>(`/fees/templates/${id}/`, data),

  applyTemplate: (templateId: string, studentId: string, academicYearId: string) =>
    api.post(`/fees/templates/${templateId}/apply/`, {
      student_id: studentId,
      academic_year_id: academicYearId,
    }),

  // Template Items
  createTemplateItem: (data: Partial<FeeTemplateItem>) =>
    api.post<FeeTemplateItem>("/fees/template-items/", data),

  updateTemplateItem: (id: string, data: Partial<FeeTemplateItem>) =>
    api.patch<FeeTemplateItem>(`/fees/template-items/${id}/`, data),

  deleteTemplateItem: (id: string) =>
    api.delete(`/fees/template-items/${id}/`),

  // Student Fee Assignments
  getStudentAssignment: (studentId: string, academicYearId: string) =>
    api.get<PaginatedResponse<StudentFeeAssignment>>("/fees/assignments/", {
      params: { student: studentId, academic_year: academicYearId },
    }),

  createAssignment: (data: Partial<StudentFeeAssignment>) =>
    api.post<StudentFeeAssignment>("/fees/assignments/", data),

  // Student Charges
  listCharges: (params: Record<string, string | undefined>) =>
    api.get<PaginatedResponse<StudentCharge>>("/student-charges/", { params }),

  createCharge: (data: Partial<StudentCharge>) =>
    api.post<StudentCharge>("/student-charges/", data),

  updateCharge: (id: string, data: Partial<StudentCharge>) =>
    api.patch<StudentCharge>(`/student-charges/${id}/`, data),

  applyAdjustment: (id: string, data: { adjustment_type: string; new_amount: number; reason: string }) =>
    api.post(`/student-charges/${id}/adjust/`, data),
};
