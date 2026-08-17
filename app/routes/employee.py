import os
import urllib.parse
import io
from datetime import date
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from app.db import get_db
from app.storage.base import StorageService
from app.routes.deps import get_storage, get_current_user
from app.models.employee import Employee
from app.models.department import Department
from app.models.history import EmployeeHistory
from app.models.user import User
from app.schemas import EmployeeResponse, EmployeeDetailResponse
from app.utils.crypto import encrypt, decrypt, encrypt_bytes, decrypt_bytes, hash_search_key

router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    dependencies=[Depends(get_current_user)]
)
BASE_URL = os.getenv("BASE_URL", "http://localhost").rstrip("/")

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EmployeeResponse
)
async def create_employee(
    employee_code: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    department_id: int | None = Form(None),
    role: str = Form("一般"),
    start_date: date | None = Form(None),
    phone: str | None = Form(None),
    address: str | None = Form(None),
    birth_date: str | None = Form(None),
    photo: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage)
):
    """
    Creates a new employee and optional initial history, uploading profile photo asynchronously.
    Both personal data and photos are encrypted in this process.
    """
    # Unique check for employee_code (stored in plaintext)
    stmt = select(Employee).filter(Employee.employee_code == employee_code)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee code '{employee_code}' already exists."
        )

    # Unique check for email using fast indexed email_hash query
    target_email_hash = hash_search_key(email)
    stmt = select(Employee).filter(Employee.email_hash == target_email_hash)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{email}' is already in use."
        )

    # Department validation
    if department_id is not None:
        dept_stmt = select(Department).filter(Department.id == department_id)
        dept_result = await db.execute(dept_stmt)
        if not dept_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department ID {department_id} does not exist."
            )

    # Image upload and encryption
    photo_filename = None
    if photo:
        if photo.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG and PNG images are supported."
            )
        # Read the image and encrypt the raw bytes
        photo_data = await photo.read()
        encrypted_photo = encrypt_bytes(photo_data)
        
        photo_filename = f"employees/{employee_code}_{photo.filename}"
        
        # Upload the encrypted bytes wrapped in BytesIO
        await storage.upload(io.BytesIO(encrypted_photo), photo_filename)

    # Encrypt text fields
    encrypted_first_name = encrypt(first_name)
    encrypted_last_name = encrypt(last_name)
    encrypted_email = encrypt(email)
    encrypted_phone = encrypt(phone)
    encrypted_address = encrypt(address)
    encrypted_birth_date = encrypt(birth_date)

    # Create employee
    db_employee = Employee(
        employee_code=employee_code,
        first_name=encrypted_first_name,
        last_name=encrypted_last_name,
        email=encrypted_email,
        email_hash=target_email_hash,
        phone=encrypted_phone,
        address=encrypted_address,
        birth_date=encrypted_birth_date,
        department_id=department_id,
        photo_url=photo_filename  # Save raw filename to retrieve and decrypt later
    )
    db.add(db_employee)
    await db.flush()  # Generate db_employee.id

    # Create initial history if department is assigned
    if department_id is not None:
        eff_start_date = start_date or date.today()
        db_history = EmployeeHistory(
            employee_id=db_employee.id,
            department_id=department_id,
            role=role,
            start_date=eff_start_date,
            end_date=None
        )
        db.add(db_history)

    await db.commit()
    
    # Eagerly load department relation and decrypt fields for response
    stmt = select(Employee).options(joinedload(Employee.department)).filter(Employee.id == db_employee.id)
    refreshed_result = await db.execute(stmt)
    db_employee = refreshed_result.scalars().first()
    
    # Decrypt attributes for response serialization
    db_employee.first_name = decrypt(db_employee.first_name)
    db_employee.last_name = decrypt(db_employee.last_name)
    db_employee.email = decrypt(db_employee.email)
    db_employee.phone = decrypt(db_employee.phone)
    db_employee.address = decrypt(db_employee.address)
    db_employee.birth_date = decrypt(db_employee.birth_date)
    if db_employee.photo_url:
        db_employee.photo_url = f"/api/v1/employees/{db_employee.id}/photo"
        
    return db_employee


