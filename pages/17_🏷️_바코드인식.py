import streamlit as st
import pandas as pd
import os
import sys
from io import BytesIO
from datetime import datetime

# 상위 폴더에서 공용 모듈 가져오기
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password
from components.scanner import barcode_scanner

# ── 페이지 기본 설정 ──
st.set_page_config(
    page_title="바코드 인식 - 마이 유틸리티",
    page_icon="🏷️",
    layout="wide"
)
apply_common_style()
check_password()
show_page_header("🏷️", "바코드 인식", "바코드를 스캔해서 엑셀 파일과 대조합니다")


# ── 세션 상태 초기화 ──
if "scan_history" not in st.session_state:
    st.session_state.scan_history = []  # 스캔 이력 저장 리스트
if "excel_data" not in st.session_state:
    st.session_state.excel_data = None  # 업로드된 엑셀 데이터
if "last_timestamp" not in st.session_state:
    st.session_state.last_timestamp = 0  # 마지막 스캔 시각 (중복 방지용)


def create_sample_excel():
    """샘플 엑셀 양식을 만들어서 바이트로 반환하는 함수"""
    sample = pd.DataFrame({
        "상품명": ["콜라 500ml", "새우깡", "바나나우유", "삼각김밥 참치마요", "물 2L"],
        "바코드번호": ["8801234567890", "8802345678901", "8803456789012", "8804567890123", "8805678901234"],
        "카테고리": ["음료", "과자", "유제품", "식품", "음료"],
        "수량": [24, 12, 10, 30, 20],
        "비고": ["", "", "", "", ""],
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        sample.to_excel(writer, index=False, sheet_name="상품목록")
    return output.getvalue()


def process_barcode(barcode_value):
    """스캔된 바코드를 엑셀 데이터와 대조하는 함수.
    일치하면 비고란에 O를 표시하고 상품명을 반환한다."""
    df = st.session_state.excel_data
    if df is None:
        return None, "엑셀 파일을 먼저 업로드해주세요"

    # 바코드번호 열에서 검색 (문자열로 비교)
    barcode_str = str(barcode_value).strip()
    df["바코드번호"] = df["바코드번호"].astype(str).str.strip()
    match_mask = df["바코드번호"] == barcode_str

    if match_mask.any():
        # 일치하는 행의 비고란에 O 표시
        row_idx = match_mask.idxmax()
        product_name = df.loc[row_idx, "상품명"]
        df.loc[row_idx, "비고"] = "O"
        st.session_state.excel_data = df
        return product_name, None
    else:
        return None, f"바코드 [{barcode_str}]에 해당하는 상품을 찾을 수 없습니다"


def get_updated_excel():
    """현재 엑셀 데이터를 xlsx 파일(바이트)로 변환하는 함수"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        st.session_state.excel_data.to_excel(writer, index=False, sheet_name="상품목록")
    return output.getvalue()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 화면 구성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 1단계: 엑셀 파일 업로드 ──
st.markdown("### 📂 1단계: 엑셀 파일 준비")

col_upload, col_sample = st.columns([3, 1])

with col_sample:
    st.download_button(
        label="📥 샘플 양식 다운로드",
        data=create_sample_excel(),
        file_name="바코드_상품목록_양식.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

with col_upload:
    uploaded_file = st.file_uploader(
        "엑셀 파일(.xlsx)을 업로드하세요",
        type=["xlsx"],
        help="상품명, 바코드번호, 카테고리, 수량, 비고 열이 포함된 엑셀 파일",
    )

# 파일이 업로드되면 데이터 읽기
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        # 필수 열 확인
        required_cols = ["상품명", "바코드번호", "비고"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            st.error(f"엑셀 파일에 다음 열이 없습니다: {', '.join(missing)}")
            st.info("열 이름이 정확히 '상품명', '바코드번호', '비고'인지 확인해주세요")
            st.stop()

        # 비고 열이 비어있으면 빈 문자열로 채우기
        df["비고"] = df["비고"].fillna("")
        st.session_state.excel_data = df
    except Exception as e:
        st.error("엑셀 파일을 읽는 중 오류가 발생했습니다. 올바른 .xlsx 파일인지 확인해주세요.")
        st.stop()

# 엑셀 데이터가 있으면 표시
if st.session_state.excel_data is not None:
    df = st.session_state.excel_data

    # 진행률 표시
    total = len(df)
    checked = int((df["비고"] == "O").sum())
    st.markdown(f"**진행률: {checked} / {total}개 완료**")
    st.progress(checked / total if total > 0 else 0)

    # 데이터 테이블 (비고가 O인 행은 강조)
    st.dataframe(
        df.style.apply(
            lambda row: ["background-color: #E6FFF9" if row["비고"] == "O" else "" for _ in row],
            axis=1,
        ),
        use_container_width=True,
        height=250,
    )

    st.divider()

    # ── 2단계: 바코드 스캔 ──
    st.markdown("### 📷 2단계: 바코드 스캔")

    tab_camera, tab_manual = st.tabs(["카메라 스캔", "직접 입력"])

    with tab_camera:
        st.caption("아래 '스캔 시작' 버튼을 누르고, 바코드에 카메라를 비춰주세요")
        scan_result = barcode_scanner(key="scanner")

        # 스캔 결과 처리
        if scan_result is not None:
            barcode = scan_result.get("barcode", "")
            timestamp = scan_result.get("timestamp", 0)

            # 새로운 스캔인지 확인 (중복 방지)
            if timestamp > st.session_state.last_timestamp and barcode:
                st.session_state.last_timestamp = timestamp
                product_name, error_msg = process_barcode(barcode)
                now = datetime.now().strftime("%H:%M:%S")

                if product_name:
                    st.success(f"✅ **{product_name}** — 비고란에 O 표시 완료!")
                    st.session_state.scan_history.insert(0, {
                        "시각": now, "바코드": barcode, "상품명": product_name, "결과": "✅ 성공"
                    })
                else:
                    st.warning(f"⚠️ {error_msg}")
                    st.session_state.scan_history.insert(0, {
                        "시각": now, "바코드": barcode, "상품명": "-", "결과": "❌ 미등록"
                    })

    with tab_manual:
        st.caption("카메라가 안 될 때는 바코드 숫자를 직접 입력할 수 있습니다")
        with st.form("manual_form", clear_on_submit=True):
            manual_barcode = st.text_input(
                "바코드 번호 입력",
                placeholder="예: 8801234567890",
            )
            submitted = st.form_submit_button("🔍 대조하기", use_container_width=True)

        if submitted and manual_barcode:
            product_name, error_msg = process_barcode(manual_barcode)
            now = datetime.now().strftime("%H:%M:%S")

            if product_name:
                st.success(f"✅ **{product_name}** — 비고란에 O 표시 완료!")
                st.session_state.scan_history.insert(0, {
                    "시각": now, "바코드": manual_barcode, "상품명": product_name, "결과": "✅ 성공"
                })
            else:
                st.warning(f"⚠️ {error_msg}")
                st.session_state.scan_history.insert(0, {
                    "시각": now, "바코드": manual_barcode, "상품명": "-", "결과": "❌ 미등록"
                })

    st.divider()

    # ── 3단계: 스캔 이력 & 다운로드 ──
    col_history, col_download = st.columns([2, 1])

    with col_download:
        st.markdown("### 💾 수정된 엑셀 다운로드")
        st.download_button(
            label="📥 엑셀 파일 다운로드",
            data=get_updated_excel(),
            file_name=f"바코드_체크결과_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        if checked == total and total > 0:
            st.success("🎉 모든 상품 스캔 완료!")

    with col_history:
        st.markdown("### 📋 스캔 이력")
        if st.session_state.scan_history:
            st.dataframe(
                pd.DataFrame(st.session_state.scan_history),
                use_container_width=True,
                height=200,
            )
        else:
            st.info("아직 스캔한 바코드가 없습니다")

else:
    # 엑셀 파일이 아직 없을 때
    st.info("👆 위에서 엑셀 파일을 업로드하면 바코드 스캔을 시작할 수 있습니다")
