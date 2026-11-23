import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Save, School, Bell, Printer } from "lucide-react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { getErrorMessage } from "@/services/api";
import type { School as SchoolType, SchoolSettings } from "@/types";

export function SettingsPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState<"school" | "receipts">("school");

  const { data: schoolData } = useQuery({
    queryKey: ["school", schoolId],
    queryFn: () => api.get<SchoolType>(`/schools/${schoolId}/`),
    enabled: !!schoolId,
  });

  const { data: settingsData } = useQuery({
    queryKey: ["school-settings", schoolId],
    queryFn: () => api.get<SchoolSettings>(`/schools/${schoolId}/settings/`),
    enabled: !!schoolId,
  });

  const schoolForm = useForm<Partial<SchoolType>>();
  const settingsForm = useForm<Partial<SchoolSettings>>();

  React.useEffect(() => {
    if (schoolData) schoolForm.reset(schoolData);
  }, [schoolData]);

  React.useEffect(() => {
    if (settingsData) settingsForm.reset(settingsData);
  }, [settingsData]);

  const schoolMutation = useMutation({
    mutationFn: (d: Partial<SchoolType>) => api.patch(`/schools/${schoolId}/`, d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["school"] }); toast.success("School details updated."); },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const settingsMutation = useMutation({
    mutationFn: (d: Partial<SchoolSettings>) => api.patch(`/schools/${schoolId}/settings/`, d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["school-settings"] }); toast.success("Settings saved."); },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const tabs = [
    { id: "school" as const, label: "School Profile", icon: <School className="h-4 w-4" /> },
    { id: "receipts" as const, label: "Receipt Settings", icon: <Printer className="h-4 w-4" /> },
  ];

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Configure your school's information and preferences</p>
        </div>
      </div>

      <div className="flex border-b border-surface-border">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id ? "border-primary text-primary" : "border-transparent text-text-secondary hover:text-text-primary"
            }`}
          >
            {tab.icon}{tab.label}
          </button>
        ))}
      </div>

      {activeTab === "school" && (
        <form onSubmit={schoolForm.handleSubmit((d) => schoolMutation.mutate(d))} className="card">
          <div className="card-header"><h3>School Information</h3></div>
          <div className="card-body grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input label="School Name" required {...schoolForm.register("name")} />
            <Input label="School Code" {...schoolForm.register("code")} />
            <Input label="Phone Number" {...schoolForm.register("phone_number")} />
            <Input label="Email" type="email" {...schoolForm.register("email")} />
            <Input label="Website" {...schoolForm.register("website")} />
            <div className="md:col-span-2">
              <label className="form-label">Address</label>
              <textarea className="form-input resize-none" rows={2} {...schoolForm.register("address")} />
            </div>
          </div>
          <div className="card-footer flex justify-end">
            <Button variant="primary" type="submit" loading={schoolMutation.isPending} leftIcon={<Save className="h-4 w-4" />}>
              Save Changes
            </Button>
          </div>
        </form>
      )}

      {activeTab === "receipts" && (
        <form onSubmit={settingsForm.handleSubmit((d) => settingsMutation.mutate(d))} className="card">
          <div className="card-header"><h3>Receipt Configuration</h3></div>
          <div className="card-body space-y-4">
            <Input label="Receipt Printer Name" placeholder="e.g. EPSON TM-T88V" {...settingsForm.register("receipt_printer_name")} />
            <Input label="Receipt Copies" type="number" min={1} max={5} {...settingsForm.register("receipt_copies", { valueAsNumber: true })} />
            <div>
              <label className="form-label">Receipt Footer Message</label>
              <textarea className="form-input resize-none" rows={3}
                placeholder="Thank you for your payment..."
                {...settingsForm.register("receipt_footer")} />
            </div>
            <Input label="Currency Symbol" placeholder="NLe" {...settingsForm.register("currency_symbol")} />
            <Input label="Currency Code" placeholder="SLL" {...settingsForm.register("currency_code")} />
          </div>
          <div className="card-footer flex justify-end">
            <Button variant="primary" type="submit" loading={settingsMutation.isPending} leftIcon={<Save className="h-4 w-4" />}>
              Save Settings
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
