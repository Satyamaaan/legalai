import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { ApiResponse, ApiError, ValidationError } from '@/types/api';

// Environment configuration
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://api.legaltranslate.pro/v1',
  timeout: import.meta.env.VITE_API_TIMEOUT ? parseInt(import.meta.env.VITE_API_TIMEOUT) : 30000,
  retryAttempts: 3,
  retryDelay: 1000,
};

// Custom error classes
export class ApiClientError extends Error {
  constructor(
    message: string,
    public code: string,
    public status?: number,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

export class ValidationApiError extends ApiClientError {
  constructor(
    message: string,
    public fieldErrors: Record<string, string[]>,
    status?: number
  ) {
    super(message, 'VALIDATION_ERROR', status);
    this.name = 'ValidationApiError';
  }
}

export class NetworkError extends ApiClientError {
  constructor(message: string = 'Network connection failed') {
    super(message, 'NETWORK_ERROR');
    this.name = 'NetworkError';
  }
}

export class TimeoutError extends ApiClientError {
  constructor(message: string = 'Request timeout') {
    super(message, 'TIMEOUT_ERROR');
    this.name = 'TimeoutError';
  }
}

// Request/Response interceptor types
interface RequestInterceptor {
  onFulfilled?: (config: AxiosRequestConfig) => AxiosRequestConfig | Promise<AxiosRequestConfig>;
  onRejected?: (error: any) => any;
}

interface ResponseInterceptor {
  onFulfilled?: (response: AxiosResponse) => AxiosResponse | Promise<AxiosResponse>;
  onRejected?: (error: AxiosError) => any;
}

// API Client class
class ApiClient {
  private client: AxiosInstance;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];

  constructor() {
    this.client = axios.create({
      baseURL: API_CONFIG.baseURL,
      timeout: API_CONFIG.timeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor for adding auth tokens, request ID, etc.
    this.client.interceptors.request.use(
      (config) => {
        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId();
        
        // Add timestamp
        config.headers['X-Request-Timestamp'] = new Date().toISOString();
        
        // Add auth token if available
        const token = this.getAuthToken();
        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`;
        }

        // Add API version
        config.headers['X-API-Version'] = '1.0';

        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, {
          headers: config.headers,
          data: config.data,
        });

        return config;
      },
      (error) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling and response transformation
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[API] Response ${response.status}:`, {
          url: response.config.url,
          data: response.data,
        });
        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        console.error('[API] Response error:', {
          status: error.response?.status,
          url: error.config?.url,
          message: error.message,
          data: error.response?.data,
        });

        // Handle network errors
        if (!error.response) {
          if (error.code === 'ECONNABORTED') {
            throw new TimeoutError('Request timeout - please check your connection');
          }
          throw new NetworkError('Network connection failed - please check your internet connection');
        }

        const { status, data } = error.response;

        // Handle specific HTTP status codes
        switch (status) {
          case 400:
            if (this.isValidationError(data)) {
              throw new ValidationApiError(
                data.message || 'Validation failed',
                data.field_errors,
                status
              );
            }
            throw new ApiClientError(
              data?.message || 'Bad request',
              data?.code || 'BAD_REQUEST',
              status,
              data?.details
            );

          case 401:
            // Handle unauthorized - maybe refresh token or redirect to login
            this.handleUnauthorized();
            throw new ApiClientError(
              'Authentication required',
              'UNAUTHORIZED',
              status
            );

          case 403:
            throw new ApiClientError(
              'Access forbidden',
              'FORBIDDEN',
              status
            );

          case 404:
            throw new ApiClientError(
              'Resource not found',
              'NOT_FOUND',
              status
            );

          case 409:
            throw new ApiClientError(
              data?.message || 'Conflict',
              'CONFLICT',
              status,
              data?.details
            );

          case 422:
            throw new ApiClientError(
              data?.message || 'Unprocessable entity',
              'UNPROCESSABLE_ENTITY',
              status,
              data?.details
            );

          case 429:
            // Rate limiting - implement retry with exponential backoff
            if (!originalRequest._retry && this.shouldRetry(originalRequest)) {
              originalRequest._retry = true;
              const retryAfter = error.response.headers['retry-after'];
              const delay = retryAfter ? parseInt(retryAfter) * 1000 : API_CONFIG.retryDelay;
              
              await this.delay(delay);
              return this.client(originalRequest);
            }
            throw new ApiClientError(
              'Too many requests - please try again later',
              'RATE_LIMITED',
              status
            );

          case 500:
          case 502:
          case 503:
          case 504:
            // Server errors - implement retry logic
            if (!originalRequest._retry && this.shouldRetry(originalRequest)) {
              originalRequest._retry = true;
              await this.delay(API_CONFIG.retryDelay);
              return this.client(originalRequest);
            }
            throw new ApiClientError(
              'Server error - please try again later',
              'SERVER_ERROR',
              status
            );

          default:
            throw new ApiClientError(
              data?.message || 'An unexpected error occurred',
              data?.code || 'UNKNOWN_ERROR',
              status,
              data?.details
            );
        }
      }
    );
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getAuthToken(): string | null {
    // Get token from localStorage, sessionStorage, or context
    return localStorage.getItem('auth_token');
  }

  private handleUnauthorized(): void {
    // Clear auth token and redirect to login
    localStorage.removeItem('auth_token');
    // You might want to emit an event or call a callback here
    console.warn('[API] Unauthorized - clearing auth token');
  }

  private isValidationError(data: any): data is ValidationError {
    return data && typeof data === 'object' && 'field_errors' in data;
  }

  private shouldRetry(config: AxiosRequestConfig): boolean {
    // Don't retry POST/PUT/PATCH requests by default to avoid duplicate operations
    const method = config.method?.toLowerCase();
    return !['post', 'put', 'patch'].includes(method || '');
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Public methods for making requests
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.get<ApiResponse<T>>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.patch<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.delete<ApiResponse<T>>(url, config);
    return response.data;
  }

  // File upload with progress tracking
  async uploadFile<T>(
    url: string,
    file: File,
    onProgress?: (progress: { loaded: number; total: number; percentage: number }) => void,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<ApiResponse<T>>(url, formData, {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            percentage,
          });
        }
      },
    });

    return response.data;
  }

  // Add custom interceptors
  addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor);
  }

  addResponseInterceptor(interceptor: ResponseInterceptor): void {
    this.responseInterceptors.push(interceptor);
  }

  // Get the underlying axios instance for advanced usage
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }

  // Cancel all pending requests
  cancelAllRequests(): void {
    // Implementation would depend on how you want to track requests
    console.log('[API] Cancelling all pending requests');
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();

// Export types for use in other files
export type { AxiosRequestConfig, AxiosResponse };