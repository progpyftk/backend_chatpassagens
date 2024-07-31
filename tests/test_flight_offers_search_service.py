# test_flight_offers_search_service.py
from datetime import datetime, timedelta
import pytest
from services.amadeus_flight_offers_search_service import AmadeusFlightOffersSearchService

@pytest.fixture
def flight_service():
    return AmadeusFlightOffersSearchService()

def test_search_flights_real(flight_service):
    # Configurando as datas para 10 dias a partir de hoje e retorno em 5 dias após a partida
    today = datetime.today()
    departure_date = (today + timedelta(days=10)).strftime('%Y-%m-%d')
    return_date = (today + timedelta(days=15)).strftime('%Y-%m-%d')
    
    # Parâmetros de teste
    origin = 'JFK'  # Aeroporto de Nova Iorque
    destination = 'BOS'  # Aeroporto de Boston
    adults = 1  # Número de adultos
    children = 0  # Número de crianças
    infants = 0  # Número de bebês
    travel_class = 'ECONOMY'  # Classe de viagem
    max_price = 1500  # Preço máximo
    non_stop = False  # Permitir voos com escala
    included_airline_codes = None  # Não especificar companhias aéreas
    excluded_airline_codes = None  # Não excluir companhias aéreas
    currency_code = 'USD'  # Moeda
    max_results = 5  # Número máximo de resultados

    # Chamando o método de busca real
    try:
        flight_offers = flight_service.search_flights(
            origin,
            destination,
            departure_date,
            return_date,
            adults,
            children,
            infants,
            travel_class,
            max_price,
            non_stop,
            included_airline_codes,
            excluded_airline_codes,
            currency_code,
            max_results
        )
        
        # Verificações básicas
        assert flight_offers is not None, "A resposta da API não deve ser None"
        assert len(flight_offers.data) > 0, "A resposta deve conter ao menos uma oferta de voo"

        for offer in flight_offers.data:
            assert offer.price.total is not None, "O preço total deve estar presente"
            assert offer.price.currency == 'USD', "A moeda deve ser USD"
            assert offer.itineraries is not None and len(offer.itineraries) > 0, "Deve haver pelo menos um itinerário"
            assert offer.travelerPricings is not None, "Deve haver informações de preços para viajantes"
    except Exception as e:
        pytest.fail(f"Erro durante a chamada real à API: {e}")
