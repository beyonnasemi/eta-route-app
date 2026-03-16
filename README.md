# 🚢 AIS 선박 실시간 위치 및 ETA 모니터링 시스템

이 프로젝트는 핀란드 해양청(Digitraffic Finland)의 오픈 API를 활용하여 실시간 선박 데이터를 수집하고, 이를 지도에 시각화하며 목적지까지의 ETA(도착 예정 시간)를 계산하는 Streamlit 기반 웹 애플리케이션입니다.

---

## ✨ 주요 기능

1.  **실시간 데이터 수집**: 공식 AIS 오픈 API를 연동하여 실시간 선박 정보(MMSI, 위도, 경도, 속도, 목적지 등)를 수집합니다.
2.  **인터랙티브 지도**: 실시간 선박 위치를 지도에 마커로 표시하며, 선박의 상태(항해/정지)에 따라 마커 색상을 구분합니다.
3.  **데이터 필터링**: 목적지(Destination)별로 선박을 필터링하여 원하는 정보만 확인할 수 있습니다.
4.  **ETA 계산기**: 하버사인(Haversine) 공식을 활용해 현재 위치에서 주요 항구까지의 거리와 도착 예정 시간을 계산합니다.
5.  **자동 복구(Fallback)**: 네트워크 연결 이슈 발생 시 자동으로 샘플 데이터를 로드하여 앱 사용성을 보장합니다.

---

## 📂 프로젝트 구조

```text
eta-route-app/
├── src/
│   ├── api_handler.py    # AIS 데이터 수집 및 전처리 로직
│   └── calculator.py     # 거리 및 ETA 계산 로직
├── app.py                # Streamlit 메인 애플리케이션 파일
├── requirements.txt      # 프로젝트 의존성 라이브러리 목록
└── README.md             # 프로젝트 설명서 (본 파일)
```

---

## 🚀 로컬 실행 방법

가상환경을 사용하거나 아래 명령어를 터미널에 입력하여 실행할 수 있습니다.

1.  **필수 라이브러리 설치**
    ```bash
    pip install streamlit pandas requests folium streamlit-folium geopy
    ```

2.  **애플리케이션 실행**
    ```bash
    streamlit run app.py
    ```

---

## 🌐 서버 배포 방법 (Streamlit Cloud)

1.  **GitHub에 코드 업로드**: 새 Repository를 만들어 `app.py`, `requirements.txt`, `src/` 폴더를 모두 업로드합니다.
2.  **Streamlit Cloud 가입**: [share.streamlit.io](https://share.streamlit.io/)에 접속하여 GitHub 계정으로 로그인합니다.
3.  **App 생성**: `Deploy an app` 버튼을 누르고 해당 저장소를 선택합니다.
4.  **배포**: `Main file path`를 `app.py`로 설정한 후 `Deploy`를 클릭합니다.

---

## 📝 주의사항

- **네트워크 설정**: 로컬 환경에서 핀란드 서버 접속이 원활하지 않을 경우 `DNS`를 `8.8.8.8`로 변경하거나, 배포 환경(Streamlit Cloud)을 권장합니다.
- **데이터 출처**: 본 서비스는 핀란드 해양청(Digitraffic Finland)의 공공 데이터를 활용합니다.

---
**문의 및 지원**: [사용 중인 AI 어시스턴트에게 질문해 주세요!]
