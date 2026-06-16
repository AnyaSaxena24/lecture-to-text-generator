"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, full_name: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Hardcoded guest profile enabling direct access to workspace features
const DEFAULT_USER: User = {
  id: "default_student",
  email: "student@example.com",
  full_name: "Student Workspace",
  created_at: new Date().toISOString()
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(DEFAULT_USER);
  const [loading, setLoading] = useState(false);

  const login = async (email: string, password: string) => {
    // No-op - registration/login bypassed
  };

  const register = async (email: string, full_name: string, password: string) => {
    // No-op - registration/login bypassed
  };

  const logout = () => {
    // No-op - registration/login bypassed
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
