import os
from app.core.config import Settings

def test_config_loading():
    # Test that default values are set
    settings = Settings()
    assert settings.API_V1_PREFIX == "/api/v1"
    
    # Test overriding via environment variable
    os.environ["API_V1_PREFIX"] = "/api/v2"
    settings_override = Settings()
    assert settings_override.API_V1_PREFIX == "/api/v2"
    
    # Cleanup
    del os.environ["API_V1_PREFIX"]
