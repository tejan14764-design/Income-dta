import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, Download } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { PaymentStatusBadge } from "@/components/ui/Badge";
import { Table } from "@/components/ui/Table";
import { api, getApiBaseUrl } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import type { AcademicYear, Class, FinancialReportRow, FinancialReportSummary } from "@/types";

export function ReportsPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const [academicYear, setAcademicYear] = useState("");
  const [classId, setClassId] = useState("");
  const [paymentStatus, setPaymentStatus] = useState("");
  const [runQuery, setRunQuery] = useState(false);

  const { data: yearsData } = useQuery({
    queryKey: ["academic-years", schoolId],
    queryFn: () => api.get<{ results: AcademicYear[] }>(`/academic-years/?school=${schoolId}&page_size=50`),
    enabled: !!schoolId,
  });

  const { data: classesData } = useQuery({
    queryKey: ["classes", schoolId],
    queryFn: () => api.get<{ results: Class[] }>(`/classes/?school=${schoolId}&page_size=100`),
    enabled: !!schoolId,
  });

  const { data: reportData, isLoading } = useQuery({
    queryKey: ["financial-report", schoolId, academicYear, classId, paymentStatus],
    queryFn: () => {
      const params = new URLSearchParams({ school: schoolId, academic_year: academicYear });
      if (classId) params.append("class_id", classId);
      if (paymentStatus) params.append("payment_status", paymentStatus);
      return api.get<{ success: boolean; data: { rows: FinancialReportRow[]; summary: FinancialReportSummary } }>(
        `/reports/financial/?${params}`
      );
    },
    enabled: runQuery && !!academicYear,
  });

  const years = (yearsData?.results ?? []).map((y) => ({ value: y.id, label: y.name }));
  const classes = [
    { value: "", label: "All Classes" },
    ...(classesData?.results ?? []).map((c) => ({ value: c.id, label: c.name })),
  ];
  const statusOptions = [
    { value: "", label: "All Statuses" },
    { value: "fully_paid", label: "Fully Paid" },
    { value: "partially_paid", label: "Partially Paid" },
    { value: "unpaid", label: "Unpaid" },
  ];

  const summary = reportData?.data?.summary;
  const rows = reportData?.data?.rows ?? [];

  const csvUrl = (() => {
    if (!academicYear) return "#";
    const params = new URLSearchParams({ school: schoolId, academic_year: academicYear });
    if (classId) params.append("class_id", classId);
    return `${getApiBaseUrl()}/reports/export/csv/?${params}`;
  })();

  const columns = [
    { key: "admission_number", header: "Adm. No.", render: (v: unknown) => <span className="font-mono text-sm text-primary">{String(v)}</span> },
    { key: "student_name", header: "Student" },
    { key: "class", header: "Class" },
    { key: "total_expected", header: "Expected (NLe)", render: (v: unknown) => <span className="font-mono">{Number(v).toLocaleString()}</span> },
    { key: "total_paid", header: "Paid (NLe)", render: (v: unknown) => <span className="font-mono text-accent">{Number(v).toLocaleString()}</span> },
    { key: "outstanding", header: "Outstanding (NLe)", render: (v: unknown) => <span className="font-mono text-status-warning">{Number(v).toLocaleString()}</span> },
    { key: "payment_status", header: "Status", render: (v: unknown) => <PaymentStatusBadge status={String(v).toLowerCase().replace(" ", "_")} /> },
  ];

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Financial Reports</h1>
          <p className="page-subtitle">Class-based fee collection summary</p>
        </div>
        {academicYear && (
          <a href={csvUrl} download="financial-report.csv">
            <Button variant="outline" leftIcon={<Download className="h-4 w-4" />}>
              Export CSV
            </Button>
          </a>
        )}
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-3 flex-wrap">
          <Select label="Academic Year" options={years} placeholder="Select year"
            value={academicYear} onChange={(e) => { setAcademicYear(e.target.value); setRunQuery(false); }} />
          <Select label="Class" options={classes}
            value={classId} onChange={(e) => { setClassId(e.target.value); setRunQuery(false); }} />
          <Select label="Payment Status" options={statusOptions}
            value={paymentStatus} onChange={(e) => { setPaymentStatus(e.target.value); setRunQuery(false); }} />
          <div className="flex items-end">
            <Button
              variant="primary"
              leftIcon={<BarChart3 className="h-4 w-4" />}
              disabled={!academicYear}
              onClick={() => setRunQuery(true)}
            >
              Generate Report
            </Button>
          </div>
        </div>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total Students", value: summary.total_students, color: "text-text-primary" },
            { label: "Total Expected (NLe)", value: Number(summary.total_expected).toLocaleString(), color: "text-text-primary" },
            { label: "Total Collected (NLe)", value: Number(summary.total_collected).toLocaleString(), color: "text-accent" },
            { label: "Total Outstanding (NLe)", value: Number(summary.total_outstanding).toLocaleString(), color: "text-status-warning" },
            { label: "Fully Paid", value: summary.fully_paid, color: "text-accent" },
            { label: "Partially Paid", value: summary.partially_paid, color: "text-secondary" },
            { label: "Unpaid", value: summary.unpaid, color: "text-status-error" },
          ].map((s) => (
            <div key={s.label} className="card p-4">
              <p className="text-xs text-text-muted">{s.label}</p>
              <p className={`text-lg font-bold mt-1 ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Report table */}
      {runQuery && (
        <div className="card">
          <Table
            columns={columns as any}
            data={rows}
            keyExtractor={(r) => r.admission_number}
            loading={isLoading}
            emptyMessage={academicYear ? "No data for selected filters." : "Select an academic year and generate."}
          />
        </div>
      )}
    </div>
  );
}
