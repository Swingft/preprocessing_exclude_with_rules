"""
dataset_generator.py

데이터셋 생성 파이프라인
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.settings import (
    INPUT_SWIFT_DIR, OUTPUT_JSONL, MAX_WORKERS, 
    REQUEST_DELAY, DEBUG
)
from handlers.claude_handler import ClaudeHandler
from analyzers.ast_analyzer import ASTAnalyzer
from analyzers.rule_filter import RuleFilter
from generators.prompt_builder import PromptBuilder


class DatasetGenerator:
    """데이터셋 생성 파이프라인"""
    
    def __init__(self, rules_yaml_path: Path):
        """
        Args:
            rules_yaml_path: YAML Rule 파일 경로
        """
        self.claude_handler = ClaudeHandler()
        self.ast_analyzer = ASTAnalyzer(use_cache=True)
        self.rule_filter = RuleFilter(rules_yaml_path)
        self.prompt_builder = PromptBuilder()
    
    def process_single_file(self, swift_file: Path, file_index: int, total_files: int) -> Optional[Dict[str, str]]:
        """
        단일 Swift 파일 처리
        
        Args:
            swift_file: Swift 파일 경로
            file_index: 파일 인덱스
            total_files: 전체 파일 수
            
        Returns:
            {"instruction": "...", "input": "...", "output": "..."} 또는 None
        """
        try:
            print(f"[{file_index}/{total_files}] 처리 중: {swift_file.name}")

            # 1. Swift 코드 로드
            swift_code = swift_file.read_text(encoding='utf-8')

            if not swift_code.strip():
                print(f"  ⚠️  빈 파일, 건너뜀")
                return None

            # 2. AST 추출
            print(f"  📊 AST 추출 중...")
            ast_data = self.ast_analyzer.extract_ast(swift_file)

            # 3. Rule 필터링
            if ast_data:
                print(f"  🔍 Rule 필터링 중...")
                filtered_rules = self.rule_filter.filter_rules_for_file(ast_data)
                rules_text = self.rule_filter.format_rules_for_prompt(filtered_rules)
                print(f"  ✓ {len(filtered_rules)}개 Rule 매칭")
            else:
                print(f"  ⚠️  AST 추출 실패, Rule 없이 진행")
                filtered_rules = []
                rules_text = "No rules available (AST extraction failed)"

            # 4. 프롬프트 생성 (instruction + input 분리)
            instruction = """You are an expert Swift code auditor specializing in obfuscation safety analysis.

Analyze the provided Swift source code, AST (Abstract Syntax Tree), and exclusion rule examples to identify ALL identifiers that must be excluded from obfuscation.

**What to analyze:**
- Swift source code with complete implementation
- AST symbol information including attributes, inheritance, protocols, and modifiers
- Example exclusion rules (use as reference patterns, not exhaustive requirements)

**What to identify:**
- Framework delegate methods (UITableViewDelegate, UIApplicationDelegate, etc.)
- System lifecycle methods (viewDidLoad, viewWillAppear, applicationDidFinishLaunching, etc.)
- Protocol requirements and their implementations (Codable properties, Identifiable.id, etc.)
- @objc exposed symbols and Objective-C runtime dependencies
- IBOutlet, IBAction, and Interface Builder connections
- String-based lookups (KVC, KVO, NSCoding keys)
- Serialization properties (Codable, JSON keys)
- SwiftUI View body and environment properties
- Any identifiers that could break runtime behavior if renamed

**Critical instructions:**
1. The provided rules are EXAMPLES - use your Swift/iOS expertise to find additional patterns
2. Analyze ALL three inputs: source code, AST structure, and rule patterns
3. Return EVERY identifier that needs exclusion, even if not matching example rules
4. Consider runtime dependencies, framework contracts, and dynamic lookups

**Output format:**
Return a JSON object with this exact structure:
{"identifiers": ["identifier1", "identifier2", ...]}

Include ALL identifiers that must be excluded. Return empty array if none needed: {"identifiers": []}"""

            # input: Swift 코드 + AST + Rules
            if ast_data:
                ast_json = json.dumps(ast_data, indent=2, ensure_ascii=False)
                input_text = f"""### Swift Source Code:
```swift
{swift_code}
```

### AST Symbol Information:
```json
{ast_json}
```

### Example Exclusion Rules (REFERENCE):
{rules_text}
"""
            else:
                input_text = f"""### Swift Source Code:
