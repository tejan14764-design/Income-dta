import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Users, GraduationCap, DollarSign, TrendingUp,
  Clock, CheckCircle, XCircle, AlertCircle,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import type { DashboardData } from "@/types";
import { PaymentStatusBadge } from "@/components/ui/Badge";

const PAYMENT_STATUS_COLORS: Record<string, string> = {
  fully_paid: "#059669",
  partially_paid: "#d97706",
  unpaid: "#dc2626",
  overdue: "#7c3aed",
};

function StatCard({
  title, value, subtitle, icon, color,
}: {
  title: string; value: string | number; subtitle?: string;
  icon: React.ReactNode; color: string;
}) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}>{icon}</div>
      <div>
        <p className="text-text-muted text-xs font-medium">{title}</p>
        <p className="text-2xl font-bold text-text-primary mt-0.5">{value}</p>
        {subtitle && <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { activeSchool } = useAuthStore();
  const schoolId = activeSchool?.school_id;

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", schoolId],
    queryFn: () =>
      api.get<{ success: boolean; data: DashboardData }>(`/dashboard/?school=${schoolId}`),
    enabled: !!schoolId,
    refetchInterval: 60_000, // Refresh every minute
  });

  const dashboard = data?.data;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="page-header">
          <div>
            <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
            <div className="h-4 bg-gray-200 rounded w-72 mt-2 animate-pulse" />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-20 bg-gray-100 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const statusDist = dashboard?.charge_status_distribution ?? {};
  const pieData = Object.entries(statusDist)
    .filter(([, count]) => (count as number) > 0)
    .map(([status, count]) => ({
      name: status.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase()),
      value: count as number,
      color: PAYMENT_STATUS_COLORS[status] ?? "#94a3b8",
    }));

  const monthlyData = (dashboard?.monthly_collection ?? []).map((m) => ({
    month: new Date(m.month).toLocaleDateString("en", { month: "short", year: "2-digit" }),
    amount: parseFloat(m.total),
  }));

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">
            {activeSchool?.school_name} — Overview
          </p>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Students"
          value={dashboard?.total_students ?? 0}
          subtitle={`${dashboard?.total_students_all ?? 0} total`}
          icon={<Users className="h-6 w-6 text-blue-600" />}
          color="bg-blue-50"
        />
        <StatCard
          title="Classes"
          value={dashboard?.total_classes ?? 0}
          icon={<GraduationCap className="h-6 w-6 text-purple-600" />}
          color="bg-purple-50"
        />
        <StatCard
          title="Total Expected"
          value={`NLe ${Number(dashboard?.total_expected ?? 0).toLocaleString()}`}
          icon={<DollarSign className="h-6 w-6 text-emerald-600" />}
          color="bg-emerald-50"
        />
        <StatCard
          title="Confirmed Payments"
          value={`NLe ${Number(dashboard?.total_confirmed_payments ?? 0).toLocaleString()}`}
          icon={<CheckCircle className="h-6 w-6 text-green-600" />}
          color="bg-green-50"
        />
        <StatCard
          title="Outstanding"
          value={`NLe ${Number(dashboard?.total_outstanding ?? 0).toLocaleString()}`}
          icon={<AlertCircle className="h-6 w-6 text-amber-600" />}
          color="bg-amber-50"
        />
        <StatCard
          title="Pending Verification"
          value={dashboard?.pending_verification_count ?? 0}
          subtitle="Awaiting officer review"
          icon={<Clock className="h-6 w-6 text-orange-600" />}
          color="bg-orange-50"
        />
        <StatCard
          title="Fully Paid"
          value={statusDist["fully_paid"] ?? 0}
          icon={<CheckCircle className="h-6 w-6 text-teal-600" />}
          color="bg-teal-50"
        />
        <StatCard
          title="Unpaid"
          value={statusDist["unpaid"] ?? 0}
          icon={<XCircle className="h-6 w-6 text-red-600" />}
          color="bg-red-50"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly collection */}
        <div className="lg:col-span-2 card p-6">
          <h3 className="font-semibold text-text-primary mb-4">Monthly Payment Collection</h3>
          {monthlyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={monthlyData} margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false}
                  tickFormatter={(v) => `NLe ${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  formatter={(v: number) => [`NLe ${v.toLocaleString()}`, "Collected"]}
                  contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}
                />
                <Bar dataKey="amount" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-text-muted text-sm">
              No payment data yet
            </div>
          )}
        </div>

        {/* Payment status pie */}
        <div className="card p-6">
          <h3 className="font-semibold text-text-primary mb-4">Fee Payment Status</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v: number) => [v, "Students"]}
                  contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}
                />
                <Legend
                  iconType="circle"
                  iconSize={8}
                  wrapperStyle={{ fontSize: 11 }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-text-muted text-sm">
              No data yet
            </div>
          )}
        </div>
      </div>

      {/* Recent transactions */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <h3 className="font-semibold text-text-primary">Recent Transactions</h3>
          <Link to="/payments" className="text-sm text-secondary hover:underline">View all</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Amount</th>
                <th>Method</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {(dashboard?.recent_transactions ?? []).length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-text-muted">
                    No transactions yet
                  </td>
                </tr>
              ) : (
                dashboard?.recent_transactions.map((t) => (
                  <tr key={t.id}>
                    <td className="font-medium">{t.student_name}</td>
                    <td>NLe {Number(t.amount).toLocaleString()}</td>
                    <td className="capitalize">{t.method.replace("_", " ")}</td>
                    <td><PaymentStatusBadge status={t.status} /></td>
                    <td className="text-text-muted">{t.date}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
