"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const data = [
  { name: "AML-001", violations: 145, policy: "Anti Money Laundering" },
  { name: "KYC-003", violations: 98, policy: "Know Your Customer" },
  { name: "PCI-DSS", violations: 76, policy: "Payment Card Security" },
  { name: "GDPR-012", violations: 62, policy: "Data Privacy" },
  { name: "SOX-005", violations: 54, policy: "Financial Reporting" },
  { name: "HIPAA-002", violations: 43, policy: "Health Data Protection" },
  { name: "RBI-007", violations: 45, policy: "Reserve Bank Guidelines" },
];

const getBarColor = (violations: number) => {
  if (violations >= 100) return "#ef4444";
  if (violations >= 60) return "#f59e0b";
  return "#3b82f6";
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const item = payload[0].payload;
    return (
      <div className="bg-dark-800 border border-dark-600 rounded-lg p-3 shadow-xl">
        <p className="text-dark-200 font-medium">{label}</p>
        <p className="text-xs text-dark-500 mb-2">{item.policy}</p>
        <p className="text-sm text-accent-danger">
          {item.violations} violations
        </p>
      </div>
    );
  }
  return null;
};

export default function PolicyViolationsChart() {
  return (
    <div className="card h-[400px]">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-dark-100">
          Violations by Policy
        </h3>
        <p className="text-sm text-dark-500">Top policy violations breakdown</p>
      </div>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#40414f"
            horizontal={false}
          />
          <XAxis
            type="number"
            stroke="#8e8ea0"
            fontSize={12}
            tickLine={false}
            axisLine={{ stroke: "#40414f" }}
          />
          <YAxis
            dataKey="name"
            type="category"
            stroke="#8e8ea0"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            width={70}
          />
          <Tooltip
            content={<CustomTooltip />}
            cursor={{ fill: "rgba(255,255,255,0.05)" }}
          />
          <Bar dataKey="violations" radius={[0, 4, 4, 0]} barSize={24}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getBarColor(entry.violations)}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
