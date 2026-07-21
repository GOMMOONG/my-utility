// 인벤토리/장비 관련 로직 — 2단계: 아이템/인벤토리/장비
// player.inventory: [{itemId, count}, ...] / player.equipment: {weapon:아이템id 또는 null, armor:아이템id 또는 null}

const INVENTORY_MAX = 20; // 인벤토리 칸 수 (이보다 많이는 못 들고 다님)

// 몬스터를 잡았을 때 드롭 테이블을 굴려서 실제로 나온 아이템 id 목록을 돌려줌
function rollDrops(monsterId) {
  const table = DROP_TABLES[monsterId];
  if (!table) return [];
  const drops = [];
  for (const entry of table) {
    if (Math.random() < entry.chance) drops.push(entry.itemId);
  }
  return drops;
}

// 인벤토리에 아이템 1개 추가. 이미 있는 아이템이면 개수만 늘림. 가득 찼으면 false 반환
function addItemToInventory(itemId) {
  const existing = player.inventory.find(function (slot) { return slot.itemId === itemId; });
  if (existing) {
    existing.count += 1;
    return true;
  }
  if (player.inventory.length >= INVENTORY_MAX) return false;
  player.inventory.push({ itemId: itemId, count: 1 });
  return true;
}

// 인벤토리에서 아이템 1개를 뺌 (개수가 0이 되면 칸 자체를 없앰)
function removeOneItem(itemId) {
  const idx = player.inventory.findIndex(function (slot) { return slot.itemId === itemId; });
  if (idx === -1) return;
  player.inventory[idx].count -= 1;
  if (player.inventory[idx].count <= 0) player.inventory.splice(idx, 1);
}

// 지금 장착 중인 장비의 보너스 수치를 가져옴 (없으면 0)
function getEquipBonus(slot, field) {
  const itemId = player.equipment[slot];
  if (!itemId) return 0;
  const info = ITEM_DB[itemId];
  return info[field] || 0;
}

// 장비 보너스가 반영된 실제 공격력/최대체력 (전투·화면표시는 항상 이 값을 써야 함)
function getPlayerAtk() {
  return player.atk + getEquipBonus("weapon", "atkBonus");
}
function getPlayerMaxHp() {
  return player.maxHp + getEquipBonus("armor", "hpBonus");
}

// 인벤토리 칸을 클릭했을 때: 물약이면 사용(체력 회복), 무기/방어구면 장착·해제
function useItem(itemId) {
  const info = ITEM_DB[itemId];
  if (!info) return;

  if (info.type === "potion") {
    const maxHp = getPlayerMaxHp();
    if (player.hp >= maxHp) {
      addLog("체력이 이미 가득 찼습니다.");
      return;
    }
    player.hp = Math.min(maxHp, player.hp + info.healHp);
    removeOneItem(itemId);
    addLog(`${info.name}을(를) 사용해 체력을 회복했습니다.`, "log-gain");
    saveGame();
  } else {
    equipItem(itemId);
  }
  renderInventory();
}

// 무기/방어구를 장착하거나(이미 장착 중이면) 해제함
function equipItem(itemId) {
  const info = ITEM_DB[itemId];
  const slot = info.type; // "weapon" 또는 "armor"

  if (player.equipment[slot] === itemId) {
    // 이미 장착하고 있던 것을 다시 클릭 → 해제하고 인벤토리로 되돌림
    player.equipment[slot] = null;
    addItemToInventory(itemId);
    addLog(`${info.name} 장착을 해제했습니다.`);
  } else {
    // 인벤토리에서 하나 꺼내 장착하고, 기존에 있던 장비는 인벤토리로 되돌림
    removeOneItem(itemId);
    const prevEquipped = player.equipment[slot];
    if (prevEquipped) addItemToInventory(prevEquipped);
    player.equipment[slot] = itemId;
    addLog(`${info.name}을(를) 장착했습니다.`, "log-gain");
  }

  player.hp = Math.min(player.hp, getPlayerMaxHp()); // 방어구가 바뀌어 최대체력이 줄었으면 맞춰줌
  saveGame();
}

// 인벤토리 창(그리드+장비칸)을 지금 상태에 맞게 다시 그림
function renderInventory() {
  const grid = document.getElementById("inventoryGrid");
  grid.innerHTML = "";

  for (const slot of player.inventory) {
    const info = ITEM_DB[slot.itemId];
    const cell = document.createElement("div");
    cell.className = "inv-cell";
    cell.title = info.desc;
    cell.innerHTML =
      `<span class="inv-icon">${info.icon}</span>` +
      `<span class="inv-name">${info.name}</span>` +
      `<span class="inv-count">${slot.count}</span>`;
    cell.addEventListener("click", function () { useItem(slot.itemId); });
    grid.appendChild(cell);
  }

  for (let i = player.inventory.length; i < INVENTORY_MAX; i++) {
    const empty = document.createElement("div");
    empty.className = "inv-cell inv-empty";
    grid.appendChild(empty);
  }

  updateEquipSlotUI("weapon", "equipWeapon");
  updateEquipSlotUI("armor", "equipArmor");
}

function updateEquipSlotUI(slot, elId) {
  const el = document.getElementById(elId);
  const iconEl = el.querySelector(".equip-icon");
  const itemId = player.equipment[slot];
  if (itemId) {
    const info = ITEM_DB[itemId];
    iconEl.textContent = info.icon;
    el.title = info.name + " (클릭하면 해제)";
    el.onclick = function () { equipItem(itemId); renderInventory(); };
  } else {
    iconEl.textContent = "-";
    el.title = "";
    el.onclick = null;
  }
}

// "🎒 인벤토리" 버튼을 누르면 창을 열고 닫음
function toggleInventory() {
  const panel = document.getElementById("inventoryPanel");
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden")) renderInventory();
}
