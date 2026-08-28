"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout";
import { StatusBadge } from "@/components/ui";
import {
  FileText,
  Download,
  Calendar,
  Filter,
  ChevronDown,
  FileCheck,
  Clock,
  Shield,
  RefreshCw,
  Eye,
  Printer,
  Share2,
  CheckCircle,
  AlertTriangle,
  User,
  Settings,
  Loader2,
} from "lucide-react";
import { generateReport, fetchViolations } from "@/lib/api";

interface AuditLog {
  id: string;
  timestamp: string;
  action: string;
  user: string;
  policy: string;
  details: string;
  status: "success" | "warning" | "info";
}

interface Report {
  id: string;
  name: string;
  type: string;
  generatedAt: string;
  period: string;
  status: "ready" | "generating" | "scheduled";
  size: string;
  format?: string;
}

export default function AuditPage() {
  const [dateRange, setDateRange] = useState({
    start: "2026-02-01",
    end: "2026-02-21",
  });
  const [selectedPolicy, setSelectedPolicy] = useState("all");
  const [reports, setReports] = useState<Report[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [generating, setGenerating] = useState<string | null>(null);
  const [stats, setStats] = useState({ reports: 0, events: 0, pending: 0, coverage: "100%" });
  const [loading, setLoading] = useState(true);

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const violationsData = await fetchViolations({ limit: 100 });
        const violations = violationsData.violations || [];

        // Generate audit logs from violations
        const logs: AuditLog[] = violations.slice(0, 8).map((v: any, idx: number) => ({
          id: String(idx + 1),
          timestamp: v.timestamp || new Date().toISOString().replace("T", " ").slice(0, 19),
          action: v.severity === "high" ? "Violation Detected" : v.status === "approve" ? "Violation Resolved" : "Record Scanned",
          user: "System",
          policy: v.rule_id || v.policy_id || "Compliance",
          details: v.description || "Compliance check performed",
          status: v.severity === "high" ? "warning" : v.status === "approve" ? "success" : "info",
        }));

        // Add some system logs
        logs.unshift({
          id: "sys-1",
          timestamp: new Date().toISOString().replace("T", " ").slice(0, 19),
          action: "Scan Completed",
          user: "System",
          policy: "All Policies",
          details: `${violations.length} violations detected across all policies`,
          status: "success",
        });

        setAuditLogs(logs);
        setStats({
          reports: reports.length,
          events: logs.length,
          pending: violations.filter((v: any) => !v.status || v.status === "pending").length,
          coverage: "100%",
        });
      } catch {
        // Keep defaults
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleGenerateReport = async (format: string, name: string) => {
    const reportKey = `${format}-${name}`;
    setGenerating(reportKey);
    try {
      const result = await generateReport(format, true);
      const newReport: Report = {
        id: result.report_id,
        name: name,
        type: format === "json" ? "Data Report" : format === "html" ? "HTML Report" : "PDF Report",
        generatedAt: new Date().toLocaleString(),
        period: `${dateRange.start} to ${dateRange.end}`,
        status: "ready",
        size: "—",
        format: format,
      };
      setReports(prev => [newReport, ...prev]);
      setStats(prev => ({ ...prev, reports: prev.reports + 1 }));
    } catch (err: any) {
      // Fallback: generate local JSON report
      const violationsData = await fetchViolations({ limit: 100 }).catch(() => ({ violations: [] }));
      const blob = new Blob([JSON.stringify(violationsData, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${name.toLowerCase().replace(/\s+/g, "_")}.json`;
      a.click();
      URL.revokeObjectURL(url);

      const newReport: Report = {
        id: `local-${Date.now()}`,
        name: name,
        type: "JSON Report (Local)",
        generatedAt: new Date().toLocaleString(),
        period: `${dateRange.start} to ${dateRange.end}`,
        status: "ready",
        size: `${(blob.size / 1024).toFixed(0)} KB`,
      };
      setReports(prev => [newReport, ...prev]);
    } finally {
      setGenerating(null);
    }
  };

  const handleDownloadReport = async (report: Report) => {
    try {
      const res = await fetch(`/api/reports/${report.id}`);
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${report.name.toLowerCase().replace(/\s+/g, "_")}.${report.format || "json"}`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        alert("Report file not available on server. It may have been generated locally.");
      }
    } catch {
      alert("Failed to download report.");
    }
  };

  const handleExportLogs = () => {
    const blob = new Blob([JSON.stringify(auditLogs, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "audit_logs.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleApplyFilters = () => {
    // Filter logs by date range and policy
    const filtered = auditLogs.filter(log => {
      const logDate = log.timestamp.split(" ")[0];
      const matchDate = logDate >= dateRange.start && logDate <= dateRange.end;
      const matchPolicy = selectedPolicy === "all" || log.policy.toLowerCase().includes(selectedPolicy);
      return matchDate && matchPolicy;
    });
    setAuditLogs(filtered);
  };

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const violationsData = await fetchViolations({ limit: 100 });
      const violations = violationsData.violations || [];
      const logs: AuditLog[] = violations.slice(0, 8).map((v: any, idx: number) => ({
        id: String(idx + 1),
        timestamp: v.timestamp || new Date().toISOString().replace("T", " ").slice(0, 19),
        action: v.severity === "high" ? "Violation Detected" : "Record Scanned",
        user: "System",
        policy: v.rule_id || "Compliance",
        details: v.description || "Compliance check performed",
        status: v.severity === "high" ? "warning" : "info",
      }));
      logs.unshift({
        id: "sys-refresh",
        timestamp: new Date().toISOString().replace("T", " ").slice(0, 19),
        action: "Data Refreshed",
        user: "System",
        policy: "All Policies",
        details: "Audit data refreshed from server",
        status: "success",
      });
      setAuditLogs(logs);
    } catch { } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      {/* Page Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-dark-100">Audit & Reports</h1>
          <p className="text-dark-500 mt-1">
            Compliance reports, audit logs, and justification records
          </p>
        </div>
        <button
          onClick={() => handleGenerateReport("json", "Compliance Summary Report")}
          disabled={!!generating}
          className="btn-primary inline-flex items-center space-x-2"
        >
          {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
          <span>{generating ? "Generating..." : "Generate Report"}</span>
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="card py-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-accent-primary/20">
              <FileCheck className="w-5 h-5 text-accent-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-dark-100">{stats.reports}</p>
              <p className="text-sm text-dark-500">Reports Generated</p>
            </div>
          </div>
        </div>
        <div className="card py-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-accent-success/20">
              <CheckCircle className="w-5 h-5 text-accent-success" />
            </div>
            <div>
              <p className="text-2xl font-bold text-dark-100">{stats.events}</p>
              <p className="text-sm text-dark-500">Audit Events</p>
            </div>
          </div>
        </div>
        <div className="card py-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-accent-warning/20">
              <Clock className="w-5 h-5 text-accent-warning" />
            </div>
            <div>
              <p className="text-2xl font-bold text-dark-100">{stats.pending}</p>
              <p className="text-sm text-dark-500">Pending Approvals</p>
            </div>
          </div>
        </div>
        <div className="card py-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-accent-info/20">
              <Shield className="w-5 h-5 text-accent-info" />
            </div>
            <div>
              <p className="text-2xl font-bold text-dark-100">{stats.coverage}</p>
              <p className="text-sm text-dark-500">Audit Coverage</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reports Section */}
        <div className="lg:col-span-2 space-y-6">
          {/* Filters */}
          <div className="card">
            <div className="flex flex-col md:flex-row md:items-center gap-4">
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-dark-500" />
                <input
                  type="date"
                  value={dateRange.start}
                  onChange={(e) =>
                    setDateRange({ ...dateRange, start: e.target.value })
                  }
                  className="input-field text-sm"
                />
                <span className="text-dark-500">to</span>
                <input
                  type="date"
                  value={dateRange.end}
                  onChange={(e) =>
                    setDateRange({ ...dateRange, end: e.target.value })
                  }
                  className="input-field text-sm"
                />
              </div>
              <div className="relative">
                <select
                  value={selectedPolicy}
                  onChange={(e) => setSelectedPolicy(e.target.value)}
                  className="input-field appearance-none pr-10 text-sm"
                >
                  <option value="all">All Policies</option>
                  <option value="aml">AML Policies</option>
                  <option value="kyc">KYC Policies</option>
                  <option value="pci">PCI-DSS</option>
                  <option value="gdpr">GDPR</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dark-500 pointer-events-none" />
              </div>
              <button onClick={handleApplyFilters} className="btn-secondary inline-flex items-center space-x-2">
                <Filter className="w-4 h-4" />
                <span>Apply Filters</span>
              </button>
            </div>
          </div>

          {/* Available Reports */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-dark-100">
                Available Reports
              </h3>
              <button onClick={handleRefresh} className="text-sm text-accent-primary hover:underline inline-flex items-center space-x-1">
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                <span>Refresh</span>
              </button>
            </div>

            <div className="space-y-3">
              {reports.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="w-10 h-10 text-dark-600 mx-auto mb-3" />
                  <p className="text-dark-400">No reports generated yet</p>
                  <p className="text-dark-500 text-sm mt-1">Use the sidebar buttons to generate a report</p>
                </div>
              ) : (
                reports.map((report) => (
                  <div
                    key={report.id}
                    className="flex items-center justify-between p-4 bg-dark-800/50 rounded-lg border border-dark-700 hover:border-dark-600 transition-colors"
                  >
                    <div className="flex items-center space-x-4">
                      <div
                        className={`p-2 rounded-lg ${report.status === "ready"
                            ? "bg-accent-success/20"
                            : report.status === "generating"
                              ? "bg-accent-warning/20"
                              : "bg-dark-600"
                          }`}
                      >
                        <FileText
                          className={`w-5 h-5 ${report.status === "ready"
                              ? "text-accent-success"
                              : report.status === "generating"
                                ? "text-accent-warning"
                                : "text-dark-400"
                            }`}
                        />
                      </div>
                      <div>
                        <p className="font-medium text-dark-200">{report.name}</p>
                        <div className="flex items-center space-x-3 mt-1">
                          <span className="text-xs text-dark-500">
                            {report.type}
                          </span>
                          <span className="text-xs text-dark-600">•</span>
                          <span className="text-xs text-dark-500">
                            {report.period}
                          </span>
                          {report.size !== "—" && (
                            <>
                              <span className="text-xs text-dark-600">•</span>
                              <span className="text-xs text-dark-500">
                                {report.size}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <StatusBadge
                        variant={
                          report.status === "ready"
                            ? "success"
                            : report.status === "generating"
                              ? "warning"
                              : "info"
                        }
                      >
                        {report.status === "ready"
                          ? "Ready"
                          : report.status === "generating"
                            ? "Generating..."
                            : "Scheduled"}
                      </StatusBadge>
                      {report.status === "ready" && (
                        <div className="flex items-center space-x-1">
                          <button
                            className="p-2 rounded-lg hover:bg-dark-700 transition-colors"
                            title="Preview"
                            onClick={() => alert(`Report: ${report.name}\nType: ${report.type}\nPeriod: ${report.period}`)}
                          >
                            <Eye className="w-4 h-4 text-dark-400" />
                          </button>
                          <button
                            className="p-2 rounded-lg hover:bg-dark-700 transition-colors"
                            title="Download"
                            onClick={() => handleDownloadReport(report)}
                          >
                            <Download className="w-4 h-4 text-dark-400" />
                          </button>
                          <button
                            className="p-2 rounded-lg hover:bg-dark-700 transition-colors"
                            title="Share"
                            onClick={() => {
                              navigator.clipboard.writeText(`Report: ${report.name} (ID: ${report.id})`);
                              alert("Report link copied to clipboard!");
                            }}
                          >
                            <Share2 className="w-4 h-4 text-dark-400" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Audit Log */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-dark-100">
                Audit Log History
              </h3>
              <button onClick={handleExportLogs} className="btn-secondary text-sm py-1.5 px-3">
                Export Logs
              </button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 text-accent-primary animate-spin" />
                <span className="ml-2 text-dark-400">Loading logs...</span>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-dark-800">
                    <tr>
                      <th className="table-header">Timestamp</th>
                      <th className="table-header">Action</th>
                      <th className="table-header">User</th>
                      <th className="table-header">Policy</th>
                      <th className="table-header">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map((log) => (
                      <tr
                        key={log.id}
                        className="hover:bg-dark-800/50 transition-colors"
                      >
                        <td className="table-cell text-dark-400 text-sm whitespace-nowrap">
                          {log.timestamp}
                        </td>
                        <td className="table-cell">
                          <div className="flex items-center space-x-2">
                            <div
                              className={`w-2 h-2 rounded-full ${log.status === "success"
                                  ? "bg-accent-success"
                                  : log.status === "warning"
                                    ? "bg-accent-warning"
                                    : "bg-accent-info"
                                }`}
                            ></div>
                            <span className="text-dark-200">{log.action}</span>
                          </div>
                        </td>
                        <td className="table-cell text-dark-400 text-sm">
                          {log.user}
                        </td>
                        <td className="table-cell">
                          <span className="text-accent-primary text-sm">
                            {log.policy}
                          </span>
                        </td>
                        <td className="table-cell text-dark-400 text-sm max-w-xs truncate">
                          {log.details}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Generate Report Card */}
          <div className="card bg-gradient-to-br from-accent-primary/10 to-accent-info/10 border-accent-primary/30">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 rounded-lg bg-accent-primary/20">
                <FileText className="w-5 h-5 text-accent-primary" />
              </div>
              <h3 className="font-semibold text-dark-100">
                Generate New Report
              </h3>
            </div>
            <p className="text-sm text-dark-400 mb-4">
              Create custom compliance reports with AI-powered insights and
              recommendations.
            </p>
            <div className="space-y-3">
              <button
                onClick={() => handleGenerateReport("json", "Compliance Summary")}
                disabled={!!generating}
                className="w-full btn-primary text-sm inline-flex items-center justify-center space-x-2"
              >
                {generating === "json-Compliance Summary" && <Loader2 className="w-4 h-4 animate-spin" />}
                <span>Compliance Summary</span>
              </button>
              <button
                onClick={() => handleGenerateReport("json", "Violation Report")}
                disabled={!!generating}
                className="w-full btn-secondary text-sm inline-flex items-center justify-center space-x-2"
              >
                {generating === "json-Violation Report" && <Loader2 className="w-4 h-4 animate-spin" />}
                <span>Violation Report</span>
              </button>
              <button
                onClick={() => handleGenerateReport("html", "Executive Dashboard")}
                disabled={!!generating}
                className="w-full btn-secondary text-sm inline-flex items-center justify-center space-x-2"
              >
                {generating === "html-Executive Dashboard" && <Loader2 className="w-4 h-4 animate-spin" />}
                <span>Executive Dashboard PDF</span>
              </button>
            </div>
          </div>

          {/* Justification Logs */}
          <div className="card">
            <h3 className="font-semibold text-dark-100 mb-4">
              Recent Justifications
            </h3>
            <div className="space-y-3">
              {[
                {
                  action: "False Positive Marked",
                  policy: "AML-001",
                  reason: "Verified as legitimate business transaction",
                  user: "J. Smith",
                  time: "2h ago",
                },
                {
                  action: "Exception Approved",
                  policy: "KYC-003",
                  reason: "Customer provided additional documentation",
                  user: "M. Johnson",
                  time: "5h ago",
                },
                {
                  action: "Remediation Completed",
                  policy: "PCI-DSS",
                  reason: "Encryption implemented on affected tables",
                  user: "R. Kumar",
                  time: "1d ago",
                },
              ].map((item, index) => (
                <div
                  key={index}
                  className="p-3 bg-dark-800/50 rounded-lg border border-dark-700"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-dark-200">
                      {item.action}
                    </span>
                    <span className="text-xs text-dark-500">{item.time}</span>
                  </div>
                  <p className="text-xs text-accent-primary mb-1">
                    {item.policy}
                  </p>
                  <p className="text-xs text-dark-400">{item.reason}</p>
                  <p className="text-xs text-dark-500 mt-2">By {item.user}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Scheduled Reports */}
          <div className="card">
            <h3 className="font-semibold text-dark-100 mb-4">
              Scheduled Reports
            </h3>
            <div className="space-y-3">
              {[
                {
                  name: "Daily Scan Summary",
                  schedule: "Daily at 6:00 AM",
                  next: "Tomorrow",
                },
                {
                  name: "Weekly Compliance",
                  schedule: "Mondays at 9:00 AM",
                  next: "Feb 24",
                },
                {
                  name: "Monthly Executive",
                  schedule: "1st of Month",
                  next: "Mar 1",
                },
              ].map((item, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between py-2 border-b border-dark-700 last:border-b-0"
                >
                  <div>
                    <p className="text-sm text-dark-200">{item.name}</p>
                    <p className="text-xs text-dark-500">{item.schedule}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-dark-400">Next run</p>
                    <p className="text-sm text-accent-primary">{item.next}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
