import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Table } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { PaymentStatusBadge } from "@/components/ui/Badge";
import { financeService } from "@/services/finance.service";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import type { StudentCharge, AcademicYear } from "@/types";

export function StudentChargesPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [academicYear, setAcademicYear] = useState("");

  React.useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  const { data: yearsData } = useQuery({
    queryKey: ["academic-years", schoolId],
    queryFn: () => api.get<{ results: AcademicYear[] }>(`/academic-years/?school=${schoolId}&page_size=50`),
    enabled: !!schoolId,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["student-charges", schoolId, page, debouncedSearch, academicYear],
    queryFn: () =>
      financeService.listCharges({
        school: schoolId,
        academic_year: academicYear || undefined,
        search: debouncedSearch || undefined,
        page: String(page),
        page_size: "25",
      }),
    enabled: !!schoolId,
  });

  const columns = [
    { key: "description", header: "Description", sortable: true },
    { key: "category_name", header: "Category" },
    {
      key: "net_amount", header: "Expected (NLe)",
      render: (v: unknown) => <span className="font-mono">{Number(v).toLocaleString()}</span>,
    },
    {
      key: "amount_paid", header: "Paid (NLe)",
      render: (v: unknown) => <span className="font-mono text-accent">{Number(v).toLocaleString()}</span>,
    },
    {
      key: "outstanding", header: "Outstanding (NLe)",
      render: (v: unknown) => <span className="font-mono text-status-warning">{Number(v).toLocaleString()}</span>,
    },
    {
      key: "status", header: "Status",
      render: (v: unknown) => <PaymentStatusBadge status={String(v)} />,
    },
    { key: "due_date", header: "Due Date", render: (v: unknown) => v ?? "—" },
  ];

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Student Charges</h1>
          <p className="page-subtitle">All individual student fee charges</p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input placeholder="Search charges..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            leftIcon={<Search className="h-4 w-4" />} />
        </div>
        <select className="form-select w-52" value={academicYear} onChange={(e) => { setAcademicYear(e.target.value); setPage(1); }}>
          <option value="">All Academic Years</option>
          {(yearsData?.results ?? []).map((y) => (
            <option key={y.id} value={y.id}>{y.name}</option>
          ))}
        </select>
      </div>

      <div className="card">
        <Table
          columns={columns as any}
          data={data?.results ?? []}
          keyExtractor={(c) => c.id}
          loading={isLoading}
          emptyMessage="No charges found."
        />
        <Pagination page={page} pageSize={25} total={data?.count ?? 0} onPageChange={setPage} />
      </div>
    </div>
  );
}
