"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import UploadCard from "@/components/UploadCard";
import { 
  FileAudio, FileVideo, Clock, CheckCircle, 
  AlertCircle, Trash2, ArrowRight, Loader2, Sparkles 
} from "lucide-react";

interface Lecture {
  id: string;
  title: string;
  file_name: string;
  file_size: number;
  status: "pending" | "transcribing" | "generating" | "completed" | "failed";
  error_message?: string;
  created_at: string;
}

export default function Dashboard() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const showUploadAction = searchParams.get("action") === "upload";
  const filterCompleted = searchParams.get("filter") === "completed";
  
  const [lectures, setLectures] = useState<Lecture[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  // Fetch lectures list
  const fetchLectures = async (showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      const data = await api.get<Lecture[]>("/api/lectures");
      setLectures(data);
    } catch (err) {
      console.error("Failed to load lectures:", err);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/login");
      return;
    }
    fetchLectures(true);
  }, [user, authLoading]);

  // Status Polling for in-progress lectures
  useEffect(() => {
    const hasActiveTask = lectures.some(
      (l) => l.status === "pending" || l.status === "transcribing" || l.status === "generating"
    );
    if (!hasActiveTask) return;

    const interval = setInterval(() => {
      fetchLectures(false);
    }, 4000);

    return () => clearInterval(interval);
  }, [lectures]);

  const handleUploadFile = async (file: File) => {
    setUploading(true);
    setUploadError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      await api.post<Lecture>("/api/lectures/upload", formData);
      fetchLectures(false);
      // Redirect to main dashboard view
      router.push("/dashboard");
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload file. Please try again.");
      throw err;
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this lecture?")) return;

    try {
      await api.delete(`/api/lectures/${id}`);
      setLectures((prev) => prev.filter((l) => l.id !== id));
    } catch (err) {
      alert("Failed to delete lecture");
    }
  };

  const formatSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, { 
      month: "short", 
      day: "numeric", 
      year: "numeric"
    });
  };

  if (authLoading || (user && loading)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
        <Loader2 className="h-10 w-10 text-brand-500 animate-spin" />
        <p className="text-slate-400 text-sm">Loading your dashboard...</p>
      </div>
    );
  }

  if (!user) return null;

  // Filter lectures based on URL query state
  const displayedLectures = filterCompleted 
    ? lectures.filter(l => l.status === "completed")
    : lectures;

  return (
    <div className="flex flex-1 -m-8 min-h-[calc(100vh-76px)]">
      {/* Collapsible Sidebar */}
      <Sidebar lectures={lectures} />

      {/* Main Panel Content */}
      <div className="flex-1 p-8 overflow-y-auto space-y-8">
        {/* Header Banner */}
        <div className="flex items-center justify-between border-b border-dark-border pb-6">
          <div>
            <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
              <span>Student Workspace</span>
              <Sparkles className="h-5.5 w-5.5 text-brand-400" />
            </h1>
            <p className="text-slate-500 text-xs mt-1">Review lecture summaries, transcripts, and quizzes.</p>
          </div>
        </div>

        {/* Upload Form view OR Dashboard View */}
        {showUploadAction ? (
          <div className="max-w-2xl">
            <UploadCard 
              onUpload={handleUploadFile} 
              uploading={uploading} 
              error={uploadError} 
            />
          </div>
        ) : (
          <div className="grid gap-8 lg:grid-cols-3">
            {/* Left side list of lectures */}
            <div className="lg:col-span-2 space-y-4">
              <h3 className="text-lg font-bold text-white">
                {filterCompleted ? "Study History" : "Your Materials"}
              </h3>

              {displayedLectures.length === 0 ? (
                <div className="glass rounded-2xl p-12 text-center text-slate-500">
                  <FileAudio className="h-10 w-10 mx-auto text-slate-700 mb-3" />
                  <p className="text-sm font-semibold text-slate-300">No lectures found</p>
                  <p className="text-xs mt-1">Upload a lecture to start generating notes.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {displayedLectures.map((lecture) => {
                    const isProcessing = ["pending", "transcribing", "generating"].includes(lecture.status);
                    const hasFailed = lecture.status === "failed";
                    
                    return (
                      <div
                        key={lecture.id}
                        onClick={() => !isProcessing && !hasFailed && router.push(`/lectures/${lecture.id}`)}
                        className={`glass rounded-2xl p-5 flex items-center justify-between gap-4 transition duration-150 border-l-4 ${
                          isProcessing 
                            ? "border-l-yellow-500 cursor-wait bg-yellow-500/5"
                            : hasFailed
                            ? "border-l-red-500 cursor-default"
                            : "border-l-brand-500 hover:border-brand-500/50 hover:bg-slate-900/20 cursor-pointer"
                        }`}
                      >
                        <div className="flex-1 min-w-0 space-y-1">
                          <div className="flex items-center gap-2">
                            {lecture.file_name.endsWith(".mp4") ? (
                              <FileVideo className="h-4.5 w-4.5 text-slate-400 flex-shrink-0" />
                            ) : (
                              <FileAudio className="h-4.5 w-4.5 text-slate-400 flex-shrink-0" />
                            )}
                            <h4 className="text-sm font-bold text-white truncate">{lecture.title}</h4>
                          </div>
                          
                          <div className="flex items-center gap-4 text-[10px] text-slate-500">
                            <span className="flex items-center gap-1">
                              <Clock className="h-3.5 w-3.5" />
                              {formatDate(lecture.created_at)}
                            </span>
                            <span>{formatSize(lecture.file_size)}</span>
                          </div>
                        </div>

                        {/* Status Label */}
                        <div className="flex items-center gap-3">
                          {lecture.status === "pending" && (
                            <span className="flex items-center gap-1.5 rounded-full bg-yellow-500/10 px-2.5 py-0.5 text-[10px] font-bold text-yellow-500">
                              <Loader2 className="h-3 w-3 animate-spin" />
                              Queued
                            </span>
                          )}
                          {lecture.status === "transcribing" && (
                            <span className="flex items-center gap-1.5 rounded-full bg-blue-500/10 px-2.5 py-0.5 text-[10px] font-bold text-blue-400">
                              <Loader2 className="h-3 w-3 animate-spin" />
                              Whisper
                            </span>
                          )}
                          {lecture.status === "generating" && (
                            <span className="flex items-center gap-1.5 rounded-full bg-purple-500/10 px-2.5 py-0.5 text-[10px] font-bold text-purple-400">
                              <Loader2 className="h-3 w-3 animate-spin" />
                              Phi-3 Notes
                            </span>
                          )}
                          {lecture.status === "completed" && (
                            <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-bold text-emerald-400">
                              <CheckCircle className="h-3.5 w-3.5" />
                              Ready
                            </span>
                          )}
                          {lecture.status === "failed" && (
                            <span className="flex items-center gap-1 rounded-full bg-red-500/10 px-2.5 py-0.5 text-[10px] font-bold text-red-400">
                              <AlertCircle className="h-3.5 w-3.5" />
                              Failed
                            </span>
                          )}

                          <button
                            onClick={(e) => handleDelete(lecture.id, e)}
                            className="rounded-lg p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>

                          {lecture.status === "completed" && (
                            <ArrowRight className="h-4 w-4 text-slate-400 hidden sm:block" />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Quick Upload widget right side */}
            <div className="lg:col-span-1">
              <UploadCard 
                onUpload={handleUploadFile} 
                uploading={uploading} 
                error={uploadError} 
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
