"""
아이폰 벨소리 만들기 (웹 버전)
- 유튜브 주소 → 음악만 내려받기 → 들으면서 시작점 고르기 → 10~30초 m4a 벨소리로 저장
- 아이폰 사파리로 접속하면 바로 '파일' 앱에 저장할 수 있음 (카카오톡 전송 불필요)
- 데스크톱 버전: ringtone_maker.py
"""
import streamlit as st
import os
import re
import sys
import shutil
import tempfile
import subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="벨소리만들기 - 마이 유틸리티", page_icon="🔔", layout="centered")
apply_common_style()
check_password()
show_page_header("🔔", "아이폰 벨소리 만들기", "유튜브 음악을 들으면서 원하는 부분을 골라 벨소리 파일로 저장해요")

try:
    import yt_dlp
except ImportError:
    st.error("이 페이지를 쓰려면 'yt-dlp' 설치가 필요합니다. website/requirements.txt를 확인해주세요.")
    st.stop()

MAX_DURATION_SECONDS = 30 * 60  # 서버 자원 보호를 위해 30분 이하 영상만


def find_ffmpeg():
    """ffmpeg(음악 자르기·변환 프로그램) 위치 찾기. 서버는 packages.txt로 설치됨"""
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:  # 내 PC에서 실행할 때: 데스크톱 앱이 설치한 imageio-ffmpeg 사용
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


FFMPEG = find_ffmpeg()
has_node = shutil.which("node") is not None
if not FFMPEG:
    st.error("음악을 자르는 프로그램(ffmpeg)이 없어서 이 페이지를 쓸 수 없어요. 운영자 확인이 필요합니다.")
    st.stop()


