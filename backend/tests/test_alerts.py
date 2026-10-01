import pytest
import time
from app.services.alerts import AlertDispatcher

def test_alert_deduplication():
    # Use in-memory mode by passing invalid URI to avoid needing real mongo for unit test
    dispatcher = AlertDispatcher(mongo_uri="mongodb://invalid:27017/", cooldown_seconds=2)
    
    # 1. Fire first alert (should pass)
    res1 = dispatcher.dispatch(lat=20.0, lon=70.0, severity="High", reason="Test", run_id="test1")
    assert res1 is True
    assert len(dispatcher._in_memory_alerts) == 1
    
    # 2. Fire identical alert immediately (should be deduplicated)
    res2 = dispatcher.dispatch(lat=20.0, lon=70.0, severity="High", reason="Test", run_id="test2")
    assert res2 is False
    assert len(dispatcher._in_memory_alerts) == 1
    
    # 3. Fire alert in different location (should pass)
    res3 = dispatcher.dispatch(lat=21.0, lon=70.0, severity="High", reason="Test", run_id="test3")
    assert res3 is True
    assert len(dispatcher._in_memory_alerts) == 2
    
    # 4. Wait for cooldown and fire first location again
    time.sleep(2.1)
    res4 = dispatcher.dispatch(lat=20.0, lon=70.0, severity="High", reason="Test", run_id="test4")
    assert res4 is True
    assert len(dispatcher._in_memory_alerts) == 3

def test_geowithin_query():
    dispatcher = AlertDispatcher(mongo_uri="mongodb://invalid:27017/")
    # Manually populate
    dispatcher.dispatch(lat=20.0, lon=70.0, severity="High", reason="Test1", run_id="test1")
    
    # Test fallback query logic (just returns all in memory for fallback)
    res = dispatcher.query_alerts(bbox=[60, 10, 80, 30])
    assert len(res) == 1
    assert res[0]["properties"]["severity"] == "High"
