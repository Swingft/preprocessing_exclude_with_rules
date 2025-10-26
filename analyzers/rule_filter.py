"""
rule_filter.py

프로젝트 전체 Rule에서 파일별로 관련 Rule 필터링
"""

import yaml
from typing import Dict, Any, List, Set
from pathlib import Path


class RuleFilter:
    """휴리스틱 Rule 필터링"""
    
    def __init__(self, rules_yaml_path: Path):
        """
        Args:
            rules_yaml_path: YAML Rule 파일 경로
        """
        self.rules_data = self._load_rules(rules_yaml_path)
        self.all_rules = self.rules_data.get('rules', [])
    
    def _load_rules(self, path: Path) -> Dict[str, Any]:
        """YAML Rule 로드"""
        if not path.exists():
            print(f"⚠️  Rules file not found: {path}")
            return {'rules': []}
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"⚠️  Invalid YAML in rules file: {e}")
            return {'rules': []}
        except Exception as e:
            print(f"⚠️  Error loading rules: {e}")
            return {'rules': []}
    
    def extract_identifiers_from_ast(self, ast_data: List[Dict[str, Any]]) -> Set[str]:
        """
        AST에서 모든 식별자 추출
        
        Args:
            ast_data: AST JSON 데이터 리스트
            
        Returns:
            식별자 집합
        """
        identifiers = set()
        
        if not ast_data:
            return identifiers
        
        def extract_recursive(obj):
            """재귀적으로 식별자 추출"""
            if isinstance(obj, dict):
                # symbol_name 필드
                if 'symbol_name' in obj:
                    identifiers.add(obj['symbol_name'])
                
                # name 필드
                if 'name' in obj and isinstance(obj['name'], str):
                    identifiers.add(obj['name'])
                
                # 재귀
                for value in obj.values():
                    extract_recursive(value)
            
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)
        
        extract_recursive(ast_data)
        return identifiers
    
    def filter_rules_for_file(self, ast_data: List[Dict[str, Any]], 
                               max_rules: int = 20) -> List[Dict[str, Any]]:
        """
        파일의 AST를 기반으로 관련 Rule만 필터링
        
        Args:
            ast_data: 파일의 AST 데이터
            max_rules: 최대 반환 Rule 수
            
        Returns:
            관련 Rule 리스트
        """
        # 파일에 포함된 식별자 추출
        file_identifiers = self.extract_identifiers_from_ast(ast_data)
        
        if not file_identifiers:
            return []
        
        # Rule에서 관련 항목 필터링
        filtered_rules = []
        
        for rule in self.all_rules:
            if not isinstance(rule, dict):
                continue
            
            # Rule이 파일과 관련 있는지 확인
            is_relevant = self._is_rule_relevant(rule, file_identifiers, ast_data)
            
            if is_relevant:
                filtered_rules.append(rule)
                
                if len(filtered_rules) >= max_rules:
                    break
        
        return filtered_rules
    
    def _is_rule_relevant(self, rule: Dict[str, Any], 
                          file_identifiers: Set[str],
                          ast_data: List[Dict[str, Any]]) -> bool:
        """
        Rule이 파일과 관련있는지 판단
        """
        # 1. Rule description에 언급된 키워드 확인
        description = rule.get('description', '').lower()
        
        # UIKit 관련
        if 'uikit' in description or 'uiview' in description:
            if any('ui' in id.lower() for id in file_identifiers):
                return True
        
        # AppDelegate 관련
        if 'appdelegate' in description or 'scenedelegate' in description:
            if any('delegate' in id.lower() for id in file_identifiers):
                return True
        
        # @objc 관련
        if '@objc' in description or 'objective-c' in description:
            # AST에서 @objc 속성 확인
            for symbol in ast_data:
                if isinstance(symbol, dict):
                    attrs = symbol.get('attributes', [])
                    if any('@objc' in str(attr) for attr in attrs):
                        return True
        
        # Codable 관련
        if 'codable' in description:
            if any('codable' in id.lower() or 'decodable' in id.lower() 
                   for id in file_identifiers):
                return True
        
        # 2. Pattern에서 직접 매칭
        pattern = rule.get('pattern', [])
        if isinstance(pattern, list):
            for p in pattern:
                if isinstance(p, dict):
                    where_clauses = p.get('where', [])
                    for clause in where_clauses:
                        if isinstance(clause, str):
                            # 식별자 이름 직접 확인
                            for identifier in file_identifiers:
                                if identifier in clause:
                                    return True
        
        return False
    
    def format_rules_for_prompt(self, filtered_rules: List[Dict[str, Any]]) -> str:
        """
        프롬프트에 포함할 Rule 형식으로 변환
        
        Args:
            filtered_rules: 필터링된 Rule 리스트
            
        Returns:
            프롬프트용 Rule 문자열
        """
        if not filtered_rules:
            return "No specific rules matched for this file."
        
        formatted = "**Relevant Exclusion Rule Examples:**\n\n"
        formatted += "*Note: These rules are EXAMPLES. Use your expertise to find ALL identifiers that should be excluded, even if they don't match these exact patterns.*\n\n"
        
        for i, rule in enumerate(filtered_rules[:10], 1):  # 최대 10개만
            rule_id = rule.get('id', 'UNKNOWN')
            description = rule.get('description', 'No description')
            
            formatted += f"{i}. **Rule ID**: `{rule_id}`\n"
            formatted += f"   **Description**: {description}\n"
            
            # Pattern 간단히 표시
            pattern = rule.get('pattern', [])
            if pattern:
                formatted += f"   **Pattern**: Checks for specific symbol attributes\n"
            
            formatted += "\n"
        
        return formatted.strip()
