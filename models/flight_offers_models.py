# models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Aircraft(BaseModel):
    code: str

class Segment(BaseModel):
    departure: Dict[str, str]
    arrival: Dict[str, str]
    carrierCode: str
    number: str
    aircraft: Aircraft
    operating: Dict[str, str]
    duration: str
    id: str
    numberOfStops: int
    blacklistedInEU: bool

class Itinerary(BaseModel):
    duration: str
    segments: List[Segment]

class Fee(BaseModel):
    amount: str
    type: str

class Price(BaseModel):
    currency: str
    total: str
    base: str
    fees: List[Fee]
    grandTotal: str

class FlightOffer(BaseModel):
    type: str
    id: str
    source: str
    instantTicketingRequired: bool
    nonHomogeneous: bool
    oneWay: bool
    isUpsellOffer: bool
    lastTicketingDate: str
    numberOfBookableSeats: int
    itineraries: List[Itinerary]
    price: Price
    validatingAirlineCodes: List[str]
    travelerPricings: List[Dict[str, str]]

class Meta(BaseModel):
    count: int
    links: Dict[str, str]

class FlightOffersResponse(BaseModel):
    meta: Meta
    data: List[FlightOffer]
