import streamlit as st
import random
import json
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password
from data.english_data import VOCABULARY, PHRASES

st.set_page_config(page_title="영어학습 - 마이 유틸리티", page_icon="📚", layout="centered")
apply_common_style()
check_password()

# ── 세션 상태 초기화 ──
if "eng_progress" not in st.session_state:
    st.session_state.eng_progress = {
        "word_scores": {},
        "study_dates": [],
        "total_correct": 0,
        "total_answered": 0,
    }
if "eng_card_index" not in st.session_state:
    st.session_state.eng_card_index = 0
if "eng_card_flipped" not in st.session_state:
    st.session_state.eng_card_flipped = False
if "eng_current_cat" not in st.session_state:
    st.session_state.eng_current_cat = list(VOCABULARY.keys())[0]
if "eng_quiz_state" not in st.session_state:
    st.session_state.eng_quiz_state = "ready"
if "eng_quiz_score" not in st.session_state:
    st.session_state.eng_quiz_score = 0
if "eng_quiz_total" not in st.session_state:
    st.session_state.eng_quiz_total = 0

progress = st.session_state.eng_progress

def record_word(word_en, correct):
    scores = progress["word_scores"]
    if word_en not in scores:
        scores[word_en] = {"correct": 0, "total": 0}
    scores[word_en]["total"] += 1
    if correct:
        scores[word_en]["correct"] += 1
        progress["total_correct"] += 1
    progress["total_answered"] += 1
    today = str(date.today())
    if today not in progress["study_dates"]:
        progress["study_dates"].append(today)

# ── 헤더 통계 ──
days = len(progress.get("study_dates", []))
total = progress.get("total_answered", 0)
correct = progress.get("total_correct", 0)
rate = int(correct / total * 100) if total > 0 else 0

show_page_header("📚", "영어 마스터", "왕초보 → 자막없이 넷플릭스·유튜브")
st.markdown(f"학습 **{days}일째** | 정답률 **{rate}%** | 총 **{total}문제**")

# ── 탭 구성 ──
tab_home, tab_words, tab_phrases, tab_quiz, tab_stats = st.tabs(
    ["🏠 홈", "📇 단어카드", "💬 표현", "❓ 퀴즈", "📊 통계"]
)

# ──────────────────────────────────────
#  홈 탭
# ──────────────────────────────────────
with tab_home:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
                color: white; border-radius: 16px; padding: 24px; margin-bottom: 16px;">
        <h3 style="margin:0;">어서 오세요! 오늘도 한 걸음 더 나아가요</h3>
    </div>
    """, unsafe_allow_html=True)

    # 학습 로드맵
    st.markdown("#### 학습 로드맵")
    stages = [
        ("1단계", "기초 단어 120개 외우기", "🌱"),
        ("2단계", "감정·상황 표현 70개 익히기", "📗"),
        ("3단계", "드라마 단골 표현 마스터", "🎬"),
        ("4단계", "자막 없이 넷플릭스 시청!", "🎉"),
    ]
    cols = st.columns(4)
    for i, (stage, desc, icon) in enumerate(stages):
        with cols[i]:
            st.markdown(f"""
            <div class="app-card" style="text-align:center; min-height:120px;">
                <div style="font-size:2em;">{icon}</div>
                <p style="font-weight:bold;">{stage}</p>
                <p style="font-size:0.85em; color:#636E72;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    # 오늘의 추천 단어
    st.markdown("#### 오늘의 추천 단어")
    all_words = []
    for words in VOCABULARY.values():
        all_words.extend(words)

    weak = [w for w in all_words
            if w["en"] in progress["word_scores"]
            and progress["word_scores"][w["en"]]["correct"]
                < progress["word_scores"][w["en"]]["total"]]
    daily = weak[:5] if len(weak) >= 5 else random.sample(all_words, min(5, len(all_words)))

    for word in daily:
        score = progress["word_scores"].get(word["en"], {})
        t = score.get("total", 0)
        rate_text = f"정답률 {int(score['correct']/t*100)}%" if t > 0 else "미학습"

        st.markdown(f"""
        <div style="background:#1a1a2e; padding:10px 16px; border-radius:8px; margin:4px 0;
                    display:flex; justify-content:space-between; align-items:center;">
            <span><b style="color:white;">{word['en'].upper()}</b>
            <span style="color:#a0a0b0;"> [{word['pron']}] {word['ko']}</span></span>
            <span style="color:#a0a0b0; font-size:0.85em;">{rate_text}</span>
        </div>
        """, unsafe_allow_html=True)

