import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = sqlite3.connect('attendance.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 60)
print("  ATTENDANCE TRACKER - DATABASE VIEWER")
print("=" * 60)

# Users
print("\n[USERS]")
print("-" * 60)
users = c.execute('SELECT * FROM users').fetchall()
for u in users:
    status = "Approved" if u['is_approved'] else "Pending"
    print(f"  ID:{u['id']} | {u['full_name']} | {u['email']} | {u['role']} | {u['department']} | {status}")
print(f"  Total: {len(users)} users")

# Attendance
print("\n[ATTENDANCE RECORDS]")
print("-" * 60)
records = c.execute('''
    SELECT a.*, u.full_name FROM attendance a 
    JOIN users u ON a.user_id = u.id 
    ORDER BY a.check_in DESC LIMIT 20
''').fetchall()
for r in records:
    checkout = r['check_out'][:19] if r['check_out'] else 'Not yet'
    print(f"  {r['date']} | {r['full_name']} | In: {r['check_in'][:19]} | Out: {checkout} | {r['working_hours']}h | {r['status']}")
if not records:
    print("  No attendance records yet.")
print(f"  Showing: {len(records)} records")

# Leave Requests
print("\n[LEAVE REQUESTS]")
print("-" * 60)
leaves = c.execute('''
    SELECT l.*, u.full_name FROM leave_requests l 
    JOIN users u ON l.user_id = u.id 
    ORDER BY l.created_at DESC
''').fetchall()
for l in leaves:
    print(f"  {l['full_name']} | {l['leave_type']} | {l['start_date']} to {l['end_date']} | {l['status']}")
if not leaves:
    print("  No leave requests yet.")
print(f"  Total: {len(leaves)} requests")

print("\n" + "=" * 60)
conn.close()
