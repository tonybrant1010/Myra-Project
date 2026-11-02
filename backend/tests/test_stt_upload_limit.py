import pytest
import server


@pytest.mark.anyio
async def test_real_stt_route_allows_audio_larger_than_general_api_limit(client):
    response = await client.post("/api/stt/transcribe", content=b"x" * (server.API_REQUEST_MAX_BYTES + 1),
                                 headers={"Content-Type": "application/octet-stream"})
    assert response.status_code == 401, response.text


@pytest.mark.anyio
async def test_real_stt_route_rejects_above_audio_limit(client):
    response = await client.post("/api/stt/transcribe", content=b"x" * (server.STT_MAX_BYTES + 65537),
                                 headers={"Content-Type": "application/octet-stream"})
    assert response.status_code == 413
