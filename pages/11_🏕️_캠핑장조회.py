import streamlit as st
import sys, os, json, urllib.parse, urllib.request, ssl
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password
from api_config import get_key, set_key

st.set_page_config(page_title="캠핑장 조회 - 마이 유틸리티", page_icon="🏕️", layout="wide")
apply_common_style()
check_password()
show_page_header("🏕️", "전국 캠핑장 조회", "고캠핑 공공 API로 전국 3,500여 곳의 캠핑장을 실시간 검색합니다")

# ─────────────────────────────────────────────
#  상수 정의
# ─────────────────────────────────────────────
API_BASE = "http://apis.data.go.kr/B551011/GoCamping"

# 캠핑 유형 매핑 (API의 induty 값 → 화면 표시)
TYPE_MAP = {
    "일반야영장": ("일반캠핑", "⛺"),
    "자동차야영장": ("오토캠핑", "🚗"),
    "글램핑": ("글램핑", "✨"),
    "카라반": ("카라반", "🚐"),
}
TYPE_LABELS = ["전체"] + [v[0] for v in TYPE_MAP.values()]

# 유형별 색상
TYPE_COLORS = {
    "일반캠핑": "#45B7D1", "오토캠핑": "#FF9800",
    "글램핑": "#E91E63", "카라반": "#9C27B0",
}

# 전국 도/광역시 → 시/군/구 목록
REGION_DATA = {
    "서울시": ["강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구",
              "노원구","도봉구","동대문구","동작구","마포구","서대문구","서초구",
              "성동구","성북구","송파구","양천구","영등포구","용산구","은평구",
              "종로구","중구","중랑구"],
    "부산시": ["강서구","금정구","기장군","남구","동구","동래구","부산진구","북구",
              "사상구","사하구","서구","수영구","연제구","영도구","중구","해운대구"],
    "대구시": ["남구","달서구","달성군","동구","북구","서구","수성구","중구"],
    "인천시": ["강화군","계양구","남동구","동구","미추홀구","부평구","서구",
              "연수구","옹진군","중구"],
    "광주시": ["광산구","남구","동구","북구","서구"],
    "대전시": ["대덕구","동구","서구","유성구","중구"],
    "울산시": ["남구","동구","북구","울주군","중구"],
    "세종시": [],
    "경기도": ["가평군","고양시","과천시","광명시","광주시","구리시","군포시","김포시",
              "남양주시","동두천시","부천시","성남시","수원시","시흥시","안산시",
              "안성시","안양시","양주시","양평군","여주시","연천군","오산시","용인시",
              "의왕시","의정부시","이천시","파주시","평택시","포천시","하남시","화성시"],
    "강원도": ["강릉시","고성군","동해시","삼척시","속초시","양구군","양양군","영월군",
              "원주시","인제군","정선군","철원군","춘천시","태백시","평창군",
              "홍천군","화천군","횡성군"],
    "충청북도": ["괴산군","단양군","보은군","영동군","옥천군","음성군","제천시",
               "증평군","진천군","청주시","충주시"],
    "충청남도": ["계룡시","공주시","금산군","논산시","당진시","보령시","부여군",
               "서산시","서천군","아산시","예산군","천안시","청양군","태안군","홍성군"],
    "전라북도": ["고창군","군산시","김제시","남원시","무주군","부안군","순창군",
               "완주군","익산시","임실군","장수군","전주시","정읍시","진안군"],
    "전라남도": ["강진군","고흥군","곡성군","광양시","구례군","나주시","담양군",
               "목포시","무안군","보성군","순천시","신안군","여수시","영광군",
               "영암군","완도군","장성군","장흥군","진도군","함평군","해남군","화순군"],
    "경상북도": ["경산시","경주시","고령군","구미시","군위군","김천시","문경시",
               "봉화군","상주시","성주군","안동시","영덕군","영양군","영주시",
               "영천시","예천군","울릉군","울진군","의성군","청도군","청송군",
               "칠곡군","포항시"],
    "경상남도": ["거제시","거창군","고성군","김해시","남해군","밀양시","사천시",
               "산청군","양산시","의령군","진주시","창녕군","창원시","통영시",
               "하동군","함안군","함양군","합천군"],
    "제주도": ["제주시","서귀포시"],
}
REGION_NAMES = ["전체"] + list(REGION_DATA.keys())

