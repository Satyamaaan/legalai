import { apiClient } from '@/lib/api-client';
import {
  TranslationJob,
  JobStatus,
  UploadProgress,
  SignedUrlResponse,
  DownloadUrlResponse,
} from '@/types/api';

// Determine if we should use mock data. By default we only mock when the
// explicit VITE_USE_MOCKS flag is set.  This lets us run the dev server
// against the real Flask API without a rebuild.
const isDevelopment = import.meta.env.VITE_USE_MOCKS === 'true';

// Utility function for delays (extracted to file scope)
const delay = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// Mock data for development
const createMockJob = (fileId: string, originalName: string): TranslationJob => ({
  job_id: `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
  status: 'pending',
  progress: 0,
  error_message: null,
  file: {
    original_name: originalName,
  },
});

const createMockJobStatus = (jobId: string, status: JobStatus, progress: number, errorMessage?: string): TranslationJob => ({
  job_id: jobId,
  status,
  progress,
  error_message: errorMessage || null,
  file: {
    original_name: 'document.pdf',
  },
});

// Mock progress simulation with automatic advancement
class MockProgressSimulator {
  private static instances: Map<string, MockProgressSimulator> = new Map();
  private progressStates = [
    { status: 'pending' as JobStatus, progress: 0, duration: 1000 },
    { status: 'processing' as JobStatus, progress: 10, duration: 2000 },
    { status: 'extracting' as JobStatus, progress: 25, duration: 3000 },
    { status: 'extracting' as JobStatus, progress: 40, duration: 2000 },
    { status: 'translating' as JobStatus, progress: 55, duration: 4000 },
    { status: 'translating' as JobStatus, progress: 70, duration: 3000 },
    { status: 'building' as JobStatus, progress: 85, duration: 2000 },
    { status: 'building' as JobStatus, progress: 95, duration: 1500 },
    { status: 'done' as JobStatus, progress: 100, duration: 500 },
  ];
  
  private currentIndex = 0;
  private jobId: string;
  private timeoutId: NodeJS.Timeout | null = null;
  private jobData: TranslationJob;

  constructor(jobId: string, initialJob: TranslationJob) {
    this.jobId = jobId;
    this.jobData = { ...initialJob };
    this.startSimulation();
  }

  static getInstance(jobId: string, initialJob?: TranslationJob): MockProgressSimulator {
    if (!this.instances.has(jobId) && initialJob) {
      this.instances.set(jobId, new MockProgressSimulator(jobId, initialJob));
    }
    return this.instances.get(jobId)!;
  }

  static cleanup(jobId: string) {
    const instance = this.instances.get(jobId);
    if (instance) {
      instance.stop();
      this.instances.delete(jobId);
    }
  }

  private startSimulation() {
    this.scheduleNextUpdate();
  }

  private scheduleNextUpdate() {
    if (this.currentIndex >= this.progressStates.length) {
      return; // Simulation complete
    }

    const currentState = this.progressStates[this.currentIndex];
    
    this.timeoutId = setTimeout(() => {
      // Update job data
      this.jobData = createMockJobStatus(
        this.jobId, 
        currentState.status, 
        currentState.progress
      );
      
      console.log(`[Mock Progress] Job ${this.jobId}: ${currentState.status} - ${currentState.progress}%`);
      
      // Move to next state
      this.currentIndex++;
      
      // Schedule next update if not complete
      if (this.currentIndex < this.progressStates.length) {
        this.scheduleNextUpdate();
      } else {
        // Cleanup when done
        MockProgressSimulator.cleanup(this.jobId);
      }
    }, currentState.duration);
  }

  getCurrentStatus(): TranslationJob {
    return { ...this.jobData };
  }

  stop() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
  }
}

// Upload Service
export class UploadService {
  async getSignedUrl(filename: string, contentType: string): Promise<SignedUrlResponse> {
    if (isDevelopment) {
      // Mock signed URL response
      await delay(500);
      return {
        upload_url: 'https://mock-upload-url.com/upload',
        job_id: `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        expires_at: new Date(Date.now() + 3600000).toISOString(), // 1 hour from now
        max_file_size: 20 * 1024 * 1024,
      } as unknown as SignedUrlResponse;
    }

    try {
      const response = await apiClient.post<SignedUrlResponse>('/api/upload/signed-url', {
        filename,
        content_type: contentType,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get signed URL:', error);
      throw error;
    }
  }

  async uploadToSignedUrl(
    signedUrl: string,
    file: File,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<void> {
    if (isDevelopment) {
      // Mock upload with progress
      const totalSteps = 10;
      for (let i = 0; i <= totalSteps; i++) {
        await delay(200);
        const progress = Math.round((i / totalSteps) * 100);
        onProgress?.({
          loaded: (file.size * progress) / 100,
          total: file.size,
          percentage: progress,
        });
      }
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Use fetch for direct upload to signed URL (bypasses our API client)
      const response = await fetch(signedUrl, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type,
        },
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to upload to signed URL:', error);
      throw error;
    }
  }

  async confirmUpload(jobId: string): Promise<TranslationJob> {
    if (isDevelopment) {
      await delay(300);
      const mockJob = createMockJob(jobId, 'document.pdf');
      console.log(`[Mock] Created job: ${mockJob.job_id}`);
      return mockJob;
    }

    try {
      const response = await apiClient.post('/api/upload/confirm', {
        job_id: jobId,
      });

      // The confirm endpoint returns a slim payload (job_id, status, progress).
      // Convert it to a TranslationJob so the rest of the app can use it safely.
      const data = response.data as any;
      return {
        job_id: data.job_id ?? jobId,
        status: data.status ?? 'processing',
        progress: data.progress ?? 0,
        error_message: data.error_message ?? null,
        file: {
          // We don't have file info at this stage, but the type requires it.
          original_name: 'unknown',
        },
      } as TranslationJob;
    } catch (error) {
      console.error('Failed to confirm upload:', error);
      throw error;
    }
  }

  async uploadFile(
    file: File,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<{ job: TranslationJob }> {
    try {
      // Step 1: Get signed URL
      const signedUrlResponse = await this.getSignedUrl(file.name, file.type);
      
      // Step 2: Upload file to signed URL
      await this.uploadToSignedUrl(signedUrlResponse.upload_url, file, onProgress);
      
      // Step 3: Confirm upload and get job
      const job = await this.confirmUpload(signedUrlResponse.job_id);
      
      return { job };
    } catch (error) {
      console.error('Upload process failed:', error);
      throw error;
    }
  }

  async getJobStatus(jobId: string): Promise<TranslationJob> {
    if (isDevelopment) {
      await delay(300); // Shorter delay for more responsive polling
      
      // Get or create simulator instance
      const simulator = MockProgressSimulator.getInstance(jobId);
      if (simulator) {
        return simulator.getCurrentStatus();
      }
      
      // Fallback if no simulator found (shouldn't happen in normal flow)
      console.warn(`[Mock] No simulator found for job ${jobId}, creating fallback`);
      return createMockJobStatus(jobId, 'pending', 0);
    }

    try {
      const response = await apiClient.get<TranslationJob>(`/api/upload/status/${jobId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get job status:', error);
      throw error;
    }
  }
}

// Translation Service
export class TranslationService {
  async startTranslation(jobId: string): Promise<TranslationJob> {
    if (isDevelopment) {
      await delay(800);
      
      // Create initial job for the simulator
      const initialJob = createMockJobStatus(jobId, 'pending', 0);
      
      // Start the progress simulator
      MockProgressSimulator.getInstance(jobId, initialJob);
      
      console.log(`[Mock] Started translation simulation for job: ${jobId}`);
      return initialJob;
    }

    try {
      const response = await apiClient.post<TranslationJob>(`/api/translate/start/${jobId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to start translation:', error);
      throw error;
    }
  }
}

// Download Service
export class DownloadService {
  async getDownloadUrl(jobId: string): Promise<DownloadUrlResponse> {
    if (isDevelopment) {
      await delay(300);
      return {
        download_url: 'https://mock-download-url.com/download',
        expires_at: new Date(Date.now() + 3600000).toISOString(),
        filename: 'document_translated.pdf',
      };
    }

    try {
      const response = await apiClient.get<DownloadUrlResponse>(`/api/download/job/${jobId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get download URL:', error);
      throw error;
    }
  }

  async downloadFile(jobId: string, filename?: string): Promise<void> {
    if (isDevelopment) {
      // Mock download - create a fake PDF blob and trigger download
      await delay(500);
      
      const mockPdfContent = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Mock Translated Document) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF`;

      const blob = new Blob([mockPdfContent], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || 'translated_document.pdf';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      // Cleanup simulator after download
      MockProgressSimulator.cleanup(jobId);
      return;
    }

    try {
      const downloadResponse = await this.getDownloadUrl(jobId);
      
      // Download the file
      const response = await fetch(downloadResponse.download_url);
      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || downloadResponse.filename || 'translated_document.pdf';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download file:', error);
      throw error;
    }
  }
}

// Export service instances
export const translationApi = {
  upload: new UploadService(),
  translation: new TranslationService(),
  download: new DownloadService(),
};