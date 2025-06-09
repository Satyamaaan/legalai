import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { translationApi } from '@/services/translation-api';
import {
  TranslationJob,
  UploadProgress,
} from '@/types/api';
import { useToast } from '@/hooks/use-toast';
import { useCallback, useRef } from 'react';

// Query Keys
export const queryKeys = {
  job: (id: string) => ['jobs', id] as const,
};

// Upload Hooks
export function useUploadFile() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const abortControllerRef = useRef<AbortController | null>(null);

  const mutation = useMutation({
    mutationFn: async ({
      file,
      onProgress,
    }: {
      file: File;
      onProgress?: (progress: UploadProgress) => void;
    }) => {
      // Create abort controller for cancellation
      abortControllerRef.current = new AbortController();
      
      return translationApi.upload.uploadFile(file, onProgress);
    },
    onSuccess: (data) => {
      // Cache the job data
      queryClient.setQueryData(queryKeys.job(data.job.job_id), data.job);
    },
    onError: (error) => {
      console.error('Upload failed:', error);
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

// Translation Hooks
export function useStartTranslation() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (jobId: string) => translationApi.translation.startTranslation(jobId),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.job(data.job_id), data);
    },
    onError: (error) => {
      console.error('Failed to start translation:', error);
    },
  });
}

export function useJobStatus(jobId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.job(jobId),
    queryFn: () => translationApi.upload.getJobStatus(jobId),
    enabled: enabled && !!jobId,
    refetchInterval: (data) => {
      // Poll every 3 seconds for active jobs
      if (data?.status === 'processing' || 
          data?.status === 'pending' || 
          data?.status === 'extracting' || 
          data?.status === 'translating' || 
          data?.status === 'building') {
        return 3000; // 3 seconds as requested
      }
      return false; // Stop polling when done or error
    },
    staleTime: 1000, // 1 second
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
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
    enabled: enabled && !!jobId,
    staleTime: 300000, // 5 minutes
  });
}