import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password
from data.tojeong_data import (
    GWAE_DATA, MONTH_ELEMENT, MONTHLY_PHRASE_POOL, GENERATES, OVERCOMES,
)
from data.lunar_calendar import solar_to_lunar

st.set_page_config(page_title="토정비결 - 마이 유틸리티", page_icon="📅", layout="centered")
apply_common_style()
check_password()

# ── 12지지 이름표 (원본에서 가져옴) ──
JIJI = [
    "자(쥐)", "축(소)", "인(호랑이)", "묘(토끼)", "진(용)", "사(뱀)",
    "오(말)", "미(양)", "신(원숭이)", "유(닭)", "술(개)", "해(돼지)",
]

# ── 괘 계산 함수 (원본 그대로) ──
def get_jiji_number(lunar_year):
    return (lunar_year - 1900) % 12 + 1

def calc_gwae(lunar_year, lunar_month, lunar_day):
    tae_se = get_jiji_number(lunar_year)
    wol_geon = lunar_month
    il_jin = lunar_day

    sang = (tae_se + wol_geon) % 8
    sang = 8 if sang == 0 else sang
    jung = (wol_geon + il_jin) % 6
    jung = 6 if jung == 0 else jung
    ha = (il_jin + tae_se) % 3
    ha = 3 if ha == 0 else ha
    return sang, jung, ha

# ── 월별 운세 함수 (원본 그대로) ──
def _element_relation(gwae_element, month_element):
    if gwae_element == month_element:
        return "평"
    if GENERATES[gwae_element] == month_element or GENERATES[month_element] == gwae_element:
        return "길"
    if OVERCOMES[gwae_element] == month_element:
        return "길"
    if OVERCOMES[month_element] == gwae_element:
        return "흉"
    return "평"

def _decide_level(base_level, seed, offset):
    levels = ["흉", "평", "길"]
    pattern = {"길": [2, 2, 1], "흉": [0, 0, 1], "평": [1, 2, 0]}
    idx = pattern[base_level][(seed + offset) % 3]
    return levels[idx]

def get_monthly_fortune(sang, jung, ha, month, gwae_element):
    seed = sang * 100 + jung * 10 + ha + month
    base_level = _element_relation(gwae_element, MONTH_ELEMENT[month])
    themes = [("재물", 0), ("건강", 1), ("애정", 2), ("인간관계", 3)]
    sentences = []
    for theme, offset in themes:
        level = _decide_level(base_level, seed, offset)
        pool = MONTHLY_PHRASE_POOL[theme][level]
        idx = (seed + offset * 7) % len(pool)
        sentences.append(pool[idx])
    return " ".join(sentences)

def get_all_monthly_fortunes(sang, jung, ha, gwae_element):
    return {month: get_monthly_fortune(sang, jung, ha, month, gwae_element) for month in range(1, 13)}

# ── 세션 상태 ──
if "tojeong_screen" not in st.session_state:
    st.session_state.tojeong_screen = "input"

