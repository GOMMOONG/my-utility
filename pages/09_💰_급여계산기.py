import streamlit as st
import math, copy
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="급여계산기 - 마이 유틸리티", page_icon="💰", layout="centered")
apply_common_style()
check_password()
show_page_header("💰", "급여 계산기", "월급에서 세금·4대보험을 빼고 실수령액을 계산합니다 (2025년 기준)")

# ── 2025년 4대보험 요율 ──
RATE_국민연금 = 0.045
RATE_건강보험 = 0.03545
RATE_장기요양 = 0.1295
RATE_고용보험 = 0.009
NPS_MIN = 390_000
NPS_MAX = 6_170_000

# ── 간이세액 계산 함수 (원본 그대로) ──
def calc_간이세액(월급여, 부양가족수=1):
    연급여 = 월급여 * 12
    if 연급여 <= 5_000_000:     근로소득공제 = 연급여 * 0.7
    elif 연급여 <= 15_000_000:  근로소득공제 = 3_500_000 + (연급여 - 5_000_000) * 0.4
    elif 연급여 <= 45_000_000:  근로소득공제 = 7_500_000 + (연급여 - 15_000_000) * 0.15
    elif 연급여 <= 100_000_000: 근로소득공제 = 12_000_000 + (연급여 - 45_000_000) * 0.05
    else:                        근로소득공제 = 14_750_000
    근로소득공제 = min(근로소득공제, 20_000_000)
    근로소득금액 = max(연급여 - 근로소득공제, 0)
    기본공제 = 부양가족수 * 1_500_000
    과세표준 = max(근로소득금액 - 기본공제, 0)

    if 과세표준 <= 14_000_000:      산출세액 = 과세표준 * 0.06
    elif 과세표준 <= 50_000_000:    산출세액 = 840_000 + (과세표준 - 14_000_000) * 0.15
    elif 과세표준 <= 88_000_000:    산출세액 = 6_240_000 + (과세표준 - 50_000_000) * 0.24
    elif 과세표준 <= 150_000_000:   산출세액 = 15_360_000 + (과세표준 - 88_000_000) * 0.35
    elif 과세표준 <= 300_000_000:   산출세액 = 37_060_000 + (과세표준 - 150_000_000) * 0.38
    elif 과세표준 <= 500_000_000:   산출세액 = 94_060_000 + (과세표준 - 300_000_000) * 0.40
    elif 과세표준 <= 1_000_000_000: 산출세액 = 174_060_000 + (과세표준 - 500_000_000) * 0.42
    else:                            산출세액 = 384_060_000 + (과세표준 - 1_000_000_000) * 0.45

    if 산출세액 <= 1_300_000: 세액공제 = 산출세액 * 0.55
    else: 세액공제 = 715_000 + (산출세액 - 1_300_000) * 0.30
    세액공제 = min(세액공제, 660_000)

    월소득세 = int(max(산출세액 - 세액공제, 0) / 12 * 0.80)
    return max(월소득세, 0)

def calc_4대보험(월보수):
    nps_base = max(NPS_MIN, min(NPS_MAX, 월보수))
    국민연금 = math.floor(nps_base * RATE_국민연금 / 10) * 10
    건강보험 = math.floor(월보수 * RATE_건강보험 / 10) * 10
    장기요양 = math.floor(건강보험 * RATE_장기요양 / 10) * 10
    고용보험 = math.floor(월보수 * RATE_고용보험 / 10) * 10
    return {"국민연금": 국민연금, "건강보험": 건강보험, "장기요양보험": 장기요양, "고용보험": 고용보험}

def fmt(n):
    return f"{n:,}"

# ── 탭 구성 ──
tab1, tab2, tab3 = st.tabs(["📋 급여 계산", "📈 인상 시뮬레이션", "📊 장기 예측"])

# ─── 탭 1: 기본 급여 계산 ───
with tab1:
    st.markdown("#### 지급 항목")
    col1, col2 = st.columns(2)
    with col1:
        기본급 = st.number_input("기본급 (원)", min_value=0, value=3_000_000, step=100_000, format="%d")
        초과근무 = st.number_input("초과근무수당 (원)", min_value=0, value=0, step=50_000, format="%d")
    with col2:
        성과급 = st.number_input("성과급 (원)", min_value=0, value=0, step=100_000, format="%d")
        직무수당 = st.number_input("직무수당 (원)", min_value=0, value=0, step=10_000, format="%d")

    st.markdown("#### 세금 설정")
    부양가족수 = st.number_input("부양가족수 (본인 포함)", min_value=1, max_value=20, value=1)

    if st.button("계산하기", type="primary", use_container_width=True, key="calc_btn"):
        총지급 = 기본급 + 성과급 + 초과근무 + 직무수당
        과세급여 = 총지급
        보험보수 = 기본급 + 직무수당

        소득세 = calc_간이세액(과세급여, 부양가족수)
        주민세 = int(소득세 * 0.10)
        보험 = calc_4대보험(보험보수)
        총공제 = 소득세 + 주민세 + sum(보험.values())
        실수령 = 총지급 - 총공제

        st.markdown("---")

        # 실수령액 강조 표시
        m1, m2, m3 = st.columns(3)
        m1.metric("총 지급액", f"{fmt(총지급)}원")
        m2.metric("총 공제액", f"{fmt(총공제)}원")
        m3.metric("실수령액", f"{fmt(실수령)}원")

        # 공제 상세
        st.markdown("#### 🧾 공제 항목 상세")

        deduction_data = {
            "항목": ["소득세", "주민세", "국민연금", "건강보험", "장기요양보험", "고용보험"],
            "금액": [f"{fmt(소득세)}원", f"{fmt(주민세)}원",
                    f"{fmt(보험['국민연금'])}원", f"{fmt(보험['건강보험'])}원",
                    f"{fmt(보험['장기요양보험'])}원", f"{fmt(보험['고용보험'])}원"],
            "비고": [f"간이세액(부양가족 {부양가족수}인)", "소득세 × 10%",
                    "보수월액 × 4.5%", "보수월액 × 3.545%",
                    "건강보험 × 12.95%", "보수월액 × 0.9%"],
        }
        st.table(deduction_data)

        st.markdown(f"**연간 실수령액: {fmt(실수령 * 12)}원**")

