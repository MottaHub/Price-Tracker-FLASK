from flask import Flask, render_template, request, redirect, url_for
from database.db import init_db
from database.models import listar_produtos, adicionar_produto
from scrappers.mercado_livre import pegar_preco
from services.discord_alert import enviar_alerta_discord

app = Flask(__name__)

init_db()

@app.route('/')
def index():
    produtos = listar_produtos()
    return render_template('index.html', produtos=produtos)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    nome = request.form['nome']
    url = request.form['url']
    
    adicionar_produto(nome, url)
    
    return redirect(url_for('index'))

@app.route('/atualizar_precos')
def atualizar_precos():
    from database.models import atualizar_preco
    
    produtos = listar_produtos()
    alertas_enviados = []
    
    for p in produtos:
        preco = pegar_preco(p["url"])
        
        if preco:
            if p["menor_preco"] is None or preco < p["menor_preco"]:
                alertas_enviados.append(f"🔥 {p['nome']} caiu para R$ {preco:.2f}")
                enviar_alerta_discord(p["nome"], preco, p["url"])
            
            atualizar_preco(p["id"], preco)
        else:
            alertas_enviados.append(f"❌ Erro ao pegar preço de {p['nome']}")
    
    return render_template('index.html', produtos=listar_produtos(), alertas=alertas_enviados)

if __name__ == '__main__':
    app.run(debug=True)