import streamlit as st
import re
import requests
import folium
from streamlit_folium import st_folium
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password
from api_config import get_key, set_key

st.set_page_config(page_title="쏘가리낚시 - 마이 유틸리티", page_icon="🐟", layout="wide")
apply_common_style()
check_password()
show_page_header("🐟", "쏘가리 낚시 포인트 검색", "네이버 블로그에서 쏘가리 서식지·낚시 포인트를 검색하고 지도에서 확인합니다")

SEARCH_URL = "https://openapi.naver.com/v1/search/blog.json"

# ── 전국 쏘가리 낚시 포인트 데이터 ──
FISHING_SPOTS = [
    {"name": "동강 (영월)", "lat": 37.1697, "lng": 128.4617,
     "info": "쏘가리 대표 서식지, 맑은 물과 바위 지형", "keywords": ["동강", "영월"]},
    {"name": "서강 (영월)", "lat": 37.1836, "lng": 128.4100,
     "info": "동강과 합류하는 서강, 소규모 포인트 다수", "keywords": ["서강"]},
    {"name": "평창강", "lat": 37.3700, "lng": 128.3900,
     "info": "평창 일대 맑은 계류, 루어 낚시 인기", "keywords": ["평창강", "평창"]},
    {"name": "금강 상류 (무주)", "lat": 35.9200, "lng": 127.7500,
     "info": "무주 구천동 일대, 여름 피서와 함께", "keywords": ["무주", "구천동", "금강"]},
    {"name": "금강 (금산)", "lat": 36.1000, "lng": 127.4900,
     "info": "금산 일대 금강 본류, 가을 시즌 인기", "keywords": ["금산"]},
    {"name": "내성천 (봉화)", "lat": 36.8900, "lng": 128.7300,
     "info": "모래 하천으로 유명, 깨끗한 수질", "keywords": ["내성천", "봉화"]},
    {"name": "낙동강 상류 (안동)", "lat": 36.5700, "lng": 128.7300,
     "info": "안동댐 하류 구간, 대형 쏘가리 출몰", "keywords": ["낙동강", "안동"]},
    {"name": "섬진강 (구례)", "lat": 35.2000, "lng": 127.4700,
     "info": "섬진강 중류, 봄 벚꽃 시즌과 함께", "keywords": ["섬진강", "구례"]},
    {"name": "한탄강 (포천)", "lat": 38.0500, "lng": 127.1200,
     "info": "현무암 협곡, 독특한 지형의 낚시 포인트", "keywords": ["한탄강", "포천", "철원"]},
    {"name": "남한강 (충주)", "lat": 36.9700, "lng": 127.9500,
     "info": "충주댐 하류, 접근성 좋은 도심 인근 포인트", "keywords": ["남한강", "충주", "여주"]},
    {"name": "가평천 (가평)", "lat": 37.8300, "lng": 127.5100,
     "info": "수도권 근교 인기 포인트, 계곡 낚시", "keywords": ["가평천", "가평"]},
    {"name": "조종천 (가평)", "lat": 37.7800, "lng": 127.3700,
     "info": "가평 조종천 합류부, 소규모 포인트", "keywords": ["조종천"]},
    {"name": "달천 (충주)", "lat": 36.9500, "lng": 127.8800,
     "info": "남한강 지류, 충주 시내 접근 용이", "keywords": ["달천"]},
    {"name": "옥동천 (봉화)", "lat": 36.8700, "lng": 128.8800,
     "info": "봉화 청량산 인근, 자연 그대로의 계류", "keywords": ["옥동천"]},
    {"name": "송천 (인제)", "lat": 38.1500, "lng": 128.2700,
     "info": "내린천 상류, 강원도 오지 포인트", "keywords": ["송천", "인제", "내린천"]},
]

# ── 원본 로직 함수들 ──
def clean_html(text):
    text = re.sub(r"</?b>", "", text)
    return text.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")

def format_date(postdate):
    if len(postdate) == 8:
        return f"{postdate[:4]}.{postdate[4:6]}.{postdate[6:8]}"
    return postdate

