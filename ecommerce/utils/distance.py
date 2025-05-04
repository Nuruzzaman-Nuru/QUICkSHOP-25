from math import radians, sin, cos, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points in kilometers using Haversine formula
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

def get_formatted_distance(distance):
    """
    Format distance in a human-readable way
    """
    if distance < 1:
        return f"{distance * 1000:.0f}m"
    return f"{distance:.1f}km"

def estimate_travel_time(distance, transport_mode='car'):
    """
    Estimate travel time in minutes based on distance and transport mode
    """
    speeds = {
        'walk': 5,      # 5 km/h walking speed
        'bike': 15,     # 15 km/h cycling speed
        'car': 30       # 30 km/h urban driving speed
    }
    
    speed = speeds.get(transport_mode, speeds['car'])
    time_hours = distance / speed
    return round(time_hours * 60)  # Convert to minutes