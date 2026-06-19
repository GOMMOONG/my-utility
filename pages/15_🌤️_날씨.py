# -*- coding: utf-8 -*-
# 날씨 앱 웹 버전 — Open-Meteo API 기반 전국 날씨 조회

import streamlit as st
import requests
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="날씨 - 마이 유틸리티", page_icon="🌤️", layout="centered")
apply_common_style()
check_password()
show_page_header("🌤️", "전국 날씨", "Open-Meteo 기반으로 전국 52개 도시의 날씨를 조회합니다")

# ══════════════════════════════════════════════════════════════
# 전국 도시 데이터
# ══════════════════════════════════════════════════════════════
CITIES = {
    "수도권": [
        {"name": "서울", "lat": 37.5665, "lon": 126.9780},
        {"name": "인천", "lat": 37.4563, "lon": 126.7052},
        {"name": "수원", "lat": 37.2636, "lon": 127.0286},
        {"name": "성남", "lat": 37.4449, "lon": 127.1388},
        {"name": "고양", "lat": 37.6564, "lon": 126.8350},
        {"name": "부천", "lat": 37.5034, "lon": 126.7660},
        {"name": "안양", "lat": 37.3943, "lon": 126.9568},
        {"name": "의정부", "lat": 37.7382, "lon": 127.0337},
        {"name": "용인", "lat": 37.2411, "lon": 127.1776},
        {"name": "평택", "lat": 36.9921, "lon": 127.1128},
    ],
    "강원": [
        {"name": "춘천", "lat": 37.8813, "lon": 127.7298},
        {"name": "원주", "lat": 37.3422, "lon": 127.9202},
        {"name": "강릉", "lat": 37.7519, "lon": 128.8761},
        {"name": "속초", "lat": 38.2070, "lon": 128.5918},
        {"name": "동해", "lat": 37.5244, "lon": 129.1144},
        {"name": "태백", "lat": 37.1641, "lon": 128.9857},
    ],
    "충청": [
        {"name": "대전", "lat": 36.3504, "lon": 127.3845},
        {"name": "세종", "lat": 36.4801, "lon": 127.2890},
        {"name": "청주", "lat": 36.6424, "lon": 127.4890},
        {"name": "천안", "lat": 36.8151, "lon": 127.1139},
        {"name": "충주", "lat": 36.9910, "lon": 127.9259},
        {"name": "공주", "lat": 36.4465, "lon": 127.1192},
        {"name": "금산", "lat": 36.1083, "lon": 127.4884},
        {"name": "제천", "lat": 37.1325, "lon": 128.1908},
    ],
    "전라": [
        {"name": "광주", "lat": 35.1595, "lon": 126.8526},
        {"name": "전주", "lat": 35.8242, "lon": 127.1480},
        {"name": "군산", "lat": 35.9676, "lon": 126.7368},
        {"name": "익산", "lat": 35.9483, "lon": 126.9577},
        {"name": "목포", "lat": 34.8118, "lon": 126.3922},
        {"name": "여수", "lat": 34.7604, "lon": 127.6622},
        {"name": "순천", "lat": 34.9507, "lon": 127.4874},
        {"name": "남원", "lat": 35.4165, "lon": 127.3900},
    ],
    "경상": [
        {"name": "부산", "lat": 35.1796, "lon": 129.0756},
        {"name": "대구", "lat": 35.8714, "lon": 128.6014},
        {"name": "울산", "lat": 35.5384, "lon": 129.3114},
        {"name": "창원", "lat": 35.2280, "lon": 128.6811},
        {"name": "포항", "lat": 36.0190, "lon": 129.3435},
        {"name": "경주", "lat": 35.8562, "lon": 129.2247},
        {"name": "안동", "lat": 36.5684, "lon": 128.7294},
        {"name": "구미", "lat": 36.1195, "lon": 128.3446},
        {"name": "진주", "lat": 35.1799, "lon": 128.1076},
        {"name": "거제", "lat": 34.8800, "lon": 128.6211},
    ],
    "제주": [
        {"name": "제주시", "lat": 33.4996, "lon": 126.5312},
        {"name": "서귀포", "lat": 33.2541, "lon": 126.5600},
    ],
}

# 도시 이름으로 빠르게 찾기
CITY_MAP = {}
CITY_NAMES = []
for _region, _cities in CITIES.items():
    for _c in _cities:
        CITY_MAP[_c["name"]] = _c
        CITY_NAMES.append(_c["name"])


