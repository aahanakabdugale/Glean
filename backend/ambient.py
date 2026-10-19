"""
backend/ambient.py — Proactive Ambient Push & Event Watcher Engine.

Provides an asynchronous Server-Sent Events (SSE) notification broker and
temporal rule evaluator for real-time, unsolicited ambient alerts to Alexa+ devices.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
from typing import AsyncGenerator

from backend import db

logger = logging.getLogger(__name__)


def evaluate_proactive_alerts(conn=None) -> list[dict]:
    """Audit family state for immediate temporal and bureaucratic alerts."""
    if conn is None:
        conn = db.get_connection()

    db.align_demo_dates(conn)
    today = datetime.date.today()
    alerts: list[dict] = []

    try:
        # 1. Document Expirations
        docs = conn.execute(
            "SELECT d.id, d.doc_type, d.expiry_date, m.name as owner_name, m.relation "
            "FROM documents d JOIN family_members m ON m.id = d.member_id "
            "ORDER BY d.expiry_date ASC"
        ).fetchall()

        for d in docs:
            exp = datetime.date.fromisoformat(d["expiry_date"])
            days_left = (exp - today).days

            if days_left < 0:
                alerts.append({
                    "id": f"doc-exp-{d['id']}",
                    "category": "document_expired",
                    "urgency": "critical",
                    "title": f"Expired Document: {d['owner_name']}'s {d['doc_type']}",
                    "member": d["owner_name"],
                    "doc_type": d["doc_type"],
                    "days": days_left,
                    "date": d["expiry_date"],
                    "speech": f"Attention: {d['owner_name']}'s {d['doc_type']} expired {-days_left} days ago. This blocks official scheme applications.",
                    "prompt": f"Audit document dependencies and blockers for {d['owner_name']}",
                    "suggested_action": f"Audit document dependencies and blockers for {d['owner_name']}",
                    "action_label": "Audit Blockers",
                    "timestamp": datetime.datetime.now().isoformat(),
                })
            elif days_left <= 7:
                alerts.append({
                    "id": f"doc-crit-{d['id']}",
                    "category": "document_expiring_critical",
                    "urgency": "critical",
                    "title": f"Emergency Expiry: {d['owner_name']}'s {d['doc_type']} ({days_left}d left)",
                    "member": d["owner_name"],
                    "doc_type": d["doc_type"],
                    "days": days_left,
                    "date": d["expiry_date"],
                    "speech": f"Heads up: {d['owner_name']}'s {d['doc_type']} expires in {days_left} days. Immediate renewal is recommended to avoid travel or benefit lockouts.",
                    "prompt": f"Check expiring {d['doc_type']} for {d['owner_name']}",
                    "suggested_action": f"Check expiring {d['doc_type']} for {d['owner_name']}",
                    "action_label": "Renew Now",
                    "timestamp": datetime.datetime.now().isoformat(),
                })
            elif days_left <= 30:
                alerts.append({
                    "id": f"doc-soon-{d['id']}",
                    "category": "document_expiring_soon",
                    "urgency": "warning",
                    "title": f"Expiring Soon: {d['owner_name']}'s {d['doc_type']} ({days_left}d left)",
                    "member": d["owner_name"],
                    "doc_type": d["doc_type"],
                    "days": days_left,
                    "date": d["expiry_date"],
                    "speech": f"Reminder: {d['owner_name']}'s {d['doc_type']} expires on {d['expiry_date']}.",
                    "prompt": f"Check expiring {d['doc_type']} for {d['owner_name']}",
                    "suggested_action": f"Check expiring {d['doc_type']} for {d['owner_name']}",
                    "action_label": "View Expiries",
                    "timestamp": datetime.datetime.now().isoformat(),
                })

        # 2. Overdue / Due-Today Tasks
        tasks = conn.execute(
            "SELECT t.id, t.title, t.due_date, m.name as owner_name "
            "FROM tasks t LEFT JOIN family_members m ON m.id = t.member_id "
            "ORDER BY t.due_date ASC"
        ).fetchall()

        for t in tasks:
            due = datetime.date.fromisoformat(t["due_date"])
            days_left = (due - today).days

            if days_left < 0:
                who = f" for {t['owner_name']}" if t["owner_name"] else ""
                alerts.append({
                    "id": f"task-overdue-{t['id']}",
                    "category": "task_overdue",
                    "urgency": "critical",
                    "title": f"Overdue Deadline: {t['title']}{who}",
                    "member": t["owner_name"] or "Household",
                    "days": days_left,
                    "date": t["due_date"],
                    "speech": f"Notice: The task '{t['title']}' is overdue by {-days_left} days.",
                    "prompt": f"What tasks are coming up for {t['owner_name']}?" if t["owner_name"] else "What tasks are coming up in the next 30 days?",
                    "suggested_action": f"What tasks are coming up for {t['owner_name']}?" if t["owner_name"] else "What tasks are coming up in the next 30 days?",
                    "action_label": "View Tasks",
                    "timestamp": datetime.datetime.now().isoformat(),
                })
            elif days_left == 0:
                who = f" for {t['owner_name']}" if t["owner_name"] else ""
                alerts.append({
                    "id": f"task-today-{t['id']}",
                    "category": "task_due_today",
                    "urgency": "warning",
                    "title": f"Due Today: {t['title']}{who}",
                    "member": t["owner_name"] or "Household",
                    "days": 0,
                    "date": t["due_date"],
                    "speech": f"Reminder: The task '{t['title']}' is due today.",
                    "prompt": f"What tasks are coming up for {t['owner_name']}?" if t["owner_name"] else "What tasks are coming up in the next 30 days?",
                    "suggested_action": f"What tasks are coming up for {t['owner_name']}?" if t["owner_name"] else "What tasks are coming up in the next 30 days?",
                    "action_label": "View Tasks",
                    "timestamp": datetime.datetime.now().isoformat(),
                })

    except Exception as exc:
        logger.error("evaluate_proactive_alerts failed: %s", exc)

    return alerts


class AmbientBroker:
    """Manages active Server-Sent Events (SSE) connections and broadcasts ambient push alerts."""

    def __init__(self):
        self._subscribers: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        logger.info("New ambient client connected. Active subscribers: %d", len(self._subscribers))
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers.discard(q)
        logger.info("Ambient client disconnected. Active subscribers: %d", len(self._subscribers))

    async def broadcast_alert(self, alert_data: dict):
        """Send an ambient alert to all connected SSE clients."""
        payload = f"event: ambient_alert\ndata: {json.dumps(alert_data)}\n\n"
        dead_queues = []
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except Exception:
                dead_queues.append(q)

        for dq in dead_queues:
            self.unsubscribe(dq)

    async def event_generator(self, q: asyncio.Queue) -> AsyncGenerator[str, None]:
        """Yield SSE frames to client, with an immediate handshake and heartbeat."""
        try:
            # Send initial connected handshake with active alerts
            initial_alerts = evaluate_proactive_alerts()
            init_payload = {
                "type": "handshake",
                "message": "Ambient Push SSE Stream Active",
                "pending_alerts_count": len(initial_alerts),
                "top_alerts": initial_alerts[:3],
                "timestamp": datetime.datetime.now().isoformat(),
            }
            yield f"event: handshake\ndata: {json.dumps(init_payload)}\n\n"

            # If there's an immediate critical alert, push it right away
            if initial_alerts:
                top_alert = initial_alerts[0]
                yield f"event: ambient_alert\ndata: {json.dumps(top_alert)}\n\n"

            while True:
                try:
                    # Wait for next event or 15s heartbeat
                    msg = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield msg
                except asyncio.TimeoutError:
                    # SSE heartbeat keep-alive comment
                    yield ": ping\n\n"
        finally:
            self.unsubscribe(q)


# Singleton broker instance
ambient_broker = AmbientBroker()
