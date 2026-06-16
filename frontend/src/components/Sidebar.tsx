"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { 
  LayoutDashboard, Upload, History, User, LogOut, 
  BookOpen, FileText, Settings, Sparkles
} from "lucide-react";

interface SidebarProps {
  lectures?: Array<{
    id: string;
    title: string;
    status: string;
  }>;
}

export default function Sidebar({ lectures = [] }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const links = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/dashboard?action=upload", label: "Upload Lecture", icon: Upload },
    { href: "/dashboard?filter=completed", label: "Study History", icon: History },
  ];

  return (
    <aside className="w-64 bg-dark-card border-r border-dark-border hidden md:flex flex-col h-[calc(100vh-76px)] sticky top-[76px] overflow-y-auto">
      {/* Navigation Groups */}
      <div className="p-4 space-y-6 flex-1">
        <div className="space-y-1">
          <p className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Main Menu</p>
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href || (link.href.includes("action=upload") && pathname.includes("upload")); // basic check
            
            return (
              <Link
                key={link.label}
                href={link.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition duration-150 ${
                  isActive 
                    ? "bg-brand-600/15 text-brand-300 border-l-2 border-brand-500" 
                    : "text-slate-400 hover:text-white hover:bg-slate-900/50"
                }`}
              >
                <Icon className="h-4.5 w-4.5" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Recently Transcribed */}
        {lectures.length > 0 && (
          <div className="space-y-2">
            <p className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Recent Study Guides</p>
            <div className="space-y-1 max-h-[250px] overflow-y-auto scrollbar-none">
              {lectures.slice(0, 5).map((l) => (
                <Link
                  key={l.id}
                  href={`/lectures/${l.id}`}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-slate-400 hover:text-white hover:bg-slate-900/40 transition truncate"
                >
                  <BookOpen className="h-3.5 w-3.5 text-brand-400 flex-shrink-0" />
                  <span className="truncate">{l.title}</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* User Session Info Panel */}
      {user && (
        <div className="p-4 border-t border-dark-border bg-slate-950/20 space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-full bg-brand-600/20 flex items-center justify-center text-brand-400 font-bold text-sm">
              {user.full_name[0].toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold text-white truncate">{user.full_name}</p>
              <p className="text-[10px] text-slate-500 truncate">{user.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 py-2 text-xs font-bold text-red-400 hover:bg-red-500/20 transition"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      )}
    </aside>
  );
}
