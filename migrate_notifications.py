"""
ArtistHub Migration — Notifications System
============================================
Run this script once to add the notifications table to an existing database.
It is safe to run multiple times — all operations check before applying.

Usage:
    python3 migrate_notifications.py

What this script does:
    1. Creates the `notifications` table if it does not already exist
    2. Reports the final schema of the notifications table
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from sqlalchemy import text, inspect as sa_inspect


def run():
    app = create_app()

    with app.app_context():
        engine = db.engine
        dialect = engine.dialect.name
        inspector = sa_inspect(engine)

        print(f"\nArtistHub Migration — Notifications System")
        print(f"Database: {dialect}")
        print("=" * 50)

        existing_tables = inspector.get_table_names()

        if 'notifications' not in existing_tables:
            print("\n[APPLY] Creating notifications table...")
            db.create_all()
            print("[DONE]  notifications table created")
        else:
            print("\n[SKIP]  notifications table already exists")
            db.create_all()

        # ----------------------------------------------------------------
        # Verify all expected columns exist
        # ----------------------------------------------------------------
        inspector2 = sa_inspect(engine)
        cols = {c['name'] for c in inspector2.get_columns('notifications')}
        expected = {'id', 'recipient_id', 'sender_id', 'notif_type', 'artwork_id', 'read', 'created_at'}
        missing = expected - cols

        if missing:
            print(f"\n[WARN]  Missing columns detected: {missing}")
            print("        Attempting to add missing columns...")
            type_map = {
                'recipient_id': 'INTEGER REFERENCES users(id)',
                'sender_id': 'INTEGER REFERENCES users(id)',
                'notif_type': 'VARCHAR(20) NOT NULL',
                'artwork_id': 'INTEGER REFERENCES artworks(id)',
                'read': 'BOOLEAN DEFAULT FALSE',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            }
            with engine.connect() as conn:
                for col in missing:
                    if col in type_map:
                        try:
                            conn.execute(text(
                                f"ALTER TABLE notifications ADD COLUMN {col} {type_map[col]}"
                            ))
                            print(f"[DONE]  Added column: {col}")
                        except Exception as e:
                            print(f"[WARN]  Could not add {col}: {e}")
                conn.commit()
        else:
            print("\n[OK]    All expected columns present")

        # ----------------------------------------------------------------
        # Final report
        # ----------------------------------------------------------------
        print("\n" + "=" * 50)
        print("Final notifications table schema:")
        inspector3 = sa_inspect(engine)
        final_cols = {c['name']: c for c in inspector3.get_columns('notifications')}
        for name, col in final_cols.items():
            nullable = "nullable" if col.get('nullable', True) else "NOT NULL"
            col_type = str(col.get('type', 'unknown'))
            print(f"  - {name:20s} {col_type:20s} {nullable}")

        print("\nMigration complete.")


if __name__ == '__main__':
    run()
