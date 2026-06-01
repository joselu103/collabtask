# src/tests/test_health.py
from httpx import AsyncClient


async def test_health(client: AsyncClient):
    response = await client.get("http://test/api/v1/health")

    assert response.status_code == 200
