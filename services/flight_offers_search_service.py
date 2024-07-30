# services/flight_offers_search_service.py
import requests
from amadeus_auth_service import AmadeusAuthService
from models.flight_offers_models import FlightOffersResponse
import logging


class FlightOffersSearchService:
    def __init__(self):
        self.access_token = "Bearer " + AmadeusAuthService().get_access_token()
        self.base_url = 'https://test.api.amadeus.com/v2/shopping/flight-offers'
        # Configuração do logger
        logging.basicConfig(filename='flight_offers.log', level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()

    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1, max_price=None):
        """
        Faz uma chamada à API de busca de ofertas de voo.

        :param origin: Código IATA do aeroporto de origem (ex: 'JFK')
        :param destination: Código IATA do aeroporto de destino (ex: 'LAX')
        :param departure_date: Data de partida no formato YYYY-MM-DD
        :param return_date: (Opcional) Data de retorno no formato YYYY-MM-DD
        :param adults: Número de adultos
        :param max_price: (Opcional) Preço máximo para os voos
        :return: Dados da resposta em formato JSON
        """
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date,
            'adults': adults
        }
        if return_date:
            params['returnDate'] = return_date
        if max_price:
            params['maxPrice'] = max_price

        headers = {
            'Authorization': self.access_token
        }

        response = requests.get(self.base_url, headers=headers, params=params)

        if response.status_code == 200:
            response_data = response.json()
            self.logger.info(f"Request successful: {response_data}")
            # Usando Pydantic para validar e acessar os dados
            flight_offers = FlightOffersResponse(**response_data)
            # Convertendo o modelo Pydantic para dicionário
            flight_offers_dict = flight_offers.dict()

            # Convertendo o dicionário para JSON formatado
            flight_offers_json = json.dumps(flight_offers_dict, indent=4)

            # Registrando a saída JSON
            self.logger.info(f"-----------------------------------------")
            self.logger.info(f"Flight offers data: {flight_offers_json}")
            return flight_offers
        else:
            error_message = f"Erro: {response.status_code}, {response.text}"
            self.logger.error(error_message)
            raise Exception(error_message)

if __name__ == "__main__":
    flight_service = FlightOffersSearchService()
    try:
        # Exemplo de busca de voos
        origin = 'JFK'  # Aeroporto de origem
        destination = 'LAX'  # Aeroporto de destino
        departure_date = '2024-08-15'  # Data de partida
        return_date = '2024-08-20'  # (Opcional) Data de retorno

        # Chamando o método de busca
        flight_offers = flight_service.search_flights(origin, destination, departure_date, return_date, adults=1)
        
        print(flight_offers)
        # Exibindo os resultados
        for offer in flight_offers['data']:
            print(f"Preço: {offer['price']['total']} {offer['price']['currency']}")
            print(f"Origem: {offer['origin']['iataCode']}")
            print(f"Destino: {offer['destination']['iataCode']}")
            print(f"Partida: {offer['departureDate']}")
            print(f"Retorno: {offer.get('returnDate', 'N/A')}")
            print("-----")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    