@router.get(
    "",
    response_model=list[EmployeeResponse]
)
async def list_employees(
    limit: int = 20,
    offset: int = 0,
    department_id: int | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all employees.
    Note: We decrypt all records in memory to perform the query filter (q) and pagination.
    This intentionally introduces noticeable CPU overhead.
    """
    limit = min(limit, 100)
    
    # Retrieve all employees matching the department criteria (no q filter at DB level)
    stmt = select(Employee).options(joinedload(Employee.department))
    if department_id is not None:
        stmt = stmt.filter(Employee.department_id == department_id)
        
    result = await db.execute(stmt)
    all_employees = result.scalars().all()
    
    # Decrypt all retrieved records in memory
    decrypted_list = []
    for emp in all_employees:
        emp.first_name = decrypt(emp.first_name)
        emp.last_name = decrypt(emp.last_name)
        emp.email = decrypt(emp.email)
        emp.phone = decrypt(emp.phone)
        emp.address = decrypt(emp.address)
        emp.birth_date = decrypt(emp.birth_date)
        if emp.photo_url:
            emp.photo_url = f"/api/v1/employees/{emp.id}/photo"
        decrypted_list.append(emp)
        
    # Perform search filter in memory
    if q:
        q_lower = q.lower()
        decrypted_list = [
            emp for emp in decrypted_list
            if q_lower in emp.first_name.lower()
            or q_lower in emp.last_name.lower()
            or q_lower in emp.email.lower()
        ]
        
    # Perform pagination in memory
    paginated_list = decrypted_list[offset:offset+limit]
    return paginated_list


@router.get(
    "/{employee_id}",
    response_model=EmployeeDetailResponse
)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves full details of a specific employee, including department and full career histories, decrypting fields.
    """
    stmt = (
        select(Employee)
        .options(
            joinedload(Employee.department),
            selectinload(Employee.histories)
        )
        .filter(Employee.id == employee_id)
    )
    result = await db.execute(stmt)
    employee = result.scalars().first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
        
    # Decrypt attributes
    employee.first_name = decrypt(employee.first_name)
    employee.last_name = decrypt(employee.last_name)
    employee.email = decrypt(employee.email)
    employee.phone = decrypt(employee.phone)
    employee.address = decrypt(employee.address)
    employee.birth_date = decrypt(employee.birth_date)
    if employee.photo_url:
        employee.photo_url = f"/api/v1/employees/{employee.id}/photo"
        
    return employee


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse
)
async def update_employee(
    employee_id: int,
    first_name: str | None = Form(None),
    last_name: str | None = Form(None),
    email: str | None = Form(None),
    department_id: int | None = Form(None),
    role: str | None = Form(None),
    start_date: date | None = Form(None),
    phone: str | None = Form(None),
    address: str | None = Form(None),
    birth_date: str | None = Form(None),
    photo: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage)
):
    """
    Updates an employee. Encrypts fields and increments history record if department role or assignment changes.
    """
    stmt = (
        select(Employee)
        .options(selectinload(Employee.histories))
        .filter(Employee.id == employee_id)
    )
    result = await db.execute(stmt)
    employee = result.scalars().first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Email uniqueness check using indexed email_hash
    if email:
        new_email_hash = hash_search_key(email)
        if employee.email_hash != new_email_hash:
            stmt = select(Employee).filter(
                Employee.id != employee_id,
                Employee.email_hash == new_email_hash
            )
            result = await db.execute(stmt)
            if result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{email}' is already in use."
                )

    # Department validation
    if department_id is not None:
        dept_stmt = select(Department).filter(Department.id == department_id)
        dept_result = await db.execute(dept_stmt)
        if not dept_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department ID {department_id} does not exist."
            )

    # Update photo and encrypt if provided
    if photo:
        if photo.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG and PNG images are supported."
            )
        
        # Try to delete previous photo
        if employee.photo_url:
            try:
                await storage.delete(employee.photo_url)
            except Exception:
                pass  # Suppress and continue if delete fails
                
        # Read the image and encrypt the raw bytes
        photo_data = await photo.read()
        encrypted_photo = encrypt_bytes(photo_data)
        
        photo_filename = f"employees/{employee.employee_code}_{photo.filename}"
        await storage.upload(io.BytesIO(encrypted_photo), photo_filename)
        employee.photo_url = photo_filename

    # Apply encrypted updates
    if first_name is not None:
        employee.first_name = encrypt(first_name)
    if last_name is not None:
        employee.last_name = encrypt(last_name)
    if email is not None:
        employee.email = encrypt(email)
        employee.email_hash = hash_search_key(email)
    if phone is not None:
        employee.phone = encrypt(phone)
    if address is not None:
        employee.address = encrypt(address)
    if birth_date is not None:
        employee.birth_date = encrypt(birth_date)

    # History record increment logic
    dept_changed = department_id is not None and department_id != employee.department_id
    
    if dept_changed or role or start_date:
        eff_start_date = start_date or date.today()
        eff_role = role or "異動"
        new_dept_id = department_id if department_id is not None else employee.department_id

        if new_dept_id is None:
            employee.department_id = None
        else:
            # Terminate active history
            from datetime import timedelta
            for hist in employee.histories:
                if hist.end_date is None:
                    # Terminate the day before the new start date
                    hist.end_date = eff_start_date - timedelta(days=1)

            # Insert new history
            new_history = EmployeeHistory(
                employee_id=employee.id,
                department_id=new_dept_id,
                role=eff_role,
                start_date=eff_start_date,
                end_date=None
            )
            db.add(new_history)
            employee.department_id = new_dept_id

    await db.commit()
    
    # Eagerly load department relation and decrypt fields for response
    stmt = select(Employee).options(joinedload(Employee.department)).filter(Employee.id == employee.id)
    refreshed_result = await db.execute(stmt)
    employee = refreshed_result.scalars().first()
    
    # Decrypt attributes for response
    employee.first_name = decrypt(employee.first_name)
    employee.last_name = decrypt(employee.last_name)
    employee.email = decrypt(employee.email)
    employee.phone = decrypt(employee.phone)
    employee.address = decrypt(employee.address)
    employee.birth_date = decrypt(employee.birth_date)
    if employee.photo_url:
        employee.photo_url = f"/api/v1/employees/{employee.id}/photo"
        
    return employee


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage)
):
    """
    Deletes an employee from the database and removes their picture from the storage backend.
    """
    stmt = select(Employee).filter(Employee.id == employee_id)
    result = await db.execute(stmt)
    employee = result.scalars().first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Delete photo from storage
    if employee.photo_url:
        try:
            await storage.delete(employee.photo_url)
        except Exception:
            pass

    await db.delete(employee)
    await db.commit()


@router.get(
    "/{employee_id}/photo"
)
async def get_employee_photo(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage)
):
    """
    Retrieves and decrypts the profile photo of a specific employee, serving it as a direct image response.
    """
    stmt = select(Employee.photo_url).filter(Employee.id == employee_id)
    result = await db.execute(stmt)
    photo_filename = result.scalars().first()
    
    # Release DB connection immediately back to pool before starting storage I/O
    await db.close()

    if not photo_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )

    try:
        # Download encrypted file
        encrypted_bytes = await storage.download(photo_filename)
        # Decrypt binary data
        decrypted_bytes = decrypt_bytes(encrypted_bytes)
        
        # Detect mime type from file extension
        mime_type = "image/png"
        if photo_filename.lower().endswith((".jpg", ".jpeg")):
            mime_type = "image/jpeg"
            
        return Response(content=decrypted_bytes, media_type=mime_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve and decrypt photo: {str(e)}"
        )
