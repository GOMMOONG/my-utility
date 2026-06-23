# 오늘의 주요 뉴스를 경제·사회·스포츠·세계 탭으로 보여주는 페이지

import streamlit as st
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

# ── 페이지 기본 설정 ──
st.set_page_config(
    page_title="뉴스요약 - 마이 유틸리티",
    page_icon="📰",
    layout="wide",
)
apply_common_style()
check_password()
show_page_header("📰", "오늘의 뉴스", "국내·세계 주요 뉴스를 경제 / 사회 / 스포츠 / 세계로 나눠서 보여줍니다")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 네이버 뉴스 섹션 번호 (경제·사회·세계)
NAVER_SECTIONS = {
    "경제": 101,
    "사회": 102,
    "세계": 104,
}

# 구글 뉴스 RSS - 한국판 스포츠 (네이버 스포츠는 자바스크립트로 동작해서 직접 가져올 수 없음)
GOOGLE_SPORTS_RSS = (
    "https://news.google.com/rss/topics/"
    "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtdHZHZ0pMVWlnQVAB"
    "?hl=ko&gl=KR&ceid=KR:ko"
)


# ── 뉴스 가져오기 함수들 ──

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_naver_news(section_id, count=10):
    """네이버 뉴스 섹션 페이지에서 헤드라인을 가져오는 함수"""
    url = f"https://news.naver.com/section/{section_id}"
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    articles = []
    # 각 뉴스 기사의 텍스트 영역(div.sa_text)에서 제목·요약·언론사를 추출
    for text_div in soup.select("div.sa_text")[:count]:
        title_link = text_div.select_one("a.sa_text_title")
        if not title_link:
            continue

        title_strong = title_link.select_one("strong.sa_text_strong")
        lede = text_div.select_one("div.sa_text_lede")
        press = text_div.select_one("div.sa_text_press")

        title = title_strong.get_text(strip=True) if title_strong else ""
        link = title_link.get("href", "")
        summary = lede.get_text(strip=True) if lede else ""
        press_name = press.get_text(strip=True) if press else ""

        if title:
            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
                "press": press_name,
            })

    return articles


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_sports_news(count=10):
    """구글 뉴스 RSS에서 스포츠 뉴스를 가져오는 함수"""
    res = requests.get(GOOGLE_SPORTS_RSS, headers=HEADERS, timeout=10)
    root = ET.fromstring(res.content)

    articles = []
    for item in root.findall(".//item")[:count]:
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        source = item.findtext("source", "")

        # 구글 뉴스 제목 형식: "기사 제목 - 언론사" → 언론사 부분 분리
        if " - " in title and source:
            title = title.rsplit(" - ", 1)[0]

        if title:
            articles.append({
                "title": title,
                "link": link,
                "summary": "",
                "press": source,
            })

    return articles


# ── 화면에 뉴스 목록 표시 ──

def display_articles(articles):
    """뉴스 기사 목록을 카드 형태로 화면에 보여주는 함수"""
    if not articles:
        st.warning("뉴스를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
        return

    for article in articles:
        summary_html = ""
        if article["summary"]:
            summary_html = (
                f'<div style="color: #636E72; font-size: 0.9em; margin-top: 6px;">'
                f'{article["summary"]}</div>'
            )

        st.markdown(f"""
        <div style="background: white; padding: 16px; border-radius: 10px;
                    margin-bottom: 10px; border-left: 4px solid #6C5CE7;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
            <a href="{article['link']}" target="_blank"
               style="text-decoration: none; color: #2D3436;">
                <strong style="font-size: 1.05em;">{article['title']}</strong>
            </a>
            {summary_html}
            <div style="color: #B2BEC3; font-size: 0.8em; margin-top: 6px;">
                {article['press']}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── 상단: 업데이트 시간 + 새로고침 버튼 ──

col_time, col_btn = st.columns([5, 1])
with col_time:
    now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    st.caption(f"📅 {now} 기준")
with col_btn:
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()

# ── 탭별 뉴스 표시 ──

tab_economy, tab_society, tab_sports, tab_world = st.tabs(
    ["💰 경제", "🏘️ 사회", "⚽ 스포츠", "🌍 세계"]
)

with tab_economy:
    try:
        with st.spinner("경제 뉴스를 불러오는 중..."):
            articles = fetch_naver_news(NAVER_SECTIONS["경제"])
        display_articles(articles)
    except Exception:
        st.error("⚠ 경제 뉴스를 불러오지 못했습니다. 인터넷 연결을 확인해주세요.")

with tab_society:
    try:
        with st.spinner("사회 뉴스를 불러오는 중..."):
            articles = fetch_naver_news(NAVER_SECTIONS["사회"])
        display_articles(articles)
    except Exception:
        st.error("⚠ 사회 뉴스를 불러오지 못했습니다. 인터넷 연결을 확인해주세요.")

with tab_sports:
    try:
        with st.spinner("스포츠 뉴스를 불러오는 중..."):
            articles = fetch_sports_news()
        display_articles(articles)
    except Exception:
        st.error("⚠ 스포츠 뉴스를 불러오지 못했습니다. 인터넷 연결을 확인해주세요.")

with tab_world:
    try:
        with st.spinner("세계 뉴스를 불러오는 중..."):
            articles = fetch_naver_news(NAVER_SECTIONS["세계"])
        display_articles(articles)
    except Exception:
        st.error("⚠ 세계 뉴스를 불러오지 못했습니다. 인터넷 연결을 확인해주세요.")
