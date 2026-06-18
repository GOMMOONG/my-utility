import streamlit as st
import math
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="연말정산 - 마이 유틸리티", page_icon="💳", layout="wide")
apply_common_style()
check_password()
show_page_header("💳", "연말정산 계산기", "총급여·공제항목을 입력하면 환급/추납 예상액을 계산합니다 (2025년 기준)")

# ── 세금 계산 함수들 (원본 로직 그대로) ──

def calc_employment_deduction(salary):
    """근로소득공제 (총급여에서 빼주는 금액, 5단계 구간)"""
    if salary <= 5_000_000:
        return int(salary * 0.70)
    if salary <= 15_000_000:
        return int(3_500_000 + (salary - 5_000_000) * 0.40)
    if salary <= 45_000_000:
        return int(7_500_000 + (salary - 15_000_000) * 0.15)
    if salary <= 100_000_000:
        return int(12_000_000 + (salary - 45_000_000) * 0.05)
    return int(14_750_000 + (salary - 100_000_000) * 0.02)

def calc_income_tax(taxable):
    """산출세액 (과세표준에 세율 적용, 8단계 누진세)"""
    if taxable <= 0:
        return 0
    brackets = [
        (14_000_000, 0.06, 0), (50_000_000, 0.15, 1_260_000),
        (88_000_000, 0.24, 5_760_000), (150_000_000, 0.35, 15_440_000),
        (300_000_000, 0.38, 19_940_000), (500_000_000, 0.40, 25_940_000),
        (1_000_000_000, 0.42, 35_940_000), (float("inf"), 0.45, 65_940_000),
    ]
    for limit, rate, prog in brackets:
        if taxable <= limit:
            return int(taxable * rate - prog)
    return 0

def calc_earned_income_credit(tax, salary):
    """근로소득 세액공제"""
    if tax <= 0:
        return 0
    credit = tax * 0.55 if tax <= 1_300_000 else 715_000 + (tax - 1_300_000) * 0.30
    if salary <= 33_000_000: limit = 740_000
    elif salary <= 70_000_000: limit = 660_000
    elif salary <= 120_000_000: limit = 500_000
    else: limit = 200_000
    return int(min(credit, limit))

def calc_card_deduction(salary, credit, debit, cash, market, transport, culture):
    """신용카드 등 소득공제"""
    total = credit + debit + cash + market + transport + culture
    minimum = int(salary * 0.25)
    if total <= minimum:
        return 0
    rem = minimum
    credit_ex = max(0, credit - rem); rem = max(0, rem - credit)
    debit_ex = max(0, debit + cash - rem); rem = max(0, rem - debit - cash)
    market_ex = max(0, market - rem); rem = max(0, rem - market)
    transport_ex = max(0, transport - rem); rem = max(0, rem - transport)
    culture_ex = max(0, culture - rem)

    base = int(credit_ex * 0.15 + debit_ex * 0.30)
    if salary <= 70_000_000: base_limit = 3_000_000
    elif salary <= 120_000_000: base_limit = 2_500_000
    else: base_limit = 2_000_000
    base = min(base, base_limit)

    market_d = min(int(market_ex * 0.40), 1_000_000)
    transport_d = min(int(transport_ex * 0.80), 1_000_000)
    culture_d = min(int(culture_ex * 0.30), 1_000_000) if salary <= 70_000_000 else 0
    return base + market_d + transport_d + culture_d

# ── 탭 구성 ──
tab1, tab2, tab3, tab4 = st.tabs(["1. 기본 정보", "2. 소비/지출", "3. 공제 항목", "4. 결과 보기"])

# 세션 상태 초기화
if "tax_data" not in st.session_state:
    st.session_state.tax_data = {}

