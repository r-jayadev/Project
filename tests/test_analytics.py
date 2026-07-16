"""
Tests for Analytics API.
"""

def test_department_summary(client):
    """
    Test department summary endpoint.
    """

    response = client.get("/analytics/summary")

    assert response.status_code == 200

    response_data = response.json()

    assert isinstance(response_data, list)

    if response_data:
        assert "department" in response_data[0]
        assert "employee_count" in response_data[0]
        assert "average_salary" in response_data[0]
        assert "total_salary" in response_data[0]


def test_hiring_trends_monthly(client):
    """
    Test monthly hiring trends.
    """

    response = client.get("/analytics/trends")

    assert response.status_code == 200

    response_data = response.json()

    assert isinstance(response_data, list)

    if response_data:
        assert "period" in response_data[0]
        assert "hires" in response_data[0]


def test_hiring_trends_quarterly(client):
    """
    Test quarterly hiring trends.
    """

    response = client.get("/analytics/trends?frequency=Q")

    assert response.status_code == 200

    response_data = response.json()

    assert isinstance(response_data, list)

    if response_data:
        assert "period" in response_data[0]
        assert "hires" in response_data[0]