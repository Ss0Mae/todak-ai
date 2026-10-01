from pathlib import Path
import os
import yaml

# 사용자 ID는 환경 변수에서 가져오고, 없을 경우 기본값 사용
USER_ID = os.getenv("USER_ID", "user_001")

# 기본 디렉토리 설정
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROMPT_DIR = BASE_DIR / "prompts"
LOG_DIR = BASE_DIR / "logs"
AUDIO_DIR = BASE_DIR / "static"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# 디렉토리 생성
for path in [DATA_DIR, PROMPT_DIR, LOG_DIR]:
    path.mkdir(parents=True, exist_ok=True)

def load_prompt(file_name):
    prompt_path = PROMPT_DIR / file_name
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_config():
    return {
        "openai": {
            "key": os.getenv("OPENAI_API_KEY", "")
        }
    }
def load_config():
    """conf.d/config.yaml 이 있으면 그것을, 없으면 환경변수로 같은 구조를 만든다.

    로컬 재현(docker compose)에서 yaml 파일 없이 띄우기 위한 폴백이다.
    """
    config_path = Path(__file__).parent / "conf.d" / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {
        "openai": {"key": os.getenv("OPENAI_API_KEY", "")},
        "mongodb": {"uri": os.getenv("MONGODB_URI", "mongodb://localhost:27017")},
        "clova": {
            "client_id": os.getenv("CLOVA_CLIENT_ID", ""),
            "client_secret": os.getenv("CLOVA_CLIENT_SECRET", ""),
        },
    }

def set_openai_api_key():
    config = load_config()
    os.environ["OPENAI_API_KEY"] = config["openai"]["key"]

