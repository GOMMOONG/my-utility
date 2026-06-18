import streamlit as st
import re
import requests
from bs4 import BeautifulSoup
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="투자자동향 - 마이 유틸리티", page_icon="📈", layout="wide")
apply_common_style()
check_password()
show_page_header("📈", "투자자별 매매동향", "네이버증권 기반으로 기관/외국인/개인 매매동향을 조회합니다")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# 업종별 대표 종목
SECTOR_STOCKS = {
    "반도체": [("삼성전자", "005930"), ("SK하이닉스", "000660")],
    "자동차": [("현대차", "005380"), ("기아", "000270")],
    "2차전지": [("LG에너지솔루션", "373220"), ("삼성SDI", "006400")],
    "바이오": [("삼성바이오로직스", "207940"), ("셀트리온", "068270")],
    "금융": [("KB금융", "105560"), ("신한지주", "055550")],
    "인터넷/플랫폼": [("NAVER", "035420"), ("카카오", "035720")],
    "철강/화학": [("POSCO홀딩스", "005490"), ("LG화학", "051910")],
    "조선/방산": [("HD현대중공업", "329180"), ("한화에어로스페이스", "012450")],
}

MARKET_INDEXES = [("KOSPI", "코스피"), ("KOSDAQ", "코스닥")]

# ── 데이터 가져오기 함수들 (원본 로직) ──
def to_int(text):
    text = text.replace(",", "").replace("+", "")
    try: return int(text)
    except ValueError: return 0

def format_num(n):
    sign = "+" if n > 0 else ""
    return f"{sign}{n:,}"

def search_stock_code(query):
    query = query.strip()
    if re.fullmatch(r"\d{6}", query):
        return [(query, query)]
    res = requests.get("https://m.stock.naver.com/front-api/search/autoComplete",
                       params={"query": query, "target": "stock"}, headers=HEADERS, timeout=5)
    items = res.json().get("result", {}).get("items", [])
    return [(item["name"], item["code"]) for item in items if item.get("category") == "stock"]

def get_current_price(code):
    res = requests.get(f"https://polling.finance.naver.com/api/realtime/domestic/stock/{code}",
                       headers=HEADERS, timeout=5)
    datas = res.json().get("datas", [])
    if not datas: raise ValueError("현재가 정보를 찾을 수 없습니다")
    d = datas[0]
    return {
        "name": d.get("stockName", ""), "price": d.get("closePrice", "0"),
        "change": d.get("compareToPreviousClosePrice", "0"),
        "rate": d.get("fluctuationsRatio", "0"),
        "rf": str(d.get("compareToPreviousPrice", {}).get("code", "3")),
    }

def get_investor_trend(code, days=10):
    res = requests.get("https://finance.naver.com/item/frgn.naver",
                       params={"code": code}, headers=HEADERS, timeout=5)
    res.encoding = "euc-kr"
    soup = BeautifulSoup(res.text, "html.parser")
    best_rows = []
    for table in soup.select("table.type2"):
        header_text = table.get_text()
        if "기관" not in header_text or "외국인" not in header_text: continue
        rows = []
        for tr in table.select("tr"):
            tds = tr.find_all("td")
            if len(tds) < 9: continue
            date = tds[0].get_text(strip=True)
            close = tds[1].get_text(strip=True)
            if not date or not close: continue
            rows.append({"date": date, "close": close, "updown": tds[2].get_text(strip=True),
                         "inst": tds[5].get_text(strip=True), "frgn": tds[6].get_text(strip=True)})
        if len(rows) > len(best_rows): best_rows = rows
    if not best_rows: raise ValueError("매매동향 표를 찾을 수 없습니다")
    return best_rows[:days]

def get_market_investor_trend(index_code):
    res = requests.get("https://finance.naver.com/sise/sise_index.naver",
                       params={"code": index_code}, headers=HEADERS, timeout=5)
    res.encoding = "euc-kr"
    soup = BeautifulSoup(res.text, "html.parser")
    dl = soup.select_one("dl.lst_kos_info")
    if dl is None: raise ValueError("투자자별 매매동향 정보를 찾을 수 없습니다")
    dds = dl.select("dd.dd")[:3]
    keys = ("indiv", "frgn", "inst")
    result = {}
    for key, dd in zip(keys, dds):
        span = dd.find("span")
        text = span.get_text(strip=True) if span else "0"
        result[key] = to_int(text.replace("억", ""))
    return result

