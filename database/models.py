from database.db import get_connection
from urllib.parse import urlparse, urlunparse


def normalizar_url(url):
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip('/')
    normalized = urlunparse((parsed.scheme, parsed.netloc, path, '', '', ''))
    return normalized


def adicionar_produto(nome, url):
    conn = get_connection()
    cursor = conn.cursor()
    url_base = normalizar_url(url)
    cursor.execute("""
    INSERT INTO produtos (nome, url, url_base, menor_preco, menor_preco_url, ultimo_preco)
    VALUES (?, ?, ?, NULL, NULL, NULL)
    """, (nome, url, url_base))
    conn.commit()
    conn.close()


def listar_produtos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, url, url_base, menor_preco, menor_preco_url, ultimo_preco FROM produtos")
    rows = cursor.fetchall()
    conn.close()

    produtos = []
    for row in rows:
        produtos.append({
            "id": row['id'],
            "nome": row['nome'],
            "url": row['url'],
            "url_base": row['url_base'],
            "menor_preco": float(row['menor_preco']) if row['menor_preco'] is not None else None,
            "menor_preco_url": row['menor_preco_url'],
            "ultimo_preco": float(row['ultimo_preco']) if row['ultimo_preco'] is not None else None,
        })

    return produtos


def atualizar_url_base(produto_id, url_base):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE produtos SET url_base = ? WHERE id = ?", (url_base, produto_id))
    conn.commit()
    conn.close()


def listar_produtos_por_base(url_base):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, url, url_base, menor_preco, menor_preco_url, ultimo_preco FROM produtos WHERE url_base = ?",
        (url_base,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [{
        "id": row['id'],
        "nome": row['nome'],
        "url": row['url'],
        "url_base": row['url_base'],
        "menor_preco": float(row['menor_preco']) if row['menor_preco'] is not None else None,
        "menor_preco_url": row['menor_preco_url'],
        "ultimo_preco": float(row['ultimo_preco']) if row['ultimo_preco'] is not None else None,
    } for row in rows]


def definir_menor_preco(produto_id, menor_preco, menor_preco_url=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE produtos SET menor_preco = ?, menor_preco_url = ? WHERE id = ?",
        (menor_preco, menor_preco_url, produto_id)
    )
    conn.commit()
    conn.close()


def excluir_produto(produto_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()


def atualizar_preco(produto_id, preco, menor_preco=None, menor_preco_url=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT menor_preco, menor_preco_url FROM produtos WHERE id = ?", (produto_id,))
    resultado = cursor.fetchone()
    atual_menor = resultado['menor_preco'] if resultado else None
    atual_menor_url = resultado['menor_preco_url'] if resultado else None

    # Atualiza menor preço histórico se o novo for menor
    novo_menor = atual_menor
    novo_menor_url = atual_menor_url

    candidato = menor_preco if menor_preco is not None else preco
    candidato_url = menor_preco_url

    if novo_menor is None or candidato < novo_menor:
        novo_menor = candidato
        novo_menor_url = candidato_url

    cursor.execute("""
    UPDATE produtos
    SET ultimo_preco = ?, menor_preco = ?, menor_preco_url = ?
    WHERE id = ?
    """, (preco, novo_menor, novo_menor_url, produto_id))

    conn.commit()
    conn.close()