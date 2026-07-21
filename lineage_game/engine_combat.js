// 전투 관련 로직 (몬스터 클릭 → 자동 접근 → 자동 공격 → 경험치/레벨업)

let monsters = []; // 사냥터에 실제로 있는 몬스터들

const ATTACK_RANGE = 40;          // 이 거리 안에 들어와야 공격할 수 있음 (픽셀)
const ATTACK_INTERVAL_MS = 1000;  // 공격 간격 (1초에 한 번)
const PLAYER_SPEED = 160;         // 캐릭터 이동 속도 (초당 픽셀)
const REGEN_INTERVAL_MS = 2000;   // 체력 자동 회복 간격
const REGEN_AMOUNT = 1;           // 한 번에 회복하는 체력

let lastAttackAt = 0;
let lastRegenAt = 0;

// 맵에 실제로 배치될 몬스터들을 데이터(data_map.js)를 기반으로 만듦
function spawnMonsterInstances() {
  monsters = MONSTER_SPAWNS.map((spawn, idx) => {
    const info = MONSTER_DB[spawn.monsterId];
    return {
      instanceId: "m" + idx,
      monsterId: spawn.monsterId,
      homeX: spawn.x,
      homeY: spawn.y,
      x: spawn.x,
      y: spawn.y,
      hp: info.maxHp,
      alive: true,
      respawnAt: 0,
      wanderTargetX: spawn.x,
      wanderTargetY: spawn.y,
      nextWanderAt: 0,
    };
  });
}

function findMonsterById(id) {
  return monsters.find(function (m) { return m.instanceId === id; });
}

// 화면 아래 전투 로그창에 글 한 줄 추가
function addLog(text, cssClass) {
  const box = document.getElementById("logBox");
  const el = document.createElement("div");
  el.textContent = text;
  if (cssClass) el.className = cssClass;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
  while (box.childNodes.length > 50) box.removeChild(box.firstChild);
}

// 캔버스를 클릭했을 때: 몬스터를 클릭했으면 공격 대상으로 지정,
// 빈 땅을 클릭했으면 그 자리로 이동
function onCanvasClick(evt) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const clickX = (evt.clientX - rect.left) * scaleX;
  const clickY = (evt.clientY - rect.top) * scaleY;

  for (const m of monsters) {
    if (!m.alive) continue;
    const dx = clickX - m.x, dy = clickY - m.y;
    if (Math.sqrt(dx * dx + dy * dy) < 20) {
      player.targetMonsterId = m.instanceId;
      player.moveTargetX = null;
      player.moveTargetY = null;
      return;
    }
  }

  player.targetMonsterId = null;
  player.moveTargetX = clickX;
  player.moveTargetY = clickY;
}

// 몬스터들이 죽어있으면 리스폰 시간을 확인하고, 살아있으면 집 주변을 천천히 배회
function updateMonsterWander(now, dtSec) {
  for (const m of monsters) {
    if (!m.alive) {
      if (m.respawnAt && now >= m.respawnAt) {
        const info = MONSTER_DB[m.monsterId];
        m.alive = true;
        m.hp = info.maxHp;
        m.x = m.homeX;
        m.y = m.homeY;
        m.respawnAt = 0;
      }
      continue;
    }
    if (player.targetMonsterId === m.instanceId) continue; // 싸우는 중이면 안 돌아다님

    if (now >= m.nextWanderAt) {
      m.wanderTargetX = m.homeX + (Math.random() * 60 - 30);
      m.wanderTargetY = m.homeY + (Math.random() * 60 - 30);
      m.nextWanderAt = now + 3000 + Math.random() * 2000;
    }
    moveToward(m, m.wanderTargetX, m.wanderTargetY, 30, dtSec);
  }
}

// 캐릭터를 이동시킴: 공격 대상이 있으면 사거리까지 접근, 없으면 클릭한 지점으로 이동
function updatePlayerMovement(dtSec) {
  if (player.targetMonsterId) {
    const m = findMonsterById(player.targetMonsterId);
    if (!m || !m.alive) {
      player.targetMonsterId = null;
      return;
    }
    const dx = m.x - player.x, dy = m.y - player.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > ATTACK_RANGE) {
      moveToward(player, m.x, m.y, PLAYER_SPEED, dtSec);
    }
    return;
  }

  if (player.moveTargetX !== null) {
    const arrived = moveToward(player, player.moveTargetX, player.moveTargetY, PLAYER_SPEED, dtSec);
    if (arrived) {
      player.moveTargetX = null;
      player.moveTargetY = null;
    }
  }
}

// 사거리 안에 들어온 몬스터를 일정 간격마다 자동으로 공격
function updateCombat(now) {
  if (!player.targetMonsterId) return;
  const m = findMonsterById(player.targetMonsterId);
  if (!m || !m.alive) { player.targetMonsterId = null; return; }

  const dx = m.x - player.x, dy = m.y - player.y;
  if (Math.sqrt(dx * dx + dy * dy) > ATTACK_RANGE) return; // 아직 사거리 밖

  if (now - lastAttackAt < ATTACK_INTERVAL_MS) return;
  lastAttackAt = now;

  const info = MONSTER_DB[m.monsterId];
  const atk = getPlayerAtk();
  m.hp -= atk;
  addLog(`${info.name}에게 ${atk}의 피해를 입혔습니다.`, "log-damage");

  if (m.hp <= 0) {
    killMonster(m, info);
    return;
  }

  // 몬스터도 반격함
  player.hp -= info.atk;
  addLog(`${info.name}에게 ${info.atk}의 피해를 입었습니다.`, "log-damage");
  if (player.hp <= 0) killPlayer();
}

function killMonster(m, info) {
  m.alive = false;
  m.respawnAt = performance.now() + info.respawnMs;
  player.targetMonsterId = null;

  gainExp(info.exp);
  player.gold += info.gold;
  addLog(`${info.name}을(를) 처치했습니다! (경험치 +${info.exp}, 골드 +${info.gold})`, "log-gain");

  const drops = rollDrops(m.monsterId);
  for (const itemId of drops) {
    const itemInfo = ITEM_DB[itemId];
    if (addItemToInventory(itemId)) {
      addLog(`[아이템 획득] ${itemInfo.icon} ${itemInfo.name}`, "log-gain");
    } else {
      addLog(`인벤토리가 가득 차서 ${itemInfo.name}을(를) 얻지 못했습니다.`, "log-damage");
    }
  }
  renderInventory();

  saveGame();
}

function gainExp(amount) {
  player.exp += amount;
  while (player.exp >= player.expToNext) {
    player.exp -= player.expToNext;
    player.level += 1;
    player.maxHp += 10;
    player.hp = player.maxHp;
    player.atk += 2;
    player.expToNext = Math.floor(player.expToNext * 1.3);
    addLog(`레벨업! Lv.${player.level}이 되었습니다.`, "log-levelup");
  }
}

function killPlayer() {
  addLog("쓰러졌습니다... 시작 지점에서 체력을 회복하고 다시 시작합니다.", "log-damage");
  player.hp = getPlayerMaxHp();
  player.x = START_X;
  player.y = START_Y;
  player.targetMonsterId = null;
  player.moveTargetX = null;
  player.moveTargetY = null;
}

// 전투 중이 아닐 때 체력이 서서히 자동으로 회복됨
function updateRegen(now) {
  const maxHp = getPlayerMaxHp();
  if (player.hp >= maxHp) return;
  if (now - lastRegenAt < REGEN_INTERVAL_MS) return;
  lastRegenAt = now;
  player.hp = Math.min(maxHp, player.hp + REGEN_AMOUNT);
}
