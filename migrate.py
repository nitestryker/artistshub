"""
ArtistHub Database Migration Script
====================================
Run this script once to apply all schema changes to an existing database.
It is safe to run multiple times — all operations check before applying.

Usage:
    python3 migrate.py

What this script does:
    1. Adds `image_url` column to the `messages` table (channel image sharing)
    2. Drops the NOT NULL constraint on `messages.content` (allows image-only messages)
    3. Reports the current state of all expected columns
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from sqlalchemy import text, inspect as sa_inspect


def get_columns(inspector, table_name):
    try:
        return {c['name']: c for c in inspector.get_columns(table_name)}
    except Exception:
        return {}


def run():
    app = create_app()

    with app.app_context():
        engine = db.engine
        dialect = engine.dialect.name
        inspector = sa_inspect(engine)

        print(f"\nArtistHub Migration Script")
        print(f"Database: {dialect}")
        print("=" * 50)

        db.create_all()
        print("[OK] db.create_all() — all tables verified/created")

        # ----------------------------------------------------------------
        # Migration 1: messages.image_url
        # ----------------------------------------------------------------
        messages_cols = get_columns(inspector, 'messages')

        if 'image_url' not in messages_cols:
            print("\n[APPLY] Adding image_url column to messages table...")
            with engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE messages ADD COLUMN image_url VARCHAR(500)"
                ))
                conn.commit()
            print("[DONE]  image_url column added to messages")
        else:
            print("\n[SKIP]  messages.image_url already exists")

        # ----------------------------------------------------------------
        # Migration 2: messages.content — allow NULL / empty string
        # SQLite does not support ALTER COLUMN to drop constraints.
        # On SQLite this is handled at the application layer (default='').
        # On PostgreSQL we drop the NOT NULL constraint explicitly.
        # ----------------------------------------------------------------
        if dialect == 'postgresql':
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT is_nullable
                        FROM information_schema.columns
                        WHERE table_name = 'messages' AND column_name = 'content'
                    """))
                    row = result.fetchone()
                    if row and row[0] == 'NO':
                        print("\n[APPLY] Dropping NOT NULL constraint on messages.content (PostgreSQL)...")
                        conn.execute(text(
                            "ALTER TABLE messages ALTER COLUMN content DROP NOT NULL"
                        ))
                        conn.commit()
                        print("[DONE]  NOT NULL constraint removed from messages.content")
                    else:
                        print("\n[SKIP]  messages.content already allows NULL (PostgreSQL)")
            except Exception as e:
                print(f"\n[WARN]  Could not modify messages.content constraint: {e}")
        else:
            print("\n[INFO]  SQLite detected — messages.content constraint handled by application default")

        # ----------------------------------------------------------------
        # Migration 3: reports.message_id and reports.channel_id
        # ----------------------------------------------------------------
        reports_cols = get_columns(inspector, 'reports')

        if 'message_id' not in reports_cols:
            print("\n[APPLY] Adding message_id column to reports table...")
            with engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE reports ADD COLUMN message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL"
                ))
                conn.commit()
            print("[DONE]  message_id column added to reports")
        else:
            print("\n[SKIP]  reports.message_id already exists")

        if 'channel_id' not in reports_cols:
            print("\n[APPLY] Adding channel_id column to reports table...")
            with engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE reports ADD COLUMN channel_id INTEGER REFERENCES channels(id) ON DELETE SET NULL"
                ))
                conn.commit()
            print("[DONE]  channel_id column added to reports")
        else:
            print("\n[SKIP]  reports.channel_id already exists")

        # ----------------------------------------------------------------
        # Final report
        # ----------------------------------------------------------------
        print("\n" + "=" * 50)
        print("Migration complete. Current messages table schema:")
        inspector2 = sa_inspect(engine)
        final_cols = get_columns(inspector2, 'messages')
        for name, col in final_cols.items():
            nullable = "nullable" if col.get('nullable', True) else "NOT NULL"
            col_type = str(col.get('type', 'unknown'))
            print(f"  - {name:20s} {col_type:20s} {nullable}")

        print("\nAll done.")


if __name__ == '__main__':
    run()
