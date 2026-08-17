import pytest

@pytest.mark.asyncio
async def test_create_and_get_departments(client, auth_headers):
    """Verifies creating new departments and retrieving list."""
    # 1. Create department
    payload = {
        "code": "DEV-01",
        "name": "Engineering Department"
    }
    create_resp = await client.post("/api/v1/departments", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["code"] == "DEV-01"
    assert created_data["name"] == "Engineering Department"

    # 2. Get list of departments
    list_resp = await client.get("/api/v1/departments", headers=auth_headers)
    assert list_resp.status_code == 200
    depts = list_resp.json()
    assert len(depts) >= 1
    assert any(d["code"] == "DEV-01" for d in depts)

@pytest.mark.asyncio
async def test_upsert_department_on_duplicate_code(client, auth_headers):
    """Verifies that posting existing code updates the department name (UPSERT)."""
    payload1 = {
        "code": "HR-01",
        "name": "Human Resources"
    }
    resp1 = await client.post("/api/v1/departments", json=payload1, headers=auth_headers)
    assert resp1.status_code == 201
    dept_id = resp1.json()["id"]

    # Post same code with updated name
    payload2 = {
        "code": "HR-01",
        "name": "Human Resources & People Ops"
    }
    resp2 = await client.post("/api/v1/departments", json=payload2, headers=auth_headers)
    assert resp2.status_code == 201
    updated_data = resp2.json()
    assert updated_data["id"] == dept_id
    assert updated_data["name"] == "Human Resources & People Ops"
