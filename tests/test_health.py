"""
Tests for Health Check API.
"""

def test_health_check(client):
    """
    Test the health check endpoint.
    """
    
    response = client.get("/health")

    assert response.status_code == 200

    response_data = response.json()

    assert "database" in response_data
    assert "redis" in response_data
    assert "status" in response_data

    assert response_data["database"] in [
        "Connected",
        "Disconnected"
    ]

    assert response_data["redis"] in [
        "Connected",
        "Disconnected"
    ]

    assert response_data["status"] in [
        "Healthy",
        "Unhealthy"
    ]