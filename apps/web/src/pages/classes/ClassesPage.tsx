import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Edit, Users } from "lucide-react";
import toast from "react-hot-toast";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Table } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { getErrorMessage } from "@/services/api";
import type { Class } from "@/types";

export function ClassesPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const qc = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Class | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["classes", schoolId],
    queryFn: () => api.get<{ results: Class[] }>(`/classes/?school=${schoolId}&page_size=100`),
    enabled: !!schoolId,
  });

  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<Partial<Class>>();

  const mutation = useMutation({
    mutationFn: (d: Partial<Class>) =>
      editing
        ? api.patch(`/classes/${editing.id}/`, d)
        : api.post("/classes/", { ...d, school: schoolId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["classes"] });
      toast.success(editing ? "Class updated." : "Class created.");
      setModalOpen(false);
      setEditing(null);
      reset();
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const openCreate = () => { setEditing(null); reset(); setModalOpen(true); };
  const openEdit = (cls: Class) => {
    setEditing(cls);
    setValue("name", cls.name);
    setValue("short_name", cls.short_name);
    setValue("level", cls.level);
    setValue("description", cls.description);
    setValue("capacity", cls.capacity);
    setModalOpen(true);
  };

  const columns = [
    { key: "name", header: "Class Name", sortable: true },
    { key: "short_name", header: "Short Name" },
    { key: "level", header: "Level", sortable: true },
    {
      key: "student_count", header: "Students",
      render: (v: unknown) => (
        <span className="flex items-center gap-1 text-sm"><Users className="h-3.5 w-3.5" />{String(v)}</span>
      ),
    },
    {
      key: "is_active", header: "Status",
      render: (v: unknown) => <Badge variant={v ? "success" : "gray"}>{v ? "Active" : "Inactive"}</Badge>,
    },
    {
      key: "id", header: "", width: "60px",
      render: (_: unknown, row: Class) => (
        <Button variant="ghost" size="sm" onClick={() => openEdit(row)} leftIcon={<Edit className="h-3.5 w-3.5" />}>Edit</Button>
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Classes</h1>
          <p className="page-subtitle">{data?.results?.length ?? 0} classes configured</p>
        </div>
        <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
          Add Class
        </Button>
      </div>

      <div className="card">
        <Table
          columns={columns as any}
          data={data?.results ?? []}
          keyExtractor={(c) => c.id}
          loading={isLoading}
          emptyMessage="No classes yet. Add your first class."
        />
      </div>

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Edit Class" : "Add Class"} size="sm">
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
          <Input label="Class Name" required placeholder="e.g. Grade 1 or JSS 1A" {...register("name", { required: true })} />
          <Input label="Short Name" placeholder="e.g. G1" {...register("short_name")} />
          <Input label="Level" type="number" placeholder="1" {...register("level", { valueAsNumber: true })} />
          <Input label="Capacity" type="number" placeholder="30" {...register("capacity", { valueAsNumber: true })} />
          <Input label="Description" placeholder="Optional description" {...register("description")} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" loading={mutation.isPending}>
              {editing ? "Update" : "Create"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
