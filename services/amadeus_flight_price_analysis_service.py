import requests
from services.amadeus_auth_service import AmadeusAuthService
from models.flight_offers_models import FlightOffersSearchResponse
import logging
import json

"""
Self-Service APIs / Flights / Flight Price Analysis
link: https://developers.amadeus.com/self-service/category/flights/api-doc/flight-price-analysis

Esses valores representam uma análise da distribuição de preços para um determinado itinerário de voo, usando quartis. 
Aqui está o que cada um desses termos significa:

MINIMUM: 43.05 EUR
Significado: Este é o menor preço encontrado para o itinerário de voo. 
Basicamente, 43.05 EUR é o preço mais baixo disponível entre todos os preços coletados para essa rota específica na data especificada.

FIRST (Q1): 220.10 EUR
Significado: Este é o preço correspondente ao primeiro quartil (Q1), também chamado de quartil inferior. 
25% dos preços estão abaixo de 220.10 EUR, e 75% estão acima desse valor. Isso dá uma ideia de onde começa a faixa de preços após os valores mínimos.

MEDIUM (Q2): 274.33 EUR
Significado: Este é o preço mediano ou segundo quartil (Q2). 50% dos preços estão abaixo de 274.33 EUR, e 50% estão acima. 
É o valor central da distribuição de preços, representando o "preço típico" ou "preço médio" que você pode esperar.

THIRD (Q3): 324.89 EUR
Significado: Este é o preço correspondente ao terceiro quartil (Q3), ou quartil superior. 
75% dos preços estão abaixo de 324.89 EUR, e apenas 25% estão acima desse valor. Isso ajuda a entender o limite superior da faixa de preços mais comum.

MAXIMUM: 427.54 EUR
Significado: Este é o preço máximo encontrado para o itinerário de voo. 
427.54 EUR é o preço mais alto entre todos os preços coletados para essa rota específica na data especificada.
"""

class AmadeusFlightPriceAnalysisService:
    def __init__(self):
        self.access_token = "Bearer " + AmadeusAuthService().get_access_token()
        self.base_url = 'https://test.api.amadeus.com/v1/analytics/itinerary-price-metrics'
        # Configuração do logger
        logging.basicConfig(filename='flight_price_analysis.log', level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()

    def get_price_metrics(self, origin, destination, departure_date, currency_code="EUR", one_way=False):
        """
        Faz uma chamada à API de análise de preços de voos.

        :param origin: Código IATA do aeroporto de origem (ex: 'JFK')
        :param destination: Código IATA do aeroporto de destino (ex: 'LAX')
        :param departure_date: Data de partida no formato YYYY-MM-DD
        :param currency_code: (Opcional) Código da moeda preferida
        :param one_way: (Opcional) True para viagem só de ida, False para ida e volta
        :return: Dados da resposta em formato JSON
        """
        params = {
            'originIataCode': origin,
            'destinationIataCode': destination,
            'departureDate': departure_date,
            'currencyCode': currency_code,
            'oneWay': str(one_way).lower()
        }

        headers = {
            'Authorization': self.access_token
        }
        
        print(params)

        response = requests.get(self.base_url, headers=headers, params=params)
        

        if response.status_code == 200:
            response_data = response.json()
            self.logger.info(f"Request successful: {response_data}")
            try:
                # Log do JSON formatado
                formatted_response = json.dumps(response_data, indent=4)
                self.logger.info("-----------------------------------------")
                self.logger.info(f"Price metrics data: {formatted_response}")
                return response_data
            except Exception as e:
                self.logger.error(f"Error processing response: {str(e)}")
                raise Exception(f"Error processing response: {str(e)}")
        else:
            error_message = f"Erro: {response.status_code}, {response.text}"
            self.logger.error(error_message)
            raise Exception(error_message)

# Usage example:
if __name__ == "__main__":
    price_analysis_service = AmadeusFlightPriceAnalysisService()
    try:
        # Exemplo de análise de preços de voos
        origin = 'MAD'  # Aeroporto de origem
        destination = 'CDG'  # Aeroporto de destino
        departure_date = '2024-09-15'  # Data de partida
        currency_code = 'EUR'  # Moeda preferida
        one_way = False  # Viagem de ida e volta

        # Chamando o método de análise de preços
        price_metrics = price_analysis_service.get_price_metrics(
            origin, destination, departure_date, currency_code, one_way
        )
        
        print(f"Análise de preços para o voo de {origin} para {destination} em {departure_date}:")
        for metric in price_metrics['data'][0]['priceMetrics']:
            print(f"{metric['quartileRanking']}: {metric['amount']} {currency_code}")
        
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
