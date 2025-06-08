-- supabase_schema.sql
-- Complete schema for Legal Document Translator application
-- This file should be executed in the Supabase SQL editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Clean up if tables exist (for re-runs)
DROP TABLE IF EXISTS public.translation_jobs;
DROP TABLE IF EXISTS public.files;

-- =========================================
-- Files Table
-- =========================================
-- Stores metadata about uploaded files (original PDFs and translated outputs)
CREATE TABLE public.files (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id), -- Optional, for when auth is enabled
  original_name TEXT NOT NULL, -- Original filename from user
  bucket TEXT NOT NULL, -- 'uploads' or 'outputs'
  storage_path TEXT NOT NULL, -- Path within the bucket
  mime_type TEXT DEFAULT 'application/pdf', -- File MIME type
  size_bytes INTEGER, -- File size in bytes
  created_at TIMESTAMPTZ DEFAULT now(),
  
  -- Constraint to ensure bucket is valid
  CONSTRAINT valid_bucket CHECK (bucket IN ('uploads', 'outputs'))
);

COMMENT ON TABLE public.files IS 'Stores metadata for uploaded and generated PDF files';
COMMENT ON COLUMN public.files.id IS 'Unique identifier for the file';
COMMENT ON COLUMN public.files.user_id IS 'Reference to the user who uploaded the file (if auth enabled)';
COMMENT ON COLUMN public.files.original_name IS 'Original filename provided by the user';
COMMENT ON COLUMN public.files.bucket IS 'Supabase Storage bucket name (uploads or outputs)';
COMMENT ON COLUMN public.files.storage_path IS 'Path to the file within the bucket';
COMMENT ON COLUMN public.files.mime_type IS 'MIME type of the file';
COMMENT ON COLUMN public.files.size_bytes IS 'File size in bytes';
COMMENT ON COLUMN public.files.created_at IS 'Timestamp when the file record was created';

-- Create index on user_id for faster lookups when auth is enabled
CREATE INDEX idx_files_user_id ON public.files(user_id);
-- Create index on bucket for filtering by bucket type
CREATE INDEX idx_files_bucket ON public.files(bucket);
-- Create index on created_at for time-based queries
CREATE INDEX idx_files_created_at ON public.files(created_at);

-- =========================================
-- Translation Jobs Table
-- =========================================
-- Tracks translation jobs and their progress
CREATE TABLE public.translation_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  file_id UUID REFERENCES public.files(id) ON DELETE CASCADE,
  output_file_id UUID REFERENCES public.files(id) ON DELETE SET NULL,
  status TEXT DEFAULT 'pending', -- pending|processing|extracting|translating|building|done|error
  progress INTEGER DEFAULT 0, -- 0-100 percentage
  src_lang TEXT DEFAULT 'gu', -- Source language code (Gujarati default)
  tgt_lang TEXT DEFAULT 'en', -- Target language code (English default)
  pages_total INTEGER, -- Total number of pages in the document
  pages_processed INTEGER DEFAULT 0, -- Number of pages processed so far
  error_message TEXT, -- Error message if status is 'error'
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  -- Constraints
  CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100),
  CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'extracting', 'translating', 'building', 'done', 'error')),
  CONSTRAINT valid_pages CHECK (pages_processed <= pages_total OR pages_total IS NULL)
);

COMMENT ON TABLE public.translation_jobs IS 'Tracks PDF translation jobs and their progress';
COMMENT ON COLUMN public.translation_jobs.id IS 'Unique identifier for the job';
COMMENT ON COLUMN public.translation_jobs.file_id IS 'Reference to the original PDF file';
COMMENT ON COLUMN public.translation_jobs.output_file_id IS 'Reference to the translated PDF file (when complete)';
COMMENT ON COLUMN public.translation_jobs.status IS 'Current status of the translation job';
COMMENT ON COLUMN public.translation_jobs.progress IS 'Overall progress percentage (0-100)';
COMMENT ON COLUMN public.translation_jobs.src_lang IS 'Source language code (ISO 639-1)';
COMMENT ON COLUMN public.translation_jobs.tgt_lang IS 'Target language code (ISO 639-1)';
COMMENT ON COLUMN public.translation_jobs.pages_total IS 'Total number of pages in the document';
COMMENT ON COLUMN public.translation_jobs.pages_processed IS 'Number of pages processed so far';
COMMENT ON COLUMN public.translation_jobs.error_message IS 'Error message if the job failed';
COMMENT ON COLUMN public.translation_jobs.created_at IS 'Timestamp when the job was created';
COMMENT ON COLUMN public.translation_jobs.updated_at IS 'Timestamp when the job was last updated';

