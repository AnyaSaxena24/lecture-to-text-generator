"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { GraduationCap, LogOut, LayoutDashboard, User } from "lucide-react";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="glass sticky top-0 z-50 w-full px-6 py-4">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 text-xl font-bold tracking-tight text-white hover:opacity-90">
          <GraduationCap className="h-7 w-7 text-brand-500 animate-pulse-slow" />
          <span>Lecture<span className="text-brand-400">Notes AI</span></span>
        </Link>

        {/* Action Items */}
          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 text-sm font-semibold text-slate-300 hover:text-white transition"
          >
            <LayoutDashboard className="h-4 w-4" />
            <span>Dashboard Workspace</span>
          </Link>
      </div>
    </nav>
  );
}
