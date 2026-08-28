"use client";

import React, { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Bell,
  Settings,
  User,
  Search,
  X,
  Shield,
  FileText,
  AlertTriangle,
  Activity,
  LogOut,
  HelpCircle,
  Moon,
  Volume2,
  Database,
  Globe,
} from "lucide-react";

export default function Navbar() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);
  const settingsRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setShowNotifications(false);
      if (settingsRef.current && !settingsRef.current.contains(e.target as Node)) setShowSettings(false);
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) setShowProfile(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleSearch = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && searchQuery.trim()) {
      router.push(`/violations?search=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery("");
    }
  };

  const notifications = [
    { id: 1, type: "violation", title: "New high-severity violation detected", time: "2m ago", icon: AlertTriangle, color: "text-accent-danger" },
    { id: 2, type: "scan", title: "Compliance scan completed", time: "15m ago", icon: Shield, color: "text-accent-success" },
    { id: 3, type: "policy", title: "Policy rules loaded successfully", time: "1h ago", icon: FileText, color: "text-accent-primary" },
    { id: 4, type: "system", title: "System health check passed", time: "2h ago", icon: Activity, color: "text-accent-info" },
  ];

  const [readNotifs, setReadNotifs] = useState<number[]>([]);
  const unreadCount = notifications.filter(n => !readNotifs.includes(n.id)).length;

  const markAllRead = () => {
    setReadNotifs(notifications.map(n => n.id));
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-dark-700">
      <div className="flex items-center justify-between h-16 px-6">
        {/* Left - Team Branding */}
        <button
          onClick={() => router.push("/")}
          className="flex items-center space-x-3 hover:opacity-80 transition-opacity"
        >
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
            <span className="text-white font-bold text-lg">∞</span>
          </div>
          <div>
            <span className="text-dark-100 font-semibold text-sm">
              BeyondInfinity
            </span>
            <span className="text-dark-500 text-xs block">
              Enterprise Compliance
            </span>
          </div>
        </button>

        {/* Center - Product Name */}
        <div className="absolute left-1/2 transform -translate-x-1/2">
          <h1 className="text-xl font-semibold">
            <span className="gradient-text">Data Policy Agent</span>
          </h1>
          <p className="text-dark-500 text-xs text-center">
            Automated Compliance Monitoring
          </p>
        </div>

        {/* Right - Actions */}
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="relative hidden md:block">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dark-500" />
            <input
              type="text"
              placeholder="Search policies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearch}
              className="input-field pl-10 w-64 text-sm"
            />
          </div>

          {/* Notifications */}
          <div className="relative" ref={notifRef}>
            <button
              onClick={() => { setShowNotifications(!showNotifications); setShowSettings(false); setShowProfile(false); }}
              className="relative p-2 rounded-lg hover:bg-dark-700 transition-colors"
            >
              <Bell className="w-5 h-5 text-dark-400" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-2 h-2 bg-accent-danger rounded-full"></span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 top-12 w-80 bg-dark-800 border border-dark-600 rounded-xl shadow-2xl animate-fade-in z-50">
                <div className="flex items-center justify-between px-4 py-3 border-b border-dark-700">
                  <h3 className="text-sm font-semibold text-dark-100">Notifications</h3>
                  <button onClick={markAllRead} className="text-xs text-accent-primary hover:underline">
                    Mark all read
                  </button>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {notifications.map(notif => (
                    <div
                      key={notif.id}
                      className={`flex items-start space-x-3 px-4 py-3 hover:bg-dark-700/50 transition-colors cursor-pointer border-b border-dark-700/50 last:border-0 ${readNotifs.includes(notif.id) ? "opacity-60" : ""
                        }`}
                      onClick={() => {
                        setReadNotifs(prev => [...prev, notif.id]);
                        if (notif.type === "violation") router.push("/violations");
                        else if (notif.type === "policy") router.push("/policies");
                        else if (notif.type === "scan") router.push("/audit");
                        else router.push("/status");
                        setShowNotifications(false);
                      }}
                    >
                      <notif.icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${notif.color}`} />
                      <div>
                        <p className="text-sm text-dark-200">{notif.title}</p>
                        <p className="text-xs text-dark-500 mt-0.5">{notif.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="px-4 py-2 border-t border-dark-700">
                  <button
                    onClick={() => { router.push("/audit"); setShowNotifications(false); }}
                    className="text-xs text-accent-primary hover:underline w-full text-center"
                  >
                    View all activity →
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Settings */}
          <div className="relative" ref={settingsRef}>
            <button
              onClick={() => { setShowSettings(!showSettings); setShowNotifications(false); setShowProfile(false); }}
              className="p-2 rounded-lg hover:bg-dark-700 transition-colors"
            >
              <Settings className="w-5 h-5 text-dark-400" />
            </button>

            {showSettings && (
              <div className="absolute right-0 top-12 w-64 bg-dark-800 border border-dark-600 rounded-xl shadow-2xl animate-fade-in z-50">
                <div className="px-4 py-3 border-b border-dark-700">
                  <h3 className="text-sm font-semibold text-dark-100">Settings</h3>
                </div>
                <div className="py-1">
                  <button
                    onClick={() => { router.push("/status"); setShowSettings(false); }}
                    className="w-full flex items-center space-x-3 px-4 py-2.5 hover:bg-dark-700/50 transition-colors text-left"
                  >
                    <Database className="w-4 h-4 text-dark-400" />
                    <span className="text-sm text-dark-200">Database Connections</span>
                  </button>
                  <button
                    onClick={() => { router.push("/policies"); setShowSettings(false); }}
                    className="w-full flex items-center space-x-3 px-4 py-2.5 hover:bg-dark-700/50 transition-colors text-left"
                  >
                    <FileText className="w-4 h-4 text-dark-400" />
                    <span className="text-sm text-dark-200">Policy Management</span>
                  </button>
                  <button
                    onClick={() => { router.push("/status"); setShowSettings(false); }}
                    className="w-full flex items-center space-x-3 px-4 py-2.5 hover:bg-dark-700/50 transition-colors text-left"
                  >
                    <Globe className="w-4 h-4 text-dark-400" />
                    <span className="text-sm text-dark-200">API Configuration</span>
                  </button>
                  <div className="border-t border-dark-700 my-1"></div>
                  <div className="w-full flex items-center justify-between px-4 py-2.5">
                    <div className="flex items-center space-x-3">
                      <Moon className="w-4 h-4 text-dark-400" />
                      <span className="text-sm text-dark-200">Dark Mode</span>
                    </div>
                    <span className="text-xs text-accent-success bg-accent-success/20 px-2 py-0.5 rounded">On</span>
                  </div>
                  <div className="w-full flex items-center justify-between px-4 py-2.5">
                    <div className="flex items-center space-x-3">
                      <Volume2 className="w-4 h-4 text-dark-400" />
                      <span className="text-sm text-dark-200">Notifications</span>
                    </div>
                    <span className="text-xs text-accent-success bg-accent-success/20 px-2 py-0.5 rounded">On</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* User Profile */}
          <div className="relative" ref={profileRef}>
            <button
              onClick={() => { setShowProfile(!showProfile); setShowNotifications(false); setShowSettings(false); }}
              className="flex items-center space-x-2 p-2 rounded-lg hover:bg-dark-700 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-dark-600 flex items-center justify-center">
                <User className="w-4 h-4 text-dark-300" />
              </div>
            </button>

            {showProfile && (
              <div className="absolute right-0 top-12 w-56 bg-dark-800 border border-dark-600 rounded-xl shadow-2xl animate-fade-in z-50">
                <div className="px-4 py-3 border-b border-dark-700">
                  <p className="text-sm font-semibold text-dark-100">Admin User</p>
                  <p className="text-xs text-dark-500">admin@beyondinfinity.io</p>
                </div>
                <div className="py-1">
                  <button
                    onClick={() => { router.push("/"); setShowProfile(false); }}
                    className="w-full flex items-center space-x-3 px-4 py-2.5 hover:bg-dark-700/50 transition-colors text-left"
                  >
                    <Activity className="w-4 h-4 text-dark-400" />
                    <span className="text-sm text-dark-200">Dashboard</span>
                  </button>
                  <button
                    onClick={() => { router.push("/audit"); setShowProfile(false); }}
                    className="w-full flex items-center space-x-3 px-4 py-2.5 hover:bg-dark-700/50 transition-colors text-left"
                  >
                    <FileText className="w-4 h-4 text-dark-400" />
                    <span className="text-sm text-dark-200">My Reports</span>
                  </button>
                  <button
                    className="w-full flex items-center space-x-3 px-4 py-2.5 hover:bg-dark-700/50 transition-colors text-left"
                    onClick={() => window.open("https://github.com/Shreekant-Bharti/Data-Policy-Agent", "_blank")}
                  >
                    <HelpCircle className="w-4 h-4 text-dark-400" />
                    <span className="text-sm text-dark-200">Help & Docs</span>
                  </button>
                  <div className="border-t border-dark-700 my-1"></div>
                  <button
                    className="w-full flex items-center space-x-3 px-4 py-2.5 hover:bg-dark-700/50 transition-colors text-left"
                    onClick={() => { alert("Logged out successfully."); setShowProfile(false); }}
                  >
                    <LogOut className="w-4 h-4 text-accent-danger" />
                    <span className="text-sm text-accent-danger">Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
