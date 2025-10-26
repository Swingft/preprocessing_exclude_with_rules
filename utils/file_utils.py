"""
file_utils.py

파일 I/O 유틸리티
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


def read_swift_file(file_path: Path) -> Optional[str]:
    """
    Swift 파일 읽기 (여러 인코딩 시도)
    
    Args:
        file_path: 파일 경로
        
    Returns:
        파일 내용 또는 None
    """
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"⚠️  파일 읽기 실패 ({encoding}): {e}")
            continue
    
    print(f"❌ 모든 인코딩 실패: {file_path.name}")
    return None


def read_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """
    JSONL 파일 읽기
    
    Args:
        file_path: JSONL 파일 경로
        
    Returns:
        JSON 객체 리스트
    """
    data = []
    
    if not file_path.exists():
        return data
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    obj = json.loads(line)
                    data.append(obj)
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON 파싱 실패 (line {line_num}): {e}")
                    continue
    
    except Exception as e:
        print(f"❌ JSONL 읽기 실패: {e}")
    
    return data


def write_jsonl(file_path: Path, data: List[Dict[str, Any]]) -> bool:
    """
    JSONL 파일 쓰기
    
    Args:
        file_path: 출력 파일 경로
        data: JSON 객체 리스트
        
    Returns:
        성공 여부
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for obj in data:
                f.write(json.dumps(obj, ensure_ascii=False) + '\n')
        return True
    
    except Exception as e:
        print(f"❌ JSONL 쓰기 실패: {e}")
        return False


def append_jsonl(file_path: Path, obj: Dict[str, Any]) -> bool:
    """
    JSONL 파일에 항목 추가
    
    Args:
        file_path: 파일 경로
        obj: 추가할 JSON 객체
        
    Returns:
        성공 여부
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(obj, ensure_ascii=False) + '\n')
        return True
    
    except Exception as e:
        print(f"❌ JSONL 추가 실패: {e}")
        return False


def count_jsonl_lines(file_path: Path) -> int:
    """
    JSONL 파일의 라인 수 카운트
    
    Args:
        file_path: 파일 경로
        
    Returns:
        라인 수
    """
    if not file_path.exists():
        return 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0
