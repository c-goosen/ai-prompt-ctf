-- Simple one-liner fix for null string values
-- Run this against your database

UPDATE events SET input_transcription = NULL WHERE input_transcription IS NOT NULL AND (LOWER(TRIM(input_transcription)) = 'null' OR input_transcription = '');
UPDATE events SET output_transcription = NULL WHERE output_transcription IS NOT NULL AND (LOWER(TRIM(output_transcription)) = 'null' OR output_transcription = '');