-- Create indexes for performance
CREATE INDEX idx_translation_jobs_file_id ON public.translation_jobs(file_id);
CREATE INDEX idx_translation_jobs_output_file_id ON public.translation_jobs(output_file_id);
CREATE INDEX idx_translation_jobs_status ON public.translation_jobs(status);
CREATE INDEX idx_translation_jobs_created_at ON public.translation_jobs(created_at);

-- =========================================
-- Triggers
-- =========================================
-- Auto-update the updated_at timestamp when a translation job is updated
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_translation_jobs_updated_at
BEFORE UPDATE ON public.translation_jobs
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

-- =========================================
-- Enable Realtime
-- =========================================
-- Enable realtime for translation_jobs table to support progress updates
BEGIN;
  -- Drop from existing publication if it exists
  DROP PUBLICATION IF EXISTS supabase_realtime;
  
  -- Create the publication for realtime
  CREATE PUBLICATION supabase_realtime;
  
  -- Add the translation_jobs table to the publication
  ALTER PUBLICATION supabase_realtime ADD TABLE public.translation_jobs;
COMMIT;

-- =========================================
-- Row Level Security (RLS) Policies
-- =========================================
-- These are commented out for MVP simplicity
-- Uncomment and adjust when implementing authentication

-- Enable RLS on tables (commented out for MVP)
-- ALTER TABLE public.files ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.translation_jobs ENABLE ROW LEVEL SECURITY;

-- Example policies for files table (commented out for MVP)
/*
-- Allow users to select their own files
CREATE POLICY "Users can view their own files"
  ON public.files
  FOR SELECT
  USING (auth.uid() = user_id OR user_id IS NULL);

-- Allow users to insert their own files
CREATE POLICY "Users can insert their own files"
  ON public.files
  FOR INSERT
  WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

-- Allow users to update their own files
CREATE POLICY "Users can update their own files"
  ON public.files
  FOR UPDATE
  USING (auth.uid() = user_id OR user_id IS NULL);

-- Allow users to delete their own files
CREATE POLICY "Users can delete their own files"
  ON public.files
  FOR DELETE
  USING (auth.uid() = user_id OR user_id IS NULL);
*/

-- Example policies for translation_jobs table (commented out for MVP)
/*
-- Allow users to select their own jobs
CREATE POLICY "Users can view their own jobs"
  ON public.translation_jobs
  FOR SELECT
  USING (
    auth.uid() = (
      SELECT user_id FROM public.files WHERE id = file_id
    ) OR (
      SELECT user_id FROM public.files WHERE id = file_id
    ) IS NULL
  );

-- Allow users to insert jobs for their own files
CREATE POLICY "Users can insert jobs for their own files"
  ON public.translation_jobs
  FOR INSERT
  WITH CHECK (
    auth.uid() = (
      SELECT user_id FROM public.files WHERE id = file_id
    ) OR (
      SELECT user_id FROM public.files WHERE id = file_id
    ) IS NULL
  );

-- Allow users to update their own jobs
CREATE POLICY "Users can update their own jobs"
  ON public.translation_jobs
  FOR UPDATE
  USING (
    auth.uid() = (
      SELECT user_id FROM public.files WHERE id = file_id
    ) OR (
      SELECT user_id FROM public.files WHERE id = file_id
    ) IS NULL
  );
*/

-- =========================================
-- Grant Permissions
-- =========================================
-- Grant access to the anon and authenticated roles
GRANT SELECT, INSERT, UPDATE ON public.files TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.translation_jobs TO anon, authenticated;
GRANT USAGE ON SEQUENCE public.files_id_seq TO anon, authenticated;
GRANT USAGE ON SEQUENCE public.translation_jobs_id_seq TO anon, authenticated;
