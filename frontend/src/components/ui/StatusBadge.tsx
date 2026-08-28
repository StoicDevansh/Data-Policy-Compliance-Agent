"use client";

import React from "react";

type BadgeVariant = "success" | "warning" | "danger" | "info" | "default";

interface StatusBadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  success: "bg-green-500/20 text-green-400 border-green-500/30",
  warning: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  danger: "bg-red-500/20 text-red-400 border-red-500/30",
  info: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  default: "bg-dark-600/20 text-dark-300 border-dark-500/30",
};

const dotStyles: Record<BadgeVariant, string> = {
  success: "bg-green-400",
  warning: "bg-yellow-400",
  danger: "bg-red-400",
  info: "bg-cyan-400",
  default: "bg-dark-400",
};

export default function StatusBadge({
  variant,
  children,
  dot = false,
}: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${variantStyles[variant]}`}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full mr-1.5 ${dotStyles[variant]}`}
        ></span>
      )}
      {children}
    </span>
  );
}
