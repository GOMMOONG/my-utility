# 모든 페이지에서 공통으로 사용하는 스타일과 함수

import streamlit as st
import hmac

# 사이트 전체에서 쓰는 색상
COLORS = {
    "primary": "#6C5CE7",      # 보라색 (메인 포인트 색상)
    "secondary": "#A29BFE",    # 연한 보라색
    "success": "#00B894",      # 초록색
    "warning": "#FDCB6E",      # 노란색
    "danger": "#E17055",       # 빨간색
    "dark": "#2D3436",         # 짙은 글씨 색
    "light": "#DFE6E9",        # 연한 배경 색
    "white": "#FFFFFF",
}


def apply_common_style():
    """모든 페이지에 공통 CSS 스타일을 적용하는 함수"""
    st.markdown("""
    <style>
        /* 사이드바 스타일 */
        [data-testid="stSidebar"] {
            background-color: #2D3436;
        }
        [data-testid="stSidebar"] * {
            color: #DFE6E9 !important;
        }

        /* 카드 스타일 */
        .app-card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            margin-bottom: 16px;
            border: 1px solid #f0f0f0;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .app-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.12);
        }

        /* 제목 스타일 */
        .page-title {
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 0.5em;
            color: #2D3436;
        }
        .page-subtitle {
            font-size: 1.1em;
            color: #636E72;
            margin-bottom: 1.5em;
        }

        /* 결과 박스 스타일 */
        .result-box {
            background: linear-gradient(135deg, #6C5CE7 0%, #A29BFE 100%);
            color: white;
            border-radius: 16px;
            padding: 24px;
            margin: 16px 0;
        }

        /* 푸터 숨기기 */
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}

        /* ── 모바일 화면 최적화 ── */

        /* 모바일에서 버튼을 손가락으로 누르기 쉽게 */
        @media (max-width: 768px) {
            .stButton > button {
                min-height: 48px;
                font-size: 1em;
                padding: 12px 20px;
                border-radius: 12px;
                -webkit-tap-highlight-color: transparent;
            }
        }

        /* 모바일에서 카드 레이아웃 조정 */
        @media (max-width: 768px) {
            .app-card {
                padding: 16px;
                margin-bottom: 12px;
                border-radius: 12px;
            }
        }

        /* 모바일에서 사이드바 터치 영역 확대 */
        @media (max-width: 768px) {
            [data-testid="stSidebar"] a {
                min-height: 44px;
                padding: 8px 16px;
                font-size: 1em;
            }
        }

        /* 입력 필드 글자 크기 16px (아이폰 자동 확대 방지) */
        @media (max-width: 768px) {
            .stTextInput input,
            .stNumberInput input,
            .stSelectbox select,
            .stTextArea textarea {
                font-size: 16px !important;
            }
        }

        /* 모바일 전반 간격/크기 조정 */
        @media (max-width: 768px) {
            .block-container {
                padding: 1rem 1rem !important;
            }
            .page-title {
                font-size: 1.6em;
            }
            .page-subtitle {
                font-size: 1em;
            }
        }

        /* PWA 독립 모드일 때 아이폰 노치(카메라) 영역 여백 확보 */
        @media all and (display-mode: standalone) {
            .block-container {
                padding-top: calc(env(safe-area-inset-top) + 1rem) !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # PWA 메타 태그 삽입 (아이폰 홈 화면 앱 설치용)
    _inject_pwa_meta()


def _inject_pwa_meta():
    """아이폰에서 앱처럼 설치할 수 있게 만드는 PWA 설정을 삽입하는 함수"""
    st.markdown("""
    <script>
    // PWA 설정을 <head>에 직접 삽입 (Safari가 확실히 인식하도록)
    (function() {
        if (window._pwaMetaInjected) return;
        window._pwaMetaInjected = true;

        var head = document.head;

        // 메타 태그 목록
        var metas = [
            {name: 'apple-mobile-web-app-capable', content: 'yes'},
            {name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent'},
            {name: 'apple-mobile-web-app-title', content: '마이 유틸리티'},
            {name: 'theme-color', content: '#6C5CE7'}
        ];
        metas.forEach(function(m) {
            if (!head.querySelector('meta[name="' + m.name + '"]')) {
                var el = document.createElement('meta');
                el.name = m.name;
                el.content = m.content;
                head.appendChild(el);
            }
        });

        // viewport 메타 태그 업데이트 (아이폰 노치 영역 지원)
        var vp = head.querySelector('meta[name="viewport"]');
        if (vp) {
            vp.content = 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover';
        }

        // 앱 아이콘 (아이폰 홈 화면에 표시)
        if (!head.querySelector('link[rel="apple-touch-icon"]')) {
            var icon = document.createElement('link');
            icon.rel = 'apple-touch-icon';
            icon.href = '/app/static/icon-180x180.png';
            head.appendChild(icon);
        }

        // PWA 매니페스트 파일 연결
        if (!head.querySelector('link[rel="manifest"]')) {
            var manifest = document.createElement('link');
            manifest.rel = 'manifest';
            manifest.href = '/app/static/manifest.json';
            head.appendChild(manifest);
        }

        // 서비스 워커 등록
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/app/static/service-worker.js').catch(function() {});
        }
    })();
    </script>
    """, unsafe_allow_html=True)


def check_password():
    """비밀번호를 확인하는 함수. 비밀번호가 맞으면 True, 틀리면 False를 반환한다.
    비밀번호가 틀리면 로그인 화면을 보여주고 페이지 실행을 멈춘다."""
    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <div style="text-align: center; padding: 60px 0 20px 0;">
        <h1 style="font-size: 2.5em;">🔒 마이 유틸리티</h1>
        <p style="color: #636E72; font-size: 1.1em;">비밀번호를 입력해주세요</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        submitted = st.form_submit_button("로그인", type="primary", use_container_width=True)

    if submitted:
        correct_password = st.secrets.get("password", "myutility2026")
        if hmac.compare_digest(password, correct_password):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다. 다시 입력해주세요.")

    st.stop()


def show_page_header(icon, title, subtitle=""):
    """각 페이지 상단에 제목을 표시하는 함수"""
    st.markdown(f'<div class="page-title">{icon} {title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)
    st.divider()
