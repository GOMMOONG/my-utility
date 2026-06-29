import streamlit as st
import sys, os, copy, random
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="바둑 - 마이 유틸리티", page_icon="⚫", layout="wide")
apply_common_style()
check_password()
show_page_header("⚫", "바둑 입문", "튜토리얼부터 AI 대국까지 — 바둑을 처음부터 배워보세요")

BOARD_SIZE = 9

# ============================================================
# 바둑 게임 로직
# ============================================================

class GoGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = 1   # 1=흑, -1=백
        self.captured = {1: 0, -1: 0}
        self.ko_point = None
        self.consecutive_passes = 0
        self.last_move = None
        self.game_over = False

    def find_group(self, r, c, board=None):
        if board is None:
            board = self.board
        color = board[r][c]
        if color == 0:
            return set(), set()
        visited = set()
        liberties = set()
        queue = deque([(r, c)])
        visited.add((r, c))
        while queue:
            cr, cc = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = cr + dr, cc + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if (nr, nc) not in visited:
                        if board[nr][nc] == color:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
                        elif board[nr][nc] == 0:
                            liberties.add((nr, nc))
        return visited, liberties

    def is_valid_move(self, r, c):
        if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
            return False, "범위 밖"
        if self.board[r][c] != 0:
            return False, "이미 돌이 있음"
        if self.ko_point == (r, c):
            return False, "패"

        test = copy.deepcopy(self.board)
        test[r][c] = self.current_player
        opponent = -self.current_player

        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and test[nr][nc] == opponent:
                grp, libs = self.find_group(nr, nc, test)
                if not libs:
                    for gr, gc in grp:
                        test[gr][gc] = 0

        _, my_libs = self.find_group(r, c, test)
        if not my_libs:
            return False, "자살수"
        return True, ""

    def place_stone(self, r, c):
        ok, reason = self.is_valid_move(r, c)
        if not ok:
            return False, reason

        self.board[r][c] = self.current_player
        opponent = -self.current_player
        captured_stones = []

        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and self.board[nr][nc] == opponent:
                grp, libs = self.find_group(nr, nc)
                if not libs:
                    for gr, gc in grp:
                        self.board[gr][gc] = 0
                        captured_stones.append((gr, gc))

        self.captured[self.current_player] += len(captured_stones)

        if len(captured_stones) == 1:
            _, my_libs = self.find_group(r, c)
            self.ko_point = captured_stones[0] if not my_libs else None
        else:
            self.ko_point = None

        self.last_move = (r, c)
        self.consecutive_passes = 0
        self.current_player = opponent
        return True, ""

    def pass_turn(self):
        self.consecutive_passes += 1
        self.ko_point = None
        self.last_move = None
        self.current_player = -self.current_player
        if self.consecutive_passes >= 2:
            self.game_over = True

    def calculate_score(self):
        territory = {1: 0, -1: 0}
        visited = set()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == 0 and (r, c) not in visited:
                    region, borders = set(), set()
                    queue = deque([(r, c)])
                    region.add((r, c))
                    while queue:
                        cr, cc = queue.popleft()
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                                if (nr, nc) not in region:
                                    if self.board[nr][nc] == 0:
                                        region.add((nr, nc))
                                        queue.append((nr, nc))
                                    else:
                                        borders.add(self.board[nr][nc])
                    visited |= region
                    if len(borders) == 1:
                        territory[borders.pop()] += len(region)

        black = sum(1 for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.board[r][c] == 1)
        white = sum(1 for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.board[r][c] == -1)
        return territory[1] + black, territory[-1] + white + 6.5

    def get_valid_moves(self):
        return [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.is_valid_move(r, c)[0]]


