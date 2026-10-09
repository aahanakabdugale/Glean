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
    task1_due = (today + datetime.timedelta(days=4)).isoformat()
    task2_due = (today + datetime.timedelta(days=10)).isoformat()

    # 1. Family Members
    # Chandler (Grandfather), Amy (Grandmother), Justin (Father), Riley (Mother),
    # Jace (Son / Admin), Gwen (Daughter / Admin)
    members = [
        ("Chandler", "grandfather", 1950, "retired"),
        ("Amy", "grandmother", 1953, "retired"),
        ("Justin", "father", 1968, "employed"),
        ("Riley", "mother", 1972, "employed"),
        ("Jace", "son", 2000, "family admin"),
        ("Gwen", "daughter", 2003, "family admin"),
    ]

    member_ids = {}
    for name, rel, birth, status in members:
        cur.execute(
            "INSERT INTO family_members (name, relation, birth_year, status) VALUES (?, ?, ?, ?)",
            (name, rel, birth, status),
        )
        member_ids[name] = cur.lastrowid

    # 2. Documents: exactly 3 documents per person (6 * 3 = 18 documents)
    # Strictly never store document numbers — only type and ISO expiry date.
    documents = [
        # Chandler (Grandfather)
        (member_ids["Chandler"], "Passport", (today + datetime.timedelta(days=6)).isoformat()),
        (member_ids["Chandler"], "Senior Citizen Health Insurance", (today + datetime.timedelta(days=25)).isoformat()),
        (member_ids["Chandler"], "Fixed Deposit Scheme Certificate", (today + datetime.timedelta(days=180)).isoformat()),

        # Amy (Grandmother)
        (member_ids["Amy"], "Ayushman Vay Vandana Health Card", (today + datetime.timedelta(days=365)).isoformat()),
        (member_ids["Amy"], "Post Office Senior Savings Certificate", (today + datetime.timedelta(days=400)).isoformat()),
        (member_ids["Amy"], "Pension Life Verification Certificate", (today + datetime.timedelta(days=18)).isoformat()),

        # Justin (Father)
        (member_ids["Justin"], "Driving Licence", (today + datetime.timedelta(days=22)).isoformat()),
        (member_ids["Justin"], "Motor Vehicle Comprehensive Insurance", (today + datetime.timedelta(days=12)).isoformat()),
        (member_ids["Justin"], "Passport", (today + datetime.timedelta(days=750)).isoformat()),

        # Riley (Mother)
        (member_ids["Riley"], "Health Insurance Policy", (today + datetime.timedelta(days=28)).isoformat()),
        (member_ids["Riley"], "Driving Licence", (today + datetime.timedelta(days=500)).isoformat()),
        (member_ids["Riley"], "Professional Membership Card", (today + datetime.timedelta(days=120)).isoformat()),

        # Jace (Son / Admin)
        (member_ids["Jace"], "Passport", (today + datetime.timedelta(days=90)).isoformat()),
        (member_ids["Jace"], "Driving Licence", (today + datetime.timedelta(days=600)).isoformat()),
        (member_ids["Jace"], "Term Life Insurance Policy", (today + datetime.timedelta(days=300)).isoformat()),

        # Gwen (Daughter / Admin)
        (member_ids["Gwen"], "University Transit Pass", (today + datetime.timedelta(days=15)).isoformat()),
        (member_ids["Gwen"], "Passport", (today + datetime.timedelta(days=450)).isoformat()),
        (member_ids["Gwen"], "Student Health Insurance", (today + datetime.timedelta(days=95)).isoformat()),
    ]

    for m_id, doc_type, expiry in documents:
        cur.execute(
            "INSERT INTO documents (member_id, doc_type, expiry_date) VALUES (?, ?, ?)",
            (m_id, doc_type, expiry),
        )

    # 3. Tasks
    tasks = [
        ("Renew Chandler's passport appointment", task1_due, member_ids["Chandler"]),
        ("Check Ayushman & senior benefits for Chandler & Amy", task2_due, member_ids["Chandler"]),
        ("Vehicle insurance renewal check", (today + datetime.timedelta(days=14)).isoformat(), member_ids["Justin"]),
        ("Submit Amy's annual pension life certificate", (today + datetime.timedelta(days=16)).isoformat(), member_ids["Amy"]),
    ]

    for title, due, m_id in tasks:
        cur.execute(
            "INSERT INTO tasks (title, due_date, member_id, done) VALUES (?, ?, ?, 0)",
            (title, due, m_id),
        )

    conn.commit()
    print("Successfully seeded demo data:")
    print(f"  - 6 Family members: {', '.join(member_ids.keys())} (Admins: Jace, Gwen)")
    print(f"  - 18 Documents: 3 documents seeded for each of the 6 family members")
    print(f"  - 4 Tasks seeded across upcoming deadlines")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo data for Glean")
    parser.parse_args()
    seed(reset=True)
