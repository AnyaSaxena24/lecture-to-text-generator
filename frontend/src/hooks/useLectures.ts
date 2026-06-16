"use client";

import { useState, useCallback } from "react";
import axiosInstance from "@/lib/axios";
import { useToast } from "@/context/ToastContext";

interface Lecture {
  id: string;
  title: string;
  file_name: string;
  file_size: number;
  status: "pending" | "transcribing" | "generating" | "completed" | "failed";
  error_message?: string;
  created_at: string;
}

export function useLectures() {
  const [lectures, setLectures] = useState<Lecture[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const toast = useToast();

  const fetchLectures = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axiosInstance.get<Lecture[]>("/api/lectures");
      setLectures(response.data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load lectures.");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  const uploadLecture = useCallback(async (file: File, onProgress: (progress: number) => void) => {
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axiosInstance.post<Lecture>("/api/lectures/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percentCompleted);
          }
        },
      });
      
      toast.success(`Successfully uploaded ${file.name}`);
      setLectures((prev) => [response.data, ...prev]);
      return response.data;
    } catch (err: any) {
      toast.error(err.message || "File upload failed.");
      throw err;
    } finally {
      setUploading(false);
    }
  }, [toast]);

  const deleteLecture = useCallback(async (id: string) => {
    try {
      await axiosInstance.delete(`/api/lectures/${id}`);
      setLectures((prev) => prev.filter((l) => l.id !== id));
      toast.success("Lecture deleted successfully.");
    } catch (err: any) {
      toast.error(err.message || "Failed to delete lecture.");
      throw err;
    }
  }, [toast]);

  return {
    lectures,
    loading,
    uploading,
    fetchLectures,
    uploadLecture,
    deleteLecture,
  };
}
