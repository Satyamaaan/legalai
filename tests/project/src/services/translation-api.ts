import { apiClient } from '@/lib/api-client';
import {
  TranslationJob,
  SignedUrlRequest,
  SignedUrlResponse,
  UploadConfirmRequest,
  UploadConfirmResponse,
  TranslationStartRequest,
  TranslationStartResponse,
  DownloadResponse,
  HistoryRequest,
  PaginatedResponse,
  SystemStatus,
  Language,
  LanguagePair,
  UploadProgress,
} from '@/types/api';

// Upload Service
export class UploadService {
  /**
   * Get a signed URL for file upload
   */
  static async getSignedUrl(request: SignedUrlRequest): Promise<SignedUrlResponse> {
    const response = await apiClient.post<SignedUrlResponse>('/api/upload/signed-url', request);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get signed URL');
    }
    
    return response.data;
  }

  /**
   * Upload file to signed URL with progress tracking
   */
  static async uploadToSignedUrl(
    signedUrl: string,
    file: File,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<void> {
    const startTime = Date.now();
    let lastLoaded = 0;
    let lastTime = startTime;

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const currentTime = Date.now();
          const timeDiff = currentTime - lastTime;
          const loadedDiff = event.loaded - lastLoaded;
          
          // Calculate speed (bytes per second)
          const speed = timeDiff > 0 ? (loadedDiff / timeDiff) * 1000 : 0;
          
          // Calculate time remaining
          const remaining = event.total - event.loaded;
          const timeRemaining = speed > 0 ? remaining / speed : undefined;

          onProgress({
            loaded: event.loaded,
            total: event.total,
            percentage: Math.round((event.loaded / event.total) * 100),
            speed,
            timeRemaining,
          });

          lastLoaded = event.loaded;
          lastTime = currentTime;
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed due to network error'));
      });

      xhr.addEventListener('timeout', () => {
        reject(new Error('Upload timed out'));
      });

      xhr.open('PUT', signedUrl);
      xhr.setRequestHeader('Content-Type', file.type);
      xhr.timeout = 300000; // 5 minutes
      xhr.send(file);
    });
  }

  /**
   * Confirm file upload completion
   */
  static async confirmUpload(request: UploadConfirmRequest): Promise<UploadConfirmResponse> {
    const response = await apiClient.post<UploadConfirmResponse>('/api/upload/confirm', request);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to confirm upload');
    }
    
    return response.data;
  }

  /**
   * Get upload status
   */
  static async getUploadStatus(jobId: string): Promise<TranslationJob> {
    const response = await apiClient.get<TranslationJob>(`/api/upload/status/${jobId}`);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get upload status');
    }
    
    return response.data;
  }

  /**
   * Complete upload workflow
   */
  static async uploadFile(
    file: File,
    request: Omit<SignedUrlRequest, 'filename' | 'file_size' | 'file_type'>,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<UploadConfirmResponse> {
    // Step 1: Get signed URL
    const signedUrlResponse = await this.getSignedUrl({
      ...request,
      filename: file.name,
      file_size: file.size,
      file_type: file.type,
    });

    // Step 2: Upload file
    await this.uploadToSignedUrl(signedUrlResponse.upload_url, file, onProgress);

    // Step 3: Confirm upload
    return this.confirmUpload({
      job_id: signedUrlResponse.job_id,
    });
  }
}

// Translation Service
export class TranslationService {
  /**
   * Start translation job
   */
  static async startTranslation(request: TranslationStartRequest): Promise<TranslationStartResponse> {
    const response = await apiClient.post<TranslationStartResponse>(
      `/api/translate/start/${request.job_id}`,
      request
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to start translation');
    }
    
    return response.data;
  }

  /**
   * Get translation job status
   */
  static async getJobStatus(jobId: string): Promise<TranslationJob> {
    const response = await apiClient.get<TranslationJob>(`/api/translate/status/${jobId}`);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get job status');
    }
    
