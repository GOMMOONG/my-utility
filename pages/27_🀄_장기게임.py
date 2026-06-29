import streamlit as st
import sys, os, random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="장기 게임 - 마이 유틸리티", page_icon="🀄", layout="wide")
apply_common_style()
check_password()
show_page_header("🀄", "한국 장기", "AI와 장기 대결 — 한편(빨간)이 사용자, 초편(초록)이 AI입니다!")

# ══════════════════════════════════════════════════════════════
# 기물 상수 (내부 표현: "H한자"=한편, "C한자"=초편)
# ══════════════════════════════════════════════════════════════
EMPTY = ""

H_JA    = "H漢"; H_CHA = "H車"; H_PO = "H包"
H_MA    = "H馬"; H_SANG = "H象"; H_SA = "H士"; H_BYUNG = "H兵"

C_JA    = "C楚"; C_CHA = "C車"; C_PO = "C包"
C_MA    = "C馬"; C_SANG = "C象"; C_SA = "C士"; C_JUL  = "C卒"

HAN_PIECES = {H_JA, H_CHA, H_PO, H_MA, H_SANG, H_SA, H_BYUNG}
CHO_PIECES = {C_JA, C_CHA, C_PO, C_MA, C_SANG, C_SA, C_JUL}

PIECE_VALUE = {
    H_JA: 100000, H_CHA: 1300, H_PO: 700, H_MA: 500,
    H_SANG: 300,  H_SA: 300,   H_BYUNG: 200,
    C_JA: 100000, C_CHA: 1300, C_PO: 700, C_MA: 500,
    C_SANG: 300,  C_SA: 300,   C_JUL: 200,
}

def get_char(piece):
    return piece[1] if piece else ""

def is_han(p):  return p.startswith("H") if p else False
def is_cho(p):  return p.startswith("C") if p else False
def same_side(p1, p2):
    if not p1 or not p2: return False
    return (is_han(p1) and is_han(p2)) or (is_cho(p1) and is_cho(p2))

def in_bounds(r, c):      return 0 <= r <= 9 and 0 <= c <= 8
def in_han_palace(r, c):  return 7 <= r <= 9 and 3 <= c <= 5
def in_cho_palace(r, c):  return 0 <= r <= 2 and 3 <= c <= 5

# ══════════════════════════════════════════════════════════════
# 초기 보드
# ══════════════════════════════════════════════════════════════
def initial_board():
    b = [[EMPTY]*9 for _ in range(10)]
    b[0] = [C_CHA,C_MA,C_SANG,C_SA,EMPTY,C_SA,C_SANG,C_MA,C_CHA]
    b[1] = [EMPTY,EMPTY,EMPTY,EMPTY,C_JA,EMPTY,EMPTY,EMPTY,EMPTY]
    b[2] = [EMPTY,C_PO,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,C_PO,EMPTY]
    b[3] = [C_JUL,EMPTY,C_JUL,EMPTY,C_JUL,EMPTY,C_JUL,EMPTY,C_JUL]
    b[6] = [H_BYUNG,EMPTY,H_BYUNG,EMPTY,H_BYUNG,EMPTY,H_BYUNG,EMPTY,H_BYUNG]
    b[7] = [EMPTY,H_PO,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,H_PO,EMPTY]
    b[8] = [EMPTY,EMPTY,EMPTY,EMPTY,H_JA,EMPTY,EMPTY,EMPTY,EMPTY]
    b[9] = [H_CHA,H_MA,H_SANG,H_SA,EMPTY,H_SA,H_SANG,H_MA,H_CHA]
    return b

