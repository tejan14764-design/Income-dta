import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { CheckCircle, XCircle, Eye, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { PaymentStatusBadge } from "@/components/ui/Badge";
import { paymentsService } from "@/services/payments.service";
import { financeService } from "@/services/finance.service";
import { useAuthStore } from "@/store/authStore";
import { getErrorMessage } from "@/services/api";
import type { Payment } from "@/types";

export function PaymentVerificationPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const qc = useQueryClient();

  const [viewPayment, setViewPayment] = useState<Payment | null>(null);
  const [rejectModal, setRejectModal] = useState<Payment | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["pending-payments", schoolId],
    queryFn: () => paymentsService.listPending(schoolId),
    enabled: !!schoolId,
    refetchInterval: 30_000,
  });

  const { data: chargesData } = useQuery({
    queryKey: ["charges-for-verify", viewPayment?.student, viewPayment?.academic_year],
    queryFn: () =>
      financeService.listCharges({
        student: viewPayment!.student,
        academic_year: viewPayment!.academic_year,
      }),
    enabled: !!viewPayment,
  });

  const [allocations, setAllocations] = useState<Record<string, string>>({});

  const confirmMutation = useMutation({
    mutationFn: ({ id }: { id: string }) => {
      const allocs = Object.entries(allocations)
        .filter(([, amt]) => parseFloat(amt) > 0)
        .map(([charge_id, amount]) => ({ charge_id, amount: parseFloat(amount) }));
      return paymentsService.verify(id, allocs);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pending-payments"] });
      toast.success("Payment confirmed.");
      setViewPayment(null);
      setAllocations({});
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      paymentsService.reject(id, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pending-payments"] });
      toast.success("Payment rejected.");
      setRejectModal(null);
      setRejectReason("");
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const pending = data?.data ?? [];

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Payment Verification</h1>
          <p className="page-subtitle">
            {data?.count ?? 0} payments pending verification
          </p>
        </div>
      </div>

      {pending.length === 0 && !isLoading ? (
        <div className="card p-16 text-center">
          <CheckCircle className="h-12 w-12 text-accent mx-auto mb-3" />
          <p className="text-lg font-semibold text-text-primary">All caught up!</p>
          <p className="text-sm text-text-muted">No payments pending verification.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="card p-5 animate-pulse"><div className="h-16 bg-gray-100 rounded" /></div>
            ))
          ) : (
            pending.map((payment) => (
              <div key={payment.id} className="card p-5 flex flex-col sm:flex-row sm:items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap">
                    <p className="font-semibold">{payment.student_name}</p>
                    <span className="text-xs text-text-muted">{payment.student_admission_number}</span>
                    <PaymentStatusBadge status={payment.status} />
                  </div>
                  <div className="mt-1 flex flex-wrap gap-4 text-sm text-text-muted">
                    <span>NLe {Number(payment.amount).toLocaleString()}</span>
                    <span className="capitalize">{payment.payment_method.replace("_", " ")}</span>
                    {payment.transaction_reference && (
                      <span className="font-mono text-xs">Ref: {payment.transaction_reference}</span>
                    )}
                    <span>{payment.payment_date}</span>
                    <span>By: {payment.recorded_by_name}</span>
                  </div>
                  {payment.evidence_files.length > 0 && (
                    <div className="mt-2 flex gap-2">
                      {payment.evidence_files.map((ev) => (
                        <a key={ev.id} href={ev.file_url} target="_blank" rel="noreferrer"
                          className="text-xs text-secondary underline">
                          {ev.evidence_type.replace("_", " ")}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <Button
                    variant="ghost" size="sm"
                    leftIcon={<Eye className="h-3.5 w-3.5" />}
                    onClick={() => { setViewPayment(payment); setAllocations({}); }}
                  >
                    Review
                  </Button>
                  <Button
                    variant="danger" size="sm"
                    leftIcon={<XCircle className="h-3.5 w-3.5" />}
                    onClick={() => setRejectModal(payment)}
                  >
                    Reject
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Review & Confirm Modal */}
      <Modal isOpen={!!viewPayment} onClose={() => { setViewPayment(null); setAllocations({}); }}
        title="Review & Confirm Payment" size="lg">
        {viewPayment && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-3 text-sm">
              {[
                ["Student", viewPayment.student_name],
                ["Amount", `NLe ${Number(viewPayment.amount).toLocaleString()}`],
                ["Method", viewPayment.payment_method.replace("_", " ")],
                ["Date", viewPayment.payment_date],
                ["Reference", viewPayment.transaction_reference || "—"],
                ["Recorded By", viewPayment.recorded_by_name],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt className="text-xs text-text-muted">{label}</dt>
                  <dd className="font-medium capitalize">{value}</dd>
                </div>
              ))}
            </div>

            {viewPayment.evidence_files.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">Evidence Files</p>
                <div className="flex gap-3 flex-wrap">
                  {viewPayment.evidence_files.map((ev) => (
                    <a key={ev.id} href={ev.file_url} target="_blank" rel="noreferrer"
                      className="btn btn-outline btn-sm">
                      {ev.evidence_type.replace("_", " ")}
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Allocation */}
            {(chargesData?.results ?? []).filter((c) => c.status !== "fully_paid" && c.is_active).length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">Allocate to Charges</p>
                <div className="space-y-2">
                  {chargesData!.results
                    .filter((c) => c.status !== "fully_paid" && c.is_active)
                    .map((charge) => (
                      <div key={charge.id} className="flex items-center gap-3">
                        <div className="flex-1">
                          <p className="text-sm">{charge.description}</p>
                          <p className="text-xs text-text-muted">Outstanding: NLe {Number(charge.outstanding).toLocaleString()}</p>
                        </div>
                        <input
                          type="number" step="0.01" placeholder="0.00"
                          className="form-input w-28 text-sm"
                          value={allocations[charge.id] ?? ""}
                          onChange={(e) => setAllocations((prev) => ({ ...prev, [charge.id]: e.target.value }))}
                        />
                      </div>
                    ))}
                </div>
              </div>
            )}

            <div className="flex justify-end gap-3 border-t border-surface-border pt-4">
              <Button variant="outline" onClick={() => { setViewPayment(null); setAllocations({}); }}>Cancel</Button>
              <Button
                variant="accent"
                leftIcon={<CheckCircle className="h-4 w-4" />}
                loading={confirmMutation.isPending}
                onClick={() => confirmMutation.mutate({ id: viewPayment.id })}
              >
                Confirm Payment
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Reject Modal */}
      <Modal isOpen={!!rejectModal} onClose={() => { setRejectModal(null); setRejectReason(""); }}
        title="Reject Payment" size="sm">
        {rejectModal && (
          <div className="space-y-4">
            <div className="flex gap-3 p-3 bg-red-50 rounded-lg text-sm text-red-800">
              <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
              <p>You are rejecting NLe {Number(rejectModal.amount).toLocaleString()} from {rejectModal.student_name}.</p>
            </div>
            <div>
              <label className="form-label">Rejection Reason <span className="text-status-error">*</span></label>
              <textarea
                className="form-input resize-none"
                rows={3}
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Explain why this payment is being rejected..."
              />
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => { setRejectModal(null); setRejectReason(""); }}>Cancel</Button>
              <Button
                variant="danger"
                loading={rejectMutation.isPending}
                disabled={rejectReason.trim().length < 10}
                onClick={() => rejectMutation.mutate({ id: rejectModal.id, reason: rejectReason })}
              >
                Reject Payment
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
