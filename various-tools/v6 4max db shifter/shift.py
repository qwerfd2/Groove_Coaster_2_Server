import sqlite3

db_path = "player.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Delete all rows with id == 359
cur.execute("DELETE FROM result WHERE id = ?", (359,))

# 2. Shift every row with id > 359 to id = x - 1
cur.execute("UPDATE result SET id = id - 1 WHERE id > ?", (359,))

# 3. Shift every row with id == 721 to id = 10 (722 - 1)
cur.execute("UPDATE result SET id = ? WHERE id = ?", (10, 721))

# 4. Shift every row with id > 721 to id = x - 1
cur.execute("UPDATE result SET id = id - 1 WHERE id > ?", (721,))

# 5. Shift every row with id == 916 to id = 7 (918 - 2)
cur.execute("UPDATE result SET id = ? WHERE id = ?", (7, 916))

# 6. Shift every row with id > 916 to id = x - 1
cur.execute("UPDATE result SET id = id - 1 WHERE id > ?", (916,))

# 7. Shift every row with id == 918 to id = 4 (921 - 3)
cur.execute("UPDATE result SET id = ? WHERE id = ?", (4, 918))

# 8. Shift every row with id > 918 to id = x - 1
cur.execute("UPDATE result SET id = id - 1 WHERE id > ?", (918,))

conn.commit()
conn.close()