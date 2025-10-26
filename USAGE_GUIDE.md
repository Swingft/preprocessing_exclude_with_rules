# preprocessing_exclude_with_rules 사용 가이드

## 🚀 빠른 시작 (5분 안에!)

### 1단계: 압축 해제
```bash
tar -xzf preprocessing_exclude_with_rules.tar.gz
cd preprocessing_exclude_with_rules
```

### 2단계: 환경 설정
```bash
# Python 패키지 설치
pip install -r requirements.txt

# API 키 설정
cp .env.example .env
nano .env  # CLAUDE_API_KEY 입력
```

### 3단계: Swift 코드 준비
```bash
# 기존 생성된 Swift 코드를 input 디렉토리에 복사
cp /path/to/your/*.swift data/input_swift/
```

### 4단계: 실행!
```bash
# 전체 실행
python main.py

# 또는 테스트 (처음 5개만)
python main.py --limit 5
```

### 5단계: 결과 확인
```bash
cat data/output/dataset.jsonl
```

---

## 📋 필수 요구사항

### 1. Python 환경
- Python 3.8+
- pip로 설치 가능한 패키지들

### 2. API 키
- Claude API Key (Anthropic)
- `.env` 파일에 설정

### 3. SwiftASTAnalyzer (선택)
- macOS에서만 빌드 가능
- 없어도 동작하지만, AST 정보 없이 진행

---

## 🔧 상세 설정

### API 키 설정 (.env)
```bash
# .env 파일 생성
CLAUDE_API_KEY=sk-ant-api03-...

# 디버그 모드 (선택)
DEBUG=true
```

### SwiftASTAnalyzer 빌드 (macOS)
```bash
cd SwiftASTAnalyzer
swift build -c release
cd ..
```

---

## 💡 실행 옵션

### 기본 실행
```bash
python main.py
```

### 제한된 파일 수
```bash
python main.py --limit 10
```

### 순차 처리 (병렬 X)
```bash
python main.py --no-parallel
```

### 디버그 모드
```bash
python main.py --debug --limit 1
```

### 모든 옵션 조합
```bash
python main.py --limit 5 --no-parallel --debug
```

---

## 📊 출력 형식

### dataset.jsonl 구조
```jsonl
{"input": "프롬프트 전체...", "output": "{\"identifiers\": [\"id1\", \"id2\"]}"}
{"input": "프롬프트 전체...", "output": "{\"identifiers\": [\"id3\"]}"}
```

각 라인:
- **input**: Swift 코드 + AST + Rule 예시를 포함한 완전한 프롬프트
- **output**: `{"identifiers": [...]}` JSON 문자열

---

## 🐛 문제 해결

### 1. "CLAUDE_API_KEY not found"
```bash
# .env 파일 확인
cat .env

# API 키 재설정
echo "CLAUDE_API_KEY=your_key_here" > .env
```

### 2. "Swift 파일이 없습니다"
```bash
# input 디렉토리 확인
ls data/input_swift/

# Swift 파일 복사
cp *.swift data/input_swift/
```

### 3. "SwiftASTAnalyzer not found"
```bash
# 빌드 (macOS만)
cd SwiftASTAnalyzer
swift build -c release
cd ..

# 또는 AST 없이 진행 (경고만 뜸)
```

### 4. API 에러
```bash
# 재시도 로직이 자동으로 동작
# 실패 파일만 다시 처리하려면:
python main.py  # 기존 결과는 append됨
```

---

## 📈 성능 최적화

### 1. 병렬 처리
```python
# config/settings.py
MAX_WORKERS = 10  # 워커 수 증가
```

### 2. 배치 크기
```python
# config/settings.py
BATCH_SIZE = 20  # 배치 크기 조정
```

### 3. API 딜레이
```python
# config/settings.py
REQUEST_DELAY = 0.3  # 딜레이 감소 (주의!)
```

---

## 📦 데이터셋 활용

### 1. LoRA 파인튜닝
```python
# dataset.jsonl을 직접 사용
dataset = load_dataset("json", data_files="dataset.jsonl")
```

### 2. 평가 데이터셋
```python
# 일부를 평가용으로 분리
train, eval = train_test_split(dataset, test_size=0.1)
```

### 3. 데이터 증강
```python
# 기존 데이터에 추가
# append 모드로 실행하면 자동 추가됨
```

---

## 🎯 프롬프트 커스터마이징

### generators/prompt_builder.py 수정

```python
def build_prompt(self, swift_code, ast_data, rules_text):
    # 지시사항 추가
    extra_instructions = """
    추가 지시사항:
    - SwiftUI View는 모두 제외
    - @Published 속성도 고려
    """
    
    prompt = f"""
    {기본_지시사항}
    {extra_instructions}
    ...
    """
```

---

## 📞 지원

문제 발생 시:
1. README.md 확인
2. 디버그 모드로 실행: `python main.py --debug --limit 1`
3. 로그 확인

---

## ✅ 체크리스트

실행 전 확인:
- [ ] Python 3.8+ 설치됨
- [ ] `pip install -r requirements.txt` 완료
- [ ] `.env` 파일에 API 키 설정
- [ ] `data/input_swift/`에 Swift 파일 있음
- [ ] (선택) SwiftASTAnalyzer 빌드됨

모두 체크되었다면:
```bash
python main.py
```

끝! 🎉
