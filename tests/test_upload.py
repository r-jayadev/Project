
"""
Tests for CSV upload API
"""
import io

def test_upload_valid_csv(client):
    """
    Test uploading a valid employee csv
    """
    csv_data = (
        "id,name,email,phone,department,salary,status,hire_date,city\n"
        "1,John,john@test.com,9876543210,IT,65000,Active,2024-01-01,Kochi\n"
        "2,Alice,alice@test.com,9876543211,HR,55000,Active,2024-02-01,Bangalore\n"
    )

    response=client.post("/data/upload",files={"file":("employee.csv",io.BytesIO(csv_data.encode("utf-8")),"text/csv")})

    assert response.status_code == 201

    response_data=response.json()

    assert response_data["message"] == "CSV uploaded successfully."
    assert response_data["rows_inserted"] == 2

def test_upload_invalid_file(client):
    """
    Test uploading a non csv file
    """
    response=client.post("/data/upload",files={"file":("employee.txt",io.BytesIO(b"this is a text file."),"text/plain")})

    
    assert response.status_code == 400

    response_data=response.json()

    assert response_data["detail"] == "Only CSV files are allowed"

def test_upload_missingcolumns(client):
    """
    Test uploading a csv file without required columns
    """
    csv_data = (
        "id,name,email\n"
        "1,John,john@test.com\n"
    )

    response=client.post("/data/upload",files={"file":("employee.csv",io.BytesIO(csv_data.encode("utf-8")),"text/csv")})

    assert response.status_code == 500

    response_data=response.json()

    assert "Missing" in response_data["detail"]