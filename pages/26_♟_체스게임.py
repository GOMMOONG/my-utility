import streamlit as st
import sys, os, copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="체스 게임 - 마이 유틸리티", page_icon="♟", layout="wide")
apply_common_style()
check_password()
show_page_header("♟", "AI 체스 게임", "AI와 체스 대결 — 난이도를 선택하고 도전하세요!")

# ── 기물 상수 ────────────────────────────────────────────────
EMPTY = "."
WK, WQ, WR, WB, WN, WP = "WK", "WQ", "WR", "WB", "WN", "WP"
BK, BQ, BR, BB, BN, BP = "BK", "BQ", "BR", "BB", "BN", "BP"

SYMBOLS = {
    WK: "♔", WQ: "♕", WR: "♖", WB: "♗", WN: "♘", WP: "♙",
    BK: "♚", BQ: "♛", BR: "♜", BB: "♝", BN: "♞", BP: "♟",
}

PIECE_VALUE = {
    WK: 20000, WQ: 900, WR: 500, WB: 330, WN: 320, WP: 100,
    BK: 20000, BQ: 900, BR: 500, BB: 330, BN: 320, BP: 100,
}

INIT_BOARD = [
    [BR, BN, BB, BQ, BK, BB, BN, BR],
    [BP, BP, BP, BP, BP, BP, BP, BP],
    [EMPTY]*8, [EMPTY]*8, [EMPTY]*8, [EMPTY]*8,
    [WP, WP, WP, WP, WP, WP, WP, WP],
    [WR, WN, WB, WQ, WK, WB, WN, WR],
]

# 위치 보너스 테이블 (백 기준)
PAWN_T = [
    [0,0,0,0,0,0,0,0],[50,50,50,50,50,50,50,50],
    [10,10,20,30,30,20,10,10],[5,5,10,25,25,10,5,5],
    [0,0,0,20,20,0,0,0],[5,-5,-10,0,0,-10,-5,5],
    [5,10,10,-20,-20,10,10,5],[0,0,0,0,0,0,0,0],
]
KNIGHT_T = [
    [-50,-40,-30,-30,-30,-30,-40,-50],[-40,-20,0,0,0,0,-20,-40],
    [-30,0,10,15,15,10,0,-30],[-30,5,15,20,20,15,5,-30],
    [-30,0,15,20,20,15,0,-30],[-30,5,10,15,15,10,5,-30],
    [-40,-20,0,5,5,0,-20,-40],[-50,-40,-30,-30,-30,-30,-40,-50],
]
BISHOP_T = [
    [-20,-10,-10,-10,-10,-10,-10,-20],[-10,0,0,0,0,0,0,-10],
    [-10,0,5,10,10,5,0,-10],[-10,5,5,10,10,5,5,-10],
    [-10,0,10,10,10,10,0,-10],[-10,10,10,10,10,10,10,-10],
    [-10,5,0,0,0,0,5,-10],[-20,-10,-10,-10,-10,-10,-10,-20],
]
ROOK_T = [
    [0,0,0,0,0,0,0,0],[5,10,10,10,10,10,10,5],
    [-5,0,0,0,0,0,0,-5],[-5,0,0,0,0,0,0,-5],
    [-5,0,0,0,0,0,0,-5],[-5,0,0,0,0,0,0,-5],
    [-5,0,0,0,0,0,0,-5],[0,0,0,5,5,0,0,0],
]
QUEEN_T = [
    [-20,-10,-10,-5,-5,-10,-10,-20],[-10,0,0,0,0,0,0,-10],
    [-10,0,5,5,5,5,0,-10],[-5,0,5,5,5,5,0,-5],
    [0,0,5,5,5,5,0,-5],[-10,5,5,5,5,5,0,-10],
    [-10,0,5,0,0,0,0,-10],[-20,-10,-10,-5,-5,-10,-10,-20],
]
KING_T = [
    [-30,-40,-40,-50,-50,-40,-40,-30],[-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],[-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],[-10,-20,-20,-20,-20,-20,-20,-10],
    [20,20,0,0,0,0,20,20],[20,30,10,0,0,10,30,20],
]
POS_TABLE = {
    WP: PAWN_T, WN: KNIGHT_T, WB: BISHOP_T,
    WR: ROOK_T, WQ: QUEEN_T,  WK: KING_T,
}


