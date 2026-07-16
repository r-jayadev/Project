"""
Database models for the application

Contains all tables in the Postgres DB
"""
from app.database import Base
from sqlalchemy import Column, Integer, String, Float, Date, DateTime

class Employee(Base):
    """
    Employee Database Model

    Stores employee information into tables from uploaded csv files
    """
    __tablename__ = "employees"

    #id,name,email,phone,department,salary,status,hire_date,city
    #Unique Employee ID
    id = Column(Integer, primary_key=True, index=True)

    #Employee Name
    name = Column(String(100), nullable=False)

    #Employee Email
    email = Column(String(150), unique=True, nullable=False)

    #Employee Phone Number
    phone = Column(String(20), unique=True, nullable=False)

    #Employee Department Name
    department = Column(String(50), nullable=False)

    #Employee Salary
    salary = Column(Float, nullable=False)

    #Employee Status - Active/Inactive
    status = Column(String(50), nullable=False)

    #Employee hire date
    hire_date = Column(Date, nullable=False)

    #City
    city = Column(String(100), nullable=False)