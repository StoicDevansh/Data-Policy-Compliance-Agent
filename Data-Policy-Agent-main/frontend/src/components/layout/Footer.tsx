"use client";

import React from "react";

export default function Footer() {
  return (
    <footer className="fixed bottom-0 left-64 right-0 bg-dark-950 border-t border-dark-700 py-3 px-6 z-40">
      <div className="flex items-center justify-between text-xs text-dark-500">
        <span>
          Built by Team{" "}
          <span className="text-dark-300 font-medium">BeyondInfinity</span> |
          HackFest 2.0
        </span>
        <div className="flex items-center space-x-4">
          <span>v1.0.0</span>
          <span>•</span>
          <span>Data Policy Agent</span>
        </div>
      </div>
    </footer>
  );
}
