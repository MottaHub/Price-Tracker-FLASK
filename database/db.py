import sqlite3
import os

DB_PATH = "data/produtos.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force=False):
    os.makedirs("data", exist_ok=True)

    if os.path.exists(DB_PATH) and not force:
        _migrar()
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        url TEXT NOT NULL,
        url_base TEXT,
        menor_preco REAL,
        menor_preco_url TEXT,
        ultimo_preco REAL
    )
    """)

    conn.commit()
    conn.close()
    _migrar()


def _migrar():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(produtos)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'url_base' not in columns:
        cursor.execute('ALTER TABLE produtos ADD COLUMN url_base TEXT')
    if 'menor_preco_url' not in columns:
        cursor.execute('ALTER TABLE produtos ADD COLUMN menor_preco_url TEXT')

    conn.commit()

    cursor.execute('SELECT id, url FROM produtos WHERE url_base IS NULL')
    for row in cursor.fetchall():
        from database.models import normalizar_url
        base = normalizar_url(row['url'])
        cursor.execute('UPDATE produtos SET url_base = ? WHERE id = ?', (base, row['id']))

    conn.commit()
    conn.close()


def ensure_db():
    init_db(force=False)