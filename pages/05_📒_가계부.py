import streamlit as st
import json
import calendar as cal_mod
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="가계부 - 마이 유틸리티", page_icon="📒", layout="wide")
apply_common_style()
check_password()
show_page_header("📒", "월 가계부", "수입/지출을 입력하고 월별 통계를 확인하세요")

# ── 카테고리 (원본 그대로) ──
INCOME_CATS  = ["급여", "부업", "기타수입"]
EXPENSE_CATS = ["식비", "교통비", "주거비", "의료비", "교육비", "쇼핑", "외식", "문화/여가", "기타"]
WEEKDAY_KR   = ["월", "화", "수", "목", "금", "토", "일"]

# ── 세션 상태 초기화 ──
if "ledger_data" not in st.session_state:
    st.session_state.ledger_data = {}
if "ledger_year" not in st.session_state:
    st.session_state.ledger_year = datetime.now().year
if "ledger_month" not in st.session_state:
    st.session_state.ledger_month = datetime.now().month
if "ledger_day" not in st.session_state:
    st.session_state.ledger_day = datetime.now().day

data = st.session_state.ledger_data
y = st.session_state.ledger_year
m = st.session_state.ledger_month
sel_day = st.session_state.ledger_day

def day_key(y, m, d):
    return f"{y}-{m:02d}-{d:02d}"

def get_day(y, m, d):
    k = day_key(y, m, d)
    if k not in data:
        data[k] = {"income": {c: 0 for c in INCOME_CATS},
                   "expense": {c: 0 for c in EXPENSE_CATS},
                   "memo": ""}
    return data[k]

# ── 월 이동 컨트롤 ──
col_prev, col_title, col_next = st.columns([1, 3, 1])
with col_prev:
    if st.button("◀ 이전 달", use_container_width=True):
        if m == 1:
            st.session_state.ledger_month = 12
            st.session_state.ledger_year = y - 1
        else:
            st.session_state.ledger_month = m - 1
        st.session_state.ledger_day = 1
        st.rerun()
with col_title:
    st.markdown(f"<h3 style='text-align:center;'>{y}년 {m}월</h3>", unsafe_allow_html=True)
with col_next:
    if st.button("다음 달 ▶", use_container_width=True):
        if m == 12:
            st.session_state.ledger_month = 1
            st.session_state.ledger_year = y + 1
        else:
            st.session_state.ledger_month = m + 1
        st.session_state.ledger_day = 1
        st.rerun()

# ── 레이아웃: 왼쪽(달력+요약) / 오른쪽(입력) ──
left_col, right_col = st.columns([2, 3])

with left_col:
    # 달력 표시
    st.markdown("#### 📅 달력")
    first_wd, num_days = cal_mod.monthrange(y, m)
    today = datetime.now()

    # 요일 헤더
    day_cols = st.columns(7)
    for i, wd in enumerate(WEEKDAY_KR):
        day_cols[i].markdown(f"<div style='text-align:center; font-weight:bold; color:{'#E17055' if i >= 5 else '#2D3436'};'>{wd}</div>", unsafe_allow_html=True)

    # 날짜 버튼
    col_idx = first_wd
    week_cols = st.columns(7)
    # 빈 칸 채우기
    for blank in range(first_wd):
        week_cols[blank].markdown("")

    for d in range(1, num_days + 1):
        wd = (first_wd + d - 1) % 7
        if wd == 0 and d > 1:
            week_cols = st.columns(7)

        dd = get_day(y, m, d)
        has_data = sum(dd["income"].values()) > 0 or sum(dd["expense"].values()) > 0
        is_selected = (d == sel_day)
        is_today = (d == today.day and m == today.month and y == today.year)

        label = f"**{d}**" if is_selected else str(d)
        if has_data:
            label += " ●"

        with week_cols[wd]:
            btn_type = "primary" if is_selected else "secondary"
            if st.button(label, key=f"cal_{d}", use_container_width=True, type=btn_type):
                st.session_state.ledger_day = d
                st.rerun()

    # 월 요약
    st.markdown("#### 📊 월 요약")
    total_inc = total_exp = 0
    for d in range(1, num_days + 1):
        dd = get_day(y, m, d)
        total_inc += sum(dd["income"].values())
        total_exp += sum(dd["expense"].values())
    bal = total_inc - total_exp

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("총 수입", f"₩{total_inc:,}")
    mc2.metric("총 지출", f"₩{total_exp:,}")
    mc3.metric("순 저축", f"₩{bal:,}", delta=f"{bal/total_inc*100:.1f}%" if total_inc > 0 else None)

with right_col:
    wd_name = WEEKDAY_KR[datetime(y, m, sel_day).weekday()]
    st.markdown(f"### {y}년 {m}월 {sel_day}일 ({wd_name})")

    dd = get_day(y, m, sel_day)

    # 수입 입력
    with st.expander("💰 수입", expanded=True):
        income_values = {}
        for cat in INCOME_CATS:
            income_values[cat] = st.number_input(
                cat, min_value=0, value=dd["income"].get(cat, 0),
                step=1000, key=f"inc_{cat}"
            )

    # 지출 입력
    with st.expander("💸 지출", expanded=True):
        expense_values = {}
        for cat in EXPENSE_CATS:
            expense_values[cat] = st.number_input(
                cat, min_value=0, value=dd["expense"].get(cat, 0),
                step=1000, key=f"exp_{cat}"
            )

    # 메모
    memo = st.text_area("📝 하루 메모", value=dd.get("memo", ""), height=80, key="memo_input")

    # 오늘 잔액 미리보기
    today_inc = sum(income_values.values())
    today_exp = sum(expense_values.values())
    prev_bal = 0
    for d2 in range(1, sel_day):
        dd2 = get_day(y, m, d2)
        prev_bal += sum(dd2["income"].values()) - sum(dd2["expense"].values())
    today_bal = prev_bal + today_inc - today_exp

    bal_color = "#00B894" if today_bal >= 0 else "#E17055"
    st.markdown(f"""
    <div style="background: #2D3436; color: white; padding: 16px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: bold;">오늘까지 잔액</span>
        <span style="font-size: 1.3em; font-weight: bold; color: {bal_color};">₩ {today_bal:,}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # 저장 버튼
    if st.button("💾 저장", type="primary", use_container_width=True):
        k = day_key(y, m, sel_day)
        data[k] = {
            "income": income_values,
            "expense": expense_values,
            "memo": memo,
        }
        st.success(f"{m}월 {sel_day}일 데이터가 저장되었습니다.")
        st.rerun()

# ── 데이터 저장/불러오기 ──
st.divider()
st.caption("💡 가계부 데이터는 브라우저 탭을 닫으면 초기화됩니다. 아래에서 저장/불러오기를 할 수 있습니다.")

col_save, col_load = st.columns(2)
with col_save:
    if data:
        st.download_button(
            "💾 데이터 저장",
            data=json.dumps(data, ensure_ascii=False, indent=2),
            file_name="ledger_data.json",
            mime="application/json",
            use_container_width=True,
        )
with col_load:
    uploaded = st.file_uploader("📂 데이터 불러오기", type="json", label_visibility="collapsed", key="ledger_upload")
    if uploaded:
        try:
            loaded = json.loads(uploaded.read().decode("utf-8"))
            st.session_state.ledger_data = loaded
            st.rerun()
        except Exception:
            st.error("파일을 읽을 수 없습니다.")
