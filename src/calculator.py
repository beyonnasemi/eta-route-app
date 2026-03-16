import math
from datetime import datetime, timedelta

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """
    하버사인 공식(Haversine Formula)을 사용하여 두 지점(위경도) 사이의 
    직선 거리(km)를 계산합니다.
    """
    R = 6371  # 지구 반지름 (단위: km)
    
    # 위도, 경도를 라디안으로 변환
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(d_lat / 2) * math.sin(d_lat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) * math.sin(d_lon / 2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance

def estimate_eta(distance_km, speed_knots):
    """
    거리와 속력을 바탕으로 도착 예정 시간(ETA)을 계산합니다.
    - 1 Knot = 1.852 km/h
    """
    if speed_knots <= 0.5:
        return None, "선박이 정지 중이거나 속력이 너무 낮습니다."
    
    # 속력을 km/h로 변환
    speed_kmh = speed_knots * 1.852
    
    # 소요 시간 계산 (시간 단위)
    hours_needed = distance_km / speed_kmh
    
    # 현재 시간 기준으로 도착 예정 시간 산출
    eta_datetime = datetime.now() + timedelta(hours=hours_needed)
    
    return eta_datetime, hours_needed
