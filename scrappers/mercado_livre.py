"""
Scraper do Mercado Livre
- Preço atual : lido direto da página do produto cadastrado
- Menor preço : raspado das "outras opções de compra" da própria página
               + buscado via API oficial (api.mercadolibre.com)
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'pt-BR,pt;q=0.9',
}

ML_API = 'https://api.mercadolibre.com'

# ── Configuração do filtro de similaridade ─────────────────────────────────

_STOPWORDS = {
    'com', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'para',
    'por', 'e', 'ou', 'a', 'o', 'um', 'uma', 'celular', 'smartphone',
    'perfume', 'deo', 'parfum', 'eau', 'edp', 'edt', 'tela', 'camera',
    'ml', 'gb', 'tb',
}

_DISCRIMINANTES_NEGATIVOS = {
    'refil', 'kit', 'recondicionado', 'seminovo', 'usado', 'reembalado',
    'mini', 'travel', 'amostra', 'combo',
}

_DISCRIMINANTES_GENERO = {'feminino', 'masculino', 'unissex', 'infantil'}

_SUFIXOS_CRITICOS = {'gb', 'tb', 'mb'}

_SCORE_MINIMO = 0.40


# ── Normalização ───────────────────────────────────────────────────────────

def _normalizar(texto):
    texto = texto.lower()
    for origem, dest in [
        ('ã','a'), ('â','a'), ('á','a'), ('à','a'),
        ('ê','e'), ('é','e'), ('è','e'),
        ('í','i'), ('î','i'),
        ('õ','o'), ('ô','o'), ('ó','o'),
        ('ú','u'), ('û','u'), ('ç','c'),
    ]:
        texto = texto.replace(origem, dest)
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)
    return [w for w in texto.split() if w not in _STOPWORDS and len(w) > 1]


def _parse_num(token):
    m = re.match(r'^(\d+)([a-z]*)$', token)
    if m:
        return int(m.group(1)), m.group(2)
    return None, None


# ── Algoritmo de similaridade ──────────────────────────────────────────────

def _score_similaridade(nome_original, titulo_resultado):
    orig_lista  = _normalizar(nome_original)
    resul_lista = _normalizar(titulo_resultado)
    orig  = set(orig_lista)
    resul = set(resul_lista)

    for palavra in _DISCRIMINANTES_NEGATIVOS:
        if palavra in resul and palavra not in orig:
            return 0.0

    genero_orig  = _DISCRIMINANTES_GENERO & orig
    genero_resul = _DISCRIMINANTES_GENERO & resul
    if genero_orig and genero_resul and genero_orig != genero_resul:
        return 0.0

    nums_orig  = {}
    for w in orig_lista:
        v, suf = _parse_num(w)
        if v is not None and suf in _SUFIXOS_CRITICOS:
            nums_orig.setdefault(suf, []).append(v)

    nums_resul = {}
    for w in resul_lista:
        v, suf = _parse_num(w)
        if v is not None and suf in _SUFIXOS_CRITICOS:
            nums_resul.setdefault(suf, []).append(v)

    for suf, vals_orig in nums_orig.items():
        vals_resul = nums_resul.get(suf, [])
        if not vals_resul:
            continue
        for vo in vals_orig:
            for vr in vals_resul:
                ratio = max(vo, vr) / max(min(vo, vr), 1)
                if ratio < 10 and vo != vr:
                    return 0.0

    chaves = [w for w in orig_lista if len(w) >= 4 and not re.search(r'\d', w)]
    if not chaves:
        return 1.0

    # Se o nome original aparece direto no título, aceita
    if nome_original.lower() in titulo_resultado.lower():
        return 1.0

    hits = sum(1 for p in chaves if p in resul)
    return hits / len(chaves)


# ── Preço da página cadastrada ─────────────────────────────────────────────

def _get_soup(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return BeautifulSoup(r.text, 'html.parser')
        print(f'[Scraper] HTTP {r.status_code}')
    except requests.RequestException as e:
        print(f'[Scraper] Erro: {e}')
    return None


def _extrair_preco_do_bloco(bloco):
    if bloco is None:
        return None
    fraction = bloco.select_one('.andes-money-amount__fraction, .price-tag-fraction')
    cents    = bloco.select_one('.andes-money-amount__cents, .price-tag-cents')
    if not fraction:
        return None
    texto = fraction.get_text(strip=True)
    if cents:
        texto += ',' + cents.get_text(strip=True).lstrip('.')
    try:
        return float(texto.replace('.', '').replace(',', '.'))
    except ValueError:
        return None


def _preco_principal(soup):
    for seletor in ('.ui-pdp-price__second-line', '.ui-pdp-price__main-price', '.ui-pdp-price'):
        bloco = soup.select_one(seletor)
        preco = _extrair_preco_do_bloco(bloco)
        if preco:
            return preco
    fraction = soup.find('span', class_=re.compile(r'(price-tag-fraction|andes-money-amount__fraction)'))
    if fraction:
        cents = fraction.find_next_sibling('span', class_=re.compile(r'(price-tag-cents|andes-money-amount__cents)'))
        texto = fraction.get_text(strip=True)
        if cents:
            texto += ',' + cents.get_text(strip=True).lstrip('.')
        try:
            return float(texto.replace('.', '').replace(',', '.'))
        except ValueError:
            pass
    return None


# ── Outras opções de compra da página ─────────────────────────────────────

def _extrair_menor_outras_opcoes(soup, preco_principal=None):
    """
    Raspa a seção 'Outras opções de compra' da página do produto
    e retorna (menor_preco, url_do_vendedor) — apenas se for menor que o principal.
    """
    menor_preco = None
    menor_url   = None

    # Coleta todos os valores de fraction na página
    todos = []
    for fraction in soup.find_all('span', class_=re.compile(r'andes-money-amount__fraction')):
        cents = fraction.find_next_sibling('span', class_=re.compile(r'andes-money-amount__cents'))
        texto = fraction.get_text(strip=True)
        if cents:
            texto += ',' + cents.get_text(strip=True).lstrip('.')
        try:
            valor = float(texto.replace('.', '').replace(',', '.'))
            if valor > 10:  # ignora valores absurdos pequenos
                todos.append(valor)
        except ValueError:
            pass

    if not todos:
        return None, None

    menor = min(todos)
    print(f'[Scraper] Menor preço na página: R${menor:.2f}')

    # Só retorna se for realmente menor que o preço principal
    if preco_principal is not None and menor >= preco_principal:
        return None, None

    return menor, None


# ── Busca via API oficial do ML ────────────────────────────────────────────

def _buscar_menor_via_api(nome_produto, preco_referencia=None, limite=20):
    url = f'{ML_API}/sites/MLB/search?q={quote_plus(nome_produto)}&limit={limite}'

    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            print(f'[API ML] HTTP {r.status_code}')
            return None, None
        dados = r.json()
    except Exception as e:
        print(f'[API ML] Erro: {e}')
        return None, None

    resultados = dados.get('results', [])
    if not resultados:
        print(f'[API ML] Sem resultados para "{nome_produto}"')
        return None, None

    menor_preco = None
    menor_url   = None

    orig_norm = set(_normalizar(nome_produto))

    for item in resultados:
        titulo  = item.get('title', '')
        preco   = item.get('price')
        link    = item.get('permalink')
        cond    = item.get('condition', '')

        if not preco or not link:
            continue

        if cond == 'used' and 'recondicionado' not in orig_norm and 'usado' not in orig_norm:
            continue

        if preco_referencia and preco < preco_referencia * 0.15:
            continue

        score = _score_similaridade(nome_produto, titulo)
        print(f'[API ML] score={score:.2f} R${preco:<8.2f} {titulo[:55]}')

        if score < _SCORE_MINIMO:
            continue

        if menor_preco is None or preco < menor_preco:
            menor_preco = preco
            menor_url   = link

    if menor_preco:
        print(f'[API ML] ✅ Menor aprovado: R${menor_preco:.2f}')
    else:
        print(f'[API ML] ❌ Nenhum resultado passou o filtro')

    return menor_preco, menor_url


# ── API pública ────────────────────────────────────────────────────────────

def pegar_preco(url):
    """Retorna apenas o preço principal (compatibilidade com app.py)."""
    return pegar_precos_completo(url)['preco_atual']


def pegar_precos_completo(url, nome_produto=None):
    """
    Retorna dict com:
      - preco_atual    : preço do vendedor principal na URL cadastrada
      - menor_preco    : menor preço encontrado (outras opções da página + API)
      - menor_preco_url: link direto para o menor preço (ou None se veio da página)
    """
    soup = _get_soup(url)
    if soup is None:
        return {'preco_atual': None, 'menor_preco': None, 'menor_preco_url': None}

    preco_atual = _preco_principal(soup)
    print(f'[Scraper] Preço na URL: R${preco_atual}')

    # 1) Outras opções de compra na própria página
    menor_pagina, menor_pagina_url = _extrair_menor_outras_opcoes(soup, preco_principal=preco_atual)

    # 2) Busca via API
    menor_api, menor_api_url = None, None
    if nome_produto:
        menor_api, menor_api_url = _buscar_menor_via_api(
            nome_produto,
            preco_referencia=preco_atual,
        )

    # Escolhe o menor entre todas as fontes
    candidatos = []
    if menor_pagina is not None:
        candidatos.append((menor_pagina, menor_pagina_url))
    if menor_api is not None:
        candidatos.append((menor_api, menor_api_url))

    if candidatos:
        menor_final, menor_url_final = min(candidatos, key=lambda x: x[0])
    else:
        menor_final, menor_url_final = None, None

    return {
        'preco_atual': preco_atual,
        'menor_preco': menor_final,
        'menor_preco_url': menor_url_final,
    }