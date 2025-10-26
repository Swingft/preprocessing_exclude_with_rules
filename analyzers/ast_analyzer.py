"""
ast_analyzer.py

Swift 소스코드에서 AST 추출
"""

import subprocess
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
from config.settings import SWIFT_AST_ANALYZER, AST_CACHE_DIR


class ASTAnalyzer:
    """Swift AST 분석기"""
    
    def __init__(self, use_cache: bool = True):
        """
        Args:
            use_cache: AST 캐시 사용 여부
        """
        self.analyzer_path = SWIFT_AST_ANALYZER
        self.use_cache = use_cache
        
        if not self.analyzer_path.exists():
            print(f"⚠️  SwiftASTAnalyzer not found at {self.analyzer_path}")
            print("    빌드 필요: cd SwiftASTAnalyzer && swift build -c release")
    
    def _get_cache_path(self, swift_code: str) -> Path:
        """코드 해시 기반 캐시 경로 생성"""
        code_hash = hashlib.md5(swift_code.encode()).hexdigest()
        return AST_CACHE_DIR / f"{code_hash}.json"
    
    def extract_ast(self, swift_file_path: Path) -> Optional[List[Dict[str, Any]]]:
        """
        Swift 파일에서 AST 추출
        
        Args:
            swift_file_path: Swift 파일 경로
            
        Returns:
            AST JSON 리스트 또는 None
        """
        # 캐시 확인
        if self.use_cache:
            try:
                swift_code = swift_file_path.read_text(encoding='utf-8')
                cache_path = self._get_cache_path(swift_code)
                
                if cache_path.exists():
                    cached_data = json.loads(cache_path.read_text())
                    return cached_data
            except Exception:
                pass
        
        # AST Analyzer 존재 확인
        if not self.analyzer_path.exists():
            return None
        
        # AST 추출
        try:
            result = subprocess.run(
                [str(self.analyzer_path), str(swift_file_path)],
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8'
            )
            
            if result.returncode != 0:
                print(f"  ⚠️  AST 추출 실패: {swift_file_path.name}")
                return None
            
            output = result.stdout.strip()
            
            # "No Swift files found." 체크
            if "No Swift files found" in output:
                print(f"  ⚠️  Swift 파일 인식 실패: {swift_file_path.name}")
                return None

            # JSON 부분만 추출
            start_idx = output.find('{')
            if start_idx == -1:
                print(f"  ⚠️  JSON 시작 못 찾음: {swift_file_path.name}")
                return None

            json_str = output[start_idx:]
            ast_data = json.loads(json_str)

            # SwiftASTAnalyzer 출력 구조: {"meta": ..., "decisions": {...}}
            if isinstance(ast_data, dict) and "decisions" in ast_data:
                # decisions 객체를 평면 리스트로 변환
                decisions = ast_data["decisions"]
                symbol_list = []

                for category in ["classes", "structs", "enums", "protocols",
                                "methods", "properties", "variables", "enumCases",
                                "initializers", "deinitializers", "subscripts", "extensions"]:
                    if category in decisions and isinstance(decisions[category], list):
                        symbol_list.extend(decisions[category])

                if not symbol_list:
                    print(f"  ⚠️  AST에 심볼 없음: {swift_file_path.name}")
                    return None

                ast_data = symbol_list

            # 리스트가 아니면 리스트로 감싸기
            elif not isinstance(ast_data, list):
                ast_data = [ast_data]

            # 캐시 저장
            if self.use_cache:
                try:
                    swift_code = swift_file_path.read_text(encoding='utf-8')
                    cache_path = self._get_cache_path(swift_code)
                    cache_path.write_text(json.dumps(ast_data, ensure_ascii=False, indent=2))
                except Exception:
                    pass

            return ast_data

        except subprocess.TimeoutExpired:
            print(f"  ⚠️  AST 추출 타임아웃: {swift_file_path.name}")
            return None
        except json.JSONDecodeError as e:
            print(f"  ⚠️  AST JSON 파싱 실패: {swift_file_path.name}")
            print(f"      에러: {str(e)[:100]}")
            print(f"      출력 미리보기: {output[:200]}")
            return None
        except Exception as e:
            print(f"  ⚠️  AST 추출 에러: {swift_file_path.name} - {e}")
            return None

    def extract_ast_from_code(self, swift_code: str) -> Optional[List[Dict[str, Any]]]:
        """
        Swift 코드 문자열에서 AST 추출

        Args:
            swift_code: Swift 소스코드

        Returns:
            AST JSON 리스트 또는 None
        """
        import tempfile

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.swift', delete=False, encoding='utf-8') as f:
            f.write(swift_code)
            temp_path = Path(f.name)

        try:
            ast_data = self.extract_ast(temp_path)
            return ast_data
        finally:
            # 임시 파일 삭제
            if temp_path.exists():
                temp_path.unlink()