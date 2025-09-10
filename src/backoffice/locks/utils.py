from geopy.distance import distance


def is_within_radius(lat1, lon1, lat2, lon2, radius_meters):
    """
    Returns True if (lat2, lon2) is within radius_meters of (lat1, lon1).
    """
    return distance((lat1, lon1), (lat2, lon2)).meters <= radius_meters
