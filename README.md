# Price Tracker - Monitor de Preços com Alertas Discord

Um sistema completo para monitorar preços de produtos no Mercado Livre, com alertas automáticos no Discord e painel web para gerenciamento.

## 🚀 Funcionalidades

- ✅ **Scraping automático** de preços do Mercado Livre
- ✅ **Banco de dados SQLite** para armazenar produtos e histórico
- ✅ **Alertas Discord** quando preços caem
- ✅ **Painel web Flask** para visualizar e adicionar produtos
- ✅ **Atualização em lote** de preços via interface

## 📋 Pré-requisitos

- Python 3.8+
- Conta Discord (para webhooks)

## 🛠️ Instalação

1. **Clone/baixe o projeto**
2. **Instale dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure webhook Discord:**
   - No seu servidor Discord: `Configurações > Integrações > Webhooks`
   - Crie um webhook e copie a URL
   - Configure a variável de ambiente:
     ```powershell
     # Windows PowerShell
     $env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/SEU_ID/SEU_TOKEN"
     ```

## 🗄️ Banco de Dados

O projeto usa SQLite. Na primeira execução, o banco é criado automaticamente.

## ▶️ Como Usar

### 1. **Interface Web (Recomendado)**
```bash
python web.py
```
Acesse: http://127.0.0.1:5000

- **Adicionar produtos:** Use o formulário na página
- **Ver produtos:** Lista todos com preços atuais
- **Atualizar preços:** Botão "Atualizar Todos os Preços" (envia alertas se houver promoções)

### 2. **Linha de Comando**
```bash
python app.py
```
- Executa uma vez e sai
- Ideal para agendamento (cron/task scheduler)

## 📊 Estrutura do Projeto

```
price-tracker/
├── app.py                 # Script principal (CLI)
├── web.py                 # Servidor Flask
├── config.py              # Configurações
├── requirements.txt       # Dependências
├── database/
│   ├── db.py             # Conexão BD
│   └── models.py         # Funções BD
├── scrappers/
│   └── mercado_livre.py  # Scraper ML
├── services/
│   └── discord_alert.py  # Alertas Discord
└── templates/
    └── index.html        # Template web
```

## 🔧 Configuração Avançada

### Agendamento Automático

**Windows Task Scheduler:**
- Crie tarefa para executar `python app.py` a cada hora

**Linux/Mac (cron):**
```bash
# Edite crontab
crontab -e
# Adicione:
0 * * * * cd /caminho/para/projeto && python app.py
```

### Variáveis de Ambiente

```powershell
# Windows
$env:DISCORD_WEBHOOK_URL = "https://..."
$env:FLASK_ENV = "development"  # Para debug
```

## 🐛 Troubleshooting

### Erro 404 no scraping
- URLs do Mercado Livre podem mudar
- Verifique se o produto ainda existe
- O seletor CSS pode precisar atualização

### Webhook não funciona
- Verifique se a URL está correta
- Teste com: `python -c "import requests; print(requests.post('URL', json={'content':'teste'}).status_code)"`
- Deve retornar `204`

### Flask não inicia
- Porta 5000 pode estar ocupada
- Mude para: `app.run(port=8000)`

## 📈 Próximas Features

- [ ] Gráficos de histórico de preços
- [ ] Suporte a múltiplas lojas
- [ ] API REST
- [ ] Notificações por email
- [ ] Interface mobile

## 🤝 Contribuição

Sinta-se à vontade para abrir issues e PRs!

## 📄 Licença

MIT License - use como quiser!