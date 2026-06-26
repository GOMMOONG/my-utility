# 한국 주식 시장 일일 리포트 — 네이버증권 데이터 자동 수집 (API 불필요)

import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

# ── 페이지 설정 ──
st.set_page_config(
    page_title="주식 리포트 - 마이 유틸리티",
    page_icon="📊",
    layout="wide",
)
apply_common_style()
check_password()
show_page_header("📊", "한국 주식 일일 리포트", "KOSPI·KOSDAQ 지수와 주요 종목 동향을 자동으로 보여줍니다")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 시가총액 상위 주요 종목 목록
TOP_STOCKS = [
    ("삼성전자",       "005930"),
    ("SK하이닉스",     "000660"),
    ("LG에너지솔루션", "373220"),
    ("삼성바이오로직스","207940"),
    ("현대차",         "005380"),
    ("기아",           "000270"),
    ("삼성SDI",        "006400"),
    ("POSCO홀딩스",    "005490"),
    ("KB금융",         "105560"),
    ("NAVER",          "035420"),
]


# ══════════════════════════════════════════════════════════════
# 데이터 수집 함수 (30분 캐시 — 같은 페이지 내에서 새로고침해도 빠름)
# ══════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_index(code):
    """KOSPI 또는 KOSDAQ 지수를 네이버증권 API에서 가져오는 함수"""
    try:
        url = f"https://polling.finance.naver.com/api/realtime/domestic/index/{code}"
        d = requests.get(url, headers=HEADERS, timeout=8).json().get("datas", [{}])[0]
        rf = str(d.get("compareToPreviousPrice", {}).get("code", "3"))
        close = d.get("closePrice", "-")
        change = d.get("compareToPreviousClosePrice", "0")
        rate = d.get("fluctuationsRatio", "0")
        volume = d.get("accumulatedTradingValue", "")
        return {"code": code, "close": close, "change": change, "rate": rate, "rf": rf, "volume": volume}
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_stock(code, name):
    """개별 종목 현재가·등락 정보를 가져오는 함수"""
    try:
        url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
        d = requests.get(url, headers=HEADERS, timeout=5).json().get("datas", [{}])[0]
        rf = str(d.get("compareToPreviousPrice", {}).get("code", "3"))
        return {
            "name": name, "code": code,
            "price": d.get("closePrice", "-"),
            "change": d.get("compareToPreviousClosePrice", "0"),
            "rate": d.get("fluctuationsRatio", "0"),
            "rf": rf,
        }
    except Exception:
        return {"name": name, "code": code, "price": "-", "change": "0", "rate": "0", "rf": "3"}


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_economy_news():
    """네이버 경제 뉴스 헤드라인을 가져오는 함수"""
    try:
        url = "https://news.naver.com/section/101"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        articles = []
        for div in soup.select("div.sa_text")[:6]:
            a = div.select_one("a.sa_text_title")
            strong = div.select_one("strong.sa_text_strong")
            press = div.select_one("div.sa_text_press")
            if a and strong:
                articles.append({
                    "title": strong.get_text(strip=True),
                    "link": a.get("href", "#"),
                    "press": press.get_text(strip=True) if press else "",
                })
        return articles
    except Exception:
        return []


# ── 등락 방향 기호 반환 ──
def arrow(rf):
    if rf in ("1", "2"):
        return "▲", "red"
    if rf in ("4", "5"):
        return "▼", "blue"
    return "―", "#888"


def signed_rate(rf, rate):
    """등락률에 +/- 부호를 붙여서 반환하는 함수"""
    rate = rate.replace("-", "").replace("+", "")
    if rf in ("1", "2"):
        return f"+{rate}%"
    if rf in ("4", "5"):
        return f"-{rate}%"
    return f"0%"


def to_float_rate(rf, rate):
    """정렬용으로 등락률을 숫자로 변환하는 함수"""
    try:
        v = float(rate.replace(",", "").replace("+", "").replace("-", ""))
        return v if rf in ("1", "2") else (-v if rf in ("4", "5") else 0.0)
    except Exception:
        return 0.0


