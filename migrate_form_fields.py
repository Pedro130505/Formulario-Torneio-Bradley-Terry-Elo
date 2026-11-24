import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "torneio.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(inscritos_form);")
cols = [c[1] for c in cursor.fetchall()]
print("Current cols in inscritos_form:", cols)

new_cols = [
    ("como_soube_opcao", "TEXT DEFAULT ''"),
    ("projeto_extensao", "TEXT DEFAULT ''"),
    ("empresas_desejadas", "TEXT DEFAULT ''"),
    ("temas_painel", "TEXT DEFAULT ''"),
    ("tema_outro", "TEXT DEFAULT ''"),
    ("periodo_palestras", "TEXT DEFAULT ''"),
    ("horario_feira", "TEXT DEFAULT ''"),
]

for col_name, col_type in new_cols:
    if col_name not in cols:
        cursor.execute(f"ALTER TABLE inscritos_form ADD COLUMN {col_name} {col_type};")
        print(f"Added {col_name} to inscritos_form")

conn.commit()
conn.close()
print("Migration of form fields complete!")
