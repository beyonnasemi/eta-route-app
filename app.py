import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from src.api_handler import fetch_ais_data
from src.calculator import calculate_haversine_distance, estimate_eta

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="AIS 실시간 지도 및 ETA",
    page_icon="🚢",
    layout="wide"
)

# --- 2. 앱 제목 및 설명 ---
st.title("🚢 AIS 실시간 항로 및 ETA 모니터링")
st.markdown("전 세계 선박의 위치를 추적하고 목적지까지의 도착 예정 시간(ETA)을 계산합니다.")

# --- 3. 사이드바 설정 ---
st.sidebar.header("⚙️ 설정")
st.sidebar.info("핀란드 해양청(Digitraffic) 실시간 데이터를 사용 중입니다.")
if st.sidebar.button("🔄 데이터 새로고침"):
    st.cache_data.clear() # 캐시 삭제 후 새로고침

# 주요 항구 및 관심 지역 위치 데이터
PORTS = {
    "헬싱키 (Helsinki)": {"lat": 60.160, "lon": 24.950},
    "투르쿠 (Turku)": {"lat": 60.430, "lon": 22.220},
    "탈린 (Tallinn)": {"lat": 59.440, "lon": 24.760},
    "코트카 (Kotka)": {"lat": 60.460, "lon": 26.940},
    "라우마 (Rauma)": {"lat": 61.130, "lon": 21.450},
    "포리 (Pori)": {"lat": 61.480, "lon": 21.780},
    "오울루 (Oulu)": {"lat": 65.010, "lon": 25.460},
    "상트페테르부르크": {"lat": 59.930, "lon": 30.310},
    "스톡홀름": {"lat": 59.330, "lon": 18.060}
}

