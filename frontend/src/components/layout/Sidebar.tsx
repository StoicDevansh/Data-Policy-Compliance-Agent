"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  AlertTriangle,
  ClipboardList,
  Activity,
  Database,
  Shield,
  TrendingUp,
} from "lucide-react";
import { fetchDashboard, type DashboardData } from "@/lib/api";

const menuItems = [
  {
    name: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
    description: "Overview & Analytics",
  },
  {
    name: "Policy Ingestion",
    href: "/policies",
    icon: FileText,
    description: "Upload & Extract Rules",
  },
  {
    name: "Violations",
    href: "/violations",
    icon: AlertTriangle,
    description: "Monitor & Review",
  },
  {
    name: "Audit & Reports",
    href: "/audit",
    icon: ClipboardList,
    description: "Compliance Reports",
  },
  {
    name: "System Status",
    href: "/status",
    icon: Activity,
    description: "Infrastructure Health",
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [stats, setStats] = useState({
    activePolicies: "—",
    complianceRate: "—",
    connectedDBs: "—",
  });
  const [monitoring, setMonitoring] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const data: DashboardData = await fetchDashboard();
        setStats({
          activePolicies: String(data.rules_count || 0),
          complianceRate: `${(data.compliance_score || 0).toFixed(1)}%`,
          connectedDBs: String(data.connected_databases?.length || 0),
        });
      } catch {
        // Keep defaults if API not ready
      }
    };
    loadStats();
    const interval = setInterval(loadStats, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const quickStats = [
    { label: "Active Policies", value: stats.activePolicies, icon: Shield },
    { label: "Compliance Rate", value: stats.complianceRate, icon: TrendingUp },
    { label: "Connected DBs", value: stats.connectedDBs, icon: Database },
  ];

  return (
    <aside className="fixed left-0 top-16 bottom-0 w-64 bg-dark-950 border-r border-dark-700 overflow-y-auto">
      <div className="p-4 space-y-6">
        {/* Navigation */}
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${isActive
                    ? "bg-accent-primary/10 text-accent-primary border-l-2 border-accent-primary"
                    : "text-dark-400 hover:text-dark-100 hover:bg-dark-800"
                  }`}
              >
                <item.icon
                  className={`w-5 h-5 ${isActive ? "text-accent-primary" : "text-dark-500 group-hover:text-dark-300"}`}
                />
                <div>
                  <span className="text-sm font-medium block">{item.name}</span>
                  <span className="text-xs text-dark-500 block">
                    {item.description}
                  </span>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Divider */}
        <div className="border-t border-dark-700"></div>

        {/* Quick Stats */}
        <div className="space-y-3">
          <h3 className="text-xs font-medium text-dark-500 uppercase tracking-wider px-3">
            Quick Stats
          </h3>
          {quickStats.map((stat) => (
            <div
              key={stat.label}
              className="flex items-center justify-between px-3 py-2"
            >
              <div className="flex items-center space-x-2">
                <stat.icon className="w-4 h-4 text-dark-500" />
                <span className="text-sm text-dark-400">{stat.label}</span>
              </div>
              <span className="text-sm font-semibold text-dark-200">
                {stat.value}
              </span>
            </div>
          ))}
        </div>

        {/* Divider */}
        <div className="border-t border-dark-700"></div>

        {/* Monitoring Status */}
        <div className="px-3">
          <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-dark-200">
                Monitoring
              </span>
              <div className="flex items-center space-x-2">
                <span className={`w-2 h-2 rounded-full ${monitoring ? "bg-accent-success pulse-indicator" : "bg-dark-500"}`}></span>
                <span className={`text-xs ${monitoring ? "text-accent-success" : "text-dark-500"}`}>
                  {monitoring ? "Active" : "Paused"}
                </span>
              </div>
            </div>
            <p className="text-xs text-dark-500">Next scan in 4:32</p>
            <div className="mt-2 h-1 bg-dark-700 rounded-full overflow-hidden">
              <div className="h-full w-3/4 bg-accent-primary rounded-full transition-all duration-1000"></div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
