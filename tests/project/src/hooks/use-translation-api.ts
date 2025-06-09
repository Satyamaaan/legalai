import { useMutation, useQuery, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { translationApi } from '@/services/translation-api';
import {
  TranslationJob,
  SignedUrlRequest,
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
import { useToast } from '@/hooks/use-toast';
import { useCallback, useRef } from 'react';

// Query Keys
export const queryKeys = {
  jobs: ['jobs'] as const,
  job: (id: string) => ['jobs', id] as const,
  history: (params?: HistoryRequest) => ['jobs', 'history', params] as const,
  languages: ['languages'] as const,
  languagePairs: ['language-pairs'] as const,
  systemStatus: ['system', 'status'] as const,
  costEstimate: (params: {
    sourceLanguage: string;
    targetLanguage: string;
    fileSize: number;
    translationType: string;
  }) => ['cost-estimate', params] as const,
};

// Upload Hooks
export function useUploadFile() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const abortControllerRef = useRef<AbortController | null>(null);

  const mutation = useMutation({
    mutationFn: async ({
      file,
      request,
      onProgress,
    }: {
      file: File;
      request: Omit<SignedUrlRequest, 'filename' | 'file_size' | 'file_type'>;
      onProgress?: (progress: UploadProgress) => void;
    }) => {
      // Create abort controller for cancellation
      abortControllerRef.current = new AbortController();
      
      return translationApi.upload.uploadFile(file, request, onProgress);
    },
    onSuccess: (data) => {
      // Invalidate and refetch job queries
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs });
      queryClient.setQueryData(queryKeys.job(data.job.id), data.job);
      
      toast({
        title: 'Upload successful',
        description: `${data.job.filename} has been uploaded and is ready for translation.`,
      });
    },
    onError: (error) => {
      console.error('Upload failed:', error);
      toast({
        variant: 'destructive',
        title: 'Upload failed',
        description: error instanceof Error ? error.message : 'Failed to upload file',
      });
    },
  });

  const cancelUpload = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    mutation.reset();
  }, [mutation]);

  return {
    ...mutation,
    cancelUpload,
  };
}

export function useGetSignedUrl() {
  const { toast } = useToast();

  return useMutation({
    mutationFn: translationApi.upload.getSignedUrl,
    onError: (error) => {
      toast({
        variant: 'destructive',
        title: 'Failed to prepare upload',
        description: error instanceof Error ? error.message : 'Could not prepare file upload',
      });
    },
  });
}

// Translation Hooks
export function useStartTranslation() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: translationApi.translation.startTranslation,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs });
      queryClient.setQueryData(queryKeys.job(data.job.id), data.job);
      
      toast({
        title: 'Translation started',
        description: `Translation job ${data.tracking_id} has been started.`,
      });
    },
    onError: (error) => {
      toast({
        variant: 'destructive',
        title: 'Failed to start translation',
        description: error instanceof Error ? error.message : 'Could not start translation',
      });
    },
  });
}

export function useJobStatus(
  jobId: string,
  options?: Omit<UseQueryOptions<TranslationJob>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.job(jobId),
    queryFn: () => translationApi.translation.getJobStatus(jobId),
    refetchInterval: (data) => {
      // Auto-refresh for active jobs
      if (data?.status === 'processing' || data?.status === 'pending') {
        return 5000; // 5 seconds
      }
      return false;
    },
    staleTime: 30000, // 30 seconds
    ...options,
  });
}

export function useRetryJob() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: translationApi.translation.retryJob,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs });
      queryClient.setQueryData(queryKeys.job(data.id), data);
      
      toast({
        title: 'Job retried',
        description: `Translation job ${data.id.slice(-8)} has been restarted.`,
      });
    },
    onError: (error) => {
      toast({
        variant: 'destructive',
        title: 'Failed to retry job',
        description: error instanceof Error ? error.message : 'Could not retry translation',
      });
    },
  });
}

export function useCancelJob() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: translationApi.translation.cancelJob,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs });
      queryClient.setQueryData(queryKeys.job(data.id), data);
      
      toast({
        title: 'Job cancelled',
        description: `Translation job ${data.id.slice(-8)} has been cancelled.`,
      });
    },
    onError: (error) => {
      toast({
        variant: 'destructive',
        title: 'Failed to cancel job',
        description: error instanceof Error ? error.message : 'Could not cancel translation',
      });
    },
  });
}

