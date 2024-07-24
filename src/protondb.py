from typing import Union

from utils import http_client


async def get_linux_support(appid: str) -> Union[dict, None]:
    print(f"Getting linux support state for {appid}")
    r = await http_client.get(f"https://www.protondb.com/api/v1/reports/summaries/{appid}.json")
    print(f"Response: {r.text}")
    if r.status_code == 404:
        return
    r.raise_for_status()
    data = r.json()
    return {
        "tier": data["tier"].upper(),  # str
        "confidence": data["confidence"],  # str
        "report_count": data["total"],  # int
    }
