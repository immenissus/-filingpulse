"""
app/services/geocoder.py
========================
Geocoder service using the free US Census Bureau Geocoding Services API.
Makes HTTP requests to resolve address strings to coordinates (WGS-84).
"""

from __future__ import annotations

import logging
import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

from app.config import get_settings
from app.schemas.geocode import CensusApiResponse, GeocodeResult

logger = logging.getLogger(__name__)
settings = get_settings()


class GeocoderError(Exception):
    """Base exception for all geocoder service errors."""


class GeocoderNoMatchError(GeocoderError):
    """Raised when the Census API returns no matches for the address."""


class GeocoderServiceError(GeocoderError):
    """Raised when the Census API is unavailable or returns an error."""


class CensusGeocoder:
    """
    Client for the US Census Bureau Geocoding API.
    Does not require an API key.
    """

    def __init__(self) -> None:
        self.url = settings.census_geocoder_url
        self.benchmark = settings.census_geocoder_benchmark
        self.timeout = settings.census_geocoder_timeout
        
        # Configure requests session with connection pool and retries
        self.session = requests.Session()
        retries = Retry(
            total=settings.census_geocoder_retries,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def geocode(self, address_string: str) -> GeocodeResult:
        """
        Geocode a single address string using the US Census Bureau API.

        Parameters
        ----------
        address_string: str
            The address string to geocode (e.g. "1600 Pennsylvania Ave NW, Washington, DC").

        Returns
        -------
        GeocodeResult
            The canonical geocoding result containing lat, lng, and matched address.

        Raises
        ------
        GeocoderNoMatchError
            If no matches are found.
        GeocoderServiceError
            If the API request fails or is unparseable.
        """
        if not address_string or not address_string.strip():
            raise GeocoderNoMatchError("Cannot geocode empty address string.")

        params = {
            "address": address_string.strip(),
            "benchmark": self.benchmark,
            "format": "json",
        }

        try:
            response = self.session.get(
                self.url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            payload = response.json()
            api_resp = CensusApiResponse.model_validate(payload)
            
            matches = api_resp.result.addressMatches
            if not matches:
                raise GeocoderNoMatchError(f"No address matches found for: {address_string!r}")
            
            # Use the first match (Census returns highest-score match first)
            best_match = matches[0]
            
            # In GeocodeResult, latitude is best_match.coordinates.y (WGS-84) and longitude is x
            result = GeocodeResult(
                latitude=best_match.coordinates.y,
                longitude=best_match.coordinates.x,
                matched_address=best_match.matchedAddress,
                source="census_geocoder"
            )
            return result

        except requests.RequestException as e:
            logger.error("Census API request failed for %r: %s", address_string, str(e))
            raise GeocoderServiceError(f"Census Geocoder API error: {e}") from e
        except Exception as e:
            if isinstance(e, (GeocoderNoMatchError, GeocoderServiceError)):
                raise
            logger.error("Error parsing Census geocoder response for %r: %s", address_string, str(e))
            raise GeocoderServiceError(f"Failed to parse geocoder response: {e}") from e
