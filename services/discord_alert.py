import requests
from config import DISCORD_WEBHOOK_URL


def enviar_alerta_discord(nome, preco, url=None):
    """Envia alerta para Discord via webhook."""
    if not DISCORD_WEBHOOK_URL:
        print("[WARN] DISCORD_WEBHOOK_URL não configurado; alerta Discord ignorado.")
        return

    texto = f"🔥 **PROMOÇÃO!**\n{nome} caiu para **R$ {preco:.2f}**"
    if url:
        texto += f"\n{url}"

    payload = {
        "content": texto
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        print(f"[Discord] Alerta enviado: {nome} -> R$ {preco:.2f}")
    except requests.exceptions.RequestException as e:
        print(f"[Erro Discord] Falha ao enviar alerta: {e}")
