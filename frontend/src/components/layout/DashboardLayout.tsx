"use client";

import React from "react";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";
import Footer from "./Footer";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-dark-950">
      <Navbar />
      <Sidebar />
      <main className="ml-64 pt-16 pb-12 min-h-screen">
        <div className="p-6">{children}</div>
      </main>
      <Footer />
    </div>
  );
}