# ── 탭 1: 기본 정보 ──
with tab1:
    st.markdown("#### 💼 급여 및 세금 정보")
    st.caption("급여명세서 또는 원천징수영수증을 보고 입력하세요")

    col1, col2 = st.columns(2)
    with col1:
        salary = st.number_input("총급여 (세전 연봉, 비과세 제외)", min_value=0, value=0, step=1_000_000, format="%d", key="salary")
        tax_paid = st.number_input("기납부 소득세 (원천징수된 소득세)", min_value=0, value=0, step=100_000, format="%d", key="tax_paid")
        local_tax_paid = st.number_input("기납부 지방소득세 (소득세의 10%)", min_value=0, value=0, step=10_000, format="%d", key="local_tax_paid")

    with col2:
        national_pension = st.number_input("국민연금 납부액 (연간 본인 부담분)", min_value=0, value=0, step=100_000, format="%d", key="national_pension")
        health_insurance = st.number_input("건강보험료 납부액 (연간 본인 부담분)", min_value=0, value=0, step=100_000, format="%d", key="health_insurance")

    st.markdown("#### 👨‍👩‍👧‍👦 부양가족 정보")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        spouse = st.checkbox("배우자 있음 (연소득 100만원 이하)", key="spouse")
        single_parent = st.checkbox("한부모 해당", key="single_parent")
        working_woman = st.checkbox("부녀자 해당", key="working_woman")
    with col_b:
        children = st.number_input("부양 자녀 수 (20세 이하)", min_value=0, max_value=10, value=0, key="children")
        parents = st.number_input("부양 부모 수 (60세 이상)", min_value=0, max_value=10, value=0, key="parents")
    with col_c:
        elderly = st.number_input("경로우대 (70세 이상)", min_value=0, max_value=10, value=0, key="elderly")
        disabled = st.number_input("장애인 수", min_value=0, max_value=10, value=0, key="disabled")

# ── 탭 2: 소비/지출 ──
with tab2:
    st.markdown("#### 💳 카드 및 현금 사용액")
    st.caption("연간 사용 총액을 입력하세요. 총급여의 25%를 초과한 금액부터 공제됩니다.")

    col1, col2 = st.columns(2)
    with col1:
        credit_card = st.number_input("신용카드 사용액 (공제율 15%)", min_value=0, value=0, step=1_000_000, format="%d", key="credit_card")
        debit_card = st.number_input("체크카드 사용액 (공제율 30%)", min_value=0, value=0, step=1_000_000, format="%d", key="debit_card")
        cash_receipt = st.number_input("현금영수증 사용액 (공제율 30%)", min_value=0, value=0, step=1_000_000, format="%d", key="cash_receipt")
    with col2:
        traditional_market = st.number_input("전통시장 사용액 (공제율 40%)", min_value=0, value=0, step=100_000, format="%d", key="traditional_market")
        public_transport = st.number_input("대중교통 사용액 (공제율 80%)", min_value=0, value=0, step=100_000, format="%d", key="public_transport")
        culture = st.number_input("도서·공연·영화 사용액 (공제율 30%)", min_value=0, value=0, step=100_000, format="%d", key="culture")

