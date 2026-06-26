"""
API 키를 파일에 저장하고 불러오는 공용 모듈
website/data/api_keys.json 파일에 암호화 없이 로컬 저장
"""
import json
import os

# API 키 저장 파일 경로
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "data", "api_keys.json")


def load_api_keys() -> dict:
    """저장된 API 키를 불러옵니다. 파일이 없으면 빈 딕셔너리 반환."""
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_api_keys(keys: dict) -> bool:
    """API 키를 파일에 저장합니다. 성공하면 True 반환."""
    try:
        os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(keys, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_key(name: str) -> str:
    """특정 키 이름으로 저장된 값을 가져옵니다."""
    return load_api_keys().get(name, "")


def set_key(name: str, value: str) -> bool:
    """특정 키 이름으로 값을 저장합니다."""
    keys = load_api_keys()
    keys[name] = value
    return save_api_keys(keys)
