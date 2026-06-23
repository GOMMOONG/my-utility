# 쪼니 — 친근한 AI 개인비서 채팅 페이지

import streamlit as st
import requests
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

try:
    import anthropic
except ImportError:
    anthropic = None

# ── 페이지 기본 설정 ──
st.set_page_config(
    page_title="쪼니 - 마이 유틸리티",
    page_icon="🤖",
    layout="centered",
)
apply_common_style()
check_password()
show_page_header("🤖", "쪼니", "나만의 AI 개인비서 — 무엇이든 물어봐!")


# ══════════════════════════════════════════════════════════════
# 도시 좌표 (날씨 조회용, 날씨 앱에서 가져옴)
# ══════════════════════════════════════════════════════════════
CITY_COORDS = {
    "서울": (37.5665, 126.9780), "인천": (37.4563, 126.7052),
    "수원": (37.2636, 127.0286), "성남": (37.4449, 127.1388),
    "고양": (37.6564, 126.8350), "용인": (37.2411, 127.1776),
    "평택": (36.9921, 127.1128), "의정부": (37.7382, 127.0337),
    "춘천": (37.8813, 127.7298), "강릉": (37.7519, 128.8761),
    "원주": (37.3422, 127.9202), "속초": (38.2070, 128.5918),
    "대전": (36.3504, 127.3845), "세종": (36.4801, 127.2890),
    "청주": (36.6424, 127.4890), "천안": (36.8151, 127.1139),
    "금산": (36.1083, 127.4884), "제천": (37.1325, 128.1908),
    "광주": (35.1595, 126.8526), "전주": (35.8242, 127.1480),
    "목포": (34.8118, 126.3922), "여수": (34.7604, 127.6622),
    "순천": (34.9507, 127.4874),
    "부산": (35.1796, 129.0756), "대구": (35.8714, 128.6014),
    "울산": (35.5384, 129.3114), "창원": (35.2280, 128.6811),
    "포항": (36.0190, 129.3435), "경주": (35.8562, 129.2247),
    "안동": (36.5684, 128.7294), "구미": (36.1195, 128.3446),
    "진주": (35.1799, 128.1076),
    "제주시": (33.4996, 126.5312), "서귀포": (33.2541, 126.5600),
    "제주": (33.4996, 126.5312),
}

# 날씨 코드 → 설명
WEATHER_DESC = {
    0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림",
    45: "안개", 48: "안개", 51: "가벼운 이슬비", 53: "이슬비", 55: "짙은 이슬비",
    61: "가벼운 비", 63: "비", 65: "강한 비",
    71: "가벼운 눈", 73: "눈", 75: "강한 눈",
    80: "소나기", 81: "소나기", 82: "강한 소나기",
    95: "뇌우", 96: "뇌우+우박", 99: "강한 뇌우",
}


# ══════════════════════════════════════════════════════════════
# 날씨 조회 함수 (쪼니가 도구로 호출)
# ══════════════════════════════════════════════════════════════
def get_weather(city_name):
    """도시 이름으로 현재 날씨를 가져오는 함수"""
    coords = CITY_COORDS.get(city_name)
    if not coords:
        # 비슷한 이름 찾기
        for name in CITY_COORDS:
            if city_name in name or name in city_name:
                coords = CITY_COORDS[name]
                city_name = name
                break
    if not coords:
        available = ", ".join(list(CITY_COORDS.keys())[:10]) + " 등"
        return f"'{city_name}'은 목록에 없어. 가능한 도시: {available}"

    lat, lon = coords
    try:
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current_weather": True,
            "daily": "temperature_2m_max,temperature_2m_min,weathercode",
            "timezone": "Asia/Seoul", "forecast_days": 1,
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        current = data["current_weather"]
        temp = current["temperature"]
        code = current["weathercode"]
        desc = WEATHER_DESC.get(code, "알 수 없음")
        wind = current["windspeed"]

        daily = data.get("daily", {})
        t_max = daily.get("temperature_2m_max", [None])[0]
        t_min = daily.get("temperature_2m_min", [None])[0]

        result = f"{city_name} 현재 날씨: {desc}, 기온 {temp}°C, 바람 {wind}km/h"
        if t_max is not None and t_min is not None:
            result += f", 오늘 최고 {t_max}°C / 최저 {t_min}°C"
        return result
    except Exception:
        return f"{city_name} 날씨를 가져오지 못했어. 인터넷 연결을 확인해줘."


