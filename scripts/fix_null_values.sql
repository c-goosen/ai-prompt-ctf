-- Quick fix script to convert all string 'null' variations to actual NULL
-- This handles case variations, whitespace, and JSON null strings
-- Run this directly if you just need to fix existing data

-- First, let's see what we're dealing with
SELECT 
    'Before fix' as status,
    COUNT(*) as total_rows,
    COUNT(CASE WHEN input_transcription IS NULL THEN 1 END) as null_input_transcription,
    COUNT(CASE WHEN input_transcription = 'null' OR LOWER(TRIM(COALESCE(input_transcription, ''))) = 'null' THEN 1 END) as string_null_input,
    COUNT(CASE WHEN output_transcription IS NULL THEN 1 END) as null_output_transcription,
    COUNT(CASE WHEN output_transcription = 'null' OR LOWER(TRIM(COALESCE(output_transcription, ''))) = 'null' THEN 1 END) as string_null_output
FROM events;

-- Fix input_transcription - handle all variations
UPDATE events 
SET input_transcription = NULL 
WHERE input_transcription IS NOT NULL
  AND (
    LOWER(TRIM(input_transcription)) = 'null' 
    OR input_transcription = ''
    OR input_transcription = 'null'
    OR input_transcription = 'NULL'
    OR input_transcription = 'Null'
    OR TRIM(input_transcription) = ''
  );

-- Fix output_transcription - handle all variations
UPDATE events 
SET output_transcription = NULL 
WHERE output_transcription IS NOT NULL
  AND (
    LOWER(TRIM(output_transcription)) = 'null' 
    OR output_transcription = ''
    OR output_transcription = 'null'
    OR output_transcription = 'NULL'
    OR output_transcription = 'Null'
    OR TRIM(output_transcription) = ''
  );

-- Verify the fix
SELECT 
    'After fix' as status,
    COUNT(*) as total_rows,
    COUNT(CASE WHEN input_transcription IS NULL THEN 1 END) as null_input_transcription,
    COUNT(CASE WHEN input_transcription = 'null' OR LOWER(TRIM(COALESCE(input_transcription, ''))) = 'null' THEN 1 END) as string_null_input,
    COUNT(CASE WHEN output_transcription IS NULL THEN 1 END) as null_output_transcription,
    COUNT(CASE WHEN output_transcription = 'null' OR LOWER(TRIM(COALESCE(output_transcription, ''))) = 'null' THEN 1 END) as string_null_output
FROM events;

-- Show any remaining problematic rows (should be 0)
SELECT 
    id, 
    app_name, 
    session_id,
    input_transcription,
    output_transcription
FROM events 
WHERE (input_transcription IS NOT NULL AND LOWER(TRIM(input_transcription)) = 'null')
   OR (output_transcription IS NOT NULL AND LOWER(TRIM(output_transcription)) = 'null')
LIMIT 10;

