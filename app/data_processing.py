"""
Data Processing Module

Contains all panda function:
    1) Validating CSV files
    2) Cleaning the file
    3) Computing Department Analytics
    4) Computing Hire Trends
"""
import pandas as pd

REQUIRED_COLUMNS=["id","name","email","phone","department","salary","status","hire_date","city"]

def validate_columns(df: pd.DataFrame) -> None:
    """
    Check whether the uploaded CSV file contains all required columns

    Raises:
        ValueError: if any column is missing
    """
    missing=[]
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing.append(col)
    
    if missing:
        raise ValueError(
            f"Missing Column: {missing}"
        )
    
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the uploaded csv file

    Operations to be performed:
        1. Handle Missing values
        2. Remove Duplicate Rows
        3. Convert Datatypes
    """
    #Copy original df into another variable
    cleaned_df = df.copy()

    #Drop Duplicates
    cleaned_df.drop_duplicates(inplace=True)

    #Drop missing rows
    cleaned_df.dropna(inplace=True)

    #Convert Salary to numeric datatype
    cleaned_df["salary"]=pd.to_numeric(cleaned_df["salary"],errors="coerce")

    #Convert hire date to date time datatype
    cleaned_df["hire_date"]=pd.to_datetime(cleaned_df["hire_date"],errors="coerce")

    cleaned_df.dropna(inplace=True)

    return cleaned_df

def calculate_department_summary(df: pd.DataFrame) -> list[dict]:
    """
    Calculate Department wise analytics

    Returns:
        1. Department
        2. Employee Count
        3. Average Salary
        4. Total Salary
    """
    summary_df=(df.groupby('department').agg(
        employee_count=("id","count"),
        average_salary=("salary","mean"),
        total_salary=("salary","sum")).reset_index())
    
    return summary_df.to_dict(orient="records")

def calculate_hiring_trends(df: pd.DataFrame, frequency: str = "ME") -> list[dict]:
    """
    Calculate Hiring trends

    1. ME -> Monthly
    2. QE-> Quaterly
    """

    trend_df=df.copy()

    trend_df["hire_date"]=pd.to_datetime(trend_df["hire_date"])

    trend_df.set_index("hire_date", inplace=True)

    trend_df=(trend_df.resample(frequency).size().reset_index(name="hires"))

    trend_df["period"]=trend_df["hire_date"].astype(str)

    trend_df=trend_df[["period","hires"]]

    return trend_df.to_dict(orient="records")
