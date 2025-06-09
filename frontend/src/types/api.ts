// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

// Job Status Types - Updated to match backend
export type JobStatus = 'pending' | 'processing' | 'extracting' | 'translating' | 'building' | 'done' | 'error';

// Simplified Job object to match backend response
export interface TranslationJob {
  job_id: string;
  status: JobStatus;
  progress: number;
  error_message?: string | null;
  file: {
    original_name: string;
  };
}

// Upload Types - Simplified to match backend
export interface SignedUrlRequest {
  filename: string;
  content_type: string;
}

export interface SignedUrlResponse {
  upload_url: string;
  job_id: string;
  expires_at: string;
  max_file_size: number;
}

export interface UploadConfirmRequest {
  job_id: string;
}

export interface UploadConfirmResponse {
  job: TranslationJob;
  estimated_completion?: string;
  cost_estimate?: number;
}

// Error Types
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
  request_id?: string;
}

export interface ValidationError extends ApiError {
  field_errors: Record<string, string[]>;
}

// Upload Progress Types
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  speed?: number;
  timeRemaining?: number;
}