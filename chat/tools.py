#chat/tools.py

from langchain_core.tools import tool
from services.amadeus_flight_offers_search_service import AmadeusFlightOffersSearchService

@tool
def search_amadeus_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    travel_class: str = None,
    max_price: float = None,
    non_stop: bool = None,
    included_airline_codes: list = None,
    excluded_airline_codes: list = None,
    currency_code: str = None,
    max_results: int = 250
) -> dict:
    """
    Realiza uma busca detalhada por passagens aéreas utilizando a API Amadeus, ideal para consultas com datas e destinos específicos, quando o usuário já tem uma ideia clara do que deseja. Permite encontrar e comparar opções de voos com base em critérios personalizados.

    Parâmetros:
    - origin (str): Código IATA do aeroporto de origem (ex: 'JFK').
    - destination (str): Código IATA do aeroporto de destino (ex: 'LAX').
    - departure_date (str): Data de partida no formato 'YYYY-MM-DD'.
    - return_date (str, opcional): Data de retorno no formato 'YYYY-MM-DD'.
    - adults (int, opcional): Número de adultos (padrão: 1).
    - max_price (int, opcional): Preço máximo para os voos.
    - non_stop (bool, opcional): 'True' para apenas voos diretos, 'False' para incluir escalas (padrão: False).
    - currency_code (str, opcional): Código da moeda preferida (ex: 'USD').
    - max_results (int, opcional): Número máximo de resultados a retornar (padrão: 5).
    """
    print("Executando a ferramenta 'search_amadeus_flights")
    service = AmadeusFlightOffersSearchService()
    return service.search_flights(
        origin, destination, departure_date, return_date, adults, 
        children, infants, travel_class, max_price, non_stop, 
        included_airline_codes, excluded_airline_codes, currency_code, 
        max_results
    )

@tool
def tourism_info_tool(
    local: str,
) -> dict:
    """
    Busca locais sobre turismo 
    """
    print("Executando a ferramenta 'search_amadeus_flights")

    return "Parábens"