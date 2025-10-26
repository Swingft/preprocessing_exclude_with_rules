"""
main.py

데이터셋 생성 메인 실행 파일
"""

import argparse
from pathlib import Path

from config.settings import RULES_YAML_PATH, DEBUG
from generators.dataset_generator import DatasetGenerator


def main():
    """메인 함수"""
    # CLI 인자 파싱
    parser = argparse.ArgumentParser(
        description="Swift 난독화 제외 식별자 데이터셋 생성"
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='처리할 최대 파일 수 (기본: 전체)'
    )
    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='병렬 처리 비활성화'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='디버그 모드 활성화'
    )
    
    args = parser.parse_args()
    
    # 디버그 모드 설정
    if args.debug:
        import config.settings as settings
        settings.DEBUG = True
    
    # 데이터셋 생성기 초기화
    print("\n🚀 데이터셋 생성기 초기화 중...")
    
    if not RULES_YAML_PATH.exists():
        print(f"⚠️  Rule 파일이 없습니다: {RULES_YAML_PATH}")
        print("   Rule 없이 진행합니다.")
    
    generator = DatasetGenerator(RULES_YAML_PATH)
    
    # 데이터셋 생성
    use_parallel = not args.no_parallel
    success_count = generator.generate_dataset(
        limit=args.limit,
        use_parallel=use_parallel
    )
    
    if success_count > 0:
        print(f"\n✅ 성공적으로 {success_count}개 파일 처리 완료!")
    else:
        print(f"\n❌ 처리된 파일이 없습니다.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
