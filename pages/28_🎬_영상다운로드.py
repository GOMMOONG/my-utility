import streamlit as st
import re
import shutil
import tempfile
import mimetypes
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from style import apply_common_style, show_page_header, check_password

st.set_page_config(page_title="영상다운로드 - 마이 유틸리티", page_icon="🎬", layout="centered")
apply_common_style()
check_password()
show_page_header("🎬", "영상 다운로드", "유튜브 등 대부분 사이트의 영상 주소를 넣으면 파일로 저장할 수 있어요")

try:
    import yt_dlp
except ImportError:
    st.error("이 페이지를 쓰려면 'yt-dlp' 설치가 필요합니다. website/requirements.txt에 포함되어 있는지 확인해주세요.")
    st.stop()

MAX_DURATION_SECONDS = 30 * 60  # 서버 자원 보호를 위해 30분으로 제한


def build_format(quality, has_ffmpeg):
    """화질 선택값을 yt-dlp 형식 문자열로 변환"""
    height_map = {"최고화질": None, "1080p": 1080, "720p": 720, "480p": 480}
    height = height_map.get(quality)
    if has_ffmpeg:
        return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]" if height else "bestvideo+bestaudio/best"
    return f"best[height<={height}]/best" if height else "best"


def safe_filename(title):
    """파일 이름으로 쓸 수 없는 문자를 제거"""
    return re.sub(r'[\\/*?:"<>|]', "", title).strip() or "video"


def friendly_error(e, has_node):
    """yt-dlp 오류 메시지를 사용자가 이해하기 쉬운 한글 문구로 변환"""
    text = str(e)
    if "Unsupported URL" in text or "is not a valid URL" in text:
        return "지원하지 않는 사이트이거나 잘못된 주소예요. 링크를 다시 확인해주세요."
    if "Private video" in text:
        return "비공개 영상이라 다운로드할 수 없어요."
    if "Sign in to confirm your age" in text or ("age" in text.lower() and "restrict" in text.lower()):
        return "연령 제한이 있는 영상이라 다운로드할 수 없어요."
    if ("not available" in text or "This video is unavailable" in text) and not has_node:
        return "유튜브의 새로운 봇 차단 때문에 실패했을 수 있어요 (실제로는 정상 영상일 수 있음). 서버에 Node.js 설정이 필요합니다."
    if "This video is unavailable" in text:
        return "삭제되었거나 볼 수 없는 영상이에요."
    if "getaddrinfo failed" in text or "Failed to resolve" in text or "NewConnectionError" in text:
        return "인터넷 연결을 확인해주세요."
    return f"다운로드 중 오류가 발생했어요: {text[:120]}"


has_ffmpeg = shutil.which("ffmpeg") is not None
has_node = shutil.which("node") is not None
if has_ffmpeg:
    st.caption("🎬 ffmpeg 사용 가능 - 고화질로 받을 수 있어요")
else:
    st.caption("⚠ ffmpeg 미설치 - 화질이 낮게 나올 수 있어요")
if not has_node:
    st.caption("⚠ Node.js 미설치 - 일부 유튜브 영상은 받지 못할 수 있어요")

with st.expander("ℹ️ 안내 (지원 사이트 · 저작권 유의사항)"):
    st.markdown("""
    - 유튜브, 네이버TV, 인스타그램 등 대부분의 동영상 사이트 링크를 지원해요.
    - 한 번에 영상 1개만 받을 수 있어요 (재생목록 전체 다운로드는 지원하지 않아요).
    - 서버 자원 보호를 위해 **30분이 넘는 영상은 받을 수 없어요.**
    - 유튜브의 새로운 봇 차단 기술 때문에 가끔 정상 영상인데도 오류가 날 수 있어요.
      이 경우 서버에 Node.js 설정이 필요합니다(운영자 확인 필요).
    - 본인이 만든 영상이거나 다운로드가 허용된 영상만 저장해주세요.
      저작권이 있는 콘텐츠를 허락 없이 다운로드·배포하는 것은 안 됩니다.
    """)

url = st.text_input("영상 주소(URL)", placeholder="https://www.youtube.com/watch?v=...")
quality = st.selectbox("화질", ["최고화질", "1080p", "720p", "480p"])

if "video_bytes" not in st.session_state:
    st.session_state.video_bytes = None
    st.session_state.video_filename = None
    st.session_state.video_mime = None

if st.button("⬇ 다운로드 준비", type="primary", use_container_width=True):
    if not url.strip():
        st.warning("영상 주소를 입력해주세요.")
    else:
        st.session_state.video_bytes = None
        st.session_state.video_filename = None
        try:
            with st.spinner("영상 정보를 확인하는 중..."):
                probe_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
                if has_node:
                    probe_opts["js_runtimes"] = {"node": {}}
                with yt_dlp.YoutubeDL(probe_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

            duration = info.get("duration") or 0
            if duration > MAX_DURATION_SECONDS:
                st.error(f"영상이 너무 길어요 (약 {duration // 60}분). 30분 이하의 영상만 받을 수 있어요.")
            else:
                tmp_dir = tempfile.mkdtemp()
                try:
                    ydl_opts = {
                        "outtmpl": os.path.join(tmp_dir, "%(title)s.%(ext)s"),
                        "format": build_format(quality, has_ffmpeg),
                        "noplaylist": True,
                        "merge_output_format": "mp4",
                        "quiet": True,
                        "no_warnings": True,
                    }
                    if has_node:
                        ydl_opts["js_runtimes"] = {"node": {}}
                    with st.spinner("다운로드하는 중... 영상 길이에 따라 시간이 걸릴 수 있어요"):
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            result = ydl.extract_info(url, download=True)

                    files = [os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir)]
                    if not files:
                        raise RuntimeError("다운로드된 파일을 찾을 수 없어요.")
                    filepath = max(files, key=os.path.getsize)

                    with open(filepath, "rb") as f:
                        st.session_state.video_bytes = f.read()
                    ext = os.path.splitext(filepath)[1] or ".mp4"
                    st.session_state.video_filename = safe_filename(result.get("title", "video")) + ext
                    st.session_state.video_mime = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
                finally:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception as e:
            st.error(friendly_error(e, has_node))

if st.session_state.video_bytes:
    st.success("✅ 준비 완료! 아래 버튼으로 내 기기에 저장하세요.")
    st.download_button(
        "📥 내 기기에 저장하기",
        data=st.session_state.video_bytes,
        file_name=st.session_state.video_filename,
        mime=st.session_state.video_mime,
        use_container_width=True,
    )
