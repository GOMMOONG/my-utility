import streamlit as st
import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password
from data.saju_data import (
    CHEONGAN, JIJI, WOLGAN_BASE, SIGAN_BASE, SIJIN_OPTIONS,
    CHEONGAN_PERSONALITY, OHAENG_INTERPRETATION, JIJI_ANIMAL_DESC,
    GENERATES, OVERCOMES, FORTUNE_PHRASE_POOL,
)
from data.lunar_calendar import solar_to_lunar, solar_to_abs_days, lunar_to_abs_days

st.set_page_config(page_title="사주팔자 - 마이 유틸리티", page_icon="📊", layout="centered")
apply_common_style()
check_password()

# ── 60갑자 계산 함수 (원본 그대로) ──
DAY_GANJI_OFFSET = 14

def get_year_pillar(lunar_year):
    idx = (lunar_year - 4) % 60
    return idx % 10, idx % 12

def get_month_pillar(year_gan_idx, lunar_month):
    gan_idx = (WOLGAN_BASE[year_gan_idx] + (lunar_month - 1)) % 10
    ji_idx = (lunar_month + 1) % 12
    return gan_idx, ji_idx

def get_day_pillar(abs_days):
    idx = (abs_days + DAY_GANJI_OFFSET) % 60
    return idx % 10, idx % 12

def get_hour_pillar(day_gan_idx, sijin_idx):
    if sijin_idx is None:
        return None
    gan_idx = (SIGAN_BASE[day_gan_idx] + sijin_idx) % 10
    return gan_idx, sijin_idx

def count_ohaeng(pillars):
    counts = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    for gan_idx, ji_idx in pillars:
        counts[CHEONGAN[gan_idx]["element"]] += 1
        counts[JIJI[ji_idx]["element"]] += 1
    return counts

def ohaeng_level(count):
    if count >= 3: return "많음"
    if count == 0: return "부족"
    return "보통"

def pillar_text(gan_idx, ji_idx):
    gan = CHEONGAN[gan_idx]
    ji = JIJI[ji_idx]
    return f"{gan['name']}{ji['name']}({gan['hanja']}{ji['hanja']})"

# ── 운세 계산 함수 (원본 그대로) ──
def _element_relation(my_element, target_element):
    if my_element == target_element: return "평"
    if GENERATES[my_element] == target_element or GENERATES[target_element] == my_element: return "길"
    if OVERCOMES[my_element] == target_element: return "길"
    if OVERCOMES[target_element] == my_element: return "흉"
    return "평"

def _decide_level(base_level, seed, offset):
    levels = ["흉", "평", "길"]
    pattern = {"길": [2, 2, 1], "흉": [0, 0, 1], "평": [1, 2, 0]}
    idx = pattern[base_level][(seed + offset) % 3]
    return levels[idx]

def get_fortune_text(my_element, target_element, seed):
    base_level = _element_relation(my_element, target_element)
    themes = [("재물", 0), ("건강", 1), ("애정", 2), ("인간관계", 3)]
    sentences = []
    for theme, offset in themes:
        level = _decide_level(base_level, seed, offset)
        pool = FORTUNE_PHRASE_POOL[theme][level]
        idx = (seed + offset * 7) % len(pool)
        sentences.append(pool[idx])
    return " ".join(sentences)

# ── 세션 상태 ──
if "saju_screen" not in st.session_state:
    st.session_state.saju_screen = "input"

