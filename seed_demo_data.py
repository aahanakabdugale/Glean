"""Seed fake family demo data into Glean SQLite database.

Usage:
    python seed_demo_data.py [--reset]
"""

import argparse
import datetime
import os
import sqlite3

from glean import db


def seed(reset: bool = False):
    conn = db.get_connection()
    db.init_db(conn)

    cur = conn.cursor()

    if reset:
        cur.execute("DELETE FROM tasks")
        cur.execute("DELETE FROM documents")
        cur.execute("DELETE FROM family_members")
        conn.commit()
        print("Cleared existing records.")

    # Check if already seeded
    existing = cur.execute("SELECT COUNT(*) FROM family_members").fetchone()[0]
    if existing > 0 and not reset:
        print(f"Database already contains {existing} family members. Use --reset to re-seed.")
        return

    # Base dates dynamically around today
    today = datetime.date.today()
    passport_expiry = (today + datetime.timedelta(days=6)).isoformat()
    licence_expiry = (today + datetime.timedelta(days=20)).isoformat()
    health_expiry = (today + datetime.timedelta(days=180)).isoformat()

    task1_due = (today + datetime.timedelta(days=4)).isoformat()
    task2_due = (today + datetime.timedelta(days=10)).isoformat()

    # 1. Family Members
    members = [
        ("Ramesh", "grandfather", 1950, "retired"),
        ("Suresh", "father", 1966, "employed"),
        ("Sunita", "mother", 1970, "homemaker"),
        ("Maria", "daughter", 2005, "student"),
    ]

    member_ids = {}
    for name, rel, birth, status in members:
        cur.execute(
            "INSERT INTO family_members (name, relation, birth_year, status) VALUES (?, ?, ?, ?)",
            (name, rel, birth, status),
        )
        member_ids[name] = cur.lastrowid

    # 2. Documents (never store document numbers, only type and expiry)
    documents = [
        (member_ids["Ramesh"], "Passport", passport_expiry),
        (member_ids["Maria"], "Driving Licence", licence_expiry),
        (member_ids["Suresh"], "Health Insurance Card", health_expiry),
    ]

    for m_id, doc_type, expiry in documents:
        cur.execute(
            "INSERT INTO documents (member_id, doc_type, expiry_date) VALUES (?, ?, ?)",
            (m_id, doc_type, expiry),
        )

    # 3. Tasks
    tasks = [
        ("Renew Ramesh's passport appointment", task1_due, member_ids["Ramesh"]),
        ("Check senior citizen pension documents", task2_due, member_ids["Ramesh"]),
    ]

    for title, due, m_id in tasks:
        cur.execute(
            "INSERT INTO tasks (title, due_date, member_id, done) VALUES (?, ?, ?, 0)",
            (title, due, m_id),
        )

    conn.commit()
    print("Successfully seeded demo data:")
    print(f"  - 4 Family members: {', '.join(member_ids.keys())}")
    print(f"  - 3 Documents: Ramesh Passport (exp: {passport_expiry}), Maria Licence (exp: {licence_expiry}), Suresh Insurance")
    print(f"  - 2 Tasks: Passport renewal (due: {task1_due}), Pension check (due: {task2_due})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo data for Glean")
    parser.add_argument("--reset", action="store_true", help="Clear existing data before seeding")
    args = parser.parse_args()
    seed(reset=args.reset)