# ══════════════════════════════════════════════════════════════
# 날씨 코드 → 아이콘 / 설명
# ══════════════════════════════════════════════════════════════
def get_weather_info(code, hour=None):
    night = hour is not None and (hour < 6 or hour >= 20)
    icons = {
        0: "🌙" if night else "☀️", 1: "🌙" if night else "🌤",
        2: "⛅", 3: "☁️", 45: "🌫", 48: "🌫",
        51: "🌦", 53: "🌦", 55: "🌧", 56: "🌨", 57: "🌨",
        61: "🌧", 63: "🌧", 65: "🌧",
        71: "🌨", 73: "🌨", 75: "❄", 77: "🌨",
        80: "🌦", 81: "🌧", 82: "⛈", 85: "🌨", 86: "❄",
        95: "⛈", 96: "⛈", 99: "⛈",
    }
    descs = {
        0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림",
        45: "안개", 48: "안개",
        51: "가벼운 이슬비", 53: "이슬비", 55: "짙은 이슬비",
        56: "어는 이슬비", 57: "어는 이슬비",
        61: "가벼운 비", 63: "비", 65: "강한 비",
        71: "가벼운 눈", 73: "눈", 75: "강한 눈", 77: "싸락눈",
        80: "소나기", 81: "소나기", 82: "강한 소나기",
        85: "눈 소나기", 86: "강한 눈 소나기",
        95: "뇌우", 96: "뇌우+우박", 99: "강한 뇌우",
    }
    bgs = {
        0: "night" if night else "sunny", 1: "night" if night else "sunny",
        2: "cloudy", 3: "cloudy", 45: "cloudy", 48: "cloudy",
        51: "rainy", 53: "rainy", 55: "rainy",
        61: "rainy", 63: "rainy", 65: "rainy",
        71: "snowy", 73: "snowy", 75: "snowy", 77: "snowy",
        80: "rainy", 81: "rainy", 82: "rainy", 85: "snowy", 86: "snowy",
        95: "rainy", 96: "rainy", 99: "rainy",
    }
    return {
        "icon": icons.get(code, "🌡"),
        "desc": descs.get(code, "알 수 없음"),
        "bg": bgs.get(code, "default"),
    }

# 배경 그라데이션 색상
BG_COLORS = {
    "sunny": ("#1565C0", "#0D47A1"),
    "cloudy": ("#455A64", "#37474F"),
    "rainy": ("#283593", "#1A237E"),
    "snowy": ("#5C6BC0", "#3949AB"),
    "night": ("#1A1A2E", "#0D0D1A"),
    "default": ("#16213E", "#0F3460"),
}

def wind_dir_text(deg):
    dirs = ["북", "북동", "동", "남동", "남", "남서", "서", "북서"]
    return dirs[round(deg / 45) % 8]

def color_by_temp(t):
    if t >= 33: return "#E74C3C"
    if t >= 28: return "#FF7043"
    if t >= 20: return "#FFA726"
    if t >= 10: return "#42A5F5"
    return "#90CAF9"

def color_val_html(val, unit="", fmt=",.0f"):
    if val > 0:
        return f'<span style="color:#E74C3C;font-weight:bold;">{val:{fmt}}{unit}</span>'
    elif val < 0:
        return f'<span style="color:#3498DB;font-weight:bold;">{val:{fmt}}{unit}</span>'
    return f'<span style="color:#999;">0{unit}</span>'


# ══════════════════════════════════════════════════════════════
# API 호출 (5분 캐싱)
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner="날씨 데이터를 불러오는 중...")
def fetch_weather(lat, lon):
    resp = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": lat, "longitude": lon,
        "hourly": "temperature_2m,apparent_temperature,precipitation,"
                  "weathercode,windspeed_10m,winddirection_10m,relativehumidity_2m",
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,"
                 "precipitation_sum,windspeed_10m_max",
        "timezone": "Asia/Seoul", "forecast_days": 7, "wind_speed_unit": "ms",
    }, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ══════════════════════════════════════════════════════════════
# 도시 선택
# ══════════════════════════════════════════════════════════════
col_city, col_refresh = st.columns([4, 1])
with col_city:
    # 기본값: 금산 (인덱스 찾기)
    default_idx = CITY_NAMES.index("금산") if "금산" in CITY_NAMES else 0
    city_name = st.selectbox("도시 선택", CITY_NAMES, index=default_idx,
                             label_visibility="collapsed")
with col_refresh:
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()

city = CITY_MAP[city_name]

# ══════════════════════════════════════════════════════════════
# 데이터 불러오기 & 표시
# ══════════════════════════════════════════════════════════════
try:
    data = fetch_weather(city["lat"], city["lon"])
except requests.exceptions.RequestException:
    st.error("날씨 정보를 불러오지 못했습니다. 인터넷 연결을 확인해 주세요.")
    st.stop()
except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
    st.stop()

now = datetime.now()
h = data["hourly"]
d = data["daily"]
times = h["time"]

