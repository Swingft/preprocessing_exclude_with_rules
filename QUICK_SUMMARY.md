# preprocessing_exclude_with_rules - 빠른 요약

## 🎯 목적
기존 Swift 코드 + AST + 휴리스틱 Rule → 난독화 제외 식별자 추출

## 📂 핵심 파일

### 1. main.py
```python
# 메인 실행 파이프라인
# - Swift 파일 로드
# - AST 추출 및 캐싱
# - Rule 필터링
# - Claude API 호출
# - JSONL 저장
```

### 2. generators/prompt_builder.py
```python
# 프롬프트 생성 (핵심!)
# 
# 지시사항:
# - Rule은 **예시**로 제공
# - 추가 규칙도 전문가 판단으로 찾아라
# - 근거와 함께 식별자 추출
```

### 3. analyzers/rule_filter.py
```python
# YAML Rule → 파일별 필터링
# - AST 식별자 추출
# - Rule 매칭
# - 관련 Rule만 반환
```

### 4. handlers/claude_handler.py
```python
# Claude Sonnet 4.5 API
# - 재시도 로직
# - JSON 파싱
```

## 🔑 핵심 로직

### 프롬프트 전략
```
제공된 Rule은 참고 예시입니다.
Swift 난독화 안전성 전문가로서,
다음을 모두 고려하여 식별자를 추출하세요:

1. 제공된 Rule 패턴
2. 추가 난독화 위험 패턴
3. Swift/iOS 프레임워크 특성
4. 런타임 의존성

출력: {"identifiers": [...]}
```

### Rule 필터링 예시
```python
# 전체 Rule에서 파일 관련만 추출
def filter_rules_for_file(ast_data):
    file_identifiers = extract_identifiers(ast_data)
    
    filtered = []
    for rule in all_rules:
        if rule['identifier'] in file_identifiers:
            filtered.append(rule)
    
    return filtered
```

## ⚡ 실행

```bash
python main.py
```

입력: `data/input_swift/*.swift`
출력: `data/output/dataset.jsonl`

## 📊 출력 형식

```jsonl
{
  "input": "Swift Code\n\nAST: ...\n\nRules: ...",
  "output": "{\"identifiers\": [\"id1\", \"id2\"]}"
}
```

## 🎨 프롬프트 핵심

**Rule은 엄격한 필터가 아니라 참고 가이드!**

LLM이:
- Rule 예시 참고
- 추가 패턴 발견
- 전문가 판단 적용
- 종합적으로 식별자 추출

## 📦 완성된 프로젝트

전체 코드는 아래 링크에서 다운로드:
preprocessing_exclude_with_rules.zip
