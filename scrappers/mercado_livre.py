"""
Scraper do Mercado Livre
- Preço atual : vendedor principal da página
- Menor preço : menor valor encontrado nos blocos de vendedores da página
                (seção "Outras opções de compra" / buybox)
"""

import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'pt-BR,pt;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


# ── HTTP ───────────────────────────────────────────────────────────────────

def _get_soup(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return BeautifulSoup(r.text, 'html.parser')
        print(f'[Scraper] HTTP {r.status_code}')
    except requests.RequestException as e:
        print(f'[Scraper] Erro: {e}')
    return None


# ── Extração de valor monetário ────────────────────────────────────────────

def _valor_do_elemento(el):
    """
    Dado um elemento BeautifulSoup que contém um bloco de preço do ML,
    tenta extrair o float. Funciona com andes-money-amount ou price-tag.
    """
    fraction = el.select_one(
        '.andes-money-amount__fraction, .price-tag-fraction'
    )
    if not fraction:
        return None
    cents = el.select_one(
        '.andes-money-amount__cents, .price-tag-cents'
    )
    texto = fraction.get_text(strip=True)
    if cents:
        texto += ',' + cents.get_text(strip=True).lstrip('.')
    try:
        return float(texto.replace('.', '').replace(',', '.'))
    except ValueError:
        return None


# ── Preço principal ────────────────────────────────────────────────────────

def _preco_principal(soup):
    """Preço do vendedor destacado (topo da página)."""
    for seletor in (
        '.ui-pdp-price__second-line',
        '.ui-pdp-price__main-price',
        '.ui-pdp-price',
    ):
        bloco = soup.select_one(seletor)
        v = _valor_do_elemento(bloco) if bloco else None
        if v:
            return v

    # fallback: primeiro fraction da página
    fraction = soup.find(
        'span', class_=re.compile(r'(price-tag-fraction|andes-money-amount__fraction)')
    )
    if fraction:
        cents = fraction.find_next_sibling(
            'span', class_=re.compile(r'(price-tag-cents|andes-money-amount__cents)')
        )
        texto = fraction.get_text(strip=True)
        if cents:
            texto += ',' + cents.get_text(strip=True).lstrip('.')
        try:
            return float(texto.replace('.', '').replace(',', '.'))
        except ValueError:
            pass
    return None


# ── Menor preço entre outros vendedores ───────────────────────────────────

def _menor_preco_outros_vendedores(soup, preco_principal):
    """
    Busca especificamente os blocos de outros vendedores na página.
    Usa seletores conhecidos do ML e filtra preços de parcelas.
    Retorna (menor_preco, url) ou (None, None).
    """

    # Seletores dos containers de outros vendedores no ML
    SELETORES_CONTAINER = [
        '.ui-pdp-other-sellers__rows',          # lista de vendedores
        '.ui-pdp-buybox__offers',               # ofertas no buybox
        '[class*="other-sellers"]',             # qualquer classe com other-sellers
        '[class*="seller-list"]',
        '[class*="compra-agora"]',
    ]

    # Seletores de cada item/row de vendedor
    SELETORES_ROW = [
        '.ui-pdp-other-sellers__row',
        '.ui-pdp-buybox__offer',
        '[class*="seller-row"]',
        '[class*="offer-row"]',
    ]

    menor_preco = None
    menor_url   = None

    def processar_bloco(bloco):
        nonlocal menor_preco, menor_url

        preco = _valor_do_elemento(bloco)
        if preco is None:
            return

        # Ignora valores menores que 20% do preço principal (provavelmente parcela)
        if preco_principal and preco < preco_principal * 0.20:
            print(f'[Scraper] Ignorando valor suspeito (parcela?): R${preco:.2f}')
            return

        # Tenta pegar link do vendedor dentro do bloco
        link_tag = bloco.select_one('a[href]')
        link = None
        if link_tag:
            href = link_tag.get('href', '')
            if href.startswith('http'):
                link = href
            elif href.startswith('/'):
                link = 'https://www.mercadolivre.com.br' + href

        print(f'[Scraper] Vendedor encontrado: R${preco:.2f} -> {link}')

        if menor_preco is None or preco < menor_preco:
            menor_preco = preco
            menor_url   = link

    # Tenta pelos containers
    encontrou = False
    for seletor in SELETORES_CONTAINER:
        container = soup.select_one(seletor)
        if container:
            encontrou = True
            print(f'[Scraper] Container encontrado: {seletor}')
            for row_sel in SELETORES_ROW:
                rows = container.select(row_sel)
                for row in rows:
                    processar_bloco(row)
            if menor_preco is None:
                # Tenta direto no container
                processar_bloco(container)

    # Fallback: busca todos os blocos de preço que estejam dentro de links
    if not encontrou or menor_preco is None:
        print('[Scraper] Fallback: buscando preços dentro de links...')
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '')
            # Só considera links de produtos ML
            if 'mercadolivre.com.br' not in href and not href.startswith('/'):
                continue
            preco = _valor_do_elemento(a_tag)
            if preco is None:
                continue
            if preco_principal and preco < preco_principal * 0.20:
                continue
            if preco >= (preco_principal or 0):
                continue  # só interessa se for menor que o principal
            if href.startswith('/'):
                href = 'https://www.mercadolivre.com.br' + href
            print(f'[Scraper] Link com preço menor: R${preco:.2f} -> {href[:60]}')
            if menor_preco is None or preco < menor_preco:
                menor_preco = preco
                menor_url   = href

    return menor_preco, menor_url


# ── API pública ────────────────────────────────────────────────────────────

def pegar_preco(url):
    """Retorna apenas o preço principal (compatibilidade com app.py)."""
    return pegar_precos_completo(url)['preco_atual']


def pegar_precos_completo(url, nome_produto=None):
    """
    Retorna dict com:
      - preco_atual    : preço do vendedor principal na URL cadastrada
      - menor_preco    : menor preço encontrado entre outros vendedores
      - menor_preco_url: link direto para o menor preço
    """
    soup = _get_soup(url)
    if soup is None:
        return {'preco_atual': None, 'menor_preco': None, 'menor_preco_url': None}

    preco_atual = _preco_principal(soup)
    print(f'[Scraper] Preço principal: R${preco_atual}')

    menor, menor_url = _menor_preco_outros_vendedores(soup, preco_atual)

    # Só exibe menor preço se for de fato menor que o atual
    if menor is not None and preco_atual is not None and menor >= preco_atual:
        print(f'[Scraper] Nenhum vendedor com preço menor encontrado.')
        menor     = None
        menor_url = None

    if menor:
        print(f'[Scraper] ✅ Menor preço final: R${menor:.2f}')
    else:
        print(f'[Scraper] ℹ️ Sem menor preço disponível.')

    return {
        'preco_atual': preco_atual,
        'menor_preco': menor,
        'menor_preco_url': menor_url,
    }