from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.department import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.history import EmployeeHistory

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(512), nullable=False)
    last_name: Mapped[str] = mapped_column(String(512), nullable=False)
    email: Mapped[str] = mapped_column(String(512), nullable=False)
    email_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(512), nullable=True)
    address: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    birth_date: Mapped[str | None] = mapped_column(String(512), nullable=True)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    department: Mapped["Department"] = relationship(back_populates="employees")
    histories: Mapped[List["EmployeeHistory"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
