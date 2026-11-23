import React from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { ChevronLeft, Save } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { studentsService } from "@/services/students.service";
import { useAuthStore } from "@/store/authStore";
import { getErrorMessage } from "@/services/api";
import { api } from "@/services/api";
import type { AcademicYear, Class } from "@/types";

const registrationSchema = z.object({
  admission_number: z.string().min(1, "Admission number is required"),
  first_name: z.string().min(1, "First name is required"),
  middle_name: z.string().optional(),
  last_name: z.string().min(1, "Last name is required"),
  gender: z.enum(["male", "female", "other"]),
  date_of_birth: z.string().min(1, "Date of birth is required"),
  residential_address: z.string().optional(),
  admission_date: z.string().min(1, "Admission date is required"),
  status: z.string().default("active"),
  notes: z.string().optional(),
});

type RegistrationForm = z.infer<typeof registrationSchema>;

export function StudentRegistrationPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";

  const { data: yearsData } = useQuery({
    queryKey: ["academic-years", schoolId],
    queryFn: () => api.get<{ results: AcademicYear[] }>(`/academic-years/?school=${schoolId}`),
    enabled: !!schoolId,
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegistrationForm>({
    resolver: zodResolver(registrationSchema),
    defaultValues: {
      status: "active",
      admission_date: new Date().toISOString().split("T")[0],
    },
  });

  const mutation = useMutation({
    mutationFn: (data: RegistrationForm) => {
      const formData = new FormData();
      formData.append("school", schoolId);
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          formData.append(key, String(value));
        }
      });
      return studentsService.create(formData);
    },
    onSuccess: (student) => {
      queryClient.invalidateQueries({ queryKey: ["students"] });
      toast.success(`${student.full_name} registered successfully!`);
      navigate(`/students/${student.id}`);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      <div className="page-header">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary mb-2"
          >
            <ChevronLeft className="h-4 w-4" />
            Back to Students
          </button>
          <h1 className="page-title">Register New Student</h1>
        </div>
      </div>

      <form onSubmit={handleSubmit((data) => mutation.mutate(data))} noValidate>
        <div className="space-y-6">
          {/* Personal Information */}
          <div className="card">
            <div className="card-header">
              <h3>Personal Information</h3>
            </div>
            <div className="card-body grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Admission Number"
                placeholder="e.g. STU-2024-001"
                required
                error={errors.admission_number?.message}
                {...register("admission_number")}
              />
              <div /> {/* spacer */}
              <Input
                label="First Name"
                placeholder="First name"
                required
                error={errors.first_name?.message}
                {...register("first_name")}
              />
              <Input
                label="Middle Name"
                placeholder="Middle name (optional)"
                error={errors.middle_name?.message}
                {...register("middle_name")}
              />
              <Input
                label="Last Name"
                placeholder="Last name"
                required
                error={errors.last_name?.message}
                {...register("last_name")}
              />
              <Select
                label="Gender"
                required
                error={errors.gender?.message}
                options={[
                  { value: "male", label: "Male" },
                  { value: "female", label: "Female" },
                  { value: "other", label: "Other" },
                ]}
                placeholder="Select gender"
                {...register("gender")}
              />
              <Input
                label="Date of Birth"
                type="date"
                required
                error={errors.date_of_birth?.message}
                {...register("date_of_birth")}
              />
              <Input
                label="Residential Address"
                placeholder="Home address"
                error={errors.residential_address?.message}
                {...register("residential_address")}
              />
            </div>
          </div>

          {/* Admission Information */}
          <div className="card">
            <div className="card-header">
              <h3>Admission Information</h3>
            </div>
            <div className="card-body grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Admission Date"
                type="date"
                required
                error={errors.admission_date?.message}
                {...register("admission_date")}
              />
              <Select
                label="Status"
                options={[
                  { value: "active", label: "Active" },
                  { value: "inactive", label: "Inactive" },
                ]}
                {...register("status")}
              />
              <div className="md:col-span-2">
                <label className="form-label">Notes</label>
                <textarea
                  className="form-input resize-none"
                  rows={3}
                  placeholder="Additional notes (optional)"
                  {...register("notes")}
                />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <Button variant="outline" type="button" onClick={() => navigate(-1)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              type="submit"
              loading={mutation.isPending}
              leftIcon={<Save className="h-4 w-4" />}
            >
              Register Student
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
