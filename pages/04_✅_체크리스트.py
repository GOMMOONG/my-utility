import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="체크리스트 - 마이 유틸리티", page_icon="✅", layout="centered")
apply_common_style()
check_password()
show_page_header("✅", "체크리스트", "할 일을 추가하고 완료하면 취소선으로 표시됩니다")

# ── 세션 상태 초기화 ──
if "checklist_items" not in st.session_state:
    st.session_state.checklist_items = []

items = st.session_state.checklist_items

# ── 새 항목 추가 ──
col_input, col_btn = st.columns([4, 1])
with col_input:
    new_text = st.text_input("할 일 입력", placeholder="할 일을 입력하세요", label_visibility="collapsed")
with col_btn:
    add_clicked = st.button("➕ 추가", use_container_width=True)

if add_clicked and new_text.strip():
    items.append({"text": new_text.strip(), "done": False})
    st.rerun()

# ── 항목 목록 표시 ──
if not items:
    st.markdown("""
    <div style="text-align: center; padding: 40px; color: #B2BEC3;">
        <p style="font-size: 1.2em;">할 일을 추가해보세요.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    for idx, item in enumerate(items):
        col_check, col_text, col_del = st.columns([0.5, 5, 0.5])

        with col_check:
            checked = st.checkbox("done", value=item["done"], key=f"check_{idx}", label_visibility="collapsed")
            if checked != item["done"]:
                items[idx]["done"] = checked
                st.rerun()

        with col_text:
            if item["done"]:
                st.markdown(f'<span style="text-decoration: line-through; color: #B2BEC3;">{item["text"]}</span>', unsafe_allow_html=True)
            else:
                st.markdown(item["text"])

        with col_del:
            if st.button("✕", key=f"del_{idx}"):
                items.pop(idx)
                st.rerun()

    st.markdown("")

    # 완료 항목 지우기
    done_count = sum(1 for it in items if it["done"])
    if done_count > 0:
        if st.button(f"완료 항목 지우기 ({done_count}개)", type="primary", use_container_width=True):
            st.session_state.checklist_items = [it for it in items if not it["done"]]
            st.rerun()

# ── 하단 안내 ──
st.divider()
st.caption("💡 이 체크리스트는 브라우저 탭을 닫으면 초기화됩니다. 아래에서 저장/불러오기를 할 수 있습니다.")

import json

col_save, col_load = st.columns(2)
with col_save:
    if items:
        st.download_button(
            "💾 데이터 저장",
            data=json.dumps(items, ensure_ascii=False, indent=2),
            file_name="checklist_data.json",
            mime="application/json",
            use_container_width=True,
        )

with col_load:
    uploaded = st.file_uploader("📂 데이터 불러오기", type="json", label_visibility="collapsed")
    if uploaded:
        try:
            loaded = json.loads(uploaded.read().decode("utf-8"))
            st.session_state.checklist_items = loaded
            st.rerun()
        except Exception:
            st.error("파일을 읽을 수 없습니다. 올바른 JSON 파일인지 확인해주세요.")
