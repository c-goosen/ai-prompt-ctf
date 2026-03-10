-- Migration script to add input_transcription and output_transcription columns
-- to the events table for ADK session service.
--
-- Run this script against your PostgreSQL database:
--   psql "postgresql://postgres.rcguwvbhbqxdapmuczpa:265BbxN2547NgAah@aws-1-eu-west-2.pooler.supabase.com:6543/postgres" -f migrate_events_table.sql
--
-- Or connect to your database and paste these commands:

DO $$
BEGIN
    -- Add input_transcription column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'events' 
        AND column_name = 'input_transcription'
    ) THEN
        ALTER TABLE events ADD COLUMN input_transcription TEXT;
        RAISE NOTICE 'Added input_transcription column';
    ELSE
        RAISE NOTICE 'input_transcription column already exists';
        -- Fix string 'null' values to actual NULL (handle all variations)
        UPDATE events 
        SET input_transcription = NULL 
        WHERE LOWER(TRIM(input_transcription)) = 'null' 
           OR input_transcription = '';
        RAISE NOTICE 'Fixed string null values in input_transcription';
    END IF;
    
    -- Add output_transcription column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'events' 
        AND column_name = 'output_transcription'
    ) THEN
        ALTER TABLE events ADD COLUMN output_transcription TEXT;
        RAISE NOTICE 'Added output_transcription column';
    ELSE
        RAISE NOTICE 'output_transcription column already exists';
        -- Fix string 'null' values to actual NULL (handle all variations)
        UPDATE events 
        SET output_transcription = NULL 
        WHERE LOWER(TRIM(output_transcription)) = 'null' 
           OR output_transcription = '';
        RAISE NOTICE 'Fixed string null values in output_transcription';
    END IF;
END $$;