def run_ffmpeg(args):
    """ffmpeg 실행. 실패하면 오류를 일으킴"""
    result = subprocess.run([FFMPEG, "-y", "-loglevel", "error"] + args,
                            capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg 실행 실패")


def fmt_time(seconds):
    """초를 '분:초' 글자로 (예: 75 → '1:15')"""
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def safe_filename(title):
    """파일 이름으로 쓸 수 없는 글자 제거"""
    return re.sub(r'[\\/*?:"<>|]', "", title).strip()[:60] or "벨소리"


def fade_filter(length):
    """시작 1초는 서서히 커지고, 마지막 2초는 서서히 작아지게"""
    fade_out = min(2.0, length / 3)
    return f"afade=t=in:st=0:d=1,afade=t=out:st={length - fade_out:.2f}:d={fade_out:.2f}"


def friendly_error(text):
    """어려운 오류 메시지를 쉬운 말로"""
    if "Unsupported URL" in text or "is not a valid URL" in text:
        return "주소가 올바르지 않아요. 유튜브 영상 주소를 다시 복사해서 붙여넣어 주세요."
    if "Private video" in text:
        return "비공개 영상이라 받을 수 없어요."
    if ("not available" in text or "unavailable" in text) and not has_node:
        return "유튜브의 봇 차단 때문에 실패했을 수 있어요 (정상 영상일 수 있음). 잠시 후 다시 시도하거나 다른 영상을 골라주세요."
    if "unavailable" in text:
        return "삭제되었거나 볼 수 없는 영상이에요."
    if "403" in text or "Sign in" in text:
        return "유튜브가 다운로드를 막았어요 (프로그램 문제가 아니에요). 잠시 후 다시 시도해주세요."
    if "getaddrinfo" in text or "Failed to resolve" in text:
        return "인터넷 연결을 확인해주세요."
    return f"오류가 발생했어요: {text[:150]}"


# ── 상태 저장소(페이지를 다시 그려도 유지되는 값) 준비 ──────────────
ss = st.session_state
for key, default in {"rt_dir": None, "rt_song": None, "rt_listen": None, "rt_title": "",
                     "rt_duration": 0, "rt_clip": None, "rt_clip_name": ""}.items():
    if key not in ss:
        ss[key] = default

with st.expander("ℹ️ 사용 방법 · 아이폰에 등록하는 법"):
    st.markdown("""
**만드는 순서**
1. 유튜브 주소를 붙여넣고 **[음악 가져오기]**를 누릅니다.
2. 막대로 위치를 옮기며 **들어보고**, 마음에 드는 시작점을 정합니다.
3. 길이(10~30초)를 고르고 **[벨소리 만들기]** → 미리듣기 → **[벨소리 저장]**.

**아이폰에 등록하기**
- **아이폰 사파리로 이 페이지에 접속했다면:** [벨소리 저장]을 누르면 '파일' 앱의 '다운로드' 폴더에 바로 저장돼요.
- **PC에서 만들었다면:** 저장된 파일을 카카오톡 '나와의 채팅'으로 보낸 뒤, 아이폰에서 파일을 눌러 공유 → '파일에 저장'.

그다음:
- **최신 iOS:** '파일' 앱에서 파일을 길게 누름 → 공유 → **'벨소리로 사용'**이 보이면 누르면 끝!
- **그 메뉴가 없으면 GarageBand(무료 앱):**
  1. GarageBand 실행 → 아무 악기나 골라 새 프로젝트 → 왼쪽 위 '트랙 보기'(벽돌 모양)
  2. 오른쪽 위 '루프'(고리 모양) → '파일' 탭 → '파일 앱에서 항목 탐색' → 벨소리 파일 선택
  3. 파일을 길게 눌러 트랙 맨 앞으로 끌어다 놓기
  4. 왼쪽 위 '▼ 나의 노래' → 프로젝트 길게 누름 → 공유 → '벨소리' → 내보내기 → '표준 벨소리'
- 확인: '설정' → '사운드 및 햅틱' → '벨소리'

※ 개인 벨소리 용도로만 사용해주세요 (저작권 보호). 30분이 넘는 영상은 받을 수 없어요.
""")

# ── 1단계: 음악 가져오기 ────────────────────────────────────────
st.subheader("1단계 · 유튜브 주소 붙여넣기")
url = st.text_input("유튜브 주소", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")

if st.button("🎵 음악 가져오기", type="primary", use_container_width=True):
    if not url.strip().startswith("http"):
        st.warning("유튜브 주소(https://로 시작)를 붙여넣어 주세요.")
    else:
        # 이전 작업 파일 정리
        if ss.rt_dir:
            shutil.rmtree(ss.rt_dir, ignore_errors=True)
        ss.rt_dir = ss.rt_song = ss.rt_listen = ss.rt_clip = None
        try:
            opts = {"quiet": True, "no_warnings": True, "noplaylist": True, "noprogress": True}
            if has_node:
                opts["js_runtimes"] = {"node": {}}
            with st.spinner("음악 정보를 확인하는 중..."):
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            duration = info.get("duration") or 0
            if info.get("_type") == "playlist":
                st.error("재생목록 주소예요. 노래 하나의 주소를 넣어주세요.")
            elif duration > MAX_DURATION_SECONDS:
                st.error(f"영상이 너무 길어요 ({fmt_time(duration)}). 30분 이하 영상만 받을 수 있어요.")
            else:
                work = tempfile.mkdtemp(prefix="ringtone_")
                opts.update({"format": "bestaudio/best",
                             "outtmpl": os.path.join(work, "source.%(ext)s")})
                with st.spinner("음악을 내려받는 중... (1분 정도 걸릴 수 있어요)"):
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        source = ydl.prepare_filename(info)
                    # 자르기용 원본(wav)과, 화면에서 들을 가벼운 파일(m4a) 두 가지로 변환
                    song = os.path.join(work, "song.wav")
                    listen = os.path.join(work, "listen.m4a")
                    run_ffmpeg(["-i", source, "-vn", "-ac", "2", "-ar", "44100", song])
                    run_ffmpeg(["-i", song, "-c:a", "aac", "-b:a", "96k", listen])
                    os.remove(source)
                ss.rt_dir, ss.rt_song, ss.rt_listen = work, song, listen
                ss.rt_title = info.get("title", "벨소리")
                ss.rt_duration = int(info.get("duration") or duration or 1)
                ss.rt_start = 0  # 시작점 막대를 처음으로
        except Exception as e:
            st.error(friendly_error(str(e)))

# 노래가 준비되지 않았으면 여기서 멈춤
if not ss.rt_song or not os.path.exists(ss.rt_song):
    st.stop()

# ── 2단계: 들으면서 시작점 고르기 ───────────────────────────────
st.divider()
st.subheader("2단계 · 들으면서 시작점 고르기")
st.markdown(f"🎶 **{ss.rt_title}**  ({fmt_time(ss.rt_duration)})")

start = st.slider("시작점 (초)", 0, max(1, ss.rt_duration - 1), key="rt_start",
                  help="막대를 옮기면 아래 플레이어가 그 위치부터 재생돼요")
st.caption(f"📍 선택한 시작점: **{fmt_time(start)}**  — 아래 ▶를 눌러 이 위치부터 들어보세요")
with open(ss.rt_listen, "rb") as f:
    st.audio(f.read(), format="audio/mp4", start_time=start)

# ── 3단계: 길이 정하고 벨소리 만들기 ───────────────────────────
st.divider()
st.subheader("3단계 · 벨소리 만들고 저장하기")
length = st.select_slider("벨소리 길이", options=[10, 15, 20, 25, 30], value=30,
                          format_func=lambda s: f"{s}초")
length = max(1, min(length, ss.rt_duration - start))
st.caption(f"✂️ {fmt_time(start)} → {fmt_time(start + length)} 구간 ({length}초)")

if st.button("✂️ 벨소리 만들기", type="primary", use_container_width=True):
    clip = os.path.join(ss.rt_dir, "ringtone.m4a")
    try:
        with st.spinner("벨소리를 만드는 중..."):
            run_ffmpeg(["-ss", str(start), "-t", str(length), "-i", ss.rt_song,
                        "-af", fade_filter(length), "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", clip])
        with open(clip, "rb") as f:
            ss.rt_clip = f.read()
        ss.rt_clip_name = f"{safe_filename(ss.rt_title)}_벨소리.m4a"
    except Exception as e:
        st.error(f"벨소리를 만들지 못했어요: {str(e)[:150]}")

if ss.rt_clip:
    st.success("✅ 벨소리 완성! 들어보고 마음에 들면 저장하세요. (구간을 바꿨다면 [벨소리 만들기]를 다시 눌러주세요)")
    st.audio(ss.rt_clip, format="audio/mp4")
    st.download_button("📥 벨소리 저장 (m4a)", data=ss.rt_clip, file_name=ss.rt_clip_name,
                       mime="audio/mp4", use_container_width=True)
    st.caption("아이폰에 등록하는 방법은 위의 'ℹ️ 사용 방법'을 열어보세요.")