# 현재 시각 인덱스
ci = 0
md = float("inf")
for i, t in enumerate(times):
    diff = abs((datetime.fromisoformat(t) - now).total_seconds())
    if diff < md:
        md = diff
        ci = i

cur_temp = round(h["temperature_2m"][ci])
cur_app = round(h["apparent_temperature"][ci])
cur_code = h["weathercode"][ci]
cur_wind = h["windspeed_10m"][ci]
cur_dir = h["winddirection_10m"][ci]
cur_humi = h["relativehumidity_2m"][ci]
cur_rain = h["precipitation"][ci]
t_max = round(d["temperature_2m_max"][0])
t_min = round(d["temperature_2m_min"][0])
info = get_weather_info(cur_code, now.hour)
bg1, bg2 = BG_COLORS.get(info["bg"], BG_COLORS["default"])

# ── 현재 날씨 헤더 ──
st.markdown(f"""
<div style="background: linear-gradient(135deg, {bg1}, {bg2});
            border-radius: 20px; padding: 40px 24px; text-align: center;
            color: white; margin-bottom: 16px;">
    <div style="font-size: 1.6em; font-weight: 300; letter-spacing: 1px;">{city_name}</div>
    <div style="font-size: 5em; font-weight: 100; line-height: 1.1; margin: 8px 0;">{cur_temp}°</div>
    <div style="font-size: 1.4em; margin-bottom: 4px;">{info['icon']}  {info['desc']}</div>
    <div style="font-size: 1.1em; opacity: 0.8;">최고 {t_max}°  ·  최저 {t_min}°</div>
    <div style="font-size: 0.8em; opacity: 0.5; margin-top: 8px;">업데이트: {now.strftime('%H:%M')}</div>
</div>
""", unsafe_allow_html=True)

# ── 탭: 시간별 / 주간 / 상세 ──
tab_hourly, tab_daily, tab_detail = st.tabs(["🕐 시간별 예보", "📅 주간 예보", "📊 상세 정보"])

