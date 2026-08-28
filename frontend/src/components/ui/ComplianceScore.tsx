"use client";

import React from "react";
import { TrendingUp, CheckCircle, AlertTriangle } from "lucide-react";

interface ComplianceScoreProps {
  score: number;
  lastUpdated: string;
}

export default function ComplianceScore({
  score,
  lastUpdated,
}: ComplianceScoreProps) {
  const circumference = 2 * Math.PI * 88;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const getScoreColor = () => {
    if (score >= 90) return "#22c55e";
    if (score >= 70) return "#f59e0b";
    return "#ef4444";
  };

  const getScoreStatus = () => {
    if (score >= 90)
      return {
        text: "Excellent",
        icon: CheckCircle,
        color: "text-accent-success",
      };
    if (score >= 70)
      return {
        text: "Good",
        icon: AlertTriangle,
        color: "text-accent-warning",
      };
    return {
      text: "Needs Attention",
      icon: AlertTriangle,
      color: "text-accent-danger",
    };
  };

  const status = getScoreStatus();

  return (
    <div className="card col-span-2 row-span-2 flex flex-col items-center justify-center py-8">
      <h3 className="text-sm font-medium text-dark-400 uppercase tracking-wider mb-6">
        Compliance Health Score
      </h3>

      {/* Circular Progress */}
      <div className="relative w-52 h-52">
        <svg className="transform -rotate-90 w-full h-full">
          {/* Background circle */}
          <circle
            cx="104"
            cy="104"
            r="88"
            stroke="#40414f"
            strokeWidth="12"
            fill="none"
          />
          {/* Progress circle */}
          <circle
            cx="104"
            cy="104"
            r="88"
            stroke={getScoreColor()}
            strokeWidth="12"
            fill="none"
            strokeLinecap="round"
            style={{
              strokeDasharray: circumference,
              strokeDashoffset: strokeDashoffset,
              transition: "stroke-dashoffset 1s ease-out",
            }}
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-5xl font-bold text-dark-100">{score}</span>
          <span className="text-lg text-dark-400">%</span>
        </div>
      </div>

      {/* Status */}
      <div className={`flex items-center space-x-2 mt-6 ${status.color}`}>
        <status.icon className="w-5 h-5" />
        <span className="font-medium">{status.text}</span>
      </div>

      {/* Trend indicator */}
      <div className="flex items-center space-x-2 mt-3">
        <TrendingUp className="w-4 h-4 text-accent-success" />
        <span className="text-sm text-accent-success">+2.3%</span>
        <span className="text-sm text-dark-500">from last month</span>
      </div>

      {/* Last updated */}
      <p className="text-xs text-dark-500 mt-4">Last updated: {lastUpdated}</p>
    </div>
  );
}
