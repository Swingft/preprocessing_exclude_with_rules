# preprocessing_exclude_with_rules

Swift 난독화 제외 식별자 데이터셋 생성 (Rule 기반)

## 🎯 핵심 개념

**기존**: 소스코드 + AST → 식별자  
**신규**: 소스코드 + AST + **휴리스틱 Rule** → 식별자

### Rule의 역할
- 프로젝트 전체 AST 그래프 분석 결과
- 파일별로 관련 Rule만 필터링하여 제공
- LLM이 참고할 **예시 규칙**

## 📦 빠른 사용법

```bash
# 1. 설치
pip install -r requirements.txt

# 2. Swift 코드 배치
cp *.swift data/input_swift/

# 3. 실행
python main.py

# 4. 결과 확인
cat data/output/dataset.jsonl
```

## 📄 출력 예시

```jsonl
{"input": "...", "output": "{\"identifiers\": [\"viewDidLoad\", \"delegate\"]}"}
```

자세한 내용은 프로젝트 내 README.md 참고
