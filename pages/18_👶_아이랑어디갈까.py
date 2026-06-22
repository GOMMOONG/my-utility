# -*- coding: utf-8 -*-
# 아이랑 어디갈까 — 3~7세 아동 여행지/놀이시설 검색 (웹 버전)

import streamlit as st
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password
from data.kids_travel_data import PLACES, CATEGORIES, REGIONS

st.set_page_config(page_title="아이랑 어디갈까 - 마이 유틸리티", page_icon="👶", layout="wide")
apply_common_style()
check_password()
show_page_header("👶", "아이랑 어디갈까?", "3~7세 아이와 함께 갈 수 있는 여행지·놀이시설을 검색합니다")

# 현재 월
current_month = datetime.now().month

# ── 카테고리별 색상 ──
CATEGORY_COLORS = {
    "테마파크/놀이공원": "#FF6B6B",
    "키즈카페/실내놀이터": "#FF9F43",
    "체험학습/교육": "#54A0FF",
    "자연/공원": "#5CD85C",
    "동물원/수족관": "#00D2D3",
    "박물관/전시관": "#A55EEA",
    "워터파크/물놀이": "#2E86DE",
    "농장/목장체험": "#F9CA24",
}

INDOOR_ICONS = {"실내": "🏠", "실외": "🌳", "실내외": "🏠🌳"}
SEASON_ICONS = {"봄": "🌸", "여름": "☀️", "가을": "🍂", "겨울": "❄️"}

# ── 필터 영역 ──
st.markdown("### 🔍 검색 조건")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    season_options = ["전체", "봄 (3~5월)", "여름 (6~8월)", "가을 (9~11월)", "겨울 (12~2월)"]
    season_sel = st.selectbox("계절", season_options)

with col2:
    month_options = ["전체"] + [f"{m}월" for m in range(1, 13)]
    default_month = month_options[current_month]
    month_sel = st.selectbox("월", month_options, index=month_options.index(default_month))

with col3:
    indoor_options = ["전체", "실내", "실외", "실내외"]
    indoor_sel = st.selectbox("실내/실외", indoor_options)

with col4:
    category_sel = st.selectbox("종류", CATEGORIES)

with col5:
    region_sel = st.selectbox("지역", REGIONS)

# ── 필터링 ──
season = None
if season_sel != "전체":
    season = season_sel.split(" ")[0]

month = None
if month_sel != "전체":
    month = int(month_sel.replace("월", ""))

results = []
for place in PLACES:
    if season and season not in place["seasons"]:
        continue
    if month and month not in place["months"]:
        continue
    if indoor_sel != "전체" and place["indoor"] != indoor_sel:
        continue
    if category_sel != "전체" and place["category"] != category_sel:
        continue
    if region_sel != "전체" and place["region"] != region_sel:
        continue
    results.append(place)

# ── 결과 개수 표시 ──
st.markdown(f"**검색 결과: {len(results)}곳** (전체 {len(PLACES)}곳 중)")
st.divider()

# ── 결과가 없을 때 ──
if not results:
    st.info("😢 조건에 맞는 장소가 없습니다. 필터를 바꿔서 다시 검색해보세요!")

# ── 결과 카드 표시 ──
for i, place in enumerate(results):
    cat_color = CATEGORY_COLORS.get(place["category"], "#999")
    indoor_icon = INDOOR_ICONS.get(place["indoor"], "")
    season_text = " ".join([f"{SEASON_ICONS.get(s, '')}{s}" for s in place["seasons"]])

    with st.container():
        # 카드 상단: 카테고리 뱃지 + 기본 정보
        badge_col, info_col = st.columns([3, 1])
        with badge_col:
            st.markdown(
                f'<span style="background-color:{cat_color}; color:white; padding:2px 10px; '
                f'border-radius:10px; font-size:0.8em;">{place["category"]}</span>'
                f'&nbsp;&nbsp;{indoor_icon} {place["indoor"]}'
                f'&nbsp;&nbsp;📍 {place["region"]}',
                unsafe_allow_html=True,
            )
        with info_col:
            st.markdown(f'👶 {place["age"]}')

        # 장소 이름 + 설명
        st.markdown(f'#### {place["name"]}')
        st.markdown(f'{place["desc"]}')

        # 계절 + 가격
        price_col, season_col = st.columns(2)
        with season_col:
            st.caption(season_text)
        with price_col:
            st.caption(f'💰 {place["price"]}')

        # 상세 보기 (확장 패널)
        with st.expander("📋 상세 정보 보기"):
            detail_col1, detail_col2 = st.columns(2)

            with detail_col1:
                st.markdown("**📍 주소**")
                st.info(place["address"])
                st.markdown("**💰 입장료**")
                st.info(place["price"])

            with detail_col2:
                st.markdown("**💡 방문 팁**")
                st.success(place["tip"])
                st.markdown("**🗓️ 추천 시기**")
                month_text = ", ".join([f"{m}월" for m in sorted(place["months"])])
                st.info(f"{season_text}\n\n추천 월: {month_text}")

            # 버튼 영역
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            with btn_col1:
                naver_map_url = f"https://map.naver.com/v5/search/{place['name']}"
                st.link_button("🗺️ 네이버 지도에서 보기", naver_map_url, use_container_width=True)
            with btn_col2:
                if place.get("url"):
                    st.link_button("🌐 홈페이지 열기", place["url"], use_container_width=True)
                else:
                    st.button("🌐 홈페이지 없음", disabled=True, use_container_width=True, key=f"no_url_{i}")
            with btn_col3:
                kakao_map_url = f"https://map.kakao.com/?q={place['name']}"
                st.link_button("🗺️ 카카오맵에서 보기", kakao_map_url, use_container_width=True)

        st.divider()
