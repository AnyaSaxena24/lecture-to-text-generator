"use client";

import React from "react";
import { BookOpen, Award, CheckCircle } from "lucide-react";

interface NotesCardProps {
  summary: string;
  bulletNotes: string[];
}

export default function NotesCard({ summary, bulletNotes = [] }: NotesCardProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Summary Section */}
      <div className="lg:col-span-2 glass rounded-2xl p-6 space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-800/80 pb-3">
          <BookOpen className="h-5 w-5 text-brand-400" />
          <h3 className="text-lg font-bold text-white">Lecture Summary</h3>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
          {summary || "Summary generation pending."}
        </p>
      </div>

      {/* Bullet Notes / Takeaways */}
      <div className="lg:col-span-1 glass rounded-2xl p-6 space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-800/80 pb-3">
          <Award className="h-5 w-5 text-brand-400" />
          <h3 className="text-lg font-bold text-white">Study Points</h3>
        </div>
        
        {bulletNotes.length === 0 ? (
          <p className="text-xs text-slate-500">No key concepts extracted.</p>
        ) : (
          <ul className="space-y-3">
            {bulletNotes.map((note, index) => (
              <li key={index} className="flex items-start gap-2.5 text-xs text-slate-300 leading-relaxed">
                <CheckCircle className="h-4 w-4 text-brand-500 mt-0.5 flex-shrink-0" />
                <span>{note}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
