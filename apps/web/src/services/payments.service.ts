import { api, getApiBaseUrl } from "./api";
import type { Payment, PaginatedResponse, Receipt } from "@/types";

export const paymentsService = {
  list: (params: Record<string, string | undefined>) =>
    api.get<PaginatedResponse<Payment>>("/payments/", { params }),

  get: (id: string) =>
    api.get<Payment>(`/payments/${id}/`),

  record: (data: Record<string, unknown>) =>
    api.post<Payment>("/payments/", data),

  uploadEvidence: (paymentId: string, formData: FormData) =>
    api.upload(`/payments/${paymentId}/upload-evidence/`, formData),

  // Verification
  listPending: (schoolId: string) =>
    api.get<{ success: boolean; data: Payment[]; count: number }>(
      "/payment-verification/", { params: { school: schoolId } }
    ),

  verify: (paymentId: string, allocations: Array<{ charge_id: string; amount: number }>) =>
    api.post(`/payment-verification/${paymentId}/confirm/`, { allocations }),

  reject: (paymentId: string, reason: string) =>
    api.post(`/payment-verification/${paymentId}/reject/`, { reason }),

  reverse: (paymentId: string, reason: string) =>
    api.post(`/payment-verification/${paymentId}/reverse/`, { reason }),

  // Receipts
  generateReceipt: (paymentId: string) =>
    api.post<{ success: boolean; data: Receipt }>("/receipts/generate/", { payment_id: paymentId }),

  listReceipts: (params: Record<string, string | undefined>) =>
    api.get<PaginatedResponse<Receipt>>("/receipts/", { params }),

  downloadReceiptPdf: (receiptId: string) =>
    `${getApiBaseUrl()}/receipts/${receiptId}/pdf/`,

  reprintReceipt: (receiptId: string, notes?: string) =>
    api.post(`/receipts/${receiptId}/reprint/`, { notes }),
};
