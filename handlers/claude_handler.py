"""
claude_handler.py

Claude API 통신 핸들러 (Sonnet 4.5)
"""

import anthropic
import json
import re
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional
from config.settings import CLAUDE_API_KEY, CLAUDE_MODEL, MAX_TOKENS, TEMPERATURE, MAX_RETRIES


class ClaudeHandler:
    """Claude API 핸들러"""

    # 🆕 API 응답 캐시 디렉토리
    CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "api_cache"

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        self.model = CLAUDE_MODEL

    @staticmethod
    def _get_cache_path(prompt: str) -> Path:
        """프롬프트의 해시로 캐시 파일 경로 생성"""
        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        ClaudeHandler.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return ClaudeHandler.CACHE_DIR / f"{prompt_hash}.json"

    def generate_identifiers(self, prompt: str, use_cache: bool = True) -> Dict[str, List[str]]:
        """
        Claude API를 사용해 식별자 생성 (캐싱 지원)

        Args:
            prompt: 완성된 프롬프트
            use_cache: 캐시 사용 여부

        Returns:
            {"identifiers": [...]} 딕셔너리
        """
        # 1. 캐시 확인
        if use_cache:
            cache_path = self._get_cache_path(prompt)
            if cache_path.exists():
                try:
                    cached_data = json.loads(cache_path.read_text(encoding='utf-8'))
                    print(f"  💾 캐시된 응답 사용")
                    return cached_data
                except:
                    pass

        # 2. API 호출
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = response.content[0].text.strip()

            # JSON 파싱
            parsed = self._parse_response(response_text)

            # 3. 캐시 저장
            if use_cache:
                try:
                    cache_path = self._get_cache_path(prompt)
                    cache_path.write_text(json.dumps(parsed, ensure_ascii=False), encoding='utf-8')
                    print(f"  💾 응답 캐시 저장됨")
                except:
                    pass

            return parsed

        except anthropic.APIError as e:
            raise Exception(f"Claude API error: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")

    def _parse_response(self, response_text: str) -> Dict[str, List[str]]:
        """
        응답에서 {"identifiers": [...]} 추출

        3단계 파싱:
        1. 깨끗한 JSON 파싱
        2. 배열만 추출
        3. 정규식으로 식별자 추출
        """
        # 방법 1: 깨끗한 JSON 파싱
        try:
            # 마크다운 제거
            clean_text = response_text.strip()
            clean_text = clean_text.removeprefix("```json").removeprefix("```")
            clean_text = clean_text.removesuffix("```").strip()

            # JSON 블록 찾기
            start_idx = clean_text.find('{')
            end_idx = clean_text.rfind('}')

            if start_idx != -1 and end_idx != -1:
                json_str = clean_text[start_idx:end_idx + 1]

                # 주석 제거
                json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
                json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)

                data = json.loads(json_str)

                if 'identifiers' in data and isinstance(data['identifiers'], list):
                    identifiers = [str(id).strip() for id in data['identifiers'] if id]
                    return {"identifiers": identifiers}
        except:
            pass

        # 방법 2: 배열만 추출 ["id1", "id2"]
        try:
            array_match = re.search(r'\[([^\]]+)\]', response_text)
            if array_match:
                array_str = '[' + array_match.group(1) + ']'
                identifiers = json.loads(array_str)
                return {"identifiers": [str(id).strip() for id in identifiers if id]}
        except:
            pass

        # 방법 3: 따옴표로 감싼 문자열들 추출
        try:
            identifiers = re.findall(r'"([^"]+)"', response_text)
            # 키워드 필터링
            filtered = [
                id for id in identifiers
                if id not in ['identifiers', 'reasoning', 'error', 'exclusions', 'evidence']
                and len(id) > 0
                and not id.startswith('is_')
                and not id.startswith('This ')
            ]
            if filtered:
                return {"identifiers": filtered[:100]}  # 최대 100개
        except:
            pass

        # 파싱 실패
        return {"identifiers": []}

    def generate_with_retry(self, prompt: str, max_retries: int = MAX_RETRIES) -> Dict[str, List[str]]:
        """
        재시도 로직이 포함된 생성

        Args:
            prompt: 완성된 프롬프트
            max_retries: 최대 재시도 횟수

        Returns:
            {"identifiers": [...]} 딕셔너리
        """
        for attempt in range(max_retries):
            try:
                return self.generate_identifiers(prompt)
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 지수 백오프
                    print(f"  ⚠️  재시도 {attempt + 1}/{max_retries} (대기: {wait_time}초) - {str(e)[:50]}")
                    time.sleep(wait_time)
                else:
                    print(f"  ❌ 모든 재시도 실패: {e}")
                    return {"identifiers": []}