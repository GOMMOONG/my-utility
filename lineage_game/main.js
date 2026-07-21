// 게임을 시작시키는 진입점 (다른 모든 파일이 이미 다 불러와진 뒤 마지막에 실행됨)

// 캐릭터(플레이어) 상태 — 게임 전체에서 공유하는 값
let player = {
  level: 1,
  exp: 0,
  expToNext: 10,
  hp: 50,
  maxHp: 50,
  atk: 5,
  gold: 0,
  x: START_X,
  y: START_Y,
  moveTargetX: null,   // 클릭해서 이동 중인 목적지
  moveTargetY: null,
  targetMonsterId: null, // 지금 공격 중인 몬스터
  inventory: [],          // 가지고 있는 아이템: [{itemId, count}, ...]
  equipment: { weapon: null, armor: null }, // 장착 중인 무기/방어구 아이템id
};

let lastFrameTime = 0;

// 매 화면 프레임(대략 1초에 60번)마다 반복 실행되는 게임 루프
function gameLoop(timestamp) {
  const dtSec = lastFrameTime ? (timestamp - lastFrameTime) / 1000 : 0;
  lastFrameTime = timestamp;
  const now = performance.now();

  updatePlayerMovement(dtSec);
  updateMonsterWander(now, dtSec);
  updateCombat(now);
  updateRegen(now);
  autoSaveTick(now);

  drawAll();
  updateStatUI();

  requestAnimationFrame(gameLoop);
}

function startGame() {
  initRenderer();
  spawnMonsterInstances();

  const hadSave = loadGame();
  addLog(hadSave
    ? "저장된 모험을 이어서 시작합니다."
    : "사냥터에 도착했습니다! 몬스터를 클릭하면 다가가서 공격합니다.");

  canvas.addEventListener("click", onCanvasClick);
  document.getElementById("resetBtn").addEventListener("click", resetGame);
  document.getElementById("invBtn").addEventListener("click", toggleInventory);
  document.getElementById("invCloseBtn").addEventListener("click", toggleInventory);
  window.addEventListener("beforeunload", saveGame);

  requestAnimationFrame(gameLoop);
}

startGame();
