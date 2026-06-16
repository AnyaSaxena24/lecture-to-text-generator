"use client";

import React, { useState } from "react";
import { HelpCircle, ChevronRight, RefreshCw } from "lucide-react";

interface FlashcardCardProps {
  question: string;
  answer: string;
  difficulty?: string;
  tag?: string;
}

export default function FlashcardCard({ question, answer, difficulty = "Medium", tag = "Core" }: FlashcardCardProps) {
  const [flipped, setFlipped] = useState(false);

  // Difficulty badge colors
  const getDifficultyColor = (level: string) => {
    switch (level.toLowerCase()) {
      case "easy": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "hard": return "bg-red-500/10 text-red-400 border-red-500/20";
      default: return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto space-y-4">
      {/* 3D Container */}
      <div 
        onClick={() => setFlipped(!flipped)}
        className="h-64 cursor-pointer perspective-1000 w-full"
      >
        <div className={`relative w-full h-full duration-500 transform-style-3d ${flipped ? "rotate-y-180" : ""}`}>
          
          {/* Card Front */}
          <div className="absolute inset-0 w-full h-full glass rounded-2xl p-8 flex flex-col justify-between items-center text-center shadow-xl backface-hidden border border-slate-800/80">
            <div className="flex items-center justify-between w-full">
              <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border ${getDifficultyColor(difficulty)}`}>
                {difficulty}
              </span>
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
                #{tag}
              </span>
            </div>
            
            <p className="text-lg font-extrabold text-white max-w-md">{question}</p>
            
            <span className="text-[10px] font-bold text-brand-400 flex items-center gap-1.5 animate-pulse">
              <RefreshCw className="h-3 w-3" />
              <span>Click to flip card</span>
            </span>
          </div>

          {/* Card Back */}
          <div className="absolute inset-0 w-full h-full bg-brand-950/20 rounded-2xl p-8 flex flex-col justify-between items-center text-center shadow-xl backface-hidden rotate-y-180 border border-brand-500/30">
            <div className="flex items-center justify-between w-full">
              <span className="text-[10px] text-brand-400 font-bold uppercase tracking-wider">Answer Key</span>
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">#{tag}</span>
            </div>
            
            <p className="text-base text-slate-200 font-semibold max-w-md leading-relaxed">{answer}</p>
            
            <span className="text-[10px] font-bold text-slate-500">Click to flip back</span>
          </div>

        </div>
      </div>

      <style jsx global>{`
        .perspective-1000 {
          perspective: 1000px;
        }
        .transform-style-3d {
          transform-style: preserve-3d;
        }
        .backface-hidden {
          backface-visibility: hidden;
          -webkit-backface-visibility: hidden;
        }
        .rotate-y-180 {
          transform: rotateY(180deg);
        }
      `}</style>
    </div>
  );
}
