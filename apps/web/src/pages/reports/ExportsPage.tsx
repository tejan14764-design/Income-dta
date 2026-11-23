import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, FileText } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { api, getApiBaseUrl } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import type { AcademicYear, Class } from "@/types";

export function ExportsPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id ?? "";
  const [academicYear, setAcademicYear] = useState("");
  const [classId, setClassId] = useState("");

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

  const years = (yearsData?.results ?? []).map((y) => ({ value: y.id, label: y.name }));
  const classes = [
    { value: "", label: "All Classes" },
    ...(classesData?.results ?? []).map((c) => ({ value: c.id, label: c.name })),
  ];

  const buildUrl = (type: string) => {
    if (!academicYear) return "#";
    const params = new URLSearchParams({ school: schoolId, academic_year: academicYear, type });
    if (classId) params.append("class_id", classId);
    return `${getApiBaseUrl()}/reports/export/csv/?${params}`;
  };

  const exports = [
    { title: "Financial Summary", desc: "Student-by-student fee and payment summary", type: "financial_summary", filename: "financial-summary.csv" },
    { title: "Outstanding Fees", desc: "Students with outstanding balances only", type: "outstanding", filename: "outstanding-fees.csv" },
    { title: "Fully Paid Students", desc: "Students who have completed all payments", type: "fully_paid", filename: "fully-paid.csv" },
  ];

  return (
    <div className="space-y-5">
      <div className="page-header">
        <div>
          <h1 className="page-title">CSV Exports</h1>
          <p className="page-subtitle">Download financial data for analysis</p>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="font-semibold mb-4">Export Settings</h3>
        <div className="flex flex-col sm:flex-row gap-3">
          <Select label="Academic Year" options={years} placeholder="Select year"
            value={academicYear} onChange={(e) => setAcademicYear(e.target.value)} />
          <Select label="Class (optional)" options={classes}
            value={classId} onChange={(e) => setClassId(e.target.value)} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {exports.map((exp) => (
          <div key={exp.type} className="card p-5 flex flex-col gap-4">
            <div className="flex items-start gap-3">
              <FileText className="h-6 w-6 text-secondary flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-text-primary">{exp.title}</p>
                <p className="text-sm text-text-muted mt-0.5">{exp.desc}</p>
              </div>
            </div>
            <a
              href={buildUrl(exp.type)}
              download={exp.filename}
              className={!academicYear ? "pointer-events-none opacity-50" : ""}
              aria-disabled={!academicYear}
            >
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                leftIcon={<Download className="h-3.5 w-3.5" />}
                disabled={!academicYear}
              >
                Download CSV
              </Button>
            </a>
          </div>
        ))}
      </div>

      {!academicYear && (
        <p className="text-sm text-text-muted text-center py-4">
          Select an academic year above to enable exports.
        </p>
      )}
    </div>
  );
}
