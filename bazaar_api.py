import requests

class BazaarAPI:
    BASE_URL = "https://sky.coflnet.com/api/bazaar"

    def get_history(self, item: str, period: str = "hour") -> list:
        url = f"{self.BASE_URL}/{item}/history/{period}"
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()[::-1]

    def get_player_orders(self, player_id: str) -> list:
        url = f"{self.BASE_URL}/player/{player_id}/orders"
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()