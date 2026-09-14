from __future__ import annotations

import httpx


class FusekiClient:
    def __init__(
        self,
        base_url: str,
        dataset: str = "resilience",
        timeout_s: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.dataset = dataset.strip("/")
        self.timeout_s = timeout_s
        self.transport = transport

    @property
    def dataset_url(self) -> str:
        return f"{self.base_url}/{self.dataset}"

    async def ready(self) -> bool:
        async with httpx.AsyncClient(timeout=self.timeout_s, transport=self.transport) as client:
            try:
                response = await client.get(
                    f"{self.dataset_url}/sparql", params={"query": "ASK {}"}
                )
            except httpx.HTTPError:
                return False
            return response.is_success

    async def publish_turtle(self, turtle: str, graph_uri: str | None = None) -> None:
        params = {"graph": graph_uri} if graph_uri else {"default": ""}
        headers = {"content-type": "text/turtle; charset=utf-8"}
        async with httpx.AsyncClient(timeout=self.timeout_s, transport=self.transport) as client:
            response = await client.put(
                f"{self.dataset_url}/data",
                params=params,
                headers=headers,
                content=turtle.encode("utf-8"),
            )
            response.raise_for_status()

    async def query(self, sparql: str) -> dict:
        headers = {"accept": "application/sparql-results+json"}
        async with httpx.AsyncClient(timeout=self.timeout_s, transport=self.transport) as client:
            response = await client.get(
                f"{self.dataset_url}/sparql",
                params={"query": sparql},
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
