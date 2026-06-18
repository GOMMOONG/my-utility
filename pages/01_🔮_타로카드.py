import streamlit as st
import random
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password
from data.tarot_data import ALL_CARDS

st.set_page_config(page_title="타로카드 - 마이 유틸리티", page_icon="🔮", layout="centered")
apply_common_style()
check_password()

# ── 카드 뽑기 함수 (원본 그대로 재사용) ──
def draw_cards(count):
    chosen = random.sample(ALL_CARDS, count)
    return [(card, random.choice(["정방향", "역방향"])) for card in chosen]

# ── 세션 상태 초기화 ──
if "tarot_screen" not in st.session_state:
    st.session_state.tarot_screen = "start"
if "tarot_result" not in st.session_state:
    st.session_state.tarot_result = None
if "tarot_mode" not in st.session_state:
    st.session_state.tarot_mode = None
if "tarot_deck" not in st.session_state:
    st.session_state.tarot_deck = None
if "tarot_chosen" not in st.session_state:
    st.session_state.tarot_chosen = []

# ── 시작 화면 ──
if st.session_state.tarot_screen == "start":
    show_page_header("🔮", "타로카드 점", "마음속으로 궁금한 것을 떠올리며 원하는 점법을 골라 주세요")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="app-card" style="text-align: center;">
            <div style="font-size: 3em;">✨</div>
            <h3>오늘의 카드</h3>
            <p style="color: #636E72;">카드 1장을 뽑아<br>오늘 하루의 흐름을 살펴봅니다</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("카드 1장 뽑기", use_container_width=True, key="btn_one"):
            st.session_state.tarot_mode = 1
            st.session_state.tarot_deck = draw_cards(16)
            st.session_state.tarot_chosen = []
            st.session_state.tarot_screen = "select"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="app-card" style="text-align: center;">
            <div style="font-size: 3em;">🌙</div>
            <h3>3장 스프레드</h3>
            <p style="color: #636E72;">카드 3장을 뽑아<br>과거-현재-미래를 살펴봅니다</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("카드 3장 뽑기", use_container_width=True, key="btn_three"):
            st.session_state.tarot_mode = 3
            st.session_state.tarot_deck = draw_cards(16)
            st.session_state.tarot_chosen = []
            st.session_state.tarot_screen = "select"
            st.rerun()

# ── 카드 선택 화면 ──
elif st.session_state.tarot_screen == "select":
    needed = st.session_state.tarot_mode
    title = "✨ 카드 1장을 골라주세요" if needed == 1 else "🌙 카드 3장을 순서대로 골라주세요"
    show_page_header("🔮", title)

    chosen_count = len(st.session_state.tarot_chosen)
    st.info(f"선택한 카드: {chosen_count} / {needed}")

    if needed == 3:
        st.caption("먼저 고른 카드부터 차례로 과거 → 현재 → 미래가 됩니다")

    # 카드 뒷면 4x4 격자 표시
    for row in range(4):
        cols = st.columns(4)
        for col_idx in range(4):
            card_index = row * 4 + col_idx
            with cols[col_idx]:
                already_chosen = card_index in [c[0] for c in st.session_state.tarot_chosen]
                if already_chosen:
                    order = [i for i, c in enumerate(st.session_state.tarot_chosen) if c[0] == card_index][0] + 1
                    st.button(f"{order}번", key=f"card_{card_index}", disabled=True, use_container_width=True)
                else:
                    if st.button("🔮", key=f"card_{card_index}", use_container_width=True):
                        st.session_state.tarot_chosen.append((card_index, st.session_state.tarot_deck[card_index]))
                        if len(st.session_state.tarot_chosen) >= needed:
                            st.session_state.tarot_screen = "result"
                        st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("처음으로", use_container_width=True):
            st.session_state.tarot_screen = "start"
            st.rerun()
    with col_b:
        if st.button("다시 섞기", use_container_width=True):
            st.session_state.tarot_deck = draw_cards(16)
            st.session_state.tarot_chosen = []
            st.rerun()

# ── 결과 화면 ──
elif st.session_state.tarot_screen == "result":
    chosen_cards = st.session_state.tarot_chosen
    mode = st.session_state.tarot_mode

    if mode == 1:
        show_page_header("✨", "오늘의 카드")
        _idx, (card, orientation) = chosen_cards[0]
        meaning = card["upright"] if orientation == "정방향" else card["reversed"]
        color = "#6C5CE7" if orientation == "정방향" else "#E17055"

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1A1330 0%, #2A2147 100%);
                    color: white; border-radius: 16px; padding: 32px; margin: 16px 0;">
            <h2 style="color: #C9A8FF; margin-bottom: 4px;">{card['name']}</h2>
            <p style="color: {color}; font-size: 1.1em; margin-bottom: 16px;">[{orientation}]</p>
            <p style="font-size: 1.05em; line-height: 1.7;">{meaning}</p>
        </div>
        """, unsafe_allow_html=True)

        result_text = f"=== 오늘의 카드 ===\n{card['name']} - {orientation}\n\n{meaning}"

    else:
        show_page_header("🌙", "3장 스프레드 (과거-현재-미래)")
        labels = ["과거", "현재", "미래"]
        label_icons = ["⏪", "▶️", "⏩"]
        result_lines = ["=== 3장 스프레드 (과거-현재-미래) ==="]

        for i, (card_idx, (card, orientation)) in enumerate(chosen_cards):
            meaning = card["upright"] if orientation == "정방향" else card["reversed"]
            color = "#C9A8FF" if orientation == "정방향" else "#FF8A8A"

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1A1330 0%, #2A2147 100%);
                        color: white; border-radius: 16px; padding: 24px; margin: 12px 0;">
                <p style="color: #A29BFE; font-size: 0.9em; margin-bottom: 4px;">{label_icons[i]} {labels[i]}</p>
                <h3 style="color: #C9A8FF; margin-bottom: 4px;">{card['name']}</h3>
                <p style="color: {color}; margin-bottom: 12px;">[{orientation}]</p>
                <p style="font-size: 1em; line-height: 1.7;">{meaning}</p>
            </div>
            """, unsafe_allow_html=True)

            result_lines.append(f"\n[{labels[i]}] {card['name']} - {orientation}")
            result_lines.append(meaning)

        result_text = "\n".join(result_lines)

    st.markdown("")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("다시 뽑기", use_container_width=True):
            st.session_state.tarot_screen = "start"
            st.rerun()
    with col_b:
        st.download_button(
            "결과 저장 (txt)",
            data=result_text,
            file_name="타로카드_결과.txt",
            mime="text/plain",
            use_container_width=True,
        )