# ──────────────────────────────────────
#  단어 카드 탭
# ──────────────────────────────────────
with tab_words:
    cat = st.selectbox("카테고리 선택", ["전체 단어"] + list(VOCABULARY.keys()), key="word_cat_select")

    if cat == "전체 단어":
        current_words = []
        for words in VOCABULARY.values():
            current_words.extend(words)
    else:
        current_words = list(VOCABULARY.get(cat, []))

    if not current_words:
        st.warning("단어가 없습니다.")
    else:
        idx = st.session_state.eng_card_index % len(current_words)
        word = current_words[idx]

        st.caption(f"{idx + 1} / {len(current_words)}")

        # 플래시 카드
        if not st.session_state.eng_card_flipped:
            # 앞면 (영어)
            st.markdown(f"""
            <div style="background:#1a1a2e; border-radius:16px; padding:40px; text-align:center;
                        min-height:200px; display:flex; flex-direction:column; justify-content:center;">
                <p style="color:#555566; font-size:0.9em;">카드를 클릭하면 뒤집혀요</p>
                <h1 style="color:white; font-size:2.5em; margin:16px 0;">{word['en'].upper()}</h1>
                <p style="color:#a0a0b0; font-size:1.1em;">[{word['pron']}]</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 뒷면 (한국어 뜻 + 예문)
            st.markdown(f"""
            <div style="background:#0d3b66; border-radius:16px; padding:40px; text-align:center;
                        min-height:200px; display:flex; flex-direction:column; justify-content:center;">
                <h1 style="color:#FFD700; font-size:2em; margin:8px 0;">{word['ko']}</h1>
                <p style="color:#a0d8ff;">[ {word['en']} ] [{word['pron']}]</p>
                <p style="color:#88aacc; margin-top:16px;">예문: {word['ex_en']}<br>→ {word['ex_ko']}</p>
            </div>
            """, unsafe_allow_html=True)

        # 버튼들
        col_flip, col_hard, col_know, col_nav = st.columns([1, 1, 1, 1])
        with col_flip:
            if st.button("🔄 뒤집기", use_container_width=True):
                st.session_state.eng_card_flipped = not st.session_state.eng_card_flipped
                st.rerun()
        with col_hard:
            if st.button("😣 어려워요", use_container_width=True):
                record_word(word["en"], False)
                st.session_state.eng_card_index = (idx + 1) % len(current_words)
                st.session_state.eng_card_flipped = False
                st.rerun()
        with col_know:
            if st.button("😊 알아요!", use_container_width=True):
                record_word(word["en"], True)
                st.session_state.eng_card_index = (idx + 1) % len(current_words)
                st.session_state.eng_card_flipped = False
                st.rerun()
        with col_nav:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("◀", use_container_width=True, key="prev_card"):
                    st.session_state.eng_card_index = (idx - 1) % len(current_words)
                    st.session_state.eng_card_flipped = False
                    st.rerun()
            with c2:
                if st.button("▶", use_container_width=True, key="next_card"):
                    st.session_state.eng_card_index = (idx + 1) % len(current_words)
                    st.session_state.eng_card_flipped = False
                    st.rerun()

# ──────────────────────────────────────
#  표현 탭
# ──────────────────────────────────────
with tab_phrases:
    phrase_cat = st.selectbox("카테고리 선택", ["전체 표현"] + list(PHRASES.keys()), key="phrase_cat_select")

    if phrase_cat == "전체 표현":
        items = []
        for phrases in PHRASES.values():
            items.extend(phrases)
    else:
        items = PHRASES.get(phrase_cat, [])

    for p in items:
        st.markdown(f"""
        <div style="background:#1a1a2e; border-radius:12px; padding:16px; margin:8px 0;">
            <p style="color:#FFD700; font-size:1.1em; font-weight:bold; margin-bottom:4px;">"{p['phrase']}"</p>
            <p style="color:white; margin-bottom:4px;">→ {p['meaning']}</p>
            <p style="color:#7070a0; font-size:0.9em; margin-bottom:2px;">{p['usage']}</p>
            <p style="color:#555588; font-size:0.9em;">예) {p['example']}</p>
        </div>
        """, unsafe_allow_html=True)

# ──────────────────────────────────────
#  퀴즈 탭
# ──────────────────────────────────────
with tab_quiz:
    quiz_type = st.radio("퀴즈 유형", ["영어 → 한국어", "한국어 → 영어"], horizontal=True, key="quiz_type_radio")

    all_words_quiz = []
    for words in VOCABULARY.values():
        all_words_quiz.extend(words)

    if st.session_state.eng_quiz_state == "ready":
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#636E72;">
            <p style="font-size:1.3em;">아래 버튼을 눌러 퀴즈를 시작하세요!</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎯 퀴즈 시작", type="primary", use_container_width=True):
            st.session_state.eng_quiz_state = "question"
            st.session_state.eng_quiz_score = 0
            st.session_state.eng_quiz_total = 0
            st.rerun()

    elif st.session_state.eng_quiz_state == "question":
        st.markdown(f"점수: **{st.session_state.eng_quiz_score} / {st.session_state.eng_quiz_total}**")

        # 문제 생성 (seed로 안정적 출력)
        if "eng_quiz_correct" not in st.session_state:
            correct_word = random.choice(all_words_quiz)
            pool = [w for w in all_words_quiz if w["en"] != correct_word["en"]]
            wrongs = random.sample(pool, min(3, len(pool)))
            options = [correct_word] + wrongs
            random.shuffle(options)
            st.session_state.eng_quiz_correct = correct_word
            st.session_state.eng_quiz_options = options

        correct_word = st.session_state.eng_quiz_correct
        options = st.session_state.eng_quiz_options

        # 문제 표시
        if quiz_type == "영어 → 한국어":
            q_text = correct_word["en"].upper()
            q_sub = f'[{correct_word["pron"]}]'
        else:
            q_text = correct_word["ko"]
            q_sub = ""

        st.markdown(f"""
        <div style="background:#16213e; border-radius:16px; padding:32px; text-align:center; margin:16px 0;">
            <p style="color:#a0a0b0;">다음 단어의 뜻은?</p>
            <h2 style="color:white; font-size:2em; margin:12px 0;">{q_text}</h2>
            <p style="color:#7070a0;">{q_sub}</p>
            <p style="color:#404060; font-size:0.9em;">힌트: "{correct_word['ex_en']}"</p>
        </div>
        """, unsafe_allow_html=True)

        # 4개 보기
        cols = st.columns(2)
        for i, opt in enumerate(options):
            if quiz_type == "영어 → 한국어":
                opt_text = opt["ko"]
            else:
                opt_text = opt["en"].upper()

            is_right = (opt["en"] == correct_word["en"])
            with cols[i % 2]:
                if st.button(opt_text, key=f"quiz_opt_{i}", use_container_width=True):
                    st.session_state.eng_quiz_total += 1
                    record_word(correct_word["en"], is_right)
                    if is_right:
                        st.session_state.eng_quiz_score += 1
                        st.session_state.eng_quiz_result = "correct"
                    else:
                        st.session_state.eng_quiz_result = "wrong"
                    st.session_state.eng_quiz_state = "result"
                    st.rerun()

    elif st.session_state.eng_quiz_state == "result":
        st.markdown(f"점수: **{st.session_state.eng_quiz_score} / {st.session_state.eng_quiz_total}**")

        correct_word = st.session_state.eng_quiz_correct
        is_correct = st.session_state.eng_quiz_result == "correct"

        if is_correct:
            st.success("🎉 정답!")
        else:
            st.error(f"❌ 오답! 정답: {correct_word['en']} = {correct_word['ko']}")

        st.markdown(f"""
        <div style="text-align:center; padding:16px; color:#888899;">
            "{correct_word['ex_en']}"<br>→ {correct_word['ex_ko']}
        </div>
        """, unsafe_allow_html=True)

        if st.button("다음 문제 →", type="primary", use_container_width=True):
            st.session_state.eng_quiz_state = "question"
            if "eng_quiz_correct" in st.session_state:
                del st.session_state.eng_quiz_correct
            if "eng_quiz_options" in st.session_state:
                del st.session_state.eng_quiz_options
            st.rerun()

# ──────────────────────────────────────
#  통계 탭
# ──────────────────────────────────────
with tab_stats:
    st.markdown("### 나의 학습 통계")

    total_ans = progress.get("total_answered", 0)
    total_cor = progress.get("total_correct", 0)
    stat_rate = int(total_cor / total_ans * 100) if total_ans > 0 else 0
    stat_days = len(progress.get("study_dates", []))
    learned = len(progress.get("word_scores", {}))

    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    mc1.metric("학습 일수", f"{stat_days}일")
    mc2.metric("총 문제 수", f"{total_ans}문제")
    mc3.metric("정답 수", f"{total_cor}개")
    mc4.metric("정답률", f"{stat_rate}%")
    mc5.metric("학습 단어", f"{learned}개")

    # 레벨 가이드
    st.markdown("#### 학습 수준 가이드")
    levels = [
        (20, "입문", "자주 쓰는 기초 단어를 배우기 시작하는 단계"),
        (50, "초보 탈출", "짧은 영어 문장을 이해할 수 있는 단계"),
        (80, "기초 완성", "드라마 핵심 장면의 대화를 알아듣기 시작하는 단계"),
        (100, "중급 시작", "대부분의 일상 표현을 이해하는 단계"),
        (120, "단어 마스터", "이 앱의 모든 단어를 학습한 단계!"),
    ]
    for threshold, level, desc in levels:
        done = learned >= threshold
        icon = "✅" if done else "⬜"
        color = "" if done else "color: #999;"
        st.markdown(f"{icon} **{level}** ({threshold}단어 이상) — <span style='{color}'>{desc}</span>", unsafe_allow_html=True)

    # 취약 단어
    st.markdown("#### 더 연습이 필요한 단어")
    word_dict = {}
    for words in VOCABULARY.values():
        for w in words:
            word_dict[w["en"]] = w

    weak_words = []
    for en, sc in progress.get("word_scores", {}).items():
        if sc["total"] > 0 and en in word_dict:
            acc = sc["correct"] / sc["total"]
            if acc < 0.6:
                weak_words.append((acc, word_dict[en]))
    weak_words.sort(key=lambda x: x[0])

    if not weak_words:
        st.info("아직 데이터가 없거나, 모두 잘 기억하고 있어요!")
    else:
        for acc, word in weak_words[:10]:
            st.markdown(f"- **{word['en'].upper()}** = {word['ko']} — 정답률 {int(acc*100)}%")

# ── 데이터 저장/불러오기 ──
st.divider()
st.caption("💡 학습 진도는 브라우저 탭을 닫으면 초기화됩니다. 아래에서 저장/불러오기를 할 수 있습니다.")

col_save, col_load = st.columns(2)
with col_save:
    st.download_button(
        "💾 진도 저장",
        data=json.dumps(progress, ensure_ascii=False, indent=2),
        file_name="english_progress.json",
        mime="application/json",
        use_container_width=True,
    )
with col_load:
    uploaded = st.file_uploader("📂 진도 불러오기", type="json", label_visibility="collapsed", key="eng_upload")
    if uploaded:
        try:
            loaded = json.loads(uploaded.read().decode("utf-8"))
            st.session_state.eng_progress = loaded
            st.rerun()
        except Exception:
            st.error("파일을 읽을 수 없습니다.")
