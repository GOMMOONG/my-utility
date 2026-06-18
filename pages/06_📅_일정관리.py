import streamlit as st
import json
import calendar as cal_mod
from datetime import datetime, date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="일정관리 - 마이 유틸리티", page_icon="📅", layout="wide")
apply_common_style()
check_password()
show_page_header("📅", "달력 일정 관리", "날짜를 선택해서 일정을 추가하고 확인하세요")

WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]

# ── 세션 상태 초기화 ──
if "schedule_data" not in st.session_state:
    st.session_state.schedule_data = {}
if "sched_year" not in st.session_state:
    st.session_state.sched_year = datetime.now().year
if "sched_month" not in st.session_state:
    st.session_state.sched_month = datetime.now().month
if "sched_day" not in st.session_state:
    st.session_state.sched_day = datetime.now().day

data = st.session_state.schedule_data
y = st.session_state.sched_year
m = st.session_state.sched_month
sel_day = st.session_state.sched_day

def day_key(y, m, d):
    return f"{y}-{m:02d}-{d:02d}"

# ── 월 이동 컨트롤 ──
col_prev, col_today, col_title, col_next = st.columns([1, 1, 3, 1])
with col_prev:
    if st.button("◀ 이전 달", use_container_width=True):
        if m == 1:
            st.session_state.sched_month = 12
            st.session_state.sched_year = y - 1
        else:
            st.session_state.sched_month = m - 1
        st.session_state.sched_day = 1
        st.rerun()
with col_today:
    if st.button("오늘", use_container_width=True):
        now = datetime.now()
        st.session_state.sched_year = now.year
        st.session_state.sched_month = now.month
        st.session_state.sched_day = now.day
        st.rerun()
with col_title:
    st.markdown(f"<h3 style='text-align:center;'>{y}년 {m}월</h3>", unsafe_allow_html=True)
with col_next:
    if st.button("다음 달 ▶", use_container_width=True):
        if m == 12:
            st.session_state.sched_month = 1
            st.session_state.sched_year = y + 1
        else:
            st.session_state.sched_month = m + 1
        st.session_state.sched_day = 1
        st.rerun()

# ── 레이아웃: 왼쪽(달력) / 오른쪽(일정 편집) ──
left_col, right_col = st.columns([3, 2])

with left_col:
    first_wd, num_days = cal_mod.monthrange(y, m)
    today = datetime.now()

    # 요일 헤더
    day_cols = st.columns(7)
    for i, wd in enumerate(WEEKDAY_KR):
        color = "#E17055" if i >= 5 else "#2D3436"
        day_cols[i].markdown(f"<div style='text-align:center; font-weight:bold; color:{color};'>{wd}</div>", unsafe_allow_html=True)

    # 날짜 버튼 배치
    week_cols = st.columns(7)
    for blank in range(first_wd):
        week_cols[blank].markdown("")

    for d in range(1, num_days + 1):
        wd = (first_wd + d - 1) % 7
        if wd == 0 and d > 1:
            week_cols = st.columns(7)

        items = data.get(day_key(y, m, d), [])
        is_selected = (d == sel_day)
        is_today = (d == today.day and m == today.month and y == today.year)

        label = str(d)
        if items:
            label += f" ({len(items)})"
        if is_today:
            label = f"📌{label}"

        with week_cols[wd]:
            btn_type = "primary" if is_selected else "secondary"
            if st.button(label, key=f"scal_{d}", use_container_width=True, type=btn_type):
                st.session_state.sched_day = d
                st.rerun()

with right_col:
    wd_name = WEEKDAY_KR[datetime(y, m, sel_day).weekday()]
    st.markdown(f"### {y}년 {m}월 {sel_day}일 ({wd_name})")

    key = day_key(y, m, sel_day)
    items = data.get(key, [])
    items_sorted = sorted(items, key=lambda x: x.get("time", ""))

    # 일정 목록 표시
    if not items_sorted:
        st.info("이 날에는 등록된 일정이 없습니다.")
    else:
        for idx, it in enumerate(items_sorted):
            col_time, col_content, col_del = st.columns([1, 4, 0.5])
            with col_time:
                st.markdown(f"**{it.get('time', '')}**")
            with col_content:
                st.write(it.get("content", ""))
            with col_del:
                if st.button("🗑", key=f"sdel_{idx}"):
                    items_sorted.pop(idx)
                    data[key] = items_sorted
                    st.rerun()

    st.divider()

    # 새 일정 추가
    st.markdown("##### 📝 새 일정 추가")
    col_time_in, col_content_in = st.columns([1, 3])
    with col_time_in:
        new_time = st.text_input("시간", value="09:00", key="sched_time_input")
    with col_content_in:
        new_content = st.text_input("내용", placeholder="일정 내용을 입력하세요", key="sched_content_input")

    if st.button("➕ 일정 추가", type="primary", use_container_width=True):
        if new_content.strip():
            data.setdefault(key, []).append({"time": new_time.strip(), "content": new_content.strip()})
            st.rerun()
        else:
            st.warning("일정 내용을 입력해주세요.")

# ── 데이터 저장/불러오기 ──
st.divider()
st.caption("💡 일정 데이터는 브라우저 탭을 닫으면 초기화됩니다. 아래에서 저장/불러오기를 할 수 있습니다.")

col_save, col_load = st.columns(2)
with col_save:
    if data:
        st.download_button(
            "💾 데이터 저장",
            data=json.dumps(data, ensure_ascii=False, indent=2),
            file_name="schedule_data.json",
            mime="application/json",
            use_container_width=True,
        )
with col_load:
    uploaded = st.file_uploader("📂 데이터 불러오기", type="json", label_visibility="collapsed", key="sched_upload")
    if uploaded:
        try:
            loaded = json.loads(uploaded.read().decode("utf-8"))
            st.session_state.schedule_data = loaded
            st.rerun()
        except Exception:
            st.error("파일을 읽을 수 없습니다.")