# ══════════════════════════════════════════════════════════════
# 쪼니의 성격 (시스템 프롬프트)
# ══════════════════════════════════════════════════════════════
def build_system_prompt():
    now = datetime.now().strftime("%Y년 %m월 %d일 %A %H시 %M분")
    return f"""너의 이름은 '쪼니'야. 사용자의 친근한 AI 개인비서야.

## 성격과 말투
- 항상 친근한 반말을 써. ("응!", "그거 좋은 생각이야~", "알려줄게!")
- 다정하고 밝은 성격이야. 이모지를 적절히 써서 대화를 생동감있게 해.
- 짧고 핵심적으로 대답해. 너무 길게 설명하지 마.
- 모르는 건 솔직하게 모른다고 해.

## 현재 시간
지금은 {now}이야.

## 사용할 수 있는 도구
- 날씨 조회: 한국 주요 도시의 현재 날씨를 알려줄 수 있어.

## 마이 유틸리티 앱 안내
사용자가 다음 기능을 물어보면 해당 앱을 안내해줘:
- 🔮 타로카드: 오늘의 운세를 카드로 보기
- 📅 토정비결: 음력 생년월일로 신년 운세
- 📊 사주팔자: 생년월일로 사주 분석
- ✅ 체크리스트: 할 일 관리
- 📒 가계부: 수입/지출 관리
- 📅 일정 관리: 달력에 일정 입력
- 🍀 로또 번호: 당첨 분석 기반 번호 추천
- 💰 급여 계산기: 실수령액 계산
- 💳 연말정산: 환급/추납 계산
- 📈 투자자 동향: 기관/외국인 매매 조회
- 🔍 최저가 검색: 네이버 쇼핑 최저가
- 📚 영어 학습: 단어·표현·퀴즈
- 🌤️ 날씨: 전국 52개 도시 상세 날씨
- 📰 뉴스 요약: 경제/사회/스포츠/세계 뉴스
- 👶 아이랑 어디갈까: 아이와 갈 곳 검색
이 앱들은 왼쪽 사이드바에서 바로 이동할 수 있다고 안내해."""


# ══════════════════════════════════════════════════════════════
# Claude API에 등록할 도구 목록
# ══════════════════════════════════════════════════════════════
TOOLS = [
    {
        "name": "get_weather",
        "description": "한국 도시의 현재 날씨를 조회합니다. 기온, 날씨 상태, 바람, 최고/최저 기온을 반환합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "날씨를 조회할 도시 이름 (예: 서울, 부산, 대전, 제주)",
                }
            },
            "required": ["city"],
        },
    }
]


# ══════════════════════════════════════════════════════════════
# Claude API 호출 (도구 사용 포함)
# ══════════════════════════════════════════════════════════════
def call_api(client, messages):
    """Claude API를 호출하고, 도구가 필요하면 실행 후 최종 답변을 반환"""
    system = build_system_prompt()

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        tools=TOOLS,
        messages=messages,
    )

    # 도구 호출이 필요한 경우
    if response.stop_reason == "tool_use":
        tool_block = None
        for block in response.content:
            if block.type == "tool_use":
                tool_block = block
                break

        if tool_block and tool_block.name == "get_weather":
            weather_result = get_weather(tool_block.input.get("city", ""))

            # 도구 결과를 포함해서 다시 API 호출
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": tool_block.id, "content": weather_result}
                ],
            })

            final = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system,
                tools=TOOLS,
                messages=messages,
            )
            return "".join(b.text for b in final.content if b.type == "text")

    # 일반 텍스트 응답
    return "".join(b.text for b in response.content if b.type == "text")


