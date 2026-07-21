// 몬스터 종류 데이터 (몬스터 도감이라고 생각하면 됩니다)
// maxHp: 최대 체력, atk: 공격력, exp/gold: 처치했을 때 얻는 경험치와 골드
// respawnMs: 죽은 뒤 다시 나타나기까지 걸리는 시간(밀리초, 1000 = 1초)

const MONSTER_DB = {
  boar: { id: "boar", name: "멧돼지", icon: "🐗", maxHp: 20, atk: 2, exp: 5, gold: 3, respawnMs: 8000 },
  wolf: { id: "wolf", name: "늑대", icon: "🐺", maxHp: 35, atk: 4, exp: 9, gold: 6, respawnMs: 12000 },
};
