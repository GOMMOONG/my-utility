import streamlit as st
from style import apply_common_style, check_password

# 페이지 기본 설정
st.set_page_config(
    page_title="마이 유틸리티",
    page_icon="🏠",
    layout="wide",
)

apply_common_style()
check_password()

# ── 헤더 영역 ──
st.markdown("""
<div style="text-align: center; padding: 40px 0 20px 0;">
    <h1 style="font-size: 2.5em; margin-bottom: 8px;">🏠 마이 유틸리티</h1>
    <p style="font-size: 1.2em; color: #636E72;">일상에서 쓸 수 있는 다양한 도구를 모아놓은 나만의 홈페이지입니다</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── 앱 목록 데이터 ──
APPS = {
    "운세 & 점": [
        {"icon": "🔮", "name": "타로카드", "desc": "오늘의 카드 1장 또는 과거-현재-미래 3장 스프레드", "page": "pages/01_🔮_타로카드.py"},
        {"icon": "📅", "name": "토정비결", "desc": "음력 생년월일로 신년 운세 보기 (144괘)", "page": "pages/02_📅_토정비결.py"},
        {"icon": "📊", "name": "사주팔자", "desc": "생년월일·시간으로 사주 분석, 오행·성격·운세", "page": "pages/03_📊_사주팔자.py"},
    ],
    "생활 도구": [
        {"icon": "✅", "name": "체크리스트", "desc": "할 일 추가하고 완료하면 취소선 표시", "page": "pages/04_✅_체크리스트.py"},
        {"icon": "📒", "name": "가계부", "desc": "수입/지출 입력하고 월별 통계 보기", "page": "pages/05_📒_가계부.py"},
        {"icon": "📅", "name": "일정 관리", "desc": "달력에서 날짜를 골라 일정 입력/조회", "page": "pages/06_📅_일정관리.py"},
    ],
    "재테크": [
        {"icon": "🍀", "name": "로또 번호 생성기", "desc": "최근 당첨 번호 분석해서 번호 추천", "page": "pages/07_🍀_로또번호.py"},
        {"icon": "🎰", "name": "연금복권 번호 생성기", "desc": "3년치 데이터로 연금복권 번호 추천", "page": "pages/08_🎰_연금복권.py"},
        {"icon": "💰", "name": "급여 계산기", "desc": "월급에서 세금·4대보험 빼고 실수령액 계산", "page": "pages/09_💰_급여계산기.py"},
        {"icon": "💳", "name": "연말정산 계산기", "desc": "공제항목 입력해서 환급/추납 예상액 계산", "page": "pages/10_💳_연말정산.py"},
        {"icon": "📈", "name": "투자자 동향", "desc": "기관/외국인/개인 매매동향 조회 (네이버증권)", "page": "pages/13_📈_투자자동향.py"},
    ],
    "쇼핑 & 학습": [
        {"icon": "🏕️", "name": "캠핑장 조회", "desc": "금산 기준 2시간 이내 캠핑장 검색", "page": "pages/11_🏕️_캠핑장조회.py"},
        {"icon": "🔍", "name": "최저가 검색", "desc": "네이버 쇼핑에서 물건 최저가 비교", "page": "pages/12_🔍_최저가검색.py"},
        {"icon": "📚", "name": "영어 학습", "desc": "왕초보부터 넷플릭스까지! 단어·표현·퀴즈", "page": "pages/14_📚_영어학습.py"},
        {"icon": "🌤️", "name": "날씨", "desc": "전국 52개 도시 실시간 날씨·시간별/주간 예보", "page": "pages/15_🌤️_날씨.py"},
    ],
}

# ── 카테고리별 앱 카드 표시 ──
for category, apps in APPS.items():
    st.markdown(f"### {category}")

    cols = st.columns(min(len(apps), 3))
    for i, app in enumerate(apps):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="app-card">
                <div style="font-size: 2.5em; margin-bottom: 8px;">{app['icon']}</div>
                <div style="font-size: 1.2em; font-weight: 600; margin-bottom: 4px;">{app['name']}</div>
                <div style="color: #636E72; font-size: 0.9em;">{app['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            st.page_link(app["page"], label=f"{app['icon']} {app['name']} 열기", use_container_width=True)

    st.markdown("")  # 카테고리 사이 간격

# ── 하단 안내 ──
st.divider()
st.markdown("""
<div style="text-align: center; color: #B2BEC3; padding: 20px 0;">
    ← 왼쪽 사이드바에서도 원하는 도구를 선택할 수 있습니다
</div>
""", unsafe_allow_html=True)
