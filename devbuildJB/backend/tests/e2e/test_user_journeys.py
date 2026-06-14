"""
End-to-end journeys — full flows through the live API stack (DB + agents + routes).
"""

import json
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_login_submit_and_fetch_task(client: AsyncClient):
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin1234"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    submit = await client.post(
        "/api/v1/tasks",
        json={"task_text": "Calculate 100 + 23", "mode": "single"},
        headers=headers,
    )
    assert submit.status_code == 200
    task_id = submit.json()["id"]
    assert submit.json()["result"] == "123"

    fetch = await client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert fetch.status_code == 200
    assert fetch.json()["status"] == "completed"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_smart_multi_routing(client: AsyncClient, admin_headers: dict):
    payload = {
        "task_text": "Calculate 5 + 10\nConvert \"demo\" to uppercase",
        "mode": "smart_multi",
    }
    response = await client.post("/api/v1/tasks", json=payload, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "15" in data["result"]
    assert "DEMO" in data["result"]
    step_types = {s["step_type"] for s in data["execution_steps"]}
    assert "workflow" in step_types
    assert "execution" in step_types


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_weather_with_retry_recovery(client: AsyncClient, admin_headers: dict):
    response = await client.post(
        "/api/v1/tasks",
        json={"task_text": "What is the weather in London?", "mode": "single"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "London" in data["result"]
    retry_steps = [s for s in data["execution_steps"] if s["step_type"] == "retry"]
    assert len(retry_steps) >= 1


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_division_by_zero_with_trace(client: AsyncClient, admin_headers: dict):
    response = await client.post(
        "/api/v1/tasks",
        json={"task_text": "5 / 0", "mode": "single"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    error = json.loads(data["result"])
    assert error["error"] == "Division by zero"
    assert any(s["step_type"] in ("execution", "error") for s in data["execution_steps"])


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_legacy_chain_workflow(client: AsyncClient, admin_headers: dict):
    response = await client.post(
        "/api/v1/tasks",
        json={"task_text": "Calculate 10*2 and convert to uppercase", "mode": "single"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "TWENTY" in data["result"].upper()
    tools = [s["tool_name"] for s in data["execution_steps"] if s.get("tool_name")]
    assert "Calculator" in tools
    assert "TextProcessor" in tools
