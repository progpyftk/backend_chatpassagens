# services/amadeus_auth.py
import requests
import os
from datetime import datetime, timedelta

class AmadeusAuthService:
    """
    Serviço para gerenciar a autenticação com a API da Amadeus.
    Responsável por obter e armazenar tokens de acesso, verificando sua validade.

    Estrutura da resposta do token:
    {
        'access_token': 'str',
        'application_name': 'str',
        'client_id': 'str',
        'expires_in': int,
        'scope': 'str',
        'state': 'str',
        'token_type': 'str',
        'type': 'str',
        'username': 'str'
    }
    """

    def __init__(self):
        """Inicializa o serviço com as credenciais da API e configura o estado inicial."""
        self.client_id = os.getenv('AMADEUS_API_KEY')
        self.client_secret = os.getenv('AMADEUS_API_SECRET')
        self.token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        self.token_data = None
        self.token_expiry = None

    def get_full_response(self):
        """
        Retorna a resposta completa contendo o token e informações associadas.
        
        Retorna:
            dict: Dados completos da resposta do token.
        """
        if self.token_data is None or self._is_token_expired():
            self._fetch_token()
        return self.token_data

    def get_access_token(self):
        """
        Obtém o token de acesso atual. Se o token estiver ausente ou expirado, obtém um novo.

        Retorna:
            str: Token de acesso.
        """
        if self.token_data is None or self._is_token_expired():
            self._fetch_token()
        return self.token_data.get("access_token")

    def _fetch_token(self):
        """
        Faz uma solicitação para obter um novo token de acesso.
        Atualiza `token_data` com a resposta e define o tempo de expiração do token.
        """
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
        """
        Verifica se o token atual está expirado.

        Retorna:
            bool: True se o token estiver expirado ou ausente, False caso contrário.
        """
        if self.token_expiry is None:
            return True
        return datetime.now() >= self.token_expiry
