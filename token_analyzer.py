#!/usr/bin/env python3
"""
JSONL 토큰 분석기

JSONL 파일의 각 줄별 토큰 수를 계산하고 통계 제공
"""

import json
import tiktoken
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class TokenStats:
    """토큰 통계"""
    line_num: int
    total_tokens: int
    instruction_tokens: int
    input_tokens: int
    output_tokens: int
    content: Dict


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """
    텍스트의 토큰 수 계산

    Args:
        text: 텍스트
        encoding_name: tiktoken 인코딩 (GPT-4/3.5: cl100k_base)

    Returns:
        토큰 수
    """
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def analyze_jsonl_line(line: str, line_num: int) -> TokenStats:
    """
    JSONL 한 줄 분석

    Args:
        line: JSONL 한 줄
        line_num: 줄 번호

    Returns:
        토큰 통계
    """
    data = json.loads(line)

    instruction = data.get("instruction", "")
    input_text = data.get("input", "")
    output = data.get("output", "")

    instruction_tokens = count_tokens(instruction)
    input_tokens = count_tokens(input_text)
    output_tokens = count_tokens(output)
    total_tokens = instruction_tokens + input_tokens + output_tokens

    return TokenStats(
        line_num=line_num,
        total_tokens=total_tokens,
        instruction_tokens=instruction_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        content=data
    )


def analyze_jsonl_file(file_path: Path) -> List[TokenStats]:
    """
    JSONL 파일 전체 분석

    Args:
        file_path: JSONL 파일 경로

    Returns:
        각 줄의 토큰 통계 리스트
    """
    stats_list = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                stats = analyze_jsonl_line(line, line_num)
                stats_list.append(stats)
            except Exception as e:
                print(f"⚠️  Line {line_num} 에러: {e}")

    return stats_list


def print_statistics(stats_list: List[TokenStats]):
    """
    토큰 통계 출력

    Args:
        stats_list: 토큰 통계 리스트
    """
    if not stats_list:
        print("❌ 데이터 없음")
        return

    # 전체 통계
    total_lines = len(stats_list)
    total_tokens_all = sum(s.total_tokens for s in stats_list)
    avg_tokens = total_tokens_all / total_lines

    max_stat = max(stats_list, key=lambda s: s.total_tokens)
    min_stat = min(stats_list, key=lambda s: s.total_tokens)

    # 헤더
    print("\n" + "=" * 80)
    print("📊 JSONL 토큰 분석 결과")
    print("=" * 80)

    # 전체 통계
    print(f"\n📈 전체 통계:")
    print(f"  • 총 라인 수: {total_lines:,}")
    print(f"  • 총 토큰 수: {total_tokens_all:,}")
    print(f"  • 평균 토큰: {avg_tokens:,.1f}")
    print(f"  • 최대 토큰: {max_stat.total_tokens:,} (Line {max_stat.line_num})")
    print(f"  • 최소 토큰: {min_stat.total_tokens:,} (Line {min_stat.line_num})")

    # 필드별 평균
    avg_instruction = sum(s.instruction_tokens for s in stats_list) / total_lines
    avg_input = sum(s.input_tokens for s in stats_list) / total_lines
    avg_output = sum(s.output_tokens for s in stats_list) / total_lines

    print(f"\n📋 필드별 평균:")
    print(f"  • instruction: {avg_instruction:,.1f} 토큰")
    print(f"  • input:       {avg_input:,.1f} 토큰")
    print(f"  • output:      {avg_output:,.1f} 토큰")

    # 토큰 범위 분포
    print(f"\n📊 토큰 범위 분포:")
    ranges = [
        (0, 1000, "0-1K"),
        (1000, 2000, "1K-2K"),
        (2000, 5000, "2K-5K"),
        (5000, 10000, "5K-10K"),
        (10000, 20000, "10K-20K"),
        (20000, float('inf'), "20K+")
    ]

    for min_tok, max_tok, label in ranges:
        count = sum(1 for s in stats_list if min_tok <= s.total_tokens < max_tok)
        if count > 0:
            pct = count / total_lines * 100
            bar = "█" * int(pct / 2)
            print(f"  {label:>8}: {count:3} ({pct:5.1f}%) {bar}")

    # 정렬된 상세 목록
    print(f"\n📝 라인별 상세 (토큰 수 내림차순):")
    print("=" * 80)
    print(f"{'Line':>6} │ {'Total':>8} │ {'Instruction':>12} │ {'Input':>8} │ {'Output':>8}")
    print("─" * 80)

    sorted_stats = sorted(stats_list, key=lambda s: s.total_tokens, reverse=True)

    for stats in sorted_stats:
        print(f"{stats.line_num:6} │ {stats.total_tokens:8,} │ "
              f"{stats.instruction_tokens:12,} │ {stats.input_tokens:8,} │ "
              f"{stats.output_tokens:8,}")

    print("=" * 80)

    # 권장 설정
    print(f"\n💡 권장 설정:")

    # 99 percentile
    sorted_totals = sorted([s.total_tokens for s in stats_list])
    p99_idx = int(len(sorted_totals) * 0.99)
    p99_tokens = sorted_totals[p99_idx] if p99_idx < len(sorted_totals) else sorted_totals[-1]

    print(f"  • max_tokens (99%): {p99_tokens:,}")
    print(f"  • max_tokens (최대): {max_stat.total_tokens:,}")

    # 패딩 고려
    recommended_max = ((max_stat.total_tokens + 511) // 512) * 512  # 512 단위로 올림
    print(f"  • 권장 max_tokens: {recommended_max:,} (512 단위)")

    # Context window 경고
    if max_stat.total_tokens > 4096:
        print(f"\n⚠️  경고: 최대 토큰이 4K를 초과합니다. GPT-3.5는 불가능할 수 있습니다.")
    if max_stat.total_tokens > 8192:
        print(f"⚠️  경고: 최대 토큰이 8K를 초과합니다. 일부 모델에서 문제될 수 있습니다.")
    if max_stat.total_tokens > 16384:
        print(f"⚠️  경고: 최대 토큰이 16K를 초과합니다. 긴 컨텍스트 모델 필요합니다.")


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(
        description="JSONL 파일의 토큰 수 분석"
    )
    parser.add_argument(
        'file',
        type=str,
        help='JSONL 파일 경로'
    )
    parser.add_argument(
        '--encoding',
        type=str,
        default='cl100k_base',
        help='tiktoken 인코딩 (기본: cl100k_base for GPT-4/3.5-turbo)'
    )
    parser.add_argument(
        '--sort-by',
        type=str,
        choices=['total', 'instruction', 'input', 'output'],
        default='total',
        help='정렬 기준'
    )

    args = parser.parse_args()

    file_path = Path(args.file)

    if not file_path.exists():
        print(f"❌ 파일 없음: {file_path}")
        return 1

    print(f"🔍 분석 중: {file_path}")
    print(f"📐 인코딩: {args.encoding}")

    # 분석
    stats_list = analyze_jsonl_file(file_path)

    # 통계 출력
    print_statistics(stats_list)

    return 0


if __name__ == "__main__":
    exit(main())