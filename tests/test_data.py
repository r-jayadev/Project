"""
Tests for Employee Data API.
"""

def test_get_all_employees(client):
    """
    Test retrieving all employees.
    """

    response = client.get("/data")

    assert response.status_code == 200

    response_data = response.json()

    assert "page" in response_data
    assert "per_page" in response_data
    assert "total_record" in response_data
    assert "employees" in response_data


def test_get_employee_by_id(client):
    """
    Test retrieving a single employee.
    """

    response = client.get("/data/1")

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["id"] == 1
    assert "name" in response_data
    assert "email" in response_data
    assert "department" in response_data


def test_get_invalid_employee(client):
    """
    Test retrieving a non-existing employee.
    """

    response = client.get("/data/999999")

    assert response.status_code == 404

    response_data = response.json()

    assert response_data["detail"] == "Employee not found."


def test_employee_pagination(client):
    """
    Test employee pagination.
    """

    response = client.get("/data?page=1&per_page=2")

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["page"] == 1
    assert response_data["per_page"] == 2
    assert isinstance(response_data["employees"], list)