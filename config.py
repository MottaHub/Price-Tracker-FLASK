import os

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

# Debug friendly (não loga o token inteiro)
if DISCORD_WEBHOOK_URL:
    print(f"[DEBUG] DISCORD_WEBHOOK_URL detectado: {DISCORD_WEBHOOK_URL[:40]}... ({len(DISCORD_WEBHOOK_URL)} chars)")
else:
    print("[WARN] DISCORD_WEBHOOK_URL não definido. Configure em variáveis de ambiente para ativar alertas do Discord.")
