import httpx, json
class VOSClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(timeout=timeout)
    def path_url(self, path: str) -> str:
        if not path.startswith('/'):
            path = '/' + path
        return f"{self.base_url}{path}"
    def post(self, path: str, payload: dict = None) -> dict:
        url = self.path_url(path)
        headers = {"Content-Type": "text/html;charset=UTF-8"}
        try:
            r = self.client.post(url, content=json.dumps(payload or {}), headers=headers)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"retCode": -1, "exception": str(e)}
