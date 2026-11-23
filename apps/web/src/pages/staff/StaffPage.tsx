import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Plus, Shield, Users, UserX } from "lucide-react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { Table } from "@/components/ui/Table";
import { api, getErrorMessage } from "@/services/api";
import { useAuthStore } from "@/store/authStore";

interface MembershipRow {
  id: string;
  user: string;
  user_name: string;
  school: string;
  school_name: string;
  role: string;
  role_name: string;
  is_active: boolean;
  joined_at: string;
}

interface RoleRow {
  id: string;
  name: string;
  slug: string;
  description: string;
  is_active: boolean;
  is_system_role: boolean;
  permissions: { id: string; codename: string; name: string; module: string }[];
}

interface PermissionRow {
  id: string;
  codename: string;
  name: string;
  module: string;
  description: string;
}

interface StaffForm {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  confirm_password: string;
  role: string;
}

interface RoleForm {
  name: string;
  slug: string;
  description: string;
}

export function StaffPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState<"staff" | "roles">("staff");
  const [modalOpen, setModalOpen] = useState(false);
  const [roleModalOpen, setRoleModalOpen] = useState(false);
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);

  const { data: membershipsData, isLoading } = useQuery({
    queryKey: ["memberships", schoolId],
    queryFn: () =>
      api.get<{ results: MembershipRow[] }>(`/users/memberships/?school_id=${schoolId}&page_size=100`),
    enabled: !!schoolId,
  });

  const { data: rolesData } = useQuery({
    queryKey: ["roles", schoolId],
    queryFn: () => api.get<{ results: RoleRow[] }>(`/users/roles/?school_id=${schoolId}&page_size=50`),
    enabled: !!schoolId,
  });

  const { data: permissionsData } = useQuery({
    queryKey: ["permissions"],
    queryFn: () => api.get<{ results: PermissionRow[] }>(`/users/permissions/?page_size=200`),
    enabled: !!schoolId && roleModalOpen,
  });

  const staffForm = useForm<StaffForm>();
  const roleForm = useForm<RoleForm>();

  const createMutation = useMutation({
    mutationFn: async (d: StaffForm) => {
      const user = await api.post<{ id: string }>("/users/", {
        username: d.username,
        email: d.email,
        first_name: d.first_name,
        last_name: d.last_name,
        password: d.password,
        confirm_password: d.confirm_password,
      }, { params: { school_id: schoolId } });
      await api.post("/users/memberships/", { user: user.id, school: schoolId, role: d.role });
      return user;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["memberships"] });
      toast.success("Staff member added.");
      setModalOpen(false);
      staffForm.reset();
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const createRoleMutation = useMutation({
    mutationFn: (d: RoleForm) =>
      api.post<RoleRow>("/users/roles/", {
        school: schoolId,
        name: d.name,
        slug: d.slug || undefined,
        description: d.description,
        permission_ids: selectedPermissions,
      }, { params: { school_id: schoolId } }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["roles"] });
      toast.success("Role created.");
      setRoleModalOpen(false);
      roleForm.reset();
      setSelectedPermissions([]);
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => api.post(`/users/memberships/${id}/deactivate/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["memberships"] });
      toast.success("Membership deactivated.");
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const roles = (rolesData?.results ?? []).map((r) => ({ value: r.id, label: r.name }));
  const permissions = permissionsData?.results ?? [];
  const permissionGroups = React.useMemo(() => {
    const groups = new Map<string, PermissionRow[]>();
    permissions.forEach((permission) => {
      const list = groups.get(permission.module) ?? [];
      list.push(permission);
      groups.set(permission.module, list);
    });
    return Array.from(groups.entries()).map(([module, items]) => ({ module, items }));
  }, [permissions]);

  const togglePermission = (permissionId: string) => {
    setSelectedPermissions((current) =>
      current.includes(permissionId)
        ? current.filter((id) => id !== permissionId)
        : [...current, permissionId]
    );
  };

  const openRoleModal = () => {
    roleForm.reset();
    setSelectedPermissions([]);
    setRoleModalOpen(true);
  };

  const membershipColumns = [
    { key: "user_name", header: "Name", render: (v: unknown) => <span className="font-medium">{String(v)}</span> },
    { key: "role_name", header: "Role" },
    {
      key: "is_active", header: "Status",
      render: (v: unknown) => <Badge variant={v ? "success" : "gray"}>{v ? "Active" : "Inactive"}</Badge>,
    },
    {
      key: "joined_at", header: "Joined",
      render: (v: unknown) => new Date(String(v)).toLocaleDateString(),
    },
    {
      key: "id", header: "", width: "80px",
      render: (_: unknown, row: MembershipRow) =>
        row.is_active ? (
          <Button variant="ghost" size="sm" onClick={() => { if (confirm("Deactivate this membership?")) deactivateMutation.mutate(row.id); }}>
            <UserX className="h-3.5 w-3.5" />
          </Button>
        ) : null,
    },
  ];

  const roleColumns = [
    { key: "name", header: "Role", render: (v: unknown) => <span className="font-medium">{String(v)}</span> },
    { key: "slug", header: "Slug", render: (v: unknown) => <span className="font-mono text-sm text-primary">{String(v)}</span> },
    {
      key: "permissions", header: "Permissions",
      render: (v: unknown) => <span className="text-sm text-text-secondary">{Array.isArray(v) ? v.length : 0}</span>,
    },
    {
      key: "is_system_role", header: "Type",
      render: (v: unknown) => <Badge variant={v ? "info" : "gray"}>{v ? "System" : "Custom"}</Badge>,
    },
    {
      key: "is_active", header: "Status",
      render: (v: unknown) => <Badge variant={v ? "success" : "gray"}>{v ? "Active" : "Inactive"}</Badge>,
    },
  ];

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Staff & Permissions</h1>
          <p className="page-subtitle">Manage school staff accounts and roles</p>
        </div>
        {activeTab === "staff" ? (
          <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />} onClick={() => { staffForm.reset(); setModalOpen(true); }}>
            Add Staff
          </Button>
        ) : (
          <Button variant="primary" leftIcon={<Plus className="h-4 w-4" />} onClick={openRoleModal}>
            Add Role
          </Button>
        )}
      </div>

      <div className="flex border-b border-surface-border">
        <button
          type="button"
          onClick={() => setActiveTab("staff")}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "staff" ? "border-primary text-primary" : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          <Users className="h-4 w-4" /> Staff
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("roles")}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "roles" ? "border-primary text-primary" : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          <Shield className="h-4 w-4" /> Roles
        </button>
      </div>

      {activeTab === "staff" && (
        <div className="card">
          <Table
            columns={membershipColumns as any}
            data={membershipsData?.results ?? []}
            keyExtractor={(m) => m.id}
            loading={isLoading}
            emptyMessage="No staff members yet."
          />
        </div>
      )}

      {activeTab === "roles" && (
        <div className="card">
          <Table
            columns={roleColumns as any}
            data={rolesData?.results ?? []}
            keyExtractor={(r) => r.id}
            loading={!rolesData}
            emptyMessage="No roles yet. Create a role before adding staff."
          />
        </div>
      )}

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Add Staff Member" size="md">
        <form onSubmit={staffForm.handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="First Name" required {...staffForm.register("first_name", { required: true })} />
            <Input label="Last Name" required {...staffForm.register("last_name", { required: true })} />
            <Input label="Username" required {...staffForm.register("username", { required: true })} />
            <Input label="Email" type="email" required {...staffForm.register("email", { required: true })} />
            <Input label="Password" type="password" required {...staffForm.register("password", { required: true })} />
            <Input label="Confirm Password" type="password" required {...staffForm.register("confirm_password", { required: true })} />
          </div>
          <div>
            <Select label="Role" required options={roles} placeholder="Select role" {...staffForm.register("role", { required: true })} />
            {roles.length === 0 && (
              <p className="mt-1 text-xs text-text-muted">No roles yet — open the Roles tab to create one.</p>
            )}
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" loading={createMutation.isPending}>Add Staff</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={roleModalOpen} onClose={() => setRoleModalOpen(false)} title="Add Role" size="lg">
        <form onSubmit={roleForm.handleSubmit((d) => createRoleMutation.mutate(d))} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Role Name" required placeholder="e.g. Accounts Clerk" {...roleForm.register("name", { required: true })} />
            <Input label="Slug" placeholder="Auto-generated if empty" {...roleForm.register("slug")} />
          </div>
          <div>
            <label className="form-label">Description</label>
            <textarea className="form-input resize-none" rows={2} placeholder="What this role can do..." {...roleForm.register("description")} />
          </div>

          <div>
            <label className="form-label">Permissions</label>
            <div className="max-h-56 overflow-y-auto rounded-lg border border-surface-border p-3 space-y-4">
              {permissionGroups.length === 0 ? (
                <p className="text-sm text-text-muted">Loading permissions...</p>
              ) : (
                permissionGroups.map((group) => (
                  <div key={group.module}>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">{group.module}</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {group.items.map((permission) => (
                        <label key={permission.id} className="flex items-start gap-2 text-sm">
                          <input
                            type="checkbox"
                            className="mt-1 h-4 w-4 rounded border-surface-border text-primary"
                            checked={selectedPermissions.includes(permission.id)}
                            onChange={() => togglePermission(permission.id)}
                          />
                          <span>
                            <span className="font-medium text-text-primary">{permission.name}</span>
                            <span className="block text-xs text-text-muted">{permission.codename}</span>
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" type="button" onClick={() => setRoleModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" loading={createRoleMutation.isPending}>Create Role</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
