// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// Job Status Types
export type JobStatus = 'pending' | 'processing' | 'done' | 'error' | 'cancelled';

export interface TranslationJob {
  id: string;
  status: JobStatus;
  progress: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  source_language: string;
  target_language: string;
  translation_type: 'standard' | 'certified' | 'notarized';
  estimated_completion?: string;
  cost_estimate?: number;
  download_url?: string;
  download_expires_at?: string;
}

// Upload Types
export interface SignedUrlRequest {
  filename: string;
  file_size: number;
  file_type: string;
  source_language: string;
  target_language: string;
  translation_type: 'standard' | 'certified' | 'notarized';
}

export interface SignedUrlResponse {
  upload_url: string;
  job_id: string;
  expires_at: string;
  max_file_size: number;
}

export interface UploadConfirmRequest {
  job_id: string;
  file_checksum?: string;
}

export interface UploadConfirmResponse {
  job: TranslationJob;
  estimated_completion: string;
  cost_estimate: number;
}

// Translation Types
export interface TranslationStartRequest {
  job_id: string;
  priority?: 'standard' | 'expedited' | 'rush';
  special_instructions?: string;
  certification_required?: boolean;
}

export interface TranslationStartResponse {
  job: TranslationJob;
  estimated_completion: string;
  tracking_id: string;
}

// Download Types
export interface DownloadResponse {
  download_url: string;
  filename: string;
  file_size: number;
  expires_at: string;
  content_type: string;
}

// History Types
export interface HistoryRequest {
  page?: number;
  limit?: number;
  status?: JobStatus;
  search?: string;
  sort_by?: 'created_at' | 'updated_at' | 'filename' | 'status';
  sort_order?: 'asc' | 'desc';
  date_from?: string;
  date_to?: string;
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

// Language Types
export interface Language {
  code: string;
  name: string;
  native_name: string;
  supported_pairs: string[];
}

export interface LanguagePair {
  source: Language;
  target: Language;
  available_types: ('standard' | 'certified' | 'notarized')[];
  base_price: number;
  estimated_turnaround: {
    standard: string;
    expedited: string;
    rush: string;
  };
}

// System Status Types
export interface SystemStatus {
  status: 'operational' | 'degraded' | 'maintenance' | 'outage';
  services: {
    upload: 'operational' | 'degraded' | 'down';
    translation: 'operational' | 'degraded' | 'down';
    download: 'operational' | 'degraded' | 'down';
  };
  message?: string;
  last_updated: string;
}

// User Types (for future authentication)
export interface User {
  id: string;
  email: string;
  name: string;
  company?: string;
  role: 'user' | 'admin';
  subscription_tier: 'free' | 'professional' | 'enterprise';
  created_at: string;
  last_login?: string;
}

// Webhook Types
export interface WebhookEvent {
  id: string;
  type: 'job.created' | 'job.processing' | 'job.completed' | 'job.failed';
  job_id: string;
  timestamp: string;
  data: TranslationJob;
}