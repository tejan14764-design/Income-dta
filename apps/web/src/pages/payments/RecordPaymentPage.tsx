import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { ChevronLeft, Plus, Trash2, Upload } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { paymentsService } from "@/services/payments.service";
import { studentsService } from "@/services/students.service";
import { financeService } from "@/services/finance.service";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { getErrorMessage } from "@/services/api";
import type { Student, AcademicYear, StudentCharge } from "@/types";

const schema = z.object({
  student: z.string().min(1, "Student is required"),
  academic_year: z.string().min(1, "Academic year is required"),
  payment_method: z.enum(["cash", "mobile_money", "bank_transfer"]),
  amount: z.string().min(1, "Amount is required"),
  payment_date: z.string().min(1, "Payment date is required"),
  transaction_reference: z.string().optional(),
  bank_name: z.string().optional(),
  payer_name: z.string().optional(),
  notes: z.string().optional(),
});

type PaymentForm = z.infer<typeof schema>;

export function RecordPaymentPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const qc = useQueryClient();
  const preloadedStudent: Student | undefined = location.state?.student;

  const [studentSearch, setStudentSearch] = useState(preloadedStudent?.full_name ?? "");
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(preloadedStudent ?? null);
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);
  const [allocations, setAllocations] = useState<{ charge_id: string; amount: string }[]>([]);

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<PaymentForm>({
    resolver: zodResolver(schema),
    defaultValues: {
      student: preloadedStudent?.id ?? "",
      payment_date: new Date().toISOString().split("T")[0],
      payment_method: "cash",
    },
  });

  const selectedMethod = watch("payment_method");
  const selectedAcademicYear = watch("academic_year");

  const { data: studentsData } = useQuery({
    queryKey: ["students-search", studentSearch, schoolId],
    queryFn: () => studentsService.list({ school: schoolId, search: studentSearch, page_size: 10 }),
    enabled: studentSearch.length > 1 && !selectedStudent,
  });

  const { data: yearsData } = useQuery({
    queryKey: ["academic-years", schoolId],
    queryFn: () => api.get<{ results: AcademicYear[] }>(`/academic-years/?school=${schoolId}&page_size=50`),
    enabled: !!schoolId,
  });

  const { data: chargesData } = useQuery({
    queryKey: ["student-charges", selectedStudent?.id, selectedAcademicYear],
    queryFn: () =>
      financeService.listCharges({
        student: selectedStudent!.id,
        academic_year: selectedAcademicYear,
      }),
    enabled: !!selectedStudent && !!selectedAcademicYear,
  });

  const mutation = useMutation({
    mutationFn: async (data: PaymentForm) => {
      const payload: Record<string, unknown> = {
        school: schoolId,
        student: data.student,
        academic_year: data.academic_year,
        payment_method: data.payment_method,
        amount: data.amount,
        payment_date: data.payment_date,
        transaction_reference: data.transaction_reference || "",
        bank_name: data.bank_name || "",
        payer_name: data.payer_name || "",
        notes: data.notes || "",
        allocations: allocations
          .filter((a) => a.charge_id && parseFloat(a.amount) > 0)
          .map((a) => ({ charge_id: a.charge_id, amount: parseFloat(a.amount) })),
      };
      const payment = await paymentsService.record(payload);

      // Upload evidence if provided
      if (evidenceFile && (data.payment_method === "mobile_money" || data.payment_method === "bank_transfer")) {
        const fd = new FormData();
        fd.append("file", evidenceFile);
        fd.append("evidence_type",
          data.payment_method === "mobile_money" ? "sms_screenshot" : "bank_receipt"
        );
        await paymentsService.uploadEvidence(payment.id, fd);
      }

      return payment;
    },
    onSuccess: (payment) => {
      qc.invalidateQueries({ queryKey: ["payments"] });
      toast.success("Payment recorded successfully.");
      navigate(`/payments`);
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const years = (yearsData?.results ?? []).map((y) => ({ value: y.id, label: y.name }));
  const unpaidCharges = (chargesData?.results ?? []).filter(
    (c) => c.status !== "fully_paid" && c.is_active
  );

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div>
        <button onClick={() => navigate(-1)} className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary mb-3">
          <ChevronLeft className="h-4 w-4" />
          Back
        </button>
        <h1 className="page-title">Record Payment</h1>
      </div>

      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} noValidate className="space-y-5">
        {/* Student selection */}
        <div className="card">
          <div className="card-header"><h3>Student</h3></div>
          <div className="card-body space-y-3">
            {selectedStudent ? (
              <div className="flex items-center justify-between p-3 bg-surface-muted rounded-lg">
                <div>
                  <p className="font-medium">{selectedStudent.full_name}</p>
                  <p className="text-xs text-text-muted">{selectedStudent.admission_number}</p>
                </div>
                <Button variant="ghost" size="sm" onClick={() => { setSelectedStudent(null); setValue("student", ""); setStudentSearch(""); }}>
                  Change
                </Button>
              </div>
            ) : (
              <div className="relative">
                <Input
                  placeholder="Search student by name or admission number..."
                  value={studentSearch}
                  onChange={(e) => setStudentSearch(e.target.value)}
                />
                {(studentsData?.results ?? []).length > 0 && (
                  <div className="absolute z-10 w-full bg-white border border-surface-border rounded-lg shadow-card mt-1 max-h-48 overflow-y-auto">
                    {studentsData!.results.map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        className="w-full text-left px-4 py-2.5 hover:bg-surface-muted text-sm"
                        onClick={() => {
                          setSelectedStudent(s);
                          setValue("student", s.id);
                          setStudentSearch(s.full_name);
                        }}
                      >
                        <span className="font-medium">{s.full_name}</span>
                        <span className="text-text-muted ml-2 text-xs">{s.admission_number}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
            {errors.student && <p className="form-error">{errors.student.message}</p>}
          </div>
        </div>

        {/* Payment details */}
        <div className="card">
          <div className="card-header"><h3>Payment Details</h3></div>
          <div className="card-body grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select label="Academic Year" required options={years} placeholder="Select year" error={errors.academic_year?.message} {...register("academic_year")} />
            <Select
              label="Payment Method" required
              options={[
                { value: "cash", label: "Cash" },
                { value: "mobile_money", label: "Mobile Money" },
                { value: "bank_transfer", label: "Bank Transfer" },
              ]}
              {...register("payment_method")}
            />
            <Input label="Amount (NLe)" type="number" step="0.01" required placeholder="0.00"
              error={errors.amount?.message} {...register("amount")} />
            <Input label="Payment Date" type="date" required error={errors.payment_date?.message} {...register("payment_date")} />
            {(selectedMethod === "mobile_money" || selectedMethod === "bank_transfer") && (
              <Input label="Transaction Reference" required placeholder="Reference number"
                error={errors.transaction_reference?.message} {...register("transaction_reference")} />
            )}
            {selectedMethod === "bank_transfer" && (
              <Input label="Bank Name" placeholder="Bank name" {...register("bank_name")} />
            )}
            <Input label="Payer Name" placeholder="Name on receipt" {...register("payer_name")} />
            <div className="md:col-span-2">
              <label className="form-label">Notes</label>
              <textarea className="form-input resize-none" rows={2} placeholder="Optional notes..." {...register("notes")} />
            </div>
          </div>
        </div>

        {/* Evidence upload */}
        {(selectedMethod === "mobile_money" || selectedMethod === "bank_transfer") && (
          <div className="card">
            <div className="card-header"><h3>Payment Evidence</h3></div>
            <div className="card-body">
              <label className="flex flex-col items-center justify-center border-2 border-dashed border-surface-border rounded-xl p-8 cursor-pointer hover:border-primary transition-colors">
                <Upload className="h-8 w-8 text-text-muted mb-2" />
                <p className="text-sm font-medium text-text-primary">
                  {evidenceFile ? evidenceFile.name : "Upload screenshot or receipt"}
                </p>
                <p className="text-xs text-text-muted mt-1">JPG, PNG or PDF, max 10MB</p>
                <input
                  type="file"
                  className="hidden"
                  accept=".jpg,.jpeg,.png,.webp,.pdf"
                  onChange={(e) => setEvidenceFile(e.target.files?.[0] ?? null)}
                />
              </label>
            </div>
          </div>
        )}

        {/* Fee allocation */}
        {unpaidCharges.length > 0 && (
          <div className="card">
            <div className="card-header flex items-center justify-between">
              <h3>Allocate to Charges</h3>
              <span className="text-xs text-text-muted">Optional — assign payment to specific fees</span>
            </div>
            <div className="card-body space-y-3">
              {unpaidCharges.map((charge) => {
                const existing = allocations.find((a) => a.charge_id === charge.id);
                return (
                  <div key={charge.id} className="flex items-center gap-3">
                    <div className="flex-1">
                      <p className="text-sm font-medium">{charge.description}</p>
                      <p className="text-xs text-text-muted">
                        Outstanding: NLe {Number(charge.outstanding).toLocaleString()}
                      </p>
                    </div>
                    <div className="w-32">
                      <Input
                        type="number" step="0.01" placeholder="0.00"
                        value={existing?.amount ?? ""}
                        onChange={(e) => {
                          const val = e.target.value;
                          setAllocations((prev) => {
                            const filtered = prev.filter((a) => a.charge_id !== charge.id);
                            if (val) return [...filtered, { charge_id: charge.id, amount: val }];
                            return filtered;
                          });
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3">
          <Button variant="outline" type="button" onClick={() => navigate(-1)}>Cancel</Button>
          <Button variant="primary" type="submit" loading={mutation.isPending}>Record Payment</Button>
        </div>
      </form>
    </div>
  );
}
