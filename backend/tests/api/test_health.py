from app.core.config import settings

def test_health_endpoint(client):
    response = client.get(f"{settings.API_V1_PREFIX}/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")
    assert "database" in data
    
def test_app_startup(client):
    # The client fixture uses TestClient as a context manager, 
    # which triggers FastAPI lifespan events (startup/shutdown).
    # If the app starts without errors, this test implicitly passes.
    assert True
