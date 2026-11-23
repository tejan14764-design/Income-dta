import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Edit } from "lucide-react";
import toast from "react-hot-toast";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { financeService } from "@/services/finance.service";
import { useAuthStore } from "@/store/authStore";
import { getErrorMessage } from "@/services/api";
import type { FeeCategory } from "@/types";

const DEFAULT_CATEGORIES = [
  "School Fees", "Registration Fees", "Uniform", "School Polo",
  "Books", "Examination Fees", "Transportation", "Feeding", "Sports", "Other"
];

export function FeeCategoriesPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const qc = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<FeeCategory | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["fee-categories", schoolId],
    queryFn: () => financeService.listCategories(schoolId),
    enabled: !!schoolId,
  });

  const { register, handleSubmit, reset, setValue } = useForm<Partial<FeeCategory>>();

  const mutation = useMutation({
    mutationFn: (d: Partial<FeeCategory>) =>
      editing
        ? financeService.updateCategory(editing.id, d)
        : financeService.createCategory({ ...d, school: schoolId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fee-categories"] });
      toast.success(editing ? "Category updated." : "Category created.");
      setModalOpen(false); setEditing(null); reset();
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const openEdit = (cat: FeeCategory) => {
    setEditing(cat);
    setValue("name", cat.name); setValue("code", cat.code); setValue("description", cat.description);
    setModalOpen(true);
  };

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Fee Categories</h1>
          <p className="page-subtitle">Define fee types for your school</p>
        </div>
        <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />} onClick={() => { setEditing(null); reset(); setModalOpen(true); }}>
          Add Category
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card p-4 animate-pulse"><div className="h-12 bg-gray-100 rounded" /></div>
          ))
        ) : (data?.results ?? []).length === 0 ? (
          <div className="card p-10 text-center text-text-muted col-span-3">
            No fee categories. Add categories to get started.
          </div>
        ) : (
          (data?.results ?? []).map((cat) => (
            <div key={cat.id} className="card p-4 flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold text-text-primary">{cat.name}</p>
                {cat.code && <p className="text-xs text-text-muted font-mono">{cat.code}</p>}
                {cat.description && <p className="text-xs text-text-secondary mt-1">{cat.description}</p>}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <Badge variant={cat.is_active ? "success" : "gray"}>{cat.is_active ? "Active" : "Inactive"}</Badge>
                <Button variant="ghost" size="sm" onClick={() => openEdit(cat)}><Edit className="h-3.5 w-3.5" /></Button>
              </div>
            </div>
          ))
        )}
      </div>

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Edit Category" : "Add Fee Category"} size="sm">
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
          <Input label="Category Name" required placeholder="e.g. School Fees" {...register("name", { required: true })} />
          <Input label="Code" placeholder="e.g. SCH_FEE" {...register("code")} />
          <Input label="Description" placeholder="Optional" {...register("description")} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" loading={mutation.isPending}>{editing ? "Update" : "Create"}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
