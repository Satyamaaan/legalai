import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  Download, 
  CheckCircle, 
  FileText, 
  ExternalLink, 
  Copy, 
  Loader2,
  Eye,
  Calendar,
  HardDrive
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

interface DownloadCardProps {
  downloadUrl: string;
  filename: string;
  fileSize?: number;
  onDownload?: () => void;
  isDownloading?: boolean;
  completedAt?: string;
  originalFilename?: string;
  translatedFrom?: string;
  translatedTo?: string;
}

export function DownloadCard({ 
  downloadUrl, 
  filename, 
  fileSize,
  onDownload,
  isDownloading = false,
  completedAt,
  originalFilename,
  translatedFrom = 'English',
  translatedTo = 'Spanish'
}: DownloadCardProps) {
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [isCopying, setIsCopying] = useState(false);
  const { toast } = useToast();

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleDownload = async () => {
    try {
      onDownload?.();
      
      // Simulate download progress
      setDownloadProgress(0);
      for (let i = 0; i <= 100; i += 10) {
        setDownloadProgress(i);
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      // Create download link
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast({
        title: "Download started",
        description: `${filename} is being downloaded.`,
      });
      
      setDownloadProgress(0);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Download failed",
        description: "There was an error downloading the file. Please try again.",
      });
      setDownloadProgress(0);
    }
  };

  const handleViewInBrowser = () => {
    window.open(downloadUrl, '_blank', 'noopener,noreferrer');
    toast({
      title: "Opening in browser",
      description: "The document will open in a new tab.",
    });
  };

  const handleCopyLink = async () => {
    setIsCopying(true);
    try {
      await navigator.clipboard.writeText(downloadUrl);
      toast({
        title: "Link copied",
        description: "Download link has been copied to your clipboard.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Copy failed",
        description: "Unable to copy link to clipboard.",
      });
    } finally {
      setIsCopying(false);
    }
  };

  return (
    <Card className="w-full border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-950/20 transition-all duration-200 hover:shadow-md">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-12 h-12 rounded-full bg-green-100 dark:bg-green-950/40">
              <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <CardTitle className="text-lg text-green-800 dark:text-green-200">
                Translation Complete
              </CardTitle>
              <p className="text-sm text-green-700 dark:text-green-300">
                Your document is ready for download
              </p>
            </div>
          </div>
          <Badge variant="default" className="bg-green-600 hover:bg-green-700">
            Ready
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* File Information */}
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-white dark:bg-slate-800 border">
              <FileText className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm truncate" title={filename}>
                {filename}
              </p>
              <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1">
                {fileSize && (
                  <div className="flex items-center gap-1">
                    <HardDrive className="h-3 w-3" />
                    {formatFileSize(fileSize)}
                  </div>
                )}
                {completedAt && (
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatTimestamp(completedAt)}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Translation Details */}
          {originalFilename && (
            <>
              <Separator />
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Translation Details
                </p>
                <div className="grid grid-cols-1 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Original:</span>
                    <span className="font-medium truncate ml-2" title={originalFilename}>
                      {originalFilename}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Language:</span>
                    <span className="font-medium">
                      {translatedFrom} → {translatedTo}
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Download Progress */}
        {(isDownloading || downloadProgress > 0) && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Downloading...</span>
              <span className="text-green-600 dark:text-green-400 font-medium">
                {downloadProgress}%
              </span>
            </div>
            <Progress 
              value={downloadProgress} 
              className="h-2"
            />
          </div>
        )}

        <Separator />

        {/* Action Buttons */}
        <div className="space-y-3">
          {/* Primary Download Button */}
          <Button
            onClick={handleDownload}
            disabled={isDownloading || downloadProgress > 0}
            className="w-full bg-green-600 hover:bg-green-700 text-white"
            size="lg"
          >
            {isDownloading || downloadProgress > 0 ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Downloading...
              </>
            ) : (
              <>
                <Download className="h-4 w-4 mr-2" />
                Download PDF
              </>
            )}
          </Button>

          {/* Secondary Actions */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              onClick={handleViewInBrowser}
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
            >
              <Eye className="h-3 w-3" />
              Preview
            </Button>
            
            <Button
              onClick={handleCopyLink}
              disabled={isCopying}
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
            >
              {isCopying ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
              Copy Link
            </Button>
          </div>
        </div>

        {/* Additional Info */}
        <div className="p-3 rounded-lg bg-green-100/50 dark:bg-green-950/30 border border-green-200 dark:border-green-800">
          <div className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-green-800 dark:text-green-200">
              <p className="font-medium">Quality Assured</p>
              <p className="text-green-700 dark:text-green-300 mt-0.5">
                This translation has been reviewed and certified by our professional translators.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}