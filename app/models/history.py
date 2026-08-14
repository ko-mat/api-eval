from datetime import date, datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Date, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.department import Base

if TYPE_CHECKING:
    from app.models.employee import Employee

class EmployeeHistory(Base):
    __tablename__ = "employee_histories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    employee: Mapped["Employee"] = relationship(back_populates="histories")

    # Table arguments for indexes
    __table_args__ = (
        Index("idx_histories_dates", "employee_id", "start_date"),
    )
