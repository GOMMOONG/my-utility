// 화면 그리기 담당 (Canvas = 그림을 그리는 도화지 같은 것)

let canvas, ctx;

// 캔버스(도화지)를 화면에서 찾아서 그림 그릴 준비를 함
function initRenderer() {
  canvas = document.getElementById("gameCanvas");
  ctx = canvas.getContext("2d");
}

// obj(캐릭터 또는 몬스터)를 목표 지점으로 한 프레임만큼 이동시킴
// speed: 초당 이동 픽셀 수, dtSec: 이번 프레임이 몇 초 걸렸는지
// 목표 지점에 도착했으면 true를 돌려줌
function moveToward(obj, targetX, targetY, speed, dtSec) {
  const dx = targetX - obj.x;
  const dy = targetY - obj.y;
  const dist = Math.sqrt(dx * dx + dy * dy);
  if (dist < 2) {
    obj.x = targetX;
    obj.y = targetY;
    return true;
  }
  const moveDist = speed * dtSec;
  const ratio = Math.min(1, moveDist / dist);
  obj.x += dx * ratio;
  obj.y += dy * ratio;
  return false;
}

function drawBackground() {
  ctx.fillStyle = "#274623";
  ctx.fillRect(0, 0, MAP_WIDTH, MAP_HEIGHT);

  // 풀숲 느낌을 주는 단순한 점 무늬 장식 (부딪히지 않는 그냥 배경 그림)
  ctx.fillStyle = "rgba(255,255,255,0.04)";
  for (let i = 0; i < 50; i++) {
    const gx = (i * 137) % MAP_WIDTH;
    const gy = (i * 79) % MAP_HEIGHT;
    ctx.fillRect(gx, gy, 3, 10);
  }
}

function drawMonster(m) {
  if (!m.alive) return;
  const info = MONSTER_DB[m.monsterId];

  ctx.textAlign = "center";
  ctx.font = "28px sans-serif";
  ctx.fillText(info.icon, m.x, m.y);

  ctx.font = "11px sans-serif";
  ctx.fillStyle = "#ffffff";
  ctx.fillText(info.name, m.x, m.y - 26);

  // 몬스터 체력바 (빨간 막대)
  const barW = 30;
  ctx.fillStyle = "#3a1010";
  ctx.fillRect(m.x - barW / 2, m.y - 21, barW, 4);
  ctx.fillStyle = "#e04848";
  ctx.fillRect(m.x - barW / 2, m.y - 21, barW * (m.hp / info.maxHp), 4);

  // 지금 공격 중인 몬스터는 노란 원으로 표시
  if (player.targetMonsterId === m.instanceId) {
    ctx.strokeStyle = "#ffd76a";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(m.x, m.y, 22, 0, Math.PI * 2);
    ctx.stroke();
  }
}

function drawPlayer() {
  ctx.textAlign = "center";
  ctx.font = "30px sans-serif";
  ctx.fillText("🙂", player.x, player.y);
}

function drawAll() {
  drawBackground();
  for (const m of monsters) drawMonster(m);
  drawPlayer();
}

// 화면 위쪽 상태 표시줄(레벨/HP/EXP/골드)을 최신 상태로 갱신
function updateStatUI() {
  document.getElementById("statLevel").textContent = "Lv." + player.level;

  const maxHp = getPlayerMaxHp();
  document.getElementById("hpBar").style.width = (100 * player.hp / maxHp) + "%";
  document.getElementById("hpText").textContent = player.hp + " / " + maxHp;

  document.getElementById("expBar").style.width = (100 * player.exp / player.expToNext) + "%";
  document.getElementById("expText").textContent = player.exp + " / " + player.expToNext;

  document.getElementById("statGold").textContent = "💰 " + player.gold;
}
