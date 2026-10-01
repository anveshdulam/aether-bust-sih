import pytest
import json
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_live_replay():
    # We will test the SSE endpoint using httpx
    # NOTE: Since we don't have a true event loop for streaming in a simple test,
    # we can just consume the generator manually or via HTTPx async client.
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # We pass a negative speed multiplier to trigger the gap simulation
        response = await ac.get("/api/v1/live/replay?speed=-1.0")
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        
        # Collect events
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
                
        # We should have 10 time steps + 1 complete event
        assert len(events) >= 10
        
        # Check that gap simulation triggered
        has_gap = any(e.get("status") == "missing_data" for e in events)
        assert has_gap
        
        # Check that latency was measured on normal frames
        normal_frames = [e for e in events if e.get("status") == "playing"]
        assert len(normal_frames) > 0
        assert "dispatch_latency_ms" in normal_frames[0]
        assert normal_frames[0]["dispatch_latency_ms"] >= 0
