import React, { useCallback, useRef, useState } from 'react';
import { Cloud, Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

interface UploadDropzoneProps {
  onFileAccepted: (file: File) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB in bytes
const ACCEPTED_FILE_TYPE = 'application/pdf';

export function UploadDropzone({ onFileAccepted, isLoading = false, disabled = false }: UploadDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [hasValidFile, setHasValidFile] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const validateFile = useCallback((file: File): string | null => {
    if (file.type !== ACCEPTED_FILE_TYPE) {
      return 'Please upload a PDF file only.';
    }
    
    if (file.size > MAX_FILE_SIZE) {
      return `File size must be less than ${MAX_FILE_SIZE / (1024 * 1024)}MB.`;
    }
    
    return null;
  }, []);

  const handleFileSelection = useCallback((files: FileList | null) => {
    if (!files) return;
    
    if (files.length > 1) {
      toast({
        variant: "destructive",
        title: "Multiple files not allowed",
        description: "Please select only one PDF file at a time.",
      });
      return;
    }
    
    const file = files[0];
    const validationError = validateFile(file);
    
    if (validationError) {
      toast({
        variant: "destructive",
        title: "Invalid file",
        description: validationError,
      });
      setHasValidFile(false);
      return;
    }
    
    setHasValidFile(true);
    onFileAccepted(file);
    
    toast({
      title: "File accepted",
      description: `${file.name} is ready for processing.`,
    });
  }, [validateFile, onFileAccepted, toast]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled && !isLoading) {
      setIsDragOver(true);
    }
  }, [disabled, isLoading]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    
    if (disabled || isLoading) return;
    
    const files = e.dataTransfer.files;
    handleFileSelection(files);
  }, [disabled, isLoading, handleFileSelection]);

  const handleClick = useCallback(() => {
    if (disabled || isLoading) return;
    fileInputRef.current?.click();
  }, [disabled, isLoading]);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelection(e.target.files);
    // Reset the input value to allow selecting the same file again
    e.target.value = '';
  }, [handleFileSelection]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }, [handleClick]);

  const getDropzoneState = () => {
    if (disabled || isLoading) return 'disabled';
    if (hasValidFile) return 'success';
    if (isDragOver) return 'active';
    return 'default';
  };

  const dropzoneState = getDropzoneState();

  return (
    <div className="w-full">
      <div
        className={cn(
          'relative min-h-[200px] w-full rounded-lg border-2 border-dashed transition-all duration-200 ease-in-out',
          'flex flex-col items-center justify-center gap-4 p-8',
          'cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
          {
            'border-muted-foreground/25 bg-background hover:border-muted-foreground/50 hover:bg-muted/50': 
              dropzoneState === 'default',
            'border-primary bg-primary/5 border-solid': 
              dropzoneState === 'active',
            'border-destructive bg-destructive/5': 
              dropzoneState === 'error',
            'border-green-500 bg-green-50 dark:bg-green-950/20': 
              dropzoneState === 'success',
            'border-muted-foreground/10 bg-muted/20 cursor-not-allowed': 
              dropzoneState === 'disabled',
          }
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        tabIndex={disabled || isLoading ? -1 : 0}
        role="button"
        aria-label="Upload PDF file"
        aria-describedby="upload-description"
      >
        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm rounded-lg">
            <div className="flex items-center gap-2 text-muted-foreground">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <span className="text-sm font-medium">Processing...</span>
            </div>
          </div>
        )}

        {/* Upload icon */}
        <div className="flex items-center justify-center">
          {hasValidFile ? (
            <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
              <CheckCircle className="h-8 w-8" />
              <FileText className="h-8 w-8" />
            </div>
          ) : (
            <Cloud className={cn(
              'h-12 w-12 transition-colors duration-200',
              {
                'text-muted-foreground': dropzoneState === 'default',
                'text-primary': dropzoneState === 'active',
                'text-green-500': dropzoneState === 'success',
                'text-muted-foreground/50': dropzoneState === 'disabled',
              }
            )} />
          )}
        </div>

        {/* Main text */}
        <div className="text-center space-y-2">
          <p className={cn(
            'text-lg font-medium transition-colors duration-200',
            {
              'text-foreground': dropzoneState === 'default' || dropzoneState === 'active',
              'text-green-600 dark:text-green-400': dropzoneState === 'success',
              'text-muted-foreground': dropzoneState === 'disabled',
            }
          )}>
            {hasValidFile 
              ? 'File ready for processing'
              : 'Drag & drop your PDF here, or click to browse'
            }
          </p>
          
          {!hasValidFile && (
            <p id="upload-description" className="text-sm text-muted-foreground">
              Supports PDF files up to 20MB
            </p>
          )}
        </div>

        {/* Additional info */}
        {!isLoading && !hasValidFile && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Upload className="h-3 w-3" />
            <span>PDF only • Max 20MB</span>
          </div>
        )}

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileInputChange}
          className="hidden"
          disabled={disabled || isLoading}
          aria-hidden="true"
        />
      </div>
    </div>
  );
}