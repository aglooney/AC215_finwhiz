"""
Migration script to add user profile fields to the users table.

Run this script to add the profile columns to the existing users table.
"""

import os
from sqlalchemy import create_engine, text

# Read database connection info from environment
DB_USER = os.environ.get("DB_USER", "postgres")
DB_NAME = os.environ.get("DB_NAME", "finwhiz_db")
DB_HOST = os.environ.get("DB_HOST", "/cloudsql/finwhiz-ac215:us-central1:finwhiz-cloud-sql")

# Support both direct password or file-based secret
db_pass_value = os.environ.get("DB_PASS", "")
if os.path.isfile(db_pass_value):
    with open(db_pass_value, "r") as f:
        DB_PASS = f.read().strip()
else:
    DB_PASS = db_pass_value

# Cloud SQL connection string
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

def migrate():
    """Add profile columns to users table."""
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    with engine.connect() as conn:
        print("Starting migration: Adding user profile fields...")

        # Add columns one by one with IF NOT EXISTS to make migration idempotent
        migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS age INTEGER",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS retirement_age INTEGER",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS risk_tolerance VARCHAR(32)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS investment_goal TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_completed_at TIMESTAMP WITH TIME ZONE",
        ]

        for migration_sql in migrations:
            print(f"Executing: {migration_sql}")
            conn.execute(text(migration_sql))
            conn.commit()

        print("✅ Migration completed successfully!")
        print("Added columns: age, retirement_age, risk_tolerance, investment_goal, profile_completed_at")


if __name__ == "__main__":
    migrate()
