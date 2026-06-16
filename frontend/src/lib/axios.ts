import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor: Attach JWT token dynamically
axiosInstance.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Parse standardized API errors
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = "An unexpected error occurred.";
    if (error.response) {
      // Server returned error status code
      message = error.response.data?.detail || message;
    } else if (error.request) {
      // Request sent but no response
      message = "Network error. Please check your connection.";
    }
    
    // Create normalized error object to propagate
    const parsedError = new Error(message);
    (parsedError as any).status = error.response?.status;
    return Promise.reject(parsedError);
  }
);

export default axiosInstance;
