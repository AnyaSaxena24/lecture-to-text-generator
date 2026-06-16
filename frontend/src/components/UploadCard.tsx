"use client";

import React, { useState, useRef } from "react";
import { Upload, FileAudio, Loader2, Sparkles } from "lucide-react";

interface UploadCardProps {
  onUpload: (file: File) => Promise<void>;
  uploading: boolean;
  error?: string;
}

export default function UploadCard({ onUpload, uploading, error }: UploadCardProps) {
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      triggerUpload(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      triggerUpload(e.target.files[0]);
    }
  };

  const triggerUpload = async (file: File) => {
    // Simulate upload progress bar loading
    setProgress(10);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 15;
      });
    }, 200);

    try {
      await onUpload(file);
      setProgress(100);
    } catch (err) {
      setProgress(0);
    } finally {
      clearInterval(interval);
    }
  };

  return (
    <div className="glass rounded-2xl p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <span>AI Study Builder</span>
          <Sparkles className="h-5 w-5 text-brand-400 animate-pulse" />
        </h3>
      </div>

      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition relative overflow-hidden group ${
          dragActive ? "border-brand-500 bg-brand-500/5" : "border-slate-800 hover:border-brand-500/50 bg-slate-900/10 hover:bg-slate-900/20"
        } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleChange}
          accept="audio/*,video/*"
          className="hidden"
        />

        {uploading ? (
          <div className="space-y-4 w-full max-w-[200px]">
            <Loader2 className="h-10 w-10 text-brand-500 animate-spin mx-auto" />
            <p className="text-sm font-semibold text-white">Uploading Lecture...</p>
            {/* Progress Bar */}
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-brand-500 to-violet-500 transition-all duration-300 rounded-full"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-[10px] text-slate-500">{progress}% Completed</p>
          </div>
        ) : (
          <>
            <div className="mb-4 rounded-xl bg-slate-800 p-4 text-slate-400 group-hover:text-brand-400 group-hover:bg-brand-500/10 transition duration-200">
              <Upload className="h-6 w-6" />
            </div>
            <p className="text-sm font-bold text-white">Drag and drop lecture audio or video</p>
            <p className="text-xs text-slate-400 mt-2">
              Supports MP3, WAV, M4A, MP4 up to 100MB
            </p>
          </>
        )}
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-3.5 text-xs font-semibold text-red-400">
          {error}
        </div>
      )}
    </div>
  );
}
