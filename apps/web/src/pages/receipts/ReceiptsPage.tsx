import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { FileText, Download, Printer, Search } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Table } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { paymentsService } from "@/services/payments.service";
import { useAuthStore } from "@/store/authStore";
import { getErrorMessage } from "@/services/api";
import type { Receipt } from "@/types";

export function ReceiptsPage() {
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
    queryKey: ["receipts", schoolId, page, debSearch],
    queryFn: () => paymentsService.listReceipts({ school: schoolId, page: String(page), search: debSearch || undefined }),
    enabled: !!schoolId,
  });

  const reprintMutation = useMutation({
    mutationFn: (id: string) => paymentsService.reprintReceipt(id),
    onSuccess: () => toast.success("Reprint logged."),
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const columns = [
    {
      key: "receipt_number", header: "Receipt No.",
      render: (v: unknown) => <span className="font-mono text-sm text-primary font-medium">{String(v)}</span>,
    },
    { key: "student_name", header: "Student" },
    { key: "student_admission_number", header: "Adm No." },
    { key: "academic_year_name", header: "Academic Year" },
    {
      key: "amount_paid", header: "Amount (NLe)",
      render: (v: unknown) => <span className="font-mono">NLe {Number(v).toLocaleString()}</span>,
    },
    { key: "payment_method", header: "Method" },
    {
      key: "generated_at", header: "Date",
      render: (v: unknown) => new Date(String(v)).toLocaleDateString(),
    },
    {
      key: "id", header: "", width: "120px",
      render: (_: unknown, row: Receipt) => (
        <div className="flex gap-1">
          <a
            href={paymentsService.downloadReceiptPdf(row.id)}
            target="_blank" rel="noreferrer"
            className="btn btn-outline btn-sm"
            title="Download PDF"
          >
            <Download className="h-3.5 w-3.5" />
          </a>
          <Button
            variant="ghost" size="sm"
            leftIcon={<Printer className="h-3.5 w-3.5" />}
            onClick={() => reprintMutation.mutate(row.id)}
            title="Log reprint"
          >
            Reprint
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Receipts</h1>
          <p className="page-subtitle">{data?.count ?? 0} receipts generated</p>
        </div>
      </div>

      <div className="flex gap-3">
        <div className="flex-1">
          <Input
            placeholder="Search by student name or receipt number..."
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
          keyExtractor={(r) => r.id}
          loading={isLoading}
          emptyMessage="No receipts generated yet."
        />
        <Pagination page={page} pageSize={25} total={data?.count ?? 0} onPageChange={setPage} />
      </div>
    </div>
  );
}
