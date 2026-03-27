from database.db import init_db
from database.models import listar_produtos, atualizar_preco
from scrappers.mercado_livre import pegar_preco
from services.discord_alert import enviar_alerta_discord

init_db()

produtos = listar_produtos()

for p in produtos:
    preco = pegar_preco(p["url"])

    if preco:
        print(f'{p["nome"]} -> R$ {preco}')

        if p["menor_preco"] is None or preco < p["menor_preco"] or True:  # adicione "or True"
            print("🔥 PROMOÇÃO DETECTADA!")
            print(f'💰 {p["nome"]} agora está por R$ {preco}')
            enviar_alerta_discord(p["nome"], preco, p["url"])

        atualizar_preco(p["id"], preco)

    else:
        print(f'{p["nome"]} -> Erro ao pegar preço')