// ============================================================
// INCOME – TypeScript Types
// ============================================================

// ---- API Response ----
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  details?: Record<string, unknown>;
  count?: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ---- Auth ----
export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  is_active: boolean;
  must_change_password: boolean;
  date_joined: string;
}

export interface SchoolMembership {
  school_id: string;
  school_name: string;
  role_id: string;
  role_name: string;
  role_slug: string;
}

export interface AuthState {
  user: User | null;
  memberships: SchoolMembership[];
  access: string | null;
  refresh: string | null;
  activeSchool: SchoolMembership | null;
}

// ---- Schools ----
export interface School {
  id: string;
  name: string;
  code: string;
  address: string;
  phone_number: string;
  email: string;
  website: string;
  logo?: string;
  logo_url?: string;
  is_active: boolean;
  settings?: SchoolSettings;
  created_at: string;
}

export interface SchoolSettings {
  id: string;
  currency_code: string;
  currency_symbol: string;
  receipt_footer: string;
  receipt_printer_name: string;
  receipt_copies: number;
  enable_sms_notifications: boolean;
  max_payment_evidence_size_mb: number;
}

// ---- Students ----
export type StudentStatus = "active" | "inactive" | "graduated" | "transferred" | "withdrawn" | "suspended";
export type GenderType = "male" | "female" | "other";

export interface Student {
  id: string;
  school: string;
  admission_number: string;
  first_name: string;
  middle_name: string;
  last_name: string;
  full_name: string;
  gender: GenderType;
  date_of_birth: string;
  photograph?: string;
  photograph_url?: string;
  residential_address: string;
  email: string;
  admission_date: string;
  status: StudentStatus;
  notes: string;
  current_class?: string;
  current_academic_year?: string;
  guardians?: StudentGuardian[];
  created_at: string;
  updated_at: string;
}

export interface Guardian {
  id: string;
  school: string;
  first_name: string;
  last_name: string;
  full_name: string;
  gender: string;
  phone_number: string;
  alternate_phone: string;
  email: string;
  occupation: string;
  address: string;
}

export interface StudentGuardian {
  id: string;
  student: string;
  guardian: string;
  guardian_detail: Guardian;
  relationship: string;
  is_primary: boolean;
  is_emergency_contact: boolean;
  can_pickup: boolean;
}

export interface StudentConfidential {
  id: string;
  has_disability: boolean;
  disability_category: string;
  disability_details: string;
  requires_special_support: boolean;
  special_support_notes: string;
  medical_conditions: string;
  allergies: string;
  emergency_medical_notes: string;
}

// ---- Academics ----
export type AcademicYearStatus = "upcoming" | "active" | "closed" | "archived";

export interface AcademicYear {
  id: string;
  school: string;
  name: string;
  start_date: string;
  end_date: string;
  status: AcademicYearStatus;
  is_current: boolean;
  created_at: string;
}

export interface Class {
  id: string;
  school: string;
  name: string;
  short_name: string;
  level: number;
  description: string;
  capacity?: number;
  is_active: boolean;
  student_count: number;
}

export interface Enrollment {
  id: string;
  school: string;
  student: string;
  student_name: string;
  student_admission_number: string;
  academic_year: string;
  academic_year_name: string;
  class_ref: string;
  class_name: string;
  status: string;
  is_active: boolean;
  enrollment_date: string;
  end_date?: string;
}

// ---- Finance ----
export interface FeeCategory {
  id: string;
  school: string;
  name: string;
  code: string;
  description: string;
  is_active: boolean;
}

export interface FeeTemplateItem {
  id: string;
  template: string;
  category: string;
  category_name: string;
  description: string;
  amount: string;
  is_mandatory: boolean;
  due_date?: string;
  sort_order: number;
}

export interface FeeTemplate {
  id: string;
  school: string;
  academic_year: string;
  academic_year_name: string;
  target_class?: string;
  class_name?: string;
  name: string;
  description: string;
  is_active: boolean;
  items: FeeTemplateItem[];
  total_amount: string;
  created_at: string;
}

