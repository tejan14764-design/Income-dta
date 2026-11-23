import React from "react";
import { clsx } from "clsx";

type BadgeVariant = "success" | "warning" | "error" | "info" | "purple" | "gray";

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variantMap: Record<BadgeVariant, string> = {
  success: "badge-success",
  warning: "badge-warning",
  error: "badge-error",
  info: "badge-info",
  purple: "badge-purple",
  gray: "badge-gray",
};

export function Badge({ variant = "gray", children, className }: BadgeProps) {
  return (
    <span className={clsx(variantMap[variant], className)}>
      {children}
    </span>
  );
}

// Payment status badge helper
export function PaymentStatusBadge({ status }: { status: string }) {
  const map: Record<string, { variant: BadgeVariant; label: string }> = {
    confirmed: { variant: "success", label: "Confirmed" },
    pending: { variant: "warning", label: "Pending" },
    rejected: { variant: "error", label: "Rejected" },
    reversed: { variant: "gray", label: "Reversed" },
    refunded: { variant: "info", label: "Refunded" },
    fully_paid: { variant: "success", label: "Fully Paid" },
    partially_paid: { variant: "warning", label: "Partial" },
    unpaid: { variant: "error", label: "Unpaid" },
    overdue: { variant: "error", label: "Overdue" },
    pending_verification: { variant: "purple", label: "Pending" },
  };

  const config = map[status] ?? { variant: "gray" as BadgeVariant, label: status };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
