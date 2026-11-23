import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus, Search, Eye } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Table } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { PaymentStatusBadge } from "@/components/ui/Badge";
import { paymentsService } from "@/services/payments.service";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import type { Payment, AcademicYear } from "@/types";

export function PaymentsPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debSearch, setDebSearch] = useState("");
  const [status, setStatus] = useState("");
  const [method, setMethod] = useState("");
  const [academicYear, setAcademicYear] = useState("");

  React.useEffect(() => {
    const t = setTimeout(() => setDebSearch(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  const { data: yearsData } = useQuery({
    queryKey: ["academic-years", schoolId],
    queryFn: () => api.get<{ results: AcademicYear[] }>(`/academic-years/?school=${schoolId}&page_size=50`),
    enabled: !!schoolId,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["payments", schoolId, page, debSearch, status, method, academicYear],
    queryFn: () =>
      paymentsService.list({
        school: schoolId,
        page: String(page),
        search: debSearch || undefined,
        status: status || undefined,
        payment_method: method || undefined,
        academic_year: academicYear || undefined,
      }),
    enabled: !!schoolId,
  });

  const columns = [
    {
      key: "student_name", header: "Student",
      render: (v: unknown, row: Payment) => (
        <div>
          <p className="font-medium">{String(v)}</p>
          <p className="text-xs text-text-muted">{row.student_admission_number}</p>
        </div>
      ),
    },
    {
      key: "amount", header: "Amount (NLe)",
      render: (v: unknown) => <span className="font-mono font-semibold">NLe {Number(v).toLocaleString()}</span>,
    },
    {
      key: "payment_method", header: "Method",
      render: (v: unknown) => <span className="capitalize">{String(v).replace("_", " ")}</span>,
    },
    { key: "payment_date", header: "Date" },
    {
      key: "status", header: "Status",
      render: (v: unknown) => <PaymentStatusBadge status={String(v)} />,
    },
    { key: "recorded_by_name", header: "Recorded By" },
    {
      key: "id", header: "", width: "50px",
      render: (_: unknown, row: Payment) => (
        <Link to={`/payments/${row.id}`} className="btn btn-ghost btn-sm">
          <Eye className="h-4 w-4" />
        </Link>
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Payments</h1>
          <p className="page-subtitle">{data?.count ?? 0} payment records</p>
        </div>
        <Link to="/payments/record">
          <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />}>Record Payment</Button>
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 flex-wrap">
        <div className="flex-1 min-w-[200px]">
          <Input placeholder="Search by student or reference..." value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            leftIcon={<Search className="h-4 w-4" />} />
        </div>
        <select className="form-select w-40" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="confirmed">Confirmed</option>
          <option value="rejected">Rejected</option>
          <option value="reversed">Reversed</option>
        </select>
        <select className="form-select w-44" value={method} onChange={(e) => { setMethod(e.target.value); setPage(1); }}>
          <option value="">All Methods</option>
          <option value="cash">Cash</option>
          <option value="mobile_money">Mobile Money</option>
          <option value="bank_transfer">Bank Transfer</option>
        </select>
        <select className="form-select w-44" value={academicYear} onChange={(e) => { setAcademicYear(e.target.value); setPage(1); }}>
          <option value="">All Years</option>
          {(yearsData?.results ?? []).map((y) => <option key={y.id} value={y.id}>{y.name}</option>)}
        </select>
      </div>

      <div className="card">
        <Table
          columns={columns as any}
          data={data?.results ?? []}
          keyExtractor={(p) => p.id}
          loading={isLoading}
          emptyMessage="No payments recorded yet."
        />
        <Pagination page={page} pageSize={25} total={data?.count ?? 0} onPageChange={setPage} />
      </div>
    </div>
  );
}
