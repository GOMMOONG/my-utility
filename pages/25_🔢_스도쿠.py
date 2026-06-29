import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="스도쿠 - 마이 유틸리티", page_icon="🔢", layout="wide")
apply_common_style()
check_password()
show_page_header("🔢", "스도쿠 학습", "입문부터 중급까지 — 스도쿠를 체계적으로 배워보세요")

SUDOKU_HTML = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: '맑은 고딕', 'Malgun Gothic', sans-serif; background: #F8F9FA; color: #333; padding: 8px; }

.container { display: flex; gap: 18px; align-items: flex-start; }
.left  { flex: 0 0 auto; }
.right { flex: 1; min-width: 180px; max-width: 260px; }

/* 퍼즐 선택 버튼 */
.selector-row { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 7px; }
.puzzle-btn {
    padding: 5px 10px; border: 1.5px solid #90CAF9;
    background: #E3F2FD; color: #1565C0;
    border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold;
}
.puzzle-btn.active { background: #1565C0; color: white; border-color: #1565C0; }
.puzzle-btn:hover:not(.active) { background: #BBDEFB; }

/* 랜덤 생성 버튼 */
.rand-row { display: flex; align-items: center; gap: 5px; margin-bottom: 9px; flex-wrap: wrap; }
.rand-label { font-size: 12px; color: #555; white-space: nowrap; }
.rand-btn {
    padding: 5px 10px; border: none; border-radius: 6px;
    cursor: pointer; font-size: 11px; font-weight: bold; color: white;
}
.rand-easy   { background: #66BB6A; }
.rand-normal { background: #FFA726; }
.rand-hard   { background: #EF5350; }
.rand-btn:hover { opacity: 0.85; }

/* 팁 */
.tip {
    font-size: 12px; color: #1B5E20; background: #E8F5E9;
    border-left: 3px solid #4CAF50; padding: 6px 10px;
    border-radius: 4px; margin-bottom: 9px; max-width: 488px;
    min-height: 28px; line-height: 1.5;
}

/* 스도쿠 그리드 */
.grid-outer { border: 3px solid #263238; display: inline-block; line-height: 0; }
table.sudoku { border-collapse: collapse; }
.cell {
    width: 52px; height: 52px;
    text-align: center; vertical-align: middle;
    font-size: 20px; font-weight: bold;
    border: 1px solid #90A4AE;
    cursor: pointer; user-select: none; -webkit-user-select: none;
    transition: background 0.1s;
    position: relative;
}
.cell.br { border-right: 2.5px solid #263238; }
.cell.bb { border-bottom: 2.5px solid #263238; }
.cell.fixed     { color: #1A1A2E; cursor: default; }
.cell.user-in   { color: #1565C0; }
.cell.err       { color: #C62828; }
.cell.hint-cl   { color: #2E7D32; }
.cell.selected  { background: #BBDEFB !important; }
.cell.related   { background: #E3F2FD; }
.cell.same-num  { background: #C8E6C9; }

/* 숫자 버튼 */
.num-row { display: flex; gap: 4px; margin-top: 10px; }
.num-btn {
    width: 44px; height: 40px;
    border: 1.5px solid #90CAF9; background: #E3F2FD;
    color: #1565C0; font-size: 18px; font-weight: bold;
    border-radius: 6px; cursor: pointer;
}
.num-btn:hover { background: #BBDEFB; }
.del-btn {
    width: 58px; height: 40px;
    border: 1.5px solid #FFCDD2; background: #FFEBEE;
    color: #C62828; font-size: 12px; font-weight: bold;
    border-radius: 6px; cursor: pointer; margin-left: 4px;
}
.del-btn:hover { background: #FFCDD2; }

/* 컨트롤 버튼 */
.ctrl-row { display: flex; gap: 5px; margin-top: 8px; flex-wrap: wrap; }
.ctrl-btn {
    padding: 7px 12px; border: none; border-radius: 8px;
    cursor: pointer; font-size: 12px; font-weight: bold;
}
.btn-check  { background: #E8F5E9; color: #2E7D32; }
.btn-hint   { background: #FFF9C4; color: #F57F17; }
.btn-solve  { background: #EDE7F6; color: #6A1B9A; }
.btn-reset  { background: #FCE4EC; color: #B71C1C; }
.btn-tut    { background: #E3F2FD; color: #0D47A1; }
.ctrl-btn:hover { opacity: 0.8; }

/* 상태 바 */
.status-row { display: flex; gap: 20px; margin-top: 10px; font-size: 13px; color: #555; }
.status-item span { font-weight: bold; color: #1565C0; }

/* 가이드 */
.guide-title { font-size: 13px; font-weight: bold; color: #1565C0; margin-bottom: 8px; }
.guide-box {
    font-size: 12px; line-height: 1.8; color: #37474F;
    height: 600px; overflow-y: auto;
    background: white; border: 1px solid #E0E0E0;
    border-radius: 8px; padding: 12px;
    white-space: pre-line;
}

/* 모달 오버레이 */
.modal-mask {
    display: none; position: fixed; top:0; left:0;
    width:100%; height:100%; background: rgba(0,0,0,0.5);
    z-index: 200; align-items: center; justify-content: center;
}
.modal-mask.show { display: flex; }
.modal-box {
    background: white; border-radius: 12px; padding: 22px;
    max-width: 500px; width: 95%; box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    max-height: 90vh; overflow-y: auto;
}
.modal-box h2 { font-size: 17px; color: #1565C0; margin-bottom: 10px; }
.modal-step { font-size: 12px; color: #888; margin-bottom: 4px; }
.modal-text { font-size: 13px; line-height: 1.8; color: #333; margin-bottom: 14px; white-space: pre-line; }
.tut-grid-wrap { display: flex; justify-content: center; margin-bottom: 14px; }
table.tut-tbl { border-collapse: collapse; border: 2.5px solid #263238; }
.tcell {
    width: 38px; height: 38px;
    text-align: center; vertical-align: middle;
    font-size: 15px; font-weight: bold;
    border: 1px solid #90A4AE;
}
.tcell.tbr { border-right: 2.5px solid #263238; }
.tcell.tbb { border-bottom: 2.5px solid #263238; }
.tcell.t-fixed { color: #1A1A2E; }
.tcell.t-hl1  { background: #FFF9C4; color: #F57F17; }
.tcell.t-hl2  { background: #C8E6C9; color: #2E7D32; }
.tcell.t-hl3  { background: #BBDEFB; color: #1565C0; }
.tcell.t-ans  { color: #2E7D32; font-size: 17px; }
.modal-nav { display: flex; justify-content: space-between; gap: 10px; margin-top: 6px; }
.modal-nav-btn {
    flex: 1; padding: 10px; border: none; border-radius: 8px;
    cursor: pointer; font-size: 14px; font-weight: bold;
}
.btn-prev { background: #ECEFF1; color: #455A64; }
.btn-next { background: #1565C0; color: white; }
.btn-close-modal { background: #E8F5E9; color: #2E7D32; margin-top: 0; }

/* 모바일 */
@media (max-width: 640px) {
    .container { flex-direction: column; }
    .right { max-width: 100%; width: 100%; }
    .cell { width: 38px; height: 38px; font-size: 15px; }
    .num-btn { width: 34px; height: 36px; font-size: 15px; }
}
</style>
</head>
<body>

<!-- ══════════════════════ 메인 레이아웃 ══════════════════════ -->
<div class="container">
  <!-- 왼쪽: 게임 영역 -->
  <div class="left">

    <!-- 고정 퍼즐 선택 -->
    <div class="selector-row" id="pzBtns"></div>

    <!-- 랜덤 생성 버튼 -->
    <div class="rand-row">
      <span class="rand-label">🎲 랜덤 생성 →</span>
      <button class="rand-btn rand-easy"   onclick="loadRandom('쉬움')">⭐ 쉬움</button>
      <button class="rand-btn rand-normal" onclick="loadRandom('보통')">⭐⭐ 보통</button>
      <button class="rand-btn rand-hard"   onclick="loadRandom('어려움')">⭐⭐⭐ 어려움</button>
    </div>

    <!-- 팁 -->
    <div class="tip" id="tipLabel">퍼즐을 선택하거나 랜덤 생성 버튼을 눌러 시작하세요!</div>

    <!-- 스도쿠 그리드 -->
    <div class="grid-outer">
      <table class="sudoku" id="gridTable"></table>
    </div>

    <!-- 숫자 버튼 -->
    <div class="num-row" id="numBtns"></div>

    <!-- 컨트롤 버튼 -->
    <div class="ctrl-row">
      <button class="ctrl-btn btn-check"  onclick="checkAnswer()">✅ 정답 확인</button>
      <button class="ctrl-btn btn-hint"   onclick="getHint()">💡 힌트</button>
      <button class="ctrl-btn btn-solve"  onclick="autoSolve()">🔓 자동풀기</button>
      <button class="ctrl-btn btn-reset"  onclick="resetPuzzle()">🔄 초기화</button>
      <button class="ctrl-btn btn-tut"    onclick="openTutorial()">📖 튜토리얼</button>
    </div>

    <!-- 상태 바 -->
    <div class="status-row">
      <div class="status-item">실수: <span id="mistakeCnt">0</span>번</div>
      <div class="status-item">시간: <span id="timerLbl">00:00</span></div>
    </div>
  </div>

  <!-- 오른쪽: 학습 가이드 -->
  <div class="right">
    <div class="guide-title">📚 학습 가이드</div>
    <div class="guide-box" id="guideBox"></div>
  </div>
</div>

<!-- ══════════════════════ 튜토리얼 모달 ══════════════════════ -->
<div class="modal-mask" id="tutModal">
  <div class="modal-box">
    <div class="modal-step" id="tutStep"></div>
    <h2 id="tutTitle"></h2>
    <div class="modal-text" id="tutText"></div>
    <div class="tut-grid-wrap" id="tutGridWrap"></div>
    <div class="modal-nav">
      <button class="modal-nav-btn btn-prev" onclick="tutNav(-1)">◀ 이전</button>
      <button class="modal-nav-btn btn-next" onclick="tutNav(1)"  id="tutNextBtn">다음 ▶</button>
    </div>
    <div class="modal-nav" style="margin-top:8px;">
      <button class="modal-nav-btn btn-close-modal" onclick="closeTutorial()">✅ 튜토리얼 닫기</button>
    </div>
  </div>
</div>

<script>
// ══════════════════════════════════════════════
// 1. 퍼즐 데이터 (고정 4개)
// ══════════════════════════════════════════════
const PUZZLES = [
  {
    name: '★ 입문 1',
    tip:  '💡 숫자가 많이 채워진 가로줄을 먼저 찾아보세요. 빈 칸이 1~2개인 줄은 쉽게 채울 수 있어요!',
    grid: [
      [5,3,0,0,7,0,0,0,0],
      [6,0,0,1,9,5,0,0,0],
      [0,9,8,0,0,0,0,6,0],
      [8,0,0,0,6,0,0,0,3],
      [4,0,0,8,0,3,0,0,1],
      [7,0,0,0,2,0,0,0,6],
      [0,6,0,0,0,0,2,8,0],
      [0,0,0,4,1,9,0,0,5],
      [0,0,0,0,8,0,0,7,9],
    ]
  },
  {
    name: '★★ 초급 1',
    tip:  '💡 각 3×3 박스 안에 아직 없는 숫자가 어느 칸에 들어갈 수 있는지 박스별로 확인해보세요!',
    grid: [
      [0,0,0,2,6,0,7,0,1],
      [6,8,0,0,7,0,0,9,0],
      [1,9,0,0,0,4,5,0,0],
      [8,2,0,1,0,0,0,4,0],
      [0,0,4,6,0,2,9,0,0],
      [0,5,0,0,0,3,0,2,8],
      [0,0,9,3,0,0,0,7,4],
      [0,4,0,0,5,0,0,3,6],
      [7,0,3,0,1,8,0,0,0],
    ]
  },
  {
    name: '★★ 초급 2',
    tip:  '💡 대칭 모양의 퍼즐이에요. 각 숫자가 행·열·박스 중 어느 한 곳에만 들어갈 수 있는지 찾아보세요!',
    grid: [
      [0,0,3,0,2,0,6,0,0],
      [9,0,0,3,0,5,0,0,1],
      [0,0,1,8,0,6,4,0,0],
      [0,0,8,1,0,2,9,0,0],
      [7,0,0,0,0,0,0,0,8],
      [0,0,6,7,0,8,2,0,0],
      [0,0,2,6,0,9,5,0,0],
      [8,0,0,2,0,3,0,0,9],
      [0,0,5,0,1,0,3,0,0],
    ]
  },
  {
    name: '★★★ 중급 1',
    tip:  '💡 [힌트] 버튼으로 각 칸의 후보수를 확인하고, 후보수가 1개인 칸부터 채워보세요!',
    grid: [
      [8,0,0,0,0,0,0,0,0],
      [0,0,3,6,0,0,0,0,0],
      [0,7,0,0,9,0,2,0,0],
      [0,5,0,0,0,7,0,0,0],
      [0,0,0,0,4,5,7,0,0],
      [0,0,0,1,0,0,0,3,0],
      [0,0,1,0,0,0,0,6,8],
      [0,0,8,5,0,0,0,1,0],
      [0,9,0,0,0,0,4,0,0],
    ]
  },
];

// ══════════════════════════════════════════════
// 2. 학습 가이드 텍스트
// ══════════════════════════════════════════════
const GUIDE_TEXT = `📖 스도쿠 기본 규칙
━━━━━━━━━━━━━━━━━━━━━━
스도쿠는 9×9 칸으로 이루어진
숫자 퍼즐입니다.

✅ 규칙 3가지
① 각 가로줄(행): 1~9가 한 번씩
② 각 세로줄(열): 1~9가 한 번씩
③ 3×3 박스: 1~9가 한 번씩

같은 숫자가 같은 행·열·박스에
두 번 나오면 안 됩니다!


🔍 기술 1: 나홀로 후보수
━━━━━━━━━━━━━━━━━━━━━━
가장 기본적인 풀이 기술입니다.

방법:
① 빈 칸 하나를 선택합니다
② 같은 행, 열, 박스에 있는
   숫자를 모두 확인합니다
③ 1~9 중 들어갈 수 없는
   숫자를 제거합니다
④ 딱 하나만 남으면 → 정답!

예시:
같은 행에 1,2,3,4,5,6,7,8이
있다면 → 그 칸에는 반드시 9!


🎯 기술 2: 숨겨진 나홀로
━━━━━━━━━━━━━━━━━━━━━━
한 행(또는 열, 박스)에서
특정 숫자가 들어갈 수 있는
칸이 딱 하나뿐이라면
→ 그 칸 = 그 숫자!


💡 기술 3: 후보수 메모
━━━━━━━━━━━━━━━━━━━━━━
어려운 퍼즐에서 유용합니다.

각 빈 칸에 들어갈 수 있는
숫자들을 머릿속에 메모하면:
• 후보수 1개 → 바로 채우기
• 패턴 발견이 쉬워집니다


🚀 풀이 순서
━━━━━━━━━━━━━━━━━━━━━━
① 숫자가 많은 행·열·박스부터
② 나홀로 후보수로 풀 수 있는
   칸 찾기
③ 숨겨진 나홀로 찾기
④ 막히면 [힌트] 버튼 활용


🎨 색상 의미
━━━━━━━━━━━━━━━━━━━━━━
⚫ 검정 굵은 글씨: 처음 주어진 숫자
🔵 파란 글씨: 내가 입력한 숫자
🔴 빨간 글씨: 틀린 숫자
🟢 초록 글씨: 힌트로 채운 숫자


⌨️ 사용 방법
━━━━━━━━━━━━━━━━━━━━━━
• 칸 클릭 후 숫자 버튼 누르기
• 키보드 숫자키도 사용 가능
• 화살표 키로 칸 이동 가능
• Delete/Backspace: 숫자 지우기`;

// ══════════════════════════════════════════════
// 3. 게임 로직 함수들
// ══════════════════════════════════════════════
function isValid(g, r, c, n) {
    for (let i = 0; i < 9; i++) {
        if (g[r][i] === n) return false;
        if (g[i][c] === n) return false;
    }
    const br = Math.floor(r / 3) * 3, bc = Math.floor(c / 3) * 3;
    for (let i = 0; i < 3; i++)
        for (let j = 0; j < 3; j++)
            if (g[br+i][bc+j] === n) return false;
    return true;
}

function getCandidates(g, r, c) {
    if (g[r][c] !== 0) return [];
    return [1,2,3,4,5,6,7,8,9].filter(n => isValid(g, r, c, n));
}

function solve(g) {
    const flat = g.flat();
    const idx = flat.indexOf(0);
    if (idx === -1) return g.map(r => r.slice());
    const r = Math.floor(idx / 9), c = idx % 9;
    for (let n = 1; n <= 9; n++) {
        if (isValid(g, r, c, n)) {
            g[r][c] = n;
            const res = solve(g);
            if (res) return res;
            g[r][c] = 0;
        }
    }
    return null;
}

// 랜덤 퍼즐 생성
function generateFullGrid() {
    const g = Array.from({length:9}, () => Array(9).fill(0));
    function fill(pos) {
        if (pos === 81) return true;
        const r = Math.floor(pos / 9), c = pos % 9;
        const nums = [1,2,3,4,5,6,7,8,9].sort(() => Math.random() - 0.5);
        for (const n of nums) {
            if (isValid(g, r, c, n)) {
                g[r][c] = n;
                if (fill(pos + 1)) return true;
                g[r][c] = 0;
            }
        }
        return false;
    }
    return fill(0) ? g : null;
}

function countSolutions(g, limit = 2) {
    let count = 0;
    const grid = g.map(r => r.slice());
    function bt() {
        if (count >= limit) return;
        // MRV: 후보수가 가장 적은 빈 칸 선택
        let bR = -1, bC = -1, bCands = null, bN = 10;
        for (let r = 0; r < 9; r++) {
            for (let c = 0; c < 9; c++) {
                if (grid[r][c] === 0) {
                    const cands = getCandidates(grid, r, c);
                    if (cands.length === 0) return;
                    if (cands.length < bN) {
                        bR = r; bC = c; bCands = cands; bN = cands.length;
                        if (bN === 1) break;
                    }
                }
            }
            if (bN === 1) break;
        }
        if (bR === -1) { count++; return; }
        for (const n of bCands) {
            grid[bR][bC] = n; bt(); grid[bR][bC] = 0;
            if (count >= limit) return;
        }
    }
    bt();
    return count;
}

function generateSudoku(difficulty) {
    const solution = generateFullGrid();
    if (!solution) return null;
    const puzzle = solution.map(r => r.slice());
    const targets = { '쉬움': 36, '보통': 46, '어려움': 52 };
    const target = targets[difficulty];
    const positions = [];
    for (let r = 0; r < 9; r++)
        for (let c = 0; c < 9; c++)
            positions.push([r, c]);
    positions.sort(() => Math.random() - 0.5);
    let removed = 0;
    for (const [r, c] of positions) {
        if (removed >= target) break;
        const val = puzzle[r][c];
        puzzle[r][c] = 0;
        if (countSolutions(puzzle) === 1) removed++;
        else puzzle[r][c] = val;
    }
    return { puzzle, solution };
}

// ══════════════════════════════════════════════
// 4. 게임 상태
// ══════════════════════════════════════════════
let puzzle    = null;    // 초기 퍼즐 (0=빈 칸)
let solution  = null;    // 정답
let userGrid  = null;    // 사용자 입력 포함 그리드
let fixedCell = null;    // 처음부터 주어진 칸 여부
let hintCells = new Set();
let selected  = null;    // [r, c]
let mistakes  = 0;
let startTime = null;
let timerID   = null;
let puzzleIdx = -1;      // -1=랜덤, 0~3=고정
let randData  = null;    // 랜덤 퍼즐 보관 (초기화용)

// ══════════════════════════════════════════════
// 5. 그리드 그리기
// ══════════════════════════════════════════════
function buildGrid() {
    const tbl = document.getElementById('gridTable');
    tbl.innerHTML = '';
    for (let r = 0; r < 9; r++) {
        const tr = document.createElement('tr');
        for (let c = 0; c < 9; c++) {
            const td = document.createElement('td');
            td.className = 'cell';
            if (c === 2 || c === 5) td.classList.add('br');
            if (r === 2 || r === 5) td.classList.add('bb');
            td.dataset.r = r;
            td.dataset.c = c;
            td.addEventListener('click', () => selectCell(r, c));
            tr.appendChild(td);
        }
        tbl.appendChild(tr);
    }
}

function renderGrid() {
    if (!puzzle) return;
    const cells = document.querySelectorAll('.cell');
    const selN = selected ? userGrid[selected[0]][selected[1]] : 0;
    cells.forEach(td => {
        const r = +td.dataset.r, c = +td.dataset.c;
        const v = userGrid[r][c];
        const key = r * 9 + c;
        const isSel = selected && selected[0] === r && selected[1] === c;
        const isRel = !isSel && selected &&
            (selected[0] === r || selected[1] === c ||
             (Math.floor(selected[0]/3) === Math.floor(r/3) &&
              Math.floor(selected[1]/3) === Math.floor(c/3)));
        const isSame = !isSel && selN > 0 && v === selN;

        td.className = 'cell';
        if (c === 2 || c === 5) td.classList.add('br');
        if (r === 2 || r === 5) td.classList.add('bb');

        if (isSel)        td.classList.add('selected');
        else if (isSame)  td.classList.add('same-num');
        else if (isRel)   td.classList.add('related');

        if (fixedCell[r][c]) {
            td.classList.add('fixed');
        } else if (hintCells.has(key)) {
            td.classList.add('hint-cl');
        } else if (v !== 0 && v !== solution[r][c]) {
            td.classList.add('err');
        } else if (v !== 0) {
            td.classList.add('user-in');
        }
        td.textContent = v || '';
    });
}

// ══════════════════════════════════════════════
// 6. 퍼즐 로드
// ══════════════════════════════════════════════
function loadPuzzle(idx) {
    puzzleIdx = idx;
    const p = PUZZLES[idx];
    puzzle   = p.grid.map(r => r.slice());
    solution = solve(p.grid.map(r => r.slice()));
    initGame(puzzle, solution, p.tip);

    // 버튼 강조
    document.querySelectorAll('.puzzle-btn').forEach((b, i) => {
        b.classList.toggle('active', i === idx);
    });
}

function loadRandom(difficulty) {
    document.getElementById('tipLabel').textContent = `🔄 ${difficulty} 퍼즐을 생성 중이에요... 잠깐만요!`;
    // 비동기로 처리 (UI 업데이트 후 생성)
    setTimeout(() => {
        let result = null;
        for (let i = 0; i < 3; i++) {
            result = generateSudoku(difficulty);
            if (result) break;
        }
        if (!result) {
            document.getElementById('tipLabel').textContent = '❌ 생성 실패. 다시 눌러주세요.';
            return;
        }
        puzzleIdx = -1;
        randData  = result;
        puzzle    = result.puzzle.map(r => r.slice());
        solution  = result.solution;
        const empty = puzzle.flat().filter(v => v === 0).length;
        const tips  = {
            '쉬움':   `💡 랜덤 생성 쉬움 (빈 칸 ${empty}개) — 나홀로 후보수로 대부분 풀 수 있어요!`,
            '보통':   `💡 랜덤 생성 보통 (빈 칸 ${empty}개) — 숨겨진 나홀로 기술도 써보세요!`,
            '어려움': `💡 랜덤 생성 어려움 (빈 칸 ${empty}개) — [힌트] 버튼을 적극 활용하세요!`,
        };
        initGame(puzzle, solution, tips[difficulty]);
        document.querySelectorAll('.puzzle-btn').forEach(b => b.classList.remove('active'));
    }, 30);
}

function initGame(pz, sol, tip) {
    puzzle    = pz.map(r => r.slice());
    solution  = sol;
    userGrid  = pz.map(r => r.slice());
    fixedCell = pz.map(r => r.map(v => v !== 0));
    hintCells = new Set();
    selected  = null;
    mistakes  = 0;
    document.getElementById('mistakeCnt').textContent = '0';
    document.getElementById('tipLabel').textContent   = tip;
    if (timerID) clearInterval(timerID);
    startTime = Date.now();
    timerID   = setInterval(updateTimer, 1000);
    updateTimer();
    renderGrid();
}

// ══════════════════════════════════════════════
// 7. 인터랙션
// ══════════════════════════════════════════════
function selectCell(r, c) {
    selected = [r, c];
    renderGrid();
}

function inputNumber(n) {
    if (!selected || !puzzle) return;
    const [r, c] = selected;
    if (fixedCell[r][c]) return;
    const key = r * 9 + c;
    hintCells.delete(key);
    if (n === 0) {
        userGrid[r][c] = 0;
    } else {
        if (userGrid[r][c] !== 0 && userGrid[r][c] !== solution[r][c]) {
            // 이미 틀린 숫자가 있을 때 교체해도 실수 카운트 추가 안 함
        } else if (userGrid[r][c] === 0 && n !== solution[r][c]) {
            mistakes++;
            document.getElementById('mistakeCnt').textContent = mistakes;
        }
        userGrid[r][c] = n;
    }
    renderGrid();
    checkComplete();
}

function checkComplete() {
    const done = userGrid.every((row, r) =>
        row.every((v, c) => v !== 0 && v === solution[r][c])
    );
    if (done) {
        clearInterval(timerID);
        const elapsed = formatTime(Date.now() - startTime);
        setTimeout(() => alert(`🎉 완성! 정말 잘 하셨어요!\n소요 시간: ${elapsed}  실수: ${mistakes}번`), 100);
    }
}

document.addEventListener('keydown', e => {
    if (document.getElementById('tutModal').classList.contains('show')) return;
    if (!selected) return;
    const [r, c] = selected;
    if (e.key >= '1' && e.key <= '9') { inputNumber(+e.key); return; }
    if (e.key === '0' || e.key === 'Backspace' || e.key === 'Delete') { inputNumber(0); return; }
    if (e.key === 'ArrowUp'    && r > 0) { selected = [r-1, c]; renderGrid(); }
    if (e.key === 'ArrowDown'  && r < 8) { selected = [r+1, c]; renderGrid(); }
    if (e.key === 'ArrowLeft'  && c > 0) { selected = [r, c-1]; renderGrid(); }
    if (e.key === 'ArrowRight' && c < 8) { selected = [r, c+1]; renderGrid(); }
    e.preventDefault();
});

// ══════════════════════════════════════════════
// 8. 컨트롤 버튼 기능
// ══════════════════════════════════════════════
function checkAnswer() {
    if (!puzzle) return;
    let empty = 0, wrong = 0;
    userGrid.forEach((row, r) => row.forEach((v, c) => {
        if (!fixedCell[r][c]) {
            if (v === 0) empty++;
            else if (v !== solution[r][c]) wrong++;
        }
    }));
    if (empty === 0 && wrong === 0) alert('🎉 완벽합니다! 모두 정답이에요!');
    else alert(`📊 확인 결과\n남은 빈 칸: ${empty}개\n틀린 숫자: ${wrong}개`);
}

function getHint() {
    if (!puzzle || !selected) { alert('💡 칸을 먼저 클릭해서 선택해주세요!'); return; }
    const [r, c] = selected;
    if (fixedCell[r][c]) { alert('💡 이 칸은 처음부터 주어진 숫자예요.'); return; }
    if (userGrid[r][c] === solution[r][c]) { alert('💡 이 칸은 이미 정답이에요!'); return; }
    const cands = getCandidates(userGrid, r, c);
    if (cands.length === 0) { alert('⚠️ 이 칸에 들어갈 수 있는 숫자가 없어요.\n다른 칸에 오류가 있는지 확인해보세요.'); return; }
    if (cands.length === 1) {
        if (confirm(`💡 이 칸에는 [${cands[0]}]만 들어갈 수 있어요!\n자동으로 채울까요?`)) {
            userGrid[r][c] = cands[0];
            hintCells.add(r * 9 + c);
            renderGrid();
            checkComplete();
        }
    } else {
        alert(`💡 이 칸의 후보수: ${cands.join(', ')}\n\n정답: ${solution[r][c]}`);
    }
}

function autoSolve() {
    if (!puzzle) return;
    if (!confirm('🔓 정답을 모두 채울까요?')) return;
    for (let r = 0; r < 9; r++)
        for (let c = 0; c < 9; c++)
            userGrid[r][c] = solution[r][c];
    hintCells = new Set();
    renderGrid();
    clearInterval(timerID);
}

function resetPuzzle() {
    if (!puzzle) return;
    if (!confirm('🔄 입력한 내용을 모두 지울까요?')) return;
    if (puzzleIdx >= 0) {
        loadPuzzle(puzzleIdx);
    } else if (randData) {
        puzzle   = randData.puzzle.map(r => r.slice());
        solution = randData.solution;
        const tip = document.getElementById('tipLabel').textContent;
        initGame(puzzle, solution, tip);
    }
}

// ══════════════════════════════════════════════
// 9. 타이머
// ══════════════════════════════════════════════
function formatTime(ms) {
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60);
    return `${String(m).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;
}
function updateTimer() {
    if (!startTime) return;
    document.getElementById('timerLbl').textContent = formatTime(Date.now() - startTime);
}

// ══════════════════════════════════════════════
// 10. 튜토리얼
// ══════════════════════════════════════════════
// 예시에 쓸 작은 9×9 그리드 (위키피디아 스도쿠 예제)
const TUT_FULL = [
    [5,3,4,6,7,8,9,1,2],
    [6,7,2,1,9,5,3,4,8],
    [1,9,8,3,4,2,5,6,7],
    [8,5,9,7,6,1,4,2,3],
    [4,2,6,8,5,3,7,9,1],
    [7,1,3,9,2,4,8,5,6],
    [9,6,1,5,3,7,2,8,4],
    [2,8,7,4,1,9,6,3,5],
    [3,4,5,2,8,6,1,7,9],
];

// 빈 칸들이 있는 예제 퍼즐 (튜토리얼용)
const TUT_PUZZLE = [
    [5,3,0,0,7,0,0,0,0],
    [6,0,0,1,9,5,0,0,0],
    [0,9,8,0,0,0,0,6,0],
    [8,0,0,0,6,0,0,0,3],
    [4,0,0,8,0,3,0,0,1],
    [7,0,0,0,2,0,0,0,6],
    [0,6,0,0,0,0,2,8,0],
    [0,0,0,4,1,9,0,0,5],
    [0,0,0,0,8,0,0,7,9],
];

const TUT_STEPS = [
    {
        title: '스도쿠란 무엇인가요?',
        text: `스도쿠는 9×9 칸에 1부터 9까지의 숫자를 채우는 퍼즐입니다.

처음부터 일부 숫자가 주어지고,
나머지 빈 칸을 규칙에 맞게 채우면 됩니다.

오른쪽 그리드를 보세요 — 검정 숫자들이
처음부터 주어진 숫자들입니다.`,
        grid: TUT_PUZZLE,
        hl: {},
    },
    {
        title: '규칙 ① — 가로줄(행)',
        text: `첫 번째 규칙:
각 가로줄(행)에 1~9가 각각 한 번씩만 있어야 합니다.

노란색으로 강조된 가로줄을 보세요.
5, 3이 있고, 나머지 7칸에
1, 2, 4, 6, 7, 8, 9가 들어가야 합니다.`,
        grid: TUT_PUZZLE,
        hl: {
            '00':'t-hl1','01':'t-hl1','02':'t-hl1',
            '03':'t-hl1','04':'t-hl1','05':'t-hl1',
            '06':'t-hl1','07':'t-hl1','08':'t-hl1',
        },
    },
    {
        title: '규칙 ② — 세로줄(열)',
        text: `두 번째 규칙:
각 세로줄(열)에도 1~9가 각각 한 번씩만 있어야 합니다.

파란색으로 강조된 세로줄을 보세요.
5, 9, 8이 있으니 나머지 칸에
1, 2, 3, 4, 6, 7이 들어가야 합니다.`,
        grid: TUT_PUZZLE,
        hl: {
            '02':'t-hl3','12':'t-hl3','22':'t-hl3',
            '32':'t-hl3','42':'t-hl3','52':'t-hl3',
            '62':'t-hl3','72':'t-hl3','82':'t-hl3',
        },
    },
    {
        title: '규칙 ③ — 3×3 박스',
        text: `세 번째 규칙:
9개의 3×3 박스 각각에도 1~9가 한 번씩만 있어야 합니다.

초록색으로 강조된 왼쪽 위 박스를 보세요.
5, 3, 6, 9, 8, 1이 있으니
나머지 3칸에 2, 4, 7이 들어가야 합니다.`,
        grid: TUT_PUZZLE,
        hl: {
            '00':'t-hl2','01':'t-hl2','02':'t-hl2',
            '10':'t-hl2','11':'t-hl2','12':'t-hl2',
            '20':'t-hl2','21':'t-hl2','22':'t-hl2',
        },
    },
    {
        title: '풀이 기술: 나홀로 후보수',
        text: `가장 기본적인 풀이 기술입니다.

빈 칸에 들어갈 수 있는 숫자(후보수)를 구합니다.
같은 행·열·박스에 이미 있는 숫자는 제외됩니다.

노란색 칸(1행 3번째)을 보세요.
같은 행: 5, 3, 7이 있고
같은 열: 4, 8이 있고
같은 박스: 5, 3, 6, 9, 8, 1이 있습니다.

1, 2, 3, 4, 5, 6, 7, 8, 9 에서
제외하면 → 오직 4만 남습니다! ✅`,
        grid: TUT_PUZZLE,
        hl: { '02':'t-hl1' },
    },
    {
        title: '완성된 스도쿠',
        text: `모든 규칙을 지키며 빈 칸을 채우면
이런 완성된 스도쿠가 됩니다.

초록색 숫자들이 채워진 정답입니다.
모든 행·열·박스에 1~9가 한 번씩 있습니다.

이제 직접 도전해보세요! 🎉

• ⭐ 쉬움: 입문자에게 추천
• ⭐⭐ 보통: 기본기 익히기
• ⭐⭐⭐ 어려움: 실력 검증`,
        grid: TUT_FULL,
        hl: {
            '02':'t-ans','03':'t-ans','05':'t-ans','06':'t-ans','07':'t-ans','08':'t-ans',
            '11':'t-ans','12':'t-ans','14':'t-ans','15':'t-ans','16':'t-ans','17':'t-ans','18':'t-ans',
            '20':'t-ans','23':'t-ans','24':'t-ans','25':'t-ans','26':'t-ans','28':'t-ans',
            '31':'t-ans','32':'t-ans','33':'t-ans','35':'t-ans','37':'t-ans','38':'t-ans',
            '41':'t-ans','42':'t-ans','44':'t-ans','46':'t-ans','47':'t-ans','48':'t-ans',
            '51':'t-ans','53':'t-ans','55':'t-ans','57':'t-ans','58':'t-ans',
            '60':'t-ans','62':'t-ans','63':'t-ans','64':'t-ans','66':'t-ans',
            '70':'t-ans','71':'t-ans','73':'t-ans','75':'t-ans','76':'t-ans','78':'t-ans',
            '80':'t-ans','81':'t-ans','82':'t-ans','83':'t-ans','85':'t-ans','86':'t-ans','88':'t-ans',
        },
    },
];

let tutIdx = 0;

function openTutorial() {
    tutIdx = 0;
    renderTutStep();
    document.getElementById('tutModal').classList.add('show');
}
function closeTutorial() {
    document.getElementById('tutModal').classList.remove('show');
}
function tutNav(dir) {
    tutIdx = Math.max(0, Math.min(TUT_STEPS.length - 1, tutIdx + dir));
    renderTutStep();
}

function renderTutStep() {
    const step = TUT_STEPS[tutIdx];
    document.getElementById('tutStep').textContent  = `${tutIdx + 1} / ${TUT_STEPS.length}`;
    document.getElementById('tutTitle').textContent = step.title;
    document.getElementById('tutText').textContent  = step.text;

    // 그리드 그리기
    const wrap = document.getElementById('tutGridWrap');
    let html = '<table class="tut-tbl">';
    for (let r = 0; r < 9; r++) {
        html += '<tr>';
        for (let c = 0; c < 9; c++) {
            const cls = ['tcell'];
            if (c === 2 || c === 5) cls.push('tbr');
            if (r === 2 || r === 5) cls.push('tbb');
            const hlKey = `${r}${c}`;
            if (step.hl[hlKey]) cls.push(step.hl[hlKey]);
            else cls.push('t-fixed');
            const v = step.grid[r][c] || '';
            html += `<td class="${cls.join(' ')}">${v}</td>`;
        }
        html += '</tr>';
    }
    html += '</table>';
    wrap.innerHTML = html;

    // 이전/다음 버튼 텍스트
    const nextBtn = document.getElementById('tutNextBtn');
    document.querySelector('.btn-prev').disabled = tutIdx === 0;
    nextBtn.textContent = tutIdx === TUT_STEPS.length - 1 ? '처음으로 🔁' : '다음 ▶';
    if (tutIdx === TUT_STEPS.length - 1) {
        nextBtn.onclick = () => { tutIdx = 0; renderTutStep(); };
    } else {
        nextBtn.onclick = () => tutNav(1);
    }
}

// ══════════════════════════════════════════════
// 11. 초기화
// ══════════════════════════════════════════════
function init() {
    // 퍼즐 선택 버튼 생성
    const row = document.getElementById('pzBtns');
    PUZZLES.forEach((p, i) => {
        const b = document.createElement('button');
        b.className = 'puzzle-btn';
        b.textContent = p.name;
        b.onclick = () => loadPuzzle(i);
        row.appendChild(b);
    });

    // 숫자 버튼 생성
    const nr = document.getElementById('numBtns');
    [1,2,3,4,5,6,7,8,9].forEach(n => {
        const b = document.createElement('button');
        b.className = 'num-btn';
        b.textContent = n;
        b.onclick = () => inputNumber(n);
        nr.appendChild(b);
    });
    const del = document.createElement('button');
    del.className = 'del-btn';
    del.textContent = '지우기';
    del.onclick = () => inputNumber(0);
    nr.appendChild(del);

    // 가이드 텍스트
    document.getElementById('guideBox').textContent = GUIDE_TEXT;

    // 그리드 구조 생성 후 첫 퍼즐 로드
    buildGrid();
    loadPuzzle(0);
}

init();
</script>
</body>
</html>
"""

st.components.v1.html(SUDOKU_HTML, height=920, scrolling=True)