# ─── 탭 2: 인상 시뮬레이션 ───
with tab2:
    st.markdown("#### 현재 기본급 입력")
    base_기본급 = st.number_input("현재 기본급 (원)", min_value=0, value=3_000_000, step=100_000, format="%d", key="raise_base")
    base_직무수당 = st.number_input("직무수당 (원)", min_value=0, value=0, step=10_000, format="%d", key="raise_duty")
    raise_부양가족 = st.number_input("부양가족수", min_value=1, max_value=20, value=1, key="raise_fam")

    st.markdown("#### 인상률 비교")
    rates = [3.0, 5.0, 7.0, 10.0]

    if st.button("시나리오 비교", type="primary", use_container_width=True, key="scenario_btn"):
        rows = []
        for rate in rates:
            인상기본급 = int(base_기본급 * (1 + rate / 100))
            총지급_현재 = base_기본급 + base_직무수당
            총지급_인상 = 인상기본급 + base_직무수당

            소득세_현재 = calc_간이세액(총지급_현재, raise_부양가족)
            보험_현재 = calc_4대보험(총지급_현재)
            총공제_현재 = 소득세_현재 + int(소득세_현재 * 0.1) + sum(보험_현재.values())
            실수령_현재 = 총지급_현재 - 총공제_현재

            소득세_인상 = calc_간이세액(총지급_인상, raise_부양가족)
            보험_인상 = calc_4대보험(총지급_인상)
            총공제_인상 = 소득세_인상 + int(소득세_인상 * 0.1) + sum(보험_인상.values())
            실수령_인상 = 총지급_인상 - 총공제_인상

            월증가 = 실수령_인상 - 실수령_현재

            rows.append({
                "인상률": f"{rate}%",
                "인상후 기본급": f"{fmt(인상기본급)}원",
                "월 실수령액": f"{fmt(실수령_인상)}원",
                "월 증가액": f"+{fmt(월증가)}원",
                "연간 증가액": f"+{fmt(월증가 * 12)}원",
            })

        st.table(rows)
        st.caption("※ 세금·4대보험이 자동 재계산되어 실제 실수령 증가액이 반영됩니다.")

# ─── 탭 3: 장기 예측 ───
with tab3:
    st.markdown("#### 연봉 인상 장기 예측")
    proj_기본급 = st.number_input("현재 기본급 (원)", min_value=0, value=3_000_000, step=100_000, format="%d", key="proj_base")
    proj_직무수당 = st.number_input("직무수당 (원)", min_value=0, value=0, step=10_000, format="%d", key="proj_duty")
    proj_rate = st.slider("연 인상률 (%)", min_value=1.0, max_value=15.0, value=5.0, step=0.5)
    proj_부양가족 = st.number_input("부양가족수", min_value=1, max_value=20, value=1, key="proj_fam")

    if st.button("예측 보기", type="primary", use_container_width=True, key="proj_btn"):
        rows = []
        cur_기본급 = proj_기본급
        base_총지급 = proj_기본급 + proj_직무수당
        base_소득세 = calc_간이세액(base_총지급, proj_부양가족)
        base_보험 = calc_4대보험(base_총지급)
        base_총공제 = base_소득세 + int(base_소득세 * 0.1) + sum(base_보험.values())
        base_실수령 = base_총지급 - base_총공제
        base_연간 = base_실수령 * 12

        for yr in range(0, 21):
            총지급 = cur_기본급 + proj_직무수당
            소득세 = calc_간이세액(총지급, proj_부양가족)
            보험 = calc_4대보험(총지급)
            총공제 = 소득세 + int(소득세 * 0.1) + sum(보험.values())
            실수령 = 총지급 - 총공제
            연간 = 실수령 * 12
            연간증가 = 연간 - base_연간

            if yr % 5 == 0:
                label = "현재" if yr == 0 else f"{yr}년차"
                rows.append({
                    "시점": label,
                    "기본급": f"{fmt(cur_기본급)}원",
                    "월 실수령": f"{fmt(실수령)}원",
                    "연간 실수령": f"{fmt(연간)}원",
                    "연간 증가": f"+{fmt(연간증가)}원" if 연간증가 > 0 else "-",
                })

            cur_기본급 = int(cur_기본급 * (1 + proj_rate / 100))

        st.table(rows)
        st.caption(f"※ 매년 {proj_rate}% 복리 인상 기준, 세금·4대보험 자동 재계산")
