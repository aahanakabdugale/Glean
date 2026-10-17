"""
Tests for Proactive Ambient Push & Event Watcher Engine (backend/ambient.py).
Validates temporal rule evaluations, critical expiry alerts, overdue tasks,
SSE event framing, and the trigger_proactive_ambient_alert MCP tool.
"""

import asyncio
import datetime as _dt
import json
import sqlite3
import pytest

import backend.db as glean_db
from backend.ambient import AmbientBroker, evaluate_proactive_alerts
from backend.tools import (
    add_document,
    add_family_member,
    add_task,
    trigger_proactive_ambient_alert,
)


@pytest.fixture
def db_conn(monkeypatch):
    """In-memory SQLite DB fixture isolated for each test."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    glean_db.init_db(conn)

    monkeypatch.setattr(glean_db, "get_connection", lambda *args, **kwargs: conn)
    yield conn


def test_evaluate_expired_document_alert(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")
    today = _dt.date.today()
    past_date = (today - _dt.timedelta(days=12)).isoformat()
    add_document("Passport", "Chandler", past_date)

    alerts = evaluate_proactive_alerts(db_conn)
    assert len(alerts) >= 1
    expired = next(a for a in alerts if a["category"] == "document_expired")
    assert expired["urgency"] == "critical"
    assert expired["member"] == "Chandler"
    assert expired["days"] == -12
    assert "expired 12 days ago" in expired["speech"]


def test_evaluate_critical_7d_expiry(db_conn):
    add_family_member("Justin", "father", 1968, "employed")
    today = _dt.date.today()
    near_date = (today + _dt.timedelta(days=6)).isoformat()
    add_document("Driving License", "Justin", near_date)

    alerts = evaluate_proactive_alerts(db_conn)
    assert len(alerts) >= 1
    crit = next(a for a in alerts if a["category"] == "document_expiring_critical")
    assert crit["urgency"] == "critical"
    assert crit["days"] == 6
    assert "expires in 6 days" in crit["speech"]


def test_evaluate_overdue_task_alert(db_conn):
    add_family_member("Justin", "father", 1968, "employed")
    today = _dt.date.today()
    past_due = (today - _dt.timedelta(days=3)).isoformat()
    add_task("Renew auto insurance", past_due, "Justin")

    alerts = evaluate_proactive_alerts(db_conn)
    task_alert = next(a for a in alerts if a["category"] == "task_overdue")
    assert task_alert["urgency"] == "critical"
    assert task_alert["days"] == -3
    assert "overdue by 3 days" in task_alert["speech"]


def test_trigger_proactive_ambient_alert_tool(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")
    today = _dt.date.today()
    add_document("Passport", "Chandler", (today + _dt.timedelta(days=4)).isoformat())

    res = trigger_proactive_ambient_alert("Chandler")
    assert "PROACTIVE AMBIENT PUSH & TEMPORAL WATCHER" in res
    assert "BROADCASTED TO ALEXA+ AMBIENT STREAM" in res
    assert "CRITICAL" in res
    assert "Echo Show Ambient Canvas" in res
    assert "Voice Synthesizer Speech" in res


def test_trigger_proactive_custom_broadcast(db_conn):
    res = trigger_proactive_ambient_alert(custom_message="Severe weather alert: check family transit passes")
    assert "Severe weather alert: check family transit passes" in res
    assert "BROADCASTED TO ALEXA+ AMBIENT STREAM" in res


@pytest.mark.anyio
async def test_ambient_broker_sse_framing():
    broker = AmbientBroker()
    q = broker.subscribe()

    test_data = {"type": "test_alert", "urgency": "high", "text": "Chime alert"}
    await broker.broadcast_alert(test_data)

    item = await asyncio.wait_for(q.get(), timeout=2.0)
    assert item.startswith("event: ambient_alert\n")
    assert '"text": "Chime alert"' in item
    broker.unsubscribe(q)