# ── 탭 3: 공제 항목 ──
with tab3:
    st.caption("해당하는 항목만 입력하세요. 입력하지 않은 항목은 0원으로 처리됩니다.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 🛡️ 보험료")
        insurance_premium = st.number_input("보장성 보험료 (한도 100만원, 12%)", min_value=0, value=0, step=100_000, format="%d", key="insurance_premium")
        disabled_insurance = st.number_input("장애인 보장성 보험료 (한도 100만원, 15%)", min_value=0, value=0, step=100_000, format="%d", key="disabled_insurance")

        st.markdown("##### 🏥 의료비")
        medical_self = st.number_input("본인 의료비 (한도 없음, 15%)", min_value=0, value=0, step=100_000, format="%d", key="medical_self")
        medical_elderly = st.number_input("65세 이상·장애인 의료비 (한도 없음, 15%)", min_value=0, value=0, step=100_000, format="%d", key="medical_elderly")
        medical_infertility = st.number_input("난임시술비 (한도 없음, 30%)", min_value=0, value=0, step=100_000, format="%d", key="medical_infertility")
        medical_family = st.number_input("기타 가족 의료비 (한도 700만원, 15%)", min_value=0, value=0, step=100_000, format="%d", key="medical_family")

        st.markdown("##### 📚 교육비")
        education_self = st.number_input("본인 교육비 (한도 없음, 15%)", min_value=0, value=0, step=100_000, format="%d", key="education_self")
        education_preschool = st.number_input("취학 전 아동 교육비 (한도 300만원)", min_value=0, value=0, step=100_000, format="%d", key="education_preschool")
        education_k12 = st.number_input("초·중·고 교육비 (한도 300만원)", min_value=0, value=0, step=100_000, format="%d", key="education_k12")
        education_university = st.number_input("대학생 교육비 (한도 900만원)", min_value=0, value=0, step=100_000, format="%d", key="education_university")

    with col2:
        st.markdown("##### 🤝 기부금")
        donation_legal = st.number_input("법정기부금 (전액 공제, 15%/30%)", min_value=0, value=0, step=100_000, format="%d", key="donation_legal")
        donation_designated = st.number_input("지정기부금 (소득 30% 한도)", min_value=0, value=0, step=100_000, format="%d", key="donation_designated")

        st.markdown("##### 🏠 연금 및 주거")
        pension_saving = st.number_input("연금저축 납입액 (한도 600만원)", min_value=0, value=0, step=100_000, format="%d", key="pension_saving")
        irp = st.number_input("IRP 납입액 (연금저축 합산 900만원 한도)", min_value=0, value=0, step=100_000, format="%d", key="irp")
        rent = st.number_input("월세 납부액 (연간 합계, 한도 750만원)", min_value=0, value=0, step=100_000, format="%d", key="rent")
        homeless = st.checkbox("무주택 세대주", key="homeless")

        st.markdown("##### 🏗️ 주택 관련 소득공제")
        housing_loan_repay = st.number_input("주택임차차입금 원리금 상환액", min_value=0, value=0, step=100_000, format="%d", key="housing_loan_repay")
        housing_savings = st.number_input("주택마련저축 납입액 (청약저축)", min_value=0, value=0, step=100_000, format="%d", key="housing_savings")
        mortgage_interest = st.number_input("장기주택저당차입금 이자상환액", min_value=0, value=0, step=100_000, format="%d", key="mortgage_interest")
        mortgage_type = st.selectbox("대출 유형", [
            "15년↑ 고정+비거치 (한도 1,800만)", "15년↑ 고정 또는 비거치 (한도 1,500만)",
            "15년↑ 기타 (한도 500만)", "10~15년 고정 또는 비거치 (한도 300만)",
        ], key="mortgage_type")

        st.markdown("##### 👶 기타 세액공제·감면")
        child_credit_count = st.number_input("자녀 세액공제 대상 수 (만 8세~20세)", min_value=0, max_value=10, value=0, key="child_credit_count")
        newborn_count = st.number_input("올해 출산·입양 자녀 수", min_value=0, max_value=10, value=0, key="newborn_count")
        marriage = st.checkbox("올해 혼인신고 (50만원 공제)", key="marriage")
        sme_youth = st.checkbox("중소기업 취업 청년 감면 (소득세 90% 감면)", key="sme_youth")

