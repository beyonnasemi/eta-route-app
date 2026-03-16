import requests
import pandas as pd

def fetch_ais_data():
    """
    핀란드 해양청 공식 API(meri.digitraffic.fi)에서 실시간 선박 위치 데이터를 가져옵니다.
    네트워크 문제로 접속이 불가능할 경우 실습용 샘플 데이터를 반환합니다.
    """
    # 안정적인 공식 API 엔드포인트
    url = "https://meri.digitraffic.fi/api/ais/v1/locations"
    
    headers = {
        "User-Agent": "eta-route-app/1.0 (Student Project; contact: your-email@example.com)",
        "Accept-Encoding": "gzip",
        "Accept": "application/json"
    }

    try:
        # 데이터 가져오기에 15초 제한을 두어 무한 대기를 방지합니다.
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        vessels = []
        # GeoJSON의 features 리스트를 순회하며 데이터 추출
        for feature in data.get('features', []):
            prop = feature.get('properties', {})
            geom = feature.get('geometry', {})
            coords = geom.get('coordinates', [0, 0])
            
            # 필수 데이터(MMSI, 좌표)가 있는 경우만 추가
            if prop.get('mmsi') and len(coords) >= 2:
                vessels.append({
                    "mmsi": prop.get('mmsi'),
                    "lat": coords[1], # GeoJSON은 [경도, 위도] 순서
                    "lon": coords[0],
                    "speed": prop.get('sog', 0.0),
                    "vessel_name": prop.get('name', f"Vessel-{prop.get('mmsi')}"),
                    "destination": prop.get('destination', '정보 없음'),
                    "timestamp": prop.get('timestamp')
                })
            
        df = pd.DataFrame(vessels)
        
        if not df.empty:
            df['is_real_data'] = True
            return df
        else:
            raise ValueError("API 응답에 선박 데이터가 없습니다.")

    except Exception as e:
        # API 접속 실패 시 사용자에게 알리기 위해 터미널에 로그를 남깁니다.
        print(f"⚠️ 실시간 API 연결 실패: {e}")
        
        # 실습을 위해 미리 준비된 샘플 데이터 (핀란드 헬싱키 인근)
        sample_vessels = [
            {"mmsi": 230991000, "lat": 60.169, "lon": 24.938, "speed": 12.5, "vessel_name": "HELSINKI_EXPRESS", "destination": "Turku"},
            {"mmsi": 211234000, "lat": 59.933, "lon": 24.450, "speed": 8.2, "vessel_name": "FINLAND_STAR", "destination": "Tallinn"},
            {"mmsi": 440123000, "lat": 60.450, "lon": 22.260, "speed": 0.5, "vessel_name": "TURKU_PORT", "destination": "Helsinki"},
            {"mmsi": 230112233, "lat": 60.100, "lon": 25.100, "speed": 18.0, "vessel_name": "BALTIC_LINER", "destination": "Kotka"}
        ]
        df_sample = pd.DataFrame(sample_vessels)
        df_sample['is_real_data'] = False
        return df_sample

if __name__ == "__main__":
    # 단독 실행 시 데이터 확인용
    result_df = fetch_ais_data()
    print(f"실시간 데이터 여부: {result_df['is_real_data'].iloc[0]}")
    print(result_df.head())
