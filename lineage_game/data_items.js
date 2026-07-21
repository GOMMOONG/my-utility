// 아이템 데이터 (아이템 도감) — 2단계: 아이템/인벤토리/장비
// type: "potion"(물약, 체력회복) / "weapon"(무기, 공격력+) / "armor"(방어구, 최대체력+)

const ITEM_DB = {
  potion_small: { id: "potion_small", name: "작은 물약", icon: "🧪", type: "potion", healHp: 30, desc: "체력을 30 회복합니다." },
  potion_big:   { id: "potion_big",   name: "큰 물약",   icon: "🍶", type: "potion", healHp: 80, desc: "체력을 80 회복합니다." },
  sword_wood:   { id: "sword_wood",   name: "나무 검",   icon: "🗡️", type: "weapon", atkBonus: 3, desc: "공격력 +3" },
  sword_iron:   { id: "sword_iron",   name: "철 검",     icon: "⚔️", type: "weapon", atkBonus: 8, desc: "공격력 +8" },
  armor_leather:{ id: "armor_leather",name: "가죽 갑옷", icon: "🥋", type: "armor", hpBonus: 20, desc: "최대체력 +20" },
  armor_iron:   { id: "armor_iron",   name: "철 갑옷",   icon: "🛡️", type: "armor", hpBonus: 50, desc: "최대체력 +50" },
};

// 몬스터를 처치했을 때 어떤 아이템이 얼마의 확률(0~1)로 나오는지 정의
const DROP_TABLES = {
  boar: [
    { itemId: "potion_small", chance: 0.35 },
    { itemId: "sword_wood", chance: 0.08 },
    { itemId: "armor_leather", chance: 0.06 },
  ],
  wolf: [
    { itemId: "potion_small", chance: 0.30 },
    { itemId: "potion_big", chance: 0.12 },
    { itemId: "sword_iron", chance: 0.06 },
    { itemId: "armor_iron", chance: 0.05 },
  ],
};
