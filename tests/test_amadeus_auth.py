# tests/test_amadeus_auth.py
import pytest
from services.amadeus_auth import AmadeusAuthService

@pytest.fixture
def auth_service():
    return AmadeusAuthService()

def test_get_access_token(auth_service):
    token = auth_service.get_access_token()
    assert token is not None
    assert isinstance(token, str)

def test_is_token_expired(auth_service):
    # Se o token é None, consideramos como expirado
    assert auth_service._is_token_expired() is True

def test_get_full_response(auth_service):
    response = auth_service.get_full_response()
    assert response is not None
    assert isinstance(response, dict)
    assert "access_token" in response
    assert "expires_in" in response