# ── 규칙 기반 자동 총평 생성 ──
def make_summary(kospi, kosdaq, stocks):
    """지수와 종목 데이터를 바탕으로 자동으로 총평 문장을 만드는 함수"""
    lines = []

    def desc(idx):
        if not idx:
            return ""
        sym, _ = arrow(idx["rf"])
        r = signed_rate(idx["rf"], idx["rate"])
        mood = "강세" if idx["rf"] in ("1","2") else ("약세" if idx["rf"] in ("4","5") else "보합")
        return f"{idx['code']} {idx['close']}pt ({r}) {mood}"

    if kospi:
        lines.append(f"오늘 {desc(kospi)}을 보였습니다.")
    if kosdaq:
        lines.append(f"코스닥은 {desc(kosdaq)}으로 마감했습니다.")

    # 상승/하락 종목 수
    up_cnt   = sum(1 for s in stocks if s["rf"] in ("1","2"))
    down_cnt = sum(1 for s in stocks if s["rf"] in ("4","5"))
    lines.append(f"주요 10개 종목 중 {up_cnt}개 상승, {down_cnt}개 하락했습니다.")

    # 가장 많이 오른 종목, 가장 많이 내린 종목
    if stocks:
        best  = max(stocks, key=lambda s: to_float_rate(s["rf"], s["rate"]))
        worst = min(stocks, key=lambda s: to_float_rate(s["rf"], s["rate"]))
        if best["rf"] in ("1","2"):
            lines.append(f"가장 큰 상승폭을 기록한 종목은 {best['name']} ({signed_rate(best['rf'], best['rate'])})입니다.")
        if worst["rf"] in ("4","5"):
            lines.append(f"가장 큰 하락폭은 {worst['name']} ({signed_rate(worst['rf'], worst['rate'])})이었습니다.")

    return " ".join(lines) if lines else "데이터를 불러오는 중입니다."


# ══════════════════════════════════════════════════════════════
# 메인 화면
# ══════════════════════════════════════════════════════════════

# 상단: 기준 시각 + 새로고침 버튼
col_time, col_btn = st.columns([5, 1])
with col_time:
    st.caption(f"📅 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')} 기준  |  30분마다 자동 갱신")
with col_btn:
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# ── 데이터 수집 ──
with st.spinner("📡 시장 데이터를 불러오는 중..."):
    kospi  = fetch_index("KOSPI")
    kosdaq = fetch_index("KOSDAQ")
    stocks = [fetch_stock(code, name) for name, code in TOP_STOCKS]
    news   = fetch_economy_news()

# ══ 1. 지수 요약 카드 ══
st.subheader("1. 시장 지수 요약")
col_k, col_q = st.columns(2)