# ══════════════════════════════════════════════════════════════
# API 키 관리
# ══════════════════════════════════════════════════════════════
def get_api_key():
    """Streamlit secrets 또는 사이드바 입력에서 API 키를 가져오는 함수"""
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        key = ""
    if not key:
        key = st.session_state.get("api_key", "")
    return key


# ══════════════════════════════════════════════════════════════
# 사이드바: API 키 입력 + 대화 초기화
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ 쪼니 설정")

    api_key = get_api_key()
    has_secret = bool(api_key)

    if not has_secret:
        st.markdown("""
        **Claude API 키가 필요해요!**

        1. [console.anthropic.com](https://console.anthropic.com) 접속
        2. 회원가입 후 API Keys 메뉴에서 키 생성
        3. 아래에 붙여넣기
        """)
        input_key = st.text_input(
            "API 키 입력",
            type="password",
            placeholder="sk-ant-...",
            key="api_key_input",
        )
        if input_key:
            st.session_state.api_key = input_key
            st.rerun()

    if api_key:
        st.success("✅ API 키 연결됨")

    st.divider()

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()

    st.caption("쪼니는 Claude AI 기반이에요.\n대화 내용은 저장되지 않아요.")


# ══════════════════════════════════════════════════════════════
# 채팅 화면
# ══════════════════════════════════════════════════════════════

# anthropic 패키지 미설치 확인
if anthropic is None:
    st.error("⚠ `anthropic` 패키지가 설치되어 있지 않아요.\n터미널에서 `pip install anthropic`을 실행해주세요.")
    st.stop()

# API 키 확인
api_key = get_api_key()
if not api_key:
    st.info("👈 왼쪽 사이드바에서 API 키를 먼저 입력해주세요!")
    st.stop()

# 대화 기록 초기화
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# 인사말 (첫 방문 시)
if not st.session_state.chat_messages:
    with st.chat_message("assistant", avatar="🤖"):
        st.write("안녕! 나는 **쪼니**야 😊 무엇이든 물어봐! 날씨도 알려줄 수 있어~")

# 기존 대화 표시
for msg in st.session_state.chat_messages:
    avatar = "🤖" if msg["role"] == "assistant" else "😊"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

# 사용자 입력
if user_input := st.chat_input("쪼니에게 말해보세요..."):
    # 사용자 메시지 표시 + 저장
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="😊"):
        st.write(user_input)

    # 쪼니 응답
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("쪼니가 생각하는 중..."):
            try:
                client = anthropic.Anthropic(api_key=api_key)

                # API용 메시지 목록 (최근 20개만 전송해서 비용 절약)
                api_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_messages[-20:]
                ]

                answer = call_api(client, api_messages)

                if not answer:
                    answer = "음... 잠깐 문제가 생겼어. 다시 말해줄래? 😅"

                st.write(answer)
                st.session_state.chat_messages.append({"role": "assistant", "content": answer})

            except anthropic.AuthenticationError:
                st.error("⚠ API 키가 올바르지 않아요. 사이드바에서 다시 입력해주세요.")
            except anthropic.RateLimitError:
                st.error("⚠ 요청이 너무 많아요. 잠시 후 다시 시도해주세요.")
            except anthropic.BadRequestError as e:
                if "credit" in str(e).lower():
                    st.error("⚠ API 크레딧(잔액)이 부족해요. console.anthropic.com에서 충전해주세요.")
                else:
                    st.error(f"⚠ 요청 오류가 발생했어요: {e}")
            except anthropic.APIConnectionError:
                st.error("⚠ 인터넷 연결을 확인해주세요.")
            except Exception as e:
                st.error(f"⚠ 오류가 발생했어요: {e}")