def color_value(val):
    """양수면 빨간색, 음수면 파란색으로 HTML 반환"""
    if val > 0: return f'<span style="color: #E74C3C; font-weight: bold;">{format_num(val)}</span>'
    elif val < 0: return f'<span style="color: #3498DB; font-weight: bold;">{format_num(val)}</span>'
    return f'<span style="color: #636E72;">0</span>'

# ── 탭 구성 ──
tab_market, tab_search, tab_sector = st.tabs(["🏛 시장 투자 현황", "🔍 종목 검색", "🏭 업종별 한눈에 보기"])

# ── 탭 1: 시장 투자 현황 ──
with tab_market:
    st.caption("코스피·코스닥 시장 전체의 개인/외국인/기관 순매매 현황 (단위: 억원)")
    st.caption("※ 빨간색 = 순매수(사들임), 파란색 = 순매도(팔아치움)")

    if st.button("🔄 새로고침", key="market_refresh"):
        st.cache_data.clear()

    @st.cache_data(ttl=300, show_spinner="시장 데이터를 불러오는 중...")
    def load_market_data():
        results = {}
        for code, label in MARKET_INDEXES:
            try:
                results[code] = get_market_investor_trend(code)
            except Exception:
                results[code] = {"indiv": 0, "frgn": 0, "inst": 0}
        return results

    try:
        market_data = load_market_data()

        # 시장별 현황 표
        header_html = "<tr><th style='padding:12px; background:#f8f9fa;'>시장</th>"
        header_html += "<th style='padding:12px; background:#f8f9fa;'>개인 순매매</th>"
        header_html += "<th style='padding:12px; background:#f8f9fa;'>외국인 순매매</th>"
        header_html += "<th style='padding:12px; background:#f8f9fa;'>기관 순매매</th></tr>"

        rows_html = ""
        for code, label in MARKET_INDEXES:
            d = market_data.get(code, {})
            rows_html += f"<tr><td style='padding:10px; font-weight:bold;'>{label}</td>"
            rows_html += f"<td style='padding:10px; text-align:center;'>{color_value(d.get('indiv', 0))}억</td>"
            rows_html += f"<td style='padding:10px; text-align:center;'>{color_value(d.get('frgn', 0))}억</td>"
            rows_html += f"<td style='padding:10px; text-align:center;'>{color_value(d.get('inst', 0))}억</td></tr>"

        st.markdown(f"""
        <table style="width:100%; border-collapse:collapse; border:1px solid #ddd; border-radius:8px;">
        {header_html}{rows_html}
        </table>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"시장 데이터를 불러오지 못했습니다: {e}")

# ── 탭 2: 종목 검색 ──
with tab_search:
    col_q, col_btn = st.columns([4, 1])
    with col_q:
        stock_query = st.text_input("종목명 또는 종목코드", placeholder="삼성전자, 005930 등", key="stock_query")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        search_clicked = st.button("🔍 검색", key="stock_search", use_container_width=True)

    if search_clicked and stock_query.strip():
        try:
            with st.spinner("종목을 검색하는 중..."):
                results = search_stock_code(stock_query)

            if not results:
                st.warning("검색 결과가 없습니다. 종목명이나 코드를 확인해주세요.")
            else:
                if len(results) > 1:
                    selected = st.selectbox("검색 결과가 여러 개입니다. 선택하세요:",
                                           [f"{name} ({code})" for name, code in results])
                    idx = [f"{name} ({code})" for name, code in results].index(selected)
                    name, code = results[idx]
                else:
                    name, code = results[0]

                with st.spinner(f"{name} 데이터를 가져오는 중..."):
                    price_info = get_current_price(code)
                    trend_rows = get_investor_trend(code)

                # 현재가 표시
                rf = price_info["rf"]
                price_color = "#E74C3C" if rf in ("1", "2") else "#3498DB" if rf in ("4", "5") else "#636E72"

                st.markdown(f"""
                <div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #ddd; margin: 12px 0;">
                    <span style="font-size: 1.3em; font-weight: bold;">{price_info['name']}</span>
                    <span style="font-size: 0.9em; color: #636E72; margin-left: 8px;">({code})</span>
                    <span style="float: right; font-size: 1.5em; font-weight: bold; color: {price_color};">
                        {price_info['price']}원
                        <span style="font-size: 0.7em;">({price_info['change']} / {price_info['rate']}%)</span>
                    </span>
                </div>
                """, unsafe_allow_html=True)

                # 매매동향 표
                st.markdown("#### 최근 매매동향")
                st.caption("※ '개인 순매매(추정)'은 '기관+외국인'을 반대로 한 추정값입니다")

                header = "<tr>"
                for h in ["날짜", "종가", "기관 순매매", "외국인 순매매", "개인 순매매(추정)"]:
                    header += f"<th style='padding:8px; background:#f8f9fa; text-align:center;'>{h}</th>"
                header += "</tr>"

                body = ""
                for row in trend_rows:
                    inst = to_int(row["inst"])
                    frgn = to_int(row["frgn"])
                    indiv = -(inst + frgn)

                    close_val = to_int(row["close"])
                    updown = row.get("updown", "")
                    close_color = "#E74C3C" if "상승" in updown else "#3498DB" if "하락" in updown else "#333"

                    body += f"<tr>"
                    body += f"<td style='padding:8px; text-align:center;'>{row['date']}</td>"
                    body += f"<td style='padding:8px; text-align:right; color:{close_color};'>{row['close']}</td>"
                    body += f"<td style='padding:8px; text-align:center;'>{color_value(inst)}</td>"
                    body += f"<td style='padding:8px; text-align:center;'>{color_value(frgn)}</td>"
                    body += f"<td style='padding:8px; text-align:center;'>{color_value(indiv)}</td>"
                    body += f"</tr>"

                st.markdown(f"""
                <table style="width:100%; border-collapse:collapse; border:1px solid #ddd;">
                {header}{body}
                </table>
                """, unsafe_allow_html=True)

        except requests.exceptions.RequestException:
            st.error("인터넷 연결을 확인해주세요.")
        except Exception as e:
            st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")

# ── 탭 3: 업종별 한눈에 보기 ──
with tab_sector:
    st.caption("주요 업종별 대표 종목의 현재가와 매매동향을 한 화면에서 확인합니다")
    st.caption("※ '개인 순매매(추정)'은 '기관+외국인'을 반대로 한 추정값입니다")

    if st.button("🔄 업종 데이터 새로고침", key="sector_refresh"):
        if "sector_cache" in st.session_state:
            del st.session_state.sector_cache

    @st.cache_data(ttl=300, show_spinner="업종별 데이터를 불러오는 중... (종목이 많아 시간이 걸릴 수 있습니다)")
    def load_sector_data():
        all_data = {}
        for sector, stocks in SECTOR_STOCKS.items():
            sector_rows = []
            for name, code in stocks:
                try:
                    price_info = get_current_price(code)
                    trend = get_investor_trend(code, days=1)
                    sector_rows.append((name, code, price_info, trend, None))
                except Exception as e:
                    sector_rows.append((name, code, None, None, str(e)))
            all_data[sector] = sector_rows
        return all_data

    try:
        sector_data = load_sector_data()

        for sector, rows in sector_data.items():
            st.markdown(f"##### 📁 {sector}")

            header = "<tr>"
            for h in ["종목", "현재가", "등락률", "기관 순매매", "외국인 순매매", "개인 순매매(추정)"]:
                header += f"<th style='padding:6px; background:#f0f0f0; text-align:center; font-size:0.85em;'>{h}</th>"
            header += "</tr>"

            body = ""
            for name, code, price_info, trend, error in rows:
                if error or not price_info:
                    body += f"<tr><td style='padding:6px;'>{name}</td><td colspan='5' style='color:#999;'>데이터 없음</td></tr>"
                    continue

                rf = price_info["rf"]
                price_color = "#E74C3C" if rf in ("1", "2") else "#3498DB" if rf in ("4", "5") else "#333"

                inst, frgn = 0, 0
                if trend:
                    inst = to_int(trend[0]["inst"])
                    frgn = to_int(trend[0]["frgn"])
                indiv = -(inst + frgn)

                body += f"<tr>"
                body += f"<td style='padding:6px; font-weight:bold;'>{name}</td>"
                body += f"<td style='padding:6px; text-align:right; color:{price_color};'>{price_info['price']}</td>"
                body += f"<td style='padding:6px; text-align:center; color:{price_color};'>{price_info['rate']}%</td>"
                body += f"<td style='padding:6px; text-align:center;'>{color_value(inst)}</td>"
                body += f"<td style='padding:6px; text-align:center;'>{color_value(frgn)}</td>"
                body += f"<td style='padding:6px; text-align:center;'>{color_value(indiv)}</td>"
                body += f"</tr>"

            st.markdown(f"<table style='width:100%; border-collapse:collapse; border:1px solid #ddd; margin-bottom:16px;'>{header}{body}</table>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"업종 데이터를 불러오지 못했습니다: {e}")
