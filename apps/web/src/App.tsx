import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { useAuthStore } from "@/store/authStore";

// Pages
import { LoginPage } from "@/pages/auth/LoginPage";
import { DashboardPage } from "@/pages/dashboard/DashboardPage";
import { StudentsPage } from "@/pages/students/StudentsPage";
import { StudentRegistrationPage } from "@/pages/students/StudentRegistrationPage";
import { StudentProfilePage } from "@/pages/students/StudentProfilePage";
import { ClassesPage } from "@/pages/classes/ClassesPage";
import { AcademicYearsPage } from "@/pages/academic-years/AcademicYearsPage";
import { FeeCategoriesPage } from "@/pages/fees/FeeCategoriesPage";
import { FeeTemplatesPage } from "@/pages/fees/FeeTemplatesPage";
import { StudentChargesPage } from "@/pages/fees/StudentChargesPage";
import { PaymentsPage } from "@/pages/payments/PaymentsPage";
import { RecordPaymentPage } from "@/pages/payments/RecordPaymentPage";
import { PaymentVerificationPage } from "@/pages/payments/PaymentVerificationPage";
import { ReceiptsPage } from "@/pages/receipts/ReceiptsPage";
import { ReportsPage } from "@/pages/reports/ReportsPage";
import { ExportsPage } from "@/pages/reports/ExportsPage";
import { StaffPage } from "@/pages/staff/StaffPage";
import { AuditLogsPage } from "@/pages/audit/AuditLogsPage";
import { SettingsPage } from "@/pages/settings/SettingsPage";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function RedirectIfAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          <RedirectIfAuth>
            <LoginPage />
          </RedirectIfAuth>
        }
      />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />

        {/* Students */}
        <Route path="students" element={<StudentsPage />} />
        <Route path="students/register" element={<StudentRegistrationPage />} />
        <Route path="students/:id" element={<StudentProfilePage />} />

        {/* Academics */}
        <Route path="classes" element={<ClassesPage />} />
        <Route path="academic-years" element={<AcademicYearsPage />} />

        {/* Fees */}
        <Route path="fees/categories" element={<FeeCategoriesPage />} />
        <Route path="fees/templates" element={<FeeTemplatesPage />} />
        <Route path="fees/student-charges" element={<StudentChargesPage />} />

        {/* Payments */}
        <Route path="payments" element={<PaymentsPage />} />
        <Route path="payments/record" element={<RecordPaymentPage />} />
        <Route path="payment-verification" element={<PaymentVerificationPage />} />

        {/* Receipts */}
        <Route path="receipts" element={<ReceiptsPage />} />

        {/* Reports */}
        <Route path="reports" element={<ReportsPage />} />
        <Route path="exports" element={<ExportsPage />} />

        {/* Administration */}
        <Route path="staff" element={<StaffPage />} />
        <Route path="audit" element={<AuditLogsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
