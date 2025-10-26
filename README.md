# preprocessing_exclude_with_rules

Swift 난독화 제외 식별자 데이터셋 생성 파이프라인 (휴리스틱 Rule 기반)

## 📋 개요

기존 생성된 Swift 코드를 입력으로 받아, **소스코드 + AST + 휴리스틱 Rule**을 결합하여 난독화 제외 식별자를 추출하는 학습 데이터셋을 생성합니다.

### 핵심 특징

- ✅ **Rule은 예시**: LLM이 Rule을 참고하되, 전문가 판단으로 추가 패턴도 발견
- ✅ **AST 기반 필터링**: 프로젝트 전체 Rule에서 파일 관련 Rule만 추출
- ✅ **Claude Sonnet 4.5**: 고품질 식별자 추출
- ✅ **JSONL 출력**: LoRA 파인튜닝 데이터셋으로 바로 사용 가능

## 🏗️ 프로젝트 구조

```
preprocessing_exclude_with_rules/
├── config/
│   ├── __init__.py
│   └── settings.py              # API 키, 경로 설정
├── handlers/
│   ├── __init__.py
│   └── claude_handler.py        # Claude Sonnet 4.5 API
├── analyzers/
│   ├── __init__.py
│   ├── ast_analyzer.py          # Swift AST 추출
│   └── rule_filter.py           # YAML Rule 필터링
├── generators/
│   ├── __init__.py
│   ├── prompt_builder.py        # 프롬프트 생성
│   └── dataset_generator.py    # 데이터셋 생성 파이프라인
├── utils/
│   ├── __init__.py
│   └── file_utils.py            # 파일 I/O 유틸리티
├── data/
│   ├── input_swift/             # ← Swift 코드 여기에
│   ├── rules/
│   │   └── swift_exclusion_rules.yaml
│   ├── ast_cache/               # AST 캐시
│   └── output/
│       └── dataset.jsonl        # ← 결과
├── SwiftASTAnalyzer/            # Swift AST 추출 도구
│   ├── Package.swift
│   └── Sources/...
├── main.py                      # 메인 실행 파일
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성
cp .env.example .env
# .env 파일을 열어서 CLAUDE_API_KEY 설정

# SwiftASTAnalyzer 빌드 (macOS 필요)
cd SwiftASTAnalyzer
swift build -c release
cd ..
```

### 2. 데이터 준비

```bash
# Swift 코드 배치
cp /path/to/generated/*.swift data/input_swift/

# Rule 파일 확인 (이미 포함되어 있음)
ls data/rules/swift_exclusion_rules.yaml
```

### 3. 실행

```bash
# 전체 파일 처리
python main.py

# 처음 10개 파일만 테스트
python main.py --limit 10

# 순차 처리 (디버깅용)
python main.py --no-parallel --debug --limit 1
```

## 📄 출력 형식

### dataset.jsonl
```jsonl
{"input": "You are an expert...\n\nSwift Code:\n...", "output": "{\"identifiers\": [\"viewDidLoad\", \"delegate\"]}"}
{"input": "You are an expert...\n\nSwift Code:\n...", "output": "{\"identifiers\": [\"id\", \"name\"]}"}
```

각 라인은 하나의 학습 샘플입니다:
- **input**: 완성된 프롬프트 (Swift 코드 + AST + Rule 예시)
- **output**: JSON 문자열 `{"identifiers": [...]}`

## 🎯 핵심 로직

### 1. Rule 필터링

```python
# 프로젝트 전체 YAML Rule
rules = load_yaml("swift_exclusion_rules.yaml")

# 파일의 AST 추출
ast_data = extract_ast("MyViewController.swift")

# 파일과 관련된 Rule만 필터링
filtered_rules = filter_by_identifiers(ast_data, rules)
# → UIViewController 관련 Rule만 선택
```

### 2. 프롬프트 생성

```
# Role
You are a Swift obfuscation safety expert.

# Instructions
- The provided rules are EXAMPLES (참고용)
- Use your expertise to find ADDITIONAL patterns
- Apply Swift/iOS framework knowledge

# Input
- Swift Code: ...
- AST: ...
- Example Rules: ...

# Output
{"identifiers": ["id1", "id2", ...]}
```

### 3. Claude API 호출

```python
response = claude.generate(prompt)
# → {"identifiers": ["viewDidLoad", "tableView", ...]}
```

## ⚙️ 설정

### config/settings.py

```python
CLAUDE_MODEL = "claude-sonnet-4.5-20241022"
MAX_TOKENS = 4096
TEMPERATURE = 0.2
MAX_WORKERS = 5
```

### 환경 변수 (.env)

```bash
CLAUDE_API_KEY=sk-ant-...
DEBUG=false
```

## 🔧 주요 기능

### AST 캐싱
- 동일한 코드는 한 번만 AST 추출
- `data/ast_cache/` 디렉토리에 캐시 저장

### 병렬 처리
- 기본 5개 워커로 병렬 처리
- `--no-parallel`로 순차 처리 가능

### 재시도 로직
- API 실패 시 최대 3회 재시도
- 지수 백오프 적용

### 강력한 JSON 파싱
- 3단계 파싱으로 안정적인 결과 추출
- 마크다운, 주석 자동 제거

## 💡 사용 예시

### 전체 파이프라인
```bash
python main.py
```

### 테스트 (처음 5개 파일)
```bash
python main.py --limit 5 --debug
```

### 순차 처리 (디버깅)
```bash
python main.py --no-parallel --debug --limit 1
```

## 📊 성능

- **처리 속도**: ~10-20 files/min (Claude API 속도에 따라)
- **AST 캐싱**: 중복 파일 빠른 처리
- **병렬 처리**: 5-10 워커 추천

## ⚠️ 주의사항

1. **Claude API 비용**: 파일 수 × 토큰 수 고려
2. **SwiftASTAnalyzer**: macOS에서 Swift 빌드 필요
3. **Rule 파일**: YAML 형식 엄격히 준수

## 📦 출력 활용

생성된 `dataset.jsonl`은 다음 용도로 사용:
- **LoRA 파인튜닝** 데이터셋
- **평가 데이터셋**
- **추가 데이터 증강**

## 🐛 디버깅

### AST 추출 확인
```bash
cd SwiftASTAnalyzer
./.build/release/SwiftASTAnalyzer ../data/input_swift/example.swift
```

### 캐시 확인
```bash
ls data/ast_cache/
```

### 프롬프트 출력
```bash
python main.py --debug --limit 1
```

## 🤝 기여

이 프로젝트는 Swingft 프로젝트의 일부입니다.

## 📄 라이센스

MIT
