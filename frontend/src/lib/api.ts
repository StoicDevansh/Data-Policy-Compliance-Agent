/**
 * Centralized API client for Data Policy Agent backend.
 * All API calls go through /api/* which is proxied to the FastAPI backend.
 */

const API_BASE = "/api";

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const { headers: optHeaders, ...restOptions } = options;
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...restOptions,
    headers: {
      "Content-Type": "application/json",
      ...optHeaders,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

// ======================== Dashboard ========================

export interface DashboardData {
  total_violations: number;
  high_severity: number;
  medium_severity: number;
  low_severity: number;
  compliance_score: number;
  policies_count: number;
  rules_count: number;
  connected_databases: string[];
  recent_violations: any[];
  severity_distribution: Record<string, number>;
}

export async function fetchDashboard(): Promise<DashboardData> {
  return request<DashboardData>("/dashboard");
}

export async function fetchHealth(): Promise<{ status: string; timestamp: string }> {
  return request("/health");
}

// ======================== Policies ========================

export interface PolicyResult {
  success: boolean;
  policy: any;
  rules_extracted: number;
}

export async function uploadPolicy(file: File): Promise<PolicyResult> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/policies`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Upload failed: ${res.status}`);
  }

  return res.json();
}

export async function fetchPolicies(): Promise<{ policies: any[]; count: number }> {
  return request("/policies");
}

export async function fetchRules(): Promise<{ rules: any[]; count: number }> {
  return request("/rules");
}

export async function loadRules(ruleset?: string): Promise<{
  success: boolean;
  rules_loaded: number;
  total_rules: number;
}> {
  const params = ruleset ? `?ruleset=${ruleset}` : "";
  return request(`/rules/load${params}`, { method: "POST" });
}

// ======================== Database ========================

export async function setupDemoDatabase(): Promise<{
  success: boolean;
  message: string;
  database_path: string;
  tables: string[];
  rules_loaded: number;
}> {
  return request("/database/demo", { method: "POST" });
}

export async function connectDatabase(config: {
  type: string;
  host?: string;
  port?: number;
  name: string;
  user?: string;
  password?: string;
}): Promise<{ success: boolean; message: string; database: string }> {
  return request("/database/connect", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export async function fetchTables(): Promise<{ tables: string[] }> {
  return request("/database/tables");
}

// ======================== Scan & Violations ========================

export async function runScan(options?: {
  tables?: string[];
  rules?: string[];
  limit?: number;
}): Promise<{
  success: boolean;
  violations_found: number;
  violations: any[];
}> {
  return request("/scan", {
    method: "POST",
    body: JSON.stringify(options || {}),
  });
}

export async function fetchViolations(filters?: {
  severity?: string;
  table?: string;
  status?: string;
  limit?: number;
}): Promise<{
  violations: any[];
  total: number;
  filtered: number;
}> {
  const params = new URLSearchParams();
  if (filters?.severity && filters.severity !== "all")
    params.set("severity", filters.severity);
  if (filters?.table) params.set("table", filters.table);
  if (filters?.status) params.set("status", filters.status);
  if (filters?.limit) params.set("limit", String(filters.limit));

  const qs = params.toString();
  return request(`/violations${qs ? `?${qs}` : ""}`);
}

export async function reviewViolation(
  violationId: string,
  decision: "approve" | "reject" | "escalate",
  reviewer: string = "admin",
  comments?: string
): Promise<{ success: boolean; violation_id: string; new_status: string }> {
  return request(`/violations/${violationId}/review`, {
    method: "POST",
    body: JSON.stringify({
      violation_ids: [violationId],
      decision,
      reviewer,
      comments,
    }),
  });
}

// ======================== Reports ========================

export async function generateReport(
  format: string = "json",
  includeDetails: boolean = true
): Promise<{
  success: boolean;
  report_id: string;
  format: string;
  path: string;
}> {
  return request("/reports", {
    method: "POST",
    body: JSON.stringify({ format, include_details: includeDetails }),
  });
}

export async function downloadReport(reportId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/reports/${reportId}`);
  if (!res.ok) throw new Error("Report not found");
  return res.blob();
}

// ======================== Datasets ========================

export async function fetchDatasets(): Promise<{ datasets: any[] }> {
  return request("/datasets");
}

export async function analyzeAML(): Promise<any> {
  return request("/analyze/aml", { method: "POST" });
}

export async function analyzePaySim(): Promise<any> {
  return request("/analyze/paysim", { method: "POST" });
}
