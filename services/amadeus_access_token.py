# services/amadeus_auth.py
import requests
import os
from datetime import datetime, timedelta

class AmadeusAuthService:
    def __init__(self):
        self.client_id = os.getenv('AMADEUS_API_KEY')
        self.client_secret = os.getenv('AMADEUS_API_SECRET')
        self.token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        self.token_data = None
        self.token_expiry = None
        
    def get_full_response(self):
        if self.token_data is None or self._is_token_expired():
            self._fetch_token()
        return self.token_data

    def get_access_token(self):
        if self.token_data is None or self._is_token_expired():
            self._fetch_token()
        return self.token_data.get("access_token")

    def _fetch_token(self):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(self.token_url, headers=headers, data=data)
        response.raise_for_status()
        self.token_data = response.json()
        self.token_expiry = datetime.now() + timedelta(seconds=self.token_data.get("expires_in", 0))

    def _is_token_expired(self):
        if self.token_expiry is None:
            return True
        return datetime.now() >= self.token_expiry

    