def search_blogs(query, client_id, client_secret, sort="sim", display=20, start=1):
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    res = requests.get(SEARCH_URL, params={"query": query, "display": display, "sort": sort, "start": start},
                       headers=headers, timeout=5)
    if res.status_code == 401:
        raise PermissionError("API 키가 올바르지 않습니다")
    res.raise_for_status()
    data = res.json()
    total = data.get("total", 0)
    items = []
    for item in data.get("items", []):
        items.append({
            "title": clean_html(item.get("title", "")),
            "description": clean_html(item.get("description", "")),
            "link": item.get("link", ""),
            "bloggername": item.get("bloggername", ""),
            "postdate": item.get("postdate", ""),
        })
    return items, total

def find_matching_spot(text):
    for spot in FISHING_SPOTS:
        for keyword in spot["keywords"]:
            if keyword in text:
                return spot
    return None

def create_map(center_lat=36.5, center_lng=127.8, zoom=7, highlight_spot=None):
    """전국 쏘가리 포인트가 표시된 지도를 만듦"""
    m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom)
    for spot in FISHING_SPOTS:
        # 강조할 포인트는 빨간색, 나머지는 파란색
        if highlight_spot and spot["name"] == highlight_spot["name"]:
            color = "red"
            icon_type = "star"
        else:
            color = "blue"
            icon_type = "info-sign"
        folium.Marker(
            location=[spot["lat"], spot["lng"]],
            popup=folium.Popup(f"<b>{spot['name']}</b><br>{spot['info']}", max_width=200),
            tooltip=spot["name"],
            icon=folium.Icon(color=color, icon=icon_type),
        ).add_to(m)
    return m

# ── API 키 관리 ──
# 파일에 저장된 키 우선, 없으면 Streamlit Secrets에서 시도
if "naver_id" not in st.session_state:
    saved_id = get_key("naver_client_id")
    if not saved_id:
        try:
            saved_id = st.secrets.get("naver_client_id", "")
        except Exception:
            saved_id = ""
    st.session_state.naver_id = saved_id

if "naver_secret" not in st.session_state:
    saved_secret = get_key("naver_client_secret")
    if not saved_secret:
        try:
            saved_secret = st.secrets.get("naver_client_secret", "")
        except Exception:
            saved_secret = ""
    st.session_state.naver_secret = saved_secret

with st.expander("⚙️ 네이버 API 키 설정 (처음 한 번만 필요)"):
    st.markdown("""
    1. [developers.naver.com](https://developers.naver.com) 접속 후 네이버 계정으로 로그인
    2. 상단 메뉴에서 **Application > 애플리케이션 등록** 클릭
    3. 애플리케이션 이름을 자유롭게 입력하고, 사용 API에서 **'검색'** 선택
    4. 등록 후 발급된 **Client ID**와 **Client Secret**을 아래에 입력하세요 (무료)

    ※ 최저가 검색에서 이미 등록했다면 같은 키를 사용하면 됩니다.
    """)
    naver_id = st.text_input("Client ID", value=st.session_state.naver_id, key="input_naver_id")
    naver_secret = st.text_input("Client Secret", value=st.session_state.naver_secret, type="password", key="input_naver_secret")
    if st.button("💾 저장 (다음에도 자동 입력됨)"):
        st.session_state.naver_id = naver_id
        st.session_state.naver_secret = naver_secret
        set_key("naver_client_id", naver_id)
        set_key("naver_client_secret", naver_secret)
        st.success("✅ API 키가 저장되었습니다! 다음번에 자동으로 불러옵니다.")

# ── 빠른 검색 버튼 ──
st.markdown("#### 🎣 빠른 검색")
preset_cols = st.columns(6)
preset_queries = [
    ("서식지", "쏘가리 서식지"), ("낚시 포인트", "쏘가리 낚시 포인트"),
    ("루어 낚시", "쏘가리 루어"), ("포인트 추천", "쏘가리 포인트 추천"),
    ("채비 방법", "쏘가리 채비"), ("시즌 정보", "쏘가리 시즌"),
]
for i, (label, query) in enumerate(preset_queries):
    with preset_cols[i]:
        if st.button(label, key=f"preset_{i}", use_container_width=True):
            st.session_state.sogari_query = query

