from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas import DepartmentCreate, DepartmentResponse
from app.routes.deps import get_current_user

router = APIRouter(
    prefix="/departments",
    tags=["departments"],
    dependencies=[Depends(get_current_user)]
)

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DepartmentResponse
)
async def create_department(
    schema: DepartmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new department.
    """
    # Check duplicate code -> UPSERT behavior
    stmt = select(Department).filter(Department.code == schema.code)
    result = await db.execute(stmt)
    db_dept = result.scalars().first()
    if db_dept:
        db_dept.name = schema.name
        await db.commit()
        await db.refresh(db_dept)
        return db_dept
    
    db_dept = Department(
        code=schema.code,
        name=schema.name
    )
    db.add(db_dept)
    await db.commit()
    await db.refresh(db_dept)
    return db_dept

@router.get(
    "",
    response_model=list[DepartmentResponse]
)
async def list_departments(
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all departments.
    """
    stmt = select(Department).order_by(Department.code)
    result = await db.execute(stmt)
    return result.scalars().all()
