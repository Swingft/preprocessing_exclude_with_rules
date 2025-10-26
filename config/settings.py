"""
settings.py

프로젝트 설정 및 환경 변수
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# .env 파일 로드
load_dotenv(PROJECT_ROOT / ".env")

# API 키
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
if not CLAUDE_API_KEY:
    raise ValueError("CLAUDE_API_KEY not found in .env file")

# Claude 모델 설정
CLAUDE_MODEL = "claude-sonnet-4-5"  # Claude Sonnet 4.5
MAX_TOKENS = 8192
TEMPERATURE = 0.2

# 디렉토리 경로
INPUT_SWIFT_DIR = PROJECT_ROOT / "data" / "input_swift"
RULES_DIR = PROJECT_ROOT / "data" / "rules"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
AST_CACHE_DIR = PROJECT_ROOT / "data" / "ast_cache"

# SwiftASTAnalyzer 실행 파일 경로
SWIFT_AST_ANALYZER = PROJECT_ROOT / "SwiftASTAnalyzer" / ".build" / "release" / "SwiftASTAnalyzer"

# Rule 파일 경로
RULES_YAML_PATH = RULES_DIR / "swift_exclusion_rules.yaml"

# 처리 설정
MAX_WORKERS = 5  # 병렬 처리 워커 수
BATCH_SIZE = 10  # 배치 크기
REQUEST_DELAY = 0.5  # API 요청 간 딜레이 (초)
MAX_RETRIES = 3  # 최대 재시도 횟수

# 출력 설정
OUTPUT_JSONL = OUTPUT_DIR / "dataset.jsonl"

# 디버그 모드
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# 디렉토리 생성
for directory in [INPUT_SWIFT_DIR, RULES_DIR, OUTPUT_DIR, AST_CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

print(f"✓ 설정 로드 완료")
print(f"  - 입력 디렉토리: {INPUT_SWIFT_DIR}")
print(f"  - Rule 파일: {RULES_YAML_PATH}")
print(f"  - 출력 파일: {OUTPUT_JSONL}")
print(f"  - AST 캐시: {AST_CACHE_DIR}")
print(f"  - 모델: {CLAUDE_MODEL}")