# ── 검색 영역 ──
col_q, col_sort = st.columns([3, 1])
with col_q:
    query = st.text_input("검색어", value=st.session_state.get("sogari_query", ""),
                          placeholder="쏘가리 관련 검색어를 입력하세요", label_visibility="collapsed")
with col_sort:
    sort_option = st.selectbox("정렬", ["관련도순", "최신순"], label_visibility="collapsed")

sort_map = {"관련도순": "sim", "최신순": "date"}

search_clicked = st.button("🔍 검색", type="primary", use_container_width=True)

# ── 시즌 팁 ──
st.info("💡 **쏘가리 시즌 팁:** 봄(4~6월)과 가을(9~11월)이 쏘가리 낚시의 적기입니다. 수온 15~22°C에서 활성도가 높아요!")

# ── 검색 결과 + 지도 ──
col_results, col_map = st.columns([1, 1])

# 지도는 항상 표시
with col_map:
    st.markdown("#### 📍 전국 쏘가리 포인트 지도")
    highlight = st.session_state.get("highlight_spot", None)
    if highlight:
        m = create_map(center_lat=highlight["lat"], center_lng=highlight["lng"],
                       zoom=12, highlight_spot=highlight)
    else:
        m = create_map()
    st_folium(m, height=500, use_container_width=True)

# 검색 결과 영역
with col_results:
    if search_clicked or st.session_state.get("sogari_query"):
        search_query = query.strip() if search_clicked else st.session_state.get("sogari_query", "").strip()

        if not search_query:
            st.warning("검색어를 입력해주세요.")
        elif not st.session_state.naver_id or not st.session_state.naver_secret:
            st.warning("먼저 네이버 API 키를 설정해주세요. (위쪽 ⚙️ 버튼 클릭)")
        else:
            try:
                with st.spinner("검색하는 중입니다..."):
                    items, total = search_blogs(search_query, st.session_state.naver_id,
                                                st.session_state.naver_secret,
                                                sort=sort_map[sort_option])

                if not items:
                    st.info("검색 결과가 없습니다.")
                else:
                    st.success(f"총 {total:,}건 중 {len(items)}개 표시 ({sort_option})")
                    st.caption("※ 블로그 링크를 클릭하면 해당 글이 새 탭에서 열립니다.")

                    for item in items:
                        # 블로그 제목과 내용에서 낚시 포인트 지역을 찾기
                        text = item["title"] + " " + item["description"]
                        spot = find_matching_spot(text)
                        location_tag = f" 📍 {spot['name']}" if spot else ""

                        with st.container():
                            st.markdown(f"**{item['title']}**{location_tag}")
                            desc = item["description"][:120] + "..." if len(item["description"]) > 120 else item["description"]
                            st.caption(desc)

                            info_col, link_col = st.columns([3, 1])
                            with info_col:
                                st.caption(f"✍️ {item['bloggername']} · 📅 {format_date(item['postdate'])}")
                            with link_col:
                                st.link_button("블로그 보기", item["link"], use_container_width=True)

                            # 지도에서 보기 버튼 (관련 위치가 있을 때만)
                            if spot:
                                if st.button(f"🗺 {spot['name']} 지도 보기", key=f"map_{item['link']}"):
                                    st.session_state.highlight_spot = spot
                                    st.rerun()
                            st.divider()

            except PermissionError:
                st.error("API 키가 올바르지 않습니다. ⚙️ 설정에서 다시 입력해주세요.")
            except requests.exceptions.RequestException:
                st.error("인터넷 연결을 확인해주세요.")
            except Exception as e:
                st.error(f"검색 중 오류가 발생했습니다: {e}")
    else:
        st.markdown("#### 검색 결과")
        st.caption("위의 빠른 검색 버튼을 누르거나 검색어를 입력하세요.")

        # 포인트 목록도 함께 표시
        st.markdown("---")
        st.markdown("#### 📋 전국 쏘가리 주요 포인트")
        for spot in FISHING_SPOTS:
            st.markdown(f"**📍 {spot['name']}** — {spot['info']}")