# ── 체스 게임 로직 ────────────────────────────────────────────
class ChessBoard:
    def __init__(self):
        self.board = [row[:] for row in INIT_BOARD]
        self.turn = "W"
        self.castling = {"WK": True, "WQ": True, "BK": True, "BQ": True}
        self.en_passant = None
        self.move_history = []

    def is_enemy(self, piece, color):
        return piece != EMPTY and piece[0] != color

    def in_bounds(self, r, c):
        return 0 <= r <= 7 and 0 <= c <= 7

    def get_raw_moves(self, r, c):
        piece = self.board[r][c]
        if piece == EMPTY:
            return []
        color = piece[0]
        moves = []

        if piece in (WP, BP):
            direction = -1 if color == "W" else 1
            start_row = 6 if color == "W" else 1
            nr = r + direction
            if self.in_bounds(nr, c) and self.board[nr][c] == EMPTY:
                moves.append((nr, c))
                if r == start_row:
                    nr2 = r + 2 * direction
                    if self.board[nr2][c] == EMPTY:
                        moves.append((nr2, c))
            for dc in [-1, 1]:
                nc = c + dc
                nr = r + direction
                if self.in_bounds(nr, nc):
                    if self.is_enemy(self.board[nr][nc], color):
                        moves.append((nr, nc))
                    elif (nr, nc) == self.en_passant:
                        moves.append((nr, nc))

        elif piece in (WN, BN):
            for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                nr, nc = r+dr, c+dc
                if self.in_bounds(nr, nc):
                    t = self.board[nr][nc]
                    if t == EMPTY or self.is_enemy(t, color):
                        moves.append((nr, nc))

        else:
            if piece in (WB, BB):
                dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
            elif piece in (WR, BR):
                dirs = [(-1,0),(1,0),(0,-1),(0,1)]
            elif piece in (WQ, BQ):
                dirs = [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]
            elif piece in (WK, BK):
                for dr in [-1,0,1]:
                    for dc in [-1,0,1]:
                        if dr == 0 and dc == 0: continue
                        nr, nc = r+dr, c+dc
                        if self.in_bounds(nr, nc):
                            t = self.board[nr][nc]
                            if t == EMPTY or self.is_enemy(t, color):
                                moves.append((nr, nc))
                if color == "W" and r == 7 and c == 4:
                    if self.castling["WK"] and self.board[7][5] == EMPTY and self.board[7][6] == EMPTY:
                        moves.append((7, 6))
                    if self.castling["WQ"] and self.board[7][3] == EMPTY and self.board[7][2] == EMPTY and self.board[7][1] == EMPTY:
                        moves.append((7, 2))
                elif color == "B" and r == 0 and c == 4:
                    if self.castling["BK"] and self.board[0][5] == EMPTY and self.board[0][6] == EMPTY:
                        moves.append((0, 6))
                    if self.castling["BQ"] and self.board[0][3] == EMPTY and self.board[0][2] == EMPTY and self.board[0][1] == EMPTY:
                        moves.append((0, 2))
                return moves
            for dr, dc in dirs:
                nr, nc = r+dr, c+dc
                while self.in_bounds(nr, nc):
                    t = self.board[nr][nc]
                    if t == EMPTY:
                        moves.append((nr, nc))
                    elif self.is_enemy(t, color):
                        moves.append((nr, nc))
                        break
                    else:
                        break
                    nr += dr; nc += dc
        return moves

    def find_king(self, color):
        king = WK if color == "W" else BK
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == king:
                    return r, c
        return None

    def is_in_check(self, color):
        kpos = self.find_king(color)
        if not kpos: return False
        kr, kc = kpos
        enemy = "B" if color == "W" else "W"
        for r in range(8):
            for c in range(8):
                if self.board[r][c] != EMPTY and self.board[r][c][0] == enemy:
                    if (kr, kc) in self.get_raw_moves(r, c):
                        return True
        return False

    def get_legal_moves(self, r, c):
        piece = self.board[r][c]
        if piece == EMPTY or piece[0] != self.turn:
            return []
        color = piece[0]
        legal = []
        for nr, nc in self.get_raw_moves(r, c):
            sb = [row[:] for row in self.board]
            sep = self.en_passant
            sc = self.castling.copy()
            self._apply_move(r, c, nr, nc)
            if not self.is_in_check(color):
                legal.append((nr, nc))
            self.board = sb
            self.en_passant = sep
            self.castling = sc
        return legal

    def _apply_move(self, r, c, nr, nc):
        piece = self.board[r][c]
        color = piece[0]
        new_ep = None
        if piece in (WP, BP):
            if abs(nr - r) == 2:
                new_ep = ((r + nr) // 2, c)
            elif (nr, nc) == self.en_passant:
                self.board[r][nc] = EMPTY
        if piece == WK:
            self.castling["WK"] = self.castling["WQ"] = False
            if c == 4 and nc == 6: self.board[7][5] = WR; self.board[7][7] = EMPTY
            elif c == 4 and nc == 2: self.board[7][3] = WR; self.board[7][0] = EMPTY
        elif piece == BK:
            self.castling["BK"] = self.castling["BQ"] = False
            if c == 4 and nc == 6: self.board[0][5] = BR; self.board[0][7] = EMPTY
            elif c == 4 and nc == 2: self.board[0][3] = BR; self.board[0][0] = EMPTY
        elif piece == WR:
            if (r, c) == (7, 0): self.castling["WQ"] = False
            elif (r, c) == (7, 7): self.castling["WK"] = False
        elif piece == BR:
            if (r, c) == (0, 0): self.castling["BQ"] = False
            elif (r, c) == (0, 7): self.castling["BK"] = False
        self.board[nr][nc] = piece
        self.board[r][c] = EMPTY
        self.en_passant = new_ep
        if piece == WP and nr == 0: self.board[nr][nc] = WQ
        elif piece == BP and nr == 7: self.board[nr][nc] = BQ

    def make_move(self, r, c, nr, nc):
        piece = self.board[r][c]
        captured = self.board[nr][nc]
        note = f"{SYMBOLS.get(piece,'?')} {chr(ord('a')+c)}{8-r}→{chr(ord('a')+nc)}{8-nr}"
        self._apply_move(r, c, nr, nc)
        self.turn = "B" if self.turn == "W" else "W"
        self.move_history.append(note)
        return captured

    def get_all_legal_moves(self, color):
        moves = []
        saved = self.turn
        self.turn = color
        for r in range(8):
            for c in range(8):
                if self.board[r][c] != EMPTY and self.board[r][c][0] == color:
                    for nr, nc in self.get_legal_moves(r, c):
                        moves.append((r, c, nr, nc))
        self.turn = saved
        return moves

    def is_checkmate(self):
        return self.is_in_check(self.turn) and len(self.get_all_legal_moves(self.turn)) == 0

    def is_stalemate(self):
        return not self.is_in_check(self.turn) and len(self.get_all_legal_moves(self.turn)) == 0


# ── AI 엔진 ──────────────────────────────────────────────────
class ChessAI:
    def __init__(self, color="B", depth=2):
        self.color = color
        self.depth = depth

    def evaluate(self, board):
        score = 0
        for r in range(8):
            for c in range(8):
                piece = board.board[r][c]
                if piece == EMPTY: continue
                val = PIECE_VALUE[piece]
                wkey = "W" + piece[1:]
                pos = 0
                if wkey in POS_TABLE:
                    tbl = POS_TABLE[wkey]
                    pos = tbl[r][c] if piece[0] == "W" else tbl[7-r][c]
                total = val + pos
                score += total if piece[0] == self.color else -total
        return score

    def minimax(self, board, depth, alpha, beta, maximizing):
        if depth == 0:
            return self.evaluate(board), None
        color = self.color if maximizing else ("W" if self.color == "B" else "B")
        moves = board.get_all_legal_moves(color)
        if not moves:
            if board.is_in_check(color):
                return (-99999 if maximizing else 99999), None
            return 0, None
        best_move = None
        if maximizing:
            best = -float("inf")
            for r, c, nr, nc in moves:
                nb = copy.deepcopy(board)
                nb.make_move(r, c, nr, nc)
                val, _ = self.minimax(nb, depth-1, alpha, beta, False)
                if val > best:
                    best = val; best_move = (r, c, nr, nc)
                alpha = max(alpha, val)
                if beta <= alpha: break
            return best, best_move
        else:
            best = float("inf")
            for r, c, nr, nc in moves:
                nb = copy.deepcopy(board)
                nb.make_move(r, c, nr, nc)
                val, _ = self.minimax(nb, depth-1, alpha, beta, True)
                if val < best:
                    best = val; best_move = (r, c, nr, nc)
                beta = min(beta, val)
                if beta <= alpha: break
            return best, best_move

    def get_best_move(self, board):
        _, move = self.minimax(board, self.depth, -float("inf"), float("inf"), True)
        return move


# ── SVG 체스판 렌더러 ─────────────────────────────────────────
def render_board_svg(board, selected=None, legal_moves=None, last_move=None):
    CELL = 64
    MARGIN = 26
    SIZE = CELL * 8 + MARGIN * 2

    light, dark = "#F0D9B5", "#B58863"
    legal_set = set(legal_moves) if legal_moves else set()
    last_set = set()
    if last_move:
        r1, c1, r2, c2 = last_move
        last_set = {(r1, c1), (r2, c2)}

    parts = [
        f'<svg width="{SIZE}" height="{SIZE}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{SIZE}" height="{SIZE}" fill="#2C2C2C" rx="6"/>',
    ]

    for r in range(8):
        for c in range(8):
            x = MARGIN + c * CELL
            y = MARGIN + r * CELL
            fill = light if (r + c) % 2 == 0 else dark
            if (r, c) in last_set:
                fill = "#CDD16E"
            if selected == (r, c):
                fill = "#7FC97F"
            parts.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{fill}"/>')

            # 이동 가능 힌트
            if (r, c) in legal_set:
                if board[r][c] == EMPTY:
                    cx, cy = x + CELL//2, y + CELL//2
                    rad = CELL // 5
                    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{rad}" fill="#3DA53D" fill-opacity="0.65"/>')
                else:
                    parts.append(f'<rect x="{x+3}" y="{y+3}" width="{CELL-6}" height="{CELL-6}" fill="none" stroke="#3DA53D" stroke-width="4" rx="3"/>')

            # 기물
            piece = board[r][c]
            if piece != EMPTY:
                symbol = SYMBOLS[piece]
                fg = "white" if piece[0] == "W" else "#1A1A1A"
                sh = "#999" if piece[0] == "W" else "#555"
                px, py = x + CELL//2, y + CELL//2 + 11
                parts.append(f'<text x="{px+1}" y="{py+1}" text-anchor="middle" font-size="40" font-family="Segoe UI Symbol,Arial Unicode MS,serif" fill="{sh}">{symbol}</text>')
                parts.append(f'<text x="{px}" y="{py}" text-anchor="middle" font-size="40" font-family="Segoe UI Symbol,Arial Unicode MS,serif" fill="{fg}">{symbol}</text>')

    # 좌표 레이블
    for i in range(8):
        lc = light if i % 2 != 0 else dark
        parts.append(f'<text x="{MARGIN+i*CELL+CELL//2}" y="{SIZE-6}" text-anchor="middle" font-size="12" font-family="Arial" fill="{lc}" font-weight="bold">{chr(ord("a")+i)}</text>')
        parts.append(f'<text x="{12}" y="{MARGIN+i*CELL+CELL//2+5}" text-anchor="middle" font-size="12" font-family="Arial" fill="{lc}" font-weight="bold">{8-i}</text>')

    parts.append('</svg>')
    return '\n'.join(parts)


# ── 좌표 변환 헬퍼 ───────────────────────────────────────────
def pos_to_label(r, c):
    """(행, 열) → 'e2' 같은 체스 좌표"""
    return f"{chr(ord('a')+c)}{8-r}"

def label_to_pos(col_letter, row_num):
    """'e', 2 → (6, 4)"""
    c = ord(col_letter) - ord('a')
    r = 8 - row_num
    return r, c


# ── 세션 초기화 ───────────────────────────────────────────────
def init_game(player_color="W", depth=2):
    st.session_state.cg_game = ChessBoard()
    st.session_state.cg_player = player_color
    st.session_state.cg_ai_color = "B" if player_color == "W" else "W"
    st.session_state.cg_depth = depth
    st.session_state.cg_last_move = None
    st.session_state.cg_cap_player = []
    st.session_state.cg_cap_ai = []
    st.session_state.cg_status = "당신 차례입니다"
    st.session_state.cg_game_over = False
    # 플레이어가 흑이면 AI(백)가 먼저
    if player_color == "B":
        do_ai_move()

def do_ai_move():
    game = st.session_state.cg_game
    ai = ChessAI(color=st.session_state.cg_ai_color, depth=st.session_state.cg_depth)
    move = ai.get_best_move(game)
    if move:
        r, c, nr, nc = move
        captured = game.make_move(r, c, nr, nc)
        if captured != EMPTY:
            st.session_state.cg_cap_ai.append(SYMBOLS.get(captured, "?"))
        st.session_state.cg_last_move = (r, c, nr, nc)


# ── 메인 화면 ────────────────────────────────────────────────
if "cg_game" not in st.session_state:
    # ── 게임 시작 화면 ─────────────────────────────────────
    st.markdown("### 게임 설정")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**내 색상 선택**")
        color_choice = st.radio("색상", ["♔ 백(White) — 먼저 시작", "♚ 흑(Black) — 나중에 시작"],
                                label_visibility="collapsed")
    with col2:
        st.markdown("**AI 난이도**")
        diff_choice = st.radio("난이도", ["👶 쉬움", "🔰 보통", "⚔️ 어려움"],
                               label_visibility="collapsed")

    st.markdown("")
    if st.button("🎮 게임 시작", type="primary", use_container_width=True):
        player_color = "W" if "백" in color_choice else "B"
        depth = {"👶 쉬움": 1, "🔰 보통": 2, "⚔️ 어려움": 3}[diff_choice]
        if depth == 3:
            with st.spinner("AI 준비 중..."):
                init_game(player_color, depth)
        else:
            init_game(player_color, depth)
        st.rerun()

    st.divider()
    st.markdown("""
    **체스 규칙 요약**
    - 킹(♔)을 잡으면 이깁니다. 킹이 도망갈 수 없으면 **체크메이트**입니다.
    - 기물별 이동: 폰(♙) 앞으로만 / 룩(♖) 직선 / 비숍(♗) 대각선 / 나이트(♘) L자 / 퀸(♕) 전방향 / 킹(♔) 1칸
    - 폰이 상대 끝줄에 도달하면 퀸으로 자동 승격됩니다.
    """)

else:
    # ── 게임 진행 화면 ─────────────────────────────────────
    game: ChessBoard = st.session_state.cg_game
    player_color = st.session_state.cg_player
    ai_color = st.session_state.cg_ai_color
    game_over = st.session_state.cg_game_over

    col_board, col_side = st.columns([1, 0.6])

    # ── 왼쪽: 체스판 ───────────────────────────────────────
    with col_board:
        # 현재 "출발칸" 선택으로 합법 이동 미리 보기
        preview_legal = []
        preview_sel = None
        from_col_key = st.session_state.get("cg_from_col", "e")
        from_row_key = st.session_state.get("cg_from_row", 2 if player_color == "W" else 7)
        pr, pc = label_to_pos(from_col_key, from_row_key)
        if game.board[pr][pc] != EMPTY and game.board[pr][pc][0] == player_color and not game_over:
            preview_legal = game.get_legal_moves(pr, pc)
            preview_sel = (pr, pc)

        svg = render_board_svg(
            game.board,
            selected=preview_sel,
            legal_moves=preview_legal,
            last_move=st.session_state.cg_last_move,
        )
        st.markdown(f'<div style="display:flex;justify-content:center;">{svg}</div>',
                    unsafe_allow_html=True)
        st.caption("초록 원 = 이동 가능한 칸 | 노란 칸 = 마지막 이동")

    # ── 오른쪽: 조작 패널 ──────────────────────────────────
    with col_side:
        # 상태 메시지
        status = st.session_state.cg_status
        if game_over:
            st.error(status)
        elif "체크" in status:
            st.warning(status)
        else:
            st.info(status)

        # 차례 표시
        if not game_over:
            if game.turn == player_color:
                st.markdown(f"**현재 차례:** {'♔ 내 차례 (백)' if player_color == 'W' else '♚ 내 차례 (흑)'}")
            else:
                st.markdown("**현재 차례:** 🤖 AI 차례")

        st.divider()

        # 이동 입력 (내 차례일 때만)
        if not game_over and game.turn == player_color:
            st.markdown("**이동할 기물 선택 (출발칸)**")
            col_a, col_b = st.columns(2)
            with col_a:
                from_col = st.selectbox("열", list("abcdefgh"), key="cg_from_col",
                                        label_visibility="collapsed")
            with col_b:
                row_opts = list(range(8, 0, -1))
                from_row = st.selectbox("행", row_opts, key="cg_from_row",
                                        label_visibility="collapsed")

            # 선택한 출발칸의 합법 이동 목록 계산
            sr, sc = label_to_pos(from_col, from_row)
            legal = []
            if game.board[sr][sc] != EMPTY and game.board[sr][sc][0] == player_color:
                legal = game.get_legal_moves(sr, sc)

            st.markdown("**이동할 위치 (도착칸)**")
            if legal:
                dest_labels = [pos_to_label(nr, nc) for nr, nc in legal]
                dest_choice = st.selectbox("도착", dest_labels, label_visibility="collapsed",
                                           key="cg_dest")
                dest_col = dest_choice[0]
                dest_row = int(dest_choice[1])
                dr, dc = label_to_pos(dest_col, dest_row)
            else:
                st.selectbox("도착", ["—"], label_visibility="collapsed",
                             disabled=True, key="cg_dest_empty")
                st.caption("선택한 칸에 내 기물이 없거나 이동 불가")
                dr, dc = None, None

            if st.button("♟ 이동", type="primary", use_container_width=True,
                         disabled=(not legal or dr is None), key="cg_move"):
                # 플레이어 이동
                captured = game.make_move(sr, sc, dr, dc)
                if captured != EMPTY:
                    st.session_state.cg_cap_player.append(SYMBOLS.get(captured, "?"))
                st.session_state.cg_last_move = (sr, sc, dr, dc)

                # 종료 체크
                if game.is_checkmate():
                    st.session_state.cg_status = "🎉 체크메이트! 당신이 이겼습니다!"
                    st.session_state.cg_game_over = True
                elif game.is_stalemate():
                    st.session_state.cg_status = "🤝 스테일메이트 — 무승부입니다."
                    st.session_state.cg_game_over = True
                else:
                    # AI 이동
                    st.session_state.cg_status = "AI가 생각 중..."
                    with st.spinner("AI가 생각 중..."):
                        do_ai_move()
                    # AI 이동 후 종료 체크
                    if game.is_checkmate():
                        st.session_state.cg_status = "😢 체크메이트! AI가 이겼습니다."
                        st.session_state.cg_game_over = True
                    elif game.is_stalemate():
                        st.session_state.cg_status = "🤝 스테일메이트 — 무승부입니다."
                        st.session_state.cg_game_over = True
                    elif game.is_in_check(game.turn):
                        st.session_state.cg_status = "⚠️ 체크! 왕을 지키세요!"
                    else:
                        st.session_state.cg_status = "당신 차례입니다"
                st.rerun()

        st.divider()

        # 잡은 기물
        cap_p = " ".join(st.session_state.cg_cap_player)
        cap_a = " ".join(st.session_state.cg_cap_ai)
        st.markdown(f"**내가 잡은 기물:** {cap_p or '—'}")
        st.markdown(f"**AI가 잡은 기물:** {cap_a or '—'}")

        st.divider()

        # 이동 기록
        if game.move_history:
            with st.expander("📋 이동 기록", expanded=False):
                for i, note in enumerate(game.move_history):
                    prefix = f"{(i//2)+1}." if i % 2 == 0 else "   "
                    st.text(f"{prefix} {note}")

        st.divider()
        if st.button("🔄 새 게임", use_container_width=True, key="cg_new"):
            for k in list(st.session_state.keys()):
                if k.startswith("cg_"):
                    del st.session_state[k]
            st.rerun()
