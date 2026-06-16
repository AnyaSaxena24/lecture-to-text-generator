"use client";

import Link from "next/link";
import { GraduationCap, ArrowRight, BrainCircuit, FileSpreadsheet, Sparkles, HelpCircle } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="relative flex flex-col items-center justify-center py-12 md:py-24 overflow-hidden">
      {/* Decorative gradient blobs */}
      <div className="absolute top-1/4 left-1/2 -z-10 h-[300px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand-500/20 blur-[100px] animate-pulse-slow" />
      <div className="absolute bottom-10 right-10 -z-10 h-[200px] w-[400px] rounded-full bg-indigo-500/10 blur-[80px]" />

      {/* Hero Badge */}
      <div className="mb-6 inline-flex items-center gap-1.5 rounded-full border border-brand-500/30 bg-brand-500/10 px-4 py-1.5 text-xs font-semibold text-brand-300 animate-fade-in">
        <Sparkles className="h-3.5 w-3.5" />
        <span>Powered by Whisper & Local AI Models</span>
      </div>

      {/* Hero Header */}
      <div className="max-w-3xl text-center animate-slide-up">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-6xl text-white">
          Turn Lecture Audio Into <br />
          <span className="bg-gradient-to-r from-brand-400 via-violet-400 to-indigo-400 bg-clip-text text-transparent">
            Perfect Study Guides
          </span>
        </h1>
        <p className="mt-6 text-lg text-slate-300 leading-relaxed max-w-xl mx-auto">
          Upload lecture videos or audio files. Instantly generate timestamped transcripts, clean summary notes, flashcards, and interactive practice quizzes.
        </p>

        {/* Call to Actions */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-3.5 font-bold text-white shadow-xl shadow-brand-600/30 hover:bg-brand-500 hover:shadow-brand-500/40 hover:-translate-y-0.5 transition duration-200 animate-pulse-slow"
          >
            <span>Open Dashboard Workspace</span>
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </div>

      {/* Features Grid */}
      <div className="mt-24 w-full max-w-5xl">
        <h2 className="text-2xl font-bold text-center text-white mb-12">Complete AI Study Suite</h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 px-4">
          
          <div className="glass rounded-2xl p-6 hover:border-brand-500/30 transition duration-300">
            <div className="mb-4 inline-block rounded-xl bg-brand-500/10 p-3 text-brand-400">
              <GraduationCap className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Speech-to-Text</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Highly accurate speech transcription with precise timing for easy tracking.
            </p>
          </div>

          <div className="glass rounded-2xl p-6 hover:border-brand-500/30 transition duration-300">
            <div className="mb-4 inline-block rounded-xl bg-brand-500/10 p-3 text-brand-400">
              <FileSpreadsheet className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Auto-Summaries</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Condenses full-length recordings into digestible takeaways, saving hours of revision.
            </p>
          </div>

          <div className="glass rounded-2xl p-6 hover:border-brand-500/30 transition duration-300">
            <div className="mb-4 inline-block rounded-xl bg-brand-500/10 p-3 text-brand-400">
              <BrainCircuit className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Smart Flashcards</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Key definitions and concepts mapped out dynamically for active recall study session.
            </p>
          </div>

          <div className="glass rounded-2xl p-6 hover:border-brand-500/30 transition duration-300">
            <div className="mb-4 inline-block rounded-xl bg-brand-500/10 p-3 text-brand-400">
              <HelpCircle className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Practice Quizzes</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Generate customizable multiple choice quizzes with instant solution explanations.
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}
