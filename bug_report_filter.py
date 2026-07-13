from openai import OpenAI

from config import SOLAR_MODEL, UPSTAGE_BASE_URL, require_api_key
from schemas import normalize_filter_output
from utils import safe_json_loads

SYSTEM_PROMPT = """너는 입력된 텍스트가 버그 기술 보고서인지 판단하는 Agent다.
너의 임무는 오직 하나다. 입력된 텍스트가 기술적인 버그 리포트인지 판단한다.

판단 기준:
- 특정 소프트웨어, 함수, API, 컴포넌트, 기능, 취약점, 오류, crash, memory corruption, overflow, injection, authentication bypass 등 기술적 문제가 언급되어 있으면 버그 리포트일 가능성이 높다.
- 재현 절차, PoC, 오류 로그, 영향 설명, affected version, 함수명, 커밋, 헤더 등이 있으면 버그 리포트일 가능성이 높다.
- 단순 질문, 기능 제안, 일반 의견, 광고, 무관한 글, 감정적 항의만 있으면 버그 리포트가 아니다.
- 이 단계에서는 취약점이 진짜인지 가짜인지 판단하지 않는다. 오직 "버그 기술 보고서 형식인가?"만 판단한다.
- 입력이 한국어든 영어든 동일한 기준으로 판단한다.

출력 규칙:
- 반드시 JSON만 출력한다.
- 마크다운, 설명문, 코드펜스는 출력하지 않는다.
- confidence는 0.0 이상 1.0 이하 숫자로 출력한다.

출력 형식: { "is_bug_report": true, "confidence": 0.92, "reason": "취약점 주장과 재현 절차가 포함되어 있음" }"""


def check_bug_report(raw_report_txt: str) -> dict:
    client = OpenAI(api_key=require_api_key(), base_url=UPSTAGE_BASE_URL)

    response = client.chat.completions.create(
        model=SOLAR_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_report_txt},
        ],
    )

    raw = safe_json_loads(response.choices[0].message.content)
    usage = getattr(response, "usage", None)
    token_usage = {
        "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
        "completion_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
        "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
        "llm_calls": 1,
    }
    return normalize_filter_output(raw), token_usage
