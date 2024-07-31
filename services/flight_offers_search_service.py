# services/flight_offers_search_service.py
import requests
from amadeus_auth_service import AmadeusAuthService
from models.flight_offers_models import FlightOffersSearchResponse
import logging
import json


class FlightOffersSearchService:
    def __init__(self):
        self.access_token = "Bearer " + AmadeusAuthService().get_access_token()
        self.base_url = 'https://test.api.amadeus.com/v2/shopping/flight-offers'
        # Configuração do logger
        logging.basicConfig(filename='flight_offers.log', level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()

    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1, max_price=None, non_stop=None, one_way=False, duration=None, view_by=None):
        """
        Faz uma chamada à API de busca de ofertas de voo.

        :param origin: Código IATA do aeroporto de origem (ex: 'JFK')
        :param destination: Código IATA do aeroporto de destino (ex: 'LAX')
        :param departure_date: Data de partida no formato YYYY-MM-DD
        :param return_date: (Opcional) Data de retorno no formato YYYY-MM-DD
        :param adults: Número de adultos
        :param max_price: (Opcional) Preço máximo para os voos
        :param non_stop: (Opcional) Filtra por voos diretos ('true' para apenas diretos, 'false' para incluir com escalas)
        :param one_way: (Opcional) Define se a busca é apenas para ida
        :param duration: (Opcional) Duração da viagem em dias (para ida e volta)
        :param view_by: (Opcional) Define a visualização dos resultados (COUNTRY, DATE, DESTINATION, DURATION, WEEK)
        :return: Dados da resposta em formato JSON
        """
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date,
            'adults': adults,
            'oneWay': str(one_way).lower()  # Converte para 'true' ou 'false'
        }
        if return_date:
            params['returnDate'] = return_date
        if max_price:
            params['maxPrice'] = max_price
        if non_stop is not None:
            params['nonStop'] = 'true' if non_stop else 'false'
        if duration:
            params['duration'] = duration
        if view_by:
            params['viewBy'] = view_by

        headers = {
            'Authorization': self.access_token
        }

        response = requests.get(self.base_url, headers=headers, params=params)

        if response.status_code == 200:
            response_data = response.json()
            self.logger.info(f"Request successful: {response_data}")
            try:
                flight_offers = FlightOffersSearchResponse(**response_data)
                return flight_offers
            except Exception as e:
                self.logger.error(f"Validation error: {str(e)}")
                raise Exception(f"Validation error: {str(e)}")
        else:
            error_message = f"Erro: {response.status_code}, {response.text}"
            self.logger.error(error_message)
            raise Exception(error_message)

if __name__ == "__main__":
    flight_service = FlightOffersSearchService()
    try:
        # Exemplo de busca de voos
        origin = 'JFK'  # Aeroporto de origem
        destination = 'GRU'  # Aeroporto de destino
        departure_date = '2024-08-15'  # Data de partida
        return_date = '2024-08-20'  # (Opcional) Data de retorno

        # Chamando o método de busca
        flight_offers = flight_service.search_flights(origin, destination, departure_date, return_date, adults=1)
        
        for offer in flight_offers.data:
            print(f"Preço: {offer.price.total} {offer.price.currency}")
            print("Itinerários:")
            for idx, itinerary in enumerate(offer.itineraries):
                tipo_voo = "Voo de Ida" if idx == 0 else "Voo de Volta"
                print(f" {tipo_voo}:")
                for seg_idx, segment in enumerate(itinerary.segments):
                    escala = "sem escala" if len(itinerary.segments) == 1 else "com escala"
                    print(f"  Segmento {seg_idx + 1}:")
                    print(f"   Origem: {segment.departure.iataCode}")
                    print(f"   Destino: {segment.arrival.iataCode}")
                    print(f"   Partida: {segment.departure.at}")
                    print(f"   Chegada: {segment.arrival.at}")
                    print(f"   Escala: {escala}")
                    print("   -----")
                # Informações de bagagem
                for fare_detail in offer.travelerPricings[0].fareDetailsBySegment:
                    if fare_detail.segmentId == segment.id:
                        if fare_detail.includedCheckedBags:
                            included_bags = fare_detail.includedCheckedBags.quantity
                        else:
                            included_bags = 0
                        print(f"   Bagagem incluída: {included_bags} peças")
            print("-----")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")