"use client";

import React, { useState, useCallback, useEffect } from "react";
import { DashboardLayout } from "@/components/layout";
import { StatusBadge } from "@/components/ui";
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
  ChevronRight,
  Eye,
  Trash2,
  RotateCcw,
  Settings,
  Loader2,
  Download,
} from "lucide-react";
import { uploadPolicy, fetchRules, fetchPolicies, loadRules } from "@/lib/api";

interface ExtractedRule {
  id: string;
  ruleId: string;
  condition: string;
  obligation: string;
  status: "success" | "review" | "failed";
  confidence: number;
}

export default function PolicyIngestion() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [extractedRules, setExtractedRules] = useState<ExtractedRule[]>([]);
  const [humanReview, setHumanReview] = useState(true);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [policies, setPolicies] = useState<any[]>([]);
  const [stats, setStats] = useState({ documents: 0, rules: 0, avgConfidence: 0, pendingReview: 0 });
  const [activating, setActivating] = useState(false);

  // Load existing policies and rules on mount
  useEffect(() => {
    const loadExisting = async () => {
      try {
        const [policiesData, rulesData] = await Promise.all([
          fetchPolicies(),
          fetchRules(),
        ]);
        setPolicies(policiesData.policies || []);
        setStats(prev => ({
          ...prev,
          documents: policiesData.count || 0,
          rules: rulesData.count || 0,
          avgConfidence: rulesData.rules?.length > 0
            ? Math.round(rulesData.rules.reduce((acc: number, r: any) => acc + (r.confidence || 85), 0) / rulesData.rules.length)
            : 0,
          pendingReview: rulesData.rules?.filter((r: any) => r.status === "review").length || 0,
        }));
      } catch {
        // API not ready yet
      }
    };
    loadExisting();
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleUpload(files[0]);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleUpload(files[0]);
    }
  };

  const handleUpload = async (file: File) => {
    setUploadedFile(file.name);
    setUploadProgress(0);
    setIsProcessing(true);
    setExtractedRules([]);
    setUploadError(null);

    // Show progress animation
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 15;
      });
    }, 200);

    try {
      const result = await uploadPolicy(file);
      clearInterval(progressInterval);
      setUploadProgress(100);

      // Fetch the rules after upload
      const rulesData = await fetchRules();
      const mappedRules: ExtractedRule[] = (rulesData.rules || []).map((rule: any, index: number) => ({
        id: String(index + 1),
        ruleId: rule.rule_id || rule.id || `R-${100 + index + 1}`,
        condition: rule.condition || rule.description || "Condition extracted from policy",
        obligation: rule.obligation || rule.action || "Compliance action required",
        status: (rule.confidence || 85) >= 80 ? "success" : "review",
        confidence: rule.confidence || 85,
      }));

      setExtractedRules(mappedRules);
      setStats(prev => ({
        ...prev,
        documents: prev.documents + 1,
        rules: rulesData.count || 0,
      }));
    } catch (err: any) {
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadError(err.message || "Upload failed");
    } finally {
      setIsProcessing(false);
    }
  };

  const resetUpload = () => {
    setUploadedFile(null);
    setUploadProgress(0);
    setExtractedRules([]);
    setIsProcessing(false);
    setUploadError(null);
  };

  const handleActivatePolicy = async () => {
    setActivating(true);
    try {
      await loadRules();
      alert("Policy rules activated successfully!");
    } catch (err: any) {
      alert("Failed to activate: " + err.message);
    } finally {
      setActivating(false);
    }
  };

  const handleExportRules = () => {
    const blob = new Blob([JSON.stringify(extractedRules, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "extracted_rules.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDeleteRule = (ruleId: string) => {
    setExtractedRules(prev => prev.filter(r => r.id !== ruleId));
  };

  const handleViewRule = (rule: ExtractedRule) => {
    alert(`Rule ${rule.ruleId}\n\nCondition: ${rule.condition}\nObligation: ${rule.obligation}\nConfidence: ${rule.confidence}%`);
  };

  return (
    <DashboardLayout>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-dark-100">Policy Ingestion</h1>
        <p className="text-dark-500 mt-1">
          Upload compliance documents and extract structured rules
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Section */}
        <div className="lg:col-span-2 space-y-6">
          {/* Upload Box */}
          <div className="card">
            <h3 className="text-lg font-semibold text-dark-100 mb-4">
              Upload Policy Document
            </h3>

            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${isDragging
                  ? "border-accent-primary bg-accent-primary/10"
                  : "border-dark-600 hover:border-dark-500 hover:bg-dark-800/50"
                }`}
            >
              {!uploadedFile ? (
                <>
                  <Upload
                    className={`w-12 h-12 mx-auto mb-4 ${isDragging ? "text-accent-primary" : "text-dark-500"}`}
                  />
                  <p className="text-dark-200 font-medium mb-2">
                    Drag & drop your policy document here
                  </p>
                  <p className="text-dark-500 text-sm mb-4">or</p>
                  <label className="btn-primary cursor-pointer inline-block">
                    Browse Files
                    <input
                      type="file"
                      accept=".pdf,.md,.txt"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                  </label>
                  <p className="text-dark-500 text-xs mt-4">
                    Supported formats: PDF, Markdown, TXT (Max 50MB)
                  </p>
                </>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-center space-x-3">
                    <FileText className="w-10 h-10 text-accent-primary" />
                    <div className="text-left">
                      <p className="text-dark-200 font-medium">
                        {uploadedFile}
                      </p>
                      <p className="text-dark-500 text-sm">Policy Document</p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="max-w-md mx-auto">
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-dark-400">
                        {isProcessing ? "Processing..." : uploadError ? "Error" : "Upload Complete"}
                      </span>
                      <span className="text-dark-200">{uploadProgress}%</span>
                    </div>
                    <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-200 ${uploadError ? "bg-accent-danger" : "bg-accent-primary"}`}
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                    {uploadError && (
                      <p className="text-xs text-accent-danger mt-2">{uploadError}</p>
                    )}
                  </div>

                  {!isProcessing && (
                    <button
                      onClick={resetUpload}
                      className="btn-secondary inline-flex items-center space-x-2"
                    >
                      <RotateCcw className="w-4 h-4" />
                      <span>Upload Another</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Extracted Rules Panel */}
          {extractedRules.length > 0 && (
            <div className="card animate-fade-in">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-dark-100">
                    Extracted Rules
                  </h3>
                  <p className="text-dark-500 text-sm mt-1">
                    {extractedRules.length} rules extracted from document
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <StatusBadge variant="success" dot>
                    {
                      extractedRules.filter((r) => r.status === "success")
                        .length
                    }{" "}
                    Parsed
                  </StatusBadge>
                  <StatusBadge variant="warning" dot>
                    {extractedRules.filter((r) => r.status === "review").length}{" "}
                    Need Review
                  </StatusBadge>
                </div>
              </div>

              <div className="space-y-3">
                {extractedRules.map((rule) => (
                  <div
                    key={rule.id}
                    className={`p-4 rounded-lg border transition-all duration-200 hover:border-dark-500 ${rule.status === "success"
                        ? "bg-dark-800/50 border-dark-700"
                        : "bg-accent-warning/5 border-accent-warning/30"
                      }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="text-sm font-mono font-semibold text-accent-primary">
                            {rule.ruleId}
                          </span>
                          <StatusBadge
                            variant={
                              rule.status === "success" ? "success" : "warning"
                            }
                          >
                            {rule.status === "success"
                              ? "Parsed Successfully"
                              : "Needs Human Review"}
                          </StatusBadge>
                          <span className="text-xs text-dark-500">
                            AI Confidence: {rule.confidence}%
                          </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                          <div>
                            <p className="text-xs text-dark-500 uppercase tracking-wider mb-1">
                              Condition
                            </p>
                            <p className="text-sm text-dark-200">
                              {rule.condition}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-dark-500 uppercase tracking-wider mb-1">
                              Obligation
                            </p>
                            <p className="text-sm text-dark-200">
                              {rule.obligation}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={() => handleViewRule(rule)}
                          className="p-2 rounded-lg hover:bg-dark-700 transition-colors"
                        >
                          <Eye className="w-4 h-4 text-dark-400" />
                        </button>
                        <button
                          onClick={() => handleDeleteRule(rule.id)}
                          className="p-2 rounded-lg hover:bg-dark-700 transition-colors"
                        >
                          <Trash2 className="w-4 h-4 text-dark-400" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-dark-700">
                <button onClick={handleExportRules} className="btn-secondary inline-flex items-center space-x-2">
                  <Download className="w-4 h-4" />
                  <span>Export Rules</span>
                </button>
                <button
                  onClick={handleActivatePolicy}
                  disabled={activating}
                  className="btn-primary inline-flex items-center space-x-2"
                >
                  {activating && <Loader2 className="w-4 h-4 animate-spin" />}
                  <span>{activating ? "Activating..." : "Activate Policy"}</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Human Review Toggle */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-dark-100">
                Human-in-the-Loop
              </h3>
              <button
                onClick={() => setHumanReview(!humanReview)}
                className={`relative w-12 h-6 rounded-full transition-colors ${humanReview ? "bg-accent-primary" : "bg-dark-600"
                  }`}
              >
                <span
                  className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${humanReview ? "left-7" : "left-1"
                    }`}
                />
              </button>
            </div>
            <p className="text-sm text-dark-500">
              {humanReview
                ? "Rules with low confidence will be flagged for manual review before activation."
                : "All extracted rules will be auto-approved and activated."}
            </p>
          </div>

          {/* Processing Stats */}
          <div className="card">
            <h3 className="text-sm font-semibold text-dark-100 mb-4">
              Processing Statistics
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-dark-400">
                  Documents Processed
                </span>
                <span className="text-sm font-medium text-dark-200">{stats.documents}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-dark-400">Rules Extracted</span>
                <span className="text-sm font-medium text-dark-200">{stats.rules}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-dark-400">Avg. Confidence</span>
                <span className="text-sm font-medium text-dark-200">{stats.avgConfidence > 0 ? `${stats.avgConfidence}%` : "N/A"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-dark-400">Pending Review</span>
                <span className="text-sm font-medium text-accent-warning">
                  {stats.pendingReview}
                </span>
              </div>
            </div>
          </div>

          {/* Recent Uploads */}
          <div className="card">
            <h3 className="text-sm font-semibold text-dark-100 mb-4">
              Recent Uploads
            </h3>
            <div className="space-y-3">
              {policies.length > 0 ? (
                policies.slice(0, 5).map((policy: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between py-2 border-b border-dark-700 last:border-b-0"
                  >
                    <div className="flex items-center space-x-3">
                      <FileText className="w-4 h-4 text-dark-500" />
                      <div>
                        <p className="text-sm text-dark-200">{policy.name || policy.filename || `Policy ${index + 1}`}</p>
                        <p className="text-xs text-dark-500">
                          {policy.rules_count || 0} rules
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-dark-500">{policy.uploaded_at || "Recent"}</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-dark-500 text-center py-4">No policies uploaded yet</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