# 지역 이름 → 짧은 이름 매핑 (API 공식 이름과 매칭용)
REGION_SHORT = {
    "서울시": "서울", "부산시": "부산", "대구시": "대구",
    "인천시": "인천", "광주시": "광주", "대전시": "대전",
    "울산시": "울산", "세종시": "세종",
    "경기도": "경기", "강원도": "강원",
    "충청북도": "충북", "충청남도": "충남",
    "전라북도": "전북", "전라남도": "전남",
    "경상북도": "경북", "경상남도": "경남",
    "제주도": "제주",
}

# 예약/지도 플랫폼 색상
PLATFORM_COLORS = {
    "네이버지도": "#03C75A", "카카오맵": "#FEE500", "구글맵": "#4285F4",
    "네이버 예약검색": "#03C75A", "캠핑톡": "#FF8C42",
    "캠핏": "#2DB400", "땡큐캠핑": "#FF6B35", "그래가": "#6C5CE7",
}


# ─────────────────────────────────────────────
#  API 호출 함수
# ─────────────────────────────────────────────
def fetch_campsites(api_key, keyword="", num_rows=100, page=1):
    """고캠핑 API에서 캠핑장 목록 가져오기"""
    if keyword.strip():
        endpoint = f"{API_BASE}/searchList"
    else:
        endpoint = f"{API_BASE}/basedList"

    other_params = {
        "numOfRows": str(num_rows),
        "pageNo": str(page),
        "MobileOS": "ETC",
        "MobileApp": "CampingApp",
        "_type": "json",
    }
    if keyword.strip():
        other_params["keyword"] = keyword.strip()

    # serviceKey를 별도로 붙여서 이중 인코딩 방지
    param_str = urllib.parse.urlencode(other_params, quote_via=urllib.parse.quote)
    url = f"{endpoint}?serviceKey={api_key}&{param_str}"

    # SSL 인증서 검증 문제 방지
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
        raw = resp.read().decode("utf-8")

    # XML 에러 응답 확인
    if raw.strip().startswith("<"):
        if "SERVICE_KEY_IS_NOT_REGISTERED_ERROR" in raw:
            raise Exception("API 키가 등록되지 않았습니다. 키를 다시 확인해주세요.")
        if "LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR" in raw:
            raise Exception("일일 API 호출 한도를 초과했습니다. 내일 다시 시도해주세요.")
        raise Exception(f"API 오류가 발생했습니다.")

    data = json.loads(raw)
    resp_data = data.get("response", {})
    header = resp_data.get("header", {})
    result_code = header.get("resultCode", "")
    if result_code != "0000":
        result_msg = header.get("resultMsg", "알 수 없는 오류")
        raise Exception(f"API 오류: {result_msg}")

    body = resp_data.get("body", {})
    total = body.get("totalCount", 0)
    items_wrap = body.get("items", "")
    if not items_wrap or items_wrap == "":
        return [], total
    items = items_wrap.get("item", [])
    if isinstance(items, dict):
        items = [items]
    return items, total


def map_api_item(item):
    """API 응답 항목을 화면 표시용으로 변환"""
    name = item.get("facltNm", "이름 없음")
    addr = item.get("addr1", "") or ""
    addr2 = item.get("addr2", "") or ""
    full_addr = (addr + " " + addr2).strip()
    induty = item.get("induty", "") or ""
    tel = item.get("tel", "") or ""
    homepage = item.get("homepage", "") or ""
    intro = item.get("lineIntro", "") or item.get("intro", "") or ""
    if len(intro) > 150:
        intro = intro[:150] + "..."
    image_url = item.get("firstImageUrl", "") or ""
    do_nm = item.get("doNm", "") or ""
    sigungu = item.get("sigunguNm", "") or ""

    # 부대시설
    sbrs = item.get("sbrsCl", "") or ""
    sbrs_etc = item.get("sbrsEtc", "") or ""
    features = [s.strip() for s in sbrs.split(",") if s.strip()]
    if sbrs_etc:
        features += [s.strip() for s in sbrs_etc.split(",") if s.strip()]
    if not features:
        features = ["정보 없음"]

    # 유형 결정
    type_name = "일반캠핑"
    type_icon = "⛺"
    for key, (tname, ticon) in TYPE_MAP.items():
        if key in induty:
            type_name = tname
            type_icon = ticon
            break

    # URL 생성
    kw = urllib.parse.quote(name)
    map_urls = {
        "네이버지도": f"https://map.naver.com/p/search/{kw}",
        "카카오맵": f"https://map.kakao.com/link/search/{kw}",
        "구글맵": f"https://www.google.com/maps/search/{kw}",
    }
    reserve_urls = {
        "네이버 예약검색": f"https://search.naver.com/search.naver?query={kw}+예약",
        "캠핑톡": f"https://search.naver.com/search.naver?query={kw}+캠핑톡+예약",
        "캠핏": f"https://search.naver.com/search.naver?query={kw}+캠핏+예약",
        "땡큐캠핑": f"https://search.naver.com/search.naver?query={kw}+땡큐캠핑+예약",
        "그래가": f"https://search.naver.com/search.naver?query={kw}+그래가+예약",
    }

    return {
        "name": name,
        "type": type_name,
        "type_icon": type_icon,
        "location": full_addr,
        "do_nm": do_nm,
        "sigungu_nm": sigungu,
        "features": features[:6],
        "tel": tel,
        "homepage": homepage,
        "description": intro or "상세 정보는 각 플랫폼에서 확인하세요.",
        "image_url": image_url,
        "type_color": TYPE_COLORS.get(type_name, "#607D8B"),
        "map_urls": map_urls,
        "reserve_urls": reserve_urls,
    }


