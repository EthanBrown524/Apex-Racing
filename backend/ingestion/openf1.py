import requests


BASE_URL = "https://api.openf1.org/v1"


def get_sessions(year: int = 2026) -> list[dict]:
    response = requests.get(f"{BASE_URL}/sessions", params={"year": year}, timeout=30)
    response.raise_for_status()
    return response.json()

