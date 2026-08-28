"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout";
import { StatusBadge, Modal } from "@/components/ui";
import {
  Search,
  Filter,
  Download,
  Eye,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  ChevronDown,
  Brain,
  FileText,
  ArrowRight,
  Loader2,
} from "lucide-react";
import { fetchViolations, reviewViolation, generateReport } from "@/lib/api";

interface Violation {
  id: string;
  recordId: string;
  policyId: string;
  policyName: string;
  description: string;
  severity: "low" | "medium" | "high";
  confidence: number;
  timestamp: string;
  remediation: string;
  status?: string;
  explanation: {
    ruleTriggered: string;
    dataAnalyzed: string[];
    reasoning: string;
    evidence: string[];
    recommendation: string;
  };
}

export default function ViolationsPage() {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedViolation, setSelectedViolation] = useState<Violation | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [exporting, setExporting] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const pageSize = 20;

  // Stats
  const [stats, setStats] = useState({
    total: 0,
    high: 0,
    pending: 0,
    resolved: 0,
  });

  const loadViolations = async () => {
    setLoading(true);
    try {
      const data = await fetchViolations({
        severity: severityFilter !== "all" ? severityFilter : undefined,
        limit: 100,
      });

      const mapped: Violation[] = (data.violations || []).map((v: any, idx: number) => ({
        id: v.id || String(idx + 1),
        recordId: v.record_id || v.id || `REC-${idx + 1}`,
        policyId: v.rule_id || v.policy_id || "RULE",
        policyName: v.table || v.policy_name || "Compliance",
        description: v.description || v.violation_type || "Policy violation detected",
        severity: v.severity || "medium",
        confidence: v.confidence || 85,
        timestamp: v.timestamp || new Date().toISOString().replace("T", " ").slice(0, 19),
        remediation: v.remediation || v.recommendation || "Review and take corrective action",
        status: v.status || "pending",
        explanation: {
          ruleTriggered: v.rule_id || "Compliance rule triggered",
          dataAnalyzed: v.data_analyzed || [
            `Table: ${v.table || "N/A"}`,
            `Record: ${v.record_id || v.id || "N/A"}`,
            `Severity: ${v.severity || "medium"}`,
          ],
          reasoning: v.explanation || v.reasoning || "This record was flagged based on the configured compliance rules and threshold analysis.",
          evidence: v.evidence || [
            `Detection source: Automated scan`,
            `Rule: ${v.rule_id || "N/A"}`,
            `Confidence: ${v.confidence || 85}%`,
          ],
          recommendation: v.remediation || v.recommendation || "Review the flagged record and take appropriate corrective action per compliance guidelines.",
        },
      }));

      setViolations(mapped);
      setStats({
        total: data.total || mapped.length,
        high: mapped.filter(v => v.severity === "high").length,
        pending: mapped.filter(v => !v.status || v.status === "pending").length,
        resolved: mapped.filter(v => v.status === "approve" || v.status === "resolved").length,
      });
    } catch (err: any) {
      // Keep empty if API not ready
      setViolations([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadViolations();
  }, [severityFilter]);

  const filteredViolations = violations.filter((v) => {
    const matchesSearch =
      v.recordId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.policyName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const paginatedViolations = filteredViolations.slice(
    page * pageSize,
    (page + 1) * pageSize
  );

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high":
        return "danger";
      case "medium":
        return "warning";
      case "low":
        return "info";
      default:
        return "default";
    }
  };

  const handleExportReport = async () => {
    setExporting(true);
    try {
      const result = await generateReport("json", true);
      alert(`Report generated! Report ID: ${result.report_id}`);
    } catch (err: any) {
      // Fallback: export current violations as JSON
      const blob = new Blob([JSON.stringify(filteredViolations, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "violations_report.json";
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  const handleReviewAction = async (violationId: string, decision: "approve" | "reject" | "escalate") => {
    setActionLoading(decision);
    try {
      await reviewViolation(violationId, decision, "admin");
      // Update local state
      setViolations(prev =>
        prev.map(v => v.id === violationId ? { ...v, status: decision } : v)
      );
      setSelectedViolation(null);
      alert(`Violation ${decision === "reject" ? "marked as false positive" : decision === "escalate" ? "escalated" : "remediation initiated"} successfully.`);
    } catch (err: any) {
      alert("Action failed: " + err.message);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <DashboardLayout>
      {/* Page Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-dark-100">
            Violation Monitor
          </h1>
          <p className="text-dark-500 mt-1">
            Review and manage compliance violations
          </p>
        </div>
        <button
          onClick={handleExportReport}
          disabled={exporting}
          className="btn-primary inline-flex items-center space-x-2"
        >
          {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
          <span>{exporting ? "Exporting..." : "Export Report"}</span>
        </button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="card py-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-accent-danger/20">
              <AlertTriangle className="w-5 h-5 text-accent-danger" />
            </div>
            <div>
              <p className="text-2xl font-bold text-dark-100">{stats.total}</p>
              <p className="text-sm text-dark-500">Total Violations</p>
            </div>
          </div>
        </div>
        <div className="card py-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-red-500/20">
              <XCircle className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-dark-100">{stats.high}</p>
              <p className="text-sm text-dark-500">High Severity</p>
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
              <p className="text-sm text-dark-500">Pending Review</p>
            </div>
          </div>
        </div>
        <div className="card py-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-accent-success/20">
              <CheckCircle className="w-5 h-5 text-accent-success" />
            </div>
            <div>
              <p className="text-2xl font-bold text-dark-100">{stats.resolved}</p>
              <p className="text-sm text-dark-500">Resolved</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dark-500" />
            <input
              type="text"
              placeholder="Search by Record ID, Policy, or Description..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(0); }}
              className="input-field pl-10 w-full"
            />
          </div>
          <div className="flex items-center space-x-4">
            <div className="relative">
              <select
                value={severityFilter}
                onChange={(e) => { setSeverityFilter(e.target.value); setPage(0); }}
                className="input-field appearance-none pr-10"
              >
                <option value="all">All Severities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dark-500 pointer-events-none" />
            </div>
            <button onClick={loadViolations} className="btn-secondary inline-flex items-center space-x-2">
              <Filter className="w-4 h-4" />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      {/* Violations Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="w-6 h-6 text-accent-primary animate-spin" />
            <span className="ml-2 text-dark-400">Loading violations...</span>
          </div>
        ) : paginatedViolations.length === 0 ? (
          <div className="text-center py-12">
            <CheckCircle className="w-12 h-12 text-accent-success mx-auto mb-3" />
            <p className="text-dark-300 font-medium">No violations found</p>
            <p className="text-dark-500 text-sm mt-1">
              {violations.length === 0
                ? "Run a compliance scan to detect violations"
                : "No violations match your current filters"}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-dark-800">
                <tr>
                  <th className="table-header">Record ID</th>
                  <th className="table-header">Policy Violated</th>
                  <th className="table-header">Description</th>
                  <th className="table-header">Severity</th>
                  <th className="table-header">AI Confidence</th>
                  <th className="table-header">Timestamp</th>
                  <th className="table-header">Remediation</th>
                  <th className="table-header">Action</th>
                </tr>
              </thead>
              <tbody>
                {paginatedViolations.map((violation) => (
                  <tr
                    key={violation.id}
                    className="hover:bg-dark-800/50 transition-colors"
                  >
                    <td className="table-cell font-mono text-accent-primary">
                      {violation.recordId}
                    </td>
                    <td className="table-cell">
                      <div>
                        <p className="font-medium text-dark-200">
                          {violation.policyId}
                        </p>
                        <p className="text-xs text-dark-500">
                          {violation.policyName}
                        </p>
                      </div>
                    </td>
                    <td className="table-cell max-w-xs">
                      <p className="truncate">{violation.description}</p>
                    </td>
                    <td className="table-cell">
                      <StatusBadge
                        variant={getSeverityColor(violation.severity) as any}
                      >
                        {violation.severity.toUpperCase()}
                      </StatusBadge>
                    </td>
                    <td className="table-cell">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 h-2 bg-dark-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${violation.confidence >= 90
                                ? "bg-accent-success"
                                : violation.confidence >= 70
                                  ? "bg-accent-warning"
                                  : "bg-accent-danger"
                              }`}
                            style={{ width: `${violation.confidence}%` }}
                          />
                        </div>
                        <span className="text-sm text-dark-300">
                          {violation.confidence}%
                        </span>
                      </div>
                    </td>
                    <td className="table-cell text-dark-400 text-sm">
                      {violation.timestamp}
                    </td>
                    <td className="table-cell max-w-xs">
                      <p className="text-sm text-dark-400 truncate">
                        {violation.remediation}
                      </p>
                    </td>
                    <td className="table-cell">
                      <button
                        onClick={() => setSelectedViolation(violation)}
                        className="btn-secondary py-1.5 px-3 text-sm inline-flex items-center space-x-1"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Explain</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-dark-700">
          <p className="text-sm text-dark-500">
            Showing {paginatedViolations.length} of {filteredViolations.length}{" "}
            violations
          </p>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="btn-secondary py-1.5 px-3 text-sm disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={(page + 1) * pageSize >= filteredViolations.length}
              className="btn-secondary py-1.5 px-3 text-sm disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Explanation Modal */}
      <Modal
        isOpen={!!selectedViolation}
        onClose={() => setSelectedViolation(null)}
        title="AI Violation Explanation"
        size="lg"
      >
        {selectedViolation && (
          <div className="space-y-6">
            {/* Header Info */}
            <div className="flex items-start justify-between pb-4 border-b border-dark-700">
              <div>
                <div className="flex items-center space-x-3 mb-2">
                  <span className="font-mono text-lg text-accent-primary">
                    {selectedViolation.recordId}
                  </span>
                  <StatusBadge
                    variant={
                      getSeverityColor(selectedViolation.severity) as any
                    }
                  >
                    {selectedViolation.severity.toUpperCase()} SEVERITY
                  </StatusBadge>
                </div>
                <p className="text-dark-400">
                  {selectedViolation.policyName} ({selectedViolation.policyId})
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-dark-500">AI Confidence</p>
                <p className="text-2xl font-bold text-dark-100">
                  {selectedViolation.confidence}%
                </p>
              </div>
            </div>

            {/* Rule Triggered */}
            <div className="bg-dark-800 rounded-lg p-4 border-l-4 border-accent-primary">
              <div className="flex items-center space-x-2 mb-2">
                <FileText className="w-4 h-4 text-accent-primary" />
                <h4 className="font-medium text-dark-200">Rule Triggered</h4>
              </div>
              <p className="text-dark-300">
                {selectedViolation.explanation.ruleTriggered}
              </p>
            </div>

            {/* Data Analyzed */}
            <div>
              <h4 className="font-medium text-dark-200 mb-3">
                Data Points Analyzed
              </h4>
              <div className="grid grid-cols-2 gap-2">
                {selectedViolation.explanation.dataAnalyzed.map(
                  (data, index) => (
                    <div
                      key={index}
                      className="bg-dark-800 rounded-lg px-3 py-2 text-sm text-dark-300"
                    >
                      {data}
                    </div>
                  ),
                )}
              </div>
            </div>

            {/* AI Reasoning */}
            <div>
              <div className="flex items-center space-x-2 mb-3">
                <Brain className="w-4 h-4 text-accent-info" />
                <h4 className="font-medium text-dark-200">AI Reasoning</h4>
              </div>
              <p className="text-dark-400 leading-relaxed">
                {selectedViolation.explanation.reasoning}
              </p>
            </div>

            {/* Evidence */}
            <div>
              <h4 className="font-medium text-dark-200 mb-3">
                Supporting Evidence
              </h4>
              <ul className="space-y-2">
                {selectedViolation.explanation.evidence.map(
                  (evidence, index) => (
                    <li
                      key={index}
                      className="flex items-start space-x-2 text-sm text-dark-400"
                    >
                      <ArrowRight className="w-4 h-4 text-dark-500 mt-0.5 flex-shrink-0" />
                      <span>{evidence}</span>
                    </li>
                  ),
                )}
              </ul>
            </div>

            {/* Recommendation */}
            <div className="bg-accent-success/10 border border-accent-success/30 rounded-lg p-4">
              <h4 className="font-medium text-accent-success mb-2">
                Recommended Action
              </h4>
              <p className="text-dark-300">
                {selectedViolation.explanation.recommendation}
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-dark-700">
              <button
                onClick={() => handleReviewAction(selectedViolation.id, "reject")}
                disabled={!!actionLoading}
                className="btn-secondary inline-flex items-center space-x-2"
              >
                {actionLoading === "reject" && <Loader2 className="w-4 h-4 animate-spin" />}
                <span>Mark as False Positive</span>
              </button>
              <button
                onClick={() => handleReviewAction(selectedViolation.id, "escalate")}
                disabled={!!actionLoading}
                className="btn-secondary inline-flex items-center space-x-2"
              >
                {actionLoading === "escalate" && <Loader2 className="w-4 h-4 animate-spin" />}
                <span>Escalate</span>
              </button>
              <button
                onClick={() => handleReviewAction(selectedViolation.id, "approve")}
                disabled={!!actionLoading}
                className="btn-primary inline-flex items-center space-x-2"
              >
                {actionLoading === "approve" && <Loader2 className="w-4 h-4 animate-spin" />}
                <span>Initiate Remediation</span>
              </button>
            </div>
          </div>
        )}
      </Modal>
    </DashboardLayout>
  );
}
