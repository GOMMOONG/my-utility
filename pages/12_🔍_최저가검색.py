import streamlit as st
import re
import requests
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="최저가검색 - 마이 유틸리티", page_icon="🔍", layout="centered")
apply_common_style()
check_password()
show_page_header("🔍", "인터넷 최저가 검색", "네이버 쇼핑에서 물건을 검색하고 여러 쇼핑몰의 가격을 비교합니다")

SEARCH_URL = "https://openapi.naver.com/v1/search/shop.json"

# ── 원본 로직 함수들 ──
def clean_title(title):
    text = re.sub(r"</?b>", "", title)
    return text.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")

def search_products(query, client_id, client_secret, sort="asc", display=50, start=1):
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    res = requests.get(SEARCH_URL, params={"query": query, "display": display, "sort": sort, "start": start},
                       headers=headers, timeout=5)
    if res.status_code == 401:
        raise PermissionError("API 키가 올바르지 않습니다")
    res.raise_for_status()

    items = []
    for item in res.json().get("items", []):
        try: price = int(item.get("lprice", "0"))
        except ValueError: price = 0
        items.append({
            "title": clean_title(item.get("title", "")),
            "price": price,
            "mall": item.get("mallName", ""),
            "link": item.get("link", ""),
            "brand": item.get("brand", "") or item.get("maker", ""),
        })
    return items

# ── API 키 관리 ──
# Streamlit Secrets에 naver_client_id / naver_client_secret이 있으면 사용
try:
    default_id = st.secrets.get("naver_client_id", "")
    default_secret = st.secrets.get("naver_client_secret", "")
except Exception:
    default_id, default_secret = "", ""

if "naver_id" not in st.session_state:
    st.session_state.naver_id = default_id
if "naver_secret" not in st.session_state:
    st.session_state.naver_secret = default_secret

# API 키 설정 영역
with st.expander("⚙️ 네이버 API 키 설정 (처음 한 번만 필요)"):
    st.markdown("""
    1. [developers.naver.com](https://developers.naver.com) 접속 후 네이버 계정으로 로그인
    2. 상단 메뉴에서 **Application > 애플리케이션 등록** 클릭
    3. 애플리케이션 이름을 자유롭게 입력하고, 사용 API에서 **'검색'** 선택
    4. 등록 후 발급된 **Client ID**와 **Client Secret**을 아래에 입력하세요 (무료)
    """)
    naver_id = st.text_input("Client ID", value=st.session_state.naver_id, key="input_naver_id")
    naver_secret = st.text_input("Client Secret", value=st.session_state.naver_secret, type="password", key="input_naver_secret")
    if st.button("저장"):
        st.session_state.naver_id = naver_id
        st.session_state.naver_secret = naver_secret
        st.success("API 키가 저장되었습니다!")

# ── 검색 영역 ──
col_q, col_sort = st.columns([3, 1])
with col_q:
    query = st.text_input("검색어", placeholder="검색할 물건 이름을 입력하세요", label_visibility="collapsed")
with col_sort:
    sort_option = st.selectbox("정렬", ["최저가순", "최고가순"], label_visibility="collapsed")

sort_map = {"최저가순": "asc", "최고가순": "dsc"}

# 가격 범위 필터
col_min, col_dash, col_max, col_apply = st.columns([2, 0.3, 2, 1])
with col_min:
    min_price = st.number_input("최소 가격", min_value=0, value=0, step=1000, format="%d", label_visibility="collapsed")
with col_dash:
    st.markdown("<div style='text-align:center; padding-top:8px;'>~</div>", unsafe_allow_html=True)
with col_max:
    max_price = st.number_input("최대 가격 (0=제한없음)", min_value=0, value=0, step=1000, format="%d", label_visibility="collapsed")
with col_apply:
    search_clicked = st.button("🔍 검색", use_container_width=True, type="primary")

if search_clicked:
    if not query.strip():
        st.warning("검색어를 입력해주세요.")
    elif not st.session_state.naver_id or not st.session_state.naver_secret:
        st.warning("먼저 네이버 API 키를 설정해주세요. (위쪽 ⚙️ 버튼 클릭)")
    else:
        try:
            with st.spinner("검색하는 중입니다..."):
                items = search_products(query, st.session_state.naver_id, st.session_state.naver_secret,
                                       sort=sort_map[sort_option])

            # 가격 필터 적용
            if min_price > 0:
                items = [it for it in items if it["price"] >= min_price]
            if max_price > 0:
                items = [it for it in items if it["price"] <= max_price]

            if not items:
                st.info("검색 결과가 없습니다.")
            else:
                st.success(f"{len(items)}개 상품을 찾았습니다. ({sort_option})")
                st.caption("※ 상품 링크를 클릭하면 해당 쇼핑몰 페이지가 열립니다.")

                for item in items:
                    col_info, col_price, col_link = st.columns([4, 1.5, 1])
                    with col_info:
                        st.markdown(f"**{item['title']}**")
                        mall_text = item['mall']
                        if item['brand']:
                            mall_text += f" · {item['brand']}"
                        st.caption(mall_text)
                    with col_price:
                        st.markdown(f"### {item['price']:,}원")
                    with col_link:
                        st.link_button("보러가기", item["link"], use_container_width=True)
                    st.divider()

        except PermissionError:
            st.error("API 키가 올바르지 않습니다. ⚙️ 설정에서 다시 입력해주세요.")
        except requests.exceptions.RequestException:
            st.error("인터넷 연결을 확인해주세요.")
        except Exception as e:
            st.error(f"검색 중 오류가 발생했습니다: {e}")
