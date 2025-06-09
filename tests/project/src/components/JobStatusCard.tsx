import React, { useState } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { 
  FileText, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  Loader2, 
  RotateCcw, 
  X,
  Calendar
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface JobStatusCardProps {
  job: {
    id: string;
    status: 'pending' | 'processing' | 'done' | 'error';
    progress: number;
    error_message?: string;
    created_at: string;
    filename: string;
    file_size?: number;
  };
  onRetry?: (jobId: string) => void;
  onCancel?: (jobId: string) => void;
}

const statusConfig = {
  pending: {
    label: 'Pending',
    variant: 'secondary' as const,
    color: 'text-yellow-600 dark:text-yellow-400',
    bgColor: 'bg-yellow-50 dark:bg-yellow-950/20',
    borderColor: 'border-yellow-200 dark:border-yellow-800',
    icon: Clock,
  },
  processing: {
    label: 'Processing',
    variant: 'default' as const,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-950/20',
    borderColor: 'border-blue-200 dark:border-blue-800',
    icon: Loader2,
  },
  done: {
    label: 'Completed',
    variant: 'default' as const,
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-50 dark:bg-green-950/20',
    borderColor: 'border-green-200 dark:border-green-800',
    icon: CheckCircle,
  },
  error: {
    label: 'Error',
    variant: 'destructive' as const,
    color: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-50 dark:bg-red-950/20',
    borderColor: 'border-red-200 dark:border-red-800',
    icon: AlertTriangle,
  },
} as const;

export function JobStatusCard({ job, onRetry, onCancel }: JobStatusCardProps) {
  const [isRetrying, setIsRetrying] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  const config = statusConfig[job.status];
  const StatusIcon = config.icon;

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleRetry = async () => {
    if (!onRetry) return;
    setIsRetrying(true);
    try {
      await onRetry(job.id);
    } finally {
      setIsRetrying(false);
    }
  };

  const handleCancel = async () => {
    if (!onCancel) return;
    setIsCancelling(true);
    try {
      await onCancel(job.id);
    } finally {
      setIsCancelling(false);
    }
  };

  const getProgressColor = () => {
    if (job.status === 'error') return 'bg-red-500';
    if (job.status === 'done') return 'bg-green-500';
    return 'bg-blue-500';
  };

  return (
    <Card className={cn(
      'w-full transition-all duration-200 hover:shadow-md',
      config.borderColor
    )}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm text-muted-foreground">
                Job #{job.id.slice(-8).toUpperCase()}
              </h3>
              <Badge variant={config.variant} className="flex items-center gap-1">
                <StatusIcon className={cn(
                  'h-3 w-3',
                  job.status === 'processing' && 'animate-spin'
                )} />
                {config.label}
              </Badge>
            </div>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" />
              {formatTimestamp(job.created_at)}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* File Information */}
        <div className="flex items-start gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-muted">
            <FileText className="h-5 w-5 text-muted-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-sm truncate" title={job.filename}>
              {job.filename}
            </p>
            {job.file_size && (
              <p className="text-xs text-muted-foreground">
                {formatFileSize(job.file_size)}
              </p>
            )}
          </div>
        </div>

        <Separator />

        {/* Progress Section */}
        {(job.status === 'processing' || job.status === 'done') && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Progress</span>
              <span className={cn('font-medium', config.color)}>
                {job.progress}%
              </span>
            </div>
            <Progress 
              value={job.progress} 
              className="h-2"
              style={{
                '--progress-background': getProgressColor(),
              } as React.CSSProperties}
            />
            {job.status === 'processing' && (
              <p className="text-xs text-muted-foreground">
                Processing your document...
              </p>
            )}
          </div>
        )}

        {/* Pending State */}
        {job.status === 'pending' && (
          <div className={cn(
            'p-3 rounded-lg border',
            config.bgColor,
            config.borderColor
          )}>
            <div className="flex items-center gap-2">
              <Clock className={cn('h-4 w-4', config.color)} />
              <p className="text-sm font-medium">Waiting in queue</p>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Your job will start processing shortly
            </p>
          </div>
        )}

        {/* Error State */}
        {job.status === 'error' && job.error_message && (
          <div className={cn(
            'p-3 rounded-lg border',
            config.bgColor,
            config.borderColor
          )}>
            <div className="flex items-start gap-2">
              <AlertTriangle className={cn('h-4 w-4 mt-0.5 flex-shrink-0', config.color)} />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  Processing Failed
                </p>
                <p className="text-xs text-red-700 dark:text-red-300 mt-1">
                  {job.error_message}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Success State */}
        {job.status === 'done' && (
          <div className={cn(
            'p-3 rounded-lg border',
            config.bgColor,
            config.borderColor
          )}>
            <div className="flex items-center gap-2">
              <CheckCircle className={cn('h-4 w-4', config.color)} />
              <p className="text-sm font-medium text-green-800 dark:text-green-200">
                Translation completed successfully
              </p>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Your document is ready for download
            </p>
          </div>
        )}

        {/* Action Buttons */}
        {(job.status === 'error' || job.status === 'processing') && (
          <div className="flex gap-2 pt-2">
            {job.status === 'error' && onRetry && (
              <Button
                onClick={handleRetry}
                disabled={isRetrying}
                size="sm"
                className="flex items-center gap-2"
              >
                {isRetrying ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <RotateCcw className="h-3 w-3" />
                )}
                {isRetrying ? 'Retrying...' : 'Retry'}
              </Button>
            )}
            
            {(job.status === 'processing' || job.status === 'error') && onCancel && (
              <Button
                onClick={handleCancel}
                disabled={isCancelling}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                {isCancelling ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <X className="h-3 w-3" />
                )}
                {isCancelling ? 'Cancelling...' : 'Cancel'}
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}