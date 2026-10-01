import asyncio
import json
import logging
import time
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import numpy as np

from app.ml.inference import InferenceRunner
from app.services.alerts import AlertDispatcher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/live", tags=["live"])

# Instantiate globally for the router
runner = InferenceRunner()
dispatcher = AlertDispatcher()

async def event_generator(request: Request, speed_multiplier: float = 1.0):
    """
    Generator for Server-Sent Events. Replays the latest run frame by frame.
    """
    logger.info("Starting live replay stream...")
    
    # In a real system, we'd grab the latest run_id from the DB.
    # For demo, we use a fixed demo run or generate a synthetic one on the fly.
    run_id = "demo_live_feed"
    
    # 1. Run inference (this might block, but it's done once per feed start, 
    # ideally should be in a background task threadpool)
    result = runner.run(run_id)
    
    T, H, W = result.confidence.shape
    
    for t in range(T):
        if await request.is_disconnected():
            logger.info("Client disconnected from live feed.")
            break
            
        # Simulate missing data / gap handling
        if speed_multiplier < 0 and t % 3 == 0:
            logger.warning(f"Simulating missing data gap at time step {t}")
            yield f"event: gap\nid: {t}\ndata: {json.dumps({'time_step': t, 'status': 'missing_data'})}\n\n"
            continue

        start_time = time.perf_counter()
        
        # Extract frame data
        frame_conf = result.confidence[t]
        frame_sev = result.severity[t] if getattr(result, "severity", None) is not None else np.zeros((H, W))
        
        # Dispatch alerts for High/Critical cells in this frame
        high_risk_y, high_risk_x = np.where(frame_sev >= 2)
        
        alerts_fired = 0
        for y, x in zip(high_risk_y, high_risk_x):
            # Convert grid x,y to lat/lon (mock mapping: India ~ 68E-98E, 8N-38N)
            lon = 68.0 + (x / 128.0) * 30.0
            lat = 8.0 + ((127 - y) / 128.0) * 30.0
            
            sev_str = "Critical" if frame_sev[y, x] == 3 else "High"
            
            # Dispatch
            fired = dispatcher.dispatch(
                lat=lat, 
                lon=lon, 
                severity=sev_str, 
                reason=f"Live feed detected {sev_str} bust risk.", 
                run_id=run_id
            )
            if fired:
                alerts_fired += 1
                
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Send SSE payload
        payload = {
            "time_step": t,
            "max_confidence": float(np.max(frame_conf)),
            "alerts_fired": alerts_fired,
            "dispatch_latency_ms": latency_ms,
            "status": "playing"
        }
        
        yield f"event: message\nid: {t}\ndata: {json.dumps(payload)}\n\n"
        
        # Configurable speed: base wait 1 second
        await asyncio.sleep(1.0 / speed_multiplier)
        
    # Send completion event
    yield f"event: complete\ndata: {json.dumps({'status': 'done'})}\n\n"

@router.get("/replay")
async def live_replay(request: Request, speed: float = 1.0):
    """
    SSE Endpoint for real-time live replay of bust detections.
    """
    return StreamingResponse(event_generator(request, speed_multiplier=speed), media_type="text/event-stream")

@router.get("/alerts")
async def get_alerts(min_lon: float, min_lat: float, max_lon: float, max_lat: float):
    """
    REST endpoint to query stored alerts using MongoDB $geoWithin.
    """
    return dispatcher.query_alerts([min_lon, min_lat, max_lon, max_lat])
