import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="캠핑장 조회 - 마이 유틸리티", page_icon="🏕️", layout="wide")
apply_common_style()
check_password()
show_page_header("🏕️", "금산 근처 캠핑장 조회", "금산 기준 차량 2시간 이내, 1박 5만원 이하 캠핑장을 검색합니다")

# ── 캠핑장 데이터 (원본 그대로) ──
CAMPGROUNDS = [
    {"name": "태안 머드 오토캠핑장", "address": "충남 태안군 안면읍 백사장2길",
     "price": 45000, "drive_time": "1시간 50분", "activity_type": "갯벌",
     "features": ["갯벌체험", "해루질", "조개캐기", "서해 일몰"],
     "naver_url": "https://map.naver.com/v5/search/태안+머드+오토캠핑장",
     "booking_url": "https://map.naver.com/v5/search/태안+머드+오토캠핑장",
     "phone": "041-674-0070", "rating": 4.4, "infant_ok": True,
     "tip": "조개·낙지·쏙 체험 가능. 해루질 장비 대여 포함."},
    {"name": "태안 캠핑드림", "address": "충남 태안군 근흥면 신진도리",
     "price": 40000, "drive_time": "1시간 55분", "activity_type": "갯벌",
     "features": ["갯벌체험", "바지락 캐기", "전기 사이트", "잔디 사이트"],
     "naver_url": "https://map.naver.com/v5/search/태안+캠핑드림",
     "booking_url": "https://map.naver.com/v5/search/태안+캠핑드림",
     "phone": "041-675-0077", "rating": 4.3, "infant_ok": True,
     "tip": "바닷가 바로 앞 위치. 아이들 조개캐기 체험 최적."},
    {"name": "태안 바다여행 오토캠핑장", "address": "충남 태안군 소원면 의항리",
     "price": 35000, "drive_time": "1시간 45분", "activity_type": "갯벌",
     "features": ["갯벌체험", "갯바위낚시", "해수욕장", "학암포항 인접"],
     "naver_url": "https://map.naver.com/v5/search/태안+학암포+오토캠핑장",
     "booking_url": "https://map.naver.com/v5/search/태안+학암포+오토캠핑장",
     "phone": "041-672-0088", "rating": 4.2, "infant_ok": True,
     "tip": "태안해안국립공원 관리 캠핑장. 신두사구·쥬라기박물관 인근."},
    {"name": "보령 간월도 캠핑장", "address": "충남 보령시 오천면 간월도리",
     "price": 30000, "drive_time": "1시간 40분", "activity_type": "갯벌",
     "features": ["갯벌체험", "간월암 뷰", "굴·바지락 채취", "서해 석양"],
     "naver_url": "https://map.naver.com/v5/search/보령+간월도+캠핑장",
     "booking_url": "https://map.naver.com/v5/search/보령+간월도+캠핑장",
     "phone": "041-930-3114", "rating": 4.1, "infant_ok": True,
     "tip": "간월암 일몰 감상 포인트. 굴·바지락 직접 채취 가능."},
    {"name": "무주 구천동 계곡 오토캠핑장 (보보캠핑)", "address": "전북 무주군 설천면 구천동로",
     "price": 35000, "drive_time": "55분", "activity_type": "계곡",
     "features": ["무주구천동 계곡", "물놀이", "덕유산 국립공원", "야생화"],
     "naver_url": "https://map.naver.com/v5/search/무주+구천동+계곡+캠핑장",
     "booking_url": "https://www.5gcamp.com/?c=camping&m=camping&page=view&uid=55",
     "phone": "063-322-0111", "rating": 4.5, "infant_ok": True,
     "tip": "구천동 33경 계곡 직접 접근. 여름 물놀이 명소."},
    {"name": "영동 물한계곡 맑은누리 캠핑장", "address": "충북 영동군 상촌면 물한계곡로",
     "price": 22000, "drive_time": "1시간 10분", "activity_type": "계곡",
     "features": ["물한계곡", "물놀이", "천연 그늘", "데크 14면"],
     "naver_url": "https://map.naver.com/v5/search/영동+물한계곡+맑은누리+캠핑장",
     "booking_url": "https://www.gocamping.or.kr/bsite/camp/info/read.do?c_no=1035",
     "phone": "043-740-3880", "rating": 4.3, "infant_ok": True,
     "tip": "물 맑기 전국 최상위. 공공캠핑장으로 저렴."},
    {"name": "영동 물한계곡 별밤펜션 오토캠핑장", "address": "충북 영동군 상촌면 물한6길 8-1",
     "price": 40000, "drive_time": "1시간 10분", "activity_type": "계곡",
     "features": ["물한계곡", "계곡 평상", "개별 데크", "족구장"],
     "naver_url": "https://map.naver.com/v5/search/영동+물한계곡+별밤펜션+캠핑장",
     "booking_url": "http://www.starmooncamp.com/",
     "phone": "010-4413-0073", "rating": 4.4, "infant_ok": True,
     "tip": "계곡 바로 앞 14개 개별 데크. VR 미리보기 제공."},
    {"name": "무주 덕유대 오토캠핑장", "address": "전북 무주군 설천면 백련사길 2",
     "price": 20000, "drive_time": "50분", "activity_type": "계곡",
     "features": ["구천동 계곡", "생태탐방", "덕유산 곤돌라", "국립공원"],
     "naver_url": "https://map.naver.com/v5/search/무주+덕유대+야영장",
     "booking_url": "https://reservation.knps.or.kr",
     "phone": "063-322-3161", "rating": 4.5, "infant_ok": True,
     "tip": "국립공원 운영 공공 캠핑장. 계곡 생태 해설 프로그램 운영."},
    {"name": "금산 인삼골 오토캠핑장", "address": "충남 금산군 제원면 달고개길 113",
     "price": 20000, "drive_time": "15분", "activity_type": "계곡",
     "features": ["금강 수영·물놀이", "배산임수", "전망데크", "어린이체험관"],
     "naver_url": "https://map.naver.com/v5/search/금산+인삼골+오토캠핑장",
     "booking_url": "https://camp.xticket.kr/web/main?shopEncode=15e1aaac36257a8e149e7dbb83f15fc65715e5f3d4b7687daf6165ce78c5ccf7",
     "phone": "041-750-3585", "rating": 4.3, "infant_ok": True,
     "tip": "금산에서 가장 가까운 계곡형 캠핑장. 금강 상류 물놀이 가능."},
    {"name": "금산청소년수련원 캠핑장", "address": "충남 금산군 제원면 용화로 343",
     "price": 30000, "drive_time": "20분", "activity_type": "수영장",
     "features": ["수영장 (7~8월 운영)", "에어바운스", "안전요원", "잔디운동장", "풋살경기장"],
     "naver_url": "https://map.naver.com/v5/search/금산청소년수련원+캠핑장",
     "booking_url": "https://gsytc.co.kr",
     "phone": "041-750-2800", "rating": 4.2, "infant_ok": True,
     "tip": "성인풀 100~120cm / 소인풀 60~70cm. 입장료 5,000원(별도). 7월15일 오픈."},
    {"name": "대전 장태산 자연휴양림 캠핑장", "address": "대전시 서구 장안로 461",
     "price": 25000, "drive_time": "45분", "activity_type": "수영장",
     "features": ["수영장 (여름 운영)", "메타세쿼이아 숲", "출렁다리", "자연휴양림"],
     "naver_url": "https://map.naver.com/v5/search/대전+장태산+자연휴양림",
     "booking_url": "https://jangtaesan.go.kr",
     "phone": "042-270-7883", "rating": 4.4, "infant_ok": True,
     "tip": "메타세쿼이아 숲속 캠핑. 여름 물놀이장 운영. 대전 인근 접근성 최고."},
]

