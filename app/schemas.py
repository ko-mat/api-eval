from datetime import date, datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field

# --- Department Schemas ---
class DepartmentBase(BaseModel):
    code: str = Field(..., max_length=20, examples=["DEV-01"])
    name: str = Field(..., max_length=100, examples=["開発部 第1グループ"])

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- EmployeeHistory Schemas ---
class EmployeeHistoryBase(BaseModel):
    department_id: int
    role: str = Field(..., max_length=100, examples=["ソフトウェアエンジニア"])
    start_date: date
    end_date: date | None = None

class EmployeeHistoryCreate(EmployeeHistoryBase):
    pass

class EmployeeHistoryResponse(EmployeeHistoryBase):
    id: int
    employee_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Employee Schemas ---
class EmployeeBase(BaseModel):
    employee_code: str = Field(..., max_length=20, examples=["EMP2026001"])
    first_name: str = Field(..., max_length=50, examples=["太郎"])
    last_name: str = Field(..., max_length=50, examples=["山田"])
    email: EmailStr
    department_id: int | None = None
    phone: str | None = Field(None, max_length=100, examples=["090-1234-5678"])
    address: str | None = Field(None, max_length=255, examples=["東京都新宿区"])
    birth_date: str | None = Field(None, max_length=20, examples=["1990-01-01"])

class EmployeeResponse(EmployeeBase):
    id: int
    photo_url: str | None = None
    created_at: datetime
    updated_at: datetime
    department: DepartmentResponse | None = None

    model_config = ConfigDict(from_attributes=True)

class EmployeeDetailResponse(EmployeeResponse):
    department: DepartmentResponse | None = None
    histories: list[EmployeeHistoryResponse] = []

    model_config = ConfigDict(from_attributes=True)