# ── 시간별 예보 ──
with tab_hourly:
    # 24시간 예보를 6열 그리드로 표시
    cols_per_row = 6
    for row_start in range(0, 24, cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            i = row_start + j
            if i >= 24 or ci + i >= len(times):
                break
            idx = ci + i
            dt = datetime.fromisoformat(times[idx])
            lbl = "지금" if i == 0 else f"{dt.hour}시"
            hi = get_weather_info(h["weathercode"][idx], dt.hour)
            rain = h["precipitation"][idx]
            temp = round(h["temperature_2m"][idx])
            rain_txt = f"{rain:.1f}㎜" if rain > 0 else "—"
            tc = color_by_temp(temp)

            highlight = "background:rgba(100,181,246,0.15); border-radius:12px;" if i == 0 else ""
            with cols[j]:
                st.markdown(f"""
                <div style="text-align:center; padding:8px 2px; {highlight}">
                    <div style="font-size:0.85em; color:#888;">{lbl}</div>
                    <div style="font-size:1.5em;">{hi['icon']}</div>
                    <div style="font-size:1.1em; font-weight:bold; color:{tc};">{temp}°</div>
                    <div style="font-size:0.75em; color:#64B5F6;">{rain_txt}</div>
                </div>
                """, unsafe_allow_html=True)

# ── 주간 예보 ──
with tab_daily:
    kor_days = ["월", "화", "수", "목", "금", "토", "일"]
    a_max = d["temperature_2m_max"]
    a_min = d["temperature_2m_min"]
    g_max = max(a_max)
    g_min = min(a_min)
    g_rng = g_max - g_min or 1

    for i, ds in enumerate(d["time"]):
        dt = datetime.fromisoformat(ds)
        if i == 0:
            dn = "오늘"
        elif i == 1:
            dn = "내일"
        else:
            dn = f"{kor_days[dt.weekday()]}요일"

        di = get_weather_info(d["weathercode"][i], 12)
        rs = d["precipitation_sum"][i]
        d_max = round(a_max[i])
        d_min = round(a_min[i])

        bar_left = (a_min[i] - g_min) / g_rng * 100
        bar_w = max((a_max[i] - a_min[i]) / g_rng * 100, 5)
        rain_txt = f'<span style="color:#64B5F6;font-size:0.85em;">{rs:.1f}㎜</span>' if rs > 0 else ""

        st.markdown(f"""
        <div style="display:flex; align-items:center; padding:10px 8px;
                    border-bottom:1px solid rgba(0,0,0,0.06);">
            <div style="flex:0 0 60px; font-size:1em;">{dn}</div>
            <div style="flex:0 0 36px; font-size:1.3em; text-align:center;">{di['icon']}</div>
            <div style="flex:0 0 50px; text-align:center;">{rain_txt}</div>
            <div style="flex:1; height:6px; border-radius:3px; background:#eee; position:relative; margin:0 8px;">
                <div style="position:absolute; left:{bar_left:.1f}%; width:{bar_w:.1f}%;
                            height:100%; border-radius:3px;
                            background:linear-gradient(90deg, #42A5F5, #FF7043);"></div>
            </div>
            <div style="flex:0 0 36px; text-align:right; color:#999; font-size:0.95em;">{d_min}°</div>
            <div style="flex:0 0 36px; text-align:right; font-weight:bold; font-size:0.95em;">{d_max}°</div>
        </div>
        """, unsafe_allow_html=True)

# ── 상세 정보 ──
with tab_detail:
    # 2×2 정보 카드
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div style="background:#f8f9fa; border-radius:14px; padding:18px; margin-bottom:12px;">
            <div style="font-size:0.85em; color:#888; font-weight:bold;">💨 바람</div>
            <div style="font-size:1.8em; font-weight:300; margin:4px 0;">{cur_wind:.1f} m/s</div>
            <div style="font-size:0.9em; color:#888;">{wind_dir_text(cur_dir)}풍</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        humi_d = "매우 높음" if cur_humi >= 80 else ("높음" if cur_humi >= 60 else ("보통" if cur_humi >= 40 else "낮음"))
        st.markdown(f"""
        <div style="background:#f8f9fa; border-radius:14px; padding:18px; margin-bottom:12px;">
            <div style="font-size:0.85em; color:#888; font-weight:bold;">💧 습도</div>
            <div style="font-size:1.8em; font-weight:300; margin:4px 0;">{cur_humi}%</div>
            <div style="font-size:0.9em; color:#888;">{humi_d}</div>
        </div>
        """, unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown(f"""
        <div style="background:#f8f9fa; border-radius:14px; padding:18px; margin-bottom:12px;">
            <div style="font-size:0.85em; color:#888; font-weight:bold;">🌡 체감온도</div>
            <div style="font-size:1.8em; font-weight:300; margin:4px 0;">{cur_app}°</div>
            <div style="font-size:0.9em; color:#888;">실제 {cur_temp}°C</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div style="background:#f8f9fa; border-radius:14px; padding:18px; margin-bottom:12px;">
            <div style="font-size:0.85em; color:#888; font-weight:bold;">🌧 현재 강수</div>
            <div style="font-size:1.8em; font-weight:300; margin:4px 0;">{cur_rain:.1f} ㎜</div>
            <div style="font-size:0.9em; color:#888;">오늘 누적 {d['precipitation_sum'][0]:.1f}㎜</div>
        </div>
        """, unsafe_allow_html=True)

    # 시간별 바람/강수량 상세
    st.markdown("#### 🌬 향후 12시간 풍속")
    for i in range(min(13, len(times) - ci)):
        idx = ci + i
        dt = datetime.fromisoformat(times[idx])
        lbl = "지금" if i == 0 else f"{dt.hour}시"
        ws = h["windspeed_10m"][idx]
        wd = h["winddirection_10m"][idx]
        pct = min(ws / 20 * 100, 100)
        color = "#FF7043" if ws >= 10 else ("#FFA726" if ws >= 5 else "#42A5F5")

        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:3px;">
            <div style="width:40px; text-align:right; font-size:0.85em; color:#888;">{lbl}</div>
            <div style="flex:1; height:6px; background:#eee; border-radius:3px;">
                <div style="width:{pct:.1f}%; height:100%; background:{color}; border-radius:3px;"></div>
            </div>
            <div style="width:55px; font-size:0.85em; font-weight:bold;">{ws:.1f} m/s</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 🌧 향후 12시간 강수량")
    has_rain = any(h["precipitation"][ci + i] > 0 for i in range(min(13, len(times) - ci)))

    if not has_rain:
        st.info("☀️ 향후 12시간 강수 없음")
    else:
        for i in range(min(13, len(times) - ci)):
            idx = ci + i
            dt = datetime.fromisoformat(times[idx])
            lbl = "지금" if i == 0 else f"{dt.hour}시"
            rv = h["precipitation"][idx]
            pct = min(rv / 10 * 100, 100)
            color = "#1565C0" if rv >= 5 else ("#42A5F5" if rv >= 1 else "#90CAF9")
            val_txt = f"{rv:.1f} ㎜" if rv > 0 else "—"

            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:3px;">
                <div style="width:40px; text-align:right; font-size:0.85em; color:#888;">{lbl}</div>
                <div style="flex:1; height:6px; background:#eee; border-radius:3px;">
                    <div style="width:{pct:.1f}%; height:100%; background:{color}; border-radius:3px;"></div>
                </div>
                <div style="width:55px; font-size:0.85em; font-weight:bold;">{val_txt}</div>
            </div>
            """, unsafe_allow_html=True)
