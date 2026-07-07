import httpx

http_client = None

def get_http_client():
    return http_client

async def init_http_client():
    global http_client
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0))

async def close_http_client():
    global http_client
    if http_client:
        await http_client.aclose()
