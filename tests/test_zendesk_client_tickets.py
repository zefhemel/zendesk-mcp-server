"""
Tests for the ticket fields the read tools return.

Tags set through create_ticket/update_ticket must also come back from
get_ticket and get_tickets, otherwise they look lost to MCP clients.
"""
import json
import urllib.request

import pytest
import responses

from zendesk_mcp_server.zendesk_client import ZendeskClient

SUBDOMAIN = "example"
BASE = f"https://{SUBDOMAIN}.zendesk.com/api/v2"


@pytest.fixture
def client():
    return ZendeskClient(subdomain=SUBDOMAIN, email="agent@example.com", token="t")


def ticket_payload(ticket_id, tags):
    return {
        "id": ticket_id,
        "subject": "Broken boiler",
        "description": "It is cold",
        "status": "open",
        "priority": "high",
        "created_at": "2026-10-01T10:00:00Z",
        "updated_at": "2026-10-02T10:00:00Z",
        "requester_id": 1,
        "assignee_id": 2,
        "organization_id": 3,
        "tags": tags,
    }


class FakeUrlopenResponse:
    def __init__(self, payload: dict):
        self._payload = json.dumps(payload).encode()

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


@responses.activate
def test_get_ticket_returns_tags(client):
    responses.add(
        responses.GET,
        f"{BASE}/tickets/42.json",
        json={"ticket": ticket_payload(42, ["vip", "boiler"])},
    )

    ticket = client.get_ticket(42)

    assert ticket["tags"] == ["vip", "boiler"]


@responses.activate
def test_get_ticket_returns_empty_tags_when_none(client):
    responses.add(
        responses.GET,
        f"{BASE}/tickets/42.json",
        json={"ticket": ticket_payload(42, [])},
    )

    assert client.get_ticket(42)["tags"] == []


def test_get_tickets_returns_tags(client, monkeypatch):
    payload = {
        "tickets": [ticket_payload(1, ["vip"]), ticket_payload(2, [])],
        "next_page": None,
    }
    monkeypatch.setattr(
        urllib.request, "urlopen", lambda *a, **kw: FakeUrlopenResponse(payload)
    )

    result = client.get_tickets()

    assert [t["tags"] for t in result["tickets"]] == [["vip"], []]
