from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from database.db import ensure_db
from database.models import (
    listar_produtos, adicionar_produto, normalizar_url,
    listar_produtos_por_base, atualizar_preco, definir_menor_preco,
    atualizar_url_base, excluir_produto
)
from scrappers.mercado_livre import pegar_precos_completo
from services.discord_alert import enviar_alerta_discord

app = Flask(__name__)
ensure_db()


@app.route('/')
def index():
    produtos = listar_produtos()
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    return render_template('index.html', produtos=produtos, now=now)


@app.route('/adicionar', methods=['POST'])
def adicionar():
    nome = request.form['nome']
    url  = request.form['url']
    adicionar_produto(nome, url)
    return redirect(url_for('index'))


@app.route('/excluir/<int:produto_id>', methods=['POST'])
def excluir(produto_id):
    excluir_produto(produto_id)
    return redirect(url_for('index'))


@app.route('/atualizar_precos')
def atualizar_precos():
    produtos  = listar_produtos()
    alertas   = []
    analisados = set()

    for p in produtos:
        base = normalizar_url(p['url'])
        if base in analisados:
            continue
        analisados.add(base)

        grupo = listar_produtos_por_base(base)

        for prod in grupo:
            if not prod['url_base']:
                atualizar_url_base(prod['id'], normalizar_url(prod['url']))

            resultado = pegar_precos_completo(prod['url'], nome_produto=prod['nome'])
            preco_atual   = resultado['preco_atual']
            menor_preco   = resultado['menor_preco']
            menor_preco_url = resultado['menor_preco_url']

            if preco_atual is None:
                alertas.append(f"❌ Erro ao pegar preço de {prod['nome']}")
                continue

            # Alerta se o preço atual caiu abaixo do menor histórico
            if prod['menor_preco'] is None or preco_atual < prod['menor_preco']:
                alertas.append(f"🔥 {prod['nome']} caiu para R$ {preco_atual:.2f}")
                enviar_alerta_discord(prod['nome'], preco_atual, prod['url'])

            atualizar_preco(
                prod['id'],
                preco=preco_atual,
                menor_preco=menor_preco,
                menor_preco_url=menor_preco_url
            )

    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    return render_template('index.html', produtos=listar_produtos(), alertas=alertas, now=now)


if __name__ == '__main__':
    app.run(debug=True)