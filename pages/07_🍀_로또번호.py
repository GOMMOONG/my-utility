import streamlit as st
import urllib.request
import json
import random
from collections import Counter
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="로또번호 - 마이 유틸리티", page_icon="🍀", layout="centered")
apply_common_style()
check_password()
show_page_header("🍀", "로또 번호 생성기", "최근 1년 당첨번호를 분석해서 번호를 추천합니다")

LOTTO_API = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"

# ── 원본 로직 함수들 ──
def fetch_round(round_no):
    try:
        url = LOTTO_API.format(round_no)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=7) as res:
            data = json.loads(res.read().decode())
        if data.get("returnValue") != "success":
            return None
        return [data[f"drwtNo{i}"] for i in range(1, 7)]
    except Exception:
        return None

def get_latest_round():
    for round_no in range(1250, 1080, -1):
        nums = fetch_round(round_no)
        if nums:
            return round_no
    return 0

def fetch_frequency(latest, weeks=52):
    counter = Counter()
    for round_no in range(latest, max(1, latest - weeks), -1):
        nums = fetch_round(round_no)
        if nums:
            counter.update(nums)
    return counter

def weighted_pick(freq, count=6):
    remaining = list(range(1, 46))
    chosen = []
    while len(chosen) < count and remaining:
        weights = [freq.get(n, 0) + 1 for n in remaining]
        picked = random.choices(remaining, weights=weights, k=1)[0]
        chosen.append(picked)
        remaining.remove(picked)
    return sorted(chosen)

def random_pick(count=6):
    return sorted(random.sample(range(1, 46), count))

def ball_color(n):
    if n <= 9:  return "#FBC531"
    if n <= 19: return "#0097E6"
    if n <= 29: return "#E84118"
    if n <= 39: return "#7F8FA6"
    return "#44BD32"

# ── 데이터 수집 (캐시로 한 번만) ──
@st.cache_data(ttl=3600, show_spinner="당첨번호 데이터를 수집하는 중...")
def load_lotto_data():
    latest = get_latest_round()
    if latest == 0:
        return None, Counter(), True
    freq = fetch_frequency(latest, weeks=52)
    if not freq:
        return latest, Counter(), True
    return latest, freq, False

latest, freq, offline = load_lotto_data()

if offline:
    st.warning("인터넷 연결에 실패했습니다. 완전 랜덤 모드로 번호를 생성합니다.")
else:
    fetched = sum(freq.values()) // 6
    st.success(f"최근 {fetched}회 당첨번호 데이터를 분석했습니다 ({latest}회 기준)")

# ── 번호 생성 버튼 ──
if st.button("🍀 번호 생성하기", type="primary", use_container_width=True):
    st.session_state.lotto_generated = True

if st.session_state.get("lotto_generated"):
    st.markdown("### 추천 번호")

    for i in range(1, 6):
        if i <= 3 and not offline and freq:
            nums = weighted_pick(freq)
            method = "빈도우선"
            method_color = "#E17055"
        else:
            nums = random_pick()
            method = "완전랜덤"
            method_color = "#00B894"

        balls_html = ""
        for n in nums:
            color = ball_color(n)
            balls_html += f'<span style="display:inline-block; width:36px; height:36px; line-height:36px; text-align:center; border-radius:50%; background:{color}; color:white; font-weight:bold; margin:2px; font-size:0.9em;">{n}</span>'

        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin: 8px 0; padding: 12px; background: white; border-radius: 12px; border: 1px solid #f0f0f0;">
            <span style="font-weight: bold; font-size: 1.1em; min-width: 40px;">{i}조</span>
            <div>{balls_html}</div>
            <span style="color: {method_color}; font-size: 0.85em; font-weight: bold;">({method})</span>
        </div>
        """, unsafe_allow_html=True)

    # 빈도 TOP 15
    if not offline and freq:
        st.markdown("### 📊 빈도 TOP 15")
        st.caption("1~3조에서 우선 선택되는 번호들입니다")

        most_common = freq.most_common(15)
        if most_common:
            max_cnt = most_common[0][1]
            for num, cnt in most_common:
                bar_ratio = cnt / max_cnt
                color = ball_color(num)
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 8px; margin: 2px 0;">
                    <span style="display:inline-block; width:30px; height:30px; line-height:30px; text-align:center; border-radius:50%; background:{color}; color:white; font-weight:bold; font-size:0.8em;">{num}</span>
                    <div style="flex:1; background:#f0f0f0; border-radius:4px; height:18px;">
                        <div style="width:{bar_ratio*100:.0f}%; background:{color}; height:100%; border-radius:4px;"></div>
                    </div>
                    <span style="font-size:0.85em; color:#636E72; min-width:40px;">{cnt}회</span>
                </div>
                """, unsafe_allow_html=True)

    st.divider()
    st.caption("※ 복권 당첨번호는 완전히 무작위이며, 이 결과는 재미를 위한 참고용입니다.")
