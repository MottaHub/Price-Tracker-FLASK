import sqlite3
import os

DB_PATH = "data/produtos.db"

def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    # cria pasta se não existir
    os.makedirs("data", exist_ok=True)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        url TEXT NOT NULL,
        menor_preco REAL,
        ultimo_preco REAL
    )
    """)

    conn.commit()
    conn.close()