TYPE_STYLE = {
    "갯벌": {"icon": "🦀", "color": "#e67e22"},
    "계곡": {"icon": "🏞", "color": "#27ae60"},
    "수영장": {"icon": "🏊", "color": "#2980b9"},
}

# ── 드라이브 시간 -> 분 변환 ──
def drive_minutes(time_str):
    t = time_str.replace("시간 ", "h").replace("분", "")
    if "h" in t:
        parts = t.split("h")
        return int(parts[0]) * 60 + (int(parts[1]) if parts[1] else 0)
    return int(t)

# ── 사이드바: 필터 & 정렬 ──
st.sidebar.markdown("### 🔍 검색 조건")

filter_type = st.sidebar.radio("체험 유형", ["전체", "갯벌 🦀", "계곡 🏞", "수영장 🏊"])
filter_key = filter_type.split()[0]

sort_option = st.sidebar.radio("정렬 기준", ["⏱ 거리순", "💰 가격순", "⭐ 평점순"])

st.sidebar.markdown("---")
st.sidebar.markdown("#### 📍 기본 조건")
st.sidebar.markdown("- **기준지**: 충남 금산군")
st.sidebar.markdown("- **범위**: 차량 2시간 이내")
st.sidebar.markdown("- **인원**: 성인 3명 / 유아 2명")
st.sidebar.markdown("- **예산**: 1박 50,000원 이하")

# ── 필터링 ──
camps = [c for c in CAMPGROUNDS if filter_key == "전체" or c["activity_type"] == filter_key]

# ── 정렬 ──
if "가격순" in sort_option:
    camps.sort(key=lambda c: c["price"])
elif "평점순" in sort_option:
    camps.sort(key=lambda c: -c["rating"])
else:
    camps.sort(key=lambda c: drive_minutes(c["drive_time"]))

st.markdown(f"**총 {len(camps)}개 캠핑장**")

# ── 캠핑장 카드 표시 ──
for camp in camps:
    style = TYPE_STYLE[camp["activity_type"]]
    stars = "★" * int(camp["rating"]) + "☆" * (5 - int(camp["rating"]))

    # 특징 태그 문자열
    feature_tags = " · ".join(camp["features"])
    infant_tag = " · 👶 유아가능" if camp.get("infant_ok") else ""

    st.markdown(f"""
    <div style="background: white; border-radius: 12px; padding: 20px; margin: 12px 0;
                border-left: 5px solid {style['color']}; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div>
                <span style="font-size: 1.3em; font-weight: bold;">{style['icon']} {camp['name']}</span>
                <span style="background: {style['color']}20; color: {style['color']}; padding: 2px 8px;
                      border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-left: 8px;">{camp['activity_type']}</span>
                <span style="color: #f1c40f; margin-left: 8px;">{stars} {camp['rating']}</span>
            </div>
            <span style="font-size: 1.2em; font-weight: bold; color: {style['color']};">₩{camp['price']:,}/박</span>
        </div>
        <div style="color: #636E72; font-size: 0.9em; margin-bottom: 6px;">
            📍 {camp['address']} &nbsp;&nbsp; 🚗 금산에서 {camp['drive_time']} &nbsp;&nbsp; 📞 {camp.get('phone', '')}
        </div>
        <div style="color: {style['color']}; font-size: 0.85em; margin-bottom: 6px;">
            {feature_tags}{infant_tag}
        </div>
        <div style="color: #7f8c8d; font-size: 0.85em;">
            💡 {camp.get('tip', '')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_map, col_book = st.columns(2)
    with col_map:
        st.link_button(f"🗺️ 네이버 지도", camp["naver_url"], use_container_width=True)
    with col_book:
        st.link_button(f"📋 예약 페이지", camp["booking_url"], use_container_width=True)
