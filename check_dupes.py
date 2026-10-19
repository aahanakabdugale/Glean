from backend import db
conn = db.get_connection()
rows = conn.execute("SELECT id, title, due_date, member_id, done FROM tasks WHERE title LIKE '%Ayushman%'").fetchall()
for r in rows:
    print(dict(r))
