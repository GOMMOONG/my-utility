# -*- coding: utf-8 -*-
# 리니지st — 도트 캐릭터로 사냥터를 누비는 나만의 미니 RPG (JS/Canvas 게임을 웹페이지에 표시)

import streamlit as st
import streamlit.components.v1 as components
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, check_password

st.set_page_config(page_title="리니지st - 마이 유틸리티", page_icon="⚔️", layout="wide")
apply_common_style()
check_password()

# 게임 파일들이 들어있는 폴더
GAME_DIR = os.path.join(os.path.dirname(__file__), "..", "lineage_game")


def read_game_file(name):
    """게임 폴더 안의 파일을 읽어서 글자(문자열)로 돌려주는 함수"""
    with open(os.path.join(GAME_DIR, name), "r", encoding="utf-8") as f:
        return f.read()


# 자바스크립트 파일은 반드시 이 순서로 이어붙여야 함
# (data_*.js 가 먼저 와야 하고, main.js는 다른 함수들을 다 쓰므로 항상 맨 마지막)
JS_FILES = [
    "data_map.js",
    "data_monsters.js",
    "data_items.js",
    "engine_render.js",
    "engine_combat.js",
    "engine_inventory.js",
    "save_load.js",
    "main.js",
]

css_code = read_game_file("style.css")
js_code = "\n".join(read_game_file(name) for name in JS_FILES)

# .format()이나 f-string은 CSS/JS 속 중괄호({ })를 변수 자리로 착각해 에러가 나므로
# 단순 문자열 치환(replace)으로 뼈대(shell.html)에 CSS/JS를 끼워 넣음
shell_html = read_game_file("shell.html")
full_html = shell_html.replace("/*__STYLE__*/", css_code).replace("//__SCRIPT__//", js_code)

components.html(full_html, height=820, scrolling=False)

st.caption("💾 진행 상황은 이 브라우저에 자동으로 저장됩니다. 다른 기기·다른 브라우저에서는 이어할 수 없어요.")
