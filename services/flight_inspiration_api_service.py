# flight_inspiration_api_service.py
import requests
from amadeus_auth_service import AmadeusAuthService
import pprint

class FlightInspirationApiService:
    def __init__(self):
        self.access_token = "Bearer " + AmadeusAuthService().get_access_token()
        self.base_url = 'https://test.api.amadeus.com/v1/shopping/flight-destinations'

    def get_flight_destinations(self, origin, max_price):
        """
        Faz uma chamada à API de inspiração de voos para obter destinos a partir de uma origem específica
        e dentro de um limite de preço máximo.

        :param origin: Código IATA do aeroporto de origem (ex: 'PAR')
        :param max_price: Preço máximo para os voos (ex: '200')
        :return: Dados da resposta em formato JSON
        """
        # Defina os parâmetros da consulta
        params = {
            'origin': origin,
            'maxPrice': max_price
        }

        # Defina os cabeçalhos da requisição
        headers = {
            'Authorization': self.access_token
        }

        # Fazendo a requisição GET
        response = requests.get(self.base_url, headers=headers, params=params)

        # Verificando o status da resposta
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro: {response.status_code}, {response.text}")

# Exemplo de uso do serviço
if __name__ == "__main__":
    flight_service = FlightInspirationApiService()
    try:
        data = flight_service.get_flight_destinations('PAR', '200')
        pprint.pprint(data)
        headers = {
            'Authorization': flight_service.access_token
        }
        link = "https://test.api.amadeus.com/v2/shopping/flight-offers?originLocationCode=PAR&destinationLocationCode=SAW&departureDate=2024-09-20&returnDate=2024-10-05&adults=1&nonStop=false&maxPrice=200&currency=EUR"
        response = requests.get(link, headers=headers)
        print(response.json())
    except Exception as e:
        print(e)
