import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, CheckCircle, Archive } from "lucide-react";
import toast from "react-hot-toast";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { getErrorMessage } from "@/services/api";
import type { AcademicYear } from "@/types";

const STATUS_VARIANT = {
  active: "success", upcoming: "info", closed: "gray", archived: "gray",
} as const;

export function AcademicYearsPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const qc = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["academic-years", schoolId],
    queryFn: () => api.get<{ results: AcademicYear[] }>(`/academic-years/?school=${schoolId}&page_size=50`),
    enabled: !!schoolId,
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<Partial<AcademicYear>>();

  const createMutation = useMutation({
    mutationFn: (d: Partial<AcademicYear>) => api.post("/academic-years/", { ...d, school: schoolId }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["academic-years"] }); toast.success("Academic year created."); setModalOpen(false); reset(); },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const activateMutation = useMutation({
    mutationFn: (id: string) => api.post(`/academic-years/${id}/activate/`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["academic-years"] }); toast.success("Academic year activated."); },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const closeMutation = useMutation({
    mutationFn: (id: string) => api.post(`/academic-years/${id}/close/`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["academic-years"] }); toast.success("Academic year closed."); },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Academic Years</h1>
          <p className="page-subtitle">Manage school academic year cycles</p>
        </div>
        <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />} onClick={() => { reset(); setModalOpen(true); }}>
          Add Academic Year
        </Button>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse"><div className="h-14 bg-gray-100 rounded" /></div>
          ))
        ) : (data?.results ?? []).length === 0 ? (
          <div className="card p-12 text-center text-text-muted">No academic years yet.</div>
        ) : (
          (data?.results ?? []).map((yr) => (
            <div key={yr.id} className="card p-5 flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold text-text-primary">{yr.name}</h3>
                  {yr.is_current && <Badge variant="success">Current</Badge>}
                  <Badge variant={STATUS_VARIANT[yr.status] ?? "gray"}>{yr.status}</Badge>
                </div>
                <p className="text-sm text-text-muted mt-1">
                  {yr.start_date} → {yr.end_date}
                </p>
              </div>
              <div className="flex gap-2">
                {yr.status === "upcoming" && (
                  <Button
                    variant="accent" size="sm"
                    leftIcon={<CheckCircle className="h-3.5 w-3.5" />}
                    loading={activateMutation.isPending}
                    onClick={() => activateMutation.mutate(yr.id)}
                  >
                    Activate
                  </Button>
                )}
                {yr.status === "active" && (
                  <Button
                    variant="outline" size="sm"
                    leftIcon={<Archive className="h-3.5 w-3.5" />}
                    loading={closeMutation.isPending}
                    onClick={() => { if (confirm("Close this academic year?")) closeMutation.mutate(yr.id); }}
                  >
                    Close Year
                  </Button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Add Academic Year" size="sm">
        <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
          <Input label="Year Name" required placeholder="e.g. 2024/2025" {...register("name", { required: true })} />
          <Input label="Start Date" type="date" required {...register("start_date", { required: true })} />
          <Input label="End Date" type="date" required {...register("end_date", { required: true })} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" loading={createMutation.isPending}>Create</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