# ── 탭 4: 결과 보기 ──
with tab4:
    if st.button("📊 계산하기", type="primary", use_container_width=True):
        if salary <= 0:
            st.error("총급여(연봉)를 입력해주세요. (탭 1 '기본 정보'에서 입력)")
        else:
            # 근로소득공제 → 근로소득금액
            emp_ded = calc_employment_deduction(salary)
            earned_income = salary - emp_ded

            # 인적공제
            person_count = 1 + (1 if spouse else 0) + children + parents
            personal_ded = person_count * 1_500_000
            personal_ded += elderly * 1_000_000 + disabled * 2_000_000
            if single_parent: personal_ded += 1_000_000
            if working_woman: personal_ded += 500_000

            # 소득공제
            pension_ded = national_pension
            health_ded = health_insurance
            card_ded = calc_card_deduction(salary, credit_card, debit_card, cash_receipt,
                                           traditional_market, public_transport, culture)

            # 주택 관련 소득공제
            loan_ded = min(int(housing_loan_repay * 0.40), 4_000_000) if homeless and salary <= 50_000_000 else 0
            savings_ded = min(int(housing_savings * 0.40), 3_000_000) if homeless and salary <= 70_000_000 else 0
            combined_housing = min(loan_ded + savings_ded, 4_000_000)
            mg_limits = {"15년↑ 고정+비거치 (한도 1,800만)": 18_000_000, "15년↑ 고정 또는 비거치 (한도 1,500만)": 15_000_000,
                         "15년↑ 기타 (한도 500만)": 5_000_000, "10~15년 고정 또는 비거치 (한도 300만)": 3_000_000}
            mortgage_ded = min(mortgage_interest, mg_limits.get(mortgage_type, 18_000_000))
            housing_ded = combined_housing + mortgage_ded

            total_ded = personal_ded + pension_ded + health_ded + card_ded + housing_ded
            taxable = max(0, earned_income - total_ded)
            computed_tax = calc_income_tax(taxable)

            # 세액감면
            sme_exempt = min(int(computed_tax * 0.90), 2_000_000) if sme_youth else 0
            tax_after = max(0, computed_tax - sme_exempt)

            # 세액공제
            c_earned = calc_earned_income_credit(computed_tax, salary)
            c_insurance = int(min(insurance_premium, 1_000_000) * 0.12 + min(disabled_insurance, 1_000_000) * 0.15)

            # 의료비
            med_fam_cap = min(medical_family, 7_000_000)
            med_total = medical_self + medical_elderly + medical_infertility + med_fam_cap
            med_thresh = int(salary * 0.03)
            if med_total <= med_thresh:
                c_medical = 0
            else:
                non_infer = medical_self + medical_elderly + med_fam_cap
                if non_infer >= med_thresh:
                    c_medical = int((non_infer - med_thresh) * 0.15 + medical_infertility * 0.30)
                else:
                    c_medical = int(max(0, medical_infertility - (med_thresh - non_infer)) * 0.30)

            c_education = int((education_self + min(education_preschool, 3_000_000) + min(education_k12, 3_000_000) + min(education_university, 9_000_000)) * 0.15)

            don_desig_cap = min(donation_designated, int(earned_income * 0.30))
            don_total = donation_legal + don_desig_cap
            c_donation = int(don_total * 0.15) if don_total <= 10_000_000 else int(10_000_000 * 0.15 + (don_total - 10_000_000) * 0.30)

            pens_sv_cap = min(pension_saving, 6_000_000)
            pens_total = min(pens_sv_cap + irp, 9_000_000)
            pension_rate = 0.15 if salary <= 55_000_000 else 0.12
            c_pension = int(pens_total * pension_rate)

            c_rent = 0
            if rent > 0 and homeless and salary <= 70_000_000:
                rent_rate = 0.17 if salary <= 55_000_000 else 0.15
                c_rent = int(min(rent, 7_500_000) * rent_rate)

            # 자녀 세액공제
            if child_credit_count <= 0: c_child = 0
            elif child_credit_count == 1: c_child = 250_000
            elif child_credit_count == 2: c_child = 550_000
            else: c_child = 950_000 + (child_credit_count - 3) * 400_000
            birth_credit = 0
            if newborn_count >= 1: birth_credit += 300_000
            if newborn_count >= 2: birth_credit += 500_000
            for _ in range(max(0, newborn_count - 2)): birth_credit += 700_000
            c_child += birth_credit

            c_marriage = 500_000 if marriage else 0

            total_credit = c_earned + c_insurance + c_medical + c_education + c_donation + c_pension + c_rent + c_child + c_marriage
            determined = max(0, tax_after - total_credit)
            local_tax = int(determined * 0.10)
            refund_inc = tax_paid - determined
            refund_loc = local_tax_paid - local_tax
            total_refund = refund_inc + refund_loc

            # ── 결과 표시 ──
            if total_refund >= 0:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #2E75B6, #1F4E79); color: white; border-radius: 16px; padding: 32px; text-align: center; margin: 16px 0;">
                    <h3 style="margin-bottom: 8px;">🎉 예상 환급액</h3>
                    <h1 style="font-size: 2.5em; margin: 0;">+{total_refund:,}원</h1>
                    <p style="margin-top: 12px; opacity: 0.8;">소득세: {refund_inc:+,}원 / 지방소득세: {refund_loc:+,}원</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #C00000, #8B0000); color: white; border-radius: 16px; padding: 32px; text-align: center; margin: 16px 0;">
                    <h3 style="margin-bottom: 8px;">⚠️ 추가 납부 예상액</h3>
                    <h1 style="font-size: 2.5em; margin: 0;">{total_refund:,}원</h1>
                    <p style="margin-top: 12px; opacity: 0.8;">소득세: {refund_inc:+,}원 / 지방소득세: {refund_loc:+,}원</p>
                </div>
                """, unsafe_allow_html=True)

            # 계산 내역 표
            st.markdown("### 📋 계산 내역")
            rows_data = [
                ("총급여", salary), ("(-) 근로소득공제", emp_ded),
                ("**= 근로소득금액**", earned_income), ("", ""),
                ("(-) 인적공제", personal_ded), ("(-) 국민연금 공제", pension_ded),
                ("(-) 건강보험료 공제", health_ded), ("(-) 신용카드 등 공제", card_ded),
                ("(-) 주택 관련 소득공제", housing_ded),
                ("**= 과세표준**", taxable), ("", ""),
                ("**산출세액 (세율 적용)**", computed_tax),
                ("(-) 중소기업 청년 감면", sme_exempt),
                ("**= 감면 후 세액**", tax_after), ("", ""),
                ("(-) 근로소득 세액공제", c_earned), ("(-) 보험료 세액공제", c_insurance),
                ("(-) 의료비 세액공제", c_medical), ("(-) 교육비 세액공제", c_education),
                ("(-) 기부금 세액공제", c_donation), ("(-) 연금저축/IRP 세액공제", c_pension),
                ("(-) 월세 세액공제", c_rent), ("(-) 자녀 세액공제", c_child),
                ("(-) 혼인 세액공제", c_marriage),
                ("**= 결정세액**", determined), ("(+) 지방소득세 (10%)", local_tax), ("", ""),
                ("기납부 소득세", tax_paid), ("기납부 지방소득세", local_tax_paid),
                ("**= 최종 환급/추납액**", total_refund),
            ]

            for label, value in rows_data:
                if label == "" and value == "":
                    st.divider()
                    continue
                col_l, col_r = st.columns([3, 1])
                with col_l:
                    st.markdown(label)
                with col_r:
                    if isinstance(value, int):
                        color = "red" if value < 0 else ""
                        st.markdown(f"**{value:,}원**" if "=" in label or "최종" in label else f"{value:,}원")

            # 결과 다운로드
            result_lines = [f"=== 연말정산 계산 결과 ===", f"총급여: {salary:,}원",
                           f"결정세액: {determined:,}원", f"기납부 소득세: {tax_paid:,}원",
                           f"기납부 지방소득세: {local_tax_paid:,}원",
                           f"", f"최종 환급/추납액: {total_refund:+,}원",
                           f"  소득세: {refund_inc:+,}원", f"  지방소득세: {refund_loc:+,}원"]
            st.download_button("결과 저장 (txt)", data="\n".join(result_lines),
                              file_name="연말정산_결과.txt", mime="text/plain",
                              use_container_width=True)

    else:
        st.info("기본 정보와 지출 내역을 입력한 뒤 '계산하기' 버튼을 눌러주세요.")
