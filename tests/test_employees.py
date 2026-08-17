import pytest
import io

@pytest.mark.asyncio
async def test_employee_crud_and_photo_streaming(client, auth_headers):
    """Verifies full Employee lifecycle: create department, create employee with photo, get detail and stream photo."""
    # 1. Prepare Department
    dept_resp = await client.post(
        "/api/v1/departments",
        json={"code": "DEV-02", "name": "Development Team 2"},
        headers=auth_headers
    )
    assert dept_resp.status_code == 201
    dept_id = dept_resp.json()["id"]

    # 2. Create Employee with Photo
    fake_png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    
    files = {
        "photo": ("avatar.png", io.BytesIO(fake_png_data), "image/png")
    }
    data = {
        "employee_code": "EMP2026999",
        "first_name": "Taro",
        "last_name": "Yamada",
        "email": "taro.yamada@example.com",
        "department_id": str(dept_id),
        "phone": "090-1111-2222",
        "address": "Tokyo Chiyoda",
        "birth_date": "1990-01-01"
    }

    create_emp_resp = await client.post(
        "/api/v1/employees",
        data=data,
        files=files,
        headers=auth_headers
    )
    assert create_emp_resp.status_code == 201
    emp_data = create_emp_resp.json()
    emp_id = emp_data["id"]
    assert emp_data["employee_code"] == "EMP2026999"
    assert emp_data["email"] == "taro.yamada@example.com"
    assert emp_data["photo_url"] is not None

    # 3. Get Employee Detail
    detail_resp = await client.get(f"/api/v1/employees/{emp_id}", headers=auth_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["employee_code"] == "EMP2026999"

    # 4. Stream and Decrypt Photo
    photo_resp = await client.get(f"/api/v1/employees/{emp_id}/photo", headers=auth_headers)
    assert photo_resp.status_code == 200
    assert photo_resp.headers["content-type"].startswith("image/")
    assert photo_resp.content == fake_png_data

@pytest.mark.asyncio
async def test_employee_list_pagination(client, auth_headers):
    """Verifies listing employees with query params."""
    list_resp = await client.get("/api/v1/employees?skip=0&limit=10", headers=auth_headers)
    assert list_resp.status_code == 200
    employees = list_resp.json()
    assert isinstance(employees, list)
