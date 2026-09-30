import sqlite3
from datetime import date

conn=sqlite3.connect("expenses.db")
conn.execute("""CREATE TABLE IF NOT EXISTS expenses(
id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,amount REAL NOT NULL,
category TEXT NOT NULL,expense_date TEXT NOT NULL,notes TEXT DEFAULT '')""")
today=date.today().isoformat()
rows=[
("Hostel lunch",180,"Food",today,"Canteen"),
("Uber",240,"Transport",today,"College trip"),
("Notebook",120,"Education",today,"Semester notes"),
("Cold coffee",160,"Food",today,"Cafe")
]
conn.executemany("INSERT INTO expenses(title,amount,category,expense_date,notes) VALUES(?,?,?,?,?)",rows)
conn.commit()
conn.close()
print("Demo data added.")
