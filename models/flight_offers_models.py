from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union

class FlightEndPoint(BaseModel):
    iataCode: str
    terminal: Optional[str] = None
    at: str

class AircraftEquipment(BaseModel):
    code: str

class OperatingFlight(BaseModel):
    carrierCode: Optional[str] = None

class Segment(BaseModel):
    id: str
    departure: FlightEndPoint
    arrival: FlightEndPoint
    carrierCode: str
    number: str
    aircraft: AircraftEquipment
    operating: Optional[OperatingFlight] = None
    duration: str
    numberOfStops: int
    blacklistedInEU: bool

class Itinerary(BaseModel):
    duration: str
    segments: List[Segment]

class Fee(BaseModel):
    amount: str
    type: str

class AdditionalService(BaseModel):
    amount: str
    type: str

class Price(BaseModel):
    currency: str
    total: str
    base: str
    fees: Optional[List[Fee]] = None
    grandTotal: Optional[str] = None
    additionalServices: Optional[List[AdditionalService]] = None

class PricingOptions(BaseModel):
    fareType: List[str]
    includedCheckedBagsOnly: bool

class IncludedCheckedBags(BaseModel):
    quantity: Optional[int] = None
    weight: Optional[int] = None
    weightUnit: Optional[str] = None

class FareDetailsBySegment(BaseModel):
    segmentId: str
    cabin: str
    fareBasis: str
    brandedFare: Optional[str] = None
    brandedFareLabel: Optional[str] = None
    class_: str = Field(..., alias='class')
    includedCheckedBags: Optional[IncludedCheckedBags] = None

class TravelerPricing(BaseModel):
    travelerId: str
    fareOption: str
    travelerType: str
    price: Price
    fareDetailsBySegment: List[FareDetailsBySegment]

class FlightOffer(BaseModel):
    type: str
    id: str
    source: str
    instantTicketingRequired: bool
    nonHomogeneous: bool
    oneWay: bool
    lastTicketingDate: Optional[str] = None
    lastTicketingDateTime: Optional[str] = None
    numberOfBookableSeats: int
    itineraries: List[Itinerary]
    price: Price
    pricingOptions: PricingOptions
    validatingAirlineCodes: List[str]
    travelerPricings: List[TravelerPricing]

class CollectionMeta(BaseModel):
    count: int
    links: dict

class FlightOffersSearchResponse(BaseModel):
    meta: CollectionMeta
    data: List[FlightOffer]

    @validator('data')
    def validate_data(cls, v):
        if not v:
            raise ValueError("Data field cannot be empty")
        return v

