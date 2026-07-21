// 저장/불러오기 담당 (localStorage = 이 브라우저 안에만 저장되는 저장공간)

const SAVE_KEY = "lineage_save_v1"; // 저장할 때 쓰는 이름표
const AUTO_SAVE_INTERVAL_MS = 12000; // 자동 저장 주기 (12초)

let lastAutoSaveAt = 0;

function saveGame() {
  const data = {
    level: player.level,
    exp: player.exp,
    expToNext: player.expToNext,
    hp: player.hp,
    maxHp: player.maxHp,
    atk: player.atk,
    gold: player.gold,
    x: player.x,
    y: player.y,
    inventory: player.inventory,
    equipment: player.equipment,
  };
  localStorage.setItem(SAVE_KEY, JSON.stringify(data));
}

// 저장된 캐릭터가 있으면 불러와서 player에 덮어씀 (있었으면 true, 없었으면 false)
function loadGame() {
  const raw = localStorage.getItem(SAVE_KEY);
  if (!raw) return false;
  try {
    const data = JSON.parse(raw);
    Object.assign(player, data);
    player.targetMonsterId = null;
    player.moveTargetX = null;
    player.moveTargetY = null;
    return true;
  } catch (e) {
    return false;
  }
}

// "새로 시작" 버튼: 저장된 캐릭터를 지우고 처음부터 다시 시작
function resetGame() {
  if (!confirm("정말 캐릭터를 지우고 새로 시작할까요?")) return;
  localStorage.removeItem(SAVE_KEY);
  location.reload();
}

// 일정 시간마다 자동으로 저장 (게임 루프 안에서 매 프레임 호출됨)
function autoSaveTick(now) {
  if (now - lastAutoSaveAt < AUTO_SAVE_INTERVAL_MS) return;
  lastAutoSaveAt = now;
  saveGame();
}
