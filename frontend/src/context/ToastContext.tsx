"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle, AlertCircle, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((message: string, type: ToastType) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
    
    // Auto remove after 4 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const success = useCallback((msg: string) => addToast(msg, "success"), [addToast]);
  const error = useCallback((msg: string) => addToast(msg, "error"), [addToast]);
  const info = useCallback((msg: string) => addToast(msg, "info"), [addToast]);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const getToastStyles = (type: ToastType) => {
    switch (type) {
      case "success":
        return {
          bg: "border-emerald-500/20 bg-emerald-950/20 text-emerald-400",
          icon: <CheckCircle className="h-5 w-5 text-emerald-400" />
        };
      case "error":
        return {
          bg: "border-red-500/20 bg-red-950/20 text-red-400",
          icon: <AlertCircle className="h-5 w-5 text-red-400" />
        };
      default:
        return {
          bg: "border-blue-500/20 bg-blue-950/20 text-blue-400",
          icon: <Info className="h-5 w-5 text-blue-400" />
        };
    }
  };

  return (
    <ToastContext.Provider value={{ success, error, info }}>
      {children}
      
      {/* Toast Render Area */}
      <div className="fixed top-6 right-6 z-[100] space-y-3 w-full max-w-sm pointer-events-none">
        {toasts.map((toast) => {
          const styles = getToastStyles(toast.type);
          return (
            <div
              key={toast.id}
              className={`glass flex items-center justify-between gap-4 p-4 rounded-xl border pointer-events-auto shadow-2xl animate-slide-up ${styles.bg}`}
            >
              <div className="flex items-center gap-3">
                {styles.icon}
                <p className="text-xs font-bold leading-relaxed">{toast.message}</p>
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="hover:opacity-80 transition shrink-0"
              >
                <X className="h-4 w-4 opacity-50 hover:opacity-100" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
