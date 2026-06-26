# 앱 아이콘 생성 스크립트 — 한 번만 실행하면 됩니다
# 실행 방법: python generate_icons.py

import subprocess
import sys
import os

# Pillow(이미지 처리 도구)가 없으면 자동 설치
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow 패키지를 설치합니다...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont

# static 폴더 만들기
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)

# 만들 아이콘 크기 목록
SIZES = {
    "icon-180x180.png": 180,   # 아이폰 홈화면용
    "icon-192x192.png": 192,   # PWA 표준 크기
    "icon-512x512.png": 512,   # PWA 큰 아이콘 (스플래시 화면)
}

# 색상 설정
BG_COLOR = (108, 92, 231)      # #6C5CE7 보라색
TEXT_COLOR = (255, 255, 255)    # 흰색

for filename, size in SIZES.items():
    # 보라색 배경 이미지 생성
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 둥근 모서리 사각형 그리기
    radius = size // 5
    draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=radius,
        fill=BG_COLOR,
    )

    # 가운데에 "MU" 글자 넣기
    font_size = size // 3
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    text = "MU"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2
    y = (size - text_h) // 2
    draw.text((x, y), text, fill=TEXT_COLOR, font=font)

    # 파일 저장
    filepath = os.path.join(static_dir, filename)
    img.save(filepath, "PNG")
    print(f"  생성 완료: {filename} ({size}x{size})")

print("\n모든 아이콘이 static 폴더에 생성되었습니다!")
