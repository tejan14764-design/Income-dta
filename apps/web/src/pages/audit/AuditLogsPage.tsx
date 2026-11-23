import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Shield } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Table } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import type { AuditLog } from "@/types";

const ACTION_COLOR: Record<string, "success" | "warning" | "error" | "info" | "purple" | "gray"> = {
  PAYMENT_VERIFIED: "success", PAYMENT_RECORDED: "info",
  PAYMENT_REJECTED: "error", PAYMENT_REVERSED: "warning",
  STUDENT_REGISTERED: "success", STUDENT_UPDATED: "info",
  FEE_ADJUSTED: "warning", CSV_EXPORTED: "gray",
  USER_CREATED: "info", RECEIPT_GENERATED: "purple",
};

export function AuditLogsPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debSearch, setDebSearch] = useState("");

  React.useEffect(() => {
    const t = setTimeout(() => setDebSearch(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  const { data, isLoading } = useQuery({
    queryKey: ["audit-logs", schoolId, page, debSearch],
    queryFn: () =>
      api.get<{ results: AuditLog[]; count: number }>(
        `/audit/?school=${schoolId}&page=${page}&search=${encodeURIComponent(debSearch)}&page_size=25`
      ),
    enabled: !!schoolId,
  });

  const columns = [
    {
      key: "timestamp", header: "Time",
      render: (v: unknown) => (
        <span className="text-xs text-text-muted whitespace-nowrap">
          {new Date(String(v)).toLocaleString()}
        </span>
      ),
      width: "160px",
    },
    {
      key: "actor_name", header: "User",
      render: (v: unknown) => <span className="font-medium">{String(v)}</span>,
    },
    {
      key: "action", header: "Action",
      render: (v: unknown) => (
        <Badge variant={ACTION_COLOR[String(v)] ?? "gray"} className="font-mono text-xs">
          {String(v).replace(/_/g, " ")}
        </Badge>
      ),
    },
    { key: "object_type", header: "Type" },
    {
      key: "object_repr", header: "Object",
      render: (v: unknown) => (
        <span className="text-sm text-text-secondary truncate max-w-[200px] block">{String(v)}</span>
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Audit Logs</h1>
          <p className="page-subtitle">Complete activity trail — read only</p>
        </div>
      </div>

      <div className="flex gap-3">
        <div className="flex-1">
          <Input
            placeholder="Search actions, users, records..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>
      </div>

      <div className="card">
        <Table
          columns={columns as any}
          data={data?.results ?? []}
          keyExtractor={(l) => l.id}
          loading={isLoading}
          emptyMessage="No audit records found."
        />
        <Pagination page={page} pageSize={25} total={data?.count ?? 0} onPageChange={setPage} />
      </div>
    </div>
  );
}
