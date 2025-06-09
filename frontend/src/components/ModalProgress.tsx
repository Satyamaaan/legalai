import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, FileText, Languages, Download, X, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ModalProgressProps {
  open: boolean;
  progress: number; // 0-100
  stage: string;
  estimatedTimeRemaining?: string;
  onCancel?: () => void;
  error?: string;
  onRetry?: () => void;
}

const stageIcons = {
  'pending': Loader2,
  'processing': Loader2,
  'extracting': FileText,
  'translating': Languages,
  'building': Download,
  'error': AlertTriangle,
} as const;

const stageColors = {
  'pending': 'text-yellow-600',
  'processing': 'text-blue-600',
  'extracting': 'text-blue-600',
  'translating': 'text-purple-600',
  'building': 'text-green-600',
  'error': 'text-red-600',
} as const;

export function ModalProgress({ 
  open, 
  progress, 
  stage, 
  estimatedTimeRemaining, 
  onCancel,
  error,
  onRetry 
}: ModalProgressProps) {
  const [displayProgress, setDisplayProgress] = useState(0);
  const [isIndeterminate, setIsIndeterminate] = useState(true);

  // Smooth progress animation
  useEffect(() => {
    if (progress > 0) {
      setIsIndeterminate(false);
      const timer = setTimeout(() => {
        setDisplayProgress(progress);
      }, 100);
      return () => clearTimeout(timer);
    } else {
      setIsIndeterminate(true);
      setDisplayProgress(0);
    }
  }, [progress]);

  // Get stage icon and color based on stage name
  const getStageIcon = (stageName: string) => {
    const lowerStage = stageName.toLowerCase();
    if (error) return stageIcons.error;
    if (lowerStage.includes('pending') || lowerStage.includes('waiting')) return stageIcons.pending;
    if (lowerStage.includes('extract')) return stageIcons.extracting;
    if (lowerStage.includes('translat')) return stageIcons.translating;
    if (lowerStage.includes('build') || lowerStage.includes('generat')) return stageIcons.building;
    return stageIcons.processing;
  };

  const getStageColor = (stageName: string) => {
    const lowerStage = stageName.toLowerCase();
    if (error) return stageColors.error;
    if (lowerStage.includes('pending') || lowerStage.includes('waiting')) return stageColors.pending;
    if (lowerStage.includes('extract')) return stageColors.extracting;
    if (lowerStage.includes('translat')) return stageColors.translating;
    if (lowerStage.includes('build') || lowerStage.includes('generat')) return stageColors.building;
    return stageColors.processing;
  };

  const StageIcon = getStageIcon(stage);
  const stageColor = getStageColor(stage);

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent 
        className="sm:max-w-md w-[95vw] max-w-[400px] p-0 gap-0 border-0 bg-transparent shadow-none"
        hideCloseButton
        onPointerDownOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <DialogTitle className="sr-only">
          {error ? 'Processing Error' : 'Processing Document'}
        </DialogTitle>
        <DialogDescription className="sr-only">
          {error ? 'An error occurred during processing' : 'Please wait while we process your document'}
        </DialogDescription>
        
        <Card className="w-full border shadow-lg modern-card">
          <CardContent className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn(
                  'flex items-center justify-center w-10 h-10 rounded-full',
                  error ? 'bg-red-100' : 'bg-primary/10'
                )}>
                  {error ? (
                    <StageIcon className={cn('w-5 h-5', stageColor)} />
                  ) : (
                    <StageIcon className={cn(
                      'w-5 h-5',
                      (isIndeterminate || StageIcon === Loader2) ? 'animate-spin' : '',
                      stageColor
                    )} />
                  )}
                </div>
                <div>
                  <h3 className="font-semibold text-lg text-foreground">
                    {error ? 'Processing Error' : 'Processing Document'}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {error ? 'An error occurred during processing' : 'Please wait while we process your document'}
                  </p>
                </div>
              </div>
              
              {onCancel && !error && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onCancel}
                  className="h-8 w-8 p-0 hover:bg-muted"
                >
                  <X className="h-4 w-4" />
                  <span className="sr-only">Cancel</span>
                </Button>
              )}
            </div>

            {/* Progress Section */}
            {!error && (
              <div className="space-y-4">
                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-foreground">{displayProgress}%</span>
                    {estimatedTimeRemaining && (
                      <span className="text-muted-foreground">
                        {estimatedTimeRemaining} remaining
                      </span>
                    )}
                  </div>
                  
                  <div className="relative">
                    <Progress 
                      value={isIndeterminate ? undefined : displayProgress} 
                      className="h-2 transition-all duration-500 ease-out"
                    />
                    
                    {/* Indeterminate animation overlay */}
                    {isIndeterminate && (
                      <div className="absolute inset-0 overflow-hidden rounded-full bg-muted">
                        <div className="h-full w-1/3 bg-gradient-to-r from-transparent via-primary to-transparent animate-pulse" 
                             style={{
                               animation: 'shimmer 2s infinite',
                               background: 'linear-gradient(90deg, transparent, hsl(var(--primary)), transparent)',
                             }} 
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Stage Status */}
                <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center justify-center">
                    {isIndeterminate ? (
                      <Loader2 className="w-4 h-4 animate-spin text-primary" />
                    ) : (
                      <div className={cn('w-2 h-2 rounded-full bg-current', stageColor)} />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">{stage}</p>
                    {!isIndeterminate && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Step {Math.ceil(displayProgress / 33)} of 3
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Error Section */}
            {error && (
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-red-50 border border-red-200">
                  <p className="text-sm text-red-800">
                    {error}
                  </p>
                </div>
                
                <div className="flex gap-2 justify-end">
                  {onCancel && (
                    <Button variant="secondary\" onClick={onCancel}>
                      Cancel
                    </Button>
                  )}
                  {onRetry && (
                    <Button onClick={onRetry}>
                      Try Again
                    </Button>
                  )}
                </div>
              </div>
            )}

            {/* Processing Steps Info */}
            {!error && (
              <div className="space-y-2 pt-2 border-t">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Processing Steps
                </p>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className={cn(
                    'flex items-center gap-1.5 p-2 rounded transition-colors',
                    displayProgress >= 15 ? 'bg-blue-50 text-blue-700' : 'text-muted-foreground'
                  )}>
                    <FileText className="w-3 h-3" />
                    <span>Extract</span>
                  </div>
                  <div className={cn(
                    'flex items-center gap-1.5 p-2 rounded transition-colors',
                    displayProgress >= 40 ? 'bg-purple-50 text-purple-700' : 'text-muted-foreground'
                  )}>
                    <Languages className="w-3 h-3" />
                    <span>Translate</span>
                  </div>
                  <div className={cn(
                    'flex items-center gap-1.5 p-2 rounded transition-colors',
                    displayProgress >= 70 ? 'bg-green-50 text-green-700' : 'text-muted-foreground'
                  )}>
                    <Download className="w-3 h-3" />
                    <span>Build PDF</span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </DialogContent>
      
      <style jsx>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
      `}</style>
    </Dialog>
  );
}