# ══════════════════════════════════════════════════════════════
# 이동 규칙
# ══════════════════════════════════════════════════════════════
def get_raw_moves(board, r, c):
    piece = board[r][c]
    if not piece: return []
    moves = []

    if piece in (H_JA, C_JA):
        palace = in_han_palace if is_han(piece) else in_cho_palace
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r+dr, c+dc
            if palace(nr, nc) and not same_side(piece, board[nr][nc]):
                moves.append((nr, nc))

    elif piece in (H_SA, C_SA):
        palace = in_han_palace if is_han(piece) else in_cho_palace
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r+dr, c+dc
            if palace(nr, nc) and not same_side(piece, board[nr][nc]):
                moves.append((nr, nc))

    elif piece in (H_CHA, C_CHA):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            while in_bounds(nr, nc):
                if board[nr][nc]:
                    if not same_side(piece, board[nr][nc]): moves.append((nr, nc))
                    break
                moves.append((nr, nc))
                nr, nc = nr+dr, nc+dc

    elif piece in (H_PO, C_PO):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            jumped = False
            while in_bounds(nr, nc):
                if not jumped:
                    if board[nr][nc]:
                        if board[nr][nc] in (H_PO, C_PO): break
                        jumped = True
                else:
                    if board[nr][nc]:
                        if not same_side(piece, board[nr][nc]) and board[nr][nc] not in (H_PO, C_PO):
                            moves.append((nr, nc))
                        break
                    else:
                        moves.append((nr, nc))
                nr, nc = nr+dr, nc+dc

    elif piece in (H_MA, C_MA):
        for (dr1,dc1), dests in [
            ((-1,0),[(-2,-1),(-2,1)]), ((1,0),[(2,-1),(2,1)]),
            ((0,-1),[(-1,-2),(1,-2)]), ((0,1),[(-1,2),(1,2)])
        ]:
            mr, mc = r+dr1, c+dc1
            if not in_bounds(mr, mc) or board[mr][mc]: continue
            for dr2, dc2 in dests:
                nr, nc = r+dr2, c+dc2
                if in_bounds(nr, nc) and not same_side(piece, board[nr][nc]):
                    moves.append((nr, nc))

    elif piece in (H_SANG, C_SANG):
        for (dr1,dc1),(dr2,dc2),(dr3,dc3) in [
            ((-1,0),(-2,-1),(-3,-2)),((-1,0),(-2,1),(-3,2)),
            ((1,0),(2,-1),(3,-2)),   ((1,0),(2,1),(3,2)),
            ((0,-1),(-1,-2),(-2,-3)),((0,-1),(1,-2),(2,-3)),
            ((0,1),(-1,2),(-2,3)),   ((0,1),(1,2),(2,3)),
        ]:
            m1r,m1c = r+dr1,c+dc1; m2r,m2c = r+dr2,c+dc2; dr,dc = r+dr3,c+dc3
            if not (in_bounds(m1r,m1c) and in_bounds(m2r,m2c) and in_bounds(dr,dc)): continue
            if board[m1r][m1c] or board[m2r][m2c]: continue
            if not same_side(piece, board[dr][dc]): moves.append((dr, dc))

    elif piece == C_JUL:
        for dr, dc in [(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if in_bounds(nr, nc) and not same_side(piece, board[nr][nc]):
                moves.append((nr, nc))

    elif piece == H_BYUNG:
        for dr, dc in [(-1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if in_bounds(nr, nc) and not same_side(piece, board[nr][nc]):
                moves.append((nr, nc))

    return moves


def find_king(board, side):
    king = H_JA if side == "han" else C_JA
    for r in range(10):
        for c in range(9):
            if board[r][c] == king: return (r, c)
    return None


def is_in_check(board, side):
    kp = find_king(board, side)
    if not kp: return True
    kr, kc = kp
    enemy = "cho" if side == "han" else "han"
    for r in range(10):
        for c in range(9):
            p = board[r][c]
            if (enemy == "han" and is_han(p)) or (enemy == "cho" and is_cho(p)):
                if (kr, kc) in get_raw_moves(board, r, c): return True
    op = find_king(board, enemy)
    if op:
        okr, okc = op
        if okc == kc:
            mn, mx = min(kr, okr), max(kr, okr)
            if not any(board[rr][kc] for rr in range(mn+1, mx)):
                return True
    return False


def make_move(board, fr, fc, tr, tc):
    nb = [row[:] for row in board]
    nb[tr][tc] = nb[fr][fc]
    nb[fr][fc] = EMPTY
    return nb


def get_valid_moves(board, r, c):
    piece = board[r][c]
    if not piece: return []
    side = "han" if is_han(piece) else "cho"
    return [(tr,tc) for tr,tc in get_raw_moves(board,r,c)
            if not is_in_check(make_move(board,r,c,tr,tc), side)]


def get_all_moves(board, side):
    pieces = HAN_PIECES if side == "han" else CHO_PIECES
    result = []
    for r in range(10):
        for c in range(9):
            if board[r][c] in pieces:
                for tr, tc in get_valid_moves(board, r, c):
                    result.append((r,c,tr,tc))
    return result

# ══════════════════════════════════════════════════════════════
# AI
# ══════════════════════════════════════════════════════════════
def evaluate(board):
    score = 0
    for r in range(10):
        for c in range(9):
            p = board[r][c]
            if p:
                v = PIECE_VALUE.get(p, 0)
                score += v if is_cho(p) else -v
    return score

def sort_moves(board, moves):
    return sorted(moves, key=lambda m: PIECE_VALUE.get(board[m[2]][m[3]], 0), reverse=True)

def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0: return evaluate(board)
    side = "cho" if maximizing else "han"
    moves = sort_moves(board, get_all_moves(board, side))
    if not moves:
        return (-100000 if maximizing else 100000) if is_in_check(board, side) else 0
    if maximizing:
        best = -999999
        for fr,fc,tr,tc in moves:
            val = minimax(make_move(board,fr,fc,tr,tc), depth-1, alpha, beta, False)
            best = max(best, val); alpha = max(alpha, val)
            if beta <= alpha: break
        return best
    else:
        best = 999999
        for fr,fc,tr,tc in moves:
            val = minimax(make_move(board,fr,fc,tr,tc), depth-1, alpha, beta, True)
            best = min(best, val); beta = min(beta, val)
            if beta <= alpha: break
        return best

def ai_best_move(board, depth):
    moves = sort_moves(board, get_all_moves(board, "cho"))
    if not moves: return None
    best_val, best_moves = -999999, []
    for fr,fc,tr,tc in moves:
        val = minimax(make_move(board,fr,fc,tr,tc), depth-1, -999999, 999999, False)
        if val > best_val:   best_val = val; best_moves = [(fr,fc,tr,tc)]
        elif val == best_val: best_moves.append((fr,fc,tr,tc))
    return random.choice(best_moves)

# ══════════════════════════════════════════════════════════════
# SVG 장기판 렌더러
# ══════════════════════════════════════════════════════════════
CELL   = 54
MARGIN = 38
BW = MARGIN*2 + CELL*8   # 보드 너비
BH = MARGIN*2 + CELL*9   # 보드 높이

def render_janggi_svg(board, selected=None, valid_moves=None, last_move=None):
    valid_set = set(valid_moves) if valid_moves else set()
    last_set  = set()
    if last_move:
        fr, fc, tr, tc = last_move
        last_set = {(fr,fc),(tr,tc)}

    p = [f'<svg width="{BW}" height="{BH}" xmlns="http://www.w3.org/2000/svg">',
         f'<rect width="{BW}" height="{BH}" fill="#DEB887" rx="6"/>']

    # 격자선
    for r in range(10):
        x0 = MARGIN;          y0 = MARGIN + r*CELL
        x1 = MARGIN + 8*CELL; y1 = y0
        p.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="#5C3A1E" stroke-width="1.2"/>')
    for c in range(9):
        x0 = MARGIN + c*CELL; y0 = MARGIN
        x1 = x0;              y1 = MARGIN + 9*CELL
        p.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="#5C3A1E" stroke-width="1.2"/>')

    # 강(楚漢之界)
    mid_y = MARGIN + 4*CELL + CELL//2
    p.append(f'<text x="{BW//2}" y="{mid_y+5}" text-anchor="middle" '
             f'font-size="13" font-family="맑은 고딕,serif" fill="#1A5276" '
             f'font-style="italic">楚 漢 之 界</text>')

    # 궁성 대각선 (초편: 행0-2 열3-5, 한편: 행7-9 열3-5)
    for row_s in (0, 7):
        x0 = MARGIN+3*CELL; y0 = MARGIN+row_s*CELL
        x1 = MARGIN+5*CELL; y1 = MARGIN+(row_s+2)*CELL
        p.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="#5C3A1E" stroke-width="1.2"/>')
        x0 = MARGIN+5*CELL; x1 = MARGIN+3*CELL
        p.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="#5C3A1E" stroke-width="1.2"/>')

    # 마지막 이동 강조 배경
    for (mr, mc) in last_set:
        cx = MARGIN + mc*CELL; cy = MARGIN + mr*CELL
        p.append(f'<circle cx="{cx}" cy="{cy}" r="25" fill="#CDD16E" fill-opacity="0.55"/>')

    # 선택된 기물 강조
    if selected:
        sr, sc = selected
        cx = MARGIN + sc*CELL; cy = MARGIN + sr*CELL
        p.append(f'<circle cx="{cx}" cy="{cy}" r="25" fill="#FFD700" fill-opacity="0.6"/>')

    # 이동 가능 위치 표시
    for (mr, mc) in valid_set:
        cx = MARGIN + mc*CELL; cy = MARGIN + mr*CELL
        if board[mr][mc]:
            p.append(f'<circle cx="{cx}" cy="{cy}" r="24" fill="none" '
                     f'stroke="#FF4500" stroke-width="3"/>')
        else:
            p.append(f'<circle cx="{cx}" cy="{cy}" r="10" '
                     f'fill="#3DA53D" fill-opacity="0.7"/>')

    # 기물 그리기
    for r in range(10):
        for c in range(9):
            piece = board[r][c]
            if not piece: continue
            cx = MARGIN + c*CELL; cy = MARGIN + r*CELL
            fill   = "#CC0000" if is_han(piece) else "#228B22"
            stroke = "#8B0000" if is_han(piece) else "#145214"
            char   = get_char(piece)
            p.append(f'<circle cx="{cx}" cy="{cy}" r="22" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
            p.append(f'<text x="{cx}" y="{cy+7}" text-anchor="middle" '
                     f'font-size="18" font-weight="bold" '
                     f'font-family="맑은 고딕,serif" fill="white">{char}</text>')

    # 좌표 레이블 (열: 1~9, 행: 1~10)
    COL_LABELS = "①②③④⑤⑥⑦⑧⑨"
    for c in range(9):
        cx = MARGIN + c*CELL
        p.append(f'<text x="{cx}" y="{BH-5}" text-anchor="middle" '
                 f'font-size="11" font-family="맑은 고딕" fill="#5C3A1E">{COL_LABELS[c]}</text>')
    for r in range(10):
        cy = MARGIN + r*CELL
        p.append(f'<text x="12" y="{cy+5}" text-anchor="middle" '
                 f'font-size="11" font-family="맑은 고딕" fill="#5C3A1E">{r+1}</text>')

    p.append('</svg>')
    return '\n'.join(p)

# ══════════════════════════════════════════════════════════════
# 세션 초기화
# ══════════════════════════════════════════════════════════════
def init_game(depth=2):
    st.session_state.jg_board     = initial_board()
    st.session_state.jg_depth     = depth
    st.session_state.jg_turn      = "han"
    st.session_state.jg_selected  = None
    st.session_state.jg_valid     = []
    st.session_state.jg_last_move = None
    st.session_state.jg_status    = "한편(빨간) 차례입니다 — 기물을 선택하세요"
    st.session_state.jg_game_over = False
    st.session_state.jg_history   = []

def do_ai_move():
    move = ai_best_move(st.session_state.jg_board, st.session_state.jg_depth)
    if move:
        fr, fc, tr, tc = move
        st.session_state.jg_board    = make_move(st.session_state.jg_board, fr, fc, tr, tc)
        st.session_state.jg_last_move = move
        board = st.session_state.jg_board
        piece_char = get_char(st.session_state.jg_board[tr][tc])
        st.session_state.jg_history.append(f"초 {piece_char} ({fr+1}행{fc+1}열→{tr+1}행{tc+1}열)")

# ══════════════════════════════════════════════════════════════
# 메인 화면
# ══════════════════════════════════════════════════════════════
if "jg_board" not in st.session_state:
    # ── 게임 시작 화면 ────────────────────────────────────────
    st.markdown("### 게임 설정")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**AI 난이도**")
        diff_choice = st.radio("난이도", ["👶 쉬움", "🔰 보통", "⚔️ 어려움"],
                               label_visibility="collapsed")
    with col2:
        st.markdown("**장기 규칙 요약**")
        st.markdown("""
- **한편(빨간)** = 사용자 / **초편(초록)** = AI
- 상대 장(將)을 잡으면 승리합니다
- 장군(將軍): 상대 장이 공격받는 상태
- 외통수: 장군을 피할 방법이 없으면 패배
        """)

    if st.button("🎮 게임 시작", type="primary", use_container_width=True):
        depth = {"👶 쉬움": 1, "🔰 보통": 2, "⚔️ 어려움": 3}[diff_choice]
        init_game(depth)
        st.rerun()

    st.divider()
    st.markdown("""
    **기물별 이동 방법**

    | 기물 | 이동 방법 |
    |------|----------|
    | 車(차) | 직선으로 몇 칸이든 (막히면 불가) |
    | 包(포) | 기물 1개를 뛰어넘어 이동·잡기 (포로 포 불가) |
    | 馬(마) | 직선 1칸 후 대각선 1칸 (L자) |
    | 象(상) | 직선 1칸 후 대각선 2칸 |
    | 士(사) | 궁성 안에서 직선·대각선 1칸 |
    | 漢/楚(장) | 궁성 안에서 직선·대각선 1칸 |
    | 兵/卒(졸·병) | 앞 또는 양옆 1칸 (뒤로 불가) |
    """)

else:
    # ── 게임 진행 화면 ────────────────────────────────────────
    board     = st.session_state.jg_board
    game_over = st.session_state.jg_game_over
    selected  = st.session_state.jg_selected
    valid     = st.session_state.jg_valid

    col_board, col_side = st.columns([1, 0.55])

    # ── 왼쪽: 장기판 ─────────────────────────────────────────
    with col_board:
        svg = render_janggi_svg(
            board,
            selected=selected,
            valid_moves=valid,
            last_move=st.session_state.jg_last_move,
        )
        st.markdown(f'<div style="display:flex;justify-content:center;">{svg}</div>',
                    unsafe_allow_html=True)
        st.caption("🟢 초록 점 = 이동 가능 / 🔴 빨간 테두리 = 잡을 수 있는 기물 / 🟡 노란 배경 = 마지막 이동")

    # ── 오른쪽: 조작 패널 ─────────────────────────────────────
    with col_side:
        # 상태 메시지
        status = st.session_state.jg_status
        if game_over:
            st.error(status)
        elif "장군" in status:
            st.warning(status)
        else:
            st.info(status)

        st.divider()

        # 이동 입력 (내 차례이고 게임 진행 중일 때만)
        if not game_over and st.session_state.jg_turn == "han":
            # ── 1단계: 기물 선택 ──
            st.markdown("**① 움직일 기물 위치 선택**")
            c1, c2 = st.columns(2)
            with c1:
                sel_row = st.selectbox("행(위→아래)", list(range(1, 11)),
                                       index=8, key="jg_sel_row",
                                       label_visibility="collapsed",
                                       format_func=lambda x: f"{x}행")
            with c2:
                sel_col = st.selectbox("열(좌→우)", list(range(1, 10)),
                                       index=3, key="jg_sel_col",
                                       label_visibility="collapsed",
                                       format_func=lambda x: f"{x}열")

            sr, sc = sel_row - 1, sel_col - 1
            piece_at = board[sr][sc]

            # 기물 선택 버튼
            if st.button("🔍 기물 선택 / 확인", use_container_width=True):
                if is_han(piece_at):
                    vm = get_valid_moves(board, sr, sc)
                    if vm:
                        st.session_state.jg_selected = (sr, sc)
                        st.session_state.jg_valid    = vm
                    else:
                        st.session_state.jg_selected = None
                        st.session_state.jg_valid    = []
                        st.warning("이 기물은 이동할 수 있는 곳이 없습니다.")
                else:
                    st.session_state.jg_selected = None
                    st.session_state.jg_valid    = []
                    if piece_at:
                        st.warning("상대 기물은 선택할 수 없습니다.")
                    else:
                        st.warning("빈 칸입니다. 한편(빨간) 기물을 선택하세요.")
                st.rerun()

            # ── 2단계: 이동 위치 선택 ──
            if selected and valid:
                st.markdown("**② 이동할 위치 선택**")
                dest_labels = [f"{tr+1}행 {tc+1}열" for tr, tc in valid]
                dest_choice = st.selectbox("도착 위치", dest_labels,
                                           label_visibility="collapsed",
                                           key="jg_dest")
                di = dest_labels.index(dest_choice)
                tr, tc = valid[di]

                if st.button("♟ 이동 실행", type="primary", use_container_width=True):
                    # 기물 이름 기록용
                    piece_char = get_char(board[selected[0]][selected[1]])
                    fr, fc = selected
                    st.session_state.jg_board = make_move(board, fr, fc, tr, tc)
                    board = st.session_state.jg_board
                    st.session_state.jg_last_move = (fr, fc, tr, tc)
                    st.session_state.jg_selected  = None
                    st.session_state.jg_valid     = []
                    st.session_state.jg_history.append(f"한 {piece_char} ({fr+1}행{fc+1}열→{tr+1}행{tc+1}열)")

                    # 게임 종료 확인 (초편이 이동 불가?)
                    cho_moves = get_all_moves(board, "cho")
                    if not cho_moves:
                        st.session_state.jg_game_over = True
                        st.session_state.jg_status    = "🎉 외통수! 한편(당신) 승리!"
                        st.rerun()

                    # AI 차례
                    st.session_state.jg_turn = "cho"
                    st.session_state.jg_status = "AI(초편·초록) 생각 중…"
                    with st.spinner("AI가 생각 중입니다…"):
                        do_ai_move()

                    board = st.session_state.jg_board
                    # 게임 종료 확인 (한편이 이동 불가?)
                    han_moves = get_all_moves(board, "han")
                    if not han_moves:
                        if is_in_check(board, "han"):
                            st.session_state.jg_status    = "😢 외통수! AI(초편) 승리!"
                        else:
                            st.session_state.jg_status    = "🤝 비김(무승부)!"
                        st.session_state.jg_game_over = True
                    elif is_in_check(board, "han"):
                        st.session_state.jg_status = "⚠️ 장군(將軍)! 피하세요!"
                    else:
                        st.session_state.jg_status = "한편(빨간) 차례입니다 — 기물을 선택하세요"

                    st.session_state.jg_turn = "han"
                    st.rerun()
            else:
                st.caption("기물을 선택하면 이동 가능한 위치가 표시됩니다.")

        st.divider()

        # 새 게임 버튼
        if st.button("🔄 새 게임", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k.startswith("jg_"):
                    del st.session_state[k]
            st.rerun()

        # 이동 기록
        if st.session_state.get("jg_history"):
            with st.expander("📋 이동 기록", expanded=False):
                for note in reversed(st.session_state.jg_history[-30:]):
                    st.caption(note)
