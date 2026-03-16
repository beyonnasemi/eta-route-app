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

# 주요 항구 위치 데이터
PORTS = {
    "헬싱키 (Helsinki)": {"lat": 60.16, "lon": 24.95},
    "투르쿠 (Turku)": {"lat": 60.43, "lon": 22.22},
    "탈린 (Tallinn)": {"lat": 59.44, "lon": 24.76},
    "상트페테르부르크": {"lat": 59.93, "lon": 30.31}
}

# --- 4. 데이터 로드 ---
try:
    with st.spinner('실시간 위치 정보를 가져오는 중입니다...'):
        df = fetch_ais_data()

    if not df.empty:
        # 데이터 출처 표시
        if df['is_real_data'].iloc[0]:
            st.sidebar.success(f"✅ 실시간 연결 성공 (총 {len(df):,}척)")
        else:
            st.sidebar.warning("⚠️ 네트워크 오류로 샘플 데이터를 표시 중입니다.")

        # --- 필터 설정 ---
        st.sidebar.subheader("🔍 필터")
        all_destinations = sorted([str(d) for d in df['destination'].unique()])
        # 데이터가 너무 많으므로 초기에는 '정보 없음' 또는 일부만 선택
        default_selection = [d for d in all_destinations if d == '정보 없음' or d == 'Unknown']
        if not default_selection:
            default_selection = all_destinations[:5]

        selected_dests = st.sidebar.multiselect("목적지별 필터링", all_destinations, default=default_selection)
        
        # 필터링 적용
        filtered_df = df[df['destination'].isin(selected_dests)]

        # 상단 요약 지표
        m1, m2, m3 = st.columns(3)
        m1.metric("표시 중인 선박", f"{len(filtered_df)} 척")
        m2.metric("최고 속력", f"{filtered_df['speed'].max() if not filtered_df.empty else 0} Kn")
        m3.metric("평균 속력", f"{round(filtered_df['speed'].mean(), 1) if not filtered_df.empty else 0} Kn")

        # 화면 구성을 위한 탭
        tab_map, tab_eta, tab_data = st.tabs(["🗺️ 실시간 지도", "⏳ ETA 계산기", "📊 상세 데이터"])

        with tab_map:
            if not filtered_df.empty:
                # 성능을 위해 상위 2000개만 지도에 표시
                map_display_df = filtered_df.head(2000)
                if len(filtered_df) > 2000:
                    st.info("ℹ️ 성능을 위해 상위 2,000척의 위치만 지도에 표시합니다. 필터를 사용해 범위를 좁히세요.")

                avg_lat = map_display_df['lat'].mean()
                avg_lon = map_display_df['lon'].mean()
                m = folium.Map(location=[avg_lat, avg_lon], zoom_start=7)
                
                # 마커 클러스터 추가 (수천 개의 마커 처리를 위해 필수)
                marker_cluster = MarkerCluster().add_to(m)

                for i, row in map_display_df.iterrows():
                    popup_text = f"<b>{row['vessel_name']}</b><br>목적지: {row['destination']}<br>속도: {row['speed']} Kn"
                    color = "blue" if row['speed'] > 0.5 else "red"
                    folium.Marker(
                        location=[row['lat'], row['lon']],
                        popup=folium.Popup(popup_text, max_width=200),
                        tooltip=row['vessel_name'],
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
