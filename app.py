from database.db import init_db
from database.models import listar_produtos, atualizar_preco
from scrappers.mercado_livre import pegar_preco

init_db()

produtos = listar_produtos()

for p in produtos:
    preco = pegar_preco(p["url"])

    if preco:
        print(f'{p["nome"]} -> R$ {preco}')

        if p["menor_preco"] is None or preco < p["menor_preco"]:
            print("🔥 PROMOÇÃO DETECTADA!")

        atualizar_preco(p["id"], preco)

    else:
        print(f'{p["nome"]} -> Erro ao pegar preço')