from database.db import get_connection


def adicionar_produto(nome, url):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO produtos (nome, url, menor_preco, ultimo_preco)
    VALUES (?, ?, NULL, NULL)
    """, (nome, url))

    conn.commit()
    conn.close()


def listar_produtos():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM produtos")
    rows = cursor.fetchall()

    conn.close()

    produtos = []
    for row in rows:
        produtos.append({
            "id": row[0],
            "nome": row[1],
            "url": row[2],
            "menor_preco": row[3],
            "ultimo_preco": row[4]
        })

    return produtos

def atualizar_preco(produto_id, preco):
    conn = get_connection()
    cursor = conn.cursor()

    # pega dados atuais
    cursor.execute("SELECT menor_preco FROM produtos WHERE id = ?", (produto_id,))
    resultado = cursor.fetchone()

    menor_preco = resultado[0]

    # define novo menor preço
    if menor_preco is None or preco < menor_preco:
        menor_preco = preco

    cursor.execute("""
    UPDATE produtos
    SET ultimo_preco = ?, menor_preco = ?
    WHERE id = ?
    """, (preco, menor_preco, produto_id))

    conn.commit()
    conn.close()