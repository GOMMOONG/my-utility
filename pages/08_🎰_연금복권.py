import streamlit as st
import urllib.request
import re
import random
from datetime import date
from collections import Counter
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="연금복권 - 마이 유틸리티", page_icon="🎰", layout="centered")
apply_common_style()
check_password()
show_page_header("🎰", "연금복권720+ 번호 생성기", "최근 3년치 당첨번호를 분석해서 번호를 추천합니다")

RESULT_URL = "https://www.dhlottery.co.kr/gameResult.do?method=win720&drwNo={}"
FIRST_DRAW_DATE = date(2020, 2, 13)

# ── 원본 로직 함수들 ──
def fetch_round(round_no):
    try:
        url = RESULT_URL.format(round_no)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=7) as res:
            html = res.read().decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        m = re.search(r"1\s*등.{0,40}?([1-5])\s*조.{0,40}?(\d{6})", text)
        if not m:
            return None
        return int(m.group(1)), m.group(2)
    except Exception:
        return None

def estimate_latest_round():
    days = (date.today() - FIRST_DRAW_DATE).days
    return max(1, days // 7 + 1)

def get_latest_round():
    estimate = estimate_latest_round()
    for round_no in range(estimate + 5, max(1, estimate - 10), -1):
        result = fetch_round(round_no)
        if result:
            return round_no
    return 0

def fetch_history(latest, weeks=156):
    history = []
    for round_no in range(latest, max(0, latest - weeks), -1):
        result = fetch_round(round_no)
        if result:
            history.append(result)
    return history

def build_digit_counters(history):
    counters = [Counter() for _ in range(6)]
    for _group, number in history:
        for i, ch in enumerate(number):
            counters[i][int(ch)] += 1
    return counters

def weighted_digit(counter):
    digits = list(range(10))
    weights = [counter.get(d, 0) + 1 for d in digits]
    return random.choices(digits, weights=weights, k=1)[0]

def random_number():
    return "".join(str(random.randint(0, 9)) for _ in range(6))

def weighted_number(counters):
    return "".join(str(weighted_digit(c)) for c in counters)

# ── 데이터 수집 (캐시) ──
@st.cache_data(ttl=3600, show_spinner="연금복권 당첨번호를 수집하는 중...")
def load_pension_data():
    latest = get_latest_round()
    if latest == 0:
        return None, [], True
    history = fetch_history(latest, weeks=156)
    if not history:
        return latest, [], True
    counters = build_digit_counters(history)
    return latest, counters, False

latest, counters, offline = load_pension_data()

if offline:
    st.warning("인터넷 연결에 실패했습니다. 완전 랜덤 모드로 번호를 생성합니다.")
else:
    st.success(f"당첨번호 데이터를 분석했습니다 ({latest}회 기준)")

# ── 번호 생성 ──
if st.button("🎰 번호 생성하기", type="primary", use_container_width=True):
    st.session_state.pension_generated = True

if st.session_state.get("pension_generated"):
    st.markdown("### 추천 번호")

    for group in range(1, 6):
        if offline or not counters:
            number = random_number()
            method = "랜덤"
            method_color = "#00B894"
        else:
            number = weighted_number(counters)
            method = "빈도반영"
            method_color = "#E17055"

        digits_html = ""
        for d in number:
            digits_html += f'<span style="display:inline-block; width:36px; height:36px; line-height:36px; text-align:center; border-radius:8px; background:#6C5CE7; color:white; font-weight:bold; margin:2px; font-size:1.1em;">{d}</span>'

        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin: 8px 0; padding: 12px; background: white; border-radius: 12px; border: 1px solid #f0f0f0;">
            <span style="font-weight: bold; font-size: 1.1em; min-width: 40px;">{group}조</span>
            <div>{digits_html}</div>
            <span style="color: {method_color}; font-size: 0.85em; font-weight: bold;">({method})</span>
        </div>
        """, unsafe_allow_html=True)

    # 자리별 빈도
    if not offline and counters:
        st.markdown("### 📊 자리별 최다 출현 숫자 TOP 3")
        for i, counter in enumerate(counters, start=1):
            top3 = counter.most_common(3)
            if top3:
                top_text = ", ".join(f"**{n}** ({cnt}회)" for n, cnt in top3)
                st.markdown(f"- **{i}번째 자리**: {top_text}")

    st.divider()
    st.caption("※ 복권 당첨번호는 완전히 무작위이며, 이 결과는 재미를 위한 참고용입니다.")