    return response.data;
  }

  /**
   * Cancel translation job
   */
  static async cancelJob(jobId: string): Promise<TranslationJob> {
    const response = await apiClient.post<TranslationJob>(`/api/translate/cancel/${jobId}`);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to cancel job');
    }
    
    return response.data;
  }

  /**
   * Retry failed translation job
   */
  static async retryJob(jobId: string): Promise<TranslationJob> {
    const response = await apiClient.post<TranslationJob>(`/api/translate/retry/${jobId}`);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to retry job');
    }
    
    return response.data;
  }

  /**
   * Get available languages
   */
  static async getLanguages(): Promise<Language[]> {
    const response = await apiClient.get<Language[]>('/api/translate/languages');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get languages');
    }
    
    return response.data;
  }

  /**
   * Get supported language pairs
   */
  static async getLanguagePairs(): Promise<LanguagePair[]> {
    const response = await apiClient.get<LanguagePair[]>('/api/translate/language-pairs');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get language pairs');
    }
    
    return response.data;
  }

  /**
   * Get translation cost estimate
   */
  static async getCostEstimate(
    sourceLanguage: string,
    targetLanguage: string,
    fileSize: number,
    translationType: 'standard' | 'certified' | 'notarized'
  ): Promise<{ cost: number; currency: string; estimated_completion: string }> {
    const response = await apiClient.post<{
      cost: number;
      currency: string;
      estimated_completion: string;
    }>('/api/translate/estimate', {
      source_language: sourceLanguage,
      target_language: targetLanguage,
      file_size: fileSize,
      translation_type: translationType,
    });
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get cost estimate');
    }
    
    return response.data;
  }
}

// Download Service
export class DownloadService {
  /**
   * Get download URL for completed job
   */
  static async getDownloadUrl(jobId: string): Promise<DownloadResponse> {
    const response = await apiClient.get<DownloadResponse>(`/api/download/job/${jobId}`);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get download URL');
    }
    
    return response.data;
  }

  /**
   * Download file directly
   */
  static async downloadFile(jobId: string, filename?: string): Promise<Blob> {
    const downloadInfo = await this.getDownloadUrl(jobId);
    
    const response = await fetch(downloadInfo.download_url);
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }
    
    const blob = await response.blob();
    
    // Trigger download
    if (filename || downloadInfo.filename) {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || downloadInfo.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }
    
    return blob;
  }
}

// History Service
export class HistoryService {
  /**
   * Get translation job history
   */
  static async getHistory(request: HistoryRequest = {}): Promise<PaginatedResponse<TranslationJob>> {
    const params = new URLSearchParams();
    
    Object.entries(request).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });
    
    const response = await apiClient.get<TranslationJob[]>(
      `/api/upload/history?${params.toString()}`
    );
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to get history');
    }
    
    // Type assertion since we know this endpoint returns paginated data
    return response as PaginatedResponse<TranslationJob>;
  }

  /**
   * Delete job from history
   */
  static async deleteJob(jobId: string): Promise<void> {
    const response = await apiClient.delete(`/api/upload/history/${jobId}`);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to delete job');
    }
  }

  /**
   * Bulk delete jobs
   */
  static async bulkDeleteJobs(jobIds: string[]): Promise<void> {
    const response = await apiClient.post('/api/upload/history/bulk-delete', {
      job_ids: jobIds,
    });
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to delete jobs');
    }
  }
}

// System Service
export class SystemService {
  /**
   * Get system status
   */
  static async getStatus(): Promise<SystemStatus> {
    const response = await apiClient.get<SystemStatus>('/api/system/status');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get system status');
    }
    
    return response.data;
  }

  /**
   * Health check
   */
  static async healthCheck(): Promise<{ status: 'ok' | 'error'; timestamp: string }> {
    const response = await apiClient.get<{ status: 'ok' | 'error'; timestamp: string }>(
      '/api/system/health'
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Health check failed');
    }
    
    return response.data;
  }
}

// Export all services
export const translationApi = {
  upload: UploadService,
  translation: TranslationService,
  download: DownloadService,
  history: HistoryService,
  system: SystemService,
};