# ── 입력 화면 ──
if st.session_state.saju_screen == "input":
    show_page_header("📊", "사주팔자 보기", "생년월일과 태어난 시간을 입력하면 사주·오행·성격·운세를 알려드립니다")

    with st.form("saju_form"):
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

        # 시진 선택
        sijin_labels = [label for label, _ in SIJIN_OPTIONS]
        sijin_selected = st.selectbox("태어난 시간 (모르면 '모름' 선택)", sijin_labels, index=len(sijin_labels) - 1)

        st.caption("※ 이 결과는 절기(節氣)가 아닌 음력 월/연을 기준으로 한 약식 계산이며, 재미로 보는 참고용입니다.")
        submitted = st.form_submit_button("사주 보기", type="primary", use_container_width=True)

    if submitted:
        is_solar = calendar_type == "양력"
        if is_solar:
            try:
                lunar_year, lunar_month, lunar_day, is_leap = solar_to_lunar(year, month, day)
                if lunar_month == 0:
                    st.error("음력으로 변환할 수 없는 날짜입니다.")
                    st.stop()
            except (IndexError, ValueError):
                st.error("음력으로 변환할 수 없는 날짜입니다.")
                st.stop()
            abs_days = solar_to_abs_days(year, month, day)
        else:
            lunar_year, lunar_month, lunar_day = year, month, day
            abs_days = lunar_to_abs_days(year, month, day, is_leap)

        # 시진 index
        sijin_idx = None
        for label, idx in SIJIN_OPTIONS:
            if label == sijin_selected:
                sijin_idx = idx
                break

        # 사주 계산
        year_gan, year_ji = get_year_pillar(lunar_year)
        month_gan, month_ji = get_month_pillar(year_gan, lunar_month)
        day_gan, day_ji = get_day_pillar(abs_days)
        hour_pillar = get_hour_pillar(day_gan, sijin_idx)

        pillars = {"년주": (year_gan, year_ji), "월주": (month_gan, month_ji),
                   "일주": (day_gan, day_ji), "시주": hour_pillar}

        # 운세 계산
        my_element = CHEONGAN[day_gan]["element"]
        today = datetime.date.today()
        today_abs = solar_to_abs_days(today.year, today.month, today.day)
        today_lunar_year, _, _, _ = solar_to_lunar(today.year, today.month, today.day)
        this_year_gan, _ = get_year_pillar(today_lunar_year)
        today_day_gan, _ = get_day_pillar(today_abs)

        today_fortune = get_fortune_text(my_element, CHEONGAN[today_day_gan]["element"], abs_days + today_abs)
        year_fortune = get_fortune_text(my_element, CHEONGAN[this_year_gan]["element"], abs_days + today.year)
        monthly_fortunes = {}
        for m in range(1, 13):
            this_month_gan, _ = get_month_pillar(this_year_gan, m)
            seed = abs_days + today.year * 100 + m
            monthly_fortunes[m] = get_fortune_text(my_element, CHEONGAN[this_month_gan]["element"], seed)

        st.session_state.saju_screen = "result"
        st.session_state.saju_data = {
            "name": name.strip() or "OOO님", "gender": gender,
            "calendar_type": calendar_type,
            "solar_year": year, "solar_month": month, "solar_day": day,
            "lunar_year": lunar_year, "lunar_month": lunar_month, "lunar_day": lunar_day,
            "is_leap": is_leap, "pillars": pillars,
            "today": today, "today_fortune": today_fortune,
            "year_fortune": year_fortune, "monthly_fortunes": monthly_fortunes,
        }
        st.rerun()