// Download Hooks
export function useDownloadFile() {
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ jobId, filename }: { jobId: string; filename?: string }) =>
      translationApi.download.downloadFile(jobId, filename),
    onSuccess: () => {
      toast({
        title: 'Download started',
        description: 'Your translated document is being downloaded.',
      });
    },
    onError: (error) => {
      toast({
        variant: 'destructive',
        title: 'Download failed',
        description: error instanceof Error ? error.message : 'Could not download file',
      });
    },
  });
}

export function useGetDownloadUrl(jobId: string, enabled = true) {
  return useQuery({
    queryKey: ['download-url', jobId],
    queryFn: () => translationApi.download.getDownloadUrl(jobId),
    enabled,
    staleTime: 300000, // 5 minutes
  });
}

// History Hooks
export function useJobHistory(
  params: HistoryRequest = {},
  options?: Omit<UseQueryOptions<PaginatedResponse<TranslationJob>>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.history(params),
    queryFn: () => translationApi.history.getHistory(params),
    staleTime: 60000, // 1 minute
    ...options,
  });
}

export function useDeleteJob() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: translationApi.history.deleteJob,
    onSuccess: (_, jobId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs });
      queryClient.removeQueries({ queryKey: queryKeys.job(jobId) });
      
      toast({
        title: 'Job deleted',
        description: 'Translation job has been removed from your history.',
      });
    },
    onError: (error) => {
      toast({
        variant: 'destructive',
        title: 'Failed to delete job',
        description: error instanceof Error ? error.message : 'Could not delete job',
      });
    },
  });
}

export function useBulkDeleteJobs() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: translationApi.history.bulkDeleteJobs,
    onSuccess: (_, jobIds) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs });
      jobIds.forEach(jobId => {
        queryClient.removeQueries({ queryKey: queryKeys.job(jobId) });
      });
      
      toast({
        title: 'Jobs deleted',
        description: `${jobIds.length} translation jobs have been removed.`,
      });
    },
    onError: (error) => {
      toast({
        variant: 'destructive',
        title: 'Failed to delete jobs',
        description: error instanceof Error ? error.message : 'Could not delete selected jobs',
      });
    },
  });
}

// Language Hooks
export function useLanguages() {
  return useQuery({
    queryKey: queryKeys.languages,
    queryFn: translationApi.translation.getLanguages,
    staleTime: 3600000, // 1 hour
    cacheTime: 3600000, // 1 hour
  });
}

export function useLanguagePairs() {
  return useQuery({
    queryKey: queryKeys.languagePairs,
    queryFn: translationApi.translation.getLanguagePairs,
    staleTime: 3600000, // 1 hour
    cacheTime: 3600000, // 1 hour
  });
}

export function useCostEstimate(
  sourceLanguage: string,
  targetLanguage: string,
  fileSize: number,
  translationType: 'standard' | 'certified' | 'notarized',
  enabled = true
) {
  return useQuery({
    queryKey: queryKeys.costEstimate({
      sourceLanguage,
      targetLanguage,
      fileSize,
      translationType,
    }),
    queryFn: () =>
      translationApi.translation.getCostEstimate(
        sourceLanguage,
        targetLanguage,
        fileSize,
        translationType
      ),
    enabled: enabled && !!sourceLanguage && !!targetLanguage && fileSize > 0,
    staleTime: 300000, // 5 minutes
  });
}

// System Hooks
export function useSystemStatus() {
  return useQuery({
    queryKey: queryKeys.systemStatus,
    queryFn: translationApi.system.getStatus,
    refetchInterval: 60000, // 1 minute
    staleTime: 30000, // 30 seconds
  });
}

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health-check'],
    queryFn: translationApi.system.healthCheck,
    refetchInterval: 30000, // 30 seconds
    retry: 3,
    retryDelay: 1000,
  });
}

// Polling Hook for Multiple Jobs
export function useJobsPolling(jobIds: string[], enabled = true) {
  const queryClient = useQueryClient();

  return useQuery({
    queryKey: ['jobs-polling', jobIds],
    queryFn: async () => {
      const jobs = await Promise.all(
        jobIds.map(id => translationApi.translation.getJobStatus(id))
      );
      
      // Update individual job caches
      jobs.forEach(job => {
        queryClient.setQueryData(queryKeys.job(job.id), job);
      });
      
      return jobs;
    },
    enabled: enabled && jobIds.length > 0,
    refetchInterval: (data) => {
      // Stop polling if all jobs are completed
      const hasActiveJobs = data?.some(job => 
        job.status === 'processing' || job.status === 'pending'
      );
      return hasActiveJobs ? 5000 : false;
    },
    staleTime: 10000, // 10 seconds
  });
}