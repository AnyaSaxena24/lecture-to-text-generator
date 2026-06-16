"use client";

import React from "react";
import { FileText, Clock } from "lucide-react";

interface Segment {
  start: number;
  end: number;
  text: string;
}

interface TranscriptPanelProps {
  segments: Segment[];
}

export default function TranscriptPanel({ segments = [] }: TranscriptPanelProps) {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="glass rounded-2xl p-6 space-y-6">
      <div className="flex items-center gap-2 border-b border-slate-800/80 pb-4">
        <FileText className="h-5 w-5 text-brand-400" />
        <h3 className="text-lg font-bold text-white">Lecture Transcript</h3>
      </div>

      <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
        {segments.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-8">No transcript segments available.</p>
        ) : (
          segments.map((seg, idx) => (
            <div 
              key={idx} 
              className="flex gap-4 p-3 rounded-xl hover:bg-slate-900/20 border border-transparent hover:border-slate-800/50 transition group"
            >
              <span className="text-xs font-bold text-brand-400 bg-brand-500/10 px-2.5 py-1 rounded h-fit flex items-center gap-1 select-none">
                <Clock className="h-3 w-3" />
                <span>{formatTime(seg.start)}</span>
              </span>
              <p className="text-sm text-slate-300 leading-relaxed flex-1 group-hover:text-white transition">
                {seg.text}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
