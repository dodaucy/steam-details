import httpx


http_client = httpx.AsyncClient()
http_client.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0"


def price_string_to_float(price_string: str) -> float:
    return float(price_string.replace("€", "").replace(" ", "").replace(",", "."))
