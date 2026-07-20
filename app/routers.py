"""
API Routes Module

Contains all FastAPI endpoints for:

1. Uploading employee CSV files
2. Retrieving employee records
3. Analytics
4. Health Check
"""

import pandas as pd

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import Employee
from app.schemas import EmployeeResponse, PaginatedEmployees, DepartmentSummary, HiringTrend, HealthResponse

from app.data_processing import validate_columns, clean_data, calculate_department_summary, calculate_hiring_trends


from app.redis_client import get_cache,set_cache,delete_cache,check_redis_connection

from app.config import settings


router = APIRouter()


@router.post("/data/upload", status_code=status.HTTP_201_CREATED)
def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload employee CSV file.

    Steps:
    1. Read CSV
    2. Validate columns
    3. Clean data
    4. Store in PostgreSQL
    5. Clear analytics cache
    """

    try:

        if not file.filename.endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail="Only CSV files are allowed."
            )

        try:
            employee_df = pd.read_csv(file.file)

        except Exception as error:
            raise HTTPException(
                status_code=400,
                detail=f"Unable to read CSV file. {error}"
            )

        validate_columns(employee_df)

        cleaned_df = clean_data(employee_df)

        employee_objects = []
        existing_emps={emp.id for emp in db.query(Employee.id).all()}

        for _, row in cleaned_df.iterrows():
            if row["id"] in existing_emps:
                continue

            employee = Employee(
                id=int(row["id"]),
                name=row["name"],
                email=row["email"],
                phone=row["phone"],
                department=row["department"],
                salary=float(row["salary"]),
                status=row["status"],
                hire_date=row["hire_date"],
                city=row["city"]
            )

            employee_objects.append(employee)

        try:
            db.add_all(employee_objects)
            db.commit()

        except Exception as error:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database Error: {error}"
            )

        delete_cache("department_summary")
        delete_cache("hiring_trends_M")
        delete_cache("hiring_trends_Q")

        return {
            "message": "CSV uploaded successfully.",
            "rows_inserted": len(employee_objects)
        }

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

@router.get("/data", response_model=PaginatedEmployees)
def get_all_employees(page: int = 1, per_page: int = 10, department: str | None = None,status_filter: str | None = None,db: Session = Depends(get_db)):
    """
    Return paginated employee records.

    Optional Filters:
    1. department
    2. status
    """

    try:

        query = db.query(Employee)

        if department:
            query = query.filter(
                Employee.department == department
            )

        if status_filter:
            query = query.filter(
                Employee.status == status_filter
            )

        total_records = query.count()

        employees = (query.offset((page - 1) * per_page).limit(per_page).all())

        return PaginatedEmployees(
            page=page,
            per_page=per_page,
            total_records=total_records,
            employees=employees
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )


@router.get("/data/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """
    Return one employee by ID.
    """

    try:

        employee = (
            db.query(Employee)
            .filter(Employee.id == employee_id)
            .first()
        )

        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found."
            )

        return employee

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

@router.get("/analytics/summary", response_model=list[DepartmentSummary])
def department_summary(db: Session = Depends(get_db)):
    """
    Return department-wise analytics.
    """

    try:

        cache_key = "department_summary"

        cached_summary = get_cache(cache_key)

        if cached_summary:
            return cached_summary

        employees = db.query(Employee).all()

        if not employees:
            return []

        employee_data = []

        for employee in employees:
            employee_data.append(
                {
                    "id": employee.id,
                    "name": employee.name,
                    "email": employee.email,
                    "phone": employee.phone,
                    "department": employee.department,
                    "salary": employee.salary,
                    "status": employee.status,
                    "hire_date": employee.hire_date,
                    "city": employee.city
                }
            )

        employee_df = pd.DataFrame(employee_data)

        summary = calculate_department_summary(employee_df)

        set_cache(cache_key, summary)

        return summary

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )


@router.get("/analytics/trends", response_model=list[HiringTrend])
def hiring_trends(frequency: str = "ME", db: Session = Depends(get_db)):
    """
    Return hiring trends.

    Frequency:
    ME -> Monthly
    QE -> Quarterly
    """

    try:

        cache_key = f"hiring_trends_{frequency}"

        cached_trends = get_cache(cache_key)

        if cached_trends:
            return cached_trends

        employees = db.query(Employee).all()

        if not employees:
            return []

        employee_data = []

        for employee in employees:
            employee_data.append(
                {
                    "id": employee.id,
                    "name": employee.name,
                    "email": employee.email,
                    "phone": employee.phone,
                    "department": employee.department,
                    "salary": employee.salary,
                    "status": employee.status,
                    "hire_date": employee.hire_date,
                    "city": employee.city
                }
            )

        employee_df = pd.DataFrame(employee_data)

        trends = calculate_hiring_trends(
            employee_df,
            frequency
        )

        set_cache(cache_key, trends)

        return trends

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )
@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Check PostgreSQL and Redis connectivity.
    """

    try:

        database_status = "Connected"

        try:
            db.execute(text("SELECT 1"))

        except Exception:
            database_status = "Disconnected"

        redis_status = (
            "Connected"
            if check_redis_connection()
            else "Disconnected"
        )

        overall_status = (
            "Healthy"
            if database_status == "Connected"
            and redis_status == "Connected"
            else "Unhealthy"
        )

        return HealthResponse(
            database=database_status,
            redis=redis_status,
            status=overall_status
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )