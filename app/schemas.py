"""
All request and response models used by FastAPI
"""
from datetime import date
from pydantic import EmailStr, BaseModel, ConfigDict, Field

class EmployeeResponse(BaseModel):
    """
    Base Schema containing Employee Fields
    """
    id: int

    name: str = Field(min_length=3, max_length=100, description="Employee Name")

    email: EmailStr

    phone: str = Field(min_length=10, max_length=15, description="Phone Number")

    department: str = Field(min_length=2, max_length=100, description="Employee Department")

    salary: float = Field(gt=0, description="Employee Salary")

    status: str

    hire_date: date

    city: str = Field(min_length=2, max_length=100, description="Employee City")

    model_config = ConfigDict(from_attributes=True)

class DepartmentSummary(BaseModel):
    """
    Response shcema for Dept Summary analytics
    """
    department: str
    employee_count: int
    average_salary: float
    total_salary: float

class PaginatedEmployees(BaseModel):
    """
    Response Schema for paginated employees
    """
    page: int
    per_page: int
    total_records: int

    employees: list[EmployeeResponse]

class HiringTrend(BaseModel):
    """
    Response schema for Hiring Trends analytics
    """
    period: str
    hires: int

class HealthResponse(BaseModel):
    """
    Response schema for health check endpoint
    """
    database: str
    redis: str
    status: str