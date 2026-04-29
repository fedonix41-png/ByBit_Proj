#!/usr/bin/env python3
"""Database migration check script for Docker containers."""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory

def check_database_connection():
    """Check if database is accessible."""
    try:
        database_url = os.getenv("DATABASE_URL", "postgresql://p2p_user:p2p_pass@localhost:5432/p2p_automation")
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return engine
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def check_migration_state(engine):
    """Check current migration state."""
    try:
        # Get Alembic config
        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)

        # Get current head
        head_revision = script.get_current_head()
        print(f"📋 Latest migration revision: {head_revision}")

        # Check current database revision
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_revision = context.get_current_revision()
            print(f"📊 Current database revision: {current_revision}")

        if current_revision == head_revision:
            print("✅ Database is up to date")
            return True
        elif current_revision is None:
            print("⚠️  Database has no migrations applied")
            print("   Run 'alembic upgrade head' to apply all migrations")
            return False
        else:
            print("⚠️  Database migration mismatch")
            print(f"   Current: {current_revision}")
            print(f"   Expected: {head_revision}")
            print("   Run 'alembic upgrade head' to sync migrations")
            return False

    except Exception as e:
        print(f"❌ Migration check failed: {e}")
        return False

def main():
    """Main entry point."""
    print("🔍 Checking database migration state...")

    # Check database connection
    engine = check_database_connection()
    if not engine:
        sys.exit(1)

    # Check migration state
    is_up_to_date = check_migration_state(engine)

    if not is_up_to_date:
        print("\n⚠️  WARNING: Database migrations may be out of sync!")
        print("   This might cause application errors.")
        print("   Consider running migrations manually if issues occur.")
        # Don't exit with error - just warn
    else:
        print("\n✅ Database migration check completed successfully")

if __name__ == "__main__":
    main()