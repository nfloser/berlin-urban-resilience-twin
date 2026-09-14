import httpx
import pytest

from urban_resilience_twin.persistence.fuseki import FusekiClient


@pytest.mark.asyncio
async def test_fuseki_client_publishes_validated_turtle_to_dataset() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = request.content.decode()
        return httpx.Response(200, json={"ok": True})

    client = FusekiClient("http://fuseki:3030", transport=httpx.MockTransport(handler))
    await client.publish_turtle("@prefix ex: <https://example.org/> . ex:a ex:b ex:c .")
    assert seen["method"] == "PUT"
    assert seen["path"] == "/resilience/data"
    assert "ex:a" in seen["body"]
