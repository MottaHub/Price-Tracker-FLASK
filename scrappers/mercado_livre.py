import requests
from bs4 import BeautifulSoup


def pegar_preco(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Erro {response.status_code} ao acessar página")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # classe atual do Mercado Livre (pode mudar no futuro)
    price = soup.find("span", class_="andes-money-amount__fraction")

    if price:
        return float(price.text.replace(".", "").replace(",", "."))
    
    return None