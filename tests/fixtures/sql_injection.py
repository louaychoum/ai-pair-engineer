"""SQL injection via raw string interpolation.

The username field is concatenated directly into the query.
A malicious user supplying " ' OR 1=1 -- " gets every row.
"""

import sqlite3


def find_user(conn: sqlite3.Connection, username: str) -> dict | None:
    query = "SELECT id, username, email FROM users WHERE username = '" + username + "'"
    cursor = conn.cursor()
    cursor.execute(query)
    row = cursor.fetchone()
    if row is None:
        return None
    return {"id": row[0], "username": row[1], "email": row[2]}
