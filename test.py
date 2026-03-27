#!/usr/bin/env python3
"""
Script de teste para o Price Tracker
Testa funcionalidades principais sem afetar o banco real
"""

import os
import sys
import requests
from config import DISCORD_WEBHOOK_URL

def testar_webhook():
    """Testa se o webhook Discord está funcionando"""
    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL não configurado")
        return False

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json={
            "content": "🧪 **Teste Price Tracker**\nWebhook funcionando! ✅"
        }, timeout=10)
        response.raise_for_status()
        print("✅ Webhook Discord OK")
        return True
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return False

def testar_scraper():
    """Testa o scraper com uma URL conhecida"""
    from scrappers.mercado_livre import pegar_preco

    # URL de teste (pode mudar)
    url_teste = "https://www.mercadolivre.com.br/essencial-atrai-deo-parfum-masculino-100-ml/p/MLB123456789"

    try:
        preco = pegar_preco(url_teste)
        if preco:
            print(f"✅ Scraper OK - Preço encontrado: R$ {preco:.2f}")
            return True
        else:
            print("⚠️ Scraper retornou None (URL pode estar inválida)")
            return False
    except Exception as e:
        print(f"❌ Erro no scraper: {e}")
        return False

def testar_banco():
    """Testa conexão com banco de dados"""
    try:
        from database.db import init_db, get_connection
        init_db()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM produtos")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Banco OK - {count} produtos cadastrados")
        return True
    except Exception as e:
        print(f"❌ Erro no banco: {e}")
        return False

def main():
    print("🧪 **Testando Price Tracker**\n")

    tests = [
        ("Banco de Dados", testar_banco),
        ("Webhook Discord", testar_webhook),
        ("Scraper Mercado Livre", testar_scraper),
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        print(f"🔍 Testando {name}...")
        if test_func():
            passed += 1
        print()

    print(f"📊 Resultado: {passed}/{total} testes passaram")

    if passed == total:
        print("🎉 Tudo funcionando! Pronto para usar.")
        print("\n💡 Comandos:")
        print("   python web.py        # Interface web")
        print("   python app.py        # Atualização CLI")
    else:
        print("⚠️ Alguns testes falharam. Verifique configurações.")

if __name__ == "__main__":
    main()