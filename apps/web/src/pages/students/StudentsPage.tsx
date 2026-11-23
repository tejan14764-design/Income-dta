import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { UserPlus, Search, Filter, Eye } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Table } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { Badge } from "@/components/ui/Badge";
import { studentsService } from "@/services/students.service";
import { useAuthStore } from "@/store/authStore";
import type { Student } from "@/types";

const STATUS_VARIANT = {
  active: "success",
  inactive: "gray",
  graduated: "info",
  transferred: "warning",
  withdrawn: "gray",
  suspended: "error",
} as const;

export function StudentsPage() {
  const navigate = useNavigate();
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // Debounce search
  React.useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  const { data, isLoading } = useQuery({
    queryKey: ["students", schoolId, page, debouncedSearch, statusFilter],
    queryFn: () =>
      studentsService.list({
        school: schoolId,
        page,
        search: debouncedSearch || undefined,
        status: statusFilter || undefined,
        page_size: 25,
      }),
    enabled: !!schoolId,
  });

  const columns = [
    {
      key: "admission_number",
      header: "Adm. No.",
      sortable: true,
      width: "120px",
      render: (value: unknown) => (
        <span className="font-mono text-sm font-medium text-primary">{String(value)}</span>
      ),
    },
    {
      key: "full_name",
      header: "Student Name",
      sortable: true,
      render: (value: unknown, row: Student) => (
        <div>
          <p className="font-medium text-text-primary">{String(value)}</p>
          <p className="text-xs text-text-muted">{row.gender}</p>
        </div>
      ),
    },
    {
      key: "current_class",
      header: "Class",
      render: (value: unknown) => value ? (
        <span className="badge badge-info">{String(value)}</span>
      ) : <span className="text-text-muted text-xs">—</span>,
    },
    {
      key: "current_academic_year",
      header: "Academic Year",
      render: (value: unknown) => value ? String(value) : <span className="text-text-muted text-xs">—</span>,
    },
    {
      key: "admission_date",
      header: "Admitted",
      render: (value: unknown) => (
        <span className="text-sm text-text-secondary">{String(value)}</span>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (value: unknown) => (
        <Badge variant={STATUS_VARIANT[value as keyof typeof STATUS_VARIANT] ?? "gray"}>
          {String(value)}
        </Badge>
      ),
    },
    {
      key: "id",
      header: "",
      width: "60px",
      render: (_: unknown, row: Student) => (
        <Link to={`/students/${row.id}`} className="btn btn-ghost btn-sm">
          <Eye className="h-4 w-4" />
        </Link>
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Students</h1>
          <p className="page-subtitle">
            {data?.count ?? 0} students registered
          </p>
        </div>
        <Button
          variant="primary"
          leftIcon={<UserPlus className="h-4 w-4" />}
          onClick={() => navigate("/students/register")}
        >
          Register Student
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            placeholder="Search by name or admission number..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>
        <select
          className="form-select w-40"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          aria-label="Filter by status"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="graduated">Graduated</option>
          <option value="transferred">Transferred</option>
          <option value="withdrawn">Withdrawn</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>

      {/* Table */}
      <div className="card">
        <Table
          columns={columns}
          data={data?.results ?? []}
          keyExtractor={(s) => s.id}
          loading={isLoading}
          emptyMessage="No students found. Register the first student to get started."
        />
        <Pagination
          page={page}
          pageSize={25}
          total={data?.count ?? 0}
          onPageChange={setPage}
        />
      </div>
    </div>
  );
}
