#!/usr/bin/env python3
"""
Migration script to add input_transcription and output_transcription columns
to the events table for ADK session service.

This script requires asyncpg. Install it with:
    uv add asyncpg
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


async def migrate_events_table(db_url: str) -> None:
    """
    Add missing columns to the events table if they don't exist.
    
    Args:
        db_url: PostgreSQL connection URL (can be postgresql:// or postgresql+asyncpg://)
    """
    # Ensure we're using asyncpg driver
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not db_url.startswith("postgresql+asyncpg://"):
        print("Error: Database URL must be a PostgreSQL connection string")
        sys.exit(1)
    
    # Disable statement caching for pgbouncer compatibility
    engine = create_async_engine(
        db_url, 
        echo=True,
        connect_args={"statement_cache_size": 0}
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Check if columns exist and add them if they don't
            # Also fix any string 'null' values to actual NULL
            check_and_add_column = text("""
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
            """)
            
            result = await session.execute(check_and_add_column)
            await session.commit()
            print("✓ Migration completed successfully!")
            
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python migrate_events_table.py <postgresql_connection_url>")
        print("\nExample:")
        print("  python migrate_events_table.py 'postgresql://user:pass@host:port/db'")
        sys.exit(1)
    
    db_url = sys.argv[1]
    asyncio.run(migrate_events_table(db_url))

