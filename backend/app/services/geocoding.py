"""Fetchify.io UK postcode → lat/lng geocoding service."""

import httpx
from app.config import settings


async def geocode_postcode(postcode: str) -> tuple[float, float] | None:
    """
    Return (latitude, longitude) for a UK postcode via Fetchify.io.
    Returns None if lookup fails.
    """
    if not settings.fetchify_api_key:
        return None

    clean_postcode = postcode.strip().upper().replace(" ", "")
    url = "https://pcls1.craftyclicks.co.uk/json/rapidaddress"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                params={
                    "key": settings.fetchify_api_key,
                    "postcode": clean_postcode,
                    "response": "data_formatted",
                },
            )
            response.raise_for_status()
            data = response.json()

            if "error_code" in data:
                return None

            delivery_points = data.get("delivery_points", [])
            if delivery_points:
                lat = float(data.get("latitude", 0))
                lng = float(data.get("longitude", 0))
                if lat and lng:
                    return lat, lng

            # Fallback to root-level lat/lng
            lat = data.get("latitude")
            lng = data.get("longitude")
            if lat and lng:
                return float(lat), float(lng)

    except (httpx.HTTPError, ValueError, KeyError):
        pass

    return None