export interface StudentCharge {
  id: string;
  school: string;
  student: string;
  academic_year: string;
  category: string;
  category_name: string;
  description: string;
  base_amount: string;
  discount_amount: string;
  waiver_amount: string;
  net_amount: string;
  amount_paid: string;
  outstanding: string;
  is_mandatory: boolean;
  is_active: boolean;
  due_date?: string;
  status: string;
  created_at: string;
}

export interface StudentFeeAssignment {
  id: string;
  school: string;
  student: string;
  student_name: string;
  academic_year: string;
  academic_year_name: string;
  template?: string;
  notes: string;
  charges: StudentCharge[];
  assigned_at: string;
}

export interface FinancialSummary {
  total_expected: string;
  total_paid: string;
  outstanding: string;
  credit_balance: string;
  payment_progress: string;
  payment_status: string;
  charges: StudentCharge[];
}

// ---- Payments ----
export type PaymentMethod = "cash" | "mobile_money" | "bank_transfer" | "cheque";
export type PaymentStatus = "pending" | "confirmed" | "rejected" | "reversed" | "refunded";

export interface Payment {
  id: string;
  school: string;
  student: string;
  student_name: string;
  student_admission_number: string;
  academic_year: string;
  academic_year_name: string;
  payment_method: PaymentMethod;
  amount: string;
  payment_date: string;
  status: PaymentStatus;
  transaction_reference: string;
  bank_name: string;
  payer_name: string;
  payer_phone: string;
  notes: string;
  rejection_reason: string;
  recorded_by: string;
  recorded_by_name: string;
  verified_by?: string;
  verified_by_name?: string;
  verified_at?: string;
  allocations: PaymentAllocation[];
  evidence_files: PaymentEvidence[];
  created_at: string;
  updated_at: string;
}

export interface PaymentAllocation {
  id: string;
  payment: string;
  charge: string;
  charge_description: string;
  amount_allocated: string;
  is_reversed: boolean;
  created_at: string;
}

export interface PaymentEvidence {
  id: string;
  payment: string;
  evidence_type: string;
  file: string;
  file_url: string;
  original_filename: string;
  file_size: number;
  content_type: string;
  uploaded_at: string;
}

// ---- Receipts ----
export interface Receipt {
  id: string;
  receipt_number: string;
  student_name: string;
  student_admission_number: string;
  class_name: string;
  academic_year_name: string;
  payment_method: string;
  amount_paid: string;
  outstanding_after: string;
  fee_descriptions: Array<{ description: string; amount: string }>;
  transaction_reference: string;
  cashier_name: string;
  generated_at: string;
}

// ---- Dashboard ----
export interface DashboardData {
  total_students: number;
  total_students_all: number;
  total_classes: number;
  total_expected: string;
  total_confirmed_payments: string;
  total_outstanding: string;
  pending_verification_count: number;
  charge_status_distribution: Record<string, number>;
  recent_transactions: Array<{
    id: string;
    student_name: string;
    amount: string;
    method: string;
    status: string;
    date: string;
  }>;
  monthly_collection: Array<{ month: string; total: string }>;
}

// ---- Reports ----
export interface FinancialReportRow {
  admission_number: string;
  student_name: string;
  class: string;
  academic_year: string;
  total_expected: string;
  total_paid: string;
  outstanding: string;
  payment_status: string;
}

export interface FinancialReportSummary {
  total_students: number;
  total_expected: string;
  total_collected: string;
  total_outstanding: string;
  fully_paid: number;
  partially_paid: number;
  unpaid: number;
}

// ---- Audit ----
export interface AuditLog {
  id: string;
  school: string;
  actor: string;
  actor_name: string;
  action: string;
  object_type: string;
  object_id: string;
  object_repr: string;
  previous_data?: Record<string, unknown>;
  new_data?: Record<string, unknown>;
  extra?: Record<string, unknown>;
  ip_address?: string;
  timestamp: string;
}

// ---- UI helpers ----
export interface SelectOption {
  value: string;
  label: string;
}

export interface TableColumn<T> {
  key: keyof T | string;
  header: string;
  render?: (value: unknown, row: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
}
