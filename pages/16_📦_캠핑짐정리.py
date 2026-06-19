# -*- coding: utf-8 -*-
# 패밀리 캠핑 짐 정리 3D — HTML 앱을 웹페이지에 그대로 표시

import streamlit as st
import streamlit.components.v1 as components
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, check_password

st.set_page_config(page_title="캠핑 짐 정리 3D - 마이 유틸리티", page_icon="📦", layout="wide")
apply_common_style()
check_password()

# HTML 파일 읽기
html_path = os.path.join(os.path.dirname(__file__), "..", "car_cargo_3d.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# HTML을 화면 전체에 표시 (높이 800px)
components.html(html_content, height=800, scrolling=False)