# ─────────────────────────────────────────────
#  사이드바: API 키 & 필터
# ─────────────────────────────────────────────
st.sidebar.markdown("### 🔑 API 키 설정")
st.sidebar.markdown(
    "한국관광공사 고캠핑 API 키가 필요합니다.\n\n"
    "[공공데이터포털](https://www.data.go.kr)에서 무료로 발급받을 수 있습니다.",
    unsafe_allow_html=True
)

# API 키를 session_state에 저장 (파일에서 먼저 불러옴)
if "camping_api_key" not in st.session_state:
    st.session_state.camping_api_key = get_key("camping_api_key")

api_key_input = st.sidebar.text_input(
    "API 키 입력", value=st.session_state.camping_api_key,
    type="password", placeholder="발급받은 API 키를 붙여넣으세요"
)
if api_key_input:
    st.session_state.camping_api_key = api_key_input

# API 키 저장 버튼
if st.sidebar.button("💾 API 키 저장", use_container_width=True, help="입력한 키를 파일에 저장하면 다음에 자동으로 불러옵니다"):
    if st.session_state.camping_api_key:
        set_key("camping_api_key", st.session_state.camping_api_key)
        st.sidebar.success("✅ 저장되었습니다!")
    else:
        st.sidebar.warning("API 키를 먼저 입력해주세요.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 검색 조건")

# 키워드 검색
search_keyword = st.sidebar.text_input("🔎 키워드 검색", placeholder="캠핑장 이름으로 검색")

# 캠핑 유형 필터
filter_type = st.sidebar.selectbox("⛺ 캠핑 유형", TYPE_LABELS)

# 지역 필터 (도/광역시)
filter_region = st.sidebar.selectbox("📍 도/광역시", REGION_NAMES)

# 시/군/구 필터 (선택한 도에 따라 변경)
if filter_region != "전체" and filter_region in REGION_DATA:
    sigungu_list = REGION_DATA[filter_region]
    if sigungu_list:
        filter_sigungu = st.sidebar.selectbox(
            "🏘️ 시/군/구", ["전체"] + sigungu_list
        )
    else:
        filter_sigungu = "전체"
        st.sidebar.info(f"{filter_region}는 시/군/구 구분이 없습니다")
else:
    filter_sigungu = "전체"

st.sidebar.markdown("---")
st.sidebar.markdown("#### ℹ️ 안내")
st.sidebar.markdown("- **데이터**: 한국관광공사 고캠핑 API")
st.sidebar.markdown("- **전국 약 3,500여 곳** 캠핑장 검색")
st.sidebar.markdown("- 지역 선택 시 전체 데이터를 불러와서\n  몇 초 걸릴 수 있습니다")


# ─────────────────────────────────────────────
#  검색 실행
# ─────────────────────────────────────────────
if not st.session_state.camping_api_key:
    st.info("👈 왼쪽 사이드바에서 API 키를 먼저 입력해주세요.\n\n"
            "**API 키 발급 방법:**\n"
            "1. [공공데이터포털](https://www.data.go.kr) 회원가입 (무료)\n"
            "2. '고캠핑' 검색 → '고캠핑정보 조회서비스' 활용 신청\n"
            "3. 마이페이지에서 일반 인증키(Encoding) 복사\n"
            "4. 왼쪽에 붙여넣기")
    st.stop()

# 검색 버튼
search_clicked = st.button("🔍 캠핑장 검색", type="primary", use_container_width=True)

