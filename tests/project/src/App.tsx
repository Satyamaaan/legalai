import React, { useState } from 'react';
import { AppLayout } from '@/components/AppLayout';
import { UploadDropzone } from '@/components/UploadDropzone';
import { ModalProgress } from '@/components/ModalProgress';
import { JobStatusCard } from '@/components/JobStatusCard';
import { DownloadCard } from '@/components/DownloadCard';
import { HistoryPage } from '@/components/HistoryPage';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FileText, Languages, Shield, Play, RotateCcw, History, Upload } from 'lucide-react';

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showProgress, setShowProgress] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [estimatedTime, setEstimatedTime] = useState<string>();
  const [error, setError] = useState<string>();
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [currentTab, setCurrentTab] = useState('upload');

  // Sample job data for demonstration
  const [jobs] = useState([
    {
      id: 'job_abc123def456',
      status: 'done' as const,
      progress: 100,
      created_at: '2024-01-15T10:30:00Z',
      filename: 'contract_agreement.pdf',
      file_size: 2456789,
      source_language: 'English',
      target_language: 'Spanish',
      completed_at: '2024-01-15T10:45:00Z',
    },
    {
      id: 'job_xyz789uvw012',
      status: 'processing' as const,
      progress: 65,
      created_at: '2024-01-15T11:15:00Z',
      filename: 'legal_document_translation.pdf',
      file_size: 1234567,
      source_language: 'English',
      target_language: 'French',
    },
    {
      id: 'job_mno345pqr678',
      status: 'error' as const,
      progress: 25,
      error_message: 'Failed to extract text from PDF. The document may be corrupted or password-protected.',
      created_at: '2024-01-15T09:45:00Z',
      filename: 'encrypted_document.pdf',
      file_size: 987654,
      source_language: 'English',
      target_language: 'German',
    },
    {
      id: 'job_stu901vwx234',
      status: 'pending' as const,
      progress: 0,
      created_at: '2024-01-15T11:45:00Z',
      filename: 'terms_and_conditions.pdf',
      file_size: 3456789,
      source_language: 'English',
      target_language: 'Italian',
    },
    {
      id: 'job_def456ghi789',
      status: 'done' as const,
      progress: 100,
      created_at: '2024-01-14T16:20:00Z',
      filename: 'privacy_policy.pdf',
      file_size: 1890456,
      source_language: 'English',
      target_language: 'French',
      completed_at: '2024-01-14T16:35:00Z',
    },
    {
      id: 'job_jkl012mno345',
      status: 'done' as const,
      progress: 100,
      created_at: '2024-01-14T14:10:00Z',
      filename: 'user_manual.pdf',
      file_size: 5432109,
      source_language: 'English',
      target_language: 'Spanish',
      completed_at: '2024-01-14T14:30:00Z',
    },
    {
      id: 'job_pqr678stu901',
      status: 'error' as const,
      progress: 15,
      error_message: 'Unsupported file format detected. Please ensure the PDF is not password-protected.',
      created_at: '2024-01-14T12:05:00Z',
      filename: 'technical_specifications.pdf',
      file_size: 2109876,
      source_language: 'English',
      target_language: 'Japanese',
    },
    {
      id: 'job_vwx234yza567',
      status: 'done' as const,
      progress: 100,
      created_at: '2024-01-13T09:30:00Z',
      filename: 'financial_report.pdf',
      file_size: 3765432,
      source_language: 'English',
      target_language: 'German',
      completed_at: '2024-01-13T09:50:00Z',
    },
  ]);

  // Sample completed downloads
  const [completedDownloads] = useState([
    {
      downloadUrl: 'https://example.com/downloads/contract_agreement_es.pdf',
      filename: 'contract_agreement_spanish.pdf',
      fileSize: 2567890,
      completedAt: '2024-01-15T10:45:00Z',
      originalFilename: 'contract_agreement.pdf',
      translatedFrom: 'English',
      translatedTo: 'Spanish',
    },
    {
      downloadUrl: 'https://example.com/downloads/privacy_policy_fr.pdf',
      filename: 'privacy_policy_french.pdf',
      fileSize: 1890456,
      completedAt: '2024-01-14T16:20:00Z',
      originalFilename: 'privacy_policy.pdf',
      translatedFrom: 'English',
      translatedTo: 'French',
    },
  ]);

  const handleFileAccepted = async (file: File) => {
    setSelectedFile(file);
    setIsProcessing(true);
    
    // Simulate file processing
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setIsProcessing(false);
  };

  const simulateProcessing = async () => {
    setShowProgress(true);
    setProgress(0);
    setError(undefined);
    
    // Stage 1: OCR Extraction (0-40%)
    setStage('Extracting text from PDF...');
    setEstimatedTime('2 minutes');
    
    for (let i = 0; i <= 40; i += 2) {
      setProgress(i);
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // Stage 2: Translation (40-70%)
    setStage('Translating document content...');
    setEstimatedTime('1 minute');
    
    for (let i = 40; i <= 70; i += 2) {
      setProgress(i);
      await new Promise(resolve => setTimeout(resolve, 80));
    }
    
    // Stage 3: PDF Building (70-100%)
    setStage('Building translated PDF...');
    setEstimatedTime('30 seconds');
    
    for (let i = 70; i <= 100; i += 3) {
      setProgress(i);
      await new Promise(resolve => setTimeout(resolve, 60));
    }
    
    // Complete
    await new Promise(resolve => setTimeout(resolve, 500));
    setShowProgress(false);
    setProgress(0);
  };

  const simulateError = async () => {
    setShowProgress(true);
    setProgress(0);
    setError(undefined);
    
    // Start processing
    setStage('Extracting text from PDF...');
    setEstimatedTime('2 minutes');
    
    for (let i = 0; i <= 25; i += 5) {
      setProgress(i);
      await new Promise(resolve => setTimeout(resolve, 200));
    }
    
    // Simulate error
    setError('Failed to extract text from PDF. The document may be corrupted or password-protected.');
  };

  const handleCancel = () => {
    setShowProgress(false);
    setProgress(0);
    setError(undefined);
  };

  const handleRetry = () => {
    setError(undefined);
    simulateProcessing();
  };

  const handleJobRetry = async (jobId: string) => {
    console.log('Retrying job:', jobId);
    // Simulate retry delay
    await new Promise(resolve => setTimeout(resolve, 1000));
  };

  const handleJobCancel = async (jobId: string) => {
    console.log('Cancelling job:', jobId);
    // Simulate cancel delay
    await new Promise(resolve => setTimeout(resolve, 500));
  };

  const handleDownload = (jobId?: string) => {
    console.log('Download initiated for job:', jobId);
  };

  const handleHistoryRefresh = async () => {
    setIsHistoryLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsHistoryLoading(false);
  };

  const handleHistoryDelete = async (jobId: string) => {
    console.log('Deleting job:', jobId);
    // Simulate delete delay
    await new Promise(resolve => setTimeout(resolve, 500));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getPageTitle = () => {
    switch (currentTab) {
      case 'history':
        return 'Translation History';
      case 'upload':
      default:
        return 'Document Translation';
    }
  };

  const getCurrentPage = () => {
    switch (currentTab) {
      case 'history':
        return 'history';
      case 'upload':
      default:
        return 'upload';
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <AppLayout 
        title={getPageTitle()}
        currentPage={getCurrentPage()}
      >
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

        {/* Main Content Tabs */}
        <Tabs value={currentTab} onValueChange={setCurrentTab} className="content-spacing">
          <TabsList className="grid w-full grid-cols-2 max-w-md mx-auto">
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Upload & Process
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2">
              <History className="h-4 w-4" />
              Translation History
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="element-spacing">
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
              {/* Left Column - Upload and Demo */}
              <div className="element-spacing">
                {/* Upload Section */}
                <Card className="modern-card">
                  <CardHeader>
                    <CardTitle className="text-foreground">Upload Document</CardTitle>
                    <CardDescription>
                      Upload your legal document for professional translation. We accept PDF files up to 20MB.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <UploadDropzone 
                      onFileAccepted={handleFileAccepted}
                      isLoading={isProcessing}
                    />
                  </CardContent>
                </Card>

                {/* File Info */}
                {selectedFile && (
                  <Card className="modern-card">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-foreground">
                        <FileText className="h-5 w-5" />
                        Selected Document
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="element-spacing">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-foreground">{selectedFile.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {formatFileSize(selectedFile.size)} • PDF Document
                            </p>
                          </div>
                          <Badge variant="secondary" className="status-success">Ready</Badge>
                        </div>
                        
                        <Separator />
                        
                        <div className="text-sm text-muted-foreground">
                          <p className="mb-3 font-medium text-foreground">
                            Next steps:
                          </p>
                          <ol className="list-decimal list-inside space-y-2 ml-4">
                            <li>Select target language</li>
                            <li>Choose certification level</li>
                            <li>Review translation options</li>
                            <li>Submit for processing</li>
                          </ol>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Demo Section */}
                <Card className="modern-card">
                  <CardHeader>
                    <CardTitle className="text-foreground">Demo Progress Modal</CardTitle>
                    <CardDescription>
                      Test the progress modal component with different scenarios.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-3">
                      <Button onClick={simulateProcessing} className="flex items-center gap-2">
                        <Play className="h-4 w-4" />
                        Start Processing
                      </Button>
                      <Button onClick={simulateError} variant="secondary" className="flex items-center gap-2">
                        <RotateCcw className="h-4 w-4" />
                        Simulate Error
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Middle Column - Job Status Cards */}
              <div className="element-spacing">
                <Card className="modern-card">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-foreground">
                      <FileText className="h-5 w-5" />
                      Recent Jobs
                    </CardTitle>
                    <CardDescription>
                      Track the status of your recent translation jobs.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="element-spacing">
                      {jobs.slice(0, 4).map((job) => (
                        <JobStatusCard
                          key={job.id}
                          job={job}
                          onRetry={handleJobRetry}
                          onCancel={handleJobCancel}
                        />
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Right Column - Download Cards */}
              <div className="element-spacing">
                <Card className="modern-card">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-foreground">
                      <FileText className="h-5 w-5" />
                      Completed Translations
                    </CardTitle>
                    <CardDescription>
                      Download your completed translation documents.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="element-spacing">
                      {completedDownloads.map((download, index) => (
                        <DownloadCard
                          key={index}
                          downloadUrl={download.downloadUrl}
                          filename={download.filename}
                          fileSize={download.fileSize}
                          completedAt={download.completedAt}
                          originalFilename={download.originalFilename}
                          translatedFrom={download.translatedFrom}
                          translatedTo={download.translatedTo}
                          onDownload={() => handleDownload()}
                        />
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="history">
            <HistoryPage
              jobs={jobs}
              isLoading={isHistoryLoading}
              onRefresh={handleHistoryRefresh}
              onDownload={handleDownload}
              onRetry={handleJobRetry}
              onDelete={handleHistoryDelete}
            />
          </TabsContent>
        </Tabs>
        
        <ModalProgress
          open={showProgress}
          progress={progress}
          stage={stage}
          estimatedTimeRemaining={estimatedTime}
          onCancel={handleCancel}
          error={error}
          onRetry={handleRetry}
        />
      </AppLayout>
    </div>
  );
}

export default App;