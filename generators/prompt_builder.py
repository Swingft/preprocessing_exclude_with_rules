"""
prompt_builder.py

Swift 코드 분석을 위한 프롬프트 생성
"""

import json
from typing import Dict, Any, List


class PromptBuilder:
    """프롬프트 생성"""
    
    @staticmethod
    def build_prompt(swift_code: str, 
                     ast_data: List[Dict[str, Any]], 
                     rules_text: str) -> str:
        """
        완성된 프롬프트 생성
        
        Args:
            swift_code: Swift 소스코드
            ast_data: AST JSON 데이터
            rules_text: 포맷팅된 Rule 텍스트
            
        Returns:
            완성된 프롬프트
        """
        # AST를 보기 좋게 포맷팅
        ast_json = json.dumps(ast_data, indent=2, ensure_ascii=False)
        
        prompt = f"""You are an expert Swift code auditor specializing in code obfuscation safety analysis.

Your task is to analyze the provided Swift source code and its AST (Abstract Syntax Tree) information to identify ALL identifiers that MUST be excluded from obfuscation.

## CRITICAL INSTRUCTIONS

1. **Rules are EXAMPLES, not exhaustive requirements**
   - The provided rules below are REFERENCE EXAMPLES based on common patterns
   - Use your expertise to identify ADDITIONAL patterns not covered by these rules
   - If you find identifiers that should be excluded but don't match the example rules, INCLUDE THEM

2. **Apply Swift/iOS Framework Knowledge**
   - Framework delegate methods (UITableViewDelegate, etc.)
   - Lifecycle methods (viewDidLoad, viewWillAppear, etc.)
   - Protocol requirements (Codable, Identifiable, etc.)
   - System callbacks and runtime dependencies
   - @objc exposed symbols
   - IBOutlet, IBAction, and Interface Builder connections

3. **Look for Runtime Dependencies**
   - String-based lookups (KVC, KVO)
   - Objective-C runtime interactions
   - Serialization contracts (JSON, Codable)
   - Foreign function interfaces
   - Dynamic member lookup

4. **Output Format Requirements**
   - Return ONLY a valid JSON object
   - Use this EXACT format: {{"identifiers": ["id1", "id2", ...]}}
   - NO markdown code blocks
   - NO explanations or comments
   - NO additional text before or after the JSON
   - If no identifiers need exclusion, return {{"identifiers": []}}

---

## OUTPUT FORMAT EXAMPLES

**Example 1 - UIViewController with lifecycle methods:**
```json
{{"identifiers": ["viewDidLoad", "viewWillAppear", "viewDidDisappear", "tableView", "numberOfRowsInSection", "cellForRowAt"]}}
```

**Example 2 - Codable struct:**
```json
{{"identifiers": ["id", "name", "email", "createdAt"]}}
```

**Example 3 - @objc exposed class:**
```json
{{"identifiers": ["MyViewController", "handleTap", "updateUI", "delegate"]}}
```

**Example 4 - No exclusions needed:**
```json
{{"identifiers": []}}
```

**Example 5 - SwiftUI View:**
```json
{{"identifiers": ["body", "navigationTitle", "onAppear"]}}
```

---

## INPUT DATA

### Swift Source Code:
```swift
{swift_code}
```

### AST Symbol Information:
```json
{ast_json}
```

### Example Exclusion Rules (REFERENCE ONLY):
{rules_text}

---

## YOUR TASK

Analyze the code and return ONLY a JSON object with ALL identifiers that should be excluded from obfuscation.

**CRITICAL**: Your response must be ONLY the JSON object. Do not include any other text, explanations, or markdown formatting.

Output format:
{{"identifiers": ["identifier1", "identifier2", ...]}}
"""

        return prompt

    @staticmethod
    def build_simple_prompt(swift_code: str) -> str:
        """
        AST/Rule 없이 간단한 프롬프트 (fallback)

        Args:
            swift_code: Swift 소스코드

        Returns:
            간단한 프롬프트
        """
        prompt = f"""You are an expert Swift code auditor. Analyze this Swift code and identify ALL identifiers that must be excluded from obfuscation.

Consider:
- Framework delegate methods
- Lifecycle methods
- Protocol requirements
- @objc exposed symbols
- Runtime dependencies

**Swift Code:**
```swift
{swift_code}
```

Return ONLY a JSON object: {{"identifiers": ["id1", "id2", ...]}}
"""
        return prompt