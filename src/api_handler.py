import requests
import pandas as pd

import requests
import pandas as pd

def fetch_ais_data(api_key=None):
    """
    핀란드 해양청 공식 API(meri.digitraffic.fi)에서 실시간 선박 데이터를 가져옵니다.
    """
    # 더 안정적인 공식 API 엔드포인트로 변경
    url = "https://meri.digitraffic.fi/api/ais/v1/locations"
    
    headers = {
        "User-Agent": "eta-route-app/1.0 (Student Project)",
        "Accept-Encoding": "gzip",
        "Accept": "application/json"
    }

    try:
        # 데이터 가져오기 시도
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        vessels = []
        for feature in data.get('features', []):
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            coordinates = geometry.get('coordinates', [0, 0])
            
            if not properties.get('mmsi') or len(coordinates) < 2:
                continue

            vessels.append({
                "mmsi": properties.get('mmsi'),
                "lat": coordinates[1],
                "lon": coordinates[0],
                "speed": properties.get('sog', 0.0),
                "vessel_name": properties.get('name', f"Vessel-{properties.get('mmsi')}"),
                "destination": properties.get('destination', 'Unknown'), # 목적지 필드 추가
                "timestamp": properties.get('timestamp')
            })
            
        df = pd.DataFrame(vessels)
        if not df.empty:
            # 실시간 데이터임을 표시하는 플래그 추가
            df['is_real_data'] = True
            return df

    except Exception as e:
        # 네트워크 오류 발생 시 샘플 데이터 반환
        print(f"⚠️ API 연결 실패: {e}")
        
        sample_vessels = [
            {"mmsi": 230991000, "lat": 60.169, "lon": 24.938, "speed": 12.5, "vessel_name": "HELSINKI_EXPRESS", "destination": "Turku"},
            {"mmsi": 211234000, "lat": 59.933, "lon": 24.450, "speed": 8.2, "vessel_name": "FINLAND_STAR", "destination": "Tallinn"},
            {"mmsi": 440123000, "lat": 60.450, "lon": 22.260, "speed": 0.5, "vessel_name": "TURKU_PORT", "destination": "Helsinki"},
            {"mmsi": 230112233, "lat": 60.100, "lon": 25.100, "speed": 18.0, "vessel_name": "BALTIC_LINER", "destination": "Kotka"}
        ]
        df_sample = pd.DataFrame(sample_vessels)
        df_sample['is_real_data'] = False # 샘플 데이터임을 표시
        return df_sample

# 코드 단독 실행 테스트용
if __name__ == "__main__":
    df = fetch_ais_data()
    print(df.head())
