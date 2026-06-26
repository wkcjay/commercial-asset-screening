import math


EARTH_RADIUS_KM = 6371.0088


def distance_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    a_lat_rad = math.radians(a_lat)
    b_lat_rad = math.radians(b_lat)
    delta_lat = math.radians(b_lat - a_lat)
    delta_lon = math.radians(b_lon - a_lon)

    hav = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(a_lat_rad) * math.cos(b_lat_rad) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(hav))
