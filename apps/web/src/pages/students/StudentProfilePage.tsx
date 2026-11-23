import React, { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  ChevronLeft, Edit, User, GraduationCap, DollarSign,
  Phone, MapPin, Calendar, Hash, AlertTriangle, Plus,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge, PaymentStatusBadge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { studentsService } from "@/services/students.service";
import { financeService } from "@/services/finance.service";
import { paymentsService } from "@/services/payments.service";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import type { Student, FinancialSummary, Enrollment, Receipt } from "@/types";

function ProfileField({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <dt className="text-xs text-text-muted font-medium">{label}</dt>
      <dd className="mt-0.5 text-sm text-text-primary">{value || "—"}</dd>
    </div>
  );
}

function ProgressBar({ progress }: { progress: number }) {
  const pct = Math.min(100, Math.max(0, progress));
  const color = pct >= 100 ? "bg-accent" : pct >= 50 ? "bg-secondary" : "bg-status-warning";
  return (
    <div className="w-full bg-gray-100 rounded-full h-2 mt-1">
      <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${pct}%` }} />
    </div>
  );
}

export function StudentProfilePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { activeSchool } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"academic" | "financial">("academic");
  const [applyTemplateOpen, setApplyTemplateOpen] = useState(false);

  const { data: student, isLoading } = useQuery({
    queryKey: ["student", id],
    queryFn: () => studentsService.get(id!),
    enabled: !!id,
  });

  const { data: financialData } = useQuery({
    queryKey: ["student-financial", id],
    queryFn: () => studentsService.getFinancialSummary(id!),
    enabled: !!id && activeTab === "financial",
  });

  const { data: enrollmentsData } = useQuery({
    queryKey: ["enrollments", id],
    queryFn: () =>
      api.get<{ results: Enrollment[] }>(`/enrollments/?student=${id}&school=${activeSchool?.school_id}`),
    enabled: !!id,
  });

  const { data: receiptsData } = useQuery({
    queryKey: ["receipts", id],
    queryFn: () => paymentsService.listReceipts({ student: id! }),
    enabled: !!id && activeTab === "financial",
  });

  const financial: FinancialSummary | undefined = financialData?.data;

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="card p-6 animate-pulse">
          <div className="flex gap-6">
            <div className="w-20 h-20 rounded-full bg-gray-200" />
            <div className="flex-1 space-y-3">
              <div className="h-6 bg-gray-200 rounded w-48" />
              <div className="h-4 bg-gray-200 rounded w-32" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!student) return <div className="text-center py-12 text-text-muted">Student not found.</div>;

  const tabs = [
    { id: "academic" as const, label: "Academic Profile", icon: <GraduationCap className="h-4 w-4" /> },
    { id: "financial" as const, label: "Financial Profile", icon: <DollarSign className="h-4 w-4" /> },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Back + header */}
      <div>
        <button
          onClick={() => navigate("/students")}
          className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary mb-3"
        >
          <ChevronLeft className="h-4 w-4" />
          Back to Students
        </button>
      </div>

      {/* Student hero card */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row gap-5">
          {/* Photo */}
          <div className="flex-shrink-0">
            {student.photograph_url ? (
              <img
                src={student.photograph_url}
                alt={student.full_name}
                className="w-20 h-20 rounded-full object-cover border-2 border-surface-border"
              />
            ) : (
              <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="h-8 w-8 text-primary" />
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <h1 className="text-xl font-bold text-text-primary">{student.full_name}</h1>
                <div className="flex flex-wrap items-center gap-3 mt-1 text-sm text-text-muted">
                  <span className="flex items-center gap-1">
                    <Hash className="h-3.5 w-3.5" />
                    {student.admission_number}
                  </span>
                  <span className="flex items-center gap-1 capitalize">
                    <User className="h-3.5 w-3.5" />
                    {student.gender}
                  </span>
                  {student.current_class && (
                    <span className="flex items-center gap-1">
                      <GraduationCap className="h-3.5 w-3.5" />
                      {student.current_class}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  variant={student.status === "active" ? "success" : "gray"}
                >
                  {student.status}
                </Badge>
                <Link to={`/students/${id}/edit`}>
                  <Button variant="outline" size="sm" leftIcon={<Edit className="h-3.5 w-3.5" />}>
                    Edit
                  </Button>
                </Link>
                <Link to="/payments/record" state={{ student }}>
                  <Button variant="accent" size="sm" leftIcon={<Plus className="h-3.5 w-3.5" />}>
                    Record Payment
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-surface-border">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-text-secondary hover:text-text-primary"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "academic" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Personal info */}
          <div className="card">
            <div className="card-header"><h3>Personal Information</h3></div>
            <div className="card-body">
              <dl className="grid grid-cols-2 gap-4">
                <ProfileField label="Full Name" value={student.full_name} />
                <ProfileField label="Admission No." value={student.admission_number} />
                <ProfileField label="Gender" value={student.gender} />
                <ProfileField label="Date of Birth" value={student.date_of_birth} />
                <ProfileField label="Admission Date" value={student.admission_date} />
                <ProfileField label="Status" value={student.status} />
                <div className="col-span-2">
                  <ProfileField label="Address" value={student.residential_address} />
                </div>
              </dl>
            </div>
          </div>

          {/* Guardians */}
          <div className="card">
            <div className="card-header flex items-center justify-between">
              <h3>Parent / Guardian</h3>
            </div>
            <div className="card-body space-y-4">
              {(student.guardians ?? []).length === 0 ? (
                <p className="text-sm text-text-muted">No guardians linked yet.</p>
              ) : (
                student.guardians!.map((sg) => (
                  <div key={sg.id} className="border border-surface-border rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <p className="font-medium text-sm">{sg.guardian_detail.full_name}</p>
                      {sg.is_primary && <Badge variant="info">Primary</Badge>}
                      {sg.is_emergency_contact && <Badge variant="warning">Emergency</Badge>}
                    </div>
                    <p className="text-xs text-text-muted capitalize">{sg.relationship}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-text-secondary">
                      <span className="flex items-center gap-1">
                        <Phone className="h-3 w-3" />
                        {sg.guardian_detail.phone_number}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Enrollment history */}
          <div className="card lg:col-span-2">
            <div className="card-header"><h3>Enrollment History</h3></div>
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Academic Year</th>
                    <th>Class</th>
                    <th>Status</th>
                    <th>Enrolled</th>
                  </tr>
                </thead>
                <tbody>
                  {(enrollmentsData?.results ?? []).length === 0 ? (
                    <tr><td colSpan={4} className="text-center py-6 text-text-muted">No enrollment records</td></tr>
                  ) : (
                    enrollmentsData!.results.map((e) => (
                      <tr key={e.id}>
                        <td>{e.academic_year_name}</td>
                        <td>{e.class_name}</td>
                        <td><Badge variant={e.is_active ? "success" : "gray"}>{e.status}</Badge></td>
                        <td className="text-text-muted">{e.enrollment_date}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === "financial" && (
        <div className="space-y-5">
          {/* Financial summary */}
          {financial && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Total Expected", value: `NLe ${Number(financial.total_expected).toLocaleString()}`, color: "text-text-primary" },
                { label: "Total Paid", value: `NLe ${Number(financial.total_paid).toLocaleString()}`, color: "text-accent" },
                { label: "Outstanding", value: `NLe ${Number(financial.outstanding).toLocaleString()}`, color: "text-status-warning" },
                { label: "Credit Balance", value: `NLe ${Number(financial.credit_balance).toLocaleString()}`, color: "text-secondary" },
              ].map((s) => (
                <div key={s.label} className="card p-4">
                  <p className="text-xs text-text-muted">{s.label}</p>
                  <p className={`text-lg font-bold mt-1 ${s.color}`}>{s.value}</p>
                </div>
              ))}
            </div>
          )}

          {/* Payment progress */}
          {financial && (
            <div className="card p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Payment Progress</span>
                <div className="flex items-center gap-2">
                  <PaymentStatusBadge status={financial.payment_status} />
                  <span className="text-sm font-bold text-primary">{financial.payment_progress}%</span>
                </div>
              </div>
              <ProgressBar progress={parseFloat(financial.payment_progress)} />
            </div>
          )}

          {/* Charge breakdown */}
          <div className="card">
            <div className="card-header flex items-center justify-between">
              <h3>Fee Breakdown</h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setApplyTemplateOpen(true)}
                leftIcon={<Plus className="h-3.5 w-3.5" />}
              >
                Apply Template
              </Button>
            </div>
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>Category</th>
                    <th>Expected</th>
                    <th>Paid</th>
                    <th>Outstanding</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(financial?.charges ?? []).length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-text-muted">
                        No fee charges assigned yet.
                      </td>
                    </tr>
                  ) : (
                    financial!.charges.map((c) => (
                      <tr key={c.id}>
                        <td>
                          <div>
                            <p className="font-medium">{c.description}</p>
                            {!c.is_mandatory && <span className="text-xs text-text-muted">Optional</span>}
                          </div>
                        </td>
                        <td>{c.category_name}</td>
                        <td className="font-mono text-sm">NLe {Number(c.net_amount).toLocaleString()}</td>
                        <td className="font-mono text-sm text-accent">NLe {Number(c.amount_paid).toLocaleString()}</td>
                        <td className="font-mono text-sm text-status-warning">NLe {Number(c.outstanding).toLocaleString()}</td>
                        <td><PaymentStatusBadge status={c.status} /></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recent receipts */}
          <div className="card">
            <div className="card-header"><h3>Receipts</h3></div>
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Receipt No.</th>
                    <th>Date</th>
                    <th>Amount</th>
                    <th>Method</th>
                    <th>Outstanding After</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {(receiptsData?.results ?? []).length === 0 ? (
                    <tr><td colSpan={6} className="text-center py-6 text-text-muted">No receipts yet</td></tr>
                  ) : (
                    receiptsData!.results.map((r) => (
                      <tr key={r.id}>
                        <td className="font-mono text-sm text-primary">{r.receipt_number}</td>
                        <td>{new Date(r.generated_at).toLocaleDateString()}</td>
                        <td className="font-mono">NLe {Number(r.amount_paid).toLocaleString()}</td>
                        <td>{r.payment_method}</td>
                        <td className="font-mono">NLe {Number(r.outstanding_after).toLocaleString()}</td>
                        <td>
                          <a
                            href={paymentsService.downloadReceiptPdf(r.id)}
                            target="_blank"
                            rel="noreferrer"
                            className="text-sm text-secondary hover:underline"
                          >
                            PDF
                          </a>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
