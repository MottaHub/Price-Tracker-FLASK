import sqlite3
import os

DB_PATH = "data/produtos.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force=False):
    # cria pasta se não existir
    os.makedirs("data", exist_ok=True)

    # verifica se banco já existe (para evitar recriar em imports)
    if os.path.exists(DB_PATH) and not force:
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
        ultimo_preco REAL
    )
    """)

    # migrar campo url_base se necessário
    cursor.execute("PRAGMA table_info(produtos)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'url_base' not in columns:
        cursor.execute('ALTER TABLE produtos ADD COLUMN url_base TEXT')

    conn.commit()

    # normalizar urls já existentes
    cursor.execute('SELECT id, url FROM produtos')
    for produto_id, url in cursor.fetchall():
        from database.models import normalizar_url
        base = normalizar_url(url)
        cursor.execute('UPDATE produtos SET url_base = ? WHERE id = ?', (base, produto_id))

    conn.commit()
    conn.close()


def ensure_db():
    """Garante que o banco existe (chamado explicitamente)"""
    init_db(force=False)