```swift
{swift_code}
```
"""

            # 5. 전체 프롬프트 (Claude 호출용)
            if ast_data:
                full_prompt = self.prompt_builder.build_prompt(swift_code, ast_data, rules_text)
            else:
                full_prompt = self.prompt_builder.build_simple_prompt(swift_code)

            if DEBUG:
                print(f"\n{'='*60}")
                print(f"PROMPT for {swift_file.name}:")
                print(full_prompt[:500] + "...")
                print(f"{'='*60}\n")

            # 6. Claude API 호출
            print(f"  🤖 Claude API 호출 중...")
            result = self.claude_handler.generate_with_retry(full_prompt)

            identifiers = result.get('identifiers', [])
            print(f"  ✅ 완료: {len(identifiers)}개 식별자 추출")

            if DEBUG and identifiers:
                print(f"     식별자: {identifiers[:10]}")

            # 7. Alpaca 형식 데이터셋 항목 생성
            dataset_entry = {
                "instruction": instruction,
                "input": input_text,
                "output": json.dumps(result, ensure_ascii=False)
            }

            return dataset_entry

        except Exception as e:
            print(f"  ❌ 에러: {e}")
            return None

    def generate_dataset(self, limit: Optional[int] = None, use_parallel: bool = True) -> int:
        """
        전체 데이터셋 생성

        Args:
            limit: 처리할 최대 파일 수 (None이면 전체)
            use_parallel: 병렬 처리 여부

        Returns:
            성공한 파일 수
        """
        # Swift 파일 목록 (재귀 검색)
        swift_files = sorted(INPUT_SWIFT_DIR.rglob("*.swift"))

        if not swift_files:
            print(f"❌ Swift 파일이 없습니다: {INPUT_SWIFT_DIR}")
            return 0

        if limit:
            swift_files = swift_files[:limit]

        total_files = len(swift_files)

        # 이미 처리된 파일 확인
        processed_files = set()
        if OUTPUT_JSONL.exists():
            print(f"📋 기존 결과 파일 발견: {OUTPUT_JSONL}")
            try:
                with open(OUTPUT_JSONL, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            # input에서 파일명 추출 (간단한 방법)
                            # 또는 카운트만 세기
                            processed_files.add(len(processed_files))
                print(f"✓ 이미 처리된 항목: {len(processed_files)}개")
            except:
                print(f"⚠️  기존 파일 읽기 실패, 새로 시작")
                processed_files = set()

        print(f"\n{'='*60}")
        print(f"📦 데이터셋 생성 시작")
        print(f"{'='*60}")
        print(f"총 파일 수: {total_files}")
        print(f"이미 처리됨: {len(processed_files)}개")
        print(f"처리 대상: {total_files - len(processed_files)}개")
        print(f"병렬 처리: {use_parallel} (워커: {MAX_WORKERS if use_parallel else 1})")
        print(f"출력 파일: {OUTPUT_JSONL}")
        print(f"{'='*60}\n")

        start_time = time.time()
        success_count = len(processed_files)  # 기존 처리 개수부터 시작

        # JSONL 파일 열기 (append 모드로 이어쓰기)
        mode = 'a' if OUTPUT_JSONL.exists() else 'w'
        with open(OUTPUT_JSONL, mode, encoding='utf-8') as f:

            if use_parallel and total_files > 1:
                # 병렬 처리
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = {}

                    for i, swift_file in enumerate(swift_files, 1):
                        # 이미 처리된 파일은 건너뛰기 (간단한 인덱스 기반)
                        if i - 1 < len(processed_files):
                            print(f"[{i}/{total_files}] ⏭️  건너뜀: {swift_file.name} (이미 처리됨)")
                            continue

                        future = executor.submit(
                            self.process_single_file,
                            swift_file,
                            i,
                            total_files
                        )
                        futures[future] = swift_file

                        # API 과부하 방지
                        time.sleep(REQUEST_DELAY)

                    # 결과 수집
                    for future in as_completed(futures):
                        swift_file = futures[future]

                        try:
                            result = future.result()

                            if result:
                                # JSONL 저장
                                f.write(json.dumps(result, ensure_ascii=False) + '\n')
                                f.flush()
                                success_count += 1

                        except Exception as e:
                            print(f"❌ {swift_file.name} 처리 실패: {e}")

            else:
                # 순차 처리
                for i, swift_file in enumerate(swift_files, 1):
                    # 이미 처리된 파일은 건너뛰기
                    if i - 1 < len(processed_files):
                        print(f"[{i}/{total_files}] ⏭️  건너뜀: {swift_file.name} (이미 처리됨)")
                        continue

                    result = self.process_single_file(swift_file, i, total_files)

                    if result:
                        f.write(json.dumps(result, ensure_ascii=False) + '\n')
                        f.flush()
                        success_count += 1

                    # 딜레이
                    if i < total_files:
                        time.sleep(REQUEST_DELAY)

        # 결과 출력
        elapsed_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ 데이터셋 생성 완료!")
        print(f"{'='*60}")
        print(f"⏱️  처리 시간: {elapsed_time:.2f}초")
        print(f"✅ 성공: {success_count}개")
        print(f"❌ 실패: {total_files - success_count}개")
        print(f"📊 성공률: {success_count / total_files * 100:.1f}%")
        print(f"📁 출력: {OUTPUT_JSONL}")
        print(f"{'='*60}\n")

        return success_count