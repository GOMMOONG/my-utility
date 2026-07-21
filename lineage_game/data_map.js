// 사냥터 맵 데이터
// - 장애물이 없는 단순한 사냥터 1개만 사용합니다 (부딪히는 계산 없이 자유롭게 이동)

const MAP_WIDTH = 800;
const MAP_HEIGHT = 500;

// 캐릭터가 부활(리스폰)하는 시작 위치
const START_X = 400;
const START_Y = 400;

// 몬스터가 처음 나타나는 좌표들 (이 자리를 중심으로 조금씩 배회함)
const MONSTER_SPAWNS = [
  { monsterId: "boar", x: 200, y: 150 },
  { monsterId: "boar", x: 300, y: 250 },
  { monsterId: "wolf", x: 550, y: 180 },
  { monsterId: "wolf", x: 620, y: 300 },
  { monsterId: "boar", x: 480, y: 120 },
];
