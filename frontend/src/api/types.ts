export type PlanTier = "free" | "pro";

export type Driver = {
  id: string;
  name: string;
  email: string;
  email_verified: boolean;
  plan: PlanTier;
  created_at: string;
};

export type DriverToken = {
  access_token: string;
  token_type: string;
  driver: Driver;
};

export type PlanInfo = {
  plan: PlanTier;
  docx_export: boolean;
  evidence_per_session_limit: number | null;
};

export type Carrier = {
  id: string;
  name: string;
  default_rate_cents: number | null;
  created_at: string;
};

export type WorkSessionStatus = "open" | "closed";
export type PaymentStatus = "pending" | "partial" | "received";

export type WorkSession = {
  id: string;
  carrier_id: string;
  carrier_name: string;
  route_id: string | null;
  service_date: string;
  start_time: string | null;
  end_time: string | null;
  packages_assigned: number;
  exceptions_count: number;
  packages_completed: number;
  mileage: number | null;
  agreed_rate_cents: number;
  expected_gross_cents: number | null;
  status: WorkSessionStatus;
  payment_due_date: string | null;
  payment_status: PaymentStatus;
  payment_received_cents: number | null;
  payment_received_at: string | null;
  difference_cents: number | null;
  outstanding_cents: number;
  created_at: string;
  closed_at: string | null;
};

export type EvidenceKind =
  | "route_screenshot"
  | "rate_screenshot"
  | "gps_session"
  | "completion_record"
  | "settlement_statement"
  | "other";

export type Evidence = {
  id: string;
  session_id: string;
  kind: EvidenceKind;
  file_url: string;
  note: string | null;
  uploaded_at: string;
};

export type WorkReport = {
  report_number: string;
  driver_name: string;
  carrier_name: string;
  service_date: string;
  route_id: string | null;
  work_record: {
    route_started: string | null;
    route_completed: string | null;
    packages_assigned: number;
    packages_completed: number;
    exceptions: number;
    mileage: number | null;
  };
  compensation: {
    agreed_rate_cents: number;
    expected_gross_cents: number | null;
    payment_due_date: string | null;
    payment_status: PaymentStatus;
    payment_received_cents: number | null;
    payment_received_at: string | null;
    difference_cents: number | null;
  };
  supporting_records: Evidence[];
};

export type LedgerEntry = {
  session_id: string;
  carrier_name: string;
  route_id: string | null;
  service_date: string;
  expected_gross_cents: number;
  payment_received_cents: number | null;
  outstanding_cents: number;
  payment_due_date: string | null;
  payment_status: PaymentStatus;
};

export type LedgerSummary = {
  outstanding_total_cents: number;
  entries: LedgerEntry[];
};
