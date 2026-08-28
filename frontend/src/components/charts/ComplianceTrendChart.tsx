"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const data = [
  { name: "Jan", compliance: 85, violations: 15 },
  { name: "Feb", compliance: 88, violations: 12 },
  { name: "Mar", compliance: 82, violations: 18 },
  { name: "Apr", compliance: 90, violations: 10 },
  { name: "May", compliance: 92, violations: 8 },
  { name: "Jun", compliance: 94, violations: 6 },
  { name: "Jul", compliance: 91, violations: 9 },
  { name: "Aug", compliance: 93, violations: 7 },
  { name: "Sep", compliance: 95, violations: 5 },
  { name: "Oct", compliance: 94, violations: 6 },
  { name: "Nov", compliance: 96, violations: 4 },
  { name: "Dec", compliance: 94.2, violations: 5.8 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-dark-800 border border-dark-600 rounded-lg p-3 shadow-xl">
        <p className="text-dark-200 font-medium mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: {entry.value}%
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function ComplianceTrendChart() {
  return (
    <div className="card h-[400px]">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-dark-100">
          Compliance Trend
        </h3>
        <p className="text-sm text-dark-500">
          Monthly compliance rate over time
        </p>
      </div>
      <ResponsiveContainer width="100%" height="85%">
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#40414f"
            vertical={false}
          />
          <XAxis
            dataKey="name"
            stroke="#8e8ea0"
            fontSize={12}
            tickLine={false}
            axisLine={{ stroke: "#40414f" }}
          />
          <YAxis
            stroke="#8e8ea0"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            domain={[0, 100]}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: "10px" }}
            formatter={(value) => (
              <span className="text-dark-300 text-sm capitalize">{value}</span>
            )}
          />
          <Line
            type="monotone"
            dataKey="compliance"
            stroke="#22c55e"
            strokeWidth={3}
            dot={{ fill: "#22c55e", strokeWidth: 0, r: 4 }}
            activeDot={{ r: 6, fill: "#22c55e" }}
          />
          <Line
            type="monotone"
            dataKey="violations"
            stroke="#ef4444"
            strokeWidth={3}
            dot={{ fill: "#ef4444", strokeWidth: 0, r: 4 }}
            activeDot={{ r: 6, fill: "#ef4444" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
