import httpx


http_client = httpx.AsyncClient()
http_client.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0"


def display_time(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02}:{minutes:02}"


def price_string_to_float(price_string: str) -> float:
    return float(price_string.replace("€", "").replace(" ", "").replace(",", "."))