# ── 결과 화면 ──
elif st.session_state.saju_screen == "result":
    d = st.session_state.saju_data
    pillars = d["pillars"]
    today = d["today"]
    leap_text = "(윤달) " if d["is_leap"] else ""

    if d["calendar_type"] == "양력":
        birth_text = (f"양력 {d['solar_year']}년 {d['solar_month']}월 {d['solar_day']}일 → "
                      f"음력 {d['lunar_year']}년 {leap_text}{d['lunar_month']}월 {d['lunar_day']}일 · {d['gender']}성")
    else:
        birth_text = f"음력 {d['lunar_year']}년 {leap_text}{d['lunar_month']}월 {d['lunar_day']}일 · {d['gender']}성"

    show_page_header("📊", f"{d['name']}의 사주팔자")
    st.caption(birth_text)

    # 사주표
    st.markdown("### 🔮 나의 사주(四柱)")
    cols = st.columns(4)
    for i, col_name in enumerate(["년주", "월주", "일주", "시주"]):
        with cols[i]:
            pillar = pillars[col_name]
            st.markdown(f"**{col_name}**")
            if pillar is None:
                st.markdown("모름")
            else:
                gan_idx, ji_idx = pillar
                gan = CHEONGAN[gan_idx]
                ji = JIJI[ji_idx]
                st.markdown(f"""
                <div style="text-align:center; background:#F5F0E6; border-radius:12px; padding:12px; border:1px solid #D8CFBC;">
                    <div style="font-size:1.3em; font-weight:bold; color:#A6841C;">{gan['name']} ({gan['hanja']})</div>
                    <div style="font-size:0.8em; color:#5A5A5A;">{gan['element']}({gan['yinyang']})</div>
                    <hr style="margin:6px 0; border-color:#D8CFBC;">
                    <div style="font-size:1.3em; font-weight:bold; color:#2C2C2C;">{ji['name']} ({ji['hanja']})</div>
                    <div style="font-size:0.8em; color:#5A5A5A;">{ji['element']}</div>
                </div>
                """, unsafe_allow_html=True)

    # 오행 분석
    valid_pillars = [v for v in pillars.values() if v is not None]
    ohaeng_counts = count_ohaeng(valid_pillars)

    st.markdown("### 🌳🔥 오행(五行) 분석")
    ohaeng_icons = {"목": "🌳", "화": "🔥", "토": "🪨", "금": "⚙️", "수": "💧"}
    ohaeng_cols = st.columns(5)
    for i, (element, count) in enumerate(ohaeng_counts.items()):
        with ohaeng_cols[i]:
            st.metric(f"{ohaeng_icons[element]} {element}", f"{count}개")

    for element, count in ohaeng_counts.items():
        level = ohaeng_level(count)
        st.markdown(f"> {OHAENG_INTERPRETATION[element][level]}")

    # 일간 성격
    day_gan_name = CHEONGAN[pillars["일주"][0]]["name"]
    st.markdown(f"### 🙂 일간({day_gan_name}) 성격 풀이")
    st.info(CHEONGAN_PERSONALITY[day_gan_name])

    # 띠 정보
    year_ji_idx = pillars["년주"][1]
    year_ji_name = JIJI[year_ji_idx]["name"]
    year_animal = JIJI[year_ji_idx]["animal"]
    st.markdown(f"### 🐾 {year_animal}띠 이야기")
    st.info(JIJI_ANIMAL_DESC[year_ji_name])

    # 오늘의 운세
    st.markdown(f"### 🗓️ 오늘의 운세 ({today.strftime('%Y년 %m월 %d일')})")
    st.write(d["today_fortune"])

    # 올해 총운
    st.markdown(f"### 🌟 {today.year}년 올해의 총운")
    st.write(d["year_fortune"])

    # 월별 운세
    st.markdown(f"### 📅 {today.year}년 월별 운세")
    for m in range(1, 13):
        with st.expander(f"{m}월"):
            st.write(d["monthly_fortunes"][m])

    st.caption("※ 이 결과는 절기(節氣)가 아닌 음력 월/연을 기준으로 한 약식 계산이며, 재미로 보는 참고용입니다.")

    # 결과 텍스트 생성
    result_lines = [f"=== {d['name']}의 사주팔자 ===", birth_text, ""]
    result_lines.append("[사주(四柱)]")
    for col_name in ["년주", "월주", "일주", "시주"]:
        pillar = pillars[col_name]
        if pillar is None:
            result_lines.append(f"- {col_name}: 모름")
        else:
            result_lines.append(f"- {col_name}: {pillar_text(pillar[0], pillar[1])}")
    result_lines += ["", "[오행(五行) 분석]"]
    result_lines.append("  ·  ".join(f"{el} {cnt}개" for el, cnt in ohaeng_counts.items()))
    for element, count in ohaeng_counts.items():
        result_lines.append(f"- {OHAENG_INTERPRETATION[element][ohaeng_level(count)]}")
    result_lines += ["", f"[일간({day_gan_name}) 성격 풀이]", CHEONGAN_PERSONALITY[day_gan_name]]
    result_lines += ["", f"[{year_animal}띠 이야기]", JIJI_ANIMAL_DESC[year_ji_name]]
    result_lines += ["", f"[오늘의 운세 ({today.strftime('%Y년 %m월 %d일')})]", d["today_fortune"]]
    result_lines += ["", f"[{today.year}년 올해의 총운]", d["year_fortune"]]
    result_lines += ["", f"[{today.year}년 월별 운세]"]
    for m in range(1, 13):
        result_lines.append(f"- {m}월: {d['monthly_fortunes'][m]}")
    result_text = "\n".join(result_lines)

    st.markdown("")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("다시 입력하기", use_container_width=True):
            st.session_state.saju_screen = "input"
            st.rerun()
    with col_b:
        st.download_button("결과 저장 (txt)", data=result_text,
                           file_name=f"{d['name']}_사주팔자.txt", mime="text/plain",
                           use_container_width=True)
