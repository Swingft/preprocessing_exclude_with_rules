#!/usr/bin/env python3
"""
generate_real_world_inference.py

실세계 Swift 코드 → 추론용 JSONL 생성
기존 프로젝트의 AST Analyzer, Rule Filter 활용
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.ast_analyzer import ASTAnalyzer
from analyzers.rule_filter import RuleFilter
from generators.prompt_builder import PromptBuilder

# 시스템 프롬프트 (학습 데이터와 동일)
INSTRUCTION = """You are an expert Swift code auditor specializing in obfuscation safety analysis.

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


class RealWorldInferenceGenerator:
    """실세계 Swift 코드 → 추론용 JSONL 생성기"""

    def __init__(
            self,
            swift_dir: Path,
            rules_yaml_path: Path,
            output_jsonl: Path
    ):
        """
        Args:
            swift_dir: Swift 소스 파일 디렉토리
            rules_yaml_path: Rule YAML 경로
            output_jsonl: 출력 JSONL 파일
        """
        self.swift_dir = swift_dir
        self.rules_yaml_path = rules_yaml_path
        self.output_jsonl = output_jsonl

        # 기존 프로젝트 컴포넌트 활용
        self.ast_analyzer = ASTAnalyzer(use_cache=True)
        self.rule_filter = RuleFilter(rules_yaml_path)
        self.prompt_builder = PromptBuilder()

    def process_single_file(self, swift_file: Path) -> Optional[Dict[str, str]]:
        """
        단일 Swift 파일 처리

        Args:
            swift_file: Swift 파일 경로

        Returns:
            JSONL 한 줄 (instruction + input만)
        """
        try:
            print(f"  • 처리 중: {swift_file.name}")

            # 1. Swift 코드 로드
            swift_code = swift_file.read_text(encoding='utf-8')

            if not swift_code.strip():
                print(f"    ⚠️  빈 파일, 건너뜀")
                return None

            # 2. AST 추출 (기존 ASTAnalyzer 사용)
            print(f"    📊 AST 추출 중...")
            ast_data = self.ast_analyzer.extract_ast(swift_file)

            if not ast_data:
                print(f"    ⚠️  AST 추출 실패, AST 없이 진행")
                ast_data = []
            else:
                print(f"    ✓ AST 추출 완료: {len(ast_data)}개 심볼")

            # 3. Rule 필터링 (기존 RuleFilter 사용)
            if ast_data:
                print(f"    🔍 Rule 필터링 중...")
                filtered_rules = self.rule_filter.filter_rules_for_file(ast_data, max_rules=20)
                rules_text = self.rule_filter.format_rules_for_prompt(filtered_rules)
                print(f"    ✓ {len(filtered_rules)}개 Rule 매칭")
            else:
                filtered_rules = []
                rules_text = "No rules available (AST extraction failed)"

            # 4. Input 텍스트 생성
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
                # AST 없이
                input_text = f"""### Swift Source Code:
```swift
{swift_code}
```

### Example Exclusion Rules (REFERENCE):
{rules_text}
"""

            # 5. JSONL 항목 생성 (output 없음)
            jsonl_entry = {
                "instruction": INSTRUCTION,
                "input": input_text
            }

            print(f"    ✅ 완료")
            return jsonl_entry

        except Exception as e:
            print(f"    ❌ 에러: {e}")
            return None

    def generate(self) -> int:
        """
        전체 JSONL 생성

        Returns:
            성공한 파일 수
        """
        # Swift 파일 찾기
        swift_files = sorted(self.swift_dir.rglob("*.swift"))

        if not swift_files:
            print(f"❌ Swift 파일 없음: {self.swift_dir}")
            return 0

        total_files = len(swift_files)
        success_count = 0

        print(f"\n{'=' * 70}")
        print(f"🚀 추론용 JSONL 생성 시작")
        print(f"{'=' * 70}")
        print(f"📂 Swift 디렉토리: {self.swift_dir}")
        print(f"📄 Rule 파일: {self.rules_yaml_path}")
        print(f"📝 출력 파일: {self.output_jsonl}")
        print(f"\n🔍 Swift 파일 발견: {total_files}개\n")

        # JSONL 생성
        with open(self.output_jsonl, 'w', encoding='utf-8') as f:
            for i, swift_file in enumerate(swift_files, 1):
                print(f"[{i}/{total_files}]")

                result = self.process_single_file(swift_file)

                if result:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    f.flush()
                    success_count += 1

                print()  # 빈 줄

        # 결과 출력
        print(f"{'=' * 70}")
        print(f"✅ 생성 완료!")
        print(f"{'=' * 70}")
        print(f"✅ 성공: {success_count}/{total_files}개")
        print(f"📊 성공률: {success_count / total_files * 100:.1f}%")
        print(f"📁 출력: {self.output_jsonl}")
        print(f"{'=' * 70}\n")

        print(f"다음 단계:")
        print(f"  1. 토큰 확인: python token_analyzer.py {self.output_jsonl}")
        print(f"  2. RunPod 업로드")
        print(f"  3. 파인튜닝 모델로 추론\n")

        return success_count


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(
        description="실세계 Swift 코드 → 추론용 JSONL 생성 (기존 프로젝트 구조 활용)"
    )
    parser.add_argument(
        '--swift-dir',
        type=str,
        default='data/input_swift/real_world',
        help='Swift 소스 파일 디렉토리'
    )
    parser.add_argument(
        '--rules',
        type=str,
        default='data/rules/swift_exclusion_rules.yaml',
        help='Rule YAML 파일'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='inference_input.jsonl',
        help='출력 JSONL 파일명'
    )

    args = parser.parse_args()

    # 경로 설정
    swift_dir = Path(args.swift_dir)
    rules_yaml_path = Path(args.rules)
    output_jsonl = Path(args.output)

    # 경로 확인
    if not swift_dir.exists():
        print(f"❌ Swift 디렉토리 없음: {swift_dir}")
        print(f"   디렉토리를 생성하거나 경로를 확인하세요.")
        return 1

    if not rules_yaml_path.exists():
        print(f"⚠️  Rule 파일 없음: {rules_yaml_path}")
        print(f"   Rule 없이 진행합니다.")

    # 생성기 실행
    generator = RealWorldInferenceGenerator(
        swift_dir=swift_dir,
        rules_yaml_path=rules_yaml_path,
        output_jsonl=output_jsonl
    )

    success_count = generator.generate()

    if success_count == 0:
        print("❌ 처리된 파일이 없습니다.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())