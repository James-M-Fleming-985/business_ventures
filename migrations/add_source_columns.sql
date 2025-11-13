-- Migration: Add source1 and source2 columns to correlation_results table
-- Run this via: railway run psql $DATABASE_URL < migrations/add_source_columns.sql

BEGIN;

-- Add source1 column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='correlation_results' AND column_name='source1'
    ) THEN
        ALTER TABLE correlation_results ADD COLUMN source1 VARCHAR(100);
        RAISE NOTICE 'Added source1 column';
    ELSE
        RAISE NOTICE 'source1 column already exists';
    END IF;
END$$;

-- Add source2 column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='correlation_results' AND column_name='source2'
    ) THEN
        ALTER TABLE correlation_results ADD COLUMN source2 VARCHAR(100);
        RAISE NOTICE 'Added source2 column';
    ELSE
        RAISE NOTICE 'source2 column already exists';
    END IF;
END$$;

COMMIT;

-- Verify columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'correlation_results' 
AND column_name IN ('source1', 'source2');
