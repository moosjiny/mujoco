"""ROOPS-DAM 커맨드라인 인터페이스"""
import argparse
import os
import sys


def get_api_key() -> str:
    key = os.environ.get("DAM_API_KEY", "")
    if not key:
        print("경고: DAM_API_KEY 환경변수 없음 → 로컬 캐시만 사용")
    return key


def cmd_status(args):
    from .dam import DAM
    dam = DAM(args.agent, api_key=get_api_key())
    s = dam.status()
    print(f"에이전트:   {s['agent']}")
    print(f"임베딩 차원: {s['dim']}")
    print(f"저장된 패턴: {s['n_patterns']}개")
    if s['recent']:
        print("최근 패턴:")
        for lb in s['recent']:
            print(f"  {lb}")


def cmd_query(args):
    from .dam import DAM
    dam = DAM(args.agent, api_key=get_api_key())
    hits = dam.query(args.question, top_k=args.top_k)
    if not hits:
        print("결과 없음")
        return
    for label, score in hits:
        print(f"{score:+.3f}  {label}")


def cmd_store(args):
    from .dam import DAM
    dam = DAM(args.agent, api_key=get_api_key())
    dam.store_fact(args.text, note=args.note)
    print("저장 완료")


def cmd_demo(args):
    """Phase 1 검증용 데모: 단일 에이전트 저장 → 복원 정확도 측정"""
    from .dam import DAM
    import numpy as np

    print("=== ROOPS-DAM Phase 1 데모 ===")
    dam = DAM(args.agent, api_key=get_api_key())

    facts = [
        "ADR-002 홉필드 캐시 메모리 설계 — Phase 1-5 검증 계획",
        "thesis v2 제출 완료: Cloudflare Tunnel GCP 차단 보고",
        "Rudex dual_arms 레포 접근 권한 승인 2026-06-09",
        "Memory API egs.hyperbook.com 포트 443 연결 확인",
        "W 행렬 persist 없으면 Phase 4 세션 단절 복원 불가",
    ]

    print("\n[저장 단계]")
    for i, fact in enumerate(facts):
        dam.store_fact(fact, note=f"demo_{i}")
        print(f"  저장: {fact[:50]}...")

    print("\n[복원 단계]")
    queries = [
        "홉필드 ADR",
        "thesis cloudflare",
        "rudex 권한",
    ]
    correct = 0
    for q in queries:
        hits = dam.query(q, top_k=1)
        if hits:
            label, score = hits[0]
            print(f"  쿼리: '{q}'")
            print(f"  복원: {label} (유사도 {score:+.3f})")
            if score > 0.3:
                correct += 1

    accuracy = correct / len(queries) * 100
    print(f"\n복원 정확도: {accuracy:.0f}% (목표: 70%)")
    status = "✅ Phase 1 통과" if accuracy >= 70 else "⚠️ Phase 1 미달"
    print(status)


def main():
    parser = argparse.ArgumentParser(description="ROOPS-DAM CLI")
    parser.add_argument("--agent", default="hermes",
                        choices=["hermes","mojo","rudex","aegis","eos","eros"])
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status", help="네트워크 상태 확인")

    p_q = sub.add_parser("query", help="팀 기억 검색")
    p_q.add_argument("question")
    p_q.add_argument("--top-k", type=int, default=5)

    p_s = sub.add_parser("store", help="텍스트 저장")
    p_s.add_argument("text")
    p_s.add_argument("--note", default="")

    sub.add_parser("demo", help="Phase 1 검증 데모")

    args = parser.parse_args()
    if args.cmd == "status":  cmd_status(args)
    elif args.cmd == "query": cmd_query(args)
    elif args.cmd == "store": cmd_store(args)
    elif args.cmd == "demo":  cmd_demo(args)
    else: parser.print_help()


if __name__ == "__main__":
    main()