def index_card(col, idx, label):
    with col:
        if idx:
            sym, color = arrow(idx["rf"])
            r = signed_rate(idx["rf"], idx["rate"])
            chg_sign = "+" if idx["rf"] in ("1","2") else ("-" if idx["rf"] in ("4","5") else "")
            st.markdown(f"""
            <div style="background:white; border-radius:12px; padding:20px 24px;
                        box-shadow:0 2px 8px rgba(0,0,0,0.08); border-left:5px solid {color};">
                <div style="font-size:1.1em; color:#636E72; margin-bottom:4px;">{label}</div>
                <div style="font-size:2em; font-weight:700;">{idx['close']}<span style="font-size:0.5em; color:#aaa;">pt</span></div>
                <div style="font-size:1.2em; color:{color}; font-weight:600;">
                    {sym} {chg_sign}{idx['change']}pt &nbsp; <span style="font-size:0.85em;">({r})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning(f"{label} 데이터를 불러오지 못했습니다.")

index_card(col_k, kospi,  "🔵 KOSPI (코스피)")
index_card(col_q, kosdaq, "🟢 KOSDAQ (코스닥)")

st.markdown("")

# ══ 2. 주요 종목 현황 ══
st.subheader("2. 시가총액 상위 10개 종목")

# 테이블 헤더
header = """
<div style="display:grid; grid-template-columns:2fr 2fr 2fr 2fr;
            background:#F0F2F6; border-radius:8px 8px 0 0;
            padding:10px 16px; font-weight:600; color:#636E72; font-size:0.9em;">
    <div>종목명</div><div style="text-align:right;">현재가</div>
    <div style="text-align:right;">등락</div><div style="text-align:right;">등락률</div>
</div>
"""
st.markdown(header, unsafe_allow_html=True)

for i, s in enumerate(stocks):
    sym, color = arrow(s["rf"])
    r = signed_rate(s["rf"], s["rate"])
    chg_sign = "+" if s["rf"] in ("1","2") else ("-" if s["rf"] in ("4","5") else "")
    bg = "#FFFFFF" if i % 2 == 0 else "#F9FAFB"
    st.markdown(f"""
    <div style="display:grid; grid-template-columns:2fr 2fr 2fr 2fr;
                background:{bg}; padding:10px 16px; border-bottom:1px solid #F0F2F6;
                {'border-radius: 0 0 8px 8px;' if i == len(stocks)-1 else ''}">
        <div><strong>{s['name']}</strong> <span style="color:#aaa; font-size:0.8em;">{s['code']}</span></div>
        <div style="text-align:right; font-weight:600;">{s['price']}원</div>
        <div style="text-align:right; color:{color};">{sym} {chg_sign}{s['change']}</div>
        <div style="text-align:right; color:{color}; font-weight:600;">{r}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

# ══ 3. 상승 / 하락 TOP 3 ══
st.subheader("3. 상승 · 하락 상위 종목")
sorted_stocks = sorted(stocks, key=lambda s: to_float_rate(s["rf"], s["rate"]), reverse=True)
col_up, col_dn = st.columns(2)

with col_up:
    st.markdown("**📈 상승 상위**")
    top_up = [s for s in sorted_stocks if s["rf"] in ("1","2")][:3]
    if top_up:
        for s in top_up:
            r = signed_rate(s["rf"], s["rate"])
            st.markdown(f"""
            <div style="background:#FFF5F5; border-left:4px solid red; border-radius:6px;
                        padding:10px 14px; margin-bottom:8px;">
                <strong>{s['name']}</strong> &nbsp; <span style="color:red; font-weight:700;">{r}</span>
                <span style="color:#aaa; font-size:0.85em; margin-left:8px;">{s['price']}원</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("상승 종목 없음")

with col_dn:
    st.markdown("**📉 하락 상위**")
    top_dn = [s for s in sorted_stocks if s["rf"] in ("4","5")][-3:][::-1]
    if top_dn:
        for s in top_dn:
            r = signed_rate(s["rf"], s["rate"])
            st.markdown(f"""
            <div style="background:#F0F4FF; border-left:4px solid #3498DB; border-radius:6px;
                        padding:10px 14px; margin-bottom:8px;">
                <strong>{s['name']}</strong> &nbsp; <span style="color:#3498DB; font-weight:700;">{r}</span>
                <span style="color:#aaa; font-size:0.85em; margin-left:8px;">{s['price']}원</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("하락 종목 없음")

st.markdown("")

# ══ 4. 자동 총평 ══
st.subheader("4. 오늘의 총평")
summary = make_summary(kospi, kosdaq, stocks)
st.markdown(f"""
<div style="background:#F8F9FA; border-left:4px solid #6C5CE7; border-radius:8px;
            padding:16px 20px; font-size:1.05em; line-height:1.8; color:#2D3436;">
    {summary}
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ══ 5. 주요 경제 뉴스 ══
st.subheader("5. 주요 경제 뉴스")
if news:
    for article in news:
        st.markdown(f"""
        <div style="background:white; padding:12px 16px; border-radius:8px;
                    margin-bottom:8px; border-left:4px solid #6C5CE7;
                    box-shadow:0 1px 3px rgba(0,0,0,0.06);">
            <a href="{article['link']}" target="_blank"
               style="text-decoration:none; color:#2D3436; font-weight:600;">
                {article['title']}
            </a>
            <div style="color:#B2BEC3; font-size:0.8em; margin-top:4px;">{article['press']}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("경제 뉴스를 불러오지 못했습니다. 인터넷 연결을 확인해주세요.")
