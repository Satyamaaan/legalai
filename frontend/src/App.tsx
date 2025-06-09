import React, { useState, useEffect } from 'react';
import { AppLayout } from '@/components/AppLayout';
import { UploadDropzone } from '@/components/UploadDropzone';
import { ModalProgress } from '@/components/ModalProgress';
import { DownloadCard } from '@/components/DownloadCard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { FileText, Languages, Shield, Play, RotateCcw, RefreshCw } from 'lucide-react';
import { useUploadFile, useStartTranslation, useJobStatus, useDownloadFile } from '@/hooks/use-translation-api';
import { JobStatus } from '@/types/api';

type AppState = 'upload' | 'processing' | 'completed' | 'error';

interface CompletedJob {
  id: string;
  filename: string;
  originalFilename: string;
  fileSize: number;
  completedAt: string;
  translatedFrom: string;
  translatedTo: string;
  downloadUrl: string;
}

function App() {
  const [appState, setAppState] = useState<AppState>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [completedJob, setCompletedJob] = useState<CompletedJob | null>(null);
  const [error, setError] = useState<string>();

  // API hooks
  const uploadFile = useUploadFile();
  const startTranslation = useStartTranslation();
  const downloadFile = useDownloadFile();
  
  // Job status polling - only when processing
  const { data: jobStatus } = useJobStatus(
    currentJobId || '', 
    !!currentJobId && appState === 'processing'
  );

  // Handle file upload and start the workflow
  const handleFileAccepted = async (file: File) => {
    setSelectedFile(file);
    setError(undefined);
    
    try {
      // Step 1: Upload file (signed-url → direct upload → confirm)
      const result = await uploadFile.mutateAsync({
        file,
        onProgress: (progress) => {
          console.log('Upload progress:', progress);
        }
      });
      
      setCurrentJobId(result.job.job_id);
      
      // Step 2: Start translation immediately after upload
      await startTranslation.mutateAsync(result.job.job_id);
      
      // Step 3: Hide upload, show progress modal
      setAppState('processing');
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload or translation start failed');
      setAppState('error');
    }
  };

  // Handle job status updates from polling
  useEffect(() => {
    if (jobStatus && appState === 'processing') {
      if (jobStatus.status === 'done') {
        // Step 4: When status="done", hide modal and show download card
        const completed: CompletedJob = {
          id: jobStatus.job_id,
          filename: `${jobStatus.file.original_name.replace('.pdf', '')}_translated.pdf`,
          originalFilename: jobStatus.file.original_name,
          fileSize: selectedFile?.size || 0,
          completedAt: new Date().toISOString(),
          translatedFrom: 'English',
          translatedTo: 'Spanish',
          downloadUrl: ''
        };
        
        setCompletedJob(completed);
        setAppState('completed');
      } else if (jobStatus.status === 'error') {
        // Step 5: When status="error", show error in modal
        setError(jobStatus.error_message || 'Translation failed');
        setAppState('error');
      }
    }
  }, [jobStatus, appState, selectedFile?.size]);

  // Get current stage and progress for modal
  const getCurrentStage = (): string => {
    if (!jobStatus) return 'Preparing...';
    
    switch (jobStatus.status) {
      case 'pending':
        return 'Waiting in queue...';
      case 'processing':
        return 'Processing document...';
      case 'extracting':
        return 'Extracting text from PDF...';
      case 'translating':
        return 'Translating document content...';
      case 'building':
        return 'Building translated PDF...';
      default:
        return 'Processing...';
    }
  };

  const getEstimatedTime = (): string | undefined => {
    if (!jobStatus) return undefined;
    
    switch (jobStatus.status) {
      case 'extracting':
        return '2 minutes';
      case 'translating':
        return '1 minute';
      case 'building':
        return '30 seconds';
      default:
        return undefined;
    }
  };

  // Handle download
  const handleDownload = async () => {
    if (!currentJobId) return;
    
    try {
      await downloadFile.mutateAsync({ 
        jobId: currentJobId,
        filename: completedJob?.filename 
      });
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  // Step 6: Reset everything back to step 1
  const resetToUpload = () => {
    setAppState('upload');
    setSelectedFile(null);
    setCurrentJobId(null);
    setCompletedJob(null);
    setError(undefined);
    uploadFile.reset();
    startTranslation.reset();
    downloadFile.reset();
  };

  // Retry translation (for error state)
  const handleRetry = async () => {
    if (!currentJobId) {
      resetToUpload();
      return;
    }
    
    setError(undefined);
    setAppState('processing');
    
    try {
      await startTranslation.mutateAsync(currentJobId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retry translation');
      setAppState('error');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-white">
      <AppLayout title="Document Translation" currentPage="upload" showNavigation={false}>
        {/* Hero Section */}
        <div className="text-center mb-12 section-spacing">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-primary text-primary-foreground">
              <Languages className="h-7 w-7" />
            </div>
            <h1 className="text-4xl font-bold tracking-tight text-foreground">Professional Legal Translation</h1>
          </div>
          <p className="text-lg text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            Secure, accurate translation of legal documents by certified translators. 
            Upload your PDF documents and receive professional translations with guaranteed confidentiality.
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <Card className="text-center modern-card">
            <CardContent className="pt-8 pb-6">
              <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-green-100 text-green-600 mx-auto mb-4">
                <Shield className="h-6 w-6" />
              </div>
              <h3 className="font-semibold text-lg mb-2 text-foreground">Enterprise Security</h3>
              <p className="text-sm text-muted-foreground">End-to-end encryption & SOC 2 compliance</p>
            </CardContent>
          </Card>
          <Card className="text-center modern-card">
            <CardContent className="pt-8 pb-6">
              <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-blue-100 text-blue-600 mx-auto mb-4">
                <FileText className="h-6 w-6" />
              </div>
              <h3 className="font-semibold text-lg mb-2 text-foreground">All PDF Formats</h3>
              <p className="text-sm text-muted-foreground">Complex layouts, forms & scanned documents</p>
            </CardContent>
          </Card>
          <Card className="text-center modern-card">
            <CardContent className="pt-8 pb-6">
              <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-purple-100 text-purple-600 mx-auto mb-4">
                <Languages className="h-6 w-6" />
              </div>
              <h3 className="font-semibold text-lg mb-2 text-foreground">50+ Languages</h3>
              <p className="text-sm text-muted-foreground">Certified legal translators worldwide</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          {/* Upload State - Show only when in upload mode */}
          {appState === 'upload' && (
            <Card className="modern-card">
              <CardHeader>
                <CardTitle className="text-foreground">Upload Document</CardTitle>
                <CardDescription>
                  Upload your legal document for professional translation. We accept PDF files up to 20MB.
                  Translation will start automatically after upload.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <UploadDropzone 
                  onFileAccepted={handleFileAccepted}
                  isLoading={uploadFile.isPending || startTranslation.isPending}
                />
                
                {/* Show upload progress */}
                {uploadFile.isPending && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-2 text-blue-700">
                      <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                      <span className="text-sm font-medium">Uploading document...</span>
                    </div>
                  </div>
                )}
                
                {/* Show translation start */}
                {startTranslation.isPending && (
                  <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <div className="flex items-center gap-2 text-purple-700">
                      <div className="w-4 h-4 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
                      <span className="text-sm font-medium">Starting translation...</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Completed State - Show download card */}
          {appState === 'completed' && completedJob && (
            <div className="max-w-2xl mx-auto">
              <div className="text-center mb-8">
                <div className="flex items-center justify-center w-16 h-16 rounded-full bg-green-100 text-green-600 mx-auto mb-4">
                  <FileText className="h-8 w-8" />
                </div>
                <h2 className="text-2xl font-bold text-foreground mb-2">Translation Complete!</h2>
                <p className="text-muted-foreground">Your document has been successfully translated and is ready for download.</p>
              </div>

              <DownloadCard
                downloadUrl={completedJob.downloadUrl}
                filename={completedJob.filename}
                fileSize={completedJob.fileSize}
                completedAt={completedJob.completedAt}
                originalFilename={completedJob.originalFilename}
                translatedFrom={completedJob.translatedFrom}
                translatedTo={completedJob.translatedTo}
                onDownload={handleDownload}
                isDownloading={downloadFile.isPending}
              />

              <div className="text-center mt-8">
                <Button onClick={resetToUpload} variant="secondary" className="flex items-center gap-2">
                  <RefreshCw className="h-4 w-4" />
                  Translate Another Document
                </Button>
              </div>
            </div>
          )}

          {/* Error State - Show error message with retry */}
          {appState === 'error' && (
            <div className="max-w-2xl mx-auto">
              <Card className="modern-card border-red-200">
                <CardContent className="pt-8 pb-6 text-center">
                  <div className="flex items-center justify-center w-16 h-16 rounded-full bg-red-100 text-red-600 mx-auto mb-4">
                    <FileText className="h-8 w-8" />
                  </div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">Translation Failed</h2>
                  <p className="text-muted-foreground mb-6">
                    {error || 'An error occurred during translation. Please try again.'}
                  </p>
                  <div className="flex gap-3 justify-center">
                    <Button onClick={handleRetry} className="flex items-center gap-2">
                      <RotateCcw className="h-4 w-4" />
                      Try Again
                    </Button>
                    <Button onClick={resetToUpload} variant="secondary" className="flex items-center gap-2">
                      <RefreshCw className="h-4 w-4" />
                      Start Over
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
        
        {/* Progress Modal - Show only during processing */}
        <ModalProgress
          open={appState === 'processing'}
          progress={jobStatus?.progress || 0}
          stage={getCurrentStage()}
          estimatedTimeRemaining={getEstimatedTime()}
          onCancel={resetToUpload}
          error={appState === 'error' ? error : undefined}
          onRetry={handleRetry}
        />
      </AppLayout>
    </div>
  );
}

export default App;