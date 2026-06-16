"use client";

import React, { useState } from "react";
import { Check, X, HelpCircle, AlertCircle } from "lucide-react";

interface QuizItem {
  question: string;
  options: string[];
  correct_answer: string;
  difficulty?: string;
  type?: string;
}

interface QuizCardProps {
  quizItems: QuizItem[];
}

export default function QuizCard({ quizItems = [] }: QuizCardProps) {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [shortAnswers, setShortAnswers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const getDifficultyColor = (level?: string) => {
    switch (level?.toLowerCase()) {
      case "easy": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "hard": return "bg-red-500/10 text-red-400 border-red-500/20";
      default: return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
    }
  };

  if (quizItems.length === 0) {
    return (
      <div className="glass rounded-2xl p-8 text-center text-slate-500">
        <HelpCircle className="h-10 w-10 text-slate-700 mx-auto mb-3" />
        <p className="text-sm">No quiz questions generated yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {quizItems.map((item, idx) => {
        const itemType = item.type || (item.options.length === 0 ? "short_answer" : item.options.length === 2 ? "true_false" : "mcq");
        const selected = answers[idx];
        const isCorrect = selected === item.correct_answer;

        return (
          <div key={idx} className="glass rounded-2xl p-6 space-y-4">
            {/* Question Header */}
            <div className="flex items-start justify-between gap-4">
              <h4 className="text-base font-bold text-white leading-relaxed">
                {idx + 1}. {item.question}
              </h4>
              <span className={`text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full border shrink-0 ${getDifficultyColor(item.difficulty)}`}>
                {item.difficulty || "Medium"}
              </span>
            </div>

            {/* MCQ / TF Option Selection */}
            {(itemType === "mcq" || itemType === "true_false") && (
              <div className="grid gap-3 sm:grid-cols-2">
                {item.options.map((opt, optIdx) => {
                  const isSelected = selected === opt;
                  const showCorrect = submitted && opt === item.correct_answer;
                  const showIncorrect = submitted && isSelected && !isCorrect;

                  return (
                    <button
                      key={optIdx}
                      disabled={submitted}
                      onClick={() => setAnswers(prev => ({ ...prev, [idx]: opt }))}
                      className={`p-3.5 rounded-xl text-xs font-semibold text-left border transition ${
                        showCorrect
                          ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
                          : showIncorrect
                          ? "bg-red-500/10 border-red-500 text-red-400"
                          : isSelected
                          ? "bg-brand-500/10 border-brand-500 text-brand-300"
                          : "bg-slate-900/40 border-slate-800/80 text-slate-300 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span>{opt}</span>
                        {showCorrect && <Check className="h-4 w-4 text-emerald-400" />}
                        {showIncorrect && <X className="h-4 w-4 text-red-400" />}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Short Answer Input Field */}
            {itemType === "short_answer" && (
              <div className="space-y-3">
                <textarea
                  disabled={submitted}
                  rows={2}
                  value={shortAnswers[idx] || ""}
                  onChange={(e) => setShortAnswers(prev => ({ ...prev, [idx]: e.target.value }))}
                  placeholder="Type your answer here..."
                  className="glass-input w-full rounded-xl p-3.5 text-xs placeholder:text-slate-600 focus:border-brand-500 resize-none"
                />
                
                {submitted && (
                  <div className="rounded-xl bg-slate-900/50 p-4 border border-slate-800 text-[11px] text-slate-300 leading-relaxed space-y-1">
                    <p className="font-bold text-brand-400 flex items-center gap-1">
                      <AlertCircle className="h-3.5 w-3.5" />
                      <span>Grading Answer Guideline:</span>
                    </p>
                    <p>{item.correct_answer}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}

      {/* Control Buttons */}
      {!submitted ? (
        <button
          onClick={() => setSubmitted(true)}
          className="w-full rounded-xl bg-brand-600 py-3.5 text-sm font-bold text-white hover:bg-brand-500 transition shadow-lg shadow-brand-600/15"
        >
          Submit Quiz
        </button>
      ) : (
        <button
          onClick={() => {
            setSubmitted(false);
            setAnswers({});
            setShortAnswers({});
          }}
          className="w-full rounded-xl border border-slate-700 bg-slate-900/50 py-3.5 text-sm font-bold text-slate-300 hover:bg-slate-950 transition"
        >
          Reset Quiz
        </button>
      )}
    </div>
  );
}
