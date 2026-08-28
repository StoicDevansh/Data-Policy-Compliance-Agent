"use client";

import React from "react";
import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  variant?: "default" | "success" | "warning" | "danger" | "primary";
}

const variantStyles = {
  default: "border-dark-700",
  success: "border-accent-success/30 bg-accent-success/5",
  warning: "border-accent-warning/30 bg-accent-warning/5",
  danger: "border-accent-danger/30 bg-accent-danger/5",
  primary: "border-accent-primary/30 bg-accent-primary/5",
};

const iconVariantStyles = {
  default: "bg-dark-700 text-dark-300",
  success: "bg-accent-success/20 text-accent-success",
  warning: "bg-accent-warning/20 text-accent-warning",
  danger: "bg-accent-danger/20 text-accent-danger",
  primary: "bg-accent-primary/20 text-accent-primary",
};

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  variant = "default",
}: StatCardProps) {
  return (
    <div className={`card animate-fade-in ${variantStyles[variant]}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="card-header">{title}</p>
          <p className="text-3xl font-bold text-dark-100 mt-1">{value}</p>
          {subtitle && <p className="text-sm text-dark-500 mt-1">{subtitle}</p>}
          {trend && (
            <div className="flex items-center mt-2 space-x-1">
              {trend.isPositive ? (
                <TrendingUp className="w-4 h-4 text-accent-success" />
              ) : (
                <TrendingDown className="w-4 h-4 text-accent-danger" />
              )}
              <span
                className={`text-sm font-medium ${trend.isPositive ? "text-accent-success" : "text-accent-danger"}`}
              >
                {trend.value}%
              </span>
              <span className="text-sm text-dark-500">vs last week</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-xl ${iconVariantStyles[variant]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}