if search_clicked or st.session_state.get("camping_results"):
    if search_clicked:
        # 새 검색 실행
        try:
            with st.spinner("⏳ 캠핑장 검색 중..." if filter_region == "전체"
                           else "⏳ 전국 캠핑장 불러오는 중... (몇 초 걸림)"):
                # 지역 필터가 있으면 전체 데이터를 가져와서 필터링
                if filter_region != "전체":
                    rows = 5000
                else:
                    rows = 100

                items, total = fetch_campsites(
                    st.session_state.camping_api_key,
                    keyword=search_keyword,
                    num_rows=rows, page=1
                )

            # API 결과 변환
            all_camps = [map_api_item(item) for item in items]

            # 클라이언트 필터링 (유형·지역·시군구)
            region_short = REGION_SHORT.get(filter_region, "")
            filtered = []
            for c in all_camps:
                # 유형 필터
                if filter_type != "전체" and c["type"] != filter_type:
                    continue
                # 도/광역시 필터
                if filter_region != "전체":
                    do_nm = c.get("do_nm", "")
                    addr = c.get("location", "")
                    if (filter_region not in do_nm and
                        region_short not in do_nm and
                        filter_region not in addr and
                        region_short not in addr):
                        continue
                # 시/군/구 필터
                if filter_sigungu != "전체":
                    sg_nm = c.get("sigungu_nm", "")
                    addr = c.get("location", "")
                    if filter_sigungu not in sg_nm and filter_sigungu not in addr:
                        continue
                filtered.append(c)

            st.session_state.camping_results = filtered
            st.session_state.camping_total = total

        except Exception as e:
            st.error(f"❌ 검색 중 오류가 발생했습니다: {e}")
            st.stop()

    # 결과 표시
    results = st.session_state.get("camping_results", [])
    total = st.session_state.get("camping_total", 0)

    # 검색 결과 요약
    region_text = f"{filter_region}" if filter_region != "전체" else "전국"
    sigungu_text = f" {filter_sigungu}" if filter_sigungu != "전체" else ""
    st.markdown(
        f"**📊 {region_text}{sigungu_text}** — "
        f"전체 {total:,}개 중 **{len(results)}개** 표시"
    )

    if not results:
        st.warning("😢 검색 결과가 없습니다. 다른 조건으로 검색해보세요.")
    else:
        # 캠핑장 카드 표시
        for camp in results:
            color = camp["type_color"]
            features_text = " · ".join(camp["features"])

            # 카드 HTML
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 20px; margin: 12px 0;
                        border-left: 5px solid {color}; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div>
                        <span style="font-size: 1.3em; font-weight: bold;">{camp['type_icon']} {camp['name']}</span>
                        <span style="background: {color}20; color: {color}; padding: 2px 8px;
                              border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-left: 8px;">{camp['type']}</span>
                    </div>
                </div>
                <div style="color: #636E72; font-size: 0.9em; margin-bottom: 6px;">
                    📍 {camp['location']}
                    {f"&nbsp;&nbsp; 📞 {camp['tel']}" if camp['tel'] else ""}
                </div>
                <div style="color: {color}; font-size: 0.85em; margin-bottom: 6px;">
                    {features_text}
                </div>
                <div style="color: #7f8c8d; font-size: 0.85em;">
                    💡 {camp['description']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 지도 / 예약 버튼
            col_maps, col_reserves = st.columns(2)

            with col_maps:
                map_cols = st.columns(len(camp["map_urls"]))
                for i, (pname, purl) in enumerate(camp["map_urls"].items()):
                    with map_cols[i]:
                        st.link_button(f"🗺️ {pname}", purl, use_container_width=True)

            with col_reserves:
                # 예약 플랫폼 중 처음 3개만 버튼으로 표시
                reserve_items = list(camp["reserve_urls"].items())
                res_cols = st.columns(3)
                for i in range(min(3, len(reserve_items))):
                    pname, purl = reserve_items[i]
                    with res_cols[i]:
                        st.link_button(f"📅 {pname}", purl, use_container_width=True)

            # 나머지 예약 플랫폼은 확장 영역에
            reserve_items = list(camp["reserve_urls"].items())
            if len(reserve_items) > 3:
                with st.expander("🔗 더 많은 예약 플랫폼"):
                    extra_cols = st.columns(len(reserve_items) - 3)
                    for i, (pname, purl) in enumerate(reserve_items[3:]):
                        with extra_cols[i]:
                            st.link_button(f"📅 {pname}", purl, use_container_width=True)

            st.markdown("")  # 카드 간 여백
