from database.db import get_connection
from urllib.parse import urlparse, urlunparse


def normalizar_url(url):
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip('/')
    # mantém esquema e domínio + caminho, ignora query/fragment
    normalized = urlunparse((parsed.scheme, parsed.netloc, path, '', '', ''))
    return normalized


def adicionar_produto(nome, url):
    conn = get_connection()
    cursor = conn.cursor()

    url_base = normalizar_url(url)

    cursor.execute("""
    INSERT INTO produtos (nome, url, url_base, menor_preco, ultimo_preco)
    VALUES (?, ?, ?, NULL, NULL)
    """, (nome, url, url_base))

    conn.commit()
    conn.close()


def listar_produtos():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, url, url_base, menor_preco, ultimo_preco FROM produtos")
    rows = cursor.fetchall()

    conn.close()

    produtos = []
    for row in rows:
        menor_preco = float(row['menor_preco']) if row['menor_preco'] is not None else None
        ultimo_preco = float(row['ultimo_preco']) if row['ultimo_preco'] is not None else None

        produtos.append({
            "id": row['id'],
            "nome": row['nome'],
            "url": row['url'],
            "url_base": row['url_base'],
            "menor_preco": menor_preco,
            "ultimo_preco": ultimo_preco
        })

    return produtos


def listar_produtos_por_base(url_base):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, url, url_base, menor_preco, ultimo_preco FROM produtos WHERE url_base = ?", (url_base,))
    rows = cursor.fetchall()
    conn.close()

    produtos = []
    for row in rows:
        menor_preco = float(row['menor_preco']) if row['menor_preco'] is not None else None
        ultimo_preco = float(row['ultimo_preco']) if row['ultimo_preco'] is not None else None

        produtos.append({
            "id": row['id'],
            "nome": row['nome'],
            "url": row['url'],
            "url_base": row['url_base'],
            "menor_preco": menor_preco,
            "ultimo_preco": ultimo_preco
        })

    return produtos


def definir_menor_preco(produto_id, menor_preco):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE produtos SET menor_preco = ? WHERE id = ?", (menor_preco, produto_id))
    conn.commit()
    conn.close()


def atualizar_preco(produto_id, preco):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT menor_preco FROM produtos WHERE id = ?", (produto_id,))
    resultado = cursor.fetchone()
    menor_preco = resultado[0] if resultado is not None else None

    if menor_preco is None or preco < menor_preco:
        menor_preco = preco

    cursor.execute("""
    UPDATE produtos
    SET ultimo_preco = ?, menor_preco = ?
    WHERE id = ?
    """, (preco, menor_preco, produto_id))

    conn.commit()
    conn.close()