# --- 4. 데이터 로드 ---
try:
    with st.spinner('핀란드 해양청에서 실시간 위성 AIS 데이터를 불러오는 중...'):
        df = fetch_ais_data()

    if not df.empty:
        # 데이터 출처 표시
        if df['is_real_data'].iloc[0]:
            st.sidebar.success(f"✅ 실시간 연결 성공 (총 {len(df):,}척 수신)")
        else:
            st.sidebar.warning("⚠️ 네트워크 오류로 샘플 데이터를 표시 중입니다.")

        # --- 필터 설정 ---
        st.sidebar.subheader("🔍 선박 필터링")
        
        # 1. 선박명 검색
        search_query = st.sidebar.text_input("🚢 선박 이름으로 찾기", "").strip()
        
        # 2. 목적지(Destination) 필터 고도화
        # 데이터 내 실제 목적지 값들 정리 (대문자 변환 및 중복 제거)
        raw_destinations = df['destination'].astype(str).str.upper().unique()
        raw_destinations = sorted([d for d in raw_destinations if d not in ['정보 없음', 'UNKNOWN', 'NAN', '']])
        
        st.sidebar.markdown("📍 **지역/목적지 선택**")
        
        # 주요 핀란드 항구 리스트 제공
        major_finnish_ports = ["HELSINKI", "TURKU", "TALLINN", "KOTKA", "RAUMA", "HAMINA", "HANKO", "PORI", "OULU"]
        
        filter_mode = st.sidebar.radio("필터 모드", ["전체 보기", "주요 항구", "직접 선택"], index=0)
        
        filtered_df = df.copy()
        
        if filter_mode == "주요 항구":
            selected_port_name = st.sidebar.selectbox("대상 항구 선택", major_finnish_ports)
            # 목적지 문자열에 해당 항구 이름이 포함된 경우만 필터링
            filtered_df = df[df['destination'].astype(str).str.upper().str.contains(selected_port_name, na=False)]
            if filtered_df.empty:
                st.sidebar.info(f"'{selected_port_name}'(으)로 이동 중인 것으로 표시된 배가 현재 데이터에 없습니다. (AIS 목적지는 항해사가 입력하므로 값이 다를 수 있습니다.)")
        
        elif filter_mode == "직접 선택":
            if not raw_destinations:
                st.sidebar.info("선택 가능한 구체적인 목적지 정보가 현재 데이터에 없습니다.")
                selected_dests = []
            else:
                selected_dests = st.sidebar.multiselect("목적지 상세 선택", raw_destinations)
                if selected_dests:
                    filtered_df = df[df['destination'].astype(str).str.upper().isin(selected_dests)]
        
        # 선박명 검색어 적용
        if search_query:
            filtered_df = filtered_df[filtered_df['vessel_name'].str.contains(search_query, case=False, na=False)]

        # 상단 요약 지표
        m1, m2, m3 = st.columns(3)
        m1.metric("표시 중인 선박", f"{len(filtered_df):,} 척")
        m2.metric("필터링된 선박 최고 속력", f"{filtered_df['speed'].max() if not filtered_df.empty else 0} Kn")
        m3.metric("평균 속력 (선택 범위)", f"{round(filtered_df['speed'].mean(), 1) if not filtered_df.empty else 0} Kn")

        # 화면 구성을 위한 탭
        tab_map, tab_eta, tab_data = st.tabs(["🗺️ 실시간 지도 시각화", "⏳ 항로 ETA 계산", "📊 선박 리스트"])

        with tab_map:
            if not filtered_df.empty:
                # 성능을 위해 상위 2000개만 지도에 표시
                map_display_df = filtered_df.head(2000)
                if len(filtered_df) > 2000:
                    st.info(f"ℹ️ 데이터가 너무 많아 상위 2,000척만 지도에 표시합니다. (전체: {len(filtered_df):,}척)")

                avg_lat = map_display_df['lat'].mean()
                avg_lon = map_display_df['lon'].mean()
                m = folium.Map(location=[avg_lat, avg_lon], zoom_start=7)
                
                # 마커 클러스터 추가
                marker_cluster = MarkerCluster().add_to(m)

                for i, row in map_display_df.iterrows():
                    dest_info = row['destination'] if row['destination'] != '정보 없음' else '미입력'
                    popup_text = f"<b>{row['vessel_name']}</b><br>목적지: {dest_info}<br>속도: {row['speed']} Kn"
                    color = "blue" if row['speed'] > 0.5 else "red"
                    folium.Marker(
                        location=[row['lat'], row['lon']],
                        popup=folium.Popup(popup_text, max_width=200),
                        tooltip=f"{row['vessel_name']} (To: {dest_info})",
                        icon=folium.Icon(color=color, icon='ship', prefix='fa')
                    ).add_to(marker_cluster)

                st_folium(m, width="stretch", height=500, key="main_map")
            else:
                st.info("선택한 목적지에 해당하는 선박이 없습니다. 왼쪽 사이드바에서 목적지를 선택해 주세요.")

        with tab_eta:
            st.subheader("🎯 도착 예정 시간(ETA) 계산")
            # 항해 중인 배만 필터링해서 보여주기
            moving_vessels = filtered_df[filtered_df['speed'] > 0.5]
            
            if not moving_vessels.empty:
                col_v, col_p = st.columns(2)
                with col_v:
                    selected_vessel = st.selectbox("항해 중인 선박 선택", sorted(moving_vessels['vessel_name'].unique()))
                with col_p:
                    selected_port = st.selectbox("목적지 항구 선택", list(PORTS.keys()))

                v_data = moving_vessels[moving_vessels['vessel_name'] == selected_vessel].iloc[0]
                p_data = PORTS[selected_port]
                dist = calculate_haversine_distance(v_data['lat'], v_data['lon'], p_data['lat'], p_data['lon'])
                arrival_time, hours = estimate_eta(dist, v_data['speed'])
                
                res_c1, res_c2, res_c3 = st.columns(3)
                res_c1.metric("남은 거리", f"{round(dist, 1)} km")
                res_c2.metric("현재 속도", f"{v_data['speed']} Kn")
                if arrival_time:
                    res_c3.metric("예상 소요 시간", f"{round(hours, 1)} 시간")
                    st.success(f"✅ **{selected_vessel}** 선박은 약 **{round(hours, 1)}시간** 후 도착 예정입니다.")
            else:
                st.info("현재 필터링된 선박 중 이동 중인 선박이 없습니다.")

        with tab_data:
            st.subheader("상세 선박 정보 목록")
            st.dataframe(filtered_df, width="stretch")

    else:
        st.warning("데이터를 불러올 수 없습니다.")

except Exception as e:
    st.error(f"앱 실행 중 오류가 발생했습니다: {e}")

st.divider()
st.caption("© 2026 eta-route-app | Data sourced from Digitraffic Finland")
