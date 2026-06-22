import streamlit.components.v1 as components
import os

# 바코드 스캐너 HTML 파일이 있는 폴더 경로
_SCANNER_DIR = os.path.join(os.path.dirname(__file__), "barcode_scanner")

# Streamlit 커스텀 컴포넌트 등록
_scanner_func = components.declare_component("barcode_scanner", path=_SCANNER_DIR)


def barcode_scanner(key=None):
    """바코드 스캐너 컴포넌트를 화면에 표시하고, 인식된 바코드 값을 반환하는 함수"""
    return _scanner_func(key=key, default=None)
