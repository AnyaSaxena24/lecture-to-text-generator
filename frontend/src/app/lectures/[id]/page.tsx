"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import TranscriptPanel from "@/components/TranscriptPanel";
import NotesCard from "@/components/NotesCard";
import FlashcardCard from "@/components/FlashcardCard";
import QuizCard from "@/components/QuizCard";
import { 
  FileText, Calendar, Clock, Download, ArrowLeft, Loader2,
  BookOpen, Layers, HelpCircle, ChevronLeft, ChevronRight
} from "lucide-react";

interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
}

interface Flashcard {
  question: string;
  answer: string;
  difficulty?: string;
  tag?: string;
}

interface QuizItem {
  question: string;
  options: string[];
  correct_answer: string;
  difficulty?: string;
  type?: string;
}

interface Lecture {
  id: string;
  title: string;
  file_name: string;
  file_size: number;
  status: string;
  created_at: string;
  transcript?: TranscriptSegment[];
  summary?: string;
  bullet_notes?: string[];
  flashcards?: Flashcard[];
  quizzes?: QuizItem[];
}

export default function LectureDetails() {
  const { id } = useParams();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  
  const [lecture, setLecture] = useState<Lecture | null>(null);
  const [lectures, setLectures] = useState<Lecture[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"transcript" | "summary" | "flashcards" | "quiz">("summary");
  
  // Flashcard slide state
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/login");
      return;
    }

    const fetchData = async () => {
      try {
        const detail = await api.get<Lecture>(`/api/lectures/${id}`);
        setLecture(detail);
        
        const list = await api.get<Lecture[]>("/api/lectures");
        setLectures(list);
      } catch (err) {
        console.error("Failed to load details:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, user, authLoading]);

  // Format Helper
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const handleDownloadPdf = async () => {
    if (!lecture) return;
    setDownloadingPdf(true);
    try {
      const blob = await api.getBlob(`/api/lectures/${lecture.id}/pdf`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${lecture.title.replace(/\s+/g, "_")}_study_notes.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to download PDF study guide.");
    } finally {
      setDownloadingPdf(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
        <Loader2 className="h-10 w-10 text-brand-500 animate-spin" />
        <p className="text-slate-400 text-sm">Loading study guide workspace...</p>
      </div>
    );
  }

  if (!lecture) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-300 text-lg">Lecture material not found.</p>
        <button onClick={() => router.push("/dashboard")} className="mt-4 text-brand-400 font-bold hover:underline">
          Go back to dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-1 -m-8 min-h-[calc(100vh-76px)]">
      {/* Sidebar List navigation */}
      <Sidebar lectures={lectures} />

      {/* Main Study Desk Area */}
      <div className="flex-1 p-8 overflow-y-auto space-y-8">
        
        {/* Action Controls */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-dark-border pb-6">
          <div className="space-y-1">
            <button
              onClick={() => router.push("/dashboard")}
              className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-white transition mb-2"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Workspace</span>
            </button>
            <h1 className="text-xl font-extrabold text-white">{lecture.title}</h1>
            
            {/* Meta Tags */}
            <div className="flex flex-wrap gap-4 text-[10px] text-slate-500">
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                {new Date(lecture.created_at).toLocaleDateString()}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                {lecture.transcript && lecture.transcript.length > 0 
                  ? formatTime(lecture.transcript[lecture.transcript.length - 1].end) 
                  : "00:00"}
              </span>
            </div>
          </div>

          <button
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
            className="flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg hover:bg-brand-500 transition disabled:opacity-50"
          >
            {downloadingPdf ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Download className="h-3.5 w-3.5" />
            )}
            <span>Export Notes as PDF</span>
          </button>
        </div>

        {/* Tab navigation list */}
        <div className="flex border-b border-slate-800 scrollbar-none overflow-x-auto gap-2">
          {[
            { id: "summary", label: "Executive Summary", icon: BookOpen },
            { id: "transcript", label: "Lecture Transcript", icon: FileText },
            { id: "flashcards", label: "Smart Flashcards", icon: Layers },
            { id: "quiz", label: "Practice Quiz", icon: HelpCircle },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 py-3 px-4 text-xs font-bold border-b-2 transition whitespace-nowrap ${
                  activeTab === tab.id
                    ? "border-brand-500 text-brand-400"
                    : "border-transparent text-slate-400 hover:text-white"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Active Tab View Panels */}
        <div className="mt-4">
          
          {/* Notes summary Card */}
          {activeTab === "summary" && (
            <NotesCard 
              summary={lecture.summary || ""} 
              bulletNotes={lecture.bullet_notes || []} 
            />
          )}

          {/* Transcript Viewer Panel */}
          {activeTab === "transcript" && (
            <TranscriptPanel segments={lecture.transcript || []} />
          )}

          {/* Smart Study Flashcards */}
          {activeTab === "flashcards" && (
            <div className="max-w-xl mx-auto flex flex-col items-center gap-6">
              {lecture.flashcards && lecture.flashcards.length > 0 ? (
                <>
                  <FlashcardCard 
                    question={lecture.flashcards[currentCardIndex].question}
                    answer={lecture.flashcards[currentCardIndex].answer}
                    difficulty={lecture.flashcards[currentCardIndex].difficulty}
                    tag={lecture.flashcards[currentCardIndex].tag}
                  />

                  {/* Card selector controls */}
                  <div className="flex items-center gap-6">
                    <button
                      disabled={currentCardIndex === 0}
                      onClick={() => setCurrentCardIndex(prev => prev - 1)}
                      className="rounded-full bg-slate-800 p-2 text-slate-300 hover:bg-slate-700 disabled:opacity-30 transition"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </button>
                    <span className="text-xs font-semibold text-slate-400">
                      {currentCardIndex + 1} / {lecture.flashcards.length}
                    </span>
                    <button
                      disabled={currentCardIndex === lecture.flashcards.length - 1}
                      onClick={() => setCurrentCardIndex(prev => prev + 1)}
                      className="rounded-full bg-slate-800 p-2 text-slate-300 hover:bg-slate-700 disabled:opacity-30 transition"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                </>
              ) : (
                <p className="text-xs text-slate-500 text-center py-8">No flashcards generated for this lecture.</p>
              )}
            </div>
          )}

          {/* Interactive Quizzes */}
          {activeTab === "quiz" && (
            <QuizCard quizItems={lecture.quizzes || []} />
          )}

        </div>

      </div>
    </div>
  );
}