# ── 입력 화면 ──
if st.session_state.tojeong_screen == "input":
    show_page_header("📅", "토정비결 - 신년운세 보기", "생년월일을 입력하면 올해의 총운과 월별 운세를 알려드립니다")

    with st.form("tojeong_form"):
        name = st.text_input("이름 (선택)", placeholder="이름을 입력하세요")
        gender = st.radio("성별", ["남", "여"], horizontal=True)
        calendar_type = st.radio("달력 종류", ["양력", "음력"], horizontal=True)

        col_y, col_m, col_d = st.columns(3)
        with col_y:
            year = st.number_input("년", min_value=1920, max_value=2025, value=1990)
        with col_m:
            month = st.number_input("월", min_value=1, max_value=12, value=1)
        with col_d:
            max_day = 31 if calendar_type == "양력" else 30
            day = st.number_input("일", min_value=1, max_value=max_day, value=1)

        is_leap = False
        if calendar_type == "음력":
            is_leap = st.checkbox("윤달입니다")
            st.caption("※ 윤달이어도 같은 달 숫자로 계산됩니다.")
        else:
            st.caption("※ 양력 날짜는 음력으로 자동 변환되어 계산됩니다.")

        submitted = st.form_submit_button("운세 보기", type="primary", use_container_width=True)

    if submitted:
        if calendar_type == "양력":
            try:
                lunar_year, lunar_month, lunar_day, is_leap_result = solar_to_lunar(year, month, day)
                if lunar_month == 0:
                    st.error("음력으로 변환할 수 없는 날짜입니다. 날짜를 다시 확인해주세요.")
                    st.stop()
            except (IndexError, ValueError):
                st.error("음력으로 변환할 수 없는 날짜입니다. 날짜를 다시 확인해주세요.")
                st.stop()
            is_leap = is_leap_result
        else:
            lunar_year, lunar_month, lunar_day = year, month, day

        sang, jung, ha = calc_gwae(lunar_year, lunar_month, lunar_day)
        jiji = JIJI[get_jiji_number(lunar_year) - 1]
        gwae = GWAE_DATA[f"{sang}-{jung}-{ha}"]
        monthly = get_all_monthly_fortunes(sang, jung, ha, gwae["element"])

        st.session_state.tojeong_screen = "result"
        st.session_state.tojeong_data = {
            "name": name.strip() or "OOO님",
            "gender": gender,
            "lunar_year": lunar_year, "lunar_month": lunar_month, "lunar_day": lunar_day,
            "is_leap": is_leap, "jiji": jiji,
            "sang": sang, "jung": jung, "ha": ha,
            "gwae": gwae, "monthly": monthly,
            "calendar_type": calendar_type,
            "solar_year": year, "solar_month": month, "solar_day": day,
        }
        st.rerun()

# ── 결과 화면 ──
elif st.session_state.tojeong_screen == "result":
    d = st.session_state.tojeong_data
    leap_text = "(윤달) " if d["is_leap"] else ""

    if d["calendar_type"] == "양력":
        birth_text = (f"양력 {d['solar_year']}년 {d['solar_month']}월 {d['solar_day']}일 → "
                      f"음력 {d['lunar_year']}년 {leap_text}{d['lunar_month']}월 {d['lunar_day']}일 "
                      f"({d['jiji']}띠) · {d['gender']}성")
    else:
        birth_text = (f"음력 {d['lunar_year']}년 {leap_text}{d['lunar_month']}월 {d['lunar_day']}일 "
                      f"({d['jiji']}띠) · {d['gender']}성")

    show_page_header("📅", f"{d['name']}의 신년운세")
    st.caption(f"{birth_text}  /  제 {d['sang']}-{d['jung']}-{d['ha']} 괘")

    # 총운
    gwae = d["gwae"]
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #F5F0E6 0%, #E8DCC8 100%);
                border-radius: 16px; padding: 24px; margin: 16px 0;
                border: 1px solid #D8CFBC;">
        <h3 style="color: #A6841C; margin-bottom: 4px;">{gwae['title']}</h3>
        <p style="color: #5A5A5A; font-weight: bold;">올해의 총운 ({gwae['tendency']})</p>
        <p style="color: #2C2C2C; line-height: 1.8;">{gwae['general']}</p>
    </div>
    """, unsafe_allow_html=True)

    # 월별 운세
    st.markdown("### 📅 월별 운세 (음력 기준)")

    monthly = d["monthly"]
    for month in range(1, 13):
        with st.expander(f"{month}월"):
            st.write(monthly[month])

    # 결과 텍스트 만들기
    result_lines = [f"=== {d['name']}의 토정비결 신년운세 ===",
                    birth_text,
                    f"제 {d['sang']}-{d['jung']}-{d['ha']} 괘 : {gwae['title']}",
                    "", f"[총운 - {gwae['tendency']}]", gwae["general"],
                    "", "[월별 운세]"]
    for month in range(1, 13):
        result_lines.append(f"- {month}월: {monthly[month]}")
    result_text = "\n".join(result_lines)

    st.markdown("")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("다시 입력하기", use_container_width=True):
            st.session_state.tojeong_screen = "input"
            st.rerun()
    with col_b:
        st.download_button(
            "결과 저장 (txt)", data=result_text,
            file_name=f"{d['name']}_토정비결.txt", mime="text/plain",
            use_container_width=True,
        )
