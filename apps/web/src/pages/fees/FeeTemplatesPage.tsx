import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, ChevronDown, ChevronRight, Layers } from "lucide-react";
import toast from "react-hot-toast";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { financeService } from "@/services/finance.service";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { getErrorMessage } from "@/services/api";
import type { FeeTemplate, AcademicYear, Class, FeeCategory } from "@/types";

export function FeeTemplatesPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const qc = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  const { data: templates, isLoading } = useQuery({
    queryKey: ["fee-templates", schoolId],
    queryFn: () => financeService.listTemplates({ school: schoolId }),
    enabled: !!schoolId,
  });

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

  const { data: categoriesData } = useQuery({
    queryKey: ["fee-categories", schoolId],
    queryFn: () => financeService.listCategories(schoolId),
    enabled: !!schoolId,
  });

  const { register, handleSubmit, reset } = useForm<Partial<FeeTemplate>>();

  const createMutation = useMutation({
    mutationFn: (d: Partial<FeeTemplate>) =>
      financeService.createTemplate({ ...d, school: schoolId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fee-templates"] });
      toast.success("Template created.");
      setModalOpen(false); reset();
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const years = (yearsData?.results ?? []).map((y) => ({ value: y.id, label: y.name }));
  const classes = [{ value: "", label: "All Classes" }, ...(classesData?.results ?? []).map((c) => ({ value: c.id, label: c.name }))];
  const categories = (categoriesData?.results ?? []).map((c) => ({ value: c.id, label: c.name }));

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Fee Templates</h1>
          <p className="page-subtitle">Create reusable fee structures to apply to students</p>
        </div>
        <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />} onClick={() => { reset(); setModalOpen(true); }}>
          Create Template
        </Button>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse"><div className="h-14 bg-gray-100 rounded" /></div>
          ))
        ) : (templates?.results ?? []).length === 0 ? (
          <div className="card p-12 text-center text-text-muted">
            No fee templates. Create a template to quickly apply fee structures to students.
          </div>
        ) : (
          (templates?.results ?? []).map((t) => (
            <div key={t.id} className="card">
              <div
                className="p-5 flex items-center justify-between cursor-pointer hover:bg-surface-muted transition-colors rounded-xl"
                onClick={() => setExpanded(expanded === t.id ? null : t.id)}
              >
                <div className="flex items-center gap-3">
                  <Layers className="h-5 w-5 text-secondary flex-shrink-0" />
                  <div>
                    <p className="font-semibold text-text-primary">{t.name}</p>
                    <p className="text-xs text-text-muted">
                      {t.academic_year_name} {t.class_name ? `· ${t.class_name}` : "· All Classes"}
                      {" "} · {t.items.length} items · Total: NLe {Number(t.total_amount).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={t.is_active ? "success" : "gray"}>{t.is_active ? "Active" : "Inactive"}</Badge>
                  {expanded === t.id ? <ChevronDown className="h-4 w-4 text-text-muted" /> : <ChevronRight className="h-4 w-4 text-text-muted" />}
                </div>
              </div>

              {expanded === t.id && (
                <div className="border-t border-surface-border">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Description</th>
                        <th>Category</th>
                        <th>Amount (NLe)</th>
                        <th>Mandatory</th>
                        <th>Due Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {t.items.map((item) => (
                        <tr key={item.id}>
                          <td className="font-medium">{item.description}</td>
                          <td>{item.category_name}</td>
                          <td className="font-mono">{Number(item.amount).toLocaleString()}</td>
                          <td><Badge variant={item.is_mandatory ? "info" : "gray"}>{item.is_mandatory ? "Yes" : "No"}</Badge></td>
                          <td>{item.due_date ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Create Fee Template" size="md">
        <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
          <Input label="Template Name" required placeholder="e.g. JSS 1 Standard Fees 2024/25" {...register("name", { required: true })} />
          <Select label="Academic Year" required options={years} placeholder="Select year" {...register("academic_year", { required: true })} />
          <Select label="Target Class (optional)" options={classes} {...register("target_class")} />
          <Input label="Description" placeholder="Optional description" {...register("description")} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" loading={createMutation.isPending}>Create Template</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
