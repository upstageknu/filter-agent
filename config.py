import os

from dotenv import load_dotenv

load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
UPSTAGE_BASE_URL = os.getenv("UPSTAGE_BASE_URL", "https://api.upstage.ai/v1")
SOLAR_MODEL = os.getenv("SOLAR_MODEL", "solar-pro")

DOCUMENT_PARSE_URL = os.getenv(
    "DOCUMENT_PARSE_URL", "https://api.upstage.ai/v1/document-digitization"
)
DOCUMENT_PARSE_MODEL = os.getenv("DOCUMENT_PARSE_MODEL", "document-parse")

HUB_BASE_URL = os.getenv("HUB_BASE_URL", "https://api.mingyo.kim/upstageknu2607")

# 필터 agent가 "버그 리포트 아님"을 이 값 이상으로 확신할 때만 반려한다.
# 애매한 리포트는 통과시켜 fact_check/debate 단계가 한 번 더 검증하게 하는 recall 우선 정책.
FILTER_REJECT_CONFIDENCE_THRESHOLD = float(
    os.getenv("FILTER_REJECT_CONFIDENCE_THRESHOLD", "0.6")
)


def require_api_key() -> str:
    if not UPSTAGE_API_KEY:
        raise RuntimeError("UPSTAGE_API_KEY가 설정되지 않았습니다. .env를 확인하세요.")
    return UPSTAGE_API_KEY