class GoAI:
    def __init__(self, game, level=1):
        self.game = game
        self.level = level

    def move(self):
        moves = self.game.get_valid_moves()
        if not moves:
            self.game.pass_turn()
            return None
        if self.level == 1:
            return self._beginner(moves)
        elif self.level == 2:
            return self._intermediate(moves)
        else:
            return self._advanced(moves)

    def _is_eye(self, r, c):
        color = self.game.current_player
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if self.game.board[nr][nc] != color:
                    return False
        return True

    def _beginner(self, moves):
        non_eye = [m for m in moves if not self._is_eye(*m)]
        chosen = random.choice(non_eye) if non_eye else random.choice(moves)
        self.game.place_stone(*chosen)
        return chosen

    def _intermediate(self, moves):
        for r, c in moves:
            test = copy.deepcopy(self.game.board)
            test[r][c] = self.game.current_player
            opponent = -self.game.current_player
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and test[nr][nc] == opponent:
                    grp, libs = self.game.find_group(nr, nc, test)
                    if not libs:
                        self.game.place_stone(r, c)
                        return (r, c)
        return self._beginner(moves)

    def _advanced(self, moves):
        center = BOARD_SIZE // 2
        stars = {(2, 2), (2, 6), (4, 4), (6, 2), (6, 6)}

        def score(r, c):
            s = (center - abs(r - center)) + (center - abs(c - center))
            if (r, c) in stars:
                s += 5
            return s

        scored = sorted(moves, key=lambda m: score(*m), reverse=True)
        chosen = random.choice(scored[:max(1, len(scored) // 3)])
        self.game.place_stone(*chosen)
        return chosen


# ============================================================
# 튜토리얼 데이터
# ============================================================

LESSONS = [
    {
        "title": "바둑판과 돌",
        "text": "바둑은 줄이 그려진 바둑판 위에서 두 명이 번갈아 돌을 놓는 게임입니다.\n\n⚫ 흑(검정)과 ⚪ 백(흰색) 중 하나를 골라 교차점에 돌을 놓습니다.\n\n여기서는 9×9 판으로 배워볼게요!",
        "stones": {},
        "marks": [],
    },
    {
        "title": "돌의 숨구멍 — 활로",
        "text": "돌은 상하좌우 빈 칸을 '활로'라고 합니다.\n\n아래 흑돌의 활로는 4개입니다. (초록 표시)\n\n활로가 모두 막히면 돌이 잡힙니다!",
        "stones": {(4, 4): 1},
        "marks": [(3, 4), (5, 4), (4, 3), (4, 5)],
    },
    {
        "title": "돌 잡기",
        "text": "상대 돌의 모든 활로를 막으면 그 돌을 잡을 수 있습니다.\n\n아래처럼 백돌 하나를 흑돌 넷이 둘러싸면 백돌이 잡힙니다.\n\n잡힌 돌은 판에서 없어지고 나중에 점수가 됩니다.",
        "stones": {(4, 4): -1, (3, 4): 1, (5, 4): 1, (4, 3): 1, (4, 5): 1},
        "marks": [],
    },
    {
        "title": "연결된 돌 그룹",
        "text": "같은 색 돌이 상하좌우로 붙어 있으면 하나의 그룹이 됩니다.\n\n그룹 전체가 포위되어야만 잡힙니다.\n\n아래 흑돌 셋은 한 그룹이에요.",
        "stones": {(4, 3): 1, (4, 4): 1, (4, 5): 1},
        "marks": [(3, 3), (3, 4), (3, 5), (4, 2), (4, 6), (5, 3), (5, 4), (5, 5)],
    },
    {
        "title": "집 — 점수",
        "text": "내 돌로 둘러싼 빈 칸이 '집'이 됩니다.\n\n게임이 끝날 때 집이 더 많은 사람이 이깁니다.\n\n아래는 흑이 만든 집입니다. (초록 표시)",
        "stones": {(2, 2): 1, (2, 3): 1, (2, 4): 1, (3, 2): 1, (3, 4): 1, (4, 2): 1, (4, 3): 1, (4, 4): 1},
        "marks": [(3, 3)],
    },
    {
        "title": "패 규칙",
        "text": "같은 모양이 반복되는 것을 막는 규칙이 '패'입니다.\n\n한쪽이 돌을 잡았을 때, 상대방이 즉시 그 돌을 되잡을 수 없어요.\n\n다른 곳에 한 번 두고 나서야 되잡을 수 있습니다.",
        "stones": {(4, 4): 1, (4, 3): -1, (3, 4): -1, (5, 4): -1, (4, 5): -1},
        "marks": [],
    },
    {
        "title": "자살수 금지",
        "text": "활로가 없는 곳에 돌을 놓을 수 없습니다.\n\n단, 상대 돌을 잡게 되는 경우는 놓을 수 있어요!\n\n초록 표시된 곳은 자살수라 놓을 수 없습니다.",
        "stones": {(0, 1): 1, (1, 0): 1, (1, 1): -1, (0, 2): -1},
        "marks": [(0, 0)],
    },
    {
        "title": "두 눈 — 삶",
        "text": "'두 눈'을 가진 돌 그룹은 절대 잡히지 않습니다!\n\n눈이란 내 돌로 둘러싼 빈 칸인데, 두 개 이상이면 살아있는 돌입니다.\n\n상대는 자살수이기 때문에 눈 안에 돌을 놓을 수 없어요.",
        "stones": {(1, 1): 1, (1, 2): 1, (1, 3): 1, (2, 1): 1, (2, 3): 1, (3, 1): 1, (3, 2): 1, (3, 3): 1},
        "marks": [(2, 2)],
    },
    {
        "title": "게임 끝내기",
        "text": "두 사람이 연속으로 '패스'를 하면 게임이 끝납니다.\n\n더 놓을 곳이 없다고 판단될 때 패스합니다.\n\n그 다음 집과 잡은 돌을 세어 점수를 계산합니다.\n백은 덤(6.5점)을 받습니다.",
        "stones": {},
        "marks": [],
    },
    {
        "title": "이제 직접 두어보세요!",
        "text": "축하합니다! 바둑의 기본 규칙을 모두 배웠어요 🎉\n\n이제 'AI 대국' 탭에서 실제로 두어보세요.\n\n처음엔 입문 AI와 두어보고, 익숙해지면 초급, 중급으로 도전해보세요!",
        "stones": {},
        "marks": [],
    },
]

# ============================================================
# 사활 문제 데이터
# ============================================================

TSUMEGO = [
    {
        "title": "백돌 1개를 잡으세요",
        "level": "★☆☆ 입문",
        "task": "⚫ 흑을 놓아 백돌 1개를 잡으세요.",
        "player": 1,
        "stones": {(3, 4): 1, (4, 3): 1, (4, 5): 1, (4, 4): -1},
        "answers": [(5, 4)],
        "hint": "백돌(가운데)의 남은 활로가 어디인지 찾아보세요.",
        "explain": "백돌의 마지막 활로를 막아 잡습니다!",
    },
    {
        "title": "귀의 백돌을 잡으세요",
        "level": "★☆☆ 입문",
        "task": "⚫ 흑을 놓아 귀(모서리)의 백돌을 잡으세요.",
        "player": 1,
        "stones": {(0, 0): -1, (0, 1): -1, (1, 0): 1, (1, 1): 1, (1, 2): 1},
        "answers": [(0, 2)],
        "hint": "백돌 그룹의 마지막 활로를 막아보세요.",
        "explain": "모서리 백돌 2개의 마지막 활로를 막아 잡습니다!",
    },
    {
        "title": "흑돌을 살리세요",
        "level": "★☆☆ 입문",
        "task": "⚫ 흑을 놓아 위기의 흑돌 그룹을 살리세요.",
        "player": 1,
        "stones": {(3, 4): -1, (5, 4): -1, (4, 3): -1, (4, 4): 1},
        "answers": [(4, 5)],
        "hint": "흑돌의 유일한 남은 활로 방향을 찾아보세요.",
        "explain": "활로를 추가해 흑 그룹이 살아납니다!",
    },
    {
        "title": "변의 백돌을 잡으세요",
        "level": "★★☆ 초급",
        "task": "⚫ 흑을 놓아 변(가장자리)의 백돌들을 잡으세요.",
        "player": 1,
        "stones": {(0, 3): -1, (0, 4): -1, (1, 3): 1, (1, 4): 1, (0, 2): 1},
        "answers": [(0, 5)],
        "hint": "백돌 그룹의 오른쪽 활로를 막아보세요.",
        "explain": "가장자리 백돌 2개를 한꺼번에 잡습니다!",
    },
    {
        "title": "흑 2개를 살리세요",
        "level": "★★☆ 초급",
        "task": "⚫ 흑을 놓아 포위된 흑돌 2개를 살리세요.",
        "player": 1,
        "stones": {(4, 4): 1, (4, 5): 1, (3, 4): -1, (5, 4): -1, (4, 3): -1, (3, 5): -1, (5, 5): -1},
        "answers": [(4, 6)],
        "hint": "흑 그룹의 유일한 탈출 방향을 찾아보세요.",
        "explain": "활로를 확보해 흑돌 2개가 살아납니다!",
    },
    {
        "title": "백 3개를 잡으세요",
        "level": "★★☆ 초급",
        "task": "⚫ 흑을 놓아 백돌 3개를 한번에 잡으세요.",
        "player": 1,
        "stones": {
            (4, 3): -1, (4, 4): -1, (4, 5): -1,
            (3, 3): 1, (3, 4): 1, (3, 5): 1,
            (5, 3): 1, (5, 5): 1, (4, 2): 1, (5, 4): 1,
        },
        "answers": [(4, 6)],
        "hint": "백 그룹의 마지막 활로 위치를 확인하세요.",
        "explain": "백돌 3개의 마지막 활로를 막아 한번에 잡습니다!",
    },
]

# ============================================================
# SVG 바둑판 렌더러
# ============================================================

def render_board_svg(board, last_move=None, marks=None, hint=None,
                     player_mark=None, mark_color=None):
    N = BOARD_SIZE
    CELL = 52
    MARGIN = 44
    R = 21
    size = MARGIN * 2 + (N - 1) * CELL
    end = MARGIN + (N - 1) * CELL

    lines = [
        f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{size}" height="{size}" fill="#DEB887" rx="4"/>',
    ]

    for i in range(N):
        x = MARGIN + i * CELL
        lines.append(f'<line x1="{x}" y1="{MARGIN}" x2="{x}" y2="{end}" stroke="#8B4513" stroke-width="1.2"/>')
        lines.append(f'<line x1="{MARGIN}" y1="{x}" x2="{end}" y2="{x}" stroke="#8B4513" stroke-width="1.2"/>')

    for pr, pc in ((2, 2), (2, 6), (4, 4), (6, 2), (6, 6)):
        lines.append(f'<circle cx="{MARGIN+pc*CELL}" cy="{MARGIN+pr*CELL}" r="4" fill="#5a3a1a"/>')

    for i in range(N):
        x = MARGIN + i * CELL
        lines.append(f'<text x="{x}" y="{MARGIN-14}" text-anchor="middle" font-size="13" font-family="Arial" fill="#5a3a1a">{chr(65+i)}</text>')
        lines.append(f'<text x="{MARGIN-20}" y="{MARGIN+i*CELL+5}" text-anchor="middle" font-size="13" font-family="Arial" fill="#5a3a1a">{N-i}</text>')

    if marks:
        for mr, mc in marks:
            mx, my = MARGIN + mc * CELL, MARGIN + mr * CELL
            lines.append(f'<circle cx="{mx}" cy="{my}" r="{R}" fill="#00CC44" fill-opacity="0.45" stroke="#009933" stroke-width="2"/>')

    if hint:
        hr, hc = hint
        hx, hy = MARGIN + hc * CELL, MARGIN + hr * CELL
        lines.append(f'<circle cx="{hx}" cy="{hy}" r="{R}" fill="#00CC44" fill-opacity="0.6" stroke="#009933" stroke-width="2"/>')

    for r in range(N):
        for c in range(N):
            v = board[r][c]
            if v == 0:
                continue
            x, y = MARGIN + c * CELL, MARGIN + r * CELL
            if v == 1:
                lines.append(f'<circle cx="{x+3}" cy="{y+3}" r="{R}" fill="#555"/>')
                lines.append(f'<circle cx="{x}" cy="{y}" r="{R}" fill="#1a1a1a" stroke="#000" stroke-width="1"/>')
                lines.append(f'<circle cx="{x-R//3}" cy="{y-R//3}" r="{R//4}" fill="#666"/>')
            else:
                lines.append(f'<circle cx="{x+3}" cy="{y+3}" r="{R}" fill="#aaa"/>')
                lines.append(f'<circle cx="{x}" cy="{y}" r="{R}" fill="#F5F5F5" stroke="#999" stroke-width="1"/>')
                lines.append(f'<circle cx="{x-R//3}" cy="{y-R//3}" r="{R//4}" fill="white"/>')

    if last_move:
        lr, lc = last_move
        lines.append(f'<circle cx="{MARGIN+lc*CELL}" cy="{MARGIN+lr*CELL}" r="7" fill="#FF3333"/>')

    if player_mark:
        pr2, pc2 = player_mark
        dot = mark_color or "#888"
        lines.append(f'<circle cx="{MARGIN+pc2*CELL}" cy="{MARGIN+pr2*CELL}" r="9" fill="{dot}" stroke="white" stroke-width="2"/>')

    lines.append('</svg>')
    return '\n'.join(lines)


def empty_board():
    return [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]


def coord_label(r, c):
    """(행, 열) 인덱스를 바둑 좌표 문자열로 변환. 예: (0,0)→'A9'"""
    return f"{chr(65+c)}{BOARD_SIZE - r}"


# ============================================================
# 탭 레이아웃
# ============================================================

tab1, tab2, tab3 = st.tabs(["📚 튜토리얼", "🧩 사활 문제", "⚔️ AI 대국"])

# ─────────────────────────────────────────────────────────────
# 탭 1: 튜토리얼
# ─────────────────────────────────────────────────────────────
with tab1:
    if "lesson_idx" not in st.session_state:
        st.session_state.lesson_idx = 0

    idx = st.session_state.lesson_idx
    lesson = LESSONS[idx]

    col_board, col_text = st.columns([1, 1.2])

    with col_board:
        board = empty_board()
        for (r, c), v in lesson["stones"].items():
            board[r][c] = v
        svg = render_board_svg(board, marks=lesson["marks"])
        st.markdown(f'<div style="display:flex;justify-content:center;">{svg}</div>', unsafe_allow_html=True)

    with col_text:
        st.markdown(f"### {idx+1}단계. {lesson['title']}")
        st.info(lesson["text"].replace("\n", "  \n"))

        st.progress((idx + 1) / len(LESSONS), text=f"{idx+1} / {len(LESSONS)} 단계")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("◀ 이전", disabled=(idx == 0), use_container_width=True, key="lesson_prev"):
                st.session_state.lesson_idx -= 1
                st.rerun()
        with c2:
            if st.button("처음으로", use_container_width=True, key="lesson_top"):
                st.session_state.lesson_idx = 0
                st.rerun()
        with c3:
            if idx < len(LESSONS) - 1:
                if st.button("다음 ▶", use_container_width=True, type="primary", key="lesson_next"):
                    st.session_state.lesson_idx += 1
                    st.rerun()
            else:
                st.success("완료! 🎉")

# ─────────────────────────────────────────────────────────────
# 탭 2: 사활 문제
# ─────────────────────────────────────────────────────────────
with tab2:
    for key, default in [
        ("ts_idx", 0),
        ("ts_board", None),
        ("ts_solved", False),
        ("ts_player_move", None),
        ("ts_hint_shown", False),
        ("ts_answer_shown", False),
        ("ts_completed", set()),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    prob = TSUMEGO[st.session_state.ts_idx]

    if st.session_state.ts_board is None:
        st.session_state.ts_board = dict(prob["stones"])

    # 문제 목록 선택
    prob_labels = [
        f"{'✅' if i in st.session_state.ts_completed else '⬜'} {TSUMEGO[i]['level']} — {TSUMEGO[i]['title']}"
        for i in range(len(TSUMEGO))
    ]
    sel = st.radio("문제 선택", prob_labels, index=st.session_state.ts_idx, horizontal=False, key="ts_radio")
    new_idx = prob_labels.index(sel)
    if new_idx != st.session_state.ts_idx:
        st.session_state.ts_idx = new_idx
        st.session_state.ts_board = dict(TSUMEGO[new_idx]["stones"])
        st.session_state.ts_solved = False
        st.session_state.ts_player_move = None
        st.session_state.ts_hint_shown = False
        st.session_state.ts_answer_shown = False
        st.rerun()

    prob = TSUMEGO[st.session_state.ts_idx]
    st.divider()

    col_board, col_ctrl = st.columns([1, 1])

    with col_board:
        board = empty_board()
        for (r, c), v in st.session_state.ts_board.items():
            board[r][c] = v

        hint_pos = prob["answers"][0] if (st.session_state.ts_hint_shown or st.session_state.ts_answer_shown) else None
        pm = st.session_state.ts_player_move
        pm_color = "#44CC66" if st.session_state.ts_solved else "#FF4444" if pm else None

        svg = render_board_svg(board, hint=hint_pos, player_mark=pm, mark_color=pm_color)
        st.markdown(f'<div style="display:flex;justify-content:center;">{svg}</div>', unsafe_allow_html=True)
        st.caption("A=왼쪽 1열, I=오른쪽 9열 / 9=위쪽, 1=아래쪽")

    with col_ctrl:
        st.markdown(f"**{prob['title']}**  {prob['level']}")
        st.info(prob["task"])

        if not st.session_state.ts_solved:
            ca, cb = st.columns(2)
            with ca:
                col_sel = st.selectbox("열 (가로)", list("ABCDEFGHI"), key="ts_col")
            with cb:
                row_sel = st.selectbox("행 (세로)", list(range(9, 0, -1)), key="ts_row")

            move_c = ord(col_sel) - ord('A')
            move_r = BOARD_SIZE - row_sel

            if st.button("✅ 정답 확인", type="primary", use_container_width=True, key="ts_submit"):
                if (move_r, move_c) in st.session_state.ts_board:
                    st.warning("이미 돌이 있는 곳입니다. 다른 곳을 선택해 주세요.")
                else:
                    # 이전 오답 돌 제거
                    pm_prev = st.session_state.ts_player_move
                    if pm_prev and pm_prev not in prob["stones"]:
                        st.session_state.ts_board.pop(pm_prev, None)

                    st.session_state.ts_board[(move_r, move_c)] = prob["player"]
                    st.session_state.ts_player_move = (move_r, move_c)

                    if (move_r, move_c) in prob["answers"]:
                        st.session_state.ts_solved = True
                        st.session_state.ts_completed.add(st.session_state.ts_idx)
                    st.rerun()

        if st.session_state.ts_solved:
            st.success(f"🎉 정답입니다!\n\n{prob['explain']}")
            if st.session_state.ts_idx < len(TSUMEGO) - 1:
                if st.button("다음 문제 ▶", type="primary", use_container_width=True, key="ts_next"):
                    next_i = st.session_state.ts_idx + 1
                    st.session_state.ts_idx = next_i
                    st.session_state.ts_board = dict(TSUMEGO[next_i]["stones"])
                    st.session_state.ts_solved = False
                    st.session_state.ts_player_move = None
                    st.session_state.ts_hint_shown = False
                    st.session_state.ts_answer_shown = False
                    st.rerun()
            else:
                st.balloons()
                st.success("🏁 모든 사활 문제를 풀었어요! 대단합니다!")

        st.divider()
        h1, h2, h3 = st.columns(3)
        with h1:
            if st.button("💡 힌트", use_container_width=True, key="ts_hint", disabled=st.session_state.ts_solved):
                st.session_state.ts_hint_shown = True
                st.rerun()
        with h2:
            if st.button("👁 정답 보기", use_container_width=True, key="ts_ans"):
                st.session_state.ts_answer_shown = True
                st.rerun()
        with h3:
            if st.button("🔄 다시", use_container_width=True, key="ts_retry"):
                st.session_state.ts_board = dict(prob["stones"])
                st.session_state.ts_player_move = None
                st.session_state.ts_solved = False
                st.session_state.ts_hint_shown = False
                st.session_state.ts_answer_shown = False
                st.rerun()

        if st.session_state.ts_hint_shown and not st.session_state.ts_solved:
            st.info(f"💡 힌트: {prob['hint']}")
        if st.session_state.ts_answer_shown and not st.session_state.ts_solved:
            ar, ac = prob["answers"][0]
            st.warning(f"👁 정답 위치: **{coord_label(ar, ac)}**")

# ─────────────────────────────────────────────────────────────
# 탭 3: AI 대국
# ─────────────────────────────────────────────────────────────
with tab3:
    for key, default in [
        ("game", None),
        ("ai_level", 1),
        ("game_msg", ""),
        ("game_msg_type", "info"),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    level_names = {1: "👶 입문", 2: "🔰 초급", 3: "⚔️ 중급"}

    if st.session_state.game is None:
        st.markdown("### AI 난이도를 선택하세요")
        st.markdown("처음이라면 **입문**부터 시작하세요. 바둑은 ⚫ 흑이 먼저 둡니다.")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("👶 입문\n(완전 랜덤)", use_container_width=True, type="primary", key="g1"):
                st.session_state.game = GoGame()
                st.session_state.ai_level = 1
                st.session_state.game_msg = "⚫ 흑(내가) 먼저 두세요!"
                st.session_state.game_msg_type = "info"
                st.rerun()
        with c2:
            if st.button("🔰 초급\n(잡기 우선)", use_container_width=True, key="g2"):
                st.session_state.game = GoGame()
                st.session_state.ai_level = 2
                st.session_state.game_msg = "⚫ 흑(내가) 먼저 두세요!"
                st.session_state.game_msg_type = "info"
                st.rerun()
        with c3:
            if st.button("⚔️ 중급\n(중앙 전략)", use_container_width=True, key="g3"):
                st.session_state.game = GoGame()
                st.session_state.ai_level = 3
                st.session_state.game_msg = "⚫ 흑(내가) 먼저 두세요!"
                st.session_state.game_msg_type = "info"
                st.rerun()
    else:
        game: GoGame = st.session_state.game
        ai = GoAI(game, level=st.session_state.ai_level)

        col_board, col_side = st.columns([1, 0.65])

        with col_board:
            svg = render_board_svg(game.board, last_move=game.last_move)
            st.markdown(f'<div style="display:flex;justify-content:center;">{svg}</div>', unsafe_allow_html=True)
            st.caption("A=왼쪽 1열, I=오른쪽 9열 / 9=위쪽, 1=아래쪽")

        with col_side:
            st.markdown(f"**난이도:** {level_names[st.session_state.ai_level]}")
            if not game.game_over:
                turn_str = "⚫ 흑 (내 차례)" if game.current_player == 1 else "⚪ 백 (AI 차례)"
                st.markdown(f"**현재 차례:** {turn_str}")

            msg = st.session_state.game_msg
            if msg:
                mtype = st.session_state.game_msg_type
                if mtype == "success":
                    st.success(msg)
                elif mtype == "error":
                    st.error(msg)
                elif mtype == "warning":
                    st.warning(msg)
                else:
                    st.info(msg)

            st.divider()
            st.markdown(f"⚫ 내가 잡은 돌: **{game.captured[1]}개**")
            st.markdown(f"⚪ AI가 잡은 돌: **{game.captured[-1]}개**")
            st.divider()

            if not game.game_over:
                ga, gb = st.columns(2)
                with ga:
                    move_col = st.selectbox("열 (가로)", list("ABCDEFGHI"), key="game_col")
                with gb:
                    move_row = st.selectbox("행 (세로)", list(range(9, 0, -1)), key="game_row")

                move_c = ord(move_col) - ord('A')
                move_r = BOARD_SIZE - move_row

                if st.button("⚫ 돌 놓기", type="primary", use_container_width=True, key="game_place"):
                    ok, reason = game.place_stone(move_r, move_c)
                    if ok:
                        # AI 응수
                        ai_result = ai.move()
                        if ai_result:
                            ar, ac = ai_result
                            st.session_state.game_msg = f"AI가 **{coord_label(ar, ac)}**에 두었습니다."
                        else:
                            st.session_state.game_msg = "AI가 패스했습니다."
                        st.session_state.game_msg_type = "info"
                    else:
                        reason_map = {
                            "범위 밖": "그 위치는 바둑판 밖입니다.",
                            "이미 돌이 있음": "이미 돌이 있는 곳입니다.",
                            "패": "패 규칙으로 지금은 그 곳에 놓을 수 없어요.",
                            "자살수": "자살수입니다 — 활로가 없는 곳에는 놓을 수 없어요.",
                        }
                        st.session_state.game_msg = reason_map.get(reason, f"놓을 수 없습니다: {reason}")
                        st.session_state.game_msg_type = "warning"
                    st.rerun()

                if st.button("⏭ 패스", use_container_width=True, key="game_pass"):
                    game.pass_turn()
                    if not game.game_over:
                        ai.move()
                        st.session_state.game_msg = "패스했습니다. AI가 응수했어요."
                    else:
                        st.session_state.game_msg = "양쪽 모두 패스 — 게임 종료!"
                    st.session_state.game_msg_type = "info"
                    st.rerun()
            else:
                black_score, white_score = game.calculate_score()
                st.markdown("### 게임 종료!")
                st.markdown(f"⚫ 흑 점수: **{black_score:.0f}점**")
                st.markdown(f"⚪ 백 점수: **{white_score:.1f}점** (덤 6.5 포함)")
                if black_score > white_score:
                    st.balloons()
                    st.success("🎉 흑(내가) 승리!")
                else:
                    st.error("⚪ 백(AI) 승리...")

            st.divider()
            if st.button("🔄 새 게임", use_container_width=True, key="game_reset"):
                st.session_state.game = None
                st.session_state.game_msg = ""
                st.rerun()
