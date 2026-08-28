"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout";
import { StatCard, ComplianceScore } from "@/components/ui";
import {
  ComplianceTrendChart,
  ViolationDistributionChart,
  PolicyViolationsChart,
} from "@/components/charts";
import {
  FileText,
  AlertTriangle,
  Database,
  Activity,
  Clock,
  Shield,
  Scan,
  Loader2,
} from "lucide-react";
import { fetchDashboard, setupDemoDatabase, loadRules, type DashboardData } from "@/lib/api";

export default function Dashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastScanTime, setLastScanTime] = useState<string | null>(null);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchDashboard();
      setDashboardData(data);
      setLastScanTime(new Date().toLocaleString());
    } catch (err: any) {
      // If dashboard fails, try setting up demo DB first
      try {
        await setupDemoDatabase();
        await loadRules();
        const data = await fetchDashboard();
        setDashboardData(data);
        setLastScanTime(new Date().toLocaleString());
      } catch (setupErr: any) {
        setError(setupErr.message || "Failed to load dashboard data");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const complianceScore = dashboardData?.compliance_score ?? 0;
  const totalViolations = dashboardData?.total_violations ?? 0;
  const rulesCount = dashboardData?.rules_count ?? 0;
  const connectedDbs = dashboardData?.connected_databases?.length ?? 0;
  const recentViolations = dashboardData?.recent_violations ?? [];

  // Calculate time since last scan
  const timeSinceLastScan = lastScanTime
    ? (() => {
      const diff = Date.now() - new Date(lastScanTime).getTime();
      const minutes = Math.floor(diff / 60000);
      return minutes < 1 ? "Just now" : `${minutes}m ago`;
    })()
    : "N/A";

  return (
    <DashboardLayout>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-dark-100">
          Compliance Dashboard
        </h1>
        <p className="text-dark-500 mt-1">
          Real-time compliance monitoring and analytics
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 text-accent-primary animate-spin" />
          <span className="ml-3 text-dark-400">Loading dashboard data...</span>
        </div>
      ) : error ? (
        <div className="card bg-accent-danger/10 border-accent-danger/30 p-6 text-center">
          <AlertTriangle className="w-8 h-8 text-accent-danger mx-auto mb-2" />
          <p className="text-dark-200">{error}</p>
          <button onClick={loadDashboard} className="btn-primary mt-4">Retry</button>
        </div>
      ) : (
        <>
          {/* Top Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="lg:col-span-2 lg:row-span-2">
              <ComplianceScore score={complianceScore} lastUpdated={lastScanTime || "N/A"} />
            </div>

            <StatCard
              title="Records Scanned"
              value={connectedDbs > 0 ? "Connected" : "No DB"}
              subtitle={`${connectedDbs} database(s) connected`}
              icon={Database}
              variant="primary"
            />

            <StatCard
              title="Total Violations"
              value={String(totalViolations)}
              subtitle="Across all policies"
              icon={AlertTriangle}
              trend={totalViolations > 0 ? { value: totalViolations, isPositive: false } : undefined}
              variant="danger"
            />

            <StatCard
              title="Active Rules"
              value={String(rulesCount)}
              subtitle="Monitoring enabled"
              icon={FileText}
              variant="success"
            />

            <StatCard
              title="Last Scan"
              value={timeSinceLastScan}
              subtitle={lastScanTime || "No scans yet"}
              icon={Clock}
              variant="default"
            />
          </div>

          {/* Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="card">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-accent-success/20">
                    <Activity className="w-5 h-5 text-accent-success" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-dark-200">
                      Monitoring Status
                    </p>
                    <p className="text-xs text-dark-500">Real-time scanning</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-accent-success rounded-full pulse-indicator"></span>
                  <span className="text-sm font-medium text-accent-success">
                    Active
                  </span>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-accent-primary/20">
                    <Scan className="w-5 h-5 text-accent-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-dark-200">
                      Next Scheduled Scan
                    </p>
                    <p className="text-xs text-dark-500">Automatic daily scan</p>
                  </div>
                </div>
                <span className="text-sm font-medium text-dark-200">In 4h 32m</span>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-accent-info/20">
                    <Shield className="w-5 h-5 text-accent-info" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-dark-200">
                      Policies Updated
                    </p>
                    <p className="text-xs text-dark-500">Last policy change</p>
                  </div>
                </div>
                <span className="text-sm font-medium text-dark-200">
                  {rulesCount > 0 ? "Active" : "None loaded"}
                </span>
              </div>
            </div>
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <ComplianceTrendChart />
            <ViolationDistributionChart />
          </div>

          <div className="grid grid-cols-1 gap-6">
            <PolicyViolationsChart />
          </div>

          {/* Recent Activity */}
          <div className="mt-8">
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-dark-100">
                  Recent Activity
                </h3>
                <a href="/violations" className="text-sm text-accent-primary hover:underline">
                  View All
                </a>
              </div>
              <div className="space-y-4">
                {recentViolations.length > 0 ? (
                  recentViolations.slice(0, 5).map((violation: any, index: number) => (
                    <div
                      key={violation.id || index}
                      className="flex items-center justify-between py-2 border-b border-dark-700 last:border-b-0"
                    >
                      <div className="flex items-center space-x-3">
                        <div
                          className={`w-2 h-2 rounded-full ${violation.severity === "high"
                              ? "bg-accent-danger"
                              : violation.severity === "medium"
                                ? "bg-accent-warning"
                                : "bg-accent-info"
                            }`}
                        ></div>
                        <div>
                          <p className="text-sm text-dark-200">{violation.description || violation.rule_id || "Violation detected"}</p>
                          <p className="text-xs text-dark-500">{violation.table || violation.severity || "Unknown"}</p>
                        </div>
                      </div>
                      <span className="text-xs text-dark-500">{violation.timestamp || "Recent"}</span>
                    </div>
                  ))
                ) : (
                  [
                    {
                      action: "System initialized",
                      policy: "System",
                      time: "Just now",
                      type: "info",
                    },
                    {
                      action: "Dashboard loaded",
                      policy: "System",
                      time: "Just now",
                      type: "success",
                    },
                    {
                      action: totalViolations > 0 ? `${totalViolations} violations found` : "No violations detected",
                      policy: "All Policies",
                      time: "Just now",
                      type: totalViolations > 0 ? "warning" : "success",
                    },
                  ].map((activity, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between py-2 border-b border-dark-700 last:border-b-0"
                    >
                      <div className="flex items-center space-x-3">
                        <div
                          className={`w-2 h-2 rounded-full ${activity.type === "warning"
                              ? "bg-accent-warning"
                              : activity.type === "danger"
                                ? "bg-accent-danger"
                                : activity.type === "success"
                                  ? "bg-accent-success"
                                  : "bg-accent-info"
                            }`}
                        ></div>
                        <div>
                          <p className="text-sm text-dark-200">{activity.action}</p>
                          <p className="text-xs text-dark-500">{activity.policy}</p>
                        </div>
                      </div>
                      <span className="text-xs text-dark-500">{activity.time}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </DashboardLayout>
  );
}
