from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from database.db import ensure_db
from database.models import listar_produtos, adicionar_produto, normalizar_url, listar_produtos_por_base, atualizar_preco, definir_menor_preco
from scrappers.mercado_livre import pegar_preco
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
    url = request.form['url']
    
    adicionar_produto(nome, url)
    
    return redirect(url_for('index'))

@app.route('/atualizar_precos')
def atualizar_precos():
    produtos = listar_produtos()
    alertas_enviados = []
    analisados = set()

    for p in produtos:
        base = normalizar_url(p['url'])
        if base in analisados:
            continue

        analisados.add(base)
        grupo = listar_produtos_por_base(base)

        precos_por_produto = {}
        for prod in grupo:
            preco = pegar_preco(prod['url'])
            if preco is not None:
                precos_por_produto[prod['id']] = preco
            else:
                alertas_enviados.append(f"❌ Erro ao pegar preço de {prod['nome']}")

        if not precos_por_produto:
            continue

        melhor_preco = min(precos_por_produto.values())

        for prod in grupo:
            if prod['id'] in precos_por_produto:
                atual = precos_por_produto[prod['id']]
                if prod['menor_preco'] is None or atual < prod['menor_preco']:
                    alertas_enviados.append(f"🔥 {prod['nome']} caiu para R$ {atual:.2f}")
                    enviar_alerta_discord(prod['nome'], atual, prod['url'])
                atualizar_preco(prod['id'], atual)

            if prod['menor_preco'] is None or melhor_preco < prod['menor_preco']:
                definir_menor_preco(prod['id'], melhor_preco)

    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    return render_template('index.html', produtos=listar_produtos(), alertas=alertas_enviados, now=now)

if __name__ == '__main__':
    app.run